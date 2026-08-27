from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError

from app.schemas import (
    AnalysisJobCreateResponse,
    AnalysisJobRequest,
    AnalysisJobResponse,
    AnalysisResult,
    ClarificationRequest,
    ClarificationResponse,
    MealLogRequest,
    SavedImpactResponse,
)
from app.services.mock_analysis import apply_mock_clarification, get_mock_analysis_job, save_mock_meal

SAFE_PROVIDER_ERROR_MESSAGE = "분석 제공자를 설정할 수 없어요. 로컬 mock 분석으로 개발을 계속할 수 있어요."


class AnalysisProviderConfigurationError(RuntimeError):
    """Raised for user-actionable provider configuration problems without secret details."""


class AnalysisProviderDryRunError(RuntimeError):
    """Raised when the OpenAI scaffold is intentionally prevented from making paid calls."""


class StructuredOutputMalformedError(RuntimeError):
    """Raised when a structured provider payload cannot be parsed into the schema."""


class AnalysisProviderUnavailableError(RuntimeError):
    pass


class _OpenAIResponseContent(BaseModel):
    type: str
    text: str | None = None
    refusal: str | None = None


class _OpenAIResponseOutput(BaseModel):
    type: str
    content: list[_OpenAIResponseContent] = Field(default_factory=list)


class _OpenAIResponseEnvelope(BaseModel):
    output: list[_OpenAIResponseOutput]


ResponsesCall = Callable[[dict[str, object], str], str]


class AnalysisProvider(Protocol):
    processes_jobs_synchronously: bool
    uses_persisted_result_operations: bool

    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse: ...

    def analyze(
        self,
        *,
        job_id: str,
        payload: AnalysisJobRequest,
        image_reference: str,
    ) -> AnalysisJobResponse: ...

    def get_job(self, job_id: str) -> AnalysisJobResponse: ...

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse: ...

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse: ...


class MockAnalysisProvider:
    processes_jobs_synchronously = False
    uses_persisted_result_operations = False

    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse:
        return AnalysisJobCreateResponse(analysis_job_id=f"mock-{payload.meal_type}-001", status="queued")

    def get_job(self, job_id: str) -> AnalysisJobResponse:
        return get_mock_analysis_job(job_id)

    def analyze(
        self,
        *,
        job_id: str,
        payload: AnalysisJobRequest,
        image_reference: str,
    ) -> AnalysisJobResponse:
        del payload, image_reference
        return get_mock_analysis_job(job_id)

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
        rice_answer = next((answer.value for answer in payload.answers if answer.question_key == "rice_amount"), "unknown")
        return apply_mock_clarification(job_id, rice_answer)

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse:
        return save_mock_meal(payload.clarification_value, payload.analysis_job_id)


class OpenAIAnalysisProvider:
    processes_jobs_synchronously = True
    uses_persisted_result_operations = True

    def __init__(
        self,
        *,
        api_key: str,
        vision_model: str | None,
        text_model: str | None,
        responses_call: ResponsesCall | None = None,
    ) -> None:
        self._api_key = api_key
        self._vision_model = vision_model or "gpt-5.4-mini"
        self._text_model = text_model or self._vision_model
        self._responses_call = responses_call or call_openai_responses

    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse:
        del payload
        return AnalysisJobCreateResponse(analysis_job_id=f"openai-{uuid4()}", status="queued")

    def analyze(
        self,
        *,
        job_id: str,
        payload: AnalysisJobRequest,
        image_reference: str,
    ) -> AnalysisJobResponse:
        request_payload = self.build_responses_payload(
            image_reference=image_reference,
            meal_type=payload.meal_type,
            optional_note=payload.optional_note,
        )
        result = parse_with_retry(
            lambda: self._responses_call(request_payload, self._api_key),
            parser=self.parse_structured_output,
            attempts=2,
        ).model_copy(
            update={"id": f"analysis-{job_id}", "meal_type": payload.meal_type}
        )
        status = "needs_clarification" if result.clarification_question else "completed"
        return AnalysisJobResponse(id=job_id, status=status, result=result)

    def get_job(self, job_id: str) -> AnalysisJobResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def build_responses_payload(
        self,
        *,
        image_reference: str,
        meal_type: str,
        optional_note: str | None = None,
    ) -> dict[str, object]:
        return {
            "model": self._vision_model,
            "store": False,
            "max_output_tokens": 1400,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Analyze the meal photo for a Korean trust-first nutrition log. "
                                "Estimate calories and macros as ranges, never claim visual estimates are exact, "
                                "and name the assumptions that most affect the result. If one portion answer would "
                                "materially improve accuracy, ask one single-choice question using only the option "
                                "values half_bowl, one_bowl, large_bowl, and unknown. Otherwise return null for the "
                                "question. If the image is not food, return an empty detected_foods list, very low "
                                "confidence, and explain that a meal photo is needed. All user-facing text must be Korean. "
                                f"Meal type: {meal_type}. Optional user note: {optional_note or 'none'}."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_reference,
                            "detail": "low",
                        },
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "cal_ai_analysis_result",
                    "strict": True,
                    "schema": analysis_result_json_schema(),
                }
            },
        }

    def parse_structured_output(self, raw_output: str) -> AnalysisResult:
        try:
            data = json.loads(raw_output)
            return AnalysisResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise StructuredOutputMalformedError("openai_output_malformed") from exc


def get_analysis_provider(environ: dict[str, str] | None = None) -> AnalysisProvider:
    env = environ if environ is not None else os.environ
    provider_name = env.get("AI_PROVIDER", "mock").lower()
    if provider_name == "mock":
        return MockAnalysisProvider()
    if provider_name == "openai":
        api_key = env.get("AI_PROVIDER_API_KEY")
        if not api_key:
            raise AnalysisProviderConfigurationError("openai_api_key_missing")
        vision_model = env.get("AI_MODEL_VISION")
        if vision_model and vision_model.startswith("sk-"):
            raise AnalysisProviderConfigurationError("openai_model_invalid")
        return OpenAIAnalysisProvider(
            api_key=api_key,
            vision_model=vision_model,
            text_model=env.get("AI_MODEL_TEXT"),
        )
    raise AnalysisProviderConfigurationError("ai_provider_unknown")


def failed_analysis_job(job_id: str, *, code: str = "analysis_failed", message: str = "사진 분석 중 문제가 생겼어요. 다시 시도해 주세요.") -> AnalysisJobResponse:
    return AnalysisJobResponse(id=job_id, status="failed", result=None, error={"code": code, "message": message})


def parse_with_retry(
    supplier: Callable[[], str],
    *,
    parser: Callable[[str], AnalysisResult],
    attempts: int = 2,
) -> AnalysisResult:
    last_error: StructuredOutputMalformedError | None = None
    for _ in range(attempts):
        try:
            return parser(supplier())
        except StructuredOutputMalformedError as exc:
            last_error = exc
            continue
    raise StructuredOutputMalformedError("openai_output_malformed") from last_error


def call_openai_responses(payload: dict[str, object], api_key: str) -> str:
    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            envelope = _OpenAIResponseEnvelope.model_validate_json(response.read())
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise AnalysisProviderConfigurationError("openai_api_key_rejected") from exc
        raise AnalysisProviderUnavailableError(f"openai_http_{exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise AnalysisProviderUnavailableError("openai_transport_failed") from exc
    except ValidationError as exc:
        raise StructuredOutputMalformedError("openai_response_malformed") from exc

    for output in envelope.output:
        for content in output.content:
            if content.type == "refusal":
                raise AnalysisProviderUnavailableError("openai_response_refused")
            if content.type == "output_text" and content.text:
                return content.text
    raise StructuredOutputMalformedError("openai_output_missing")


def analysis_result_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "id",
            "meal_name",
            "meal_type",
            "stage_text",
            "summary",
            "detected_foods",
            "uncertainty_reasons",
            "primary_explanation",
            "clarification_question",
        ],
        "properties": {
            "id": {"type": "string"},
            "meal_name": {"type": "string"},
            "meal_type": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
            "stage_text": {"type": "string"},
            "summary": {
                "type": "object",
                "additionalProperties": False,
                "required": ["calories_kcal", "calorie_range", "protein_g", "carbs_g", "fat_g", "confidence", "confidence_label", "confidence_group"],
                "properties": {
                    "calories_kcal": {"type": "integer"},
                    "calorie_range": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["low", "midpoint", "high"],
                        "properties": {"low": {"type": "integer"}, "midpoint": {"type": "integer"}, "high": {"type": "integer"}},
                    },
                    "protein_g": {"type": "integer"},
                    "carbs_g": {"type": "integer"},
                    "fat_g": {"type": "integer"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence_label": {"type": "string", "enum": ["high", "medium_high", "medium", "low", "manual"]},
                    "confidence_group": {"type": "string", "enum": ["certain", "estimated", "needs_check", "manual"]},
                },
            },
            "detected_foods": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "name", "assumption_label", "confidence_label"],
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "assumption_label": {"type": "string"},
                        "confidence_label": {
                            "type": "string",
                            "enum": ["high", "medium_high", "medium", "low", "manual"],
                        },
                    },
                },
            },
            "uncertainty_reasons": {"type": "array", "items": {"type": "string"}},
            "primary_explanation": {"type": "string"},
            "clarification_question": {
                "anyOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["question_key", "question", "helper_text", "type", "options"],
                        "properties": {
                            "question_key": {"type": "string"},
                            "question": {"type": "string"},
                            "helper_text": {"type": "string"},
                            "type": {"type": "string", "enum": ["single_choice"]},
                            "options": {
                                "type": "array",
                                "minItems": 4,
                                "maxItems": 4,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["label", "value", "helper_text"],
                                    "properties": {
                                        "label": {"type": "string"},
                                        "value": {
                                            "type": "string",
                                            "enum": ["half_bowl", "one_bowl", "large_bowl", "unknown"],
                                        },
                                        "helper_text": {"type": ["string", "null"]},
                                    },
                                },
                            },
                        },
                    },
                    {"type": "null"},
                ]
            },
        },
    }
