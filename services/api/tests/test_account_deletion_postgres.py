"""Opt-in real PostgreSQL checks; never point CAL_AI_TEST_PG_DSN at user data."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

psycopg = pytest.importorskip("psycopg")
from psycopg import sql

from app import account_routes, main
from app.services import account_deletion as deletion
from app.services.analytics_repository import get_analytics_repository
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from test_account_deletion import (
    FOREIGN, ONBOARDING, OWNER, admin, client, delete, headers, job, profile, upload,
)


@pytest.fixture
def postgres(monkeypatch, admin):
    base = os.environ.get("CAL_AI_TEST_PG_DSN", "")
    if not base:
        pytest.skip("CAL_AI_TEST_PG_DSN is required for real PostgreSQL evidence")
    parsed = urlsplit(base)
    query = dict(parse_qsl(parsed.query))
    if parsed.hostname or query.get("host") != "/private/tmp" or parsed.path != "/postgres":
        pytest.fail("Only the isolated Unix-socket test cluster is allowed")
    schema = "deletion_test_" + uuid4().hex
    with psycopg.connect(base, autocommit=True) as conn:
        conn.execute(sql.SQL("create schema {}").format(sql.Identifier(schema)))
    query["options"] = "-csearch_path=" + schema
    scoped = urlunsplit(parsed._replace(netloc="localhost", query=urlencode(query)))
    monkeypatch.setenv("DATABASE_URL", scoped)
    try:
        get_coach_repository()
        get_analytics_repository()
        repository = get_persistence_repository()
        repository.prepare_account_deletion()
        yield repository, scoped
    finally:
        with psycopg.connect(base, autocommit=True) as conn:
            conn.execute(sql.SQL("drop schema {} cascade").format(sql.Identifier(schema)))


@pytest.fixture
def pg_client(postgres, client):
    return client


def test_real_postgres_deletes_owned_rows_and_preserves_other_user(pg_client, postgres, admin):
    repository, _ = postgres
    own = profile(pg_client)
    foreign = profile(pg_client, FOREIGN)
    upload("own-upload")
    upload("foreign-upload", FOREIGN)
    job("own-job", "own-upload", profile_id=own)
    job("foreign-job", "foreign-upload", FOREIGN, foreign)

    assert delete(pg_client).status_code == 202
    for _ in range(30):
        result = deletion.run_account_deletion_jobs(max_objects=2)
        if result["deleted"]:
            break
    assert repository.get_account_deletion_stage(OWNER) == 3
    assert repository.get_image_upload("own-upload") is None
    assert repository.get_analysis_job("own-job") is None
    assert get_coach_repository().get_profile(own) is None
    assert get_coach_repository().get_profile(foreign).owner_id == FOREIGN
    assert repository.get_analysis_job("foreign-job").owner_id == FOREIGN
    assert repository.get_image_upload("foreign-upload").owner_id == FOREIGN
    assert len(admin.calls) == 1


def test_real_postgres_guard_blocks_pending_and_completed_subjects(pg_client, postgres):
    repository, _ = postgres
    profile(pg_client)
    assert delete(pg_client).status_code == 202
    assert pg_client.post("/v1/onboarding", headers=headers(), json={}).status_code == 403
    with pytest.raises(PersistenceError):
        upload("late-own-upload")
    upload("unrelated-upload", FOREIGN)
    for _ in range(30):
        if deletion.run_account_deletion_jobs()["deleted"]:
            break
    assert repository.get_account_deletion_stage(OWNER) == 3
    with pytest.raises(PersistenceError):
        upload("resurrected-upload")
    assert repository.get_image_upload("unrelated-upload").owner_id == FOREIGN


def test_real_postgres_worker_tables_are_not_publicly_accessible(postgres):
    _, dsn = postgres
    with psycopg.connect(dsn) as conn:
        tables = conn.execute(
            "select relname, relrowsecurity, relacl from pg_class c "
            "join pg_namespace n on n.oid = c.relnamespace "
            "where n.nspname = current_schema() and relname in "
            "('account_deletion_work', 'account_deletion_objects')"
        ).fetchall()
        assert len(tables) == 2
        assert all(row[1] for row in tables)
        assert all(not any(grant.startswith("=") for grant in row[2] or []) for row in tables)


def test_real_postgres_acceptance_sql_executes(postgres):
    repository, _ = postgres
    upload("acceptance-fixture")
    assert repository.begin_account_deletion(OWNER) == 0


def test_real_postgres_acceptance_drains_only_same_owner_writer(postgres):
    repository, dsn = postgres
    upload("inflight-source")
    upload("foreign-source", FOREIGN)
    writer = psycopg.connect(dsn)
    started = Event()

    def accept():
        started.set()
        return repository.begin_account_deletion(OWNER)

    try:
        writer.execute("update image_uploads set file_name = 'inflight-fixture.jpg' where image_upload_id = %s",
                       ("inflight-source",))
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(accept)
            assert started.wait(2)
            try:
                # A foreign owner remains writable while acceptance waits on this owner.
                upload("foreign-during-drain", FOREIGN)
                assert not future.done()
            finally:
                writer.commit()
            assert future.result(timeout=5) == 0
        with pytest.raises(PersistenceError):
            upload("late-same-owner")
        assert repository.get_image_upload("foreign-during-drain").owner_id == FOREIGN
    finally:
        writer.close()


def test_real_postgres_lease_lock_and_commit_expiry_fence_are_atomic(postgres):
    repository, dsn = postgres
    repository.begin_account_deletion(OWNER)
    assert repository.claim_account_deletion(OWNER, "old-worker")
    with pytest.raises(PersistenceError, match="account_deletion_lease_lost"):
        with repository._account_deletion_transaction(OWNER, "old-worker") as conn:
            conn.execute("update account_deletion_work set storage_uncertain = 1 where owner_id = %s", (OWNER,))
            with psycopg.connect(dsn) as competitor:
                competitor.execute("set local lock_timeout = '100ms'")
                with pytest.raises(psycopg.errors.LockNotAvailable):
                    competitor.execute("update account_deletion_work set lease_token = 'new-worker' where owner_id = %s",
                                       (OWNER,))
                competitor.rollback()
            conn.execute("update account_deletion_work set lease_until = '2000-01-01T00:00:00+00:00' where owner_id = %s",
                         (OWNER,))
    assert not repository.account_storage_uncertain(OWNER)
    assert repository.account_deletion_lease_current(OWNER, "old-worker")


def test_real_postgres_known_underage_guard_preserves_profiles_and_account_access(postgres, monkeypatch, admin):
    repository, dsn = postgres
    coach = get_coach_repository()

    def insert_profile(profile_id, owner_id, age, created_at):
        payload = {
            "profile_id": profile_id, "owner_id": owner_id,
            "onboarding": {**ONBOARDING, "age": age},
            "target": {"calories_kcal": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 60},
            "created_at": created_at,
        }
        with psycopg.connect(dsn) as conn:
            conn.execute(
                "insert into coach_profiles (profile_id, payload_json, created_at, updated_at) values (%s, %s, %s, %s)",
                (profile_id, json.dumps(payload), created_at, created_at),
            )

    def profile_rows():
        with psycopg.connect(dsn) as conn:
            return conn.execute("select * from coach_profiles order by profile_id").fetchall()

    insert_profile("newer-adult", OWNER, 18, "2026-11-01")
    insert_profile("foreign-underage", FOREIGN, 17, "2026-01-01")
    assert coach.has_underage_profile(OWNER) is False
    assert coach.has_underage_profile(FOREIGN) is True
    assert coach.has_underage_profile("unrelated-owner") is False

    monkeypatch.setattr(main, "authenticate_bearer_token", lambda value: AuthenticatedUser(
        user_id=value.removeprefix("Bearer "),
    ))
    account_calls = []
    monkeypatch.setattr(account_routes, "delete_account", lambda owner: account_calls.append(owner) or "pending")
    with TestClient(main.app, headers=headers()) as api:
        assert api.get("/v1/dashboard/today").status_code == 200
        # Legacy ages enter through bound SQL, never the adult-only request schema.
        insert_profile("legacy-underage", OWNER, 17, "2026-01-01")
        before = profile_rows()
        assert coach.has_underage_profile(OWNER) is True
        assert coach.has_underage_profile(FOREIGN) is True
        for method, path in (
            ("GET", "/v1/dashboard/today"),
            ("POST", "/v1/analysis-jobs"),
            ("POST", "/v1/profiles/newer-adult/body-check-ins"),
            ("GET", "/v1/profiles/newer-adult/workout-history"),
            ("POST", "/image-uploads/presign"),
        ):
            response = api.request(method, path, json={} if method == "POST" else None)
            assert response.status_code == 403
            assert response.json()["detail"]["code"] == "age_restricted"
            assert response.json()["detail"]["retryable"] is False
        current = api.get("/v1/profiles/me")
        assert current.status_code == 200 and current.json() == {"profile_id": "newer-adult"}
        assert api.get("/v1/billing/status").status_code == 200
        response = api.request("DELETE", "/v1/account", json={"confirm": True})
        assert response.status_code == 202 and response.json() == {"status": "pending"}
        assert account_calls == [OWNER]
        assert profile_rows() == before

    assert coach.get_profile("foreign-underage").owner_id == FOREIGN
    assert repository.get_account_deletion_stage(OWNER) is None
    assert repository.get_account_deletion_stage(FOREIGN) is None
    assert not admin.calls
