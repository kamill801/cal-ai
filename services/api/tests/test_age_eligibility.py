from __future__ import annotations

import json
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app import account_routes, coach_routes, main
from app.services.auth import AuthenticatedUser, AuthenticationError
from app.services.coach_repository import SqlCoachRepository, get_coach_repository
from app.services.persistence import PersistenceError


OWNER = "eligibility-owner"
FOREIGN = "eligibility-other-owner"
ONBOARDING = {
    "age": 18, "sex": "other", "height_cm": 170, "current_weight_kg": 65,
    "goal_type": "maintain", "activity_level": "moderate",
}
FEATURES = [
    ("POST", "/v1/onboarding"),
    ("GET", "/v1/dashboard/today"),
    ("POST", "/v1/image-uploads"),
    ("POST", "/image-uploads/presign"),
    ("POST", "/image-uploads/complete"),
    ("POST", "/v1/analysis-jobs"),
    ("GET", "/v1/analysis-jobs/existing-job"),
    ("POST", "/v1/analysis-jobs/existing-job/clarifications"),
    ("POST", "/v1/meal-logs"),
    ("GET", "/v1/profiles/legacy/dashboard/today"),
    ("GET", "/v1/profiles/legacy/meal-logs"),
    ("POST", "/v1/profiles/legacy/meal-logs/existing-log/repeat"),
    ("POST", "/v1/profiles/legacy/weight-logs"),
    ("POST", "/v1/profiles/legacy/wellness-check-ins"),
    ("POST", "/v1/profiles/legacy/body-check-ins"),
    ("POST", "/v1/profiles/legacy/workout-plans/generate"),
    ("GET", "/v1/profiles/legacy/workout-plan"),
    ("POST", "/v1/profiles/legacy/workout-sessions"),
    ("GET", "/v1/profiles/legacy/workout-history"),
    ("GET", "/v1/profiles/legacy/progress"),
    ("GET", "/v1/profiles/legacy/weekly-coach"),
    ("GET", "/v1/profiles/legacy/workout-history/"),
    ("POST", "/v1/analysis-jobs/"),
]


@pytest.fixture
def client(monkeypatch):
    def authenticate(authorization):
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("fixture_missing_token")
        return AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", authenticate)
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("BODY_AI_PROVIDER", "mock")
    monkeypatch.setenv("ACCOUNT_DELETION_ENABLED", "false")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    with TestClient(main.app) as result:
        result.headers["Authorization"] = f"Bearer {OWNER}"
        yield result


def stored_profile(age=17, *, owner=OWNER, profile_id="legacy", created_at="2026-01-01"):
    repo = get_coach_repository()
    payload = json.dumps({
        "profile_id": profile_id, "owner_id": owner,
        "onboarding": {**ONBOARDING, "age": age},
        "target": {"calories_kcal": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 60},
        "created_at": created_at,
    })
    with repo._connection() as conn:
        conn.execute("insert into coach_profiles (profile_id, payload_json, created_at, updated_at) "
                     "values (?, ?, ?, ?)", (profile_id, payload, created_at, created_at))
    return repo


def source_rows(repo):
    with repo._connection() as conn:
        return [tuple(row) for row in conn.execute("select * from coach_profiles order by profile_id").fetchall()]


@pytest.mark.parametrize("method,path", FEATURES)
def test_known_underage_owner_is_blocked_before_feature_handlers(client, monkeypatch, method, path):
    repo = stored_profile()
    before = source_rows(repo)
    monkeypatch.setattr(main, "get_analysis_provider", lambda: pytest.fail("food provider called"))
    monkeypatch.setattr(coach_routes, "get_body_analysis_provider", lambda: pytest.fail("body provider called"))
    monkeypatch.setattr(main, "create_mock_image_upload", lambda *a, **kw: pytest.fail("upload called"))
    monkeypatch.setattr(main, "create_presigned_image_upload", lambda *a, **kw: pytest.fail("presign called"))
    monkeypatch.setattr(main, "complete_presigned_image_upload", lambda *a, **kw: pytest.fail("complete called"))
    response = client.request(method, path, json={} if method == "POST" else None)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "age_restricted"
    assert response.json()["detail"]["retryable"] is False
    assert source_rows(repo) == before


@pytest.mark.parametrize("age", [14, 17])
def test_new_adult_onboarding_does_not_override_known_underage_history(client, age):
    repo = stored_profile(age)
    stored_profile(18, profile_id="newer-adult", created_at="2026-11-01")
    before = source_rows(repo)
    response = client.post("/v1/onboarding", json=ONBOARDING)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "age_restricted"
    newest = client.get("/v1/profiles/me")
    assert newest.status_code == 200
    assert newest.json()["profile_id"] == "newer-adult"
    assert client.get("/v1/dashboard/today").status_code == 403
    assert source_rows(repo) == before


@pytest.mark.parametrize("age", [18, 100, None])
def test_adults_and_owners_without_profiles_are_not_blocked_by_another_owner(client, age):
    stored_profile(14, owner=FOREIGN, profile_id="foreign-underage")
    if age is not None:
        stored_profile(age, profile_id="adult")
    assert client.get("/v1/dashboard/today").status_code == 200
    assert client.post("/v1/onboarding", json=ONBOARDING).status_code == 200


def test_profile_discovery_public_pages_and_account_management_stay_available(client, monkeypatch):
    repo = stored_profile()
    before = source_rows(repo)
    calls = []
    monkeypatch.setattr(account_routes, "delete_account", lambda owner: calls.append(owner) or "pending")
    for path in ("/privacy", "/terms", "/support", "/account-deletion", "/health"):
        assert client.get(path).status_code == 200
    assert client.get("/v1/profiles/me").json() == {"profile_id": "legacy"}
    assert client.get("/v1/profiles/me/").json() == {"profile_id": "legacy"}
    assert client.get("/v1/billing/status").status_code == 200
    response = client.request("DELETE", "/v1/account", json={"confirm": True})
    assert response.status_code == 202 and calls == [OWNER]
    # Data-deletion routes still reach their existing ownership/not-found checks.
    for path in ("/v1/profiles/missing", "/v1/profiles/legacy/meal-logs/missing"):
        assert client.delete(path).status_code == 404
    assert source_rows(repo) == before


@pytest.mark.parametrize("phase", ["initialization", "query", "filesystem"])
def test_eligibility_lookup_failure_is_controlled_and_fail_closed(client, monkeypatch, phase):
    repo = stored_profile()

    def unavailable(*a, **kw):
        if phase == "filesystem":
            raise PermissionError("fixture_private_database_error")
        raise PersistenceError("fixture_private_database_error")

    if phase != "query":
        monkeypatch.setattr(main, "get_coach_repository", unavailable)
    else:
        monkeypatch.setattr(repo, "has_underage_profile", unavailable)
    monkeypatch.setattr(main, "create_presigned_image_upload", lambda *a, **kw: pytest.fail("presign called"))
    response = client.post("/image-uploads/presign", json={})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "age_eligibility_unavailable"
    assert response.json()["detail"]["retryable"] is True
    assert "fixture_private_database_error" not in response.text
    assert client.get("/v1/profiles/me").status_code == 200


def test_age_lookup_is_not_used_for_exempt_routes_or_anonymous_local_requests(client, monkeypatch):
    repo = stored_profile()
    monkeypatch.setattr(repo, "has_underage_profile", lambda *a: pytest.fail("unexpected eligibility lookup"))
    assert client.get("/v1/profiles/me").status_code == 200
    assert client.get("/support").status_code == 200
    assert client.get("/v1/billing/status").status_code == 200
    assert client.options("/image-uploads/presign").status_code != 403
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda token: None)
    assert client.get("/v1/dashboard/today").status_code == 200


def test_age_eligibility_is_rechecked_after_a_new_underage_record(client):
    stored_profile(18, profile_id="adult")
    assert client.get("/v1/dashboard/today").status_code == 200
    stored_profile(17)
    assert client.get("/v1/dashboard/today").json()["detail"]["code"] == "age_restricted"


def test_database_query_failure_is_controlled_without_loading_profiles(client):
    repo = stored_profile()
    with repo._connection() as conn:
        conn.execute("drop table coach_profiles")
    response = client.get("/v1/dashboard/today")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "age_eligibility_unavailable"


def test_age_guard_does_not_bypass_authentication_or_account_tombstone(client, monkeypatch):
    repo = stored_profile()
    response = client.get("/v1/dashboard/today", headers={"Authorization": ""})
    assert response.status_code == 401
    monkeypatch.setattr(repo, "has_underage_profile", lambda *a: pytest.fail("age lookup before tombstone gate"))
    monkeypatch.setattr(main, "account_deletion_gate", lambda request: main.JSONResponse(
        status_code=403, content={"detail": {"code": "account_deletion_in_progress"}},
    ))
    response = client.get("/v1/dashboard/today")
    assert response.json()["detail"]["code"] == "account_deletion_in_progress"


@pytest.mark.parametrize("origin,allowed", [
    ("http://localhost:8081", True),
    ("https://not-allowed.example", False),
])
@pytest.mark.parametrize("failure,status,code", [
    ("age", 403, "age_restricted"),
    ("lookup", 503, "age_eligibility_unavailable"),
    ("authentication", 401, "authentication_required"),
    ("configuration", 503, "auth_unavailable"),
    ("tombstone", 403, "account_deletion_in_progress"),
])
def test_cors_wraps_early_access_errors(client, monkeypatch, origin, allowed, failure, status, code):
    repo = stored_profile()
    if failure == "lookup":
        def unavailable(*args):
            raise PersistenceError("fixture_lookup_unavailable")

        monkeypatch.setattr(repo, "has_underage_profile", unavailable)
    elif failure in ("authentication", "configuration"):
        error = AuthenticationError if failure == "authentication" else main.AuthConfigurationError

        def reject_authentication(authorization):
            raise error("fixture_auth_unavailable")

        monkeypatch.setattr(main, "authenticate_bearer_token", reject_authentication)
    elif failure == "tombstone":
        monkeypatch.setattr(main, "account_deletion_gate", lambda request: main.JSONResponse(
            status_code=403, content={"detail": {"code": "account_deletion_in_progress"}},
        ))

    response = client.get("/v1/dashboard/today", headers={"Origin": origin})

    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert response.headers.get("access-control-allow-origin") == (origin if allowed else None)
    assert "access-control-allow-credentials" not in response.headers
    if allowed:
        assert "Origin" in response.headers["vary"].split(", ")


@pytest.mark.parametrize("origin,status", [
    ("http://localhost:8081", 200),
    ("https://not-allowed.example", 400),
])
def test_cors_preflight_preserves_policy_and_skips_access_checks(client, monkeypatch, origin, status):
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda *args: pytest.fail("preflight authenticated"))
    monkeypatch.setattr(main, "get_coach_repository", lambda: pytest.fail("preflight age lookup"))
    requested_headers = "Authorization, Content-Type"

    response = client.options("/v1/onboarding", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": requested_headers,
    })

    assert response.status_code == status
    assert response.headers.get("access-control-allow-origin") == (origin if status == 200 else None)
    assert response.headers["access-control-allow-methods"] == "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
    assert response.headers["access-control-allow-headers"] == requested_headers
    assert "access-control-allow-credentials" not in response.headers


def test_cors_preflight_rejects_unapproved_methods(client, monkeypatch):
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda *args: pytest.fail("preflight authenticated"))
    monkeypatch.setattr(main, "get_coach_repository", lambda: pytest.fail("preflight age lookup"))

    response = client.options("/v1/onboarding", headers={
        "Origin": "http://localhost:8081",
        "Access-Control-Request-Method": "QUERY",
    })

    assert response.status_code == 400
    assert "QUERY" not in response.headers["access-control-allow-methods"].split(", ")


def test_repository_age_lookup_is_owner_scoped_without_deserializing_profiles(client, monkeypatch):
    repo = stored_profile(17)
    stored_profile(18, profile_id="newer-adult", created_at="2026-11-01")
    monkeypatch.setattr(repo, "get_profile", lambda *a: pytest.fail("full profile load"))
    monkeypatch.setattr(repo, "list_profiles_for_owner", lambda *a: pytest.fail("profile enumeration"))
    assert repo.has_underage_profile(OWNER) is True
    assert repo.has_underage_profile(FOREIGN) is False


def test_postgres_age_lookup_uses_bound_owner_and_bounded_select(monkeypatch):
    statements = []

    class Connection:
        def execute(self, statement, parameters=()):
            statements.append((statement, parameters))
            return self

        def fetchone(self):
            return {"underage": 1}

    @contextmanager
    def connection(self):
        yield Connection()

    monkeypatch.setattr(SqlCoachRepository, "_ensure_schema", lambda self: None)
    monkeypatch.setattr(SqlCoachRepository, "_connection", connection)
    repo = SqlCoachRepository("postgresql://unused-local-fixture")
    assert repo.has_underage_profile(OWNER) is True
    query, params = statements[-1]
    assert "limit 1" in query.lower() and "payload_json" in query
    assert "fetchall" not in query and "?" not in query and OWNER not in query
    assert params == (OWNER,)
    assert any("statement_timeout" in statement for statement, _ in statements)
