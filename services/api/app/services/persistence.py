from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from time import monotonic
from typing import Protocol
from uuid import uuid4

from app.schemas import (
    AnalysisJobCreateResponse,
    AnalysisJobRequest,
    AnalysisJobResponse,
    ClarificationRequest,
    ClarificationResponse,
    ImageUploadRequest,
    MealLogRequest,
    SavedImpactResponse,
)

DEFAULT_API_DATA_PATH = Path(__file__).resolve().parents[2] / ".local" / "cal-ai-api.db"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _dump_model(model: object) -> str:
    if hasattr(model, "model_dump"):
        return json.dumps(model.model_dump(mode="json", by_alias=True), ensure_ascii=False, sort_keys=True)
    return json.dumps(model, ensure_ascii=False, sort_keys=True)


def _load_json(value: str) -> object:
    return json.loads(value)


@dataclass(frozen=True)
class ImageUploadRecord:
    image_upload_id: str
    image_reference: str
    local_asset_id: str
    file_name: str
    content_type: str
    byte_size: int
    created_at: str
    storage_provider: str = "local"
    object_key: str | None = None
    upload_status: str = "ready"
    cleanup_after: str | None = None
    soft_limit_exceeded: bool = False
    upload_expires_at: str | None = None
    owner_id: str | None = None
    storage_namespace: str | None = None


@dataclass(frozen=True)
class AnalysisJobRecord:
    analysis_job_id: str
    image_upload_id: str
    image_reference: str
    meal_type: str
    optional_note: str | None
    status: str
    request: AnalysisJobRequest
    create_response: AnalysisJobCreateResponse
    response: AnalysisJobResponse | None
    created_at: str
    updated_at: str
    owner_id: str | None = None


@dataclass(frozen=True)
class ClarificationRecord:
    clarification_id: str
    analysis_job_id: str
    request: ClarificationRequest
    response: ClarificationResponse
    created_at: str


@dataclass(frozen=True)
class MealLogRecord:
    meal_log_id: str
    analysis_job_id: str
    result_id: str
    clarification_value: str
    request: MealLogRequest
    response: SavedImpactResponse
    created_at: str


class PersistenceError(RuntimeError):
    """Raised when local persistence cannot read or write safely."""


class PersistenceRepository(Protocol):
    def prepare_account_deletion(self) -> None: ...

    def get_account_deletion_stage(self, owner_id: str) -> int | None: ...

    def begin_account_deletion(self, owner_id: str) -> int: ...

    def advance_account_deletion(self, owner_id: str, stage: int, *, lease_token: str) -> None: ...

    def process_account_deletion_batch(
        self, owner_id: str, lease_token: str, *, batch_size: int = 100, timeout_seconds: float = 2,
    ) -> bool: ...

    def list_pending_account_deletions(self, limit: int) -> list[str]: ...

    def claim_account_deletion(self, owner_id: str, lease_token: str) -> bool: ...

    def release_account_deletion(self, owner_id: str, lease_token: str) -> None: ...

    def account_identity_deleted(self, owner_id: str) -> bool: ...

    def mark_account_identity_deleted(self, owner_id: str, *, lease_token: str) -> None: ...

    def account_storage_uncertain(self, owner_id: str) -> bool: ...

    def account_storage_cleanup_complete(self, owner_id: str) -> bool: ...

    def account_deletion_lease_current(self, owner_id: str, lease_token: str) -> bool: ...

    def list_account_deletion_objects(self, owner_id: str, limit: int) -> list[dict]: ...

    def mark_account_deletion_object_swept(
        self, owner_id: str, image_upload_id: str, *, lease_token: str, erase_verified: bool = False,
        storage_namespace: str | None = None,
    ) -> None: ...

    def save_image_upload(
        self,
        *,
        payload: ImageUploadRequest,
        image_upload_id: str,
        image_reference: str,
        storage_provider: str = "local",
        object_key: str | None = None,
        upload_status: str = "ready",
        cleanup_after: str | None = None,
        soft_limit_exceeded: bool = False,
        upload_expires_at: str | None = None,
        owner_id: str | None = None,
        storage_namespace: str | None = None,
    ) -> ImageUploadRecord: ...

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None: ...

    def sum_image_upload_bytes(self) -> int: ...

    def check_ready(self) -> None: ...

    def list_expired_image_uploads(self, now_iso: str, *, limit: int = 100) -> list[ImageUploadRecord]: ...

    def mark_image_upload_deleting(self, image_upload_id: str) -> bool: ...

    def mark_image_upload_deleted(self, image_upload_id: str) -> bool: ...

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
        owner_id: str | None = None,
    ) -> AnalysisJobRecord: ...

    def save_analysis_job_response(self, response: AnalysisJobResponse) -> AnalysisJobRecord | None: ...

    def get_analysis_job(self, analysis_job_id: str) -> AnalysisJobRecord | None: ...

    def list_analysis_jobs(self) -> list[AnalysisJobRecord]: ...

    def save_clarification(
        self,
        *,
        analysis_job_id: str,
        payload: ClarificationRequest,
        response: ClarificationResponse,
    ) -> ClarificationRecord: ...

    def list_clarifications(self, analysis_job_id: str) -> list[ClarificationRecord]: ...

    def save_meal_log(
        self,
        *,
        payload: MealLogRequest,
        response: SavedImpactResponse,
        meal_log_id: str | None = None,
    ) -> MealLogRecord: ...

    def list_meal_logs(self, analysis_job_id: str | None = None) -> list[MealLogRecord]: ...

    def get_meal_log(self, meal_log_id: str) -> MealLogRecord | None: ...

    def delete_meal_log(self, meal_log_id: str) -> bool: ...

    def delete_profile_artifacts(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]: ...

    def list_profile_image_uploads(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]: ...


class AccountDeletionPersistence:
    """Shared SQL cleanup and a minimal, permanent subject tombstone."""

    _account_postgres = False
    _account_guard_version = 3

    def _account_clock(self, column: str, operator: str = ">") -> str:
        if self._account_postgres:
            return f"{column}::timestamptz {operator} clock_timestamp()"
        return f"julianday({column}) {operator} julianday('now')"

    def _account_time(self, seconds: int = 0) -> str:
        if self._account_postgres:
            return f"(clock_timestamp() + interval '{seconds} seconds')::text"
        return f"strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now', '{seconds:+d} seconds')"

    def _account_transaction_limits(self, conn, seconds: float = 2) -> None:
        if not 0 < seconds <= 10:
            raise ValueError("invalid_account_deletion_timeout")
        milliseconds = str(max(1, int(seconds * 1000)))
        if self._account_postgres:
            conn.execute("set transaction isolation level read committed")
            conn.execute("select set_config('statement_timeout', %s, true)", (milliseconds,))
            conn.execute("select set_config('lock_timeout', %s, true)", (milliseconds,))
        else:
            conn.execute(f"pragma busy_timeout = {milliseconds}")
            conn.execute("begin immediate")

    def prepare_account_deletion(self) -> None:
        """Explicit migration, before enabling deletion; never called by an HTTP request/worker."""
        with self._connection() as conn:
            self._account_transaction_limits(conn, 10)
            if self._account_postgres:
                conn.execute("select pg_advisory_xact_lock(1480534353, 2)")
            row = conn.execute("select version from account_deletion_schema where id = 1").fetchone()
            if row and row["version"] == self._account_guard_version:
                return
            self._install_account_write_guards(conn)
            conn.execute(
                self._account_sql("insert into account_deletion_schema (id, version) values (1, ?) "
                                  "on conflict(id) do update set version = excluded.version"),
                (self._account_guard_version,),
            )

    def _require_account_schema(self, conn) -> None:
        row = conn.execute("select version from account_deletion_schema where id = 1").fetchone()
        if not row or row["version"] != self._account_guard_version:
            raise PersistenceError("account_deletion_schema_unavailable")

    def _require_account_lease(self, conn, owner_id, lease_token, *, lock=False):
        if not lease_token:
            raise PersistenceError("account_deletion_lease_lost")
        suffix = " for update" if lock and self._account_postgres else ""
        row = conn.execute(
            self._account_sql("select * from account_deletion_work where owner_id = ? "
                              f"and lease_token = ? and {self._account_clock('lease_until')}{suffix}"),
            (owner_id, lease_token),
        ).fetchone()
        if row is None:
            raise PersistenceError("account_deletion_lease_lost")
        return row

    @contextmanager
    def _account_deletion_transaction(self, owner_id, lease_token, *, timeout_seconds=2):
        with self._connection() as conn:
            self._account_transaction_limits(conn, timeout_seconds)
            self._require_account_schema(conn)
            self._require_account_lease(conn, owner_id, lease_token, lock=True)
            backend = "pg_backend_pid()::text" if self._account_postgres else "'sqlite'"
            conn.execute(
                self._account_sql("insert into account_deletion_mutations (owner_id, lease_token, backend_id) "
                                  f"values (?, ?, {backend}) on conflict(owner_id) do update set "
                                  "lease_token = excluded.lease_token, backend_id = excluded.backend_id"),
                (owner_id, lease_token),
            )
            yield conn
            # The locked lease row prevents reclaim; expiry is rechecked before commit too.
            self._require_account_lease(conn, owner_id, lease_token)
            conn.execute(self._account_sql("delete from account_deletion_mutations where owner_id = ?"), (owner_id,))

    def _account_sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self._account_postgres else statement

    def get_account_deletion_stage(self, owner_id: str) -> int | None:
        with self._connection() as conn:
            row = conn.execute(
                self._account_sql("select stage from account_deletions where owner_id = ?"),
                (owner_id,),
            ).fetchone()
        return int(row["stage"]) if row else None

    def begin_account_deletion(self, owner_id: str) -> int:
        with self._connection() as conn:
            self._account_transaction_limits(conn)
            self._require_account_schema(conn)
            # Every guarded writer holds this owner row until commit, including DELETEs.
            conn.execute(
                self._account_sql("insert into account_owner_state (owner_id, deleting) values (?, 1) "
                                  "on conflict(owner_id) do update set deleting = 1"),
                (owner_id,),
            )
            conn.execute(
                self._account_sql(
                    "insert into account_deletions (owner_id, stage, started_at, updated_at) "
                    "values (?, 0, ?, ?) on conflict(owner_id) do nothing"
                ),
                (owner_id, _now_iso(), _now_iso()),
            )
            row = conn.execute(
                self._account_sql("select stage from account_deletions where owner_id = ?"),
                (owner_id,),
            ).fetchone()
            phase = "profiles" if int(row["stage"]) == 0 else "done"
            conn.execute(self._account_sql("insert into account_deletion_work (owner_id, phase) values (?, ?) "
                                          "on conflict(owner_id) do nothing"), (owner_id, phase))
        return int(row["stage"])

    def advance_account_deletion(self, owner_id: str, stage: int, *, lease_token: str) -> None:
        if stage not in {1, 2, 3}:
            raise ValueError("invalid_account_deletion_stage")
        with self._account_deletion_transaction(owner_id, lease_token) as conn:
            work = self._require_account_lease(conn, owner_id, lease_token)
            current = conn.execute(self._account_sql("select stage from account_deletions where owner_id = ?"),
                                   (owner_id,)).fetchone()["stage"]
            if work["phase"] != "done" or current < stage - 1:
                raise PersistenceError("account_deletion_stage_incomplete")
            if stage >= 2 and not work["identity_deleted"]:
                raise PersistenceError("account_deletion_identity_pending")
            if stage == 3 and not self._account_storage_complete(conn, owner_id):
                raise PersistenceError("account_deletion_storage_pending")
            conn.execute(self._account_sql("update account_deletions set stage = ?, updated_at = ? "
                                          "where owner_id = ? and stage < ?"),
                         (stage, _now_iso(), owner_id, stage))

    def list_pending_account_deletions(self, limit: int) -> list[str]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid_account_deletion_batch")
        aged = ("d.updated_at::timestamptz <= clock_timestamp() - interval '24 hours'" if self._account_postgres
                else "julianday(d.updated_at) <= julianday('now', '-1 day')")
        with self._connection() as conn:
            rows = conn.execute(
                self._account_sql(
                    "select d.owner_id from account_deletions d left join account_deletion_work w "
                    "on w.owner_id = d.owner_id where d.stage < 3 "
                    f"and (w.lease_until is null or {self._account_clock('w.lease_until', '<=')}) "
                    f"and (w.next_attempt_at is null or {self._account_clock('w.next_attempt_at', '<=')}) "
                    f"order by case when ({aged}) or d.stage < 2 or coalesce(w.identity_deleted, 0) = 0 "
                    "or exists (select 1 from account_deletion_objects o where o.owner_id = d.owner_id "
                    "and o.sweep_count = 0 and o.erase_verified = 0) then 0 else 1 end, "
                    "d.updated_at, d.owner_id limit ?"
                ),
                (limit,),
            ).fetchall()
        return [row["owner_id"] for row in rows]

    def claim_account_deletion(self, owner_id: str, lease_token: str) -> bool:
        with self._connection() as conn:
            self._account_transaction_limits(conn)
            self._require_account_schema(conn)
            conn.execute(
                self._account_sql(
                    "insert into account_deletion_work (owner_id, phase) "
                    "select owner_id, case when stage = 0 then 'profiles' else 'done' end "
                    "from account_deletions where owner_id = ? and stage < 3 "
                    "on conflict(owner_id) do nothing"
                ),
                (owner_id,),
            )
            cursor = conn.execute(
                self._account_sql(
                    f"update account_deletion_work set lease_token = ?, lease_until = {self._account_time(300)} "
                    f"where owner_id = ? and (lease_until is null or {self._account_clock('lease_until', '<=')}) "
                    f"and (next_attempt_at is null or {self._account_clock('next_attempt_at', '<=')}) "
                    "and exists (select 1 from account_deletions d where "
                    "d.owner_id = account_deletion_work.owner_id and d.stage < 3)"
                ),
                (lease_token, owner_id),
            )
        return cursor.rowcount > 0

    def release_account_deletion(self, owner_id: str, lease_token: str) -> None:
        with self._connection() as conn:
            self._account_transaction_limits(conn)
            cursor = conn.execute(
                self._account_sql(
                    "update account_deletion_work set lease_token = null, lease_until = null, "
                    "next_attempt_at = case when identity_deleted = 1 and phase = 'done' "
                    "and not exists (select 1 from account_deletion_objects o where "
                    "o.owner_id = account_deletion_work.owner_id and o.sweep_count = 0 "
                    f"and o.erase_verified = 0) then {self._account_time(3600)} else null end "
                    "where owner_id = ? and lease_token = ?"
                ),
                (owner_id, lease_token),
            )
            if cursor.rowcount:
                conn.execute(
                    self._account_sql("update account_deletions set updated_at = ? where owner_id = ?"),
                    (datetime.now(UTC).isoformat(), owner_id),
                )

    def account_deletion_lease_current(self, owner_id: str, lease_token: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                self._account_sql(
                    "select owner_id from account_deletion_work "
                    f"where owner_id = ? and lease_token = ? and {self._account_clock('lease_until')}"
                ),
                (owner_id, lease_token),
            ).fetchone()
        return row is not None

    def account_identity_deleted(self, owner_id: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                self._account_sql("select identity_deleted from account_deletion_work where owner_id = ?"),
                (owner_id,),
            ).fetchone()
        return bool(row and row["identity_deleted"])

    def mark_account_identity_deleted(self, owner_id: str, *, lease_token: str) -> None:
        with self._account_deletion_transaction(owner_id, lease_token) as conn:
            stage = conn.execute(self._account_sql("select stage from account_deletions where owner_id = ?"),
                                 (owner_id,)).fetchone()["stage"]
            if stage not in {1, 2}:
                raise PersistenceError("account_deletion_stage_incomplete")
            conn.execute(
                self._account_sql("update account_deletion_work set identity_deleted = 1 where owner_id = ?"),
                (owner_id,),
            )
            conn.execute(self._account_sql("update account_deletions set stage = 2, updated_at = ? where owner_id = ?"),
                         (_now_iso(), owner_id))

    def account_storage_uncertain(self, owner_id: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                self._account_sql("select storage_uncertain from account_deletion_work where owner_id = ?"),
                (owner_id,),
            ).fetchone()
        return bool(row and row["storage_uncertain"])

    def account_storage_cleanup_complete(self, owner_id: str) -> bool:
        with self._connection() as conn:
            return self._account_storage_complete(conn, owner_id)

    def _account_storage_complete(self, conn, owner_id):
        work = conn.execute(self._account_sql("select storage_uncertain from account_deletion_work where owner_id = ?"),
                            (owner_id,)).fetchone()
        if not work or work["storage_uncertain"]:
            return False
        row = conn.execute(self._account_sql("select 1 from account_deletion_objects where owner_id = ? "
                                            "and ((storage_provider != 'local' and "
                                            "(erase_verified = 0 or storage_namespace is null or storage_namespace = '')) "
                                            "or (storage_provider = 'local' and sweep_count = 0)) limit 1"), (owner_id,)).fetchone()
        return row is None

    def _save_account_deletion_objects(self, conn, owner_id, uploads):
        for upload in uploads:
            if not upload.object_key and upload.storage_provider != "local":
                conn.execute(
                    self._account_sql(
                        "insert into account_deletion_work (owner_id, storage_uncertain) values (?, 1) "
                        "on conflict(owner_id) do update set storage_uncertain = 1"
                    ),
                    (owner_id,),
                )
            if upload.object_key:
                conn.execute(
                    self._account_sql(
                        "insert into account_deletion_objects "
                        "(owner_id, image_upload_id, storage_provider, object_key, storage_namespace) values (?, ?, ?, ?, ?) "
                        "on conflict(owner_id, image_upload_id) do nothing"
                    ),
                    (owner_id, upload.image_upload_id, upload.storage_provider, upload.object_key, upload.storage_namespace),
                )
                existing = conn.execute(self._account_sql(
                    "select storage_provider, object_key, storage_namespace from account_deletion_objects "
                    "where owner_id = ? and image_upload_id = ?"), (owner_id, upload.image_upload_id)).fetchone()
                if existing is None or (existing["storage_provider"], existing["object_key"], existing["storage_namespace"]) != (
                    upload.storage_provider, upload.object_key, upload.storage_namespace
                ):
                    raise PersistenceError("account_deletion_manifest_conflict")

    def list_account_deletion_objects(self, owner_id: str, limit: int) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid_account_deletion_batch")
        with self._connection() as conn:
            rows = conn.execute(
                self._account_sql(
                    "select * from account_deletion_objects where owner_id = ? "
                    "and erase_verified = 0 and (storage_provider != 'local' or sweep_count = 0) "
                    "order by sweep_count, coalesce(last_swept_at, ''), image_upload_id limit ?"
                ),
                (owner_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_account_deletion_object_swept(
        self, owner_id: str, image_upload_id: str, *, lease_token: str, erase_verified: bool = False,
        storage_namespace: str | None = None,
    ) -> None:
        if type(erase_verified) is not bool:
            raise ValueError("invalid_account_deletion_verification")
        with self._account_deletion_transaction(owner_id, lease_token) as conn:
            item = conn.execute(self._account_sql("select storage_provider, storage_namespace from account_deletion_objects "
                                                 "where owner_id = ? and image_upload_id = ?"),
                                (owner_id, image_upload_id)).fetchone()
            if item and item["storage_provider"] != "local" and (
                not storage_namespace or item["storage_namespace"] != storage_namespace
            ):
                raise PersistenceError("account_deletion_storage_namespace_mismatch")
            conn.execute(
                self._account_sql(
                    "update account_deletion_objects set last_swept_at = ?, sweep_count = sweep_count + 1, "
                    "erase_verified = case when erase_verified = 1 then 1 else ? end "
                    "where owner_id = ? and image_upload_id = ?"
                ),
                (datetime.now(UTC).isoformat(), int(erase_verified), owner_id, image_upload_id),
            )
            # Local URIs have no writable remote object; do not retain their unnecessary keys.
            conn.execute(self._account_sql("delete from account_deletion_objects where owner_id = ? "
                                          "and image_upload_id = ? and storage_provider = 'local' and sweep_count > 0"),
                         (owner_id, image_upload_id))

    @staticmethod
    def _account_worker_schema() -> tuple[str, ...]:
        return (
            "create table if not exists account_deletion_work (owner_id text primary key, "
            "identity_deleted integer not null default 0, storage_uncertain integer not null default 0, "
            "lease_token text, lease_until text, phase text not null default 'profiles', "
            "cursor text not null default '', next_attempt_at text)",
            "create table if not exists account_deletion_objects (owner_id text not null, "
            "image_upload_id text not null, storage_provider text not null, object_key text not null, "
            "last_swept_at text, sweep_count integer not null default 0, erase_verified integer not null default 0, "
            "storage_namespace text, "
            "primary key (owner_id, image_upload_id))",
            "create index if not exists account_deletion_objects_sweep "
            "on account_deletion_objects (owner_id, sweep_count, last_swept_at, image_upload_id)",
            "create table if not exists account_deletion_schema (id integer primary key, version integer not null)",
            "create table if not exists account_owner_state (owner_id text primary key, deleting integer not null default 0)",
            "create table if not exists account_deletion_refs (owner_id text not null, kind text not null, "
            "ref_id text not null, primary key (owner_id, kind, ref_id))",
            "create table if not exists account_deletion_mutations (owner_id text primary key, "
            "lease_token text not null, backend_id text not null)",
        )

    def _ensure_account_worker_columns(self, conn):
        additions = {
            "account_deletion_work": {"phase": "text not null default 'profiles'", "cursor": "text not null default ''",
                                      "next_attempt_at": "text"},
            "account_deletion_objects": {"erase_verified": "integer not null default 0", "storage_namespace": "text"},
            "image_uploads": {"storage_namespace": "text"},
        }
        for table, columns in additions.items():
            existing = set() if self._account_postgres else {
                row["name"] for row in conn.execute(f"pragma table_info({table})").fetchall()
            }
            for name, definition in columns.items():
                if self._account_postgres or name not in existing:
                    optional = "if not exists " if self._account_postgres else ""
                    conn.execute(f"alter table {table} add column {optional}{name} {definition}")

    def _mark_retention_upload(self, image_upload_id, *, deleted):
        with self._connection() as conn:
            self._account_transaction_limits(conn)
            suffix = " for update" if self._account_postgres else ""
            row = conn.execute(self._account_sql("select owner_id from image_uploads where image_upload_id = ?" + suffix),
                               (image_upload_id,)).fetchone()
            if row is None:
                return False
            owner = row["owner_id"]
            if owner is not None:
                state = conn.execute(
                    self._account_sql("insert into account_owner_state (owner_id, deleting) values (?, 0) "
                                      "on conflict(owner_id) do update set deleting = account_owner_state.deleting returning deleting"),
                    (owner,),
                ).fetchone()
                tombstone = conn.execute(self._account_sql("select 1 from account_deletions where owner_id = ?"), (owner,)).fetchone()
                if state["deleting"] or tombstone:
                    return False
            if deleted:
                # Retain the random key: a legacy/ownerless late PUT must remain discoverable.
                conn.execute(self._account_sql("update image_uploads set image_reference = ?, upload_status = 'deleted' "
                                              "where image_upload_id = ?"), (f"deleted://{image_upload_id}", image_upload_id))
            else:
                cursor = conn.execute(self._account_sql("update image_uploads set upload_status = 'deleting' "
                                                       "where image_upload_id = ? and upload_status != 'deleted'"), (image_upload_id,))
                return cursor.rowcount > 0
            return True

    def _original_upload_namespace(self, conn, image_upload_id, namespace):
        row = conn.execute(self._account_sql("select storage_namespace from image_uploads where image_upload_id = ?"),
                           (image_upload_id,)).fetchone()
        if row is not None:
            if namespace is not None and row["storage_namespace"] != namespace:
                raise PersistenceError("image_upload_storage_namespace_immutable")
            return row["storage_namespace"]
        return namespace

    def _profile_artifact_ids(self, conn, owner_id, profile_id, body_image_ids):
        job_profile = self._account_json("j.request_json", "profile_id")
        log_profile = self._account_json("m.request_json", "profile_id")
        rows = conn.execute(
            self._account_sql(
                "select j.analysis_job_id from analysis_jobs j "
                "where (j.owner_id = ? or j.owner_id is null) "
                f"and ({job_profile} = ? or ({job_profile} is null and exists "
                "(select 1 from meal_logs m where m.analysis_job_id = j.analysis_job_id "
                f"and {log_profile} = ?))) "
                "and not exists (select 1 from meal_logs m where "
                f"m.analysis_job_id = j.analysis_job_id and {log_profile} != ?)"
            ),
            (owner_id, profile_id, profile_id, profile_id),
        ).fetchall()
        job_ids = [row["analysis_job_id"] for row in rows]
        job_marks = ",".join("?" for _ in job_ids) or "null"
        body_marks = ",".join("?" for _ in body_image_ids) or "null"
        remaining_filter = f"remaining.analysis_job_id not in ({job_marks})" if job_ids else "1 = 1"
        table_query = (
            "select tablename as name from pg_tables where schemaname = current_schema()"
            if self._account_postgres else "select name from sqlite_master where type = 'table'"
        )
        has_events = any(row["name"] == "coach_events" for row in conn.execute(table_query).fetchall())
        body_guard = (
            "and not exists (select 1 from coach_events e where e.event_type = 'body' "
            f"and e.profile_id != ? and {self._account_json('e.payload_json', 'image_upload_id')} "
            "= u.image_upload_id)" if has_events else ""
        )
        rows = conn.execute(
            self._account_sql(
                "select u.* from image_uploads u where (u.owner_id = ? or u.owner_id is null) "
                f"and (u.image_upload_id in ({body_marks}) or u.image_upload_id in "
                f"(select image_upload_id from analysis_jobs where analysis_job_id in ({job_marks}))) "
                "and not exists (select 1 from analysis_jobs remaining where "
                "remaining.image_upload_id = u.image_upload_id "
                f"and {remaining_filter}) {body_guard}"
            ),
            (owner_id, *body_image_ids, *job_ids, *job_ids, *((profile_id,) if has_events else ())),
        ).fetchall()
        return job_ids, [SQLitePersistenceRepository._image_upload_from_row(row) for row in rows]

    def _list_owned_profile_uploads(self, owner_id, profile_id, body_image_ids):
        with self._connection() as conn:
            _, uploads = self._profile_artifact_ids(conn, owner_id, profile_id, body_image_ids)
        return uploads

    def _delete_owned_profile_artifacts(self, owner_id, profile_id, body_image_ids):
        with self._connection() as conn:
            job_ids, uploads = self._profile_artifact_ids(conn, owner_id, profile_id, body_image_ids)
            job_marks = ",".join("?" for _ in job_ids) or "null"
            conn.execute(
                self._account_sql(
                    f"delete from meal_logs where {self._account_json('request_json', 'profile_id')} = ? "
                    "and (not exists (select 1 from analysis_jobs j where "
                    "j.analysis_job_id = meal_logs.analysis_job_id) "
                    f"or analysis_job_id in ({job_marks}))"
                ),
                (profile_id, *job_ids),
            )
            for job_id in job_ids:
                for table in ("clarifications", "meal_logs", "analysis_jobs"):
                    conn.execute(self._account_sql(f"delete from {table} where analysis_job_id = ?"), (job_id,))
            for upload in uploads:
                conn.execute(
                    self._account_sql("delete from image_uploads where image_upload_id = ?"),
                    (upload.image_upload_id,),
                )
        return uploads

    def _account_json(self, column: str, key: str) -> str:
        if self._account_postgres:
            return f"({column}::jsonb ->> '{key}')"
        return f"json_extract({column}, '$.{key}')"

    @staticmethod
    def _account_ref(kind, column):
        return ("exists (select 1 from account_deletion_refs r where r.owner_id = ? "
                f"and r.kind = '{kind}' and r.ref_id = {column})")

    def _account_batch_specs(self):
        profile = lambda column: self._account_ref("profile", column)
        job = lambda column: self._account_ref("job", column)
        session = lambda column: self._account_ref("session", column)
        job_profile = self._account_json("t.request_json", "profile_id")
        body_image = self._account_json("e.payload_json", "image_upload_id")
        return {
            "profiles": ("coach_profiles", "profile_id", f"{self._account_json('t.payload_json', 'owner_id')} = ?", "profile"),
            "jobs": ("analysis_jobs", "analysis_job_id", "t.owner_id = ? or (t.owner_id is null and ("
                     f"{profile(job_profile)} or exists (select 1 from image_uploads u "
                     "where u.image_upload_id = t.image_upload_id and u.owner_id = ?)))", "job"),
            "sessions": ("app_sessions", "session_id", f"t.user_id = ? or (t.user_id is null and {profile('t.profile_id')})", "session"),
            "uploads": ("image_uploads", "image_upload_id", "t.owner_id = ? or (t.owner_id is null and ("
                        f"exists (select 1 from coach_events e where e.event_type = 'body' and {body_image} "
                        f"= t.image_upload_id and {profile('e.profile_id')}) or exists (select 1 from analysis_jobs j "
                        f"where j.image_upload_id = t.image_upload_id and {job('j.analysis_job_id')})))", None),
            "clarifications": ("clarifications", "clarification_id", job("t.analysis_job_id"), None),
            "logs": ("meal_logs", "meal_log_id", f"{job('t.analysis_job_id')} or ({profile(job_profile)} "
                     "and not exists (select 1 from analysis_jobs j where j.analysis_job_id = t.analysis_job_id "
                     "and j.owner_id is not null and j.owner_id != ?))", None),
            "delete_jobs": ("analysis_jobs", "analysis_job_id", job("t.analysis_job_id"), None),
            "events": ("product_events", "event_id", "t.user_id = ? or (t.user_id is null and ("
                       f"{profile('t.profile_id')} or {session('t.session_id')}))", None),
            "delete_sessions": ("app_sessions", "session_id", session("t.session_id"), None),
            "users": ("app_users", "user_id", "t.user_id = ?", None),
            "subscriptions": ("billing_subscriptions", "subscription_id", "t.user_id = ?", None),
            "payments": ("billing_payments", "payment_id", "t.user_id = ?", None),
            "coach_events": ("coach_events", "event_id", profile("t.profile_id"), None),
            "plans": ("workout_plans", "plan_id", profile("t.profile_id"), None),
            "delete_profiles": ("coach_profiles", "profile_id", profile("t.profile_id"), None),
        }

    def _account_upload_retained(self, conn, owner_id, upload_id):
        condition = (
            "exists (select 1 from analysis_jobs j where j.image_upload_id = ? and not "
            f"{self._account_ref('job', 'j.analysis_job_id')}) or exists (select 1 from coach_events e "
            f"where e.event_type = 'body' and {self._account_json('e.payload_json', 'image_upload_id')} = ? "
            f"and not {self._account_ref('profile', 'e.profile_id')})"
        )
        return conn.execute(self._account_sql(f"select 1 where {condition}"),
                            (upload_id, owner_id, upload_id, owner_id)).fetchone() is not None

    def process_account_deletion_batch(
        self, owner_id: str, lease_token: str, *, batch_size: int = 100, timeout_seconds: float = 2,
    ) -> bool:
        if type(batch_size) is not int or not 1 <= batch_size <= 100:
            raise ValueError("invalid_account_deletion_batch")
        stop_at = monotonic() + timeout_seconds
        with self._account_deletion_transaction(owner_id, lease_token, timeout_seconds=timeout_seconds) as conn:
            work = self._require_account_lease(conn, owner_id, lease_token)
            stage = conn.execute(self._account_sql("select stage from account_deletions where owner_id = ?"),
                                 (owner_id,)).fetchone()["stage"]
            if stage != 0:
                return stage >= 1
            phase, cursor = work["phase"], work["cursor"]
            specs = self._account_batch_specs()
            if phase == "refs":
                refs = conn.execute(self._account_sql("select kind, ref_id from account_deletion_refs where owner_id = ? "
                                                      "order by kind, ref_id limit ?"), (owner_id, batch_size)).fetchall()
                for ref in refs:
                    conn.execute(self._account_sql("delete from account_deletion_refs where owner_id = ? and kind = ? and ref_id = ?"),
                                 (owner_id, ref["kind"], ref["ref_id"]))
                    if monotonic() >= stop_at:
                        break
                if refs:
                    return False
                conn.execute(self._account_sql("update account_deletion_work set phase = 'done', cursor = '' where owner_id = ?"), (owner_id,))
                conn.execute(self._account_sql("update account_deletions set stage = 1, updated_at = ? where owner_id = ? and stage = 0"),
                             (_now_iso(), owner_id))
                return True
            if phase not in specs:
                raise PersistenceError("account_deletion_phase_invalid")
            table, key, condition, ref_kind = specs[phase]
            suffix = " for update of t" if self._account_postgres else ""
            selection = f"select t.* from {table} t where ({condition}) and t.{key} > ? order by t.{key} limit ?{suffix}"
            params = (owner_id,) * condition.count("?") + (cursor, batch_size)
            batch = conn.execute(self._account_sql(selection), params).fetchall()
            for row in batch:
                if ref_kind:
                    conn.execute(self._account_sql("insert into account_deletion_refs (owner_id, kind, ref_id) values (?, ?, ?) "
                                                  "on conflict(owner_id, kind, ref_id) do nothing"), (owner_id, ref_kind, row[key]))
                elif phase == "uploads":
                    # Parent row locks in reference guards serialize late foreign links here.
                    if not self._account_upload_retained(conn, owner_id, row[key]):
                        self._save_account_deletion_objects(conn, owner_id, [SQLitePersistenceRepository._image_upload_from_row(row)])
                        conn.execute(self._account_sql("delete from image_uploads where image_upload_id = ?"), (row[key],))
                else:
                    conn.execute(self._account_sql(f"delete from {table} where {key} = ?"), (row[key],))
                cursor = row[key]
                if monotonic() >= stop_at:
                    break
            if not batch:
                phases = [*specs, "refs"]
                phase, cursor = phases[phases.index(phase) + 1], ""
            conn.execute(self._account_sql("update account_deletion_work set phase = ?, cursor = ? where owner_id = ?"),
                         (phase, cursor, owner_id))
            return False

    def _install_account_write_guards(self, conn):
        profile_owner = (
            "(select " + self._account_json("p.payload_json", "owner_id")
            + " from coach_profiles p where p.profile_id = NEW.profile_id)"
        )
        job_owner = "(select j.owner_id from analysis_jobs j where j.analysis_job_id = NEW.analysis_job_id)"
        missing_profile = "not exists (select 1 from coach_profiles p where p.profile_id = NEW.profile_id)"
        missing_job = "not exists (select 1 from analysis_jobs j where j.analysis_job_id = NEW.analysis_job_id)"
        json_profile_id = self._account_json("NEW.request_json", "profile_id")
        missing_json_profile = (
            f"({json_profile_id} is not null and not exists "
            f"(select 1 from coach_profiles p where p.profile_id = {json_profile_id}))"
        )
        json_profile_owner = ("(select " + self._account_json("p.payload_json", "owner_id")
                              + f" from coach_profiles p where p.profile_id = {json_profile_id})")
        image_owner = "(select u.owner_id from image_uploads u where u.image_upload_id = NEW.image_upload_id)"
        body_image_id = self._account_json("NEW.payload_json", "image_upload_id")
        body_image_owner = ("(select u.owner_id from image_uploads u where NEW.event_type = 'body' "
                            f"and u.image_upload_id = {body_image_id})")
        parent_checks = {
            "analysis_jobs": "not exists (select 1 from image_uploads u where "
                f"u.image_upload_id = NEW.image_upload_id) or {missing_json_profile}",
            "coach_events": f"{missing_profile} or (NEW.event_type = 'body' and {body_image_id} is not null "
                f"and not exists (select 1 from image_uploads u where u.image_upload_id = {body_image_id}))",
            "workout_plans": missing_profile,
            "clarifications": missing_job,
            "meal_logs": f"{missing_job} or {missing_json_profile}",
            "app_sessions": f"(NEW.profile_id is not null and {missing_profile})",
            "product_events": "not exists (select 1 from app_sessions s where "
                f"s.session_id = NEW.session_id) or (NEW.profile_id is not null and {missing_profile})",
        }
        expressions = {
            "image_uploads": ["NEW.owner_id"],
            "analysis_jobs": ["NEW.owner_id", image_owner, json_profile_owner],
            "coach_profiles": [self._account_json("NEW.payload_json", "owner_id")],
            "coach_events": [profile_owner, body_image_owner],
            "workout_plans": [profile_owner],
            "clarifications": [job_owner],
            "meal_logs": [job_owner, json_profile_owner],
            "app_users": ["NEW.user_id"],
            "app_sessions": ["NEW.user_id", profile_owner],
            "product_events": ["NEW.user_id", "(select s.user_id from app_sessions s "
                               "where s.session_id = NEW.session_id)", profile_owner],
            "billing_subscriptions": ["NEW.user_id"],
            "billing_payments": ["NEW.user_id"],
        }
        parent_locks = {
            "analysis_jobs": ["select 1 from image_uploads where image_upload_id = NEW.image_upload_id",
                              f"select 1 from coach_profiles where profile_id = {json_profile_id}"],
            "coach_events": ["select 1 from coach_profiles where profile_id = NEW.profile_id",
                             f"select 1 from image_uploads where NEW.event_type = 'body' and image_upload_id = {body_image_id}"],
            "workout_plans": ["select 1 from coach_profiles where profile_id = NEW.profile_id"],
            "clarifications": ["select 1 from analysis_jobs where analysis_job_id = NEW.analysis_job_id"],
            "meal_logs": ["select 1 from analysis_jobs where analysis_job_id = NEW.analysis_job_id",
                          f"select 1 from coach_profiles where profile_id = {json_profile_id}"],
            "app_sessions": ["select 1 from coach_profiles where profile_id = NEW.profile_id"],
            "product_events": ["select 1 from app_sessions where session_id = NEW.session_id",
                               "select 1 from coach_profiles where profile_id = NEW.profile_id"],
        }
        if self._account_postgres:
            rows = conn.execute(
                "select tablename as name from pg_tables where schemaname = current_schema()"
            ).fetchall()
        else:
            rows = conn.execute("select name from sqlite_master where type = 'table'").fetchall()
        tables = {row["name"] for row in rows}
        if not expressions.keys() <= tables:
            raise PersistenceError("account_deletion_schema_unavailable")
        backend = "m.backend_id = pg_backend_pid()::text and " if self._account_postgres else ""
        permit = ("exists (select 1 from account_deletion_mutations m join account_deletion_work w "
                  "on w.owner_id = m.owner_id and w.lease_token = m.lease_token where "
                  f"{backend}{self._account_clock('w.lease_until')})")
        for table, owners in expressions.items():
            legacy_delete = ("OLD.owner_id is null and OLD.storage_provider != 'local'"
                             if table == "image_uploads" else "false")
            if self._account_postgres:
                # Only the explicit migration takes table locks; request paths use owner rows.
                conn.execute(f"lock table {table} in share row exclusive mode")
                owner_values = owners + [owner.replace("NEW.", "OLD.") for owner in owners]
                parent_sql = " ".join("perform " + sql.removeprefix("select ") + " for share;"
                                      for sql in parent_locks.get(table, []))
                parent_check = parent_checks.get(table, "false")
                conn.execute(
                    f"create or replace function account_guard_{table}() returns trigger "
                    "language plpgsql security invoker set search_path from current as $$ "
                    "declare subject text; blocked integer; begin "
                    f"if TG_OP = 'DELETE' and {permit} then return OLD; end if; "
                    f"if TG_OP = 'DELETE' and ({legacy_delete}) then "
                    "raise exception 'account_deletion_in_progress'; end if; "
                    f"if TG_OP != 'DELETE' then {parent_sql} if {parent_check} then "
                    "raise exception 'account_deletion_in_progress'; end if; end if; "
                    f"for subject in select distinct value from unnest(array[{', '.join(owner_values)}]::text[]) "
                    "as owners(value) where value is not null order by value loop "
                    "insert into account_owner_state (owner_id, deleting) values (subject, 0) "
                    "on conflict(owner_id) do update set deleting = account_owner_state.deleting "
                    "returning deleting into blocked; "
                    "if blocked = 1 or exists (select 1 from account_deletions where owner_id = subject) then "
                    "raise exception 'account_deletion_in_progress'; end if; end loop; "
                    "if TG_OP = 'DELETE' then return OLD; end if; return NEW; end; $$"
                )
                conn.execute(f"revoke all on function account_guard_{table}() from public")
                conn.execute(f"drop trigger if exists account_guard on {table}")
                conn.execute(
                    f"create trigger account_guard before insert or update or delete on {table} "
                    f"for each row execute function account_guard_{table}()"
                )
            else:
                for operation in ("insert", "update", "delete"):
                    values = owners if operation == "insert" else [owner.replace("NEW.", "OLD.") for owner in owners]
                    if operation == "update":
                        values += owners
                    statements = []
                    if operation == "delete":
                        statements.append("select raise(abort, 'account_deletion_in_progress') "
                                          f"where {legacy_delete};")
                    for expression in values:
                        statements.append("insert into account_owner_state (owner_id, deleting) "
                                          f"select {expression}, 0 where {expression} is not null "
                                          "on conflict(owner_id) do update set deleting = account_owner_state.deleting;")
                        statements.append("select raise(abort, 'account_deletion_in_progress') where "
                                          f"exists (select 1 from account_owner_state where owner_id = {expression} and deleting = 1) "
                                          f"or exists (select 1 from account_deletions where owner_id = {expression});")
                    if operation != "delete" and table in parent_checks:
                        statements.append(f"select raise(abort, 'account_deletion_in_progress') where {parent_checks[table]};")
                    when = f"when not ({permit})" if operation == "delete" else ""
                    conn.execute(f"drop trigger if exists account_guard_{table}_{operation}")
                    conn.execute(
                        f"create trigger account_guard_{table}_{operation} "
                        f"before {operation} on {table} {when} begin {' '.join(statements)} end"
                    )
        for statement in (
            "create index if not exists account_deletions_queue_idx on account_deletions(stage, updated_at, owner_id)",
            "create index if not exists account_jobs_upload_idx on analysis_jobs(image_upload_id)",
            "create index if not exists account_jobs_owner_idx on analysis_jobs(owner_id, analysis_job_id)",
            "create index if not exists account_uploads_owner_idx on image_uploads(owner_id, image_upload_id)",
            f"create index if not exists account_profiles_owner_idx on coach_profiles(({self._account_json('payload_json', 'owner_id')}), profile_id)",
            f"create index if not exists account_body_image_idx on coach_events(({self._account_json('payload_json', 'image_upload_id')}), profile_id) where event_type = 'body'",
        ):
            conn.execute(statement)
        conn.execute("update account_deletion_work set phase = 'done' where phase = 'profiles' "
                     "and exists (select 1 from account_deletions d where "
                     "d.owner_id = account_deletion_work.owner_id and d.stage > 0)")
        return tables


class SQLitePersistenceRepository(AccountDeletionPersistence):
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._ensure_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def save_image_upload(
        self,
        *,
        payload: ImageUploadRequest,
        image_upload_id: str,
        image_reference: str,
        storage_provider: str = "local",
        object_key: str | None = None,
        upload_status: str = "ready",
        cleanup_after: str | None = None,
        soft_limit_exceeded: bool = False,
        upload_expires_at: str | None = None,
        owner_id: str | None = None,
        storage_namespace: str | None = None,
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            storage_namespace = self._original_upload_namespace(conn, image_upload_id, storage_namespace)
            cursor = conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at,
                    storage_provider, object_key, upload_status, cleanup_after, soft_limit_exceeded, upload_expires_at,
                    owner_id, storage_namespace
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(image_upload_id) do update set
                    image_reference = excluded.image_reference,
                    local_asset_id = excluded.local_asset_id,
                    file_name = excluded.file_name,
                    content_type = excluded.content_type,
                    byte_size = excluded.byte_size,
                    storage_provider = excluded.storage_provider,
                    object_key = excluded.object_key,
                    upload_status = excluded.upload_status,
                    cleanup_after = excluded.cleanup_after,
                    soft_limit_exceeded = excluded.soft_limit_exceeded,
                    upload_expires_at = excluded.upload_expires_at,
                    owner_id = coalesce(image_uploads.owner_id, excluded.owner_id)
                where image_uploads.storage_namespace = excluded.storage_namespace
                   or (image_uploads.storage_namespace is null and excluded.storage_namespace is null)
                """,
                (
                    image_upload_id,
                    image_reference,
                    payload.local_asset_id,
                    payload.file_name,
                    payload.content_type,
                    payload.byte_size,
                    created_at,
                    storage_provider,
                    object_key,
                    upload_status,
                    cleanup_after,
                    int(soft_limit_exceeded),
                    upload_expires_at,
                    owner_id,
                    storage_namespace,
                ),
            )
            if not cursor.rowcount:
                raise PersistenceError("image_upload_storage_namespace_immutable")
        return ImageUploadRecord(
            image_upload_id=image_upload_id,
            image_reference=image_reference,
            local_asset_id=payload.local_asset_id,
            file_name=payload.file_name,
            content_type=payload.content_type,
            byte_size=payload.byte_size,
            created_at=created_at,
            storage_provider=storage_provider,
            object_key=object_key,
            upload_status=upload_status,
            cleanup_after=cleanup_after,
            soft_limit_exceeded=soft_limit_exceeded,
            upload_expires_at=upload_expires_at,
            owner_id=owner_id,
            storage_namespace=storage_namespace,
        )

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None:
        with self._connection() as conn:
            row = conn.execute("select * from image_uploads where image_upload_id = ?", (image_upload_id,)).fetchone()
        return self._image_upload_from_row(row) if row else None

    def sum_image_upload_bytes(self) -> int:
        now = _now_iso()
        with self._connection() as conn:
            row = conn.execute(
                """
                select coalesce(sum(byte_size), 0) as total_bytes
                  from image_uploads
                 where upload_status in ('ready', 'deleting')
                    or (
                        upload_status = 'pending'
                        and (upload_expires_at is null or upload_expires_at >= ?)
                    )
                """,
                (now,),
            ).fetchone()
        return int(row["total_bytes"]) if row else 0

    def list_expired_image_uploads(self, now_iso: str, *, limit: int = 100) -> list[ImageUploadRecord]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid_retention_batch")
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from image_uploads
                 where upload_status in ('ready', 'deleting')
                   and cleanup_after is not null
                   and cleanup_after <= ?
                   and not exists (select 1 from account_deletions d where d.owner_id = image_uploads.owner_id)
                 order by cleanup_after, image_upload_id
                 limit ?
                """,
                (now_iso, limit),
            ).fetchall()
        return [self._image_upload_from_row(row) for row in rows]

    def mark_image_upload_deleting(self, image_upload_id: str) -> bool:
        return self._mark_retention_upload(image_upload_id, deleted=False)

    def mark_image_upload_deleted(self, image_upload_id: str) -> bool:
        return self._mark_retention_upload(image_upload_id, deleted=True)

    def check_ready(self) -> None:
        with self._connection() as conn:
            conn.execute("select 1").fetchone()

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
        owner_id: str | None = None,
    ) -> AnalysisJobRecord:
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into analysis_jobs (
                    analysis_job_id, image_upload_id, image_reference, meal_type, optional_note, status,
                    request_json, create_response_json, response_json, created_at, updated_at, owner_id
                ) values (?, ?, ?, ?, ?, ?, ?, ?, null, ?, ?, ?)
                on conflict(analysis_job_id) do update set
                    image_upload_id = excluded.image_upload_id,
                    image_reference = excluded.image_reference,
                    meal_type = excluded.meal_type,
                    optional_note = excluded.optional_note,
                    status = excluded.status,
                    request_json = excluded.request_json,
                    create_response_json = excluded.create_response_json,
                    response_json = null,
                    updated_at = excluded.updated_at,
                    owner_id = coalesce(analysis_jobs.owner_id, excluded.owner_id)
                """,
                (
                    create_response.analysis_job_id,
                    payload.image_upload_id,
                    image_reference,
                    payload.meal_type,
                    payload.optional_note,
                    create_response.status,
                    _dump_model(payload),
                    _dump_model(create_response),
                    now,
                    now,
                    owner_id,
                ),
            )
        record = self.get_analysis_job(create_response.analysis_job_id)
        if record is None:
            raise RuntimeError("analysis_job_persistence_failed")
        return record

    def save_analysis_job_response(self, response: AnalysisJobResponse) -> AnalysisJobRecord | None:
        with self._connection() as conn:
            row = conn.execute(
                "select analysis_job_id from analysis_jobs where analysis_job_id = ?",
                (response.id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                update analysis_jobs
                   set status = ?, response_json = ?, updated_at = ?
                 where analysis_job_id = ?
                """,
                (response.status, _dump_model(response), _now_iso(), response.id),
            )
        return self.get_analysis_job(response.id)

    def get_analysis_job(self, analysis_job_id: str) -> AnalysisJobRecord | None:
        with self._connection() as conn:
            row = conn.execute("select * from analysis_jobs where analysis_job_id = ?", (analysis_job_id,)).fetchone()
        return self._analysis_job_from_row(row) if row else None

    def list_analysis_jobs(self) -> list[AnalysisJobRecord]:
        with self._connection() as conn:
            rows = conn.execute("select * from analysis_jobs order by created_at, analysis_job_id").fetchall()
        return [self._analysis_job_from_row(row) for row in rows]

    def save_clarification(
        self,
        *,
        analysis_job_id: str,
        payload: ClarificationRequest,
        response: ClarificationResponse,
    ) -> ClarificationRecord:
        clarification_id = f"clarification-{uuid4()}"
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into clarifications (
                    clarification_id, analysis_job_id, request_json, response_json, created_at
                ) values (?, ?, ?, ?, ?)
                """,
                (clarification_id, analysis_job_id, _dump_model(payload), _dump_model(response), created_at),
            )
            conn.execute(
                """
                update analysis_jobs
                   set status = ?, response_json = ?, updated_at = ?
                 where analysis_job_id = ?
                """,
                (
                    response.status,
                    _dump_model(
                        AnalysisJobResponse(
                            id=analysis_job_id,
                            status=response.status,
                            result=response.result,
                        )
                    ),
                    created_at,
                    analysis_job_id,
                ),
            )
        return ClarificationRecord(
            clarification_id=clarification_id,
            analysis_job_id=analysis_job_id,
            request=payload,
            response=response,
            created_at=created_at,
        )

    def list_clarifications(self, analysis_job_id: str) -> list[ClarificationRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from clarifications
                 where analysis_job_id = ?
                 order by created_at, clarification_id
                """,
                (analysis_job_id,),
            ).fetchall()
        return [self._clarification_from_row(row) for row in rows]

    def save_meal_log(
        self,
        *,
        payload: MealLogRequest,
        response: SavedImpactResponse,
        meal_log_id: str | None = None,
    ) -> MealLogRecord:
        meal_log_id = meal_log_id or f"meal-log-{uuid4()}"
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into meal_logs (
                    meal_log_id, analysis_job_id, result_id, clarification_value,
                    request_json, response_json, created_at
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    meal_log_id,
                    payload.analysis_job_id,
                    payload.result_id,
                    payload.clarification_value,
                    _dump_model(payload),
                    _dump_model(response),
                    created_at,
                ),
            )
        return MealLogRecord(
            meal_log_id=meal_log_id,
            analysis_job_id=payload.analysis_job_id,
            result_id=payload.result_id,
            clarification_value=payload.clarification_value,
            request=payload,
            response=response,
            created_at=created_at,
        )

    def list_meal_logs(self, analysis_job_id: str | None = None) -> list[MealLogRecord]:
        with self._connection() as conn:
            if analysis_job_id is None:
                rows = conn.execute("select * from meal_logs order by created_at, meal_log_id").fetchall()
            else:
                rows = conn.execute(
                    """
                    select * from meal_logs
                     where analysis_job_id = ?
                     order by created_at, meal_log_id
                    """,
                    (analysis_job_id,),
                ).fetchall()
        return [self._meal_log_from_row(row) for row in rows]

    def get_meal_log(self, meal_log_id: str) -> MealLogRecord | None:
        with self._connection() as conn:
            row = conn.execute("select * from meal_logs where meal_log_id = ?", (meal_log_id,)).fetchone()
        return self._meal_log_from_row(row) if row else None

    def delete_meal_log(self, meal_log_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute("delete from meal_logs where meal_log_id = ?", (meal_log_id,))
        return cursor.rowcount > 0

    def delete_profile_artifacts(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]:
        uploads = self.list_profile_image_uploads(
            profile_id,
            owner_id=owner_id,
            additional_image_upload_ids=additional_image_upload_ids,
        )
        if owner_id is not None:
            return self._delete_owned_profile_artifacts(owner_id, profile_id, additional_image_upload_ids or [])
        profile_logs = [record for record in self.list_meal_logs() if record.request.profile_id == profile_id]
        profile_jobs = [
            record
            for record in self.list_analysis_jobs()
            if record.request.profile_id == profile_id or (owner_id is not None and record.owner_id == owner_id)
        ]
        job_ids = {record.analysis_job_id for record in profile_logs} | {record.analysis_job_id for record in profile_jobs}
        upload_ids = {record.image_upload_id for record in uploads}

        with self._connection() as conn:
            for job_id in job_ids:
                conn.execute("delete from clarifications where analysis_job_id = ?", (job_id,))
                conn.execute("delete from meal_logs where analysis_job_id = ?", (job_id,))
                conn.execute("delete from analysis_jobs where analysis_job_id = ?", (job_id,))
            for upload_id in upload_ids:
                conn.execute("delete from image_uploads where image_upload_id = ?", (upload_id,))
        return uploads

    def list_profile_image_uploads(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]:
        if owner_id is not None:
            return self._list_owned_profile_uploads(owner_id, profile_id, additional_image_upload_ids or [])
        profile_logs = [record for record in self.list_meal_logs() if record.request.profile_id == profile_id]
        upload_ids = set(additional_image_upload_ids or [])
        logged_job_ids = {record.analysis_job_id for record in profile_logs}
        for job in self.list_analysis_jobs():
            if job.analysis_job_id in logged_job_ids or job.request.profile_id == profile_id or (owner_id is not None and job.owner_id == owner_id):
                upload_ids.add(job.image_upload_id)
        if owner_id is not None:
            upload_ids.update(record.image_upload_id for record in self._list_image_uploads_by_owner(owner_id))
        return [record for upload_id in upload_ids if (record := self.get_image_upload(upload_id)) is not None]

    def _list_image_uploads_by_owner(self, owner_id: str) -> list[ImageUploadRecord]:
        with self._connection() as conn:
            rows = conn.execute("select * from image_uploads where owner_id = ?", (owner_id,)).fetchall()
        return [self._image_upload_from_row(row) for row in rows]

    def _ensure_schema(self) -> None:
        if str(self._db_path) != ":memory:":
            try:
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise PersistenceError("persistence_unavailable") from exc
        with self._connection() as conn:
            for statement in self._account_worker_schema():
                conn.execute(statement)
            conn.executescript(
                """
                create table if not exists account_deletions (
                    owner_id text primary key,
                    stage integer not null default 0 check (stage between 0 and 3),
                    started_at text not null,
                    updated_at text not null
                );

                create table if not exists image_uploads (
                    image_upload_id text primary key,
                    image_reference text not null,
                    local_asset_id text not null,
                    file_name text not null,
                    content_type text not null,
                    byte_size integer not null,
                    created_at text not null,
                    storage_provider text not null default 'local',
                    object_key text,
                    upload_status text not null default 'ready',
                    cleanup_after text,
                    soft_limit_exceeded integer not null default 0,
                    upload_expires_at text,
                    owner_id text
                );

                create table if not exists analysis_jobs (
                    analysis_job_id text primary key,
                    image_upload_id text not null,
                    image_reference text not null,
                    meal_type text not null,
                    optional_note text,
                    status text not null,
                    request_json text not null,
                    create_response_json text not null,
                    response_json text,
                    created_at text not null,
                    updated_at text not null,
                    owner_id text
                );

                create table if not exists clarifications (
                    clarification_id text primary key,
                    analysis_job_id text not null,
                    request_json text not null,
                    response_json text not null,
                    created_at text not null
                );

                create table if not exists meal_logs (
                    meal_log_id text primary key,
                    analysis_job_id text not null,
                    result_id text not null,
                    clarification_value text not null,
                    request_json text not null,
                    response_json text not null,
                    created_at text not null
                );
                """
            )
            self._ensure_sqlite_image_upload_columns(conn)
            self._ensure_sqlite_analysis_job_columns(conn)
            self._ensure_account_worker_columns(conn)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                yield conn
        except sqlite3.Error as exc:
            raise PersistenceError("persistence_unavailable") from exc

    @staticmethod
    def _image_upload_from_row(row: sqlite3.Row) -> ImageUploadRecord:
        return ImageUploadRecord(
            image_upload_id=row["image_upload_id"],
            image_reference=row["image_reference"],
            local_asset_id=row["local_asset_id"],
            file_name=row["file_name"],
            content_type=row["content_type"],
            byte_size=row["byte_size"],
            created_at=row["created_at"],
            storage_provider=row["storage_provider"],
            object_key=row["object_key"],
            upload_status=row["upload_status"],
            cleanup_after=row["cleanup_after"],
            soft_limit_exceeded=bool(row["soft_limit_exceeded"]),
            upload_expires_at=row["upload_expires_at"],
            owner_id=row["owner_id"],
            storage_namespace=row["storage_namespace"],
        )

    @staticmethod
    def _ensure_sqlite_image_upload_columns(conn: sqlite3.Connection) -> None:
        existing_columns = {row["name"] for row in conn.execute("pragma table_info(image_uploads)").fetchall()}
        column_statements = {
            "storage_provider": "alter table image_uploads add column storage_provider text not null default 'local'",
            "object_key": "alter table image_uploads add column object_key text",
            "upload_status": "alter table image_uploads add column upload_status text not null default 'ready'",
            "cleanup_after": "alter table image_uploads add column cleanup_after text",
            "soft_limit_exceeded": "alter table image_uploads add column soft_limit_exceeded integer not null default 0",
            "upload_expires_at": "alter table image_uploads add column upload_expires_at text",
            "owner_id": "alter table image_uploads add column owner_id text",
        }
        for column_name, statement in column_statements.items():
            if column_name not in existing_columns:
                conn.execute(statement)

    @staticmethod
    def _ensure_sqlite_analysis_job_columns(conn: sqlite3.Connection) -> None:
        existing_columns = {row["name"] for row in conn.execute("pragma table_info(analysis_jobs)").fetchall()}
        if "owner_id" not in existing_columns:
            conn.execute("alter table analysis_jobs add column owner_id text")

    @staticmethod
    def _analysis_job_from_row(row: sqlite3.Row) -> AnalysisJobRecord:
        response_json = row["response_json"]
        return AnalysisJobRecord(
            analysis_job_id=row["analysis_job_id"],
            image_upload_id=row["image_upload_id"],
            image_reference=row["image_reference"],
            meal_type=row["meal_type"],
            optional_note=row["optional_note"],
            status=row["status"],
            request=AnalysisJobRequest.model_validate(_load_json(row["request_json"])),
            create_response=AnalysisJobCreateResponse.model_validate(_load_json(row["create_response_json"])),
            response=AnalysisJobResponse.model_validate(_load_json(response_json)) if response_json else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            owner_id=row["owner_id"],
        )

    @staticmethod
    def _clarification_from_row(row: sqlite3.Row) -> ClarificationRecord:
        return ClarificationRecord(
            clarification_id=row["clarification_id"],
            analysis_job_id=row["analysis_job_id"],
            request=ClarificationRequest.model_validate(_load_json(row["request_json"])),
            response=ClarificationResponse.model_validate(_load_json(row["response_json"])),
            created_at=row["created_at"],
        )

    @staticmethod
    def _meal_log_from_row(row: sqlite3.Row) -> MealLogRecord:
        return MealLogRecord(
            meal_log_id=row["meal_log_id"],
            analysis_job_id=row["analysis_job_id"],
            result_id=row["result_id"],
            clarification_value=row["clarification_value"],
            request=MealLogRequest.model_validate(_load_json(row["request_json"])),
            response=SavedImpactResponse.model_validate(_load_json(row["response_json"])),
            created_at=row["created_at"],
        )


class PostgresPersistenceRepository(AccountDeletionPersistence):
    _account_postgres = True
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._ensure_schema()

    def save_image_upload(
        self,
        *,
        payload: ImageUploadRequest,
        image_upload_id: str,
        image_reference: str,
        storage_provider: str = "local",
        object_key: str | None = None,
        upload_status: str = "ready",
        cleanup_after: str | None = None,
        soft_limit_exceeded: bool = False,
        upload_expires_at: str | None = None,
        owner_id: str | None = None,
        storage_namespace: str | None = None,
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            storage_namespace = self._original_upload_namespace(conn, image_upload_id, storage_namespace)
            cursor = conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at,
                    storage_provider, object_key, upload_status, cleanup_after, soft_limit_exceeded, upload_expires_at,
                    owner_id, storage_namespace
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                on conflict(image_upload_id) do update set
                    image_reference = excluded.image_reference,
                    local_asset_id = excluded.local_asset_id,
                    file_name = excluded.file_name,
                    content_type = excluded.content_type,
                    byte_size = excluded.byte_size,
                    storage_provider = excluded.storage_provider,
                    object_key = excluded.object_key,
                    upload_status = excluded.upload_status,
                    cleanup_after = excluded.cleanup_after,
                    soft_limit_exceeded = excluded.soft_limit_exceeded,
                    upload_expires_at = excluded.upload_expires_at,
                    owner_id = coalesce(image_uploads.owner_id, excluded.owner_id)
                where image_uploads.storage_namespace = excluded.storage_namespace
                   or (image_uploads.storage_namespace is null and excluded.storage_namespace is null)
                """,
                (
                    image_upload_id,
                    image_reference,
                    payload.local_asset_id,
                    payload.file_name,
                    payload.content_type,
                    payload.byte_size,
                    created_at,
                    storage_provider,
                    object_key,
                    upload_status,
                    cleanup_after,
                    soft_limit_exceeded,
                    upload_expires_at,
                    owner_id,
                    storage_namespace,
                ),
            )
            if not cursor.rowcount:
                raise PersistenceError("image_upload_storage_namespace_immutable")
        return ImageUploadRecord(
            image_upload_id=image_upload_id,
            image_reference=image_reference,
            local_asset_id=payload.local_asset_id,
            file_name=payload.file_name,
            content_type=payload.content_type,
            byte_size=payload.byte_size,
            created_at=created_at,
            storage_provider=storage_provider,
            object_key=object_key,
            upload_status=upload_status,
            cleanup_after=cleanup_after,
            soft_limit_exceeded=soft_limit_exceeded,
            upload_expires_at=upload_expires_at,
            owner_id=owner_id,
            storage_namespace=storage_namespace,
        )

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None:
        with self._connection() as conn:
            row = conn.execute(
                "select * from image_uploads where image_upload_id = %s",
                (image_upload_id,),
            ).fetchone()
        return SQLitePersistenceRepository._image_upload_from_row(row) if row else None

    def sum_image_upload_bytes(self) -> int:
        now = _now_iso()
        with self._connection() as conn:
            row = conn.execute(
                """
                select coalesce(sum(byte_size), 0) as total_bytes
                  from image_uploads
                 where upload_status in ('ready', 'deleting')
                    or (
                        upload_status = 'pending'
                        and (upload_expires_at is null or upload_expires_at >= %s)
                    )
                """,
                (now,),
            ).fetchone()
        return int(row["total_bytes"]) if row else 0

    def list_expired_image_uploads(self, now_iso: str, *, limit: int = 100) -> list[ImageUploadRecord]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid_retention_batch")
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from image_uploads
                 where upload_status in ('ready', 'deleting')
                   and cleanup_after is not null
                   and cleanup_after <= %s
                   and not exists (select 1 from account_deletions d where d.owner_id = image_uploads.owner_id)
                 order by cleanup_after, image_upload_id
                 limit %s
                """,
                (now_iso, limit),
            ).fetchall()
        return [SQLitePersistenceRepository._image_upload_from_row(row) for row in rows]

    def mark_image_upload_deleting(self, image_upload_id: str) -> bool:
        return self._mark_retention_upload(image_upload_id, deleted=False)

    def mark_image_upload_deleted(self, image_upload_id: str) -> bool:
        return self._mark_retention_upload(image_upload_id, deleted=True)

    def check_ready(self) -> None:
        with self._connection() as conn:
            conn.execute("select 1").fetchone()

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
        owner_id: str | None = None,
    ) -> AnalysisJobRecord:
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into analysis_jobs (
                    analysis_job_id, image_upload_id, image_reference, meal_type, optional_note, status,
                    request_json, create_response_json, response_json, created_at, updated_at, owner_id
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, null, %s, %s, %s)
                on conflict(analysis_job_id) do update set
                    image_upload_id = excluded.image_upload_id,
                    image_reference = excluded.image_reference,
                    meal_type = excluded.meal_type,
                    optional_note = excluded.optional_note,
                    status = excluded.status,
                    request_json = excluded.request_json,
                    create_response_json = excluded.create_response_json,
                    response_json = null,
                    updated_at = excluded.updated_at,
                    owner_id = coalesce(analysis_jobs.owner_id, excluded.owner_id)
                """,
                (
                    create_response.analysis_job_id,
                    payload.image_upload_id,
                    image_reference,
                    payload.meal_type,
                    payload.optional_note,
                    create_response.status,
                    _dump_model(payload),
                    _dump_model(create_response),
                    now,
                    now,
                    owner_id,
                ),
            )
        record = self.get_analysis_job(create_response.analysis_job_id)
        if record is None:
            raise RuntimeError("analysis_job_persistence_failed")
        return record

    def save_analysis_job_response(self, response: AnalysisJobResponse) -> AnalysisJobRecord | None:
        with self._connection() as conn:
            row = conn.execute(
                "select analysis_job_id from analysis_jobs where analysis_job_id = %s",
                (response.id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                update analysis_jobs
                   set status = %s, response_json = %s, updated_at = %s
                 where analysis_job_id = %s
                """,
                (response.status, _dump_model(response), _now_iso(), response.id),
            )
        return self.get_analysis_job(response.id)

    def get_analysis_job(self, analysis_job_id: str) -> AnalysisJobRecord | None:
        with self._connection() as conn:
            row = conn.execute(
                "select * from analysis_jobs where analysis_job_id = %s",
                (analysis_job_id,),
            ).fetchone()
        return SQLitePersistenceRepository._analysis_job_from_row(row) if row else None

    def list_analysis_jobs(self) -> list[AnalysisJobRecord]:
        with self._connection() as conn:
            rows = conn.execute("select * from analysis_jobs order by created_at, analysis_job_id").fetchall()
        return [SQLitePersistenceRepository._analysis_job_from_row(row) for row in rows]

    def save_clarification(
        self,
        *,
        analysis_job_id: str,
        payload: ClarificationRequest,
        response: ClarificationResponse,
    ) -> ClarificationRecord:
        clarification_id = f"clarification-{uuid4()}"
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into clarifications (
                    clarification_id, analysis_job_id, request_json, response_json, created_at
                ) values (%s, %s, %s, %s, %s)
                """,
                (clarification_id, analysis_job_id, _dump_model(payload), _dump_model(response), created_at),
            )
            conn.execute(
                """
                update analysis_jobs
                   set status = %s, response_json = %s, updated_at = %s
                 where analysis_job_id = %s
                """,
                (
                    response.status,
                    _dump_model(
                        AnalysisJobResponse(
                            id=analysis_job_id,
                            status=response.status,
                            result=response.result,
                        )
                    ),
                    created_at,
                    analysis_job_id,
                ),
            )
        return ClarificationRecord(
            clarification_id=clarification_id,
            analysis_job_id=analysis_job_id,
            request=payload,
            response=response,
            created_at=created_at,
        )

    def list_clarifications(self, analysis_job_id: str) -> list[ClarificationRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from clarifications
                 where analysis_job_id = %s
                 order by created_at, clarification_id
                """,
                (analysis_job_id,),
            ).fetchall()
        return [SQLitePersistenceRepository._clarification_from_row(row) for row in rows]

    def save_meal_log(
        self,
        *,
        payload: MealLogRequest,
        response: SavedImpactResponse,
        meal_log_id: str | None = None,
    ) -> MealLogRecord:
        meal_log_id = meal_log_id or f"meal-log-{uuid4()}"
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into meal_logs (
                    meal_log_id, analysis_job_id, result_id, clarification_value,
                    request_json, response_json, created_at
                ) values (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    meal_log_id,
                    payload.analysis_job_id,
                    payload.result_id,
                    payload.clarification_value,
                    _dump_model(payload),
                    _dump_model(response),
                    created_at,
                ),
            )
        return MealLogRecord(
            meal_log_id=meal_log_id,
            analysis_job_id=payload.analysis_job_id,
            result_id=payload.result_id,
            clarification_value=payload.clarification_value,
            request=payload,
            response=response,
            created_at=created_at,
        )

    def list_meal_logs(self, analysis_job_id: str | None = None) -> list[MealLogRecord]:
        with self._connection() as conn:
            if analysis_job_id is None:
                rows = conn.execute("select * from meal_logs order by created_at, meal_log_id").fetchall()
            else:
                rows = conn.execute(
                    """
                    select * from meal_logs
                     where analysis_job_id = %s
                     order by created_at, meal_log_id
                    """,
                    (analysis_job_id,),
                ).fetchall()
        return [SQLitePersistenceRepository._meal_log_from_row(row) for row in rows]

    def get_meal_log(self, meal_log_id: str) -> MealLogRecord | None:
        with self._connection() as conn:
            row = conn.execute("select * from meal_logs where meal_log_id = %s", (meal_log_id,)).fetchone()
        return SQLitePersistenceRepository._meal_log_from_row(row) if row else None

    def delete_meal_log(self, meal_log_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute("delete from meal_logs where meal_log_id = %s", (meal_log_id,))
        return cursor.rowcount > 0

    def delete_profile_artifacts(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]:
        uploads = self.list_profile_image_uploads(
            profile_id,
            owner_id=owner_id,
            additional_image_upload_ids=additional_image_upload_ids,
        )
        if owner_id is not None:
            return self._delete_owned_profile_artifacts(owner_id, profile_id, additional_image_upload_ids or [])
        profile_logs = [record for record in self.list_meal_logs() if record.request.profile_id == profile_id]
        profile_jobs = [
            record
            for record in self.list_analysis_jobs()
            if record.request.profile_id == profile_id or (owner_id is not None and record.owner_id == owner_id)
        ]
        job_ids = {record.analysis_job_id for record in profile_logs} | {record.analysis_job_id for record in profile_jobs}
        upload_ids = {record.image_upload_id for record in uploads}

        with self._connection() as conn:
            for job_id in job_ids:
                conn.execute("delete from clarifications where analysis_job_id = %s", (job_id,))
                conn.execute("delete from meal_logs where analysis_job_id = %s", (job_id,))
                conn.execute("delete from analysis_jobs where analysis_job_id = %s", (job_id,))
            for upload_id in upload_ids:
                conn.execute("delete from image_uploads where image_upload_id = %s", (upload_id,))
        return uploads

    def list_profile_image_uploads(
        self,
        profile_id: str,
        *,
        owner_id: str | None = None,
        additional_image_upload_ids: list[str] | None = None,
    ) -> list[ImageUploadRecord]:
        if owner_id is not None:
            return self._list_owned_profile_uploads(owner_id, profile_id, additional_image_upload_ids or [])
        profile_logs = [record for record in self.list_meal_logs() if record.request.profile_id == profile_id]
        upload_ids = set(additional_image_upload_ids or [])
        logged_job_ids = {record.analysis_job_id for record in profile_logs}
        for job in self.list_analysis_jobs():
            if job.analysis_job_id in logged_job_ids or job.request.profile_id == profile_id or (owner_id is not None and job.owner_id == owner_id):
                upload_ids.add(job.image_upload_id)
        if owner_id is not None:
            upload_ids.update(record.image_upload_id for record in self._list_image_uploads_by_owner(owner_id))
        return [record for upload_id in upload_ids if (record := self.get_image_upload(upload_id)) is not None]

    def _list_image_uploads_by_owner(self, owner_id: str) -> list[ImageUploadRecord]:
        with self._connection() as conn:
            rows = conn.execute("select * from image_uploads where owner_id = %s", (owner_id,)).fetchall()
        return [SQLitePersistenceRepository._image_upload_from_row(row) for row in rows]

    def _ensure_schema(self) -> None:
        statements = (
            "create table if not exists account_deletions (owner_id text primary key, "
            "stage integer not null default 0 check (stage between 0 and 3), "
            "started_at text not null, updated_at text not null)",
            "revoke all on account_deletions from public",
            "do $$ begin "
            "if exists (select 1 from pg_roles where rolname = 'anon') then "
            "revoke all on account_deletions from anon; end if; "
            "if exists (select 1 from pg_roles where rolname = 'authenticated') then "
            "revoke all on account_deletions from authenticated; end if; end; $$",
            """
            create table if not exists image_uploads (
                image_upload_id text primary key,
                image_reference text not null,
                local_asset_id text not null,
                file_name text not null,
                content_type text not null,
                byte_size integer not null,
                created_at text not null,
                storage_provider text not null default 'local',
                object_key text,
                upload_status text not null default 'ready',
                cleanup_after text,
                soft_limit_exceeded boolean not null default false,
                upload_expires_at text,
                owner_id text
            )
            """,
            """
            create table if not exists analysis_jobs (
                analysis_job_id text primary key,
                image_upload_id text not null,
                image_reference text not null,
                meal_type text not null,
                optional_note text,
                status text not null,
                request_json text not null,
                create_response_json text not null,
                response_json text,
                created_at text not null,
                updated_at text not null,
                owner_id text
            )
            """,
            """
            create table if not exists clarifications (
                clarification_id text primary key,
                analysis_job_id text not null,
                request_json text not null,
                response_json text not null,
                created_at text not null
            )
            """,
            """
            create table if not exists meal_logs (
                meal_log_id text primary key,
                analysis_job_id text not null,
                result_id text not null,
                clarification_value text not null,
                request_json text not null,
                response_json text not null,
                created_at text not null
            )
            """,
        )
        with self._connection() as conn:
            for statement in self._account_worker_schema():
                conn.execute(statement)
            for table in ("account_deletion_work", "account_deletion_objects", "account_deletion_schema",
                          "account_owner_state", "account_deletion_refs", "account_deletion_mutations"):
                conn.execute(f"alter table {table} enable row level security")
                conn.execute(f"revoke all on {table} from public")
                conn.execute(
                    "do $$ begin "
                    "if exists (select 1 from pg_roles where rolname = 'anon') then "
                    f"revoke all on {table} from anon; end if; "
                    "if exists (select 1 from pg_roles where rolname = 'authenticated') then "
                    f"revoke all on {table} from authenticated; end if; end; $$"
                )
            for statement in statements:
                conn.execute(statement)
            for statement in self._postgres_image_upload_column_migrations():
                conn.execute(statement)
            self._ensure_account_worker_columns(conn)

    @staticmethod
    def _postgres_image_upload_column_migrations() -> tuple[str, ...]:
        return (
            "alter table image_uploads add column if not exists storage_provider text not null default 'local'",
            "alter table image_uploads add column if not exists object_key text",
            "alter table image_uploads add column if not exists upload_status text not null default 'ready'",
            "alter table image_uploads add column if not exists cleanup_after text",
            "alter table image_uploads add column if not exists soft_limit_exceeded boolean not null default false",
            "alter table image_uploads add column if not exists upload_expires_at text",
            "alter table image_uploads add column if not exists owner_id text",
            "alter table analysis_jobs add column if not exists owner_id text",
        )

    @contextmanager
    def _connection(self) -> Iterator[object]:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise PersistenceError("postgres_driver_unavailable") from exc

        try:
            with psycopg.connect(self._database_url, row_factory=dict_row) as conn:
                yield conn
        except psycopg.Error as exc:
            raise PersistenceError("persistence_unavailable") from exc


def _create_persistence_repository(env: Mapping[str, str]) -> PersistenceRepository:
    database_url = env.get("DATABASE_URL")
    if database_url:
        return _persistence_repository_for_location(database_url, True)
    db_path = env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)
    return _persistence_repository_for_location(db_path, False)


@lru_cache(maxsize=8)
def _persistence_repository_for_location(location: str, postgres: bool) -> PersistenceRepository:
    if postgres:
        return PostgresPersistenceRepository(location)
    return SQLitePersistenceRepository(location)


def get_persistence_repository(environ: dict[str, str] | None = None) -> PersistenceRepository:
    return _create_persistence_repository(os.environ if environ is None else environ)
