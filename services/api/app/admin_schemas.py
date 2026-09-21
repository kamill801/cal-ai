from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


AnalyticsProperty = str | int | float | bool | None
ANALYTICS_ALLOWED_PROPERTY_KEYS = frozenset(
    {
        "answer",
        "byte_size",
        "clarification",
        "code",
        "confidence",
        "content_type",
        "duration_minutes",
        "exercise_count",
        "goal_type",
        "provider",
        "question_key",
        "result_id",
        "session_rpe",
        "source",
        "stage",
        "status",
        "training_frequency",
        "workout_day_id",
    }
)


class AnalyticsEventName(StrEnum):
    app_opened = "app_opened"
    login_completed = "login_completed"
    onboarding_started = "onboarding_started"
    onboarding_completed = "onboarding_completed"
    meal_photo_selected = "meal_photo_selected"
    analysis_started = "analysis_started"
    analysis_completed = "analysis_completed"
    analysis_failed = "analysis_failed"
    clarification_shown = "clarification_shown"
    clarification_answered = "clarification_answered"
    meal_saved = "meal_saved"
    workout_plan_viewed = "workout_plan_viewed"
    workout_started = "workout_started"
    workout_completed = "workout_completed"
    progress_viewed = "progress_viewed"
    coach_viewed = "coach_viewed"
    plan_viewed = "plan_viewed"
    checkout_started = "checkout_started"


class AnalyticsEventRequest(BaseModel):
    event_name: AnalyticsEventName
    session_id: str = Field(min_length=8, max_length=120, pattern=r"^[A-Za-z0-9_-]+$")
    screen: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_./-]+$")
    profile_id: str | None = Field(default=None, min_length=1, max_length=180)
    properties: dict[str, AnalyticsProperty] = Field(default_factory=dict)
    occurred_at: datetime | None = None

    @field_validator("properties")
    @classmethod
    def validate_properties(
        cls,
        value: dict[str, AnalyticsProperty],
    ) -> dict[str, AnalyticsProperty]:
        if len(value) > 12:
            raise ValueError("analytics properties are limited to 12 keys")
        sanitized: dict[str, AnalyticsProperty] = {}
        for key, item in value.items():
            if key not in ANALYTICS_ALLOWED_PROPERTY_KEYS:
                raise ValueError("analytics property key is not allowed")
            if isinstance(item, str) and len(item) > 120:
                raise ValueError("analytics string properties are limited to 120 characters")
            sanitized[key] = item
        return sanitized


class AnalyticsHeartbeatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=120, pattern=r"^[A-Za-z0-9_-]+$")
    screen: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_./-]+$")
    profile_id: str | None = Field(default=None, min_length=1, max_length=180)


class AnalyticsAcceptedResponse(BaseModel):
    status: str = "accepted"
    accepted_at: datetime


class AdminMetricSummary(BaseModel):
    total_users: int = Field(ge=0)
    today_users: int = Field(ge=0)
    new_users_today: int = Field(ge=0)
    realtime_users: int = Field(ge=0)
    active_users_24h: int = Field(ge=0)
    food_analyses_today: int = Field(ge=0)
    analysis_failures_today: int = Field(ge=0)
    meals_saved_today: int = Field(ge=0)
    workouts_completed_today: int = Field(ge=0)


class AdminFunnelStage(BaseModel):
    event_name: str
    label: str
    users: int = Field(ge=0)
    conversion_from_previous: float = Field(ge=0, le=1)
    dropoff_from_previous: float = Field(ge=0, le=1)


class AdminActivityItem(BaseModel):
    event_id: str
    user_id: str | None = None
    display_name: str | None = None
    session_id: str
    event_name: str
    screen: str
    occurred_at: datetime


class AdminUserSummary(BaseModel):
    user_id: str
    provider: str | None = None
    email: str | None = None
    display_name: str | None = None
    first_seen_at: datetime
    last_seen_at: datetime
    last_screen: str | None = None
    online: bool
    event_count: int = Field(ge=0)
    analysis_count: int = Field(ge=0)
    meal_save_count: int = Field(ge=0)
    workout_count: int = Field(ge=0)
    plan: str = "free"


class AdminPaymentSummary(BaseModel):
    payment_id: str
    user_id: str | None = None
    provider: str
    product_id: str
    amount: int = Field(ge=0)
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime


class AdminPaymentOverview(BaseModel):
    provider_configured: bool
    provider_name: str | None = None
    gross_revenue_krw: int = Field(ge=0)
    active_subscriptions: int = Field(ge=0)
    paid_count: int = Field(ge=0)
    pending_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    refunded_count: int = Field(ge=0)
    recent_payments: list[AdminPaymentSummary]


class AdminAiOperations(BaseModel):
    started_today: int = Field(ge=0)
    completed_today: int = Field(ge=0)
    failed_today: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=1)


class AdminOverviewResponse(BaseModel):
    generated_at: datetime
    realtime_window_minutes: int = 5
    metrics: AdminMetricSummary
    funnel: list[AdminFunnelStage]
    recent_activity: list[AdminActivityItem]
    users: list[AdminUserSummary]
    payments: AdminPaymentOverview
    ai_operations: AdminAiOperations


class AdminUserDetailResponse(BaseModel):
    user: AdminUserSummary
    recent_activity: list[AdminActivityItem]
    payments: list[AdminPaymentSummary]


class BillingStatusResponse(BaseModel):
    plan: str
    status: str
    checkout_available: bool
    provider: str | None = None
    message: str


AdminUserId = Annotated[str, Field(min_length=1, max_length=180)]
