from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
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


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


class CoachRepository(Protocol):
    def save_profile(self, profile: CoachProfile) -> CoachProfile: ...

    def get_profile(self, profile_id: str) -> CoachProfile | None: ...

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


def get_coach_repository(environ: dict[str, str] | None = None) -> CoachRepository:
    env = environ if environ is not None else os.environ
    location = env.get("DATABASE_URL") or env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)
    return SqlCoachRepository(location)
