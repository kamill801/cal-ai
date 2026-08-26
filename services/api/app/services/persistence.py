from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
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
    ) -> ImageUploadRecord: ...

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None: ...

    def sum_image_upload_bytes(self) -> int: ...

    def check_ready(self) -> None: ...

    def list_expired_image_uploads(self, now_iso: str) -> list[ImageUploadRecord]: ...

    def mark_image_upload_deleting(self, image_upload_id: str) -> None: ...

    def mark_image_upload_deleted(self, image_upload_id: str) -> None: ...

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


class SQLitePersistenceRepository:
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
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at,
                    storage_provider, object_key, upload_status, cleanup_after, soft_limit_exceeded, upload_expires_at,
                    owner_id
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
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

    def list_expired_image_uploads(self, now_iso: str) -> list[ImageUploadRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from image_uploads
                 where upload_status in ('ready', 'deleting')
                   and cleanup_after is not null
                   and cleanup_after <= ?
                 order by cleanup_after, image_upload_id
                """,
                (now_iso,),
            ).fetchall()
        return [self._image_upload_from_row(row) for row in rows]

    def mark_image_upload_deleting(self, image_upload_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "update image_uploads set upload_status = 'deleting' where image_upload_id = ? and upload_status != 'deleted'",
                (image_upload_id,),
            )

    def mark_image_upload_deleted(self, image_upload_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                update image_uploads
                   set image_reference = ?, object_key = null, upload_status = 'deleted'
                 where image_upload_id = ?
                """,
                (f"deleted://{image_upload_id}", image_upload_id),
            )

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
            conn.executescript(
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


class PostgresPersistenceRepository:
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
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at,
                    storage_provider, object_key, upload_status, cleanup_after, soft_limit_exceeded, upload_expires_at,
                    owner_id
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                ),
            )
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

    def list_expired_image_uploads(self, now_iso: str) -> list[ImageUploadRecord]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                select * from image_uploads
                 where upload_status in ('ready', 'deleting')
                   and cleanup_after is not null
                   and cleanup_after <= %s
                 order by cleanup_after, image_upload_id
                """,
                (now_iso,),
            ).fetchall()
        return [SQLitePersistenceRepository._image_upload_from_row(row) for row in rows]

    def mark_image_upload_deleting(self, image_upload_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "update image_uploads set upload_status = 'deleting' where image_upload_id = %s and upload_status != 'deleted'",
                (image_upload_id,),
            )

    def mark_image_upload_deleted(self, image_upload_id: str) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                update image_uploads
                   set image_reference = %s, object_key = null, upload_status = 'deleted'
                 where image_upload_id = %s
                """,
                (f"deleted://{image_upload_id}", image_upload_id),
            )

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
            for statement in statements:
                conn.execute(statement)
            for statement in self._postgres_image_upload_column_migrations():
                conn.execute(statement)

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
