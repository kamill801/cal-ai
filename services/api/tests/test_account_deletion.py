from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from threading import Event

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import account_routes, main
from app.coach_routes import router as coach_router
from app.coach_schemas import BodyCheckInResponse
from app.schemas import (
    AnalysisJobCreateResponse, AnalysisJobRequest, ImageUploadRequest, MealLogRequest, SavedImpactResponse,
)
from app.services import account_deletion as deletion, auth
from app.services.analytics_repository import get_analytics_repository
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import (
    PersistenceError,
    PostgresPersistenceRepository,
    SQLitePersistenceRepository,
    get_persistence_repository,
)
from app.services.storage import StorageConfigurationError


OWNER = "11111111-1111-4111-8111-111111111111"
FOREIGN = "22222222-2222-4222-8222-222222222222"
SECRET = "sb_secret_disposable_fixture_only"
CRON_SECRET = "disposable_cron_fixture_not_a_real_key_12345"
ONBOARDING = {
    "age": 29, "sex": "male", "height_cm": 176, "current_weight_kg": 82,
    "target_weight_kg": 76, "goal_type": "recomp", "activity_level": "moderate",
    "training_frequency": "3-4",
}


@pytest.fixture
def admin(monkeypatch):
    for key, value in {
        "ACCOUNT_DELETION_ENABLED": "true", "AUTH_PROVIDER": "supabase",
        "SUPABASE_URL": "https://fixture.supabase.co", "SUPABASE_SECRET_KEY": SECRET,
        "ACCOUNT_DELETION_WORKER_ENABLED": "true", "CRON_SECRET": CRON_SECRET,
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    calls = []
    responses = []

    def handle(request):
        calls.append(request)
        if responses:
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return httpx.Response(204 if request.method == "POST" else 200, json={})

    real_client = httpx.Client
    options = []

    def client(**kwargs):
        options.append(kwargs)
        return real_client(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(deletion.httpx, "Client", client)
    return SimpleNamespace(calls=calls, responses=responses, options=options)


@pytest.mark.parametrize("legacy", [False, True])
def test_admin_key_headers_distinguish_opaque_and_legacy_keys(admin, monkeypatch, legacy):
    key = SECRET
    if legacy:
        key = jwt.encode({"role": "service_role"}, "disposable-signing-fixture-not-a-real-key", algorithm="HS256")
        monkeypatch.delenv("SUPABASE_SECRET_KEY")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", key)
    deletion.SupabaseAccountAdmin.from_environment().delete_identity(OWNER)
    request = admin.calls[0]
    assert request.headers["apikey"] == key
    if legacy:
        assert request.headers["Authorization"] == f"Bearer {key}"
    else:
        assert "Authorization" not in request.headers


@pytest.fixture
def client(admin):
    get_persistence_repository()
    app = FastAPI()
    app.include_router(account_routes.router)
    app.include_router(account_routes.worker_router)
    app.include_router(coach_router)
    app.add_api_route("/v1/onboarding", main.create_onboarding, methods=["POST"])

    @app.middleware("http")
    async def verified_fixture_auth(request: Request, call_next):
        if request.url.path.startswith("/internal/"):
            return await call_next(request)
        # Deliberately mocked verification. No real JWT/Auth provider is used here.
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        request.state.user_id = token or None
        request.state.auth_user = AuthenticatedUser(user_id=token) if token else None
        gate = account_routes.account_deletion_gate(request)
        if gate is not None:
            return gate
        return await call_next(request)

    with TestClient(app) as result:
        yield result


def headers(owner=OWNER):
    return {"Authorization": f"Bearer {owner}"}


def delete(client, owner=OWNER, body=None, suffix=""):
    get_coach_repository()
    get_analytics_repository()
    get_persistence_repository().prepare_account_deletion()
    return client.request(
        "DELETE", "/v1/account" + suffix, headers=headers(owner),
        json={"confirm": True} if body is None else body,
    )


def complete(client, owner=OWNER):
    accepted = delete(client, owner)
    assert accepted.status_code == 202
    assert accepted.json() == {"status": "pending"}
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    return delete(client, owner)


def profile(client, owner=OWNER):
    response = client.post("/v1/onboarding", headers=headers(owner), json=ONBOARDING)
    assert response.status_code == 200
    return response.json()["profile_id"]


def upload(upload_id, owner=OWNER, *, object_key=None, expires=None):
    return get_persistence_repository().save_image_upload(
        payload=ImageUploadRequest(
            local_asset_id=upload_id, file_name="fixture.jpg", content_type="image/jpeg", byte_size=12,
        ),
        image_upload_id=upload_id, image_reference=f"fixture://{upload_id}",
        object_key=object_key, storage_provider="local", owner_id=owner, upload_expires_at=expires,
    )


def job(job_id, upload_id, owner=OWNER, profile_id=None):
    return get_persistence_repository().save_analysis_job(
        payload=AnalysisJobRequest(image_upload_id=upload_id, profile_id=profile_id),
        image_reference=f"fixture://{upload_id}", owner_id=owner,
        create_response=AnalysisJobCreateResponse(analysis_job_id=job_id, status="queued"),
    )


def rows(table):
    with sqlite3.connect(os.environ["CAL_AI_API_DATA_PATH"]) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(f"select * from {table}").fetchall()]


def test_anonymous_request_cannot_delete(client, admin):
    response = client.request("DELETE", "/v1/account", json={"confirm": True})
    assert response.status_code == 401
    assert admin.calls == []
    assert rows("account_deletions") == []


@pytest.mark.parametrize("body", [{}, {"confirm": False}, {"confirm": "true"}, {"confirm": 1},
                                   {"confirm": True, "user_id": FOREIGN}])
def test_explicit_confirmation_and_no_target_fields(client, admin, body):
    response = delete(client, body=body)
    assert response.status_code == 422
    assert not admin.calls
    assert rows("account_deletions") == []


def test_no_target_query_and_no_foreign_deletion(client, admin):
    own = profile(client)
    foreign = profile(client, FOREIGN)
    assert delete(client, suffix=f"?user_id={FOREIGN}").status_code == 422
    assert complete(client).json() == {"status": "deleted"}
    assert get_coach_repository().get_profile(own) is None
    assert get_coach_repository().get_profile(foreign).owner_id == FOREIGN
    assert str(admin.calls[-1].url).endswith(f"/admin/users/{OWNER}")


@pytest.mark.parametrize("key,value", [
    ("SUPABASE_SECRET_KEY", ""), ("SUPABASE_SECRET_KEY", "sb_publishable_fixture"),
    ("ACCOUNT_DELETION_ENABLED", "false"), ("AUTH_PROVIDER", "disabled"),
    ("ACCOUNT_DELETION_WORKER_ENABLED", "false"), ("CRON_SECRET", ""),
    ("CRON_SECRET", "too-short"),
    ("SUPABASE_URL", "https://user:password@fixture.supabase.co"),
    ("SUPABASE_URL", "https://[invalid"), ("SUPABASE_URL", "http://fixture.supabase.co"),
])
def test_config_fails_closed_without_starting_deletion(client, admin, monkeypatch, key, value):
    own = profile(client)
    monkeypatch.setenv(key, value)
    response = delete(client)
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "account_deletion_unavailable"
    assert get_persistence_repository().get_account_deletion_stage(OWNER) is None
    assert get_coach_repository().get_profile(own)
    assert not admin.calls
    assert value not in response.text if value else True


def test_orphans_legacy_links_and_foreign_owners(client, admin):
    own = profile(client)
    foreign = profile(client, FOREIGN)
    for image_id, owner in [("orphan", OWNER), ("foreign", FOREIGN), ("anonymous", None),
                            ("legacy", None), ("body-owned", OWNER)]:
        upload(image_id, owner)
    job("orphan-job", "orphan")
    job("legacy-job", "legacy", None, own)
    job("foreign-job", "foreign", FOREIGN, own)
    job("own-job-foreign-image", "foreign", OWNER)
    analytics = get_analytics_repository()
    with analytics._connection() as conn:
        for owner in (OWNER, FOREIGN):
            conn.execute(
                "insert into app_users values (?, null, null, null, 'now', 'now')", (owner,)
            )
        for session, owner, profile_id in [
            ("own-orphan", OWNER, None), ("foreign-session", FOREIGN, own),
            ("legacy-session", None, own), ("unrelated-empty", None, ""),
        ]:
            conn.execute("insert into app_sessions values (?, ?, ?, 'now', 'now', 'today')",
                         (session, owner, profile_id))
            conn.execute("insert into product_events values (?, ?, ?, ?, 'app_opened', 'today', '{}', 'now', 'now')",
                         (session, owner, session, profile_id))
        for owner in (OWNER, FOREIGN):
            conn.execute("insert into billing_subscriptions values (?, ?, 'fixture', 'beta', 'active', null, 'now', 'now')",
                         (owner, owner))
            conn.execute("insert into billing_payments values (?, ?, 'fixture', 'beta', 0, 'KRW', 'paid', 'now', 'now')",
                         (owner, owner))
    repo = get_persistence_repository()
    with repo._connection() as conn:
        for log_id, linked_job, profile_id in [("own-log", "orphan-job", own),
                                                ("legacy-log", "gone-job", own),
                                                ("foreign-log", "foreign-job", own)]:
            conn.execute("insert into meal_logs values (?, ?, 'result', 'unknown', ?, '{}', 'now')",
                         (log_id, linked_job, json.dumps({"profile_id": profile_id})))
        conn.execute("insert into clarifications values ('own-clarification', 'orphan-job', '{}', '{}', 'now')")
    assert complete(client).status_code == 200
    assert {row["image_upload_id"] for row in rows("image_uploads")} == {"foreign", "anonymous"}
    assert {row["analysis_job_id"] for row in rows("analysis_jobs")} == {"foreign-job"}
    assert [row["meal_log_id"] for row in rows("meal_logs")] == ["foreign-log"]
    assert rows("clarifications") == []
    assert {row["session_id"] for row in rows("app_sessions")} == {"foreign-session", "unrelated-empty"}
    assert {row["event_id"] for row in rows("product_events")} == {"foreign-session", "unrelated-empty"}
    assert [row["user_id"] for row in rows("app_users")] == [FOREIGN]
    assert [row["user_id"] for row in rows("billing_subscriptions")] == [FOREIGN]
    assert [row["user_id"] for row in rows("billing_payments")] == [FOREIGN]
    assert get_coach_repository().get_profile(foreign)


@pytest.mark.parametrize("image_owner", [None, OWNER])
@pytest.mark.parametrize("foreign_reference", ["job", "body"])
def test_account_shared_upload_is_not_delete_authority(client, admin, monkeypatch, image_owner, foreign_reference):
    own, foreign = profile(client), profile(client, FOREIGN)
    upload("shared-account-image", image_owner, object_key="fixture/shared-account-image")
    job("own-shared-job", "shared-account-image", OWNER, own)
    if foreign_reference == "job":
        job("foreign-shared-job", "shared-account-image", FOREIGN, foreign)
    else:
        get_coach_repository().save_body_check_in(BodyCheckInResponse(
            id="foreign-shared-body", profile_id=foreign, captured_on="2026-11-09",
            image_upload_id="shared-account-image", view="front", created_at="now",
            analysis={"provider": "mock", "confidence": "limited", "capture_quality": "good",
                      "observations": [], "training_focus": [], "comparison_note": "fixture", "safety_note": "fixture"},
        ))
    removed = []
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="local", delete_object=lambda **kwargs: removed.append(kwargs["object_key"]),
    ))
    assert delete(client).status_code == 202
    assert rows("account_deletion_objects") == []
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert removed == []
    assert get_persistence_repository().get_image_upload("shared-account-image") is not None
    assert get_persistence_repository().get_analysis_job("own-shared-job") is None
    assert get_coach_repository().get_profile(foreign) is not None
    if foreign_reference == "job":
        assert get_persistence_repository().get_analysis_job("foreign-shared-job") is not None
    else:
        assert len(get_coach_repository().list_body_check_ins(foreign)) == 1


def test_storage_outage_preserves_retry_inventory_and_durable_gate(client, admin, monkeypatch):
    own = profile(client)
    cached_profile = get_coach_repository().get_profile(own)
    upload("one", object_key="fixture/one")
    upload("two", object_key="fixture/two")
    deleted = []

    class Storage:
        provider = "local"
        fail = True

        def delete_object(self, *, object_key):
            if object_key == "fixture/two" and self.fail:
                raise StorageConfigurationError(SECRET)
            deleted.append(object_key)

    storage = Storage()
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: storage)
    response = delete(client)
    assert response.status_code == 202 and response.json() == {"status": "pending"}
    assert SECRET not in response.text
    # Small acceptance freezes sources; each worker batch captures before removing them.
    assert rows("account_deletion_objects") == []
    assert len(rows("image_uploads")) == 2
    assert not admin.calls
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert rows("image_uploads") == []
    assert get_coach_repository().get_profile(own) is None
    fresh_repository = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
    assert fresh_repository.get_account_deletion_stage(OWNER) == 2
    progress = {row["image_upload_id"]: row["sweep_count"] for row in rows("account_deletion_objects")}
    assert progress == {"two": 0}
    for method, path in [("GET", "/v1/profiles/me"), ("POST", "/v1/onboarding"),
                         ("POST", "/v1/account"), ("DELETE", f"/v1/profiles/{own}")]:
        blocked = client.request(method, path, headers=headers(), json=ONBOARDING)
        assert blocked.status_code == 403
        assert blocked.json()["detail"]["code"] == "account_deletion_in_progress"
    # An in-flight request that already passed middleware is rejected in the database too.
    with pytest.raises(PersistenceError):
        get_coach_repository().save_profile(cached_profile)
    with pytest.raises(PersistenceError):
        upload("resurrection")
    with pytest.raises(PersistenceError):
        job("resurrection-job", "one")
    with get_analytics_repository()._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("insert into app_users values (?, null, null, null, 'now', 'now')", (OWNER,))
    storage.fail = False
    monkeypatch.setattr(deletion, "get_persistence_repository", lambda: fresh_repository)
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert delete(client).json() == {"status": "deleted"}
    assert deleted.count("fixture/one") == 1
    assert len(admin.calls) == 1
    assert fresh_repository.get_account_deletion_stage(OWNER) == 3


def test_already_authorized_worker_cannot_write_after_cleanup(client):
    own = profile(client)
    cached_profile = get_coach_repository().get_profile(own)
    ready, resume = Event(), Event()

    def in_flight_request():
        assert not deletion.account_access_blocked(OWNER)
        ready.set()
        assert resume.wait(timeout=5)
        with pytest.raises(PersistenceError):
            get_coach_repository().save_profile(cached_profile)
        fresh_repository = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
        assert fresh_repository.get_account_deletion_stage(OWNER) == 3

    with ThreadPoolExecutor(max_workers=1) as executor:
        worker = executor.submit(in_flight_request)
        assert ready.wait(timeout=5)
        assert complete(client).status_code == 200
        resume.set()
        worker.result(timeout=5)
    assert get_coach_repository().get_profile(own) is None


@pytest.mark.parametrize("statement", [
    "insert into coach_events values ('late', 'gone-profile', 'weight', '{}', 'now')",
    "insert into workout_plans values ('late', 'gone-profile', '{}', 'now')",
    "insert into clarifications values ('late', 'gone-job', '{}', '{}', 'now')",
    "insert into meal_logs values ('late', 'gone-job', 'result', 'unknown', '{}', '{}', 'now')",
    "insert into product_events values ('late', null, 'gone-session', null, 'app_opened', 'today', '{}', 'now', 'now')",
])
def test_late_child_writes_cannot_recreate_orphans_when_owner_parent_is_gone(client, statement):
    own = profile(client)
    upload("owned-image")
    job("owned-job", "owned-image", profile_id=own)
    assert complete(client).status_code == 200
    with sqlite3.connect(os.environ["CAL_AI_API_DATA_PATH"]) as separate_connection:
        with pytest.raises(sqlite3.IntegrityError, match="account_deletion_in_progress"):
            separate_connection.execute(statement)


def test_provider_outage_resumes_checkpoints_and_sanitizes(client, admin):
    profile(client)
    admin.responses.append(httpx.Response(503, json={"error": SECRET}))
    response = delete(client)
    assert response.status_code == 202
    assert SECRET not in response.text
    assert response.headers["Retry-After"] == "30"
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    repo = get_persistence_repository()
    assert repo.get_account_deletion_stage(OWNER) == 1
    assert delete(client).json() == {"status": "pending"}
    admin.responses.append(httpx.Response(404, json={"code": "user_not_found"}))
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert delete(client).json() == {"status": "deleted"}
    assert [request.method for request in admin.calls] == ["DELETE", "DELETE"]
    assert repo.get_account_deletion_stage(OWNER) == 3
    monkeypatch_calls = len(admin.calls)
    assert delete(client).json() == {"status": "deleted"}
    assert len(admin.calls) == monkeypatch_calls
    assert client.get("/v1/profiles/me", headers=headers()).status_code == 403
    assert all(option["follow_redirects"] is False for option in admin.options)
    assert all(option["timeout"].read == 8 and option["timeout"].connect == 3 for option in admin.options)
    assert "Authorization" not in admin.calls[0].headers
    assert admin.calls[-1].headers["apikey"] == SECRET
    assert json.loads(admin.calls[-1].content) == {"should_soft_delete": False}


@pytest.mark.parametrize("response", [httpx.Response(401, text=SECRET), httpx.Response(403, text=SECRET),
                                      httpx.Response(404, text=SECRET),
                                      httpx.Response(307, headers={"Location": "https://foreign.invalid"}),
                                      httpx.ReadTimeout(SECRET)])
def test_provider_errors_timeouts_and_redirects_are_not_success(client, admin, response):
    get_coach_repository()
    get_analytics_repository()
    repo = get_persistence_repository()
    repo.prepare_account_deletion()
    repo.begin_account_deletion(OWNER)
    with repo._connection() as conn:
        conn.execute("update account_deletions set stage = 2 where owner_id = ?", (OWNER,))
        conn.execute("update account_deletion_work set phase = 'done' where owner_id = ?", (OWNER,))
    admin.responses.append(response)
    result = delete(client)
    assert result.status_code == 202
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert SECRET not in result.text
    assert repo.get_account_deletion_stage(OWNER) == 2


@pytest.mark.parametrize("expiry", ["2000-01-01T00:00:00+00:00", "2099-01-01T00:00:00+00:00"])
def test_r2_late_put_after_expiry_keeps_manifest_and_repeated_sweeps(client, admin, monkeypatch, expiry):
    repo = get_persistence_repository()
    upload("pending", object_key="fixture/pending", expires=expiry)
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'fixture-namespace'")
    objects = {"fixture/pending"}
    calls = []

    class Storage:
        provider = "r2"

        def storage_namespace(self):
            return "fixture-namespace"

        def delete_object(self, *, object_key):
            calls.append(object_key)
            objects.discard(object_key)

    monkeypatch.setattr(deletion, "get_storage_adapter", Storage)
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["pending"] == 1
    assert objects == set()
    # A PUT authorized before expiry finishes after the first successful DELETE.
    objects.add("fixture/pending")
    with repo._connection() as conn:
        conn.execute("update account_deletion_work set next_attempt_at = null")
    assert deletion.run_account_deletion_jobs()["pending"] == 1
    assert objects == set() and len(calls) == 2
    assert len(admin.calls) == 1
    assert repo.get_account_deletion_stage(OWNER) == 2
    assert rows("account_deletion_objects")[0]["sweep_count"] == 2
    assert delete(client).json() == {"status": "pending"}


def test_persistence_outage_cannot_bypass_gate(client, monkeypatch):
    def unavailable():
        raise PersistenceError(SECRET)

    monkeypatch.setattr(deletion, "get_persistence_repository", unavailable)
    response = client.get("/v1/profiles/me", headers=headers())
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "account_state_unavailable"
    response = delete(client)
    assert response.status_code == 503
    assert SECRET not in response.text


def test_analytics_partial_outage_retries_without_restoring_profile(client, monkeypatch):
    own = profile(client)
    analytics = get_analytics_repository()
    repo = get_persistence_repository()
    original = repo.process_account_deletion_batch

    def fail_analytics(owner_id, lease_token, **kwargs):
        if rows("account_deletion_work")[0]["phase"] == "events":
            raise PersistenceError(SECRET)
        return original(owner_id, lease_token, **kwargs)

    monkeypatch.setattr(repo, "process_account_deletion_batch", fail_analytics)
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert get_coach_repository().get_profile(own)
    assert get_persistence_repository().get_account_deletion_stage(OWNER) == 0
    monkeypatch.setattr(repo, "process_account_deletion_batch", original)
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert delete(client).status_code == 200


def test_deleted_retry_succeeds_without_config_or_admin_calls(client, admin, monkeypatch):
    assert complete(client).status_code == 200
    monkeypatch.delenv("SUPABASE_SECRET_KEY")
    assert delete(client).json() == {"status": "deleted"}
    assert len(admin.calls) == 1
    assert SECRET not in repr(deletion.SupabaseAccountAdmin("https://fixture.supabase.co", SECRET))


def test_provider_success_followed_by_checkpoint_outage_is_retryable(client, admin, monkeypatch):
    repo = get_persistence_repository()
    original = repo.mark_account_identity_deleted

    def fail_checkpoint(owner_id, **kwargs):
        raise PersistenceError(SECRET)

    monkeypatch.setattr(repo, "mark_account_identity_deleted", fail_checkpoint)
    first = delete(client)
    assert first.status_code == 202 and SECRET not in first.text
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert repo.get_account_deletion_stage(OWNER) == 1
    monkeypatch.setattr(repo, "mark_account_identity_deleted", original)
    admin.responses.append(httpx.Response(404, json={"code": "user_not_found"}))
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert delete(client).json() == {"status": "deleted"}
    assert repo.get_account_deletion_stage(OWNER) == 3


def test_profile_a_deletion_preserves_same_owner_b_and_foreign_c(client, monkeypatch):
    profiles = [profile(client), profile(client), profile(client, FOREIGN)]
    repo = get_persistence_repository()
    deleted_keys = []
    monkeypatch.setattr("app.coach_routes.get_storage_adapter", lambda: SimpleNamespace(
        provider="local", delete_object=lambda **kwargs: deleted_keys.append(kwargs["object_key"]),
    ))
    for label, profile_id, owner in zip("abc", profiles, [OWNER, OWNER, FOREIGN], strict=True):
        upload(label, owner, object_key=f"fixture/{label}")
        upload(f"body-{label}", owner, object_key=f"fixture/body-{label}")
        job(f"job-{label}", label, owner, profile_id)
        repo.save_meal_log(
            payload=MealLogRequest(analysis_job_id=f"job-{label}", result_id="result",
                                   clarification_value="unknown", profile_id=profile_id),
            response=SavedImpactResponse(confirmation="saved", remaining_calories_kcal=100,
                                         next_meal_suggestion="fixture", dashboard=main.dashboard_today()),
            meal_log_id=f"log-{label}",
        )
        with repo._connection() as conn:
            conn.execute("insert into clarifications values (?, ?, '{}', '{}', 'now')",
                         (f"clarification-{label}", f"job-{label}"))
        get_coach_repository().save_body_check_in(BodyCheckInResponse(
            id=f"event-{label}", profile_id=profile_id, captured_on="2026-11-09",
            image_upload_id=f"body-{label}", view="front", created_at="now",
            analysis={"provider": "mock", "confidence": "limited", "capture_quality": "good",
                      "observations": [], "training_focus": [], "comparison_note": "fixture", "safety_note": "fixture"},
        ))
    # A same-owner orphan is not profile A's artifact, either.
    upload("owner-orphan", object_key="fixture/owner-orphan")
    response = client.delete(f"/v1/profiles/{profiles[0]}", headers=headers())
    assert response.status_code == 200
    assert set(deleted_keys) == {"fixture/a", "fixture/body-a"}
    assert {row["analysis_job_id"] for row in rows("analysis_jobs")} == {"job-b", "job-c"}
    assert {row["meal_log_id"] for row in rows("meal_logs")} == {"log-b", "log-c"}
    assert {row["clarification_id"] for row in rows("clarifications")} == {"clarification-b", "clarification-c"}
    assert {row["image_upload_id"] for row in rows("image_uploads")} == {
        "b", "c", "body-b", "body-c", "owner-orphan",
    }
    assert get_coach_repository().get_profile(profiles[1]).owner_id == OWNER
    assert get_coach_repository().get_profile(profiles[2]).owner_id == FOREIGN


@pytest.mark.parametrize("unsafe_first", [True, False])
@pytest.mark.parametrize("failure", [
    "ownerless", "ownerless_without_key", "missing_key", "provider",
    "missing_namespace", "blank_namespace", "namespace_mismatch",
])
def test_profile_image_preflight_rejects_entire_set_before_side_effects(
    client, monkeypatch, unsafe_first, failure,
):
    own = profile(client)
    repo = get_persistence_repository()
    for label in ("valid", "unsafe"):
        upload(label, object_key=f"private-fixture/{label}")
        job(f"job-{label}", label, profile_id=own)
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'private-namespace'")
        if failure.startswith("ownerless"):
            conn.execute("update image_uploads set owner_id = null where image_upload_id = 'unsafe'")
        if failure in {"missing_key", "ownerless_without_key"}:
            conn.execute("update image_uploads set object_key = null where image_upload_id = 'unsafe'")
        if failure == "provider":
            conn.execute("update image_uploads set storage_provider = 'other-remote' where image_upload_id = 'unsafe'")
        if failure in {"missing_namespace", "blank_namespace", "namespace_mismatch"}:
            namespace = {"missing_namespace": None, "blank_namespace": " ", "namespace_mismatch": "other-private-namespace"}[failure]
            conn.execute("update image_uploads set storage_namespace = ? where image_upload_id = 'unsafe'", (namespace,))
    get_analytics_repository()
    repo.prepare_account_deletion()
    for flag in ("ACCOUNT_DELETION_ENABLED", "ACCOUNT_DELETION_WORKER_ENABLED", "R2_WRITE_ONCE_UPLOADS_ENABLED"):
        monkeypatch.setenv(flag, "false")
    selected = repo.list_profile_image_uploads(own, owner_id=OWNER)
    assert {record.image_upload_id for record in selected} == {"valid", "unsafe"}
    selected.sort(key=lambda record: (record.image_upload_id == "unsafe") != unsafe_first)
    monkeypatch.setattr(repo, "list_profile_image_uploads", lambda *a, **kw: selected)
    tables = ("image_uploads", "analysis_jobs", "coach_profiles", "account_deletions")
    before = {table: rows(table) for table in tables}
    photos = {record.object_key for record in selected if record.object_key}
    original_photos = photos.copy()
    effects = []
    original_mark = repo.mark_image_upload_deleting

    def mark(upload_id):
        effects.append(("mark", upload_id))
        return original_mark(upload_id)

    def erase(*, object_key):
        effects.append(("delete", object_key))
        photos.discard(object_key)

    monkeypatch.setattr(repo, "mark_image_upload_deleting", mark)
    monkeypatch.setattr("app.coach_routes.get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "private-namespace", delete_object=erase,
    ))
    response = client.delete(f"/v1/profiles/{own}", headers=headers())
    assert effects == []
    assert photos == original_photos
    assert {table: rows(table) for table in tables} == before
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "profile_image_verification_required"
    assert response.json()["detail"]["retryable"] is False
    for private in ("private-fixture", "private-namespace", "other-remote", OWNER):
        assert private not in response.text


@pytest.mark.parametrize("object_key", [None, "fixture/local"])
def test_profile_image_preflight_preserves_ownerless_local_fallback(client, monkeypatch, object_key):
    own = profile(client)
    upload("local-legacy", None, object_key=object_key)
    job("local-job", "local-legacy", None, own)
    get_analytics_repository()
    get_persistence_repository().prepare_account_deletion()
    deleted_keys = []
    monkeypatch.setattr("app.coach_routes.get_storage_adapter", lambda: SimpleNamespace(
        provider="local", delete_object=lambda **kw: deleted_keys.append(kw["object_key"]),
    ))
    response = client.delete(f"/v1/profiles/{own}", headers=headers())
    assert response.status_code == 200
    assert deleted_keys == ([object_key] if object_key else [])
    assert get_persistence_repository().get_image_upload("local-legacy") is None


def test_profile_image_preflight_allows_verified_owned_remote_scoped_deletion(client, monkeypatch):
    own, retained = profile(client), profile(client)
    repo = get_persistence_repository()
    for label, profile_id in (("selected", own), ("retained", retained)):
        upload(label, object_key=f"fixture/{label}")
        job(f"job-{label}", label, profile_id=profile_id)
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'fixture-namespace'")
    get_analytics_repository()
    repo.prepare_account_deletion()
    deleted_keys = []
    monkeypatch.setattr("app.coach_routes.get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "fixture-namespace",
        delete_object=lambda **kw: deleted_keys.append(kw["object_key"]),
    ))
    response = client.delete(f"/v1/profiles/{own}", headers=headers())
    assert response.status_code == 200
    assert deleted_keys == ["fixture/selected"]
    assert repo.get_image_upload("selected") is None
    assert repo.get_image_upload("retained") is not None
    assert get_coach_repository().get_profile(retained).owner_id == OWNER


def test_profile_shared_upload_and_foreign_job_links_are_not_delete_authority(client):
    a, b = profile(client), profile(client)
    upload("shared")
    upload("foreign-image", FOREIGN)
    job("a", "shared", OWNER, a)
    job("b", "shared", OWNER, b)
    job("foreign", "foreign-image", FOREIGN, a)
    repo = get_persistence_repository()
    assert repo.list_profile_image_uploads(a, owner_id=OWNER) == []
    repo.delete_profile_artifacts(a, owner_id=OWNER)
    assert {row["analysis_job_id"] for row in rows("analysis_jobs")} == {"b", "foreign"}
    assert {row["image_upload_id"] for row in rows("image_uploads")} == {"shared", "foreign-image"}


def test_profile_body_without_jobs_cannot_delete_b_upload(client):
    a, b = profile(client), profile(client)
    upload("b-image")
    job("b-job", "b-image", OWNER, b)
    repo = get_persistence_repository()
    assert repo.list_profile_image_uploads(a, owner_id=OWNER, additional_image_upload_ids=["b-image"]) == []
    repo.delete_profile_artifacts(a, owner_id=OWNER, additional_image_upload_ids=["b-image"])
    assert repo.get_image_upload("b-image") is not None
    assert repo.get_analysis_job("b-job") is not None


def test_durable_worker_resumes_after_actual_jwt_expiry_without_client(admin, monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.now(UTC)
    claims = {"iss": "https://fixture.supabase.co/auth/v1", "aud": "authenticated", "sub": OWNER,
              "exp": now + timedelta(minutes=1)}
    token = jwt.encode(claims, key, algorithm="ES256")
    monkeypatch.setenv("SUPABASE_JWT_ALGORITHM", "ES256")
    monkeypatch.setattr(auth, "_jwk_client", lambda issuer: SimpleNamespace(
        get_signing_key_from_jwt=lambda value: SimpleNamespace(key=key.public_key()),
    ))
    admin.responses.append(httpx.Response(503, text=SECRET))
    get_coach_repository()
    get_analytics_repository()
    get_persistence_repository().prepare_account_deletion()
    with TestClient(main.app) as authenticated_client:
        request_headers = {"Authorization": f"Bearer {token}"}
        accepted = authenticated_client.request("DELETE", "/v1/account", headers=request_headers, json={"confirm": True})
        assert accepted.status_code == 202
        assert deletion.run_account_deletion_jobs()["failed"] == 1

        class ExpiredClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return now + timedelta(minutes=2)

        monkeypatch.setattr(jwt.api_jwt, "datetime", ExpiredClock)
        retry = authenticated_client.request("DELETE", "/v1/account", headers=request_headers, json={"confirm": True})
        assert retry.status_code == 401
    # No client, no user token, and a new repository instance after the outage.
    repo = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
    monkeypatch.setattr(deletion, "get_persistence_repository", lambda: repo)
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert repo.get_account_deletion_stage(OWNER) == 3
    assert all("Authorization" not in request.headers and request.headers["apikey"] == SECRET for request in admin.calls)
    for table in ("account_deletions", "account_deletion_work", "account_deletion_objects"):
        assert token not in json.dumps(rows(table))


def test_bounded_object_progress_resumes_with_fresh_repository(client, monkeypatch):
    for index in range(7):
        upload(str(index), object_key=f"fixture/{index}")
    calls = []
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="local", delete_object=lambda **kwargs: calls.append(kwargs["object_key"]),
    ))
    assert delete(client).status_code == 202
    for expected in (2, 4, 6):
        assert deletion.run_account_deletion_jobs(max_objects=2)["pending"] == 1
        assert len(calls) == expected
        fresh = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
        monkeypatch.setattr(deletion, "get_persistence_repository", lambda: fresh)
    assert deletion.run_account_deletion_jobs(max_objects=2)["deleted"] == 1
    assert len(calls) == len(set(calls)) == 7


def test_local_adapter_objects_can_complete_without_external_put_gate(client):
    upload("local", object_key="fixture/local", expires="2099-01-01T00:00:00+00:00")
    assert complete(client).status_code == 200


def test_unknown_remote_key_never_reports_complete(client):
    upload("unknown")
    with get_persistence_repository()._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', upload_status = 'deleted'")
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["pending"] == 1
    assert rows("account_deletion_work")[0]["storage_uncertain"] == 1
    assert delete(client).json() == {"status": "pending"}


def test_acceptance_manifest_failure_rolls_back_tombstone(client, monkeypatch):
    upload("one", object_key="fixture/one")
    repo = get_persistence_repository()
    monkeypatch.setattr(repo, "_save_account_deletion_objects", lambda *args: (_ for _ in ()).throw(PersistenceError(SECRET)))
    response = delete(client)
    assert response.status_code == 202 and response.json() == {"status": "pending"}
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert repo.get_account_deletion_stage(OWNER) == 0
    assert repo.get_image_upload("one") is not None


def test_r2_pending_job_does_not_monopolize_fair_queue(client, monkeypatch):
    upload("remote", object_key="fixture/remote")
    with get_persistence_repository()._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'fixture-namespace'")
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "fixture-namespace", delete_object=lambda **kwargs: None,
    ))
    assert delete(client).status_code == 202
    assert delete(client, FOREIGN).status_code == 202
    assert deletion.run_account_deletion_jobs()["pending"] == 1
    with get_persistence_repository()._connection() as conn:
        conn.execute("update account_deletion_work set next_attempt_at = null")
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    assert get_persistence_repository().get_account_deletion_stage(FOREIGN) == 3
    assert get_persistence_repository().get_account_deletion_stage(OWNER) == 2


def test_lease_excludes_concurrent_workers_and_recovers_abandoned_claim(client):
    assert delete(client).status_code == 202
    repo = get_persistence_repository()
    assert repo.claim_account_deletion(OWNER, "old")
    assert not repo.claim_account_deletion(OWNER, "other")
    assert deletion.run_account_deletion_jobs()["processed"] == 0
    with repo._connection() as conn:
        conn.execute("update account_deletion_work set lease_until = '2000-01-01T00:00:00+00:00'")
    assert repo.claim_account_deletion(OWNER, "new")
    assert not repo.account_deletion_lease_current(OWNER, "old")
    repo.release_account_deletion(OWNER, "old")
    assert repo.account_deletion_lease_current(OWNER, "new")
    repo.release_account_deletion(OWNER, "new")
    assert deletion.run_account_deletion_jobs()["deleted"] == 1


def test_lost_lease_does_not_checkpoint_object_success(client, monkeypatch):
    upload("one", object_key="fixture/one")
    repo = get_persistence_repository()

    def lose_lease(**kwargs):
        with repo._connection() as conn:
            conn.execute("update account_deletion_work set lease_token = 'replacement'")

    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(provider="local", delete_object=lose_lease))
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert rows("account_deletion_objects")[0]["sweep_count"] == 0
    assert rows("account_deletion_work")[0]["lease_token"] == "replacement"


def test_stage_zero_budget_interruption_retains_manifest_and_resumes(client, monkeypatch):
    profile(client)
    upload("one", object_key="fixture/one")
    assert delete(client).status_code == 202
    repo = get_persistence_repository()
    original = repo.process_account_deletion_batch
    clock = [0.0]

    def slow_database(*args, **kwargs):
        done = original(*args, **kwargs)
        clock[0] = 10.0
        return done

    monkeypatch.setattr(deletion, "monotonic", lambda: clock[0])
    monkeypatch.setattr(repo, "process_account_deletion_batch", slow_database)
    assert deletion.run_account_deletion_jobs(budget_seconds=1)["pending"] == 1
    assert repo.get_account_deletion_stage(OWNER) == 0
    assert repo.get_image_upload("one") is not None
    monkeypatch.setattr(repo, "process_account_deletion_batch", original)
    assert deletion.run_account_deletion_jobs()["deleted"] == 1


@pytest.mark.parametrize("values", [{"budget_seconds": 0}, {"budget_seconds": 46}, {"max_jobs": 0}, {"max_objects": 26}])
def test_worker_rejects_unbounded_parameters(values):
    with pytest.raises(ValueError, match="invalid_account_deletion_batch"):
        deletion.run_account_deletion_jobs(**values)


def test_worker_router_requires_secret_and_never_accepts_owner_selector(client, admin, monkeypatch):
    assert client.get("/internal/account-deletions/run").status_code == 401
    assert client.get("/internal/account-deletions/run", headers=headers()).status_code == 401
    cron_headers = {"Authorization": f"Bearer {CRON_SECRET}"}
    assert client.post("/internal/account-deletions/run?owner_id=" + FOREIGN, headers=cron_headers).status_code == 422
    assert delete(client).status_code == 202
    response = client.get("/internal/account-deletions/run", headers=cron_headers)
    assert response.json() == {"processed": 1, "deleted": 1, "pending": 0, "failed": 0}
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    assert client.get("/internal/account-deletions/run", headers=cron_headers).status_code == 503
    assert len(admin.calls) == 1


def test_postgres_schema_guards_and_checkpoint_sql_are_server_side(monkeypatch):
    statements = []
    tables = ["image_uploads", "analysis_jobs", "coach_profiles", "coach_events", "workout_plans",
              "clarifications", "meal_logs", "app_users", "app_sessions", "product_events",
              "billing_subscriptions", "billing_payments"]

    class Cursor:
        rowcount = 1

        def __init__(self, statement):
            self.statement = statement

        def fetchone(self):
            if "select version" in self.statement:
                return {"version": PostgresPersistenceRepository._account_guard_version}
            if "select * from account_deletion_work" in self.statement:
                return {"phase": "done", "cursor": "", "identity_deleted": 1, "storage_uncertain": 0}
            if "select stage" in self.statement:
                return {"stage": 2}
            if "select storage_uncertain" in self.statement:
                return {"storage_uncertain": 0}
            return None

        def fetchall(self):
            return [{"name": table} for table in tables] if "pg_tables" in self.statement else []

    class Connection:
        def execute(self, statement, parameters=()):
            statements.append((statement, parameters))
            return Cursor(statement)

    @contextmanager
    def connection(self):
        yield Connection()

    monkeypatch.setattr(PostgresPersistenceRepository, "_connection", connection)
    repo = PostgresPersistenceRepository("postgresql://unused-disposable-fixture")
    repo._install_account_write_guards(Connection())
    repo.begin_account_deletion(OWNER)
    repo.advance_account_deletion(OWNER, 3, lease_token="lease-fixture")
    repo.delete_profile_artifacts("owned-profile", owner_id=OWNER)
    repo.list_pending_account_deletions(1)
    repo.claim_account_deletion(OWNER, "lease-fixture")
    repo.release_account_deletion(OWNER, "lease-fixture")
    repo.mark_account_identity_deleted(OWNER, lease_token="lease-fixture")
    repo.list_account_deletion_objects(OWNER, 5)
    repo.mark_account_deletion_object_swept(OWNER, "image-fixture", lease_token="lease-fixture")
    sql = "\n".join(statement for statement, _ in statements)
    assert "create table if not exists account_deletions" in sql
    assert "lock table coach_profiles in share row exclusive mode" in sql
    assert "security invoker" in sql and "security definer" not in sql
    assert "revoke all on account_deletions from authenticated" in sql
    assert "revoke all on function account_guard_coach_profiles() from public" in sql
    assert "before insert or update" in sql
    assert "payload_json::jsonb ->> 'owner_id'" in sql
    assert "request_json::jsonb ->> 'profile_id'" in sql
    assert "insert into account_owner_state" in sql
    assert "for update" in sql
    assert "before insert or update or delete" in sql
    assert "clock_timestamp()" in sql
    assert "set transaction isolation level read committed" in sql
    assert "create table if not exists account_deletion_objects" in sql
    assert "alter table account_deletion_objects enable row level security" in sql
    assert "revoke all on account_deletion_work from authenticated" in sql
    assert "where (j.owner_id = %s or j.owner_id is null)" in sql
    assert "order by sweep_count" in sql and "limit %s" in sql
    assert "where owner_id = %s and lease_token = %s" in sql
    assert all(" in (" not in spec[2] for spec in repo._account_batch_specs().values())
    assert "?" not in sql
    assert any(parameters == (OWNER, "owned-profile", "owned-profile", "owned-profile") for _, parameters in statements)
