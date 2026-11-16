import json
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from threading import Event
from time import monotonic, sleep
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import coach_routes
from app.admin_schemas import AnalyticsEventRequest
from app.coach_schemas import BodyCheckInResponse, CoachProfile
from app.schemas import AnalysisJobCreateResponse, AnalysisJobRequest, ImageUploadRequest
from app.services import account_deletion as deletion
from app.services.analytics_repository import PRIVACY_CONSENT_VERSION, get_analytics_repository
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from test_account_deletion import OWNER, FOREIGN, ONBOARDING, admin


NAMESPACE = "r2-v1:" + "a" * 64


@pytest.fixture(params=["sqlite", "postgres"])
def inventory(request, monkeypatch, admin):
    dsn = None
    if request.param == "postgres":
        base = os.environ.get("CAL_AI_TEST_PG_DSN", "")
        if not base:
            pytest.skip("CAL_AI_TEST_PG_DSN is required for isolated PostgreSQL evidence")
        psycopg = pytest.importorskip("psycopg")
        from psycopg import sql

        parsed = urlsplit(base)
        query = dict(parse_qsl(parsed.query))
        if parsed.hostname or query.get("host") != "/private/tmp" or parsed.path != "/postgres":
            pytest.fail("Only the isolated Unix-socket test cluster is allowed")
        schema = "erasure_test_" + uuid4().hex
        with psycopg.connect(base, autocommit=True) as conn:
            conn.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))
        query["options"] = "-csearch_path=" + schema
        dsn = urlunsplit(parsed._replace(netloc="localhost", query=urlencode(query)))
        monkeypatch.setenv("DATABASE_URL", dsn)

    try:
        meals = get_persistence_repository()
        coach = get_coach_repository()
        get_analytics_repository()
        meals.prepare_account_deletion()
        storage = SimpleNamespace(
            provider="r2", storage_namespace=Mock(return_value=NAMESPACE),
            erase_account_object=Mock(return_value=True), delete_object=Mock(), stat_object=Mock(),
        )
        monkeypatch.setattr(deletion, "get_storage_adapter", lambda: storage)
        monkeypatch.setattr(coach_routes, "get_storage_adapter", lambda: storage)

        def profile(label, owner=OWNER):
            coach.save_profile(CoachProfile(
                profile_id=label, owner_id=owner, created_at="2026-11-16T00:00:00+00:00",
                onboarding=ONBOARDING,
                target={"calories_kcal": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 60},
            ))
            return label

        def upload(profile_id=None, *, owner=OWNER, key=None, provider="r2", namespace=NAMESPACE):
            image_id = "image-upload-" + str(uuid4())
            key = key if key is not None else f"uploads/{image_id}/sealed-v1/image.jpg"
            record = meals.save_image_upload(
                payload=ImageUploadRequest(
                    local_asset_id=image_id, file_name="fixture.jpg", content_type="image/jpeg", byte_size=12,
                ),
                image_upload_id=image_id, image_reference=f"r2://fixture/{key}",
                object_key=key, storage_provider=provider, storage_namespace=namespace, owner_id=owner,
            )
            if profile_id is not None:
                meals.save_analysis_job(
                    payload=AnalysisJobRequest(image_upload_id=image_id, profile_id=profile_id),
                    image_reference=record.image_reference, owner_id=owner,
                    create_response=AnalysisJobCreateResponse(analysis_job_id="job-" + image_id, status="queued"),
                )
            return record

        def consent(owner=OWNER):
            with meals._connection() as conn:
                conn.execute(meals._account_sql(
                    "insert into privacy_consents (owner_id, policy_version, health_data_consent, "
                    "analytics_consent, consented_at) values (?, 'fixture-v1', 1, 0, '2026-11-16')"
                ), (owner,))

        app = FastAPI()
        app.include_router(coach_routes.router)

        @app.middleware("http")
        async def fixture_auth(request: Request, call_next):
            request.state.user_id = OWNER
            return await call_next(request)

        with TestClient(app) as client:
            yield SimpleNamespace(
                meals=meals, coach=coach, storage=storage, admin=admin, client=client,
                profile=profile, upload=upload, consent=consent, dsn=dsn,
            )
    finally:
        if dsn is not None:
            with psycopg.connect(base, autocommit=True) as conn:
                conn.execute(sql.SQL("drop schema {} cascade").format(sql.Identifier(schema)))


@pytest.mark.parametrize("failure", [
    "legacy", "provider", "namespace", "missing_namespace", "missing_key",
    "ownerless", "foreign_owner", "key_binding", "missing_erase",
])
def test_account_rejects_entire_unsafe_inventory_before_acceptance(inventory, failure):
    own = inventory.profile("selected")
    inventory.consent()
    valid = inventory.upload()
    unsafe = inventory.upload(own, owner=None if failure == "ownerless" else OWNER)
    changes = {
        "legacy": ("object_key", "uploads/legacy/image.jpg"),
        "provider": ("storage_provider", "unsupported-remote"),
        "namespace": ("storage_namespace", "other-namespace"),
        "missing_namespace": ("storage_namespace", None),
        "missing_key": ("object_key", None),
        "foreign_owner": ("owner_id", FOREIGN),
        "key_binding": ("object_key", valid.object_key),
    }
    if failure in changes:
        column, value = changes[failure]
        with inventory.meals._connection() as conn:
            conn.execute(inventory.meals._account_sql(
                f"update image_uploads set {column} = ? where image_upload_id = ?"
            ), (value, unsafe.image_upload_id))
    if failure == "missing_erase":
        inventory.storage.erase_account_object = None

    with pytest.raises(deletion.AccountDeletionError, match="account_deletion_storage_unavailable"):
        deletion.delete_account(OWNER)

    assert inventory.meals.get_account_deletion_stage(OWNER) is None
    assert inventory.meals.get_image_upload(unsafe.image_upload_id) is not None
    assert inventory.coach.get_profile(own) is not None
    with inventory.meals._connection() as conn:
        assert conn.execute("select 1 from account_owner_state where deleting = 1").fetchone() is None
        assert conn.execute("select 1 from privacy_consents").fetchone() is not None
    assert inventory.admin.calls == []
    inventory.storage.delete_object.assert_not_called()
    inventory.storage.stat_object.assert_not_called()
    if callable(inventory.storage.erase_account_object):
        inventory.storage.erase_account_object.assert_not_called()


def test_account_verified_orphan_pending_and_deleted_inventory_completes(inventory):
    records = [inventory.upload() for _ in range(3)]
    with inventory.meals._connection() as conn:
        for record, status in zip(records, ("pending", "ready", "deleted")):
            conn.execute(inventory.meals._account_sql(
                "update image_uploads set upload_status = ? where image_upload_id = ?"
            ), (status, record.image_upload_id))
    inventory.consent()
    inventory.consent(FOREIGN)

    assert deletion.delete_account(OWNER) == "pending"
    inventory.storage.erase_account_object.assert_not_called()
    assert inventory.admin.calls == []
    assert deletion.run_account_deletion_jobs(max_objects=5)["deleted"] == 1
    assert {call.kwargs["object_key"] for call in inventory.storage.erase_account_object.call_args_list} == {
        record.object_key for record in records
    }
    assert len(inventory.admin.calls) == 1
    with inventory.meals._connection() as conn:
        assert [row["owner_id"] for row in conn.execute("select owner_id from privacy_consents").fetchall()] == [FOREIGN]
    with pytest.raises(PersistenceError):
        inventory.consent()
    inventory.storage.delete_object.assert_not_called()


def test_existing_unsupported_accepted_job_does_not_delete_identity_or_source(inventory):
    record = inventory.upload(key="uploads/legacy/image.jpg")
    inventory.meals.begin_account_deletion(OWNER, validate_uploads=lambda target: None)
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert inventory.meals.get_account_deletion_stage(OWNER) == 0
    assert inventory.meals.get_image_upload(record.image_upload_id) == record
    assert inventory.admin.calls == []
    inventory.storage.erase_account_object.assert_not_called()


def test_old_manifest_without_owner_provenance_cannot_delete_identity(inventory):
    record = inventory.upload()
    meals = inventory.meals
    meals.begin_account_deletion(OWNER, validate_uploads=lambda target: None)
    assert meals.claim_account_deletion(OWNER, "fixture-worker")
    for _ in range(80):
        if meals.process_account_deletion_batch(OWNER, "fixture-worker"):
            break
    assert meals.get_account_deletion_stage(OWNER) == 1
    with meals._connection() as conn:
        conn.execute("update account_deletion_objects set upload_owner_id = null")
    meals.release_account_deletion(OWNER, "fixture-worker")

    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert meals.get_account_deletion_stage(OWNER) == 1
    assert meals.list_account_deletion_objects(OWNER, 5)[0]["object_key"] == record.object_key
    assert inventory.admin.calls == []


def test_old_uncertain_inventory_cannot_delete_identity(inventory):
    meals = inventory.meals
    meals.begin_account_deletion(OWNER)
    with meals._connection() as conn:
        conn.execute("update account_deletions set stage = 1")
        conn.execute("update account_deletion_work set phase = 'done', storage_uncertain = 1")
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert meals.get_account_deletion_stage(OWNER) == 1
    assert inventory.admin.calls == []


def test_acceptance_validates_after_inflight_owner_writer_commits(inventory):
    record = inventory.upload()
    started = Event()
    with inventory.meals._connection() as writer:
        writer.execute(inventory.meals._account_sql(
            "update image_uploads set object_key = 'uploads/legacy/image.jpg' where image_upload_id = ?"
        ), (record.image_upload_id,))
        with ThreadPoolExecutor(max_workers=1) as executor:
            def accept():
                started.set()
                return deletion.delete_account(OWNER)

            future = executor.submit(accept)
            assert started.wait(2)
            try:
                with pytest.raises(TimeoutError):
                    future.result(timeout=0.1)
                if inventory.dsn:
                    inventory.upload(owner=FOREIGN)
            finally:
                writer.commit()
            with pytest.raises(deletion.AccountDeletionError):
                future.result(timeout=5)
    assert inventory.meals.get_account_deletion_stage(OWNER) is None
    assert inventory.admin.calls == []


def test_remote_acceptance_cannot_omit_validator(inventory):
    inventory.upload()
    with pytest.raises(PersistenceError, match="account_deletion_inventory_unverified"):
        inventory.meals.begin_account_deletion(OWNER)
    assert inventory.meals.get_account_deletion_stage(OWNER) is None


def test_acceptance_holds_owner_fence_between_validation_and_tombstone(inventory):
    inventory.upload()
    validating, finish = Event(), Event()
    validator = deletion._erasure_inventory_validator(OWNER, lambda: inventory.storage)

    def validate(target):
        validator(target)
        validating.set()
        assert finish.wait(5)

    with ThreadPoolExecutor(max_workers=2) as executor:
        accepted = executor.submit(inventory.meals.begin_account_deletion, OWNER, validate_uploads=validate)
        assert validating.wait(2)
        late = executor.submit(inventory.upload)
        try:
            with pytest.raises(TimeoutError):
                late.result(timeout=0.1)
            if inventory.dsn:
                inventory.upload(owner=FOREIGN)
        finally:
            finish.set()
        assert accepted.result(timeout=5) == 0
        with pytest.raises(PersistenceError):
            late.result(timeout=5)


@pytest.mark.parametrize("after_batch", [False, True])
def test_worker_rechecks_namespace_before_cleanup_and_identity(inventory, after_batch):
    record = inventory.upload()
    meals = inventory.meals
    assert deletion.delete_account(OWNER) == "pending"
    if after_batch:
        assert meals.claim_account_deletion(OWNER, "fixture-worker")
        for _ in range(80):
            if meals.process_account_deletion_batch(OWNER, "fixture-worker"):
                break
        assert meals.get_account_deletion_stage(OWNER) == 1
        meals.release_account_deletion(OWNER, "fixture-worker")
    inventory.storage.storage_namespace.return_value = "other-namespace"
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert inventory.admin.calls == []
    inventory.storage.erase_account_object.assert_not_called()
    assert meals.get_account_deletion_stage(OWNER) == int(after_batch)
    if not after_batch:
        assert meals.get_image_upload(record.image_upload_id) is not None


def test_profile_metadata_commit_fences_late_upload_writer(inventory, monkeypatch):
    own = inventory.profile("selected")
    verified = inventory.upload(own)
    deleting, finish = Event(), Event()
    original_connection = inventory.meals._connection

    @contextmanager
    def connection():
        with original_connection() as conn:
            class Connection:
                def execute(self, statement, parameters=()):
                    if statement.startswith("delete from meal_logs where"):
                        deleting.set()
                        assert finish.wait(5)
                    return conn.execute(statement, parameters)
            yield Connection()

    monkeypatch.setattr(inventory.meals, "_connection", connection)
    with ThreadPoolExecutor(max_workers=2) as executor:
        removed = executor.submit(
            inventory.meals.delete_profile_artifacts, own,
            owner_id=OWNER, expected_uploads=[verified],
        )
        assert deleting.wait(2)
        late = executor.submit(inventory.upload, own, key="uploads/unverified/image.jpg")
        try:
            with pytest.raises(TimeoutError):
                late.result(timeout=0.1)
        finally:
            finish.set()
        assert [record.image_upload_id for record in removed.result(timeout=5)] == [verified.image_upload_id]
        unverified = late.result(timeout=5)
    assert inventory.meals.get_image_upload(verified.image_upload_id) is None
    assert inventory.meals.get_image_upload(unverified.image_upload_id) == unverified


@pytest.mark.parametrize("race", ["job", "body", "provenance"])
def test_profile_inventory_change_during_erasure_preserves_all_metadata(inventory, race):
    own = inventory.profile("selected")
    original = inventory.upload(own)
    inventory.consent()
    added = []

    def erase(**kwargs):
        if race == "provenance":
            with inventory.meals._connection() as conn:
                conn.execute(inventory.meals._account_sql(
                    "update image_uploads set object_key = 'uploads/unverified/image.jpg' where image_upload_id = ?"
                ), (original.image_upload_id,))
        else:
            added.append(inventory.upload(own if race == "job" else None, key="uploads/legacy/image.jpg"))
            if race == "body":
                inventory.coach.save_body_check_in(BodyCheckInResponse(
                    id="body-fixture", profile_id=own, image_upload_id=added[0].image_upload_id,
                    captured_on="2026-11-16", view="front",
                    analysis={
                        "provider": "mock", "confidence": "limited", "capture_quality": "good",
                        "observations": [], "training_focus": [], "comparison_note": "fixture",
                        "safety_note": "fixture",
                    },
                    created_at="2026-11-16T00:00:00+00:00",
                ))
        return True

    inventory.storage.erase_account_object.side_effect = erase
    response = inventory.client.delete(f"/v1/profiles/{own}")
    assert response.status_code == 503
    assert inventory.coach.get_profile(own) is not None
    assert inventory.meals.get_image_upload(original.image_upload_id) is not None
    assert all(inventory.meals.get_image_upload(record.image_upload_id) is not None for record in added)
    assert inventory.meals.get_analysis_job("job-" + original.image_upload_id) is not None
    with inventory.meals._connection() as conn:
        assert conn.execute("select 1 from privacy_consents").fetchone() is not None


def test_profile_erasure_does_not_delete_account_consent(inventory):
    own = inventory.profile("selected")
    inventory.upload(own)
    inventory.consent()
    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    with inventory.meals._connection() as conn:
        assert conn.execute("select owner_id from privacy_consents").fetchone()["owner_id"] == OWNER


@pytest.mark.parametrize("inventory", ["postgres"], indirect=True)
def test_postgres_profile_erasure_rejects_parent_writer_then_retries(inventory):
    own = inventory.profile("contended-profile")
    record = inventory.upload(own)
    with inventory.meals._connection() as writer, ThreadPoolExecutor(max_workers=1) as pool:
        writer.execute("select 1 from coach_profiles where profile_id = %s for share", (own,)).fetchone()
        removed = pool.submit(inventory.client.delete, f"/v1/profiles/{own}")
        try:
            response = removed.result(timeout=1.5)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "persistence_unavailable"
            inventory.storage.erase_account_object.assert_not_called()
            inventory.storage.delete_object.assert_not_called()
            assert inventory.coach.get_profile(own) is not None
            assert inventory.meals.get_image_upload(record.image_upload_id) == record
            assert inventory.meals.get_analysis_job("job-" + record.image_upload_id) is not None
            writer.execute("set local lock_timeout = '1s'")
            writer.execute(
                "insert into coach_events (event_id, profile_id, event_type, payload_json, created_at) "
                "values ('concurrent-weight', %s, 'weight', '{}', '2026-11-16')", (own,),
            )
        finally:
            writer.commit()
    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    inventory.storage.erase_account_object.assert_called_once_with(object_key=record.object_key)
    assert inventory.coach.get_profile(own) is None
    assert inventory.meals.get_image_upload(record.image_upload_id) is None


@pytest.mark.parametrize("inventory", ["postgres"], indirect=True)
def test_postgres_profile_erasure_retries_analytics_owner_lock(inventory, monkeypatch):
    own = inventory.profile("analytics-contended-profile")
    record = inventory.upload(own)
    monkeypatch.setenv("APP_ENV", "production")
    analytics = get_analytics_repository()
    analytics.save_privacy_consent(
        OWNER, policy_version=PRIVACY_CONSENT_VERSION,
        health_data_consent=True, analytics_consent=True,
    )
    owner_locked, release = Event(), Event()
    original = analytics._upsert_user

    def pause_after_owner_lock(conn, user, received_at):
        owner_locked.set()
        assert release.wait(5)
        return original(conn, user, received_at)

    monkeypatch.setattr(analytics, "_upsert_user", pause_after_owner_lock)
    with ThreadPoolExecutor(max_workers=2) as pool:
        recorded = pool.submit(
            analytics.record_event,
            AnalyticsEventRequest(event_name="app_opened", session_id="contended-analytics", screen="today"),
            AuthenticatedUser(user_id=OWNER),
        )
        try:
            assert owner_locked.wait(5)
            removed = pool.submit(inventory.client.delete, f"/v1/profiles/{own}")
            response = removed.result(timeout=1.5)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "persistence_unavailable"
            inventory.storage.erase_account_object.assert_not_called()
            inventory.storage.delete_object.assert_not_called()
            assert inventory.coach.get_profile(own) is not None
            assert inventory.meals.get_image_upload(record.image_upload_id) == record
            assert inventory.meals.get_analysis_job("job-" + record.image_upload_id) is not None
        finally:
            release.set()
        recorded.result(timeout=5)

    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    inventory.storage.erase_account_object.assert_called_once_with(object_key=record.object_key)
    assert inventory.coach.get_profile(own) is None
    assert inventory.meals.get_image_upload(record.image_upload_id) is None
    with analytics._connection() as conn:
        assert conn.execute("select 1 from product_events").fetchone() is None


@pytest.mark.parametrize("inventory", ["postgres"], indirect=True)
def test_postgres_profile_erasure_retries_image_first_analysis_writer(inventory):
    own = inventory.profile("image-contended-profile")
    record = inventory.upload(own)
    with inventory.meals._connection() as writer, ThreadPoolExecutor(max_workers=1) as pool:
        writer.execute("select 1 from image_uploads where image_upload_id = %s for share",
                       (record.image_upload_id,)).fetchone()
        removed = pool.submit(inventory.client.delete, f"/v1/profiles/{own}")
        try:
            response = removed.result(timeout=1.5)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "persistence_unavailable"
            inventory.storage.erase_account_object.assert_not_called()
            inventory.storage.delete_object.assert_not_called()
            assert inventory.coach.get_profile(own) is not None
            assert inventory.meals.get_image_upload(record.image_upload_id) == record
            assert inventory.meals.get_analysis_job("job-" + record.image_upload_id) is not None
            writer.execute("set local lock_timeout = '1s'")
            writer.execute("update analysis_jobs set updated_at = '2026-11-16T00:00:01+00:00' "
                           "where analysis_job_id = %s", ("job-" + record.image_upload_id,))
        finally:
            writer.commit()

    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    inventory.storage.erase_account_object.assert_called_once_with(object_key=record.object_key)
    assert inventory.coach.get_profile(own) is None
    assert inventory.meals.get_image_upload(record.image_upload_id) is None


@pytest.mark.parametrize("inventory", ["postgres"], indirect=True)
def test_postgres_post_erase_child_update_times_out_final_delete_and_retries(inventory, monkeypatch):
    own = inventory.profile("child-contended-profile")
    record = inventory.upload(own)
    original_connection = inventory.meals._connection
    with original_connection() as conn:
        conn.execute(
            "insert into coach_events (event_id, profile_id, event_type, payload_json, created_at) "
            "values ('contended-child', %s, 'weight', '{}', '2026-11-16')", (own,),
        )
    finalizing, allow_delete, updating, updated, release = (Event() for _ in range(5))
    backends, failures = {}, []

    @contextmanager
    def connection():
        try:
            with original_connection() as conn:
                class Connection:
                    def execute(self, statement, parameters=()):
                        if statement.startswith("delete from coach_events where profile_id"):
                            backends["eraser"] = conn.info.backend_pid
                            finalizing.set()
                            assert allow_delete.wait(5)
                        return conn.execute(statement, parameters)
                yield Connection()
        except PersistenceError as exc:
            failures.append(getattr(exc.__cause__, "sqlstate", None))
            raise

    def update_child():
        with original_connection() as writer:
            backends["writer"] = writer.info.backend_pid
            updating.set()
            writer.execute("update coach_events set created_at = '2026-11-16T00:00:01+00:00' "
                           "where event_id = 'contended-child'")
            updated.set()
            assert release.wait(5)

    monkeypatch.setattr(inventory.meals, "_connection", connection)
    with ThreadPoolExecutor(max_workers=2) as pool:
        removed = pool.submit(inventory.client.delete, f"/v1/profiles/{own}")
        try:
            assert finalizing.wait(5)
            inventory.storage.erase_account_object.assert_called_once_with(object_key=record.object_key)
            changed = pool.submit(update_child)
            assert updating.wait(5)
            deadline = monotonic() + 5
            blocked = False
            while monotonic() < deadline:
                with original_connection() as observer:
                    blockers = observer.execute("select pg_blocking_pids(%s) as blockers",
                                                (backends["writer"],)).fetchone()["blockers"]
                if backends["eraser"] in blockers:
                    blocked = True
                    break
                sleep(0.01)
            assert blocked, "the child UPDATE must hold its row while waiting on the finalizer's parent lock"
            allow_delete.set()
            response = removed.result(timeout=1.5)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "persistence_unavailable"
            assert failures == ["55P03"], "final DELETE must hit lock_timeout, not deadlock or statement_timeout"
            assert updated.wait(2)
            pending = inventory.meals.get_image_upload(record.image_upload_id)
            assert pending is not None and pending.upload_status == "deleting"
            assert pending.object_key == record.object_key
            assert pending.owner_id == record.owner_id and pending.storage_namespace == record.storage_namespace
            assert inventory.coach.get_profile(own) is not None
            assert inventory.meals.get_analysis_job("job-" + record.image_upload_id) is not None
            inventory.storage.delete_object.assert_not_called()
        finally:
            allow_delete.set()
            release.set()
        changed.result(timeout=5)

    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    assert inventory.storage.erase_account_object.call_count == 2
    assert inventory.coach.get_profile(own) is None
    assert inventory.meals.get_image_upload(record.image_upload_id) is None
    assert inventory.meals.get_analysis_job("job-" + record.image_upload_id) is None
    with original_connection() as conn:
        assert conn.execute("select 1 from coach_events where event_id = 'contended-child'").fetchone() is None


@pytest.mark.parametrize("foreign", [False, True])
def test_cached_checkin_cannot_attach_to_erasing_upload(inventory, foreign):
    own = inventory.profile("selected")
    other_owner = FOREIGN if foreign else OWNER
    other = inventory.profile("retained", owner=other_owner)
    record = inventory.upload(own)
    cached = inventory.meals.get_image_upload(record.image_upload_id)
    assert cached.upload_status == "ready"

    def erase(**kwargs):
        with pytest.raises(PersistenceError):
            inventory.meals.save_analysis_job(
                payload=AnalysisJobRequest(image_upload_id=cached.image_upload_id, profile_id=other),
                image_reference=cached.image_reference, owner_id=other_owner,
                create_response=AnalysisJobCreateResponse(analysis_job_id="late-reference", status="queued"),
            )
        return True

    inventory.storage.erase_account_object.side_effect = erase
    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    assert inventory.meals.get_analysis_job("late-reference") is None
    assert inventory.coach.get_profile(other) is not None


def test_meal_log_rechecks_erasure_state_after_fence_wait(inventory, monkeypatch):
    own = inventory.profile("selected")
    other = inventory.profile("retained")
    record = inventory.upload(own)
    claiming, finish = Event(), Event()
    original_connection = inventory.meals._connection

    @contextmanager
    def connection():
        with original_connection() as conn:
            class Connection:
                def execute(self, statement, parameters=()):
                    if statement.startswith("update image_uploads set upload_status = 'deleting'"):
                        claiming.set()
                        assert finish.wait(5)
                    return conn.execute(statement, parameters)
            yield Connection()

    def insert_log():
        with inventory.meals._connection() as conn:
            conn.execute(inventory.meals._account_sql(
                "insert into meal_logs (meal_log_id, analysis_job_id, result_id, clarification_value, "
                "request_json, response_json, created_at) values ('late-log', ?, 'fixture', '', ?, '{}', 'now')"
            ), ("job-" + record.image_upload_id, json.dumps({"profile_id": other})))

    monkeypatch.setattr(inventory.meals, "_connection", connection)
    with ThreadPoolExecutor(max_workers=2) as executor:
        claim = executor.submit(
            inventory.meals.claim_profile_erasure, own, owner_id=OWNER, expected_uploads=[record],
        )
        assert claiming.wait(2)
        late = executor.submit(insert_log)
        try:
            with pytest.raises(TimeoutError):
                late.result(timeout=0.1)
        finally:
            finish.set()
        claim.result(timeout=5)
        with pytest.raises(PersistenceError):
            late.result(timeout=5)
    with inventory.meals._connection() as conn:
        assert conn.execute("select 1 from meal_logs where meal_log_id = 'late-log'").fetchone() is None


def test_profile_is_gone_when_inventory_finalizer_returns(inventory, monkeypatch):
    own = inventory.profile("selected")
    inventory.upload(own)
    late = inventory.upload()
    name = "complete_profile_erasure" if hasattr(inventory.meals, "complete_profile_erasure") else "delete_profile_artifacts"
    original = getattr(inventory.meals, name)
    checked = []

    def finalize(*args, **kwargs):
        result = original(*args, **kwargs)
        with pytest.raises(PersistenceError):
            inventory.meals.save_analysis_job(
                payload=AnalysisJobRequest(image_upload_id=late.image_upload_id, profile_id=own),
                image_reference=late.image_reference, owner_id=OWNER,
                create_response=AnalysisJobCreateResponse(analysis_job_id="late-reference", status="queued"),
            )
        checked.append(True)
        return result

    monkeypatch.setattr(inventory.meals, name, finalize)
    assert inventory.client.delete(f"/v1/profiles/{own}").status_code == 200
    assert checked == [True]
    assert inventory.coach.get_profile(own) is None
    assert inventory.meals.get_analysis_job("late-reference") is None
    assert inventory.meals.get_image_upload(late.image_upload_id) == late


def test_pending_account_consent_cannot_be_updated_reassigned_or_recreated(inventory):
    inventory.consent()
    inventory.consent(FOREIGN)
    assert deletion.delete_account(OWNER) == "pending"
    for statement, args in (
        ("update privacy_consents set analytics_consent = 1 where owner_id = ?", (OWNER,)),
        ("update privacy_consents set owner_id = ? where owner_id = ?", (OWNER, FOREIGN)),
        ("delete from privacy_consents where owner_id = ?", (OWNER,)),
    ):
        with pytest.raises(PersistenceError):
            with inventory.meals._connection() as conn:
                conn.execute(inventory.meals._account_sql(statement), args)


def test_explicit_guard_upgrade_installs_consent_fence(inventory):
    with inventory.meals._connection() as conn:
        conn.execute("update account_deletion_schema set version = 3")
    inventory.meals.prepare_account_deletion()
    assert deletion.delete_account(OWNER) == "pending"
    with pytest.raises(PersistenceError):
        inventory.consent()


def test_guard_upgrade_requeues_legacy_accepted_consent_cleanup(inventory):
    meals = inventory.meals
    meals.begin_account_deletion(OWNER)
    with meals._connection() as conn:
        if inventory.dsn:
            conn.execute("drop trigger account_guard on privacy_consents")
        else:
            for operation in ("insert", "update", "delete"):
                conn.execute(f"drop trigger account_guard_privacy_consents_{operation}")
        conn.execute("update account_deletion_schema set version = 3")
        conn.execute("update account_deletions set stage = 1")
        conn.execute("update account_deletion_work set phase = 'done'")
    inventory.consent()

    meals.prepare_account_deletion()
    assert meals.get_account_deletion_stage(OWNER) == 0
    assert deletion.run_account_deletion_jobs()["deleted"] == 1
    with meals._connection() as conn:
        assert conn.execute("select 1 from privacy_consents").fetchone() is None
    assert len(inventory.admin.calls) == 1
