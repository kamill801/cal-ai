from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.admin_schemas import (
    AdminActivityItem,
    AdminAiOperations,
    AdminFunnelStage,
    AdminMetricSummary,
    AdminOverviewResponse,
    AdminPaymentOverview,
    AdminPaymentSummary,
    AdminUserDetailResponse,
    AdminUserSummary,
    AnalyticsEventRequest,
    AnalyticsHeartbeatRequest,
)
from app.services.auth import AuthenticatedUser
from app.services.persistence import DEFAULT_API_DATA_PATH, PersistenceError


REALTIME_WINDOW_MINUTES = 5
FUNNEL_WINDOW_DAYS = 30
DEFAULT_ANALYTICS_TIMEZONE = "Asia/Seoul"
FUNNEL_STAGES = (
    ("app_opened", "앱 열기"),
    ("onboarding_completed", "목표 설정 완료"),
    ("meal_photo_selected", "첫 음식 사진 선택"),
    ("analysis_completed", "첫 분석 완료"),
    ("meal_saved", "첫 식사 저장"),
    ("workout_plan_viewed", "운동 계획 확인"),
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def reporting_day_start(now: datetime, timezone_name: str | None = None) -> datetime:
    try:
        timezone = ZoneInfo(timezone_name or DEFAULT_ANALYTICS_TIMEZONE)
    except ZoneInfoNotFoundError:
        timezone = ZoneInfo(DEFAULT_ANALYTICS_TIMEZONE)
    return now.astimezone(timezone).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)


class AnalyticsOwnershipError(RuntimeError):
    pass


class AnalyticsProfileOwnershipError(RuntimeError):
    pass


class AnalyticsRepository:
    def __init__(self, location: str) -> None:
        self._location = location
        self._postgres = location.startswith(("postgres://", "postgresql://"))
        self._ensure_schema()

    def consume_admin_login_attempt(self) -> bool:
        window = int(now_utc().timestamp()) // 900
        with self._connection() as conn:
            row = conn.execute(
                self._sql(
                    "insert into admin_login_budget (id, window_id, attempts) values ('owner', ?, 1) "
                    "on conflict(id) do update set "
                    "attempts = case when admin_login_budget.window_id = excluded.window_id "
                    "then admin_login_budget.attempts + 1 else 1 end, window_id = excluded.window_id "
                    "where admin_login_budget.window_id != excluded.window_id or admin_login_budget.attempts < 10 "
                    "returning attempts"
                ), (window,),
            ).fetchone()
        return row is not None

    def record_event(
        self,
        payload: AnalyticsEventRequest,
        user: AuthenticatedUser | None,
    ) -> datetime:
        received_at = now_utc()
        occurred_at = payload.occurred_at or received_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        if abs((received_at - occurred_at.astimezone(UTC)).total_seconds()) > 86400:
            occurred_at = received_at
        with self._connection() as conn:
            self._upsert_user(conn, user, received_at)
            self._upsert_session(
                conn,
                session_id=payload.session_id,
                user=user,
                profile_id=payload.profile_id,
                screen=payload.screen,
                seen_at=received_at,
            )
            self._validate_profile_owner(conn, payload.profile_id, user)
            conn.execute(
                self._sql(
                    "insert into product_events (event_id, user_id, session_id, profile_id, event_name, screen, properties_json, occurred_at, received_at) "
                    "values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    str(uuid4()),
                    user.user_id if user else None,
                    payload.session_id,
                    payload.profile_id,
                    payload.event_name.value,
                    payload.screen,
                    json.dumps(payload.properties, ensure_ascii=True, sort_keys=True),
                    iso(occurred_at),
                    iso(received_at),
                ),
            )
        return received_at

    def heartbeat(
        self,
        payload: AnalyticsHeartbeatRequest,
        user: AuthenticatedUser | None,
    ) -> datetime:
        seen_at = now_utc()
        with self._connection() as conn:
            self._upsert_user(conn, user, seen_at)
            self._upsert_session(
                conn,
                session_id=payload.session_id,
                user=user,
                profile_id=payload.profile_id,
                screen=payload.screen,
                seen_at=seen_at,
            )
            self._validate_profile_owner(conn, payload.profile_id, user)
        return seen_at

    def overview(self) -> AdminOverviewResponse:
        now = now_utc()
        today_start = reporting_day_start(now, os.environ.get("ANALYTICS_TIMEZONE"))
        active_start = now - timedelta(hours=24)
        realtime_start = now - timedelta(minutes=REALTIME_WINDOW_MINUTES)
        with self._connection() as conn:
            metrics = AdminMetricSummary(
                total_users=self._count(conn, "select count(*) as value from app_users"),
                today_users=self._count(
                    conn,
                    "select count(distinct coalesce(user_id, session_id)) as value from app_sessions where last_seen_at >= ?",
                    (iso(today_start),),
                ),
                new_users_today=self._count(
                    conn,
                    "select count(*) as value from app_users where first_seen_at >= ?",
                    (iso(today_start),),
                ),
                realtime_users=self._count(
                    conn,
                    "select count(distinct coalesce(user_id, session_id)) as value from app_sessions where last_seen_at >= ?",
                    (iso(realtime_start),),
                ),
                active_users_24h=self._count(
                    conn,
                    "select count(distinct coalesce(user_id, session_id)) as value from app_sessions where last_seen_at >= ?",
                    (iso(active_start),),
                ),
                food_analyses_today=self._event_count(conn, "analysis_completed", today_start),
                analysis_failures_today=self._event_count(conn, "analysis_failed", today_start),
                meals_saved_today=self._event_count(conn, "meal_saved", today_start),
                workouts_completed_today=self._event_count(conn, "workout_completed", today_start),
            )
            users = self._users(conn, now=now, realtime_start=realtime_start)
            recent_activity = self._recent_activity(conn, limit=80)
            payments = self._payments(conn)
            funnel = self._funnel(conn, now - timedelta(days=FUNNEL_WINDOW_DAYS))
            started = self._event_count(conn, "analysis_started", today_start)
        completed = metrics.food_analyses_today
        failed = metrics.analysis_failures_today
        attempts = completed + failed
        return AdminOverviewResponse(
            generated_at=now,
            realtime_window_minutes=REALTIME_WINDOW_MINUTES,
            metrics=metrics,
            funnel=funnel,
            recent_activity=recent_activity,
            users=users,
            payments=payments,
            ai_operations=AdminAiOperations(
                started_today=max(started, attempts),
                completed_today=completed,
                failed_today=failed,
                success_rate=(completed / attempts) if attempts else 0,
            ),
        )

    def user_detail(self, user_id: str) -> AdminUserDetailResponse | None:
        now = now_utc()
        realtime_start = now - timedelta(minutes=REALTIME_WINDOW_MINUTES)
        with self._connection() as conn:
            users = self._users(
                conn,
                now=now,
                realtime_start=realtime_start,
                user_id=user_id,
            )
            if not users:
                return None
            activity = self._recent_activity(conn, limit=100, user_id=user_id)
            payments = self._payment_records(conn, limit=30, user_id=user_id)
        return AdminUserDetailResponse(
            user=users[0],
            recent_activity=activity,
            payments=payments,
        )

    def record_admin_audit(
        self,
        *,
        admin_user_id: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
    ) -> None:
        with self._connection() as conn:
            conn.execute(
                self._sql(
                    "insert into admin_audit_logs (audit_id, admin_user_id, action, resource_type, resource_id, occurred_at) "
                    "values (?, ?, ?, ?, ?, ?)"
                ),
                (
                    str(uuid4()),
                    admin_user_id,
                    action,
                    resource_type,
                    resource_id,
                    iso(now_utc()),
                ),
            )

    def billing_status(self, user_id: str | None) -> tuple[str, str]:
        if not user_id:
            return "beta", "active"
        with self._connection() as conn:
            row = conn.execute(
                self._sql(
                    "select plan, status from billing_subscriptions where user_id = ? order by updated_at desc limit 1"
                ),
                (user_id,),
            ).fetchone()
        if not row:
            return "beta", "active"
        return str(row["plan"]), str(row["status"])

    def check_ready(self) -> None:
        with self._connection() as conn:
            conn.execute("select 1").fetchone()

    def delete_profile_data(self, profile_id: str, *, owner_id: str | None) -> None:
        # Explicit foreign owners survive even if legacy rows reference this profile.
        session_filter = "user_id = ? or (user_id is null and profile_id = ?)"
        with self._connection() as conn:
            conn.execute(
                self._sql(
                    "delete from product_events where user_id = ? or (user_id is null and "
                    "(profile_id = ? or session_id in "
                    f"(select session_id from app_sessions where {session_filter})))"
                ),
                (owner_id, profile_id, owner_id, profile_id),
            )
            conn.execute(
                self._sql(f"delete from app_sessions where {session_filter}"),
                (owner_id, profile_id),
            )
            if owner_id is not None:
                conn.execute(self._sql("delete from app_users where user_id = ?"), (owner_id,))

    def _validate_profile_owner(
        self,
        conn: object,
        profile_id: str | None,
        user: AuthenticatedUser | None,
    ) -> None:
        if profile_id is None:
            return
        statement = "select payload_json from coach_profiles where profile_id = ?"
        # Keep the profile present through commit; SQLite's preceding write holds its lock.
        if self._postgres:
            statement += " for share"
        row = conn.execute(self._sql(statement), (profile_id,)).fetchone()
        if row is None or json.loads(row["payload_json"]).get("owner_id") != (
            user.user_id if user else None
        ):
            raise AnalyticsProfileOwnershipError("profile_not_found")

    def _upsert_user(
        self,
        conn: object,
        user: AuthenticatedUser | None,
        seen_at: datetime,
    ) -> None:
        if user is None:
            return
        conn.execute(
            self._sql(
                "insert into app_users (user_id, provider, email, display_name, first_seen_at, last_seen_at) "
                "values (?, ?, ?, ?, ?, ?) on conflict(user_id) do update set "
                "provider = coalesce(excluded.provider, app_users.provider), "
                "email = coalesce(excluded.email, app_users.email), "
                "display_name = coalesce(excluded.display_name, app_users.display_name), "
                "last_seen_at = excluded.last_seen_at"
            ),
            (
                user.user_id,
                user.provider,
                user.email,
                user.display_name,
                iso(seen_at),
                iso(seen_at),
            ),
        )

    def _upsert_session(
        self,
        conn: object,
        *,
        session_id: str,
        user: AuthenticatedUser | None,
        profile_id: str | None,
        screen: str,
        seen_at: datetime,
    ) -> None:
        row = conn.execute(
            self._sql(
                "insert into app_sessions (session_id, user_id, profile_id, started_at, last_seen_at, last_screen) "
                "values (?, ?, ?, ?, ?, ?) on conflict(session_id) do update set "
                "profile_id = coalesce(excluded.profile_id, app_sessions.profile_id), "
                "last_seen_at = excluded.last_seen_at, last_screen = excluded.last_screen "
                "where app_sessions.user_id = excluded.user_id "
                "or (app_sessions.user_id is null and excluded.user_id is null) "
                "returning session_id"
            ),
            (
                session_id,
                user.user_id if user else None,
                profile_id,
                iso(seen_at),
                iso(seen_at),
                screen,
            ),
        ).fetchone()
        if row is None:
            raise AnalyticsOwnershipError("analytics_session_conflict")

    def _users(
        self,
        conn: object,
        *,
        now: datetime,
        realtime_start: datetime,
        user_id: str | None = None,
    ) -> list[AdminUserSummary]:
        params: tuple[object, ...] = ()
        user_filter = ""
        if user_id:
            user_filter = "where user_id = ?"
            params = (user_id,)
        params += (100,)
        statement = f"""
            with selected_users as (
                select *
                from app_users
                {user_filter}
                order by last_seen_at desc
                limit ?
            ),
            event_counts as (
                select
                    e.user_id,
                    count(*) as event_count,
                    sum(case when e.event_name = 'analysis_completed' then 1 else 0 end) as analysis_count,
                    sum(case when e.event_name = 'meal_saved' then 1 else 0 end) as meal_save_count,
                    sum(case when e.event_name = 'workout_completed' then 1 else 0 end) as workout_count
                from product_events e
                inner join selected_users u on u.user_id = e.user_id
                group by e.user_id
            ),
            latest_sessions as (
                select user_id, last_screen
                from (
                    select
                        s.user_id,
                        s.last_screen,
                        row_number() over (
                            partition by s.user_id
                            order by s.last_seen_at desc, s.session_id desc
                        ) as row_number
                    from app_sessions s
                    inner join selected_users u on u.user_id = s.user_id
                ) ranked_sessions
                where row_number = 1
            ),
            latest_subscriptions as (
                select user_id, plan
                from (
                    select
                        b.user_id,
                        b.plan,
                        row_number() over (
                            partition by b.user_id
                            order by b.updated_at desc, b.subscription_id desc
                        ) as row_number
                    from billing_subscriptions b
                    inner join selected_users u on u.user_id = b.user_id
                ) ranked_subscriptions
                where row_number = 1
            )
            select
                u.user_id,
                u.provider,
                u.email,
                u.display_name,
                u.first_seen_at,
                u.last_seen_at,
                latest_sessions.last_screen,
                coalesce(event_counts.event_count, 0) as event_count,
                coalesce(event_counts.analysis_count, 0) as analysis_count,
                coalesce(event_counts.meal_save_count, 0) as meal_save_count,
                coalesce(event_counts.workout_count, 0) as workout_count,
                coalesce(latest_subscriptions.plan, 'free') as plan
            from selected_users u
            left join event_counts on event_counts.user_id = u.user_id
            left join latest_sessions on latest_sessions.user_id = u.user_id
            left join latest_subscriptions on latest_subscriptions.user_id = u.user_id
            order by u.last_seen_at desc
        """
        rows = conn.execute(self._sql(statement), params).fetchall()
        result: list[AdminUserSummary] = []
        for row in rows:
            current_user_id = str(row["user_id"])
            last_seen_at = datetime.fromisoformat(str(row["last_seen_at"]))
            result.append(
                AdminUserSummary(
                    user_id=current_user_id,
                    provider=row["provider"],
                    email=row["email"],
                    display_name=row["display_name"],
                    first_seen_at=datetime.fromisoformat(str(row["first_seen_at"])),
                    last_seen_at=last_seen_at,
                    last_screen=row["last_screen"],
                    online=last_seen_at >= realtime_start,
                    event_count=int(row["event_count"]),
                    analysis_count=int(row["analysis_count"]),
                    meal_save_count=int(row["meal_save_count"]),
                    workout_count=int(row["workout_count"]),
                    plan=str(row["plan"]),
                )
            )
        return result

    def _recent_activity(
        self,
        conn: object,
        *,
        limit: int,
        user_id: str | None = None,
    ) -> list[AdminActivityItem]:
        statement = (
            "select e.event_id, e.user_id, u.display_name, e.session_id, e.event_name, e.screen, e.occurred_at "
            "from product_events e left join app_users u on u.user_id = e.user_id"
        )
        params: tuple[object, ...] = ()
        if user_id:
            statement += " where e.user_id = ?"
            params = (user_id,)
        statement += " order by e.occurred_at desc limit ?"
        params += (limit,)
        rows = conn.execute(self._sql(statement), params).fetchall()
        return [
            AdminActivityItem(
                event_id=str(row["event_id"]),
                user_id=row["user_id"],
                display_name=row["display_name"],
                session_id=str(row["session_id"]),
                event_name=str(row["event_name"]),
                screen=str(row["screen"]),
                occurred_at=datetime.fromisoformat(str(row["occurred_at"])),
            )
            for row in rows
        ]

    def _funnel(self, conn: object, window_start: datetime) -> list[AdminFunnelStage]:
        rows = conn.execute(
            self._sql(
                "select coalesce(user_id, session_id) as identity, event_name, occurred_at "
                "from product_events where occurred_at >= ? order by identity, occurred_at"
            ),
            (iso(window_start),),
        ).fetchall()
        progress: dict[str, int] = {}
        for row in rows:
            identity = str(row["identity"])
            current = progress.get(identity, 0)
            if current < len(FUNNEL_STAGES) and row["event_name"] == FUNNEL_STAGES[current][0]:
                progress[identity] = current + 1
        counts = [sum(value > index for value in progress.values()) for index in range(len(FUNNEL_STAGES))]
        stages: list[AdminFunnelStage] = []
        for index, ((event_name, label), count) in enumerate(zip(FUNNEL_STAGES, counts, strict=True)):
            previous = counts[index - 1] if index else count
            conversion = 1.0 if index == 0 and count else (count / previous if previous else 0)
            stages.append(
                AdminFunnelStage(
                    event_name=event_name,
                    label=label,
                    users=count,
                    conversion_from_previous=conversion,
                    dropoff_from_previous=0 if index == 0 or previous == 0 else 1 - conversion,
                )
            )
        return stages

    def _payments(self, conn: object) -> AdminPaymentOverview:
        records = self._payment_records(conn, limit=30)
        provider_name = (os.environ.get("PAYMENT_PROVIDER") or "").strip() or None
        provider_configured = provider_name == "groble" and bool(
            (os.environ.get("GROBLE_PRODUCT_ID") or "").strip()
            and (os.environ.get("GROBLE_WEBHOOK_SECRET") or "").strip()
        )
        return AdminPaymentOverview(
            provider_configured=provider_configured,
            provider_name=provider_name,
            gross_revenue_krw=self._count(
                conn,
                "select coalesce(sum(amount), 0) as value from billing_payments where status = 'paid' and currency = 'KRW'",
            ),
            active_subscriptions=self._count(
                conn,
                "select count(*) as value from billing_subscriptions where status in ('active', 'trialing')",
            ),
            paid_count=self._count(conn, "select count(*) as value from billing_payments where status = 'paid'"),
            pending_count=self._count(conn, "select count(*) as value from billing_payments where status = 'pending'"),
            failed_count=self._count(conn, "select count(*) as value from billing_payments where status = 'failed'"),
            refunded_count=self._count(conn, "select count(*) as value from billing_payments where status = 'refunded'"),
            recent_payments=records,
        )

    def _payment_records(
        self,
        conn: object,
        *,
        limit: int,
        user_id: str | None = None,
    ) -> list[AdminPaymentSummary]:
        statement = "select * from billing_payments"
        params: tuple[object, ...] = ()
        if user_id:
            statement += " where user_id = ?"
            params = (user_id,)
        statement += " order by created_at desc limit ?"
        params += (limit,)
        rows = conn.execute(self._sql(statement), params).fetchall()
        return [
            AdminPaymentSummary(
                payment_id=str(row["payment_id"]),
                user_id=row["user_id"],
                provider=str(row["provider"]),
                product_id=str(row["product_id"]),
                amount=int(row["amount"]),
                currency=str(row["currency"]),
                status=str(row["status"]),
                created_at=datetime.fromisoformat(str(row["created_at"])),
                updated_at=datetime.fromisoformat(str(row["updated_at"])),
            )
            for row in rows
        ]

    def _event_count(self, conn: object, event_name: str, start: datetime) -> int:
        return self._count(
            conn,
            "select count(*) as value from product_events where event_name = ? and occurred_at >= ?",
            (event_name, iso(start)),
        )

    def _count(
        self,
        conn: object,
        statement: str,
        params: tuple[object, ...] = (),
    ) -> int:
        row = conn.execute(self._sql(statement), params).fetchone()
        return int(row["value"] if row else 0)

    def _ensure_schema(self) -> None:
        statements = (
            "create table if not exists admin_login_budget (id text primary key, window_id bigint not null, attempts integer not null)",
            "create table if not exists app_users (user_id text primary key, provider text, email text, display_name text, first_seen_at text not null, last_seen_at text not null)",
            "create table if not exists app_sessions (session_id text primary key, user_id text, profile_id text, started_at text not null, last_seen_at text not null, last_screen text not null)",
            "create index if not exists app_sessions_last_seen_idx on app_sessions(last_seen_at)",
            "create index if not exists app_sessions_user_idx on app_sessions(user_id, last_seen_at)",
            "create table if not exists product_events (event_id text primary key, user_id text, session_id text not null, profile_id text, event_name text not null, screen text not null, properties_json text not null, occurred_at text not null, received_at text not null)",
            "create index if not exists product_events_name_time_idx on product_events(event_name, occurred_at)",
            "create index if not exists product_events_user_time_idx on product_events(user_id, occurred_at)",
            "create index if not exists product_events_session_time_idx on product_events(session_id, occurred_at)",
            "create table if not exists billing_subscriptions (subscription_id text primary key, user_id text not null, provider text not null, plan text not null, status text not null, current_period_end text, created_at text not null, updated_at text not null)",
            "create index if not exists billing_subscriptions_user_idx on billing_subscriptions(user_id, updated_at)",
            "create table if not exists billing_payments (payment_id text primary key, user_id text, provider text not null, product_id text not null, amount integer not null, currency text not null, status text not null, created_at text not null, updated_at text not null)",
            "create index if not exists billing_payments_user_idx on billing_payments(user_id, created_at)",
            "create table if not exists admin_audit_logs (audit_id text primary key, admin_user_id text not null, action text not null, resource_type text not null, resource_id text, occurred_at text not null)",
            "create index if not exists admin_audit_time_idx on admin_audit_logs(occurred_at)",
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
                raise PersistenceError("analytics_persistence_unavailable") from exc
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise PersistenceError("analytics_persistence_unavailable") from exc
        try:
            with psycopg.connect(self._location, row_factory=dict_row) as conn:
                yield conn
        except psycopg.Error as exc:
            raise PersistenceError("analytics_persistence_unavailable") from exc

    def _sql(self, statement: str) -> str:
        return statement.replace("?", "%s") if self._postgres else statement


def _repository_location(env: Mapping[str, str]) -> str:
    return env.get("DATABASE_URL") or env.get("CAL_AI_API_DATA_PATH") or str(DEFAULT_API_DATA_PATH)


@lru_cache(maxsize=8)
def _repository_for_location(location: str) -> AnalyticsRepository:
    return AnalyticsRepository(location)


def get_analytics_repository(
    environ: Mapping[str, str] | None = None,
) -> AnalyticsRepository:
    env = os.environ if environ is None else environ
    return _repository_for_location(_repository_location(env))
