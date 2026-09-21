from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app import admin_routes, main
from app.admin_schemas import AnalyticsEventRequest
from app.services.auth import AuthenticatedUser
from app.services.analytics_repository import get_analytics_repository, iso, now_utc, reporting_day_start


client = TestClient(main.app)


def event_payload(event_name: str, *, session_id: str = "session_12345678") -> dict[str, object]:
    return {
        "event_name": event_name,
        "session_id": session_id,
        "screen": "today",
        "profile_id": None,
        "properties": {},
    }


def test_default_cors_origins_include_admin_dev_and_preview() -> None:
    origins = main.get_cors_allowed_origins({})
    assert "http://localhost:3016" in origins
    assert "http://localhost:3017" in origins


def test_admin_origin_extends_existing_cors_allowlist() -> None:
    origins = main.get_cors_allowed_origins({
        "CORS_ALLOWED_ORIGINS": "https://cal-ai-api.vercel.app",
        "ADMIN_FRONTEND_ORIGIN": "https://cal-ai-admin.vercel.app/",
    })
    assert origins == [
        "https://cal-ai-api.vercel.app",
        "https://cal-ai-admin.vercel.app",
    ]


def test_reporting_day_uses_korea_midnight_by_default() -> None:
    now = datetime(2026, 8, 29, 1, 30, tzinfo=UTC)
    assert reporting_day_start(now) == datetime(2026, 8, 28, 15, 0, tzinfo=UTC)


def test_admin_dev_origin_passes_cors_preflight() -> None:
    response = client.options(
        "/internal/admin/overview",
        headers={
            "Origin": "http://localhost:3016",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3016"


def test_anonymous_events_and_heartbeat_feed_admin_overview(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "disabled")
    for event_name in (
        "app_opened",
        "onboarding_completed",
        "meal_photo_selected",
        "analysis_started",
        "analysis_completed",
        "meal_saved",
    ):
        response = client.post("/v1/analytics/events", json=event_payload(event_name))
        assert response.status_code == 200

    heartbeat = client.post(
        "/v1/analytics/heartbeat",
        json={"session_id": "session_12345678", "screen": "today", "profile_id": None},
    )
    assert heartbeat.status_code == 200

    monkeypatch.setattr(
        admin_routes,
        "authenticate_admin_bearer_token",
        lambda _authorization: AuthenticatedUser(user_id="admin-owner"),
    )
    overview = client.get(
        "/internal/admin/overview",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert overview.status_code == 200
    body = overview.json()
    assert body["metrics"]["today_users"] == 1
    assert body["metrics"]["realtime_users"] == 1
    assert body["metrics"]["food_analyses_today"] == 1
    assert body["metrics"]["meals_saved_today"] == 1
    assert body["ai_operations"]["success_rate"] == 1
    assert [stage["users"] for stage in body["funnel"][:5]] == [1, 1, 1, 1, 1]
    assert body["payments"]["provider_configured"] is False


def test_authenticated_events_create_user_and_user_detail(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "supabase")
    monkeypatch.setattr(
        main,
        "authenticate_bearer_token",
        lambda _authorization: AuthenticatedUser(
            user_id="member-1",
            provider="kakao",
            email="member@example.com",
            display_name="테스터",
        ),
    )
    response = client.post(
        "/v1/analytics/events",
        json=event_payload("app_opened", session_id="member_session_1"),
        headers={"Authorization": "Bearer member-token"},
    )
    assert response.status_code == 200
    analysis = client.post(
        "/v1/analytics/events",
        json=event_payload("analysis_completed", session_id="member_session_1"),
        headers={"Authorization": "Bearer member-token"},
    )
    assert analysis.status_code == 200

    monkeypatch.setattr(
        admin_routes,
        "authenticate_admin_bearer_token",
        lambda _authorization: AuthenticatedUser(user_id="admin-owner"),
    )
    overview = client.get(
        "/internal/admin/overview",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert overview.status_code == 200
    user = overview.json()["users"][0]
    assert user["user_id"] == "member-1"
    assert user["provider"] == "kakao"
    assert user["display_name"] == "테스터"
    assert user["online"] is True

    detail = client.get(
        "/internal/admin/users/member-1",
        headers={"Authorization": "Bearer admin-token"},
    )
    assert detail.status_code == 200
    assert detail.json()["user"]["event_count"] == 2
    assert detail.json()["user"]["analysis_count"] == 1
    assert detail.headers["Cache-Control"] == "no-store, max-age=0"


def test_admin_users_are_loaded_with_one_bounded_aggregate_query() -> None:
    repo = get_analytics_repository()
    seen_at = now_utc()
    for index in range(3):
        user = AuthenticatedUser(user_id=f"member-{index}", provider="kakao")
        session_id = f"member_session_{index}"
        for event_name in ("app_opened", "analysis_completed", "meal_saved", "workout_completed"):
            repo.record_event(
                AnalyticsEventRequest(event_name=event_name, session_id=session_id, screen=event_name, profile_id=None),
                user,
            )
    with repo._connection() as conn:
        conn.execute(
            repo._sql(
                "insert into billing_subscriptions "
                "(subscription_id, user_id, provider, plan, status, current_period_end, created_at, updated_at) "
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            ("sub-member-1", "member-1", "groble", "pro", "active", None, iso(seen_at), iso(seen_at)),
        )

        class CountingConnection:
            def __init__(self, wrapped):
                self.wrapped = wrapped
                self.execute_count = 0

            def execute(self, *args, **kwargs):
                self.execute_count += 1
                return self.wrapped.execute(*args, **kwargs)

        counting_conn = CountingConnection(conn)
        users = repo._users(
            counting_conn,
            now=seen_at,
            realtime_start=seen_at,
        )

    assert counting_conn.execute_count == 1
    summaries = {user.user_id: user for user in users}
    assert summaries["member-0"].event_count == 4
    assert summaries["member-0"].analysis_count == 1
    assert summaries["member-0"].meal_save_count == 1
    assert summaries["member-0"].workout_count == 1
    assert summaries["member-0"].last_screen == "workout_completed"
    assert summaries["member-0"].plan == "free"
    assert summaries["member-1"].plan == "pro"


def test_admin_endpoint_is_concealed_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "false")
    response = client.get("/internal/admin/overview")
    assert response.status_code == 404


def test_admin_allowlist_is_required(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.setenv("ADMIN_SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("ADMIN_SUPABASE_JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-owner")
    monkeypatch.setattr(
        "app.services.auth._authenticate_supabase_bearer_token",
        lambda *_args, **_kwargs: AuthenticatedUser(user_id="different-user"),
    )
    response = client.get(
        "/internal/admin/overview",
        headers={"Authorization": "Bearer valid-but-not-admin"},
    )
    assert response.status_code == 403


def test_admin_auth_does_not_fall_back_to_consumer_supabase(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.delenv("ADMIN_SUPABASE_URL", raising=False)
    monkeypatch.delenv("ADMIN_SUPABASE_JWT_ALGORITHM", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://consumer.supabase.co")
    monkeypatch.setenv("SUPABASE_JWT_ALGORITHM", "ES256")
    monkeypatch.setenv("ADMIN_USER_IDS", "admin-owner")

    response = client.get(
        "/internal/admin/overview",
        headers={"Authorization": "Bearer consumer-token"},
    )

    assert response.status_code == 503
    ready = client.get("/ready")
    assert ready.json()["admin"]["status"] == "misconfigured"


def test_analytics_properties_reject_freeform_sensitive_payloads(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "disabled")
    payload = event_payload("app_opened")
    payload["properties"] = {"note": "must never reach analytics storage"}
    response = client.post("/v1/analytics/events", json=payload)
    assert response.status_code == 422


def test_billing_status_is_safe_before_groble_configuration(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "disabled")
    monkeypatch.delenv("PAYMENT_PROVIDER", raising=False)
    response = client.get("/v1/billing/status")
    assert response.status_code == 200
    assert response.json() == {
        "plan": "beta",
        "status": "active",
        "checkout_available": False,
        "provider": None,
        "message": "베타 기간에는 무료로 이용할 수 있어요. 결제 연결 후 Pro를 열 예정이에요.",
    }


def test_billing_does_not_claim_checkout_before_order_and_webhook_endpoints(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "disabled")
    monkeypatch.setenv("PAYMENT_PROVIDER", "groble")
    monkeypatch.setenv("GROBLE_PRODUCT_ID", "product-1")
    monkeypatch.setenv("GROBLE_WEBHOOK_SECRET", "test-webhook-secret")

    response = client.get("/v1/billing/status")

    assert response.status_code == 200
    assert response.json()["checkout_available"] is False
    assert "준비 중" in response.json()["message"]


def test_ready_reports_admin_configuration_without_echoing_allowlist(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_DASHBOARD_ENABLED", "true")
    monkeypatch.setenv("ADMIN_SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("ADMIN_SUPABASE_JWT_ALGORITHM", "ES256")
    monkeypatch.setenv("ADMIN_USER_IDS", "owner-private-uuid")
    monkeypatch.setenv("ADMIN_LOGIN_USERNAME", "owner-alias-fixture")
    monkeypatch.setenv("ADMIN_LOGIN_EMAIL", "owner@example.test")
    monkeypatch.setenv("ADMIN_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_fixture")

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["admin"]["status"] == "ok"
    assert "owner-private-uuid" not in response.text
    assert "owner@example.test" not in response.text
    assert "sb_publishable_fixture" not in response.text
