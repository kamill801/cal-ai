from __future__ import annotations

import json

import pytest

from app.services.analysis_provider import AnalysisProviderConfigurationError, StructuredOutputMalformedError
from app.services.body_analysis_provider import MockBodyAnalysisProvider, OpenAIBodyAnalysisProvider, get_body_analysis_provider


def valid_body_analysis() -> dict[str, object]:
    return {
        "provider": "openai",
        "confidence": "limited",
        "capture_quality": "good",
        "observations": [{"title": "촬영 조건", "detail": "전신이 프레임 안에 보여요."}],
        "training_focus": ["등 운동의 동작 품질을 확인해요."],
        "comparison_note": "이 사진만으로 이전 기록과 직접 비교하지 않아요.",
        "safety_note": "사진만으로 체지방률이나 건강 상태를 판단하지 않아요.",
    }


def test_mock_body_analysis_is_safe_and_does_not_use_image_reference() -> None:
    result = MockBodyAnalysisProvider().analyze(image_reference="secret-signed-url", view="front", has_previous=False)

    assert result.provider == "mock"
    assert result.confidence == "limited"
    assert "체지방률" in result.safety_note
    assert "secret-signed-url" not in result.model_dump_json()


def test_openai_body_payload_is_private_structured_and_safety_bounded() -> None:
    captured: dict[str, object] = {}

    def fake_call(payload: dict[str, object], api_key: str) -> str:
        captured.update(payload)
        assert api_key == "test-key"
        return json.dumps(valid_body_analysis(), ensure_ascii=False)

    result = OpenAIBodyAnalysisProvider(api_key="test-key", vision_model="gpt-test", responses_call=fake_call).analyze(
        image_reference="https://private.example/signed",
        view="front",
        has_previous=True,
    )

    assert result.provider == "openai"
    assert captured["store"] is False
    assert captured["text"]["format"]["strict"] is True
    serialized = json.dumps(captured)
    assert "input_image" in serialized
    assert "body-fat percentage" in serialized
    assert "prior image" in serialized


def test_openai_body_analysis_fails_closed_on_malformed_output() -> None:
    calls = 0

    def malformed_call(_payload: dict[str, object], _key: str) -> str:
        nonlocal calls
        calls += 1
        return '{"provider":"openai"}'

    provider = OpenAIBodyAnalysisProvider(
        api_key="test-key",
        vision_model="gpt-test",
        responses_call=malformed_call,
    )

    with pytest.raises(StructuredOutputMalformedError):
        provider.analyze(image_reference="https://private.example/signed", view="front", has_previous=False)
    assert calls == 2


def test_openai_body_analysis_fails_closed_on_schema_valid_sensitive_inference() -> None:
    calls = 0

    def unsafe_call(_payload: dict[str, object], _key: str) -> str:
        nonlocal calls
        calls += 1
        output = valid_body_analysis()
        output["observations"] = [{"title": "체성분", "detail": "체지방률은 약 18%로 보여요."}]
        return json.dumps(output, ensure_ascii=False)

    provider = OpenAIBodyAnalysisProvider(api_key="test-key", vision_model="gpt-test", responses_call=unsafe_call)

    with pytest.raises(StructuredOutputMalformedError):
        provider.analyze(image_reference="https://private.example/signed", view="front", has_previous=False)
    assert calls == 2


def test_openai_body_analysis_replaces_model_controlled_safety_note() -> None:
    def unsafe_note_call(_payload: dict[str, object], _key: str) -> str:
        output = valid_body_analysis()
        output["safety_note"] = "체지방률은 약 18%로 보여요."
        return json.dumps(output, ensure_ascii=False)

    result = OpenAIBodyAnalysisProvider(
        api_key="test-key",
        vision_model="gpt-test",
        responses_call=unsafe_note_call,
    ).analyze(image_reference="https://private.example/signed", view="front", has_previous=False)

    assert result.safety_note != "체지방률은 약 18%로 보여요."
    assert "판단하지 않아요" in result.safety_note


def test_body_provider_requires_key_only_when_openai_is_enabled() -> None:
    assert isinstance(get_body_analysis_provider({"BODY_AI_PROVIDER": "mock"}), MockBodyAnalysisProvider)
    with pytest.raises(AnalysisProviderConfigurationError):
        get_body_analysis_provider({"BODY_AI_PROVIDER": "openai"})
