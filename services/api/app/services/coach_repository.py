from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import BaseModel

from app.coach_schemas import (
    BodyCheckInResponse,
    CoachProfile,
    WeightLogResponse,
    WellnessCheckInResponse,
    WorkoutPlanResponse,
    WorkoutSessionResponse,
)
from app.services.persistence import DEFAULT_API_DATA_PATH, PersistenceError


ModelT = TypeVar("ModelT", bound=BaseModel)


class EquipmentUsageLimitError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


class CoachRepository(Protocol):
    def save_profile(self, profile: CoachProfile) -> CoachProfile: ...

    def get_profile(self, profile_id: str) -> CoachProfile | None: ...

    def list_profiles_for_owner(self, owner_id: str) -> list[CoachProfile]: ...

    def save_weight_log(self, value: WeightLogResponse) -> WeightLogResponse: ...

    def list_weight_logs(self, profile_id: str) -> list[WeightLogResponse]: ...

    def save_wellness(self, value: WellnessCheckInResponse) -> WellnessCheckInResponse: ...

    def list_wellness(self, profile_id: str) -> list[WellnessCheckInResponse]: ...

    def save_body_check_in(self, value: BodyCheckInResponse) -> BodyCheckInResponse: ...

    def list_body_check_ins(self, profile_id: str) -> list[BodyCheckInResponse]: ...

    def save_workout_plan(self, value: WorkoutPlanResponse) -> WorkoutPlanResponse: ...

    def get_workout_plan(self, profile_id: str) -> WorkoutPlanResponse | None: ...

    def save_workout_session(self, value: WorkoutSessionResponse) -> WorkoutSessionResponse: ...

    def list_workout_sessions(self, profile_id: str) -> list[WorkoutSessionResponse]: ...

    def delete_profile(self, profile_id: str) -> bool: ...

    def get_equipment_receipt(self, profile_id: str, upload_id: str) -> dict | None: ...

    def reserve_equipment_analysis(self, profile_id: str, owner_id: str, upload_id: str, owner_limit: int, global_limit: int) -> str: ...

    def finish_equipment_analysis(self, profile_id: str, upload_id: str, result: dict | None) -> None: ...

    def prune_equipment_receipts(self) -> None: ...


class SqlCoachRepository:
    def __init__(self, location: str) -> None:
        self._location = location
        self._postgres = location.startswith(("postgres://", "postgresql://"))
        self._ensure_schema()

    def save_profile(self, profile: CoachProfile) -> CoachProfile:
        with self._connection() as conn:
            conn.execute(
                self._sql(
                    "insert into coach_profiles (profile_id, payload_json, created_at, updated_at) values (?, ?, ?, ?) "
                    "on conflict(profile_id) do update set payload_json = excluded.payload_json, updated_at = excluded.updated_at"
                ),
                (profile.profile_id, self._dump(profile), profile.created_at, now_iso()),
            )
        return profile

    def get_profile(self, profile_id: str) -> CoachProfile | None:
        with self._connection() as conn:
            row = conn.execute(self._sql("select payload_json from coach_profiles where profile_id = ?"), (profile_id,)).fetchone()
        return CoachProfile.model_validate_json(row["payload_json"]) if row else None

    def list_profiles_for_owner(self, owner_id: str) -> list[CoachProfile]:
        owner_filter = (
            "payload_json::jsonb ->> 'owner_id' = ?"
            if self._postgres
            else "json_extract(payload_json, '$.owner_id') = ?"
        )
        with self._connection() as conn:
            rows = conn.execute(
                self._sql(f"select payload_json from coach_profiles where {owner_filter} order by created_at, profile_id"),
                (owner_id,),
            ).fetchall()
        return [CoachProfile.model_validate_json(row["payload_json"]) for row in rows]

    def save_weight_log(self, value: WeightLogResponse) -> WeightLogResponse:
        return self._save_event("weight", value)

    def list_weight_logs(self, profile_id: str) -> list[WeightLogResponse]:
        return self._list_events(profile_id, "weight", WeightLogResponse)

    def save_wellness(self, value: WellnessCheckInResponse) -> WellnessCheckInResponse:
        return self._save_event("wellness", value)

    def list_wellness(self, profile_id: str) -> list[WellnessCheckInResponse]:
        return self._list_events(profile_id, "wellness", WellnessCheckInResponse)

    def save_body_check_in(self, value: BodyCheckInResponse) -> BodyCheckInResponse:
        return self._save_event("body", value)

    def list_body_check_ins(self, profile_id: str) -> list[BodyCheckInResponse]:
        return self._list_events(profile_id, "body", BodyCheckInResponse)

    def save_workout_plan(self, value: WorkoutPlanResponse) -> WorkoutPlanResponse:
        with self._connection() as conn:
            conn.execute(
                self._sql(
                    "insert into workout_plans (plan_id, profile_id, payload_json, created_at) values (?, ?, ?, ?) "
                    "on conflict(profile_id) do update set plan_id = excluded.plan_id, payload_json = excluded.payload_json, created_at = excluded.created_at"
                ),
                (value.id, value.profile_id, self._dump(value), value.generated_at),
            )
        return value

    def get_workout_plan(self, profile_id: str) -> WorkoutPlanResponse | None:
        with self._connection() as conn:
            row = conn.execute(self._sql("select payload_json from workout_plans where profile_id = ?"), (profile_id,)).fetchone()
        return WorkoutPlanResponse.model_validate_json(row["payload_json"]) if row else None

    def save_workout_session(self, value: WorkoutSessionResponse) -> WorkoutSessionResponse:
        return self._save_event("workout", value)

    def list_workout_sessions(self, profile_id: str) -> list[WorkoutSessionResponse]:
        return self._list_events(profile_id, "workout", WorkoutSessionResponse)

    def delete_profile(self, profile_id: str) -> bool:
        with self._connection() as conn:
            existing = conn.execute(
                self._sql("select profile_id from coach_profiles where profile_id = ?"),
                (profile_id,),
            ).fetchone()
            if existing is None:
                return False
            conn.execute(self._sql("delete from coach_events where profile_id = ?"), (profile_id,))
            conn.execute(self._sql("delete from workout_plans where profile_id = ?"), (profile_id,))
            conn.execute(self._sql("delete from coach_profiles where profile_id = ?"), (profile_id,))
        return True

    def get_equipment_receipt(self, profile_id: str, upload_id: str) -> dict | None:
        with self._connection() as conn:
            row = conn.execute(self._sql("select payload_json from coach_events where event_id = ? and profile_id = ? and event_type = 'equipment'"), (f"equipment-{upload_id}", profile_id)).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def reserve_equipment_analysis(self, profile_id: str, owner_id: str, upload_id: str, owner_limit: int, global_limit: int) -> str:
        now = datetime.now(UTC)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(timespec="microseconds")
        active_since = (now - timedelta(minutes=2)).isoformat(timespec="microseconds")
        event_id = f"equipment-{upload_id}"
        owner_key = hashlib.sha256(owner_id.encode()).hexdigest()
        with self._connection() as conn:
            # Serialize budgets across all instances, not just one worker process.
            if self._postgres:
                conn.execute("select pg_advisory_xact_lock(196384237)")
            else:
                conn.execute("begin immediate")
            existing = conn.execute(self._sql("select profile_id, payload_json from coach_events where event_id = ?"), (event_id,)).fetchone()
            if existing:
                if existing["profile_id"] != profile_id:
                    raise PersistenceError("equipment_receipt_owner_mismatch")
                return json.loads(existing["payload_json"])["status"]
            existing_usage = conn.execute(self._sql("select status from equipment_usage where upload_id = ?"), (upload_id,)).fetchone()
            if existing_usage:
                return existing_usage["status"]
            # Minimal spend accounting survives profile deletion until its short retention expires.
            rows = conn.execute(self._sql("select owner_key, status, created_at from equipment_usage where created_at >= ?"), (min(day_start, active_since),)).fetchall()
            daily = [row for row in rows if row["created_at"] >= day_start]
            owner_values = [row for row in daily if row["owner_key"] == owner_key]
            if len(daily) >= global_limit or len(owner_values) >= owner_limit:
                raise EquipmentUsageLimitError("equipment_daily_limit")
            active = [row for row in rows if row["status"] == "running" and row["created_at"] >= active_since]
            if len(active) >= 3 or any(row["owner_key"] == owner_key for row in active):
                raise EquipmentUsageLimitError("equipment_scan_in_progress")
            created_at = now.isoformat(timespec="microseconds")
            payload = {"owner_id": owner_id, "status": "running", "result": None}
            conn.execute(self._sql("insert into coach_events (event_id, profile_id, event_type, payload_json, created_at) values (?, ?, 'equipment', ?, ?)"), (event_id, profile_id, json.dumps(payload), created_at))
            conn.execute(self._sql("insert into equipment_usage (upload_id, owner_key, status, created_at) values (?, ?, 'running', ?)"), (upload_id, owner_key, created_at))
        return "reserved"

    def finish_equipment_analysis(self, profile_id: str, upload_id: str, result: dict | None) -> None:
        with self._connection() as conn:
            event_id = f"equipment-{upload_id}"
            row = conn.execute(self._sql("select payload_json from coach_events where event_id = ? and profile_id = ? and event_type = 'equipment'"), (event_id, profile_id)).fetchone()
            if row is None:
                raise PersistenceError("equipment_receipt_missing")
            payload = json.loads(row["payload_json"])
            if payload["status"] != "running":
                return
            payload.update(status="complete" if result is not None else "failed", result=result)
            cursor = conn.execute(self._sql("update coach_events set payload_json = ? where event_id = ? and profile_id = ? and payload_json = ?"), (json.dumps(payload, ensure_ascii=False), event_id, profile_id, row["payload_json"]))
            if cursor.rowcount:
                conn.execute(self._sql("update equipment_usage set status = ? where upload_id = ? and status = 'running'"), (payload["status"], upload_id))

    def prune_equipment_receipts(self) -> None:
        cutoff = (datetime.now(UTC) - timedelta(days=2)).isoformat(timespec="microseconds")
        with self._connection() as conn:
            conn.execute(self._sql("delete from coach_events where event_type = 'equipment' and created_at < ?"), (cutoff,))
            conn.execute(self._sql("delete from equipment_usage where created_at < ?"), (cutoff,))

    def _save_event(self, event_type: str, value: ModelT) -> ModelT:
        event_id = str(getattr(value, "id"))
        profile_id = str(getattr(value, "profile_id"))
        created_at = str(getattr(value, "created_at"))
        with self._connection() as conn:
            conn.execute(
                self._sql("insert into coach_events (event_id, profile_id, event_type, payload_json, created_at) values (?, ?, ?, ?, ?)"),
                (event_id, profile_id, event_type, self._dump(value), created_at),
            )
        return value

    def _list_events(self, profile_id: str, event_type: str, model: type[ModelT]) -> list[ModelT]:
        with self._connection() as conn:
            rows = conn.execute(
                self._sql("select payload_json from coach_events where profile_id = ? and event_type = ? order by created_at, event_id"),
                (profile_id, event_type),
            ).fetchall()
        return [model.model_validate_json(row["payload_json"]) for row in rows]

    def _ensure_schema(self) -> None:
        statements = (
            "create table if not exists coach_profiles (profile_id text primary key, payload_json text not null, created_at text not null, updated_at text not null)",
            "create table if not exists coach_events (event_id text primary key, profile_id text not null, event_type text not null, payload_json text not null, created_at text not null)",
            "create index if not exists coach_events_profile_type_idx on coach_events(profile_id, event_type, created_at)",
            "create table if not exists equipment_usage (upload_id text primary key, owner_key text not null, status text not null, created_at text not null)",
            "create index if not exists equipment_usage_created_idx on equipment_usage(created_at)",
            "create table if not exists workout_plans (plan_id text not null, profile_id text primary key, payload_json text not null, created_at text not null)",
        )
        if not self._postgres and self._location != ":memory:":
            Path(self._location).parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            for statement in statements:
                conn.execute(statement)

    @contextmanager
    def _connection(self) -> Iterator[object]:
        if not self._postgres:
            try:
                with sqlite3.connect(self._location) as conn:
                    conn.row_factory = sqlite3.Row
                    yield conn
                return
            except sqlite3.Error as exc:
                raise PersistenceError("persistence_unavailable") from exc
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise PersistenceError("persistence_unavailable") from exc
        try:
            with psycopg.connect(self._location, row_factory=dict_row) as conn:
                yield conn
        except psycopg.Error as exc:
            raise PersistenceError("persistence_unavailable") from exc

    def _sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self._postgres else statement

    @staticmethod
    def _dump(value: BaseModel) -> str:
        return json.dumps(value.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)


def _coach_repository_location(env: Mapping[str, str]) -> str:
    return env.get("DATABASE_URL") or env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)


@lru_cache(maxsize=8)
def _coach_repository_for_location(location: str) -> CoachRepository:
    return SqlCoachRepository(location)


def _create_coach_repository(env: Mapping[str, str]) -> CoachRepository:
    return _coach_repository_for_location(_coach_repository_location(env))


def get_coach_repository(environ: dict[str, str] | None = None) -> CoachRepository:
    return _create_coach_repository(os.environ if environ is None else environ)
