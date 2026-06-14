from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import ValidationError

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
from app.services.image_uploads import resolve_image_reference

SAFE_PROVIDER_ERROR_MESSAGE = "분석 제공자를 설정할 수 없어요. 로컬 mock 분석으로 개발을 계속할 수 있어요."


class AnalysisProviderConfigurationError(RuntimeError):
    """Raised for user-actionable provider configuration problems without secret details."""


class AnalysisProviderDryRunError(RuntimeError):
    """Raised when the OpenAI scaffold is intentionally prevented from making paid calls."""


class StructuredOutputMalformedError(RuntimeError):
    """Raised when a structured provider payload cannot be parsed into the schema."""


class AnalysisProvider(Protocol):
    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse: ...

    def get_job(self, job_id: str) -> AnalysisJobResponse: ...

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse: ...

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse: ...


class MockAnalysisProvider:
    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse:
        return AnalysisJobCreateResponse(analysis_job_id=f"mock-{payload.meal_type}-001", status="queued")

    def get_job(self, job_id: str) -> AnalysisJobResponse:
        return get_mock_analysis_job(job_id)

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
        rice_answer = next((answer.value for answer in payload.answers if answer.question_key == "rice_amount"), "unknown")
        return apply_mock_clarification(job_id, rice_answer)

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse:
        return save_mock_meal(payload.clarification_value, payload.analysis_job_id)


class OpenAIAnalysisProvider:
    """Dry-run OpenAI provider scaffold.

    This class intentionally does not import the OpenAI SDK and does not perform HTTP calls.
    A later credential-approved integration can reuse the request builder and parser below.
    """

    def __init__(self, *, api_key: str | None, vision_model: str | None, text_model: str | None) -> None:
        self._vision_model = vision_model or "gpt-5.5"
        self._text_model = text_model or self._vision_model

    def create_job(self, payload: AnalysisJobRequest) -> AnalysisJobCreateResponse:
        _ = self.build_responses_payload(image_reference=resolve_image_reference(payload.image_upload_id), meal_type=payload.meal_type, optional_note=payload.optional_note)
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def get_job(self, job_id: str) -> AnalysisJobResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def apply_clarification(self, job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def save_meal(self, payload: MealLogRequest) -> SavedImpactResponse:
        raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    def build_responses_payload(self, *, image_reference: str, meal_type: str, optional_note: str | None = None) -> dict[str, Any]:
        return {
            "model": self._vision_model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Analyze this meal image for a trust-first nutrition log. "
                                f"Meal type: {meal_type}. "
                                f"Optional user note: {optional_note or 'none'}."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_reference,
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
        return OpenAIAnalysisProvider(
            api_key=env.get("AI_PROVIDER_API_KEY"),
            vision_model=env.get("AI_MODEL_VISION"),
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


def analysis_result_json_schema() -> dict[str, Any]:
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
            "detected_foods": {"type": "array", "items": {"type": "object"}},
            "uncertainty_reasons": {"type": "array", "items": {"type": "string"}},
            "primary_explanation": {"type": "string"},
            "clarification_question": {"type": ["object", "null"]},
        },
    }
