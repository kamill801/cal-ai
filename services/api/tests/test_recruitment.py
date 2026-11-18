from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.recruitment_routes import router
from app.recruitment_schemas import POLICY_VERSION
from app.services import recruitment
from app.services.recruitment_repository import (
    RecruitmentLimitError, RecruitmentPersistenceError, RecruitmentRepository, get_recruitment_repository,
)

ORIGIN = recruitment.DEFAULT_PUBLIC_ORIGIN
HEADERS = {"Origin": ORIGIN, "Sec-Fetch-Site": "same-origin"}
PAYLOAD = {"email": "Beta.Name+alias@Example.org", "platform": "android", "adult_confirmed": True,
           "privacy_consent": True, "policy_version": POLICY_VERSION, "website": ""}
NOW = datetime(2026, 11, 18, 6, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def recruitment_environment(monkeypatch):
    for key in ("BETA_RECRUITMENT_ENABLED", "BETA_RECRUITMENT_RETENTION_ENABLED",
                "BETA_RECRUITMENT_POLICY_APPROVED_VERSION", "BETA_RECRUITMENT_RETENTION_DAYS",
                "BETA_ANDROID_INSTALL_URL", "BETA_RECRUITMENT_PUBLIC_ORIGIN", "APP_ENV", "VERCEL_ENV",
                "VERCEL", "ENVIRONMENT"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setenv("BETA_RECRUITMENT_ENABLED", "true")
    monkeypatch.setenv("BETA_RECRUITMENT_RETENTION_ENABLED", "true")
    monkeypatch.setenv("BETA_RECRUITMENT_POLICY_APPROVED_VERSION", POLICY_VERSION)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as instance:
        yield instance


def post(client, **changes):
    return client.post("/recruitment/applications", headers=HEADERS, json={**PAYLOAD, **changes})


def assert_private(response):
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "set-cookie" not in response.headers


def records(path):
    with sqlite3.connect(path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("select * from beta_recruitment_applications order by email")]


def test_default_closed_config_and_post_do_not_touch_database(client, monkeypatch, tmp_path):
    path = tmp_path / "never-created" / "data.db"
    monkeypatch.setenv("CAL_AI_API_DATA_PATH", str(path))
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("must not open DB"))
    config = client.get("/recruitment/config")
    assert config.json() == {"accepting": False, "policy_version": POLICY_VERSION, "retention_days": 30,
                             "delivery": "on_page", "min_age": 18, "platform": "android",
                             "support_email": "areche.ai.kr@gmail.com"}
    assert_private(config)
    response = post(client)
    assert response.status_code == 503
    assert_private(response)
    assert not path.parent.exists()


def test_open_config_also_never_accesses_database_or_reveals_link(client, enabled, monkeypatch):
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("config DB access"))
    response = client.get("/recruitment/config")
    assert response.json()["accepting"] is True
    assert "expo.dev" not in response.text and "install_url" not in response.json()
    assert_private(response)


def test_production_defaults_stay_closed_without_database_initialization(client, monkeypatch, tmp_path):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("production default DB access"))
    response = client.get("/recruitment/config")
    assert response.json()["accepting"] is False
    assert "install_url" not in response.json()
    assert post(client).status_code == 503
    assert not (tmp_path / "cal-ai-api.db").exists()


@pytest.mark.parametrize("marker,value", [("VERCEL", "1"), ("APP_ENV", "production"), ("APP_ENV", "prod"),
                                         ("VERCEL_ENV", "production"), ("ENVIRONMENT", "production")])
@pytest.mark.parametrize("location", [None, "", ":memory:", "local.db", "sqlite:///local.db",
                                      "postgresqlx://fixture.invalid/db", "postgres://fixture.invalid/db",
                                      "postgresql://fixture.invalid/db"])
def test_production_accepting_requires_postgres_without_opening_database(
    client, enabled, monkeypatch, tmp_path, marker, value, location,
):
    monkeypatch.setenv(marker, value)
    if location is not None:
        monkeypatch.setenv("DATABASE_URL", location)
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("config or closed intake DB access"))
    expected = bool(location and location.startswith(("postgres://", "postgresql://")))
    response = client.get("/recruitment/config")
    assert response.json()["accepting"] is expected
    assert "fixture.invalid" not in response.text and "DATABASE_URL" not in response.text
    assert_private(response)
    if not expected:
        response = post(client)
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "recruitment_closed"
        assert "install_url" not in response.text
        assert_private(response)
    assert not (tmp_path / "cal-ai-api.db").exists()


@pytest.mark.parametrize("marker,value", [("VERCEL", "0"), ("APP_ENV", "development"), ("VERCEL_ENV", "preview")])
def test_nonproduction_sqlite_fallback_still_accepts(client, enabled, monkeypatch, tmp_path, marker, value):
    monkeypatch.setenv(marker, value)
    assert client.get("/recruitment/config").json()["accepting"] is True
    assert post(client).status_code == 202
    assert len(records(tmp_path / "cal-ai-api.db")) == 1


@pytest.mark.parametrize("key,value", [
    ("BETA_RECRUITMENT_ENABLED", "false"), ("BETA_RECRUITMENT_ENABLED", "TRUE"),
    ("BETA_RECRUITMENT_RETENTION_ENABLED", "false"),
    ("BETA_RECRUITMENT_POLICY_APPROVED_VERSION", "old"),
    ("BETA_RECRUITMENT_RETENTION_DAYS", "0"), ("BETA_RECRUITMENT_RETENTION_DAYS", "91"),
    ("BETA_RECRUITMENT_RETENTION_DAYS", "not-a-number"),
    ("BETA_RECRUITMENT_PUBLIC_ORIGIN", "https://user:private@example.org"),
])
def test_each_operational_gate_fails_closed(client, enabled, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    config = client.get("/recruitment/config")
    assert config.json()["accepting"] is False
    assert 1 <= config.json()["retention_days"] <= 90
    response = post(client)
    assert response.status_code == 503
    assert "not-a-number" not in response.text and "private" not in response.text


@pytest.mark.parametrize("days", [1, 30, 90])
def test_retention_config_is_bound_to_current_policy(client, enabled, monkeypatch, days):
    monkeypatch.setenv("BETA_RECRUITMENT_RETENTION_DAYS", str(days))
    config = client.get("/recruitment/config").json()
    assert config["retention_days"] == 30
    assert config["accepting"] is (days == 30)


@pytest.mark.parametrize("days", ["1", "29", "31", "90", "0", "91", "invalid"])
def test_retention_change_between_notice_and_submit_fails_closed(client, enabled, monkeypatch, tmp_path, days):
    notice = client.get("/recruitment/config").json()
    assert notice["accepting"] is True and notice["retention_days"] == 30
    assert post(client).status_code == 202
    path = tmp_path / "cal-ai-api.db"
    before = records(path)
    monkeypatch.setenv("BETA_RECRUITMENT_RETENTION_DAYS", days)
    with monkeypatch.context() as isolated:
        isolated.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("closed retention DB access"))
        config = client.get("/recruitment/config").json()
        assert config["accepting"] is False
        assert config["policy_version"] == notice["policy_version"]
        assert config["retention_days"] == notice["retention_days"] == 30
        for email in (PAYLOAD["email"], "new@example.org"):
            response = post(client, email=email)
            assert response.status_code == 503
            assert response.json()["detail"]["code"] == "recruitment_closed"
            assert "install_url" not in response.text
            assert_private(response)
    assert records(path) == before
    row, = before
    assert datetime.fromisoformat(row["expires_at"]) - datetime.fromisoformat(row["created_at"]) == timedelta(days=30)


@pytest.mark.parametrize("url", [
    "", recruitment.DEFAULT_INSTALL_URL.replace("https:", "http:"),
    recruitment.DEFAULT_INSTALL_URL + "?token=private", recruitment.DEFAULT_INSTALL_URL + "#private",
    recruitment.DEFAULT_INSTALL_URL + "?", recruitment.DEFAULT_INSTALL_URL + "#",
    recruitment.DEFAULT_INSTALL_URL.replace("expo.dev/", "expo.dev.attacker.invalid/"),
    recruitment.DEFAULT_INSTALL_URL.replace("expo.dev/", "user:private@expo.dev/"),
    recruitment.DEFAULT_INSTALL_URL.replace("expo.dev/", "expo.dev:443/"),
    recruitment.DEFAULT_INSTALL_URL.replace("arche-trustfirstnutrition", "other-account"),
    recruitment.DEFAULT_INSTALL_URL.replace("/trust-first-nutrition/", "/other-project/"),
    recruitment.DEFAULT_INSTALL_URL.replace("0ed6f218-7210-4ecf-9238-c522fa669bed", "not-a-uuid"),
    recruitment.DEFAULT_INSTALL_URL + "/", recruitment.DEFAULT_INSTALL_URL + "\n",
])
def test_invalid_install_urls_close_without_leak(client, enabled, monkeypatch, url):
    monkeypatch.setenv("BETA_ANDROID_INSTALL_URL", url)
    response = client.get("/recruitment/config")
    assert response.json()["accepting"] is False
    assert "install_url" not in response.json() and "private" not in response.text
    assert post(client).status_code == 503


def test_valid_override_and_committed_minimal_record(client, enabled, monkeypatch, tmp_path):
    url = recruitment.DEFAULT_INSTALL_URL.replace("0ed6f218-7210-4ecf-9238-c522fa669bed", "3cf4c15a-857a-4a7b-849d-bf567522180f")
    monkeypatch.setenv("BETA_ANDROID_INSTALL_URL", url)
    path = tmp_path / "stored.db"
    monkeypatch.setenv("CAL_AI_API_DATA_PATH", str(path))
    response = post(client)
    assert response.status_code == 202
    assert response.json() == {"accepted": True, "delivery": "on_page", "install_url": url, "app_version": "0.1.2"}
    assert "email" not in response.text and PAYLOAD["email"] not in response.text
    assert_private(response)
    row, = records(path)
    assert set(row) == {"id", "email", "adult_confirmed", "privacy_consent", "policy_version", "created_at", "expires_at"}
    assert row["email"] == "beta.name+alias@example.org"
    assert row["adult_confirmed"] == row["privacy_consent"] == 1
    assert row["policy_version"] == POLICY_VERSION
    assert datetime.fromisoformat(row["expires_at"]) - datetime.fromisoformat(row["created_at"]) == timedelta(days=30)
    with sqlite3.connect(path) as conn:
        tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
    assert tables == {"beta_recruitment_applications", "beta_recruitment_admission"}


@pytest.mark.parametrize("headers", [
    {}, {"Origin": "null"}, {"Origin": "https://attacker.invalid", "Host": "attacker.invalid"},
    {"Origin": ORIGIN + "/"}, {"Origin": ORIGIN, "Sec-Fetch-Site": "cross-site"},
    {"Origin": ORIGIN, "Sec-Fetch-Site": "none"},
    {"X-Forwarded-Host": "cal-ai-api.vercel.app", "Sec-Fetch-Site": "same-origin"},
])
def test_origin_does_not_trust_host_or_forwarded_headers(client, enabled, headers, tmp_path):
    response = client.post("/recruitment/applications", json=PAYLOAD, headers=headers)
    assert response.status_code == 403
    assert_private(response)
    assert not (tmp_path / "cal-ai-api.db").exists()


def test_explicit_local_origin_only_outside_production(client, enabled, monkeypatch):
    local = "http://localhost:5173"
    monkeypatch.setenv("BETA_RECRUITMENT_PUBLIC_ORIGIN", local)
    assert client.get("/recruitment/config").json()["accepting"] is True
    assert client.post("/recruitment/applications", headers={"Origin": local, "Sec-Fetch-Site": "same-site"}, json=PAYLOAD).status_code == 202
    monkeypatch.setenv("APP_ENV", "production")
    assert client.get("/recruitment/config").json()["accepting"] is False
    assert client.post("/recruitment/applications", headers={"Origin": local}, json=PAYLOAD).status_code == 503
    monkeypatch.delenv("APP_ENV")
    monkeypatch.setenv("VERCEL", "1")
    assert client.get("/recruitment/config").json()["accepting"] is False


@pytest.mark.parametrize("changes", [
    {"email": "not-email"}, {"email": "한글@example.org"}, {"email": "a..b@example.org"},
    {"email": ".person@example.org"}, {"email": "person.@example.org"}, {"email": "x@-bad.example"},
    {"email": "x@bad_.example"}, {"email": "x@localhost"}, {"email": "a" * 65 + "@example.org"},
    {"email": "x@example.org\r\nBcc: target@example.org"}, {"email": "a" * 255},
    {"adult_confirmed": False}, {"adult_confirmed": 1}, {"adult_confirmed": "true"},
    {"privacy_consent": False}, {"privacy_consent": 1}, {"platform": "ios"},
    {"name": "not-collected"}, {"health": "not-collected"}, {"website": None},
])
def test_invalid_fields_and_extra_data_are_not_reflected(client, enabled, changes, tmp_path):
    response = post(client, **changes)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"
    assert "target@example.org" not in response.text and "not-collected" not in response.text
    assert_private(response)
    assert not (tmp_path / "cal-ai-api.db").exists()


def test_stale_consent_and_missing_required_fields(client, enabled):
    stale = post(client, policy_version="old")
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "recruitment_policy_changed"
    for key in PAYLOAD:
        payload = {name: value for name, value in PAYLOAD.items() if name != key}
        assert client.post("/recruitment/applications", headers=HEADERS, json=payload).status_code == 422


def test_body_limits_content_type_and_chunked_enforcement(client, enabled):
    valid = json.dumps(PAYLOAD).encode()
    exactly = valid + b" " * (4096 - len(valid))
    assert client.post("/recruitment/applications", headers={**HEADERS, "Content-Type": "application/json"}, content=exactly).status_code == 202
    for content, extra in [
        (exactly + b" ", {}), (exactly + b" ", {"Content-Length": "1"}),
        (valid, {"Content-Length": "999999999999999999999999"}),
        (valid, {"Content-Length": "-1"}), (valid, {"Content-Encoding": "gzip"}),
    ]:
        response = client.post("/recruitment/applications", headers={**HEADERS, "Content-Type": "application/json", **extra}, content=content)
        assert response.status_code in (413, 422)
        assert_private(response)
    response = client.post("/recruitment/applications", headers={**HEADERS, "Content-Type": "application/json"},
                           content=iter([b" " * 3000, b" " * 3000]))
    assert response.status_code == 413
    for content in (b"{", b"[]", b"null", b"\xff", b"[" * 1500):
        assert client.post("/recruitment/applications", headers={**HEADERS, "Content-Type": "application/json"}, content=content).status_code == 422
    assert client.post("/recruitment/applications", headers=HEADERS, content=valid).status_code == 422
    assert_private(client.delete("/recruitment/applications"))


def test_honeypot_is_generic_without_database_or_install_link(client, enabled, monkeypatch):
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: pytest.fail("bot DB access"))
    response = post(client, website="https://bot.invalid")
    assert response.status_code == 202
    assert response.json() == {"accepted": True, "delivery": "on_page"}
    assert_private(response)


def test_duplicate_survives_new_repository_and_never_renews_consent_or_expiry(client, enabled, monkeypatch, tmp_path):
    first = post(client)
    path = tmp_path / "cal-ai-api.db"
    before = records(path)
    second = post(client, email=" beta.name+alias@example.org ")
    assert second.status_code == 202 and second.json() == first.json()
    assert records(path) == before
    repo = RecruitmentRepository(str(path), clock=lambda: NOW + timedelta(days=2))
    repo.save_application("beta.name+alias@example.org", "new-version-must-not-renew", 1, retention_enabled=True)
    assert records(path) == before


def test_concurrent_normalized_duplicate_intake_commits_one_row(client, enabled, tmp_path):
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda index: post(client, email=" BETA.Name+alias@example.org " if index % 2 else PAYLOAD["email"]), range(16)))
    assert all(response.status_code == 202 for response in responses)
    assert all(response.json() == responses[0].json() for response in responses)
    assert len(records(tmp_path / "cal-ai-api.db")) == 1


def test_db_rate_cap_is_global_concurrent_and_clock_rollback_does_not_reset(tmp_path):
    path = tmp_path / "rate.db"
    now = [NOW]
    repo = RecruitmentRepository(str(path), clock=lambda: now[0])
    repo.save_application("first@example.org", POLICY_VERSION, 30, retention_enabled=True)
    with sqlite3.connect(path) as conn:
        conn.execute("update beta_recruitment_admission set attempts=99")

    def submit(index):
        try:
            RecruitmentRepository(str(path), clock=lambda: now[0]).save_application(f"rate{index}@example.org", POLICY_VERSION, 30, retention_enabled=True)
            return "accepted"
        except RecruitmentLimitError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(submit, range(12)))
    assert outcomes.count("accepted") == 1
    assert outcomes.count("recruitment_rate_limited") == 11
    now[0] -= timedelta(hours=1)
    assert submit(20) == "recruitment_rate_limited"
    now[0] = NOW + timedelta(hours=1)
    assert submit(21) == "accepted"
    assert len(records(path)) == 3


def test_storage_cap_is_uniform_and_commits_admission_budget(client, enabled, tmp_path):
    assert post(client).status_code == 202
    path = tmp_path / "cal-ai-api.db"
    with sqlite3.connect(path) as conn:
        conn.execute("update beta_recruitment_admission set attempts=100")
    assert post(client).status_code == 429
    with sqlite3.connect(path) as conn:
        conn.execute("update beta_recruitment_admission set attempts=0")
        conn.executemany("insert into beta_recruitment_applications values(?,?,1,1,?,?,?)", [
            (f"seed-{i}", f"seed{i}@example.org", POLICY_VERSION, "2026-11-18T00:00:00.000000+00:00", "2999-01-01T00:00:00.000000+00:00")
            for i in range(999)
        ])
    before = records(path)
    existing = post(client)
    unknown = post(client, email="new@example.org")
    assert existing.status_code == unknown.status_code == 503
    assert existing.json() == unknown.json()
    assert existing.json()["detail"]["code"] == "recruitment_capacity_reached"
    for response in (existing, unknown):
        assert "install_url" not in response.text
        assert_private(response)
    assert records(path) == before
    with sqlite3.connect(path) as conn:
        assert conn.execute("select attempts from beta_recruitment_admission").fetchone()[0] == 2
        conn.execute("update beta_recruitment_admission set attempts=99")
    assert post(client, email="another@example.org").json()["detail"]["code"] == "recruitment_capacity_reached"
    for email in (PAYLOAD["email"], "unknown@example.org"):
        response = post(client, email=email)
        assert response.status_code == 429
        assert response.json()["detail"]["code"] == "recruitment_rate_limited"
    with sqlite3.connect(path) as conn:
        assert conn.execute("select attempts from beta_recruitment_admission").fetchone()[0] == 100


def test_storage_capacity_is_race_safe(tmp_path):
    path = tmp_path / "capacity.db"
    repo = RecruitmentRepository(str(path), clock=lambda: NOW)
    repo.save_application("first@example.org", POLICY_VERSION, 30, retention_enabled=True)
    with sqlite3.connect(path) as conn:
        conn.executemany("insert into beta_recruitment_applications values(?,?,1,1,?,?,?)", [
            (str(i), f"seed{i}@example.org", POLICY_VERSION, NOW.isoformat(), (NOW + timedelta(days=30)).isoformat())
            for i in range(998)
        ])

    def submit(index):
        try:
            repo.save_application(f"capacity{index}@example.org", POLICY_VERSION, 30, retention_enabled=True)
            return True
        except RecruitmentLimitError as exc:
            assert exc.code == "recruitment_capacity_reached"
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(submit, range(12))) == 1
    assert len(records(path)) == 1000
    with sqlite3.connect(path) as conn:
        assert conn.execute("select attempts from beta_recruitment_admission").fetchone()[0] == 13


def test_retention_is_explicit_beta_only_and_idempotent(monkeypatch, tmp_path):
    path = tmp_path / "retention.db"
    now = [NOW]
    repo = RecruitmentRepository(str(path), clock=lambda: now[0])
    repo.save_application("expires@example.org", POLICY_VERSION, 1, retention_enabled=True)
    now[0] += timedelta(days=1)
    with sqlite3.connect(path) as conn:
        conn.execute("create table existing_image_retention_state (value text)")
        conn.execute("insert into existing_image_retention_state values('preserve')")
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda env: repo)
    assert recruitment.cleanup_expired_recruitment({}) == 0
    assert len(records(path)) == 1
    assert recruitment.cleanup_expired_recruitment({"BETA_RECRUITMENT_RETENTION_ENABLED": "true"}) == 1
    assert repo.purge_expired(retention_enabled=True) == 0
    with sqlite3.connect(path) as conn:
        assert conn.execute("select value from existing_image_retention_state").fetchone()[0] == "preserve"
    never = RecruitmentRepository(str(tmp_path / "not-created.db"))
    assert never.purge_expired(retention_enabled=False) == 0
    assert not (tmp_path / "not-created.db").exists()
    with pytest.raises(RecruitmentPersistenceError):
        never.save_application("no@example.org", POLICY_VERSION, 30, retention_enabled=False)


def test_successful_intake_purges_only_expired_beta_rows(tmp_path):
    path = tmp_path / "expiry.db"
    now = [NOW]
    repo = RecruitmentRepository(str(path), clock=lambda: now[0])
    repo.save_application("expired@example.org", POLICY_VERSION, 1, retention_enabled=True)
    repo.save_application("still-active@example.org", POLICY_VERSION, 90, retention_enabled=True)
    now[0] += timedelta(days=1)
    repo.save_application("new@example.org", POLICY_VERSION, 30, retention_enabled=True)
    assert {row["email"] for row in records(path)} == {"still-active@example.org", "new@example.org"}
    with pytest.raises(RecruitmentPersistenceError):
        repo.save_application("bad@example.org", POLICY_VERSION, 91, retention_enabled=True)


def test_write_failure_rolls_back_purge_budget_and_contact_without_leaks(client, enabled, monkeypatch, tmp_path):
    path = tmp_path / "failure.db"
    repo = RecruitmentRepository(str(path), clock=lambda: NOW)
    repo.save_application("expired@example.org", POLICY_VERSION, 1, retention_enabled=True)
    with sqlite3.connect(path) as conn:
        conn.execute("update beta_recruitment_applications set expires_at='2000-01-01'")
        conn.execute("update beta_recruitment_admission set attempts=0")
        conn.execute("create trigger fail_contact before insert on beta_recruitment_applications begin select raise(abort,'private DSN person@example.org'); end")
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda: repo)
    response = post(client)
    assert response.status_code == 503
    assert "private" not in response.text and "DSN" not in response.text and "example.org" not in response.text
    assert "install_url" not in response.json()
    assert len(records(path)) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("select attempts from beta_recruitment_admission").fetchone()[0] == 0


def test_commit_failure_never_releases_install_link(client, enabled, monkeypatch, tmp_path):
    path = tmp_path / "commit.db"
    repo = RecruitmentRepository(str(path))
    original = repo._connection

    @contextmanager
    def failed_transaction():
        with original() as conn:
            yield conn
            raise sqlite3.OperationalError("private commit failure")

    monkeypatch.setattr(repo, "_connection", failed_transaction)
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda: repo)
    response = post(client)
    assert response.status_code == 503
    assert "install_url" not in response.text and "private" not in response.text
    with sqlite3.connect(path) as conn:
        assert conn.execute("select count(*) from sqlite_master where type='table'").fetchone()[0] == 0


def test_repository_location_priority_and_lazy_constructor(monkeypatch, tmp_path):
    assert get_recruitment_repository({"DATABASE_URL": "postgresql://fixture", "CAL_AI_API_DATA_PATH": "other"})._location == "postgresql://fixture"
    assert get_recruitment_repository({"CAL_AI_API_DATA_PATH": "other"})._location == "other"
    from app.services.persistence import DEFAULT_API_DATA_PATH
    assert get_recruitment_repository({})._location == str(DEFAULT_API_DATA_PATH)
    assert not (tmp_path / "lazy.db").exists()
    RecruitmentRepository(str(tmp_path / "lazy.db"))
    assert not (tmp_path / "lazy.db").exists()


def test_postgres_sql_shape_lock_timeouts_privacy_and_safe_failures(monkeypatch):
    statements, connections = [], []
    fail = [False]
    total, commits = [0], []

    class Cursor:
        rowcount = 0

        def __init__(self, value=None):
            self.value = value

        def fetchone(self):
            return self.value

    class Connection:
        def execute(self, sql, params=()):
            statements.append((sql, params))
            if sql.startswith("insert into beta_recruitment_applications") and fail[0]:
                raise psycopg.OperationalError("private DSN and email")
            if "returning attempts" in sql:
                return Cursor({"attempts": 1})
            if "count(*)" in sql:
                return Cursor({"total": total[0]})
            return Cursor()

    @contextmanager
    def connect(location, **kwargs):
        connections.append(kwargs)
        yield Connection()
        commits.append(True)

    monkeypatch.setattr(psycopg, "connect", connect)
    repo = RecruitmentRepository("postgresql://fixture", clock=lambda: NOW)
    repo.save_application("person@example.org", POLICY_VERSION, 30, retention_enabled=True)
    sql = "\n".join(statement for statement, _ in statements)
    assert statements[2][0].startswith("select pg_advisory_xact_lock")
    assert "enable row level security" in sql and "revoke all" in sql
    assert "on conflict(email) do nothing" in sql and "returning attempts" in sql
    assert "%s" in sql and "?" not in sql and "person@example.org" not in sql
    assert "set local statement_timeout = '3000ms'" in sql
    assert "set local lock_timeout = '2000ms'" in sql and connections[0]["connect_timeout"] == 3
    assert "options" not in connections[0]  # Preserve any DSN search_path options.
    total[0] = 1000
    statements.clear()
    with pytest.raises(RecruitmentLimitError, match="^recruitment_capacity_reached$"):
        repo.save_application("person@example.org", POLICY_VERSION, 30, retention_enabled=True)
    assert len(commits) == 2  # Capacity is reported only after the quota transaction commits.
    assert not any("where email=" in sql or sql.startswith("insert into beta_recruitment_applications")
                   for sql, _ in statements)
    total[0] = 0
    fail[0] = True
    with pytest.raises(RecruitmentPersistenceError, match="^recruitment_unavailable$") as raised:
        repo.save_application("person@example.org", POLICY_VERSION, 30, retention_enabled=True)
    assert raised.value.__cause__ is None
    assert len(commits) == 2
