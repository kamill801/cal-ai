from __future__ import annotations

import socket

import pytest

from app.schemas import AnalysisJobRequest, ImageUploadRequest
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    MockAnalysisProvider,
    OpenAIAnalysisProvider,
    StructuredOutputMalformedError,
    failed_analysis_job,
    get_analysis_provider,
    parse_with_retry,
)
from app.services.image_uploads import create_mock_image_upload, resolve_image_reference


def test_provider_defaults_to_mock_without_api_key() -> None:
    provider = get_analysis_provider({})

    assert isinstance(provider, MockAnalysisProvider)
    created = provider.create_job(AnalysisJobRequest(image_upload_id="local-demo-meal-preview", meal_type="lunch"))
    assert created.analysis_job_id == "mock-lunch-001"


def test_openai_provider_requires_api_key_when_enabled() -> None:
    with pytest.raises(AnalysisProviderConfigurationError) as exc_info:
        get_analysis_provider({"AI_PROVIDER": "openai", "AI_MODEL_VISION": "gpt-5.5"})

    assert str(exc_info.value) == "openai_api_key_missing"


def test_openai_provider_rejects_secret_like_model_value() -> None:
    with pytest.raises(AnalysisProviderConfigurationError) as exc_info:
        get_analysis_provider(
            {
                "AI_PROVIDER": "openai",
                "AI_PROVIDER_API_KEY": "test-key",
                "AI_MODEL_VISION": "sk-secret-was-put-in-the-wrong-field",
            }
        )

    assert str(exc_info.value) == "openai_model_invalid"


def test_openai_provider_does_not_make_network_call_until_analysis_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "socket", fail_socket)
    provider = get_analysis_provider(
        {"AI_PROVIDER": "openai", "AI_PROVIDER_API_KEY": "test-key", "AI_MODEL_VISION": "gpt-5.5"}
    )

    created = provider.create_job(AnalysisJobRequest(image_upload_id="image-upload-1", meal_type="lunch"))

    assert created.analysis_job_id.startswith("openai-")


def test_openai_request_payload_uses_responses_image_and_json_schema_shape() -> None:
    provider = OpenAIAnalysisProvider(api_key="test-key", vision_model="gpt-5.5", text_model="gpt-5.5")

    payload = provider.build_responses_payload(image_reference="data:image/jpeg;base64,abc", meal_type="lunch")

    assert payload["input"][0]["content"][1]["type"] == "input_image"
    assert payload["input"][0]["content"][1]["detail"] == "high"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert payload["store"] is False


def test_openai_provider_returns_structured_analysis_from_wire_response() -> None:
    wire_payloads: list[dict[str, object]] = []

    def fake_responses_call(payload: dict[str, object], api_key: str) -> str:
        wire_payloads.append(payload)
        assert api_key == "test-key"
        return """{
          "id": "analysis-live-1",
          "meal_name": "연어 덮밥",
          "meal_type": "dinner",
          "stage_text": "사진 근거로 추정했어요",
          "summary": {
            "calories_kcal": 640,
            "calorie_range": {"low": 560, "midpoint": 640, "high": 720},
            "protein_g": 38,
            "carbs_g": 72,
            "fat_g": 21,
            "confidence": 0.79,
            "confidence_label": "medium_high",
            "confidence_group": "estimated"
          },
          "detected_foods": [
            {"id": "food-1", "name": "연어", "assumption_label": "약 120g으로 추정", "confidence_label": "medium_high"}
          ],
          "uncertainty_reasons": ["밥과 소스 양은 사진만으로 정확히 알기 어려워요."],
          "primary_explanation": "보이는 재료와 일반적인 조리량을 기준으로 범위를 계산했어요.",
          "clarification_question": null
        }"""

    provider = OpenAIAnalysisProvider(
        api_key="test-key",
        vision_model="gpt-5.5",
        text_model="gpt-5.5",
        responses_call=fake_responses_call,
    )

    response = provider.analyze(
        job_id="openai-job-1",
        payload=AnalysisJobRequest(image_upload_id="image-upload-1", meal_type="dinner"),
        image_reference="https://example.test/private-image?signature=safe",
    )

    assert response.id == "openai-job-1"
    assert response.status == "completed"
    assert response.result is not None
    assert response.result.meal_name == "연어 덮밥"
    assert wire_payloads[0]["model"] == "gpt-5.5"


def test_openai_provider_resolves_uploaded_image_reference() -> None:
    upload = create_mock_image_upload(
        ImageUploadRequest(
            local_asset_id="openai-demo",
            file_name="meal.png",
            content_type="image/png",
            byte_size=420000,
        )
    )

    assert resolve_image_reference(upload.image_upload_id) == "local-image://local-upload-openai-demo"


def test_malformed_structured_output_retries_then_fails_closed() -> None:
    provider = OpenAIAnalysisProvider(api_key="test-key", vision_model="gpt-5.5", text_model="gpt-5.5")
    calls = 0

    def supplier() -> str:
        nonlocal calls
        calls += 1
        return "not-json"

    with pytest.raises(StructuredOutputMalformedError) as exc_info:
        parse_with_retry(supplier, parser=provider.parse_structured_output, attempts=2)

    assert calls == 2
    assert str(exc_info.value) == "openai_output_malformed"


def test_openai_analyze_retries_one_malformed_response() -> None:
    calls = 0

    def fake_responses_call(payload: dict[str, object], api_key: str) -> str:
        nonlocal calls
        del payload, api_key
        calls += 1
        if calls == 1:
            return "not-json"
        return """{
          "id": "analysis-live-retry",
          "meal_name": "닭가슴살 샐러드",
          "meal_type": "lunch",
          "stage_text": "사진 근거로 추정했어요",
          "summary": {
            "calories_kcal": 430,
            "calorie_range": {"low": 370, "midpoint": 430, "high": 500},
            "protein_g": 42,
            "carbs_g": 30,
            "fat_g": 15,
            "confidence": 0.82,
            "confidence_label": "medium_high",
            "confidence_group": "estimated"
          },
          "detected_foods": [],
          "uncertainty_reasons": ["드레싱 양은 사진만으로 정확히 알기 어려워요."],
          "primary_explanation": "보이는 재료와 일반적인 양을 기준으로 계산했어요.",
          "clarification_question": null
        }"""

    provider = OpenAIAnalysisProvider(
        api_key="test-key",
        vision_model="gpt-5.5",
        text_model="gpt-5.5",
        responses_call=fake_responses_call,
    )

    response = provider.analyze(
        job_id="openai-job-retry",
        payload=AnalysisJobRequest(image_upload_id="image-upload-1", meal_type="lunch"),
        image_reference="https://example.test/private-image?signature=safe",
    )

    assert calls == 2
    assert response.status == "completed"


def test_malformed_structured_output_parser_uses_safe_error_code() -> None:
    provider = OpenAIAnalysisProvider(api_key="test-key", vision_model="gpt-5.5", text_model="gpt-5.5")

    with pytest.raises(StructuredOutputMalformedError) as exc_info:
        provider.parse_structured_output("not-json")

    assert str(exc_info.value) == "openai_output_malformed"


def test_failed_job_contract_is_user_safe() -> None:
    response = failed_analysis_job("job-failed-1", code="provider_unavailable", message="분석을 다시 시도해 주세요.")

    assert response.status == "failed"
    assert response.result is None
    assert response.error is not None
    assert response.error.code == "provider_unavailable"
    assert "test-key" not in response.error.message
