from __future__ import annotations

import socket

import pytest

from app.schemas import AnalysisJobRequest
from app.services.analysis_provider import (
    AnalysisProviderDryRunError,
    MockAnalysisProvider,
    OpenAIAnalysisProvider,
    StructuredOutputMalformedError,
    failed_analysis_job,
    get_analysis_provider,
    parse_with_retry,
)


def test_provider_defaults_to_mock_without_api_key() -> None:
    provider = get_analysis_provider({})

    assert isinstance(provider, MockAnalysisProvider)
    created = provider.create_job(AnalysisJobRequest(image_upload_id="local-demo-meal-preview", meal_type="lunch"))
    assert created.analysis_job_id == "mock-lunch-001"


def test_openai_dry_run_provider_is_keyless_until_real_calls_are_enabled() -> None:
    provider = get_analysis_provider({"AI_PROVIDER": "openai", "AI_MODEL_VISION": "gpt-5.5"})

    assert isinstance(provider, OpenAIAnalysisProvider)
    with pytest.raises(AnalysisProviderDryRunError) as exc_info:
        provider.create_job(AnalysisJobRequest(image_upload_id="local-demo-meal-preview", meal_type="lunch"))

    assert str(exc_info.value) == "openai_provider_dry_run_only"


def test_openai_provider_is_dry_run_and_makes_no_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "socket", fail_socket)
    provider = get_analysis_provider({"AI_PROVIDER": "openai", "AI_MODEL_VISION": "gpt-5.5"})

    with pytest.raises(AnalysisProviderDryRunError):
        provider.create_job(AnalysisJobRequest(image_upload_id="local-demo-meal-preview", meal_type="lunch"))


def test_openai_request_payload_uses_responses_image_and_json_schema_shape() -> None:
    provider = OpenAIAnalysisProvider(api_key=None, vision_model="gpt-5.5", text_model="gpt-5.5")

    payload = provider.build_responses_payload(image_reference="data:image/jpeg;base64,abc", meal_type="lunch")

    assert payload["input"][0]["content"][1]["type"] == "input_image"
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True


def test_malformed_structured_output_retries_then_fails_closed() -> None:
    provider = OpenAIAnalysisProvider(api_key=None, vision_model="gpt-5.5", text_model="gpt-5.5")
    calls = 0

    def supplier() -> str:
        nonlocal calls
        calls += 1
        return "not-json"

    with pytest.raises(StructuredOutputMalformedError) as exc_info:
        parse_with_retry(supplier, parser=provider.parse_structured_output, attempts=2)

    assert calls == 2
    assert str(exc_info.value) == "openai_output_malformed"


def test_malformed_structured_output_parser_uses_safe_error_code() -> None:
    provider = OpenAIAnalysisProvider(api_key=None, vision_model="gpt-5.5", text_model="gpt-5.5")

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
