from __future__ import annotations

import os
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from contextlib import closing, contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.admin_schemas import AdminBetaApplication, AdminBetaApplicationsResponse
from app.services.persistence import DEFAULT_API_DATA_PATH


class RecruitmentPersistenceError(RuntimeError):
    pass


class RecruitmentLimitError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class RecruitmentRepository:
    """Lazy, beta-only persistence; every write shares one database admission lock."""

    def __init__(self, location: str, *, clock: Callable[[], datetime] | None = None):
        self._location = location
        self._postgres = location.startswith(("postgres://", "postgresql://"))
        self._clock = clock or (lambda: datetime.now(UTC))

    def _sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self._postgres else statement

    @contextmanager
    def _connection(self) -> Iterator:
        if self._postgres:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError:
                raise RecruitmentPersistenceError("recruitment_unavailable") from None
            try:
                with psycopg.connect(self._location, row_factory=dict_row, connect_timeout=3) as conn:
                    conn.execute("set local statement_timeout = '3000ms'")
                    conn.execute("set local lock_timeout = '2000ms'")
                    conn.execute("select pg_advisory_xact_lock(1894738271)")
                    yield conn
            except psycopg.Error:
                raise RecruitmentPersistenceError("recruitment_unavailable") from None
            return
        try:
            if self._location != ":memory:":
                Path(self._location).parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self._location, timeout=3)) as conn:
                conn.row_factory = sqlite3.Row
                with conn:
                    conn.execute("begin immediate")
                    yield conn
        except (sqlite3.Error, OSError, ValueError):
            raise RecruitmentPersistenceError("recruitment_unavailable") from None

    def _ensure_schema(self, conn) -> None:
        conn.execute("create table if not exists beta_recruitment_applications ("
                     "id text primary key, email text not null unique, adult_confirmed integer not null check(adult_confirmed=1), "
                     "privacy_consent integer not null check(privacy_consent=1), policy_version text not null, "
                     "created_at text not null, expires_at text not null)")
        conn.execute("create index if not exists beta_recruitment_expiry_idx on beta_recruitment_applications(expires_at)")
        conn.execute("create table if not exists beta_recruitment_admission ("
                     "id integer primary key check(id=1), window_id bigint not null, attempts integer not null)")
        if self._postgres:
            for table in ("beta_recruitment_applications", "beta_recruitment_admission"):
                conn.execute(f"alter table {table} enable row level security")
                conn.execute(f"revoke all on {table} from public")

    def _purge(self, conn, now: str) -> int:
        return conn.execute(self._sql("delete from beta_recruitment_applications where expires_at<=?"), (now,)).rowcount

    def save_application(self, email: str, policy_version: str, retention_days: int, *, retention_enabled: bool) -> None:
        if not retention_enabled or not 1 <= retention_days <= 90:
            raise RecruitmentPersistenceError("recruitment_retention_required")
        with self._connection() as conn:
            self._ensure_schema(conn)
            now = self._clock().astimezone(UTC)
            self._purge(conn, now.isoformat(timespec="microseconds"))
            window = int(now.timestamp()) // 3600
            admitted = conn.execute(self._sql(
                "insert into beta_recruitment_admission(id,window_id,attempts) values(1,?,1) "
                "on conflict(id) do update set attempts=case when beta_recruitment_admission.window_id<excluded.window_id "
                "then 1 else beta_recruitment_admission.attempts+1 end, "
                "window_id=case when beta_recruitment_admission.window_id<excluded.window_id "
                "then excluded.window_id else beta_recruitment_admission.window_id end "
                "where beta_recruitment_admission.window_id<excluded.window_id or beta_recruitment_admission.attempts<100 "
                "returning attempts"), (window,)).fetchone()
            if admitted is None:
                raise RecruitmentLimitError("recruitment_rate_limited")
            capacity_reached = conn.execute(
                "select count(*) as total from beta_recruitment_applications"
            ).fetchone()["total"] >= 1000
            if not capacity_reached:
                conn.execute(self._sql(
                    "insert into beta_recruitment_applications(id,email,adult_confirmed,privacy_consent,policy_version,created_at,expires_at) "
                    "values(?,?,1,1,?,?,?) on conflict(email) do nothing"),
                    (str(uuid4()), email, policy_version, now.isoformat(timespec="microseconds"),
                     (now + timedelta(days=retention_days)).isoformat(timespec="microseconds")))
        # Report capacity after commit so rejected requests still consume the shared quota.
        if capacity_reached:
            raise RecruitmentLimitError("recruitment_capacity_reached")

    def purge_expired(self, *, retention_enabled: bool) -> int:
        if not retention_enabled:
            return 0
        with self._connection() as conn:
            self._ensure_schema(conn)
            return self._purge(conn, self._clock().astimezone(UTC).isoformat(timespec="microseconds"))

    def list_applications(self, *, limit: int = 50, offset: int = 0) -> AdminBetaApplicationsResponse:
        if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
            raise ValueError("invalid_recruitment_page")
        now = self._clock().astimezone(UTC)
        cutoff = now.isoformat(timespec="microseconds")
        with self._connection() as conn:
            # Viewing an unopened intake must not create tables or purge stored applications.
            if self._postgres:
                exists = conn.execute("select to_regclass('beta_recruitment_applications') as relation").fetchone()["relation"]
            else:
                exists = conn.execute(
                    "select name from sqlite_master where type='table' and name=?",
                    ("beta_recruitment_applications",),
                ).fetchone()
            if not exists:
                total, rows = 0, []
            else:
                total = conn.execute(self._sql(
                    "select count(*) as total from beta_recruitment_applications where expires_at>?"
                ), (cutoff,)).fetchone()["total"]
                rows = conn.execute(self._sql(
                    "select id,email,created_at from beta_recruitment_applications where expires_at>? "
                    "order by created_at desc,id desc limit ? offset ?"
                ), (cutoff, limit, offset)).fetchall()
        return AdminBetaApplicationsResponse(
            generated_at=now, total=total, limit=limit, offset=offset,
            applications=[AdminBetaApplication(**dict(row)) for row in rows],
        )


def get_recruitment_repository(environ: Mapping[str, str] | None = None) -> RecruitmentRepository:
    env = os.environ if environ is None else environ
    location = env.get("DATABASE_URL") or env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)
    return RecruitmentRepository(location)
