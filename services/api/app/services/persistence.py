from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
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
    ) -> ImageUploadRecord: ...

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None: ...

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
    ) -> AnalysisJobRecord: ...

    def save_analysis_job_response(self, response: AnalysisJobResponse) -> AnalysisJobRecord | None: ...

    def get_analysis_job(self, analysis_job_id: str) -> AnalysisJobRecord | None: ...

    def save_clarification(
        self,
        *,
        analysis_job_id: str,
        payload: ClarificationRequest,
        response: ClarificationResponse,
    ) -> ClarificationRecord: ...

    def list_clarifications(self, analysis_job_id: str) -> list[ClarificationRecord]: ...

    def save_meal_log(self, *, payload: MealLogRequest, response: SavedImpactResponse) -> MealLogRecord: ...

    def list_meal_logs(self, analysis_job_id: str | None = None) -> list[MealLogRecord]: ...


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
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at
                ) values (?, ?, ?, ?, ?, ?, ?)
                on conflict(image_upload_id) do update set
                    image_reference = excluded.image_reference,
                    local_asset_id = excluded.local_asset_id,
                    file_name = excluded.file_name,
                    content_type = excluded.content_type,
                    byte_size = excluded.byte_size
                """,
                (
                    image_upload_id,
                    image_reference,
                    payload.local_asset_id,
                    payload.file_name,
                    payload.content_type,
                    payload.byte_size,
                    created_at,
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
        )

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None:
        with self._connection() as conn:
            row = conn.execute("select * from image_uploads where image_upload_id = ?", (image_upload_id,)).fetchone()
        return self._image_upload_from_row(row) if row else None

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
    ) -> AnalysisJobRecord:
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into analysis_jobs (
                    analysis_job_id, image_upload_id, image_reference, meal_type, optional_note, status,
                    request_json, create_response_json, response_json, created_at, updated_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, null, ?, ?)
                on conflict(analysis_job_id) do update set
                    image_upload_id = excluded.image_upload_id,
                    image_reference = excluded.image_reference,
                    meal_type = excluded.meal_type,
                    optional_note = excluded.optional_note,
                    status = excluded.status,
                    request_json = excluded.request_json,
                    create_response_json = excluded.create_response_json,
                    response_json = null,
                    updated_at = excluded.updated_at
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

    def save_meal_log(self, *, payload: MealLogRequest, response: SavedImpactResponse) -> MealLogRecord:
        meal_log_id = f"meal-log-{uuid4()}"
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
                    created_at text not null
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
                    updated_at text not null
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
        )

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
    ) -> ImageUploadRecord:
        created_at = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into image_uploads (
                    image_upload_id, image_reference, local_asset_id, file_name, content_type, byte_size, created_at
                ) values (%s, %s, %s, %s, %s, %s, %s)
                on conflict(image_upload_id) do update set
                    image_reference = excluded.image_reference,
                    local_asset_id = excluded.local_asset_id,
                    file_name = excluded.file_name,
                    content_type = excluded.content_type,
                    byte_size = excluded.byte_size
                """,
                (
                    image_upload_id,
                    image_reference,
                    payload.local_asset_id,
                    payload.file_name,
                    payload.content_type,
                    payload.byte_size,
                    created_at,
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
        )

    def get_image_upload(self, image_upload_id: str) -> ImageUploadRecord | None:
        with self._connection() as conn:
            row = conn.execute(
                "select * from image_uploads where image_upload_id = %s",
                (image_upload_id,),
            ).fetchone()
        return SQLitePersistenceRepository._image_upload_from_row(row) if row else None

    def save_analysis_job(
        self,
        *,
        payload: AnalysisJobRequest,
        image_reference: str,
        create_response: AnalysisJobCreateResponse,
    ) -> AnalysisJobRecord:
        now = _now_iso()
        with self._connection() as conn:
            conn.execute(
                """
                insert into analysis_jobs (
                    analysis_job_id, image_upload_id, image_reference, meal_type, optional_note, status,
                    request_json, create_response_json, response_json, created_at, updated_at
                ) values (%s, %s, %s, %s, %s, %s, %s, %s, null, %s, %s)
                on conflict(analysis_job_id) do update set
                    image_upload_id = excluded.image_upload_id,
                    image_reference = excluded.image_reference,
                    meal_type = excluded.meal_type,
                    optional_note = excluded.optional_note,
                    status = excluded.status,
                    request_json = excluded.request_json,
                    create_response_json = excluded.create_response_json,
                    response_json = null,
                    updated_at = excluded.updated_at
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

    def save_meal_log(self, *, payload: MealLogRequest, response: SavedImpactResponse) -> MealLogRecord:
        meal_log_id = f"meal-log-{uuid4()}"
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
                created_at text not null
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
                updated_at text not null
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


def get_persistence_repository(environ: dict[str, str] | None = None) -> PersistenceRepository:
    env = environ if environ is not None else os.environ
    database_url = env.get("DATABASE_URL")
    if database_url:
        return PostgresPersistenceRepository(database_url)
    db_path = env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)
    return SQLitePersistenceRepository(db_path)
