from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI

from app.schemas import DashboardTodayResponse, HealthResponse, OnboardingRequest, OnboardingResponse
from app.services.mock_analysis import get_mock_dashboard_today
from app.services.targets import calculate_initial_target

app = FastAPI(
    title="Trust-First AI Nutrition Logger API",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cal-ai-api")


@app.post("/v1/onboarding", response_model=OnboardingResponse)
def create_onboarding(payload: OnboardingRequest) -> OnboardingResponse:
    target, warnings = calculate_initial_target(payload)
    return OnboardingResponse(profile_id=uuid4(), target=target, warnings=warnings)


@app.get("/v1/dashboard/today", response_model=DashboardTodayResponse)
def dashboard_today() -> DashboardTodayResponse:
    return get_mock_dashboard_today()
