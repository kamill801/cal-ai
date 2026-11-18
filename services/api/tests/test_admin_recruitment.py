from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import admin_routes, main
from app.services.analytics_repository import get_analytics_repository
from app.services.auth import AuthenticatedUser, AuthenticationError
from app.services.persistence import PersistenceError
from app.services.recruitment_repository import RecruitmentPersistenceError, RecruitmentRepository


client = TestClient(main.app)
NOW = datetime(2026, 11, 19, 3, 30, tzinfo=UTC)
ENDPOINT = "/internal/admin/beta-applications"


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setattr(admin_routes, "authenticate_admin_bearer_token",
                        lambda _authorization: AuthenticatedUser(user_id="admin-owner"))


@pytest.fixture
def repository(monkeypatch, tmp_path):
    repo = RecruitmentRepository(str(tmp_path / "cal-ai-api.db"), clock=lambda: NOW)
    monkeypatch.setattr(admin_routes, "get_recruitment_repository", lambda: repo)
    return repo


def insert_application(repo, identifier, email, *, created_at=NOW, expires_at=None):
    with repo._connection() as conn:
        repo._ensure_schema(conn)
        conn.execute(
            "insert into beta_recruitment_applications "
            "(id,email,adult_confirmed,privacy_consent,policy_version,created_at,expires_at) values(?,?,1,1,?,?,?)",
            (identifier, email, "2026-11-18.1", created_at.isoformat(timespec="microseconds"),
             (expires_at or NOW + timedelta(days=30)).isoformat(timespec="microseconds")),
        )


def fail_database_access(monkeypatch):
    monkeypatch.setattr(admin_routes, "get_recruitment_repository", lambda: pytest.fail("unauthorized DB read"))
    monkeypatch.setattr(admin_routes, "get_analytics_repository", lambda: pytest.fail("unauthorized audit write"))


def test_beta_admin_is_concealed_when_disabled(monkeypatch):
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "false")
    fail_database_access(monkeypatch)
    response = client.get(ENDPOINT)
    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_beta_admin_requires_token(monkeypatch):
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.setenv("ADMIN_SUPABASE_URL", "https://admin.invalid")
    monkeypatch.setenv("ADMIN_SUPABASE_JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-owner")
    def authenticate(authorization, **_kwargs):
        assert authorization is None
        raise AuthenticationError("missing_bearer_token")
    monkeypatch.setattr("app.services.auth._authenticate_supabase_bearer_token", authenticate)
    fail_database_access(monkeypatch)
    response = client.get(ENDPOINT)
    assert response.status_code == 401
    assert response.json() == {"detail": "admin_access_denied"}
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_beta_admin_rejects_valid_non_owner_token(monkeypatch):
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.setenv("ADMIN_SUPABASE_URL", "https://admin.invalid")
    monkeypatch.setenv("ADMIN_SUPABASE_JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-owner")
    monkeypatch.setattr("app.services.auth._authenticate_supabase_bearer_token",
                        lambda *_args, **_kwargs: AuthenticatedUser(user_id="consumer"))
    fail_database_access(monkeypatch)
    response = client.get(ENDPOINT, headers={"Authorization": "Bearer consumer-fixture"})
    assert response.status_code == 403
    assert response.headers["cache-control"] == "no-store, max-age=0"


def test_beta_admin_does_not_fall_back_to_consumer_auth(monkeypatch):
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-owner")
    monkeypatch.setenv("SUPABASE_URL", "https://consumer.invalid")
    for name in ("ADMIN_SUPABASE_URL", "ADMIN_SUPABASE_JWT_SECRET", "ADMIN_SUPABASE_JWT_ALGORITHM"):
        monkeypatch.delenv(name, raising=False)
    fail_database_access(monkeypatch)
    response = client.get(ENDPOINT, headers={"Authorization": "Bearer consumer-fixture"})
    assert response.status_code == 503
    assert response.json() == {"detail": "admin_auth_unavailable"}


def test_empty_beta_admin_response_does_not_create_recruitment_tables(owner, repository):
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    assert response.json() == {"generated_at": NOW.isoformat().replace("+00:00", "Z"), "total": 0,
                               "limit": 50, "offset": 0, "applications": []}
    assert response.headers["cache-control"] == "no-store, max-age=0"
    with sqlite3.connect(repository._location) as conn:
        assert not conn.execute("select name from sqlite_master where name like 'beta_recruitment_%'").fetchall()


def test_paginated_beta_admin_has_global_count_deterministic_order_and_minimal_fields(owner, repository):
    insert_application(repository, "older", "older@example.invalid", created_at=NOW - timedelta(days=1))
    insert_application(repository, "tie-a", "first@example.invalid")
    insert_application(repository, "tie-b", "second@example.invalid")
    first = client.get(ENDPOINT, params={"limit": 2, "offset": 0}).json()
    second = client.get(ENDPOINT, params={"limit": 2, "offset": 2}).json()
    beyond = client.get(ENDPOINT, params={"limit": 2, "offset": 6}).json()
    assert first["total"] == second["total"] == beyond["total"] == 3
    assert first["limit"] == 2 and first["offset"] == 0
    assert [row["id"] for row in first["applications"]] == ["tie-b", "tie-a"]
    assert [row["id"] for row in second["applications"]] == ["older"]
    assert beyond["applications"] == []
    assert first["applications"][0]["email"] == "second@example.invalid"
    assert first["applications"][0]["created_at"] == NOW.isoformat().replace("+00:00", "Z")
    assert set(first) == {"generated_at", "total", "limit", "offset", "applications"}
    assert all(set(row) == {"id", "email", "created_at"} for row in first["applications"])


def test_expired_applications_are_not_visible_but_read_does_not_delete_or_change_them(owner, repository):
    insert_application(repository, "expired", "expired@example.invalid", expires_at=NOW - timedelta(seconds=1))
    insert_application(repository, "boundary", "boundary@example.invalid", expires_at=NOW)
    insert_application(repository, "valid", "valid@example.invalid", expires_at=NOW + timedelta(seconds=1))
    with sqlite3.connect(repository._location) as conn:
        before = conn.execute("select * from beta_recruitment_applications order by id").fetchall()
    body = client.get(ENDPOINT).json()
    assert body["total"] == 1
    assert [row["id"] for row in body["applications"]] == ["valid"]
    with sqlite3.connect(repository._location) as conn:
        assert conn.execute("select * from beta_recruitment_applications order by id").fetchall() == before
        assert conn.execute("select count(*) from beta_recruitment_admission").fetchone()[0] == 0


def test_beta_count_is_unique_and_independent_from_registered_users(owner, repository):
    for _ in range(2):
        repository.save_application("same@example.invalid", "2026-11-18.1", 30, retention_enabled=True)
    analytics = get_analytics_repository()
    with analytics._connection() as conn:
        analytics._upsert_user(conn, AuthenticatedUser(user_id="not-an-applicant", email="member@example.invalid"), NOW)
    body = client.get(ENDPOINT).json()
    assert body["total"] == 1
    assert [row["email"] for row in body["applications"]] == ["same@example.invalid"]


@pytest.mark.parametrize("query", [{"limit": 0}, {"limit": 101}, {"limit": "invalid"}, {"offset": -1},
                                   {"offset": 100001}, {"offset": "invalid"}])
def test_invalid_pagination_is_rejected_before_storage(owner, monkeypatch, query):
    fail_database_access(monkeypatch)
    assert client.get(ENDPOINT, params=query).status_code == 422


def test_beta_admin_uses_existing_owner_auth_and_records_audit_without_email(owner, repository):
    insert_application(repository, "application", "private@example.invalid")
    assert client.get(ENDPOINT).status_code == 200
    with sqlite3.connect(repository._location) as conn:
        row, = conn.execute("select admin_user_id,action,resource_type,resource_id from admin_audit_logs").fetchall()
    assert row == ("admin-owner", "read", "beta_applications", None)
    assert "private@example.invalid" not in repr(row)


@pytest.mark.parametrize("failure", ["storage", "audit"])
def test_beta_admin_fails_closed_and_never_returns_raw_errors_or_pii(owner, repository, monkeypatch, failure):
    insert_application(repository, "application", "private@example.invalid")
    if failure == "storage":
        def fail(**_kwargs):
            raise RecruitmentPersistenceError("postgres://secret@private.invalid private@example.invalid")
        monkeypatch.setattr(repository, "list_applications", fail)
    else:
        def fail(**_kwargs):
            raise PersistenceError("postgres://secret@private.invalid private@example.invalid")
        monkeypatch.setattr(get_analytics_repository(), "record_admin_audit", fail)
    response = client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json() == {"detail": "admin_data_unavailable"}
    assert response.headers["cache-control"] == "no-store, max-age=0"
    assert "private" not in response.text and "secret" not in response.text


def test_postgres_beta_read_uses_bound_page_and_expiry_parameters_without_ddl():
    repo = RecruitmentRepository("postgresql://fixture.invalid/db", clock=lambda: NOW)
    statements = []
    class Result:
        def __init__(self, one=None, many=None):
            self.one, self.many = one, many
        def fetchone(self):
            return self.one
        def fetchall(self):
            return self.many
    class Connection:
        def execute(self, sql, parameters=None):
            statements.append((sql, parameters))
            if "to_regclass" in sql:
                return Result({"relation": "beta_recruitment_applications"})
            if "count(*)" in sql:
                return Result({"total": 3})
            return Result(many=[{"id": "one", "email": "one@example.invalid", "created_at": NOW.isoformat()}])
    @contextmanager
    def connection():
        yield Connection()
    repo._connection = connection
    page = repo.list_applications(limit=1, offset=2)
    assert page.total == 3 and len(page.applications) == 1
    assert len(statements) == 3
    assert statements[1][1] == (NOW.isoformat(timespec="microseconds"),)
    assert statements[2][1] == (NOW.isoformat(timespec="microseconds"), 1, 2)
    assert "order by created_at desc,id desc limit %s offset %s" in statements[2][0]
    assert not any(any(word in sql.lower() for word in ("create ", "delete ", "update ", "insert ", "alter "))
                   for sql, _ in statements)


def test_unavailable_beta_storage_does_not_look_like_an_empty_list(tmp_path):
    directory = tmp_path / "is-a-directory"
    directory.mkdir()
    repo = RecruitmentRepository(str(directory), clock=lambda: NOW)
    with pytest.raises(RecruitmentPersistenceError, match="recruitment_unavailable"):
        repo.list_applications()
