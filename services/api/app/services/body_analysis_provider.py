from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Protocol

from pydantic import ValidationError

from app.coach_schemas import BodyCheckInAnalysis
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    StructuredOutputMalformedError,
    call_openai_responses,
)

FORBIDDEN_BODY_INFERENCE_TERMS = (
    "체지방",
    "비만",
    "질환",
    "진단",
    "당뇨",
    "고혈압",
    "통증 원인",
    "매력",
    "외모 점수",
    "못생",
    "예쁘",
    "나이",
    "연령",
    "인종",
    "민족",
    "신원",
    "임신",
    "body fat",
    "obese",
    "diagnosis",
    "disease",
    "attractive",
    "ethnicity",
    "identity",
    "pregnant",
)
BODY_ANALYSIS_SAFETY_NOTE = "사진만으로 체지방률, 질환, 통증 원인, 외모나 신원을 판단하지 않아요. 통증이 있으면 전문가와 상의해 주세요."


class BodyAnalysisProvider(Protocol):
    name: str
    model_name: str

    def analyze(self, *, image_reference: str, view: str, has_previous: bool) -> BodyCheckInAnalysis: ...


class MockBodyAnalysisProvider:
    name = "mock"
    model_name = "deterministic-v1"

    def analyze(self, *, image_reference: str, view: str, has_previous: bool) -> BodyCheckInAnalysis:
        del image_reference, view
        comparison_note = "첫 체크인이에요. 같은 조명과 거리로 기록하면 주간 변화를 비교하기 쉬워요."
        if has_previous:
            comparison_note = "이전 기록과 함께 보되, 사진 차이는 조명과 자세의 영향도 커서 주간 추세로 확인해요."
        return BodyCheckInAnalysis(
            provider="mock",
            confidence="limited",
            capture_quality="good",
            observations=[
                {"title": "기록 조건", "detail": "전신이 프레임 안에 들어와 비교용 기록으로 사용할 수 있어요."},
                {"title": "해석 범위", "detail": "사진에서 보이는 자세와 윤곽만 참고하고 건강 상태를 판단하지 않아요."},
            ],
            training_focus=["등과 후면 어깨를 주 2회 균형 있게 훈련", "하체 기본 동작의 반복 품질 유지"],
            comparison_note=comparison_note,
            safety_note=BODY_ANALYSIS_SAFETY_NOTE,
        )


class OpenAIBodyAnalysisProvider:
    name = "openai"

    def __init__(self, *, api_key: str, vision_model: str | None, responses_call: Callable[[dict[str, object], str], str] | None = None) -> None:
        self._api_key = api_key
        self._vision_model = vision_model or "gpt-5.4-mini"
        self._responses_call = responses_call or call_openai_responses

    @property
    def model_name(self) -> str:
        return self._vision_model

    def analyze(self, *, image_reference: str, view: str, has_previous: bool) -> BodyCheckInAnalysis:
        payload = self.build_responses_payload(image_reference=image_reference, view=view, has_previous=has_previous)
        last_error: StructuredOutputMalformedError | None = None
        for _ in range(2):
            raw_output = self._responses_call(payload, self._api_key)
            try:
                parsed = BodyCheckInAnalysis.model_validate(json.loads(raw_output))
                validate_safe_body_analysis(parsed)
                return parsed.model_copy(update={"provider": "openai", "safety_note": BODY_ANALYSIS_SAFETY_NOTE})
            except (json.JSONDecodeError, ValidationError, StructuredOutputMalformedError) as exc:
                last_error = StructuredOutputMalformedError("body_analysis_output_malformed")
                last_error.__cause__ = exc
        raise StructuredOutputMalformedError("body_analysis_output_malformed") from last_error

    def build_responses_payload(self, *, image_reference: str, view: str, has_previous: bool) -> dict[str, object]:
        comparison_context = "A prior check-in exists, but you cannot see it in this request." if has_previous else "This is the first check-in."
        return {
            "model": self._vision_model,
            "store": False,
            "max_output_tokens": 1200,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Review this optional body progress photo for a Korean fitness coaching app. "
                                "Only describe conservative, visible training-context observations and photo capture quality. "
                                "Do not infer or estimate body-fat percentage, health conditions, diagnoses, pain causes, "
                                "attractiveness, age, ethnicity, identity, or other sensitive traits. Do not shame or rank the body. "
                                "Give at most three observations and three practical training focus suggestions. "
                                "When evidence is weak, say so. Never claim comparison with a prior image because it is not supplied. "
                                f"Requested view: {view}. {comparison_context} All user-facing text must be Korean."
                            ),
                        },
                        {"type": "input_image", "image_url": image_reference, "detail": "high"},
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "cal_ai_body_check_in",
                    "strict": True,
                    "schema": body_analysis_json_schema(),
                }
            },
        }


def validate_safe_body_analysis(analysis: BodyCheckInAnalysis) -> None:
    reviewable_text = " ".join(
        [
            *(f"{item.title} {item.detail}" for item in analysis.observations),
            *analysis.training_focus,
            analysis.comparison_note,
        ]
    ).casefold()
    if any(term.casefold() in reviewable_text for term in FORBIDDEN_BODY_INFERENCE_TERMS):
        raise StructuredOutputMalformedError("body_analysis_unsafe_inference")


def get_body_analysis_provider(environ: dict[str, str] | None = None) -> BodyAnalysisProvider:
    env = environ if environ is not None else os.environ
    provider_name = env.get("BODY_AI_PROVIDER", "mock").strip().lower() or "mock"
    if provider_name == "mock":
        return MockBodyAnalysisProvider()
    if provider_name == "openai":
        api_key = env.get("AI_PROVIDER_API_KEY")
        if not api_key:
            raise AnalysisProviderConfigurationError("openai_api_key_missing")
        model = env.get("AI_MODEL_VISION")
        if model and model.startswith("sk-"):
            raise AnalysisProviderConfigurationError("openai_model_invalid")
        return OpenAIBodyAnalysisProvider(api_key=api_key, vision_model=model)
    raise AnalysisProviderConfigurationError("body_ai_provider_unknown")


def body_analysis_json_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["provider", "confidence", "capture_quality", "observations", "training_focus", "comparison_note", "safety_note"],
        "properties": {
            "provider": {"type": "string", "enum": ["openai"]},
            "confidence": {"type": "string", "enum": ["limited"]},
            "capture_quality": {"type": "string", "enum": ["good", "retake_recommended"]},
            "observations": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "detail"],
                    "properties": {"title": {"type": "string"}, "detail": {"type": "string"}},
                },
            },
            "training_focus": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
            "comparison_note": {"type": "string"},
            "safety_note": {"type": "string"},
        },
    }
