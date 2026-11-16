from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from fastapi.testclient import TestClient

from app import main
from app.privacy_routes import PRIVACY_CONSENT_VERSION
from app.services.analytics_repository import AnalyticsConsentError, get_analytics_repository
from app.services.auth import AuthenticatedUser
from app.services.persistence import PersistenceError
from app.admin_schemas import AnalyticsEventRequest


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda header: AuthenticatedUser(
        user_id=header.removeprefix("Bearer ") if header else "consent-owner-a",
    ))
    with TestClient(main.app) as client:
        yield client


def choose(client, *, health=True, analytics=False, owner="consent-owner-a", version=PRIVACY_CONSENT_VERSION):
    return client.put("/v1/privacy-consent", headers={"Authorization": "Bearer " + owner}, json={
        "policy_version": version, "health_data_consent": health, "analytics_consent": analytics,
    })


def event(client):
    return client.post("/v1/analytics/events", json={
        "event_name": "app_opened", "session_id": "consent-test-session", "screen": "today",
    })


def test_no_prior_consent_means_no_health_or_analytics_writes(client):
    assert client.get("/v1/privacy-consent").json() == {
        "policy_version": PRIVACY_CONSENT_VERSION, "health_data_consent": False,
        "analytics_consent": False, "consented_at": None,
    }
    for method, path in [("POST", "/v1/onboarding"), ("POST", "/v1/image-uploads/presign"),
                         ("POST", "/image-uploads/presign"), ("GET", "/v1/dashboard/today"),
                         ("GET", "/v1/profiles/missing/progress"), ("POST", "/v1/analytics/heartbeat")]:
        response = client.request(method, path, json={})
        assert response.status_code == 403, path
        assert response.json()["detail"]["code"] == "health_data_consent_required"
    repository = get_analytics_repository()
    with repository._connection() as conn:
        for table in ("app_users", "app_sessions", "product_events", "image_uploads"):
            assert conn.execute(f"select count(*) from {table}").fetchone()[0] == 0


def test_analytics_is_optional_and_revocation_stops_events(client):
    saved = choose(client)
    assert saved.status_code == 200
    assert saved.json()["consented_at"]
    assert client.get("/v1/dashboard/today").status_code == 200
    assert event(client).status_code == 403
    assert choose(client, analytics=True).status_code == 200
    assert event(client).status_code == 200
    assert choose(client, analytics=False).status_code == 200
    assert event(client).status_code == 403
    repository = get_analytics_repository()
    with pytest.raises(AnalyticsConsentError):
        repository.record_event(AnalyticsEventRequest(
            event_name="app_opened", session_id="consent-repository", screen="today",
        ), AuthenticatedUser(user_id="consent-owner-a"))


def test_consent_is_owner_scoped_and_requires_current_version(client):
    assert choose(client).status_code == 200
    foreign = client.get("/v1/privacy-consent", headers={"Authorization": "Bearer consent-owner-b"})
    assert foreign.json()["health_data_consent"] is False
    assert choose(client, version="old-version").status_code == 409
    repository = get_analytics_repository()
    repository.save_privacy_consent("consent-owner-a", policy_version="old-version",
                                    health_data_consent=True, analytics_consent=True)
    assert client.get("/v1/privacy-consent").json()["consented_at"] is None
    assert event(client).status_code == 403


@pytest.mark.parametrize("health,analytics", [("true", False), (1, False), (False, True)])
def test_consent_rejects_coercion_and_combined_optin(client, health, analytics):
    assert choose(client, health=health, analytics=analytics).status_code == 422


def test_consent_failure_is_fail_closed_without_blocking_public_help(client, monkeypatch):
    repository = get_analytics_repository()
    def unavailable(*args, **kwargs):
        raise PersistenceError("private-provider-detail")
    monkeypatch.setattr(repository, "privacy_consent", unavailable)
    response = client.get("/v1/dashboard/today")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "privacy_consent_unavailable"
    assert "private-provider-detail" not in response.text
    for path in ("/privacy", "/support", "/account-deletion"):
        assert client.get(path).status_code == 200
    assert client.get("/v1/profiles/me").status_code == 200
    assert client.request("DELETE", "/v1/account", json={"confirm": False}).status_code == 422


def test_sqlite_optout_serializes_with_event_before_any_write(client, monkeypatch):
    assert choose(client, analytics=True).status_code == 200
    repository = get_analytics_repository()
    user = AuthenticatedUser(user_id="consent-owner-a")
    payload = AnalyticsEventRequest(event_name="app_opened", session_id="sqlite-race", screen="today")
    checked, release, revoking = Event(), Event(), Event()
    original = repository._upsert_user

    def pause_before_first_analytics_write(conn, user, received_at):
        assert conn.in_transaction, "consent check must already hold the SQLite write transaction"
        checked.set()
        assert release.wait(10)
        return original(conn, user, received_at)

    def revoke():
        revoking.set()
        return repository.save_privacy_consent(user.user_id, policy_version=PRIVACY_CONSENT_VERSION,
                                               health_data_consent=True, analytics_consent=False)

    monkeypatch.setattr(repository, "_upsert_user", pause_before_first_analytics_write)
    with ThreadPoolExecutor(max_workers=2) as pool:
        recorded = pool.submit(repository.record_event, payload, user)
        try:
            assert checked.wait(10)
            revoked = pool.submit(revoke)
            assert revoking.wait(10)
            assert not revoked.done()
        finally:
            release.set()
        recorded.result(timeout=15)
        assert revoked.result(timeout=15)["analytics_consent"] is False
    with pytest.raises(AnalyticsConsentError):
        repository.record_event(payload, user)
    with repository._connection() as conn:
        assert conn.execute("select count(*) from product_events").fetchone()[0] == 1
