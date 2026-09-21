from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi.testclient import TestClient

from app import main
from app.services import auth
from app.services.analytics_repository import get_analytics_repository


@pytest.mark.parametrize("signals", [
    {"APP_ENV": "production"},
    {"VERCEL_ENV": "production"},
    {"VERCEL_ENV": "preview", "APP_ENV": "development"},
    {"APP_ENV": " Production ", "VERCEL_ENV": "development"},
])
@pytest.mark.parametrize("provider", [None, "", "disabled", " Disabled "])
def test_deployed_auth_cannot_fall_back_to_anonymous(monkeypatch, signals, provider):
    env = dict(signals)
    if provider is not None:
        env["AUTH_PROVIDER"] = provider
    with pytest.raises(auth.AuthConfigurationError, match="production_auth_required"):
        auth.authenticate_bearer_token(None, env)
    for key in ("APP_ENV", "VERCEL_ENV", "AUTH_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    with TestClient(main.app) as client:
        for path in ("/v1/onboarding", "/v1/analytics/events", "/image-uploads/presign"):
            response = client.post(path, json={})
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "auth_unavailable"
        assert client.get("/health").status_code == 200
        readiness = client.get("/ready")
        assert readiness.status_code == 200
        assert readiness.json()["auth"]["status"] == "misconfigured"
        assert readiness.json()["status"] == "degraded"


@pytest.mark.parametrize("env", [{}, {"APP_ENV": "test"}, {
    "APP_ENV": "development", "VERCEL_ENV": "development", "AUTH_PROVIDER": "disabled",
}])
def test_local_anonymous_fallback_is_preserved(env):
    assert auth.authenticate_bearer_token(None, env) is None


@pytest.fixture(params=["ES256", "RS256"])
def signed_token_setup(monkeypatch, request):
    algorithm = request.param
    private_key = (
        ec.generate_private_key(ec.SECP256R1()) if algorithm == "ES256"
        else rsa.generate_private_key(public_exponent=65537, key_size=2048)
    )
    public_key = private_key.public_key()
    issuer = "https://release-test.supabase.co/auth/v1"

    class LocalJwks:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=public_key)

    def local_client(actual_issuer):
        assert actual_issuer == issuer
        return LocalJwks()

    # Only key retrieval is replaced: PyJWT verifies real signatures and claims offline.
    monkeypatch.setattr(auth, "_jwk_client", local_client)
    env = {
        "APP_ENV": "production", "AUTH_PROVIDER": "supabase",
        "SUPABASE_URL": "https://release-test.supabase.co",
        "SUPABASE_JWT_ALGORITHM": algorithm,
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    claims = {
        "iss": issuer, "aud": "authenticated", "sub": "verified-owner",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return private_key, algorithm, claims, env


def test_real_signed_token_is_accepted(signed_token_setup):
    key, algorithm, claims, env = signed_token_setup
    token = jwt.encode(claims, key, algorithm=algorithm)
    assert auth.authenticate_bearer_token(f"Bearer {token}", env).user_id == "verified-owner"
    with TestClient(main.app) as client:
        response = client.post("/v1/analytics/events", headers={
            "Authorization": f"Bearer {token}",
        }, json={
            "event_name": "app_opened", "session_id": "signed_initial", "screen": "today",
            "user_id": "forged-payload-owner",
        })
    assert response.status_code == 200
    repo = get_analytics_repository()
    assert repo.user_detail("verified-owner") is not None
    assert repo.user_detail("forged-payload-owner") is None


@pytest.mark.parametrize("invalid", [
    "expired", "issuer", "audience", "missing_audience", "missing_expiry",
    "missing_subject", "empty_subject", "future_nbf", "signature", "algorithm", "unsigned",
])
def test_real_signed_token_negative_cases(signed_token_setup, invalid):
    key, algorithm, claims, env = signed_token_setup
    if invalid == "expired":
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
    elif invalid == "issuer":
        claims["iss"] = "https://other-project.supabase.co/auth/v1"
    elif invalid == "audience":
        claims["aud"] = "service_role"
    elif invalid == "missing_audience":
        claims.pop("aud")
    elif invalid == "missing_expiry":
        claims.pop("exp")
    elif invalid == "missing_subject":
        claims.pop("sub")
    elif invalid == "empty_subject":
        claims["sub"] = ""
    elif invalid == "future_nbf":
        claims["nbf"] = datetime.now(UTC) + timedelta(minutes=5)
    elif invalid == "signature":
        key = (ec.generate_private_key(ec.SECP256R1()) if algorithm == "ES256"
               else rsa.generate_private_key(public_exponent=65537, key_size=2048))
    elif invalid == "algorithm":
        algorithm, key = "HS256", "synthetic-test-signing-material-32-bytes"
    elif invalid == "unsigned":
        algorithm, key = "none", None
    token = jwt.encode(claims, key, algorithm=algorithm)
    with pytest.raises(auth.AuthenticationError):
        auth.authenticate_bearer_token(f"Bearer {token}", env)
    with TestClient(main.app) as client:
        response = client.post("/v1/analytics/events", json={}, headers={
            "Authorization": f"Bearer {token}",
        })
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "authentication_required"
