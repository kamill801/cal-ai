from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services import auth
from app import main


client = TestClient(main.app)


def test_auth_disabled_keeps_local_mvp_keyless() -> None:
    assert auth.authenticate_bearer_token(None, {"AUTH_PROVIDER": "disabled"}) is None


def test_supabase_auth_requires_https_project_url_and_bearer_token() -> None:
    with pytest.raises(auth.AuthConfigurationError):
        auth.authenticate_bearer_token("Bearer token", {"AUTH_PROVIDER": "supabase"})
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate_bearer_token(
            None,
            {
                "AUTH_PROVIDER": "supabase",
                "SUPABASE_URL": "https://project.supabase.co",
                "SUPABASE_JWT_ALGORITHM": "ES256",
            },
        )


def test_supabase_auth_verifies_issuer_audience_and_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeJwkClient:
        def __init__(self, url: str, **_kwargs: object) -> None:
            assert url == "https://project.supabase.co/auth/v1/.well-known/jwks.json"

        def get_signing_key_from_jwt(self, token: str):
            assert token == "signed-token"
            return type("SigningKey", (), {"key": "public-key"})()

    def fake_decode(token: str, key: str, **kwargs: object) -> dict[str, str]:
        assert token == "signed-token"
        assert key == "public-key"
        assert kwargs["audience"] == "authenticated"
        assert kwargs["issuer"] == "https://project.supabase.co/auth/v1"
        return {"sub": "user-123"}

    monkeypatch.setattr(auth, "PyJWKClient", FakeJwkClient)
    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    user = auth.authenticate_bearer_token(
        "Bearer signed-token",
        {
            "AUTH_PROVIDER": "supabase",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_JWT_ALGORITHM": "ES256",
        },
    )

    assert user and user.user_id == "user-123"


def test_api_rejects_missing_token_when_auth_is_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_ALGORITHM", "ES256")

    response = client.post("/v1/onboarding", json={})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"


def test_ready_requires_explicit_asymmetric_supabase_signing_algorithm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.delenv("SUPABASE_JWT_ALGORITHM", raising=False)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["auth"]["status"] == "misconfigured"


def test_profile_routes_are_scoped_to_authenticated_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth(authorization: str | None):
        assert authorization and authorization.startswith("Bearer ")
        return auth.AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", fake_auth)
    onboarding = client.post(
        "/v1/onboarding",
        headers={"Authorization": "Bearer owner-a"},
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 76,
            "goal_type": "recomp",
            "activity_level": "moderate",
            "training_frequency": "3-4",
            "experience_level": "beginner",
            "available_equipment": ["gym"],
            "session_minutes": 60,
        },
    )
    profile_id = onboarding.json()["profile_id"]

    owner_response = client.get(
        f"/v1/profiles/{profile_id}/dashboard/today",
        headers={"Authorization": "Bearer owner-a"},
    )
    other_response = client.get(
        f"/v1/profiles/{profile_id}/dashboard/today",
        headers={"Authorization": "Bearer owner-b"},
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 404
    assert other_response.json()["detail"]["code"] == "profile_not_found"


def test_image_uploads_and_analysis_jobs_are_scoped_to_authenticated_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth(authorization: str | None):
        assert authorization and authorization.startswith("Bearer ")
        return auth.AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", fake_auth)
    owner_headers = {"Authorization": "Bearer owner-a"}
    other_headers = {"Authorization": "Bearer owner-b"}
    upload = client.post(
        "/v1/image-uploads",
        headers=owner_headers,
        json={
            "local_asset_id": "owner-a-meal",
            "file_name": "meal.jpg",
            "content_type": "image/jpeg",
            "byte_size": 420000,
        },
    )
    image_upload_id = upload.json()["image_upload_id"]

    denied_analysis = client.post(
        "/v1/analysis-jobs",
        headers=other_headers,
        json={"image_upload_id": image_upload_id, "meal_type": "lunch"},
    )
    created_analysis = client.post(
        "/v1/analysis-jobs",
        headers=owner_headers,
        json={"image_upload_id": image_upload_id, "meal_type": "lunch"},
    )
    job_id = created_analysis.json()["analysis_job_id"]
    denied_poll = client.get(f"/v1/analysis-jobs/{job_id}", headers=other_headers)
    owner_poll = client.get(f"/v1/analysis-jobs/{job_id}", headers=owner_headers)
    result_id = owner_poll.json()["result"]["id"]
    denied_clarification = client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        headers=other_headers,
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )
    denied_save = client.post(
        "/v1/meal-logs",
        headers=other_headers,
        json={"analysis_job_id": job_id, "result_id": result_id, "clarification_value": "one_bowl"},
    )

    assert upload.status_code == 200
    assert denied_analysis.status_code == 404
    assert denied_analysis.json()["detail"]["code"] == "image_upload_not_found"
    assert created_analysis.status_code == 200
    assert denied_poll.status_code == 404
    assert denied_poll.json()["detail"]["code"] == "analysis_job_not_found"
    assert owner_poll.status_code == 200
    assert denied_clarification.status_code == 404
    assert denied_clarification.json()["detail"]["code"] == "analysis_job_not_found"
    assert denied_save.status_code == 404
    assert denied_save.json()["detail"]["code"] == "analysis_job_not_found"


def test_presigned_upload_completion_is_scoped_to_authenticated_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth(authorization: str | None):
        assert authorization and authorization.startswith("Bearer ")
        return auth.AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", fake_auth)
    owner_headers = {"Authorization": "Bearer owner-a"}
    presign_payload = {
        "local_asset_id": "owner-a-body",
        "file_name": "body.jpg",
        "content_type": "image/jpeg",
        "byte_size": 420000,
    }
    presign = client.post("/image-uploads/presign", headers=owner_headers, json=presign_payload)
    body = presign.json()

    denied_complete = client.post(
        "/image-uploads/complete",
        headers={"Authorization": "Bearer owner-b"},
        json={
            **presign_payload,
            "image_upload_id": body["image_upload_id"],
            "object_key": body["object_key"],
        },
    )

    assert presign.status_code == 200
    assert denied_complete.status_code == 404
    assert denied_complete.json()["detail"]["code"] == "image_upload_not_found"


def test_body_check_in_cannot_reuse_another_users_photo(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_auth(authorization: str | None):
        assert authorization and authorization.startswith("Bearer ")
        return auth.AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", fake_auth)
    upload = client.post(
        "/v1/image-uploads",
        headers={"Authorization": "Bearer owner-a"},
        json={
            "local_asset_id": "owner-a-progress",
            "file_name": "progress.jpg",
            "content_type": "image/jpeg",
            "byte_size": 420000,
        },
    )
    onboarding = client.post(
        "/v1/onboarding",
        headers={"Authorization": "Bearer owner-b"},
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 76,
            "goal_type": "recomp",
            "activity_level": "moderate",
            "training_frequency": "3-4",
        },
    )

    response = client.post(
        f"/v1/profiles/{onboarding.json()['profile_id']}/body-check-ins",
        headers={"Authorization": "Bearer owner-b"},
        json={
            "captured_on": "2026-07-23",
            "image_upload_id": upload.json()["image_upload_id"],
            "view": "front",
            "consent_to_ai_analysis": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "image_upload_not_found"
