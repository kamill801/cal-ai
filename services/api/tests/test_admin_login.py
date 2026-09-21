from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import admin_login, analytics_repository
from app.services.auth import AuthenticatedUser, AuthenticationError
from app.services.persistence import PersistenceError

client = TestClient(app)
PAYLOAD = {"username": "owner-test", "password": "fixture-password-only"}


@pytest.fixture(autouse=True)
def login_config(monkeypatch):
    for name, value in {
        "ADMIN_DASHBOARD_ENABLED": "true",
        "ADMIN_SUPABASE_URL": "https://example.supabase.co",
        "ADMIN_SUPABASE_JWT_ALGORITHM": "ES256",
        "ADMIN_SUPABASE_PUBLISHABLE_KEY": "sb_publishable_fixture",
        "ADMIN_USER_IDS": "owner-id",
        "ADMIN_LOGIN_USERNAME": "owner-test",
        "ADMIN_LOGIN_EMAIL": "owner@example.test",
    }.items():
        monkeypatch.setenv(name, value)


def test_login_returns_only_tokens_after_allowlist_check(monkeypatch):
    def post(url, **kwargs):
        assert url == "https://example.supabase.co/auth/v1/token?grant_type=password"
        assert kwargs["follow_redirects"] is False
        assert kwargs["json"] == {"email": "owner@example.test", "password": PAYLOAD["password"]}
        return httpx.Response(200, json={"access_token": "access-fixture", "refresh_token": "refresh-fixture", "email": "do-not-forward"})

    verified = []
    monkeypatch.setattr(admin_login.httpx, "post", post)
    monkeypatch.setattr(admin_login, "authenticate_admin_bearer_token", lambda token: verified.append(token) or AuthenticatedUser("owner-id"))
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == 200
    assert verified == ["Bearer access-fixture"]
    assert response.json() == {"access_token": "access-fixture", "refresh_token": "refresh-fixture"}
    assert "no-store" in response.headers["cache-control"]


def test_non_owner_token_is_not_returned(monkeypatch):
    monkeypatch.setattr(admin_login.httpx, "post", lambda *a, **kw: httpx.Response(200, json={"access_token": "access-fixture", "refresh_token": "refresh-fixture"}))
    def reject(_token):
        raise AuthenticationError("admin_forbidden")
    monkeypatch.setattr(admin_login, "authenticate_admin_bearer_token", reject)
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == 401
    assert "fixture" not in response.text


@pytest.mark.parametrize("status,expected", [(400,401), (403,401), (429,429), (500,503), (302,503)])
def test_provider_errors_are_redacted(monkeypatch, status, expected):
    monkeypatch.setattr(admin_login.httpx, "post", lambda *a, **kw: httpx.Response(status, text="sensitive-provider-error"))
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == expected
    assert "sensitive" not in response.text
    assert PAYLOAD["password"] not in response.text
    assert "no-store" in response.headers["cache-control"]


def test_invalid_schema_does_not_echo_password():
    response = client.post("/internal/admin/login", json={"username": "", "password": PAYLOAD["password"]})
    assert response.status_code == 422
    assert PAYLOAD["password"] not in response.text
    assert PAYLOAD["password"] not in repr(admin_login.AdminLoginRequest(**PAYLOAD))


def test_wrong_alias_does_not_lock_out_owner_or_call_provider(monkeypatch):
    def unexpected(*a, **kw):
        pytest.fail("must not call provider")
    monkeypatch.setattr(admin_login.httpx, "post", unexpected)
    for _ in range(20):
        assert client.post("/internal/admin/login", json={**PAYLOAD, "username": "wrong"}).status_code == 401
    monkeypatch.setattr(admin_login.httpx, "post", lambda *a, **kw: httpx.Response(400))
    for _ in range(10):
        assert client.post("/internal/admin/login", json=PAYLOAD).status_code == 401
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == 429
    assert response.headers["retry-after"] == "900"


def test_budget_is_atomic_and_resets_next_window(monkeypatch):
    repository = analytics_repository.get_analytics_repository()
    fixed = datetime(2026, 9, 5, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(analytics_repository, "now_utc", lambda: fixed)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: repository.consume_admin_login_attempt(), range(25)))
    assert sum(results) == 10
    monkeypatch.setattr(analytics_repository, "now_utc", lambda: fixed + timedelta(minutes=15))
    assert repository.consume_admin_login_attempt()


def test_missing_config_and_disabled_fail_closed(monkeypatch):
    monkeypatch.delenv("ADMIN_LOGIN_EMAIL")
    assert client.post("/internal/admin/login", json=PAYLOAD).status_code == 503
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "false")
    assert client.post("/internal/admin/login", json=PAYLOAD).status_code == 404


def test_database_failure_fails_closed(monkeypatch):
    def unavailable():
        raise PersistenceError("private-connection-value")
    monkeypatch.setattr(admin_login, "get_analytics_repository", unavailable)
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == 503
    assert "private" not in response.text


def test_network_failure_is_redacted(monkeypatch):
    def unavailable(*a, **kw):
        raise httpx.ConnectError("private-request-data")
    monkeypatch.setattr(admin_login.httpx, "post", unavailable)
    response = client.post("/internal/admin/login", json=PAYLOAD)
    assert response.status_code == 503
    assert "private" not in response.text
