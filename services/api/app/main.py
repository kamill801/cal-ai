from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI

from app.schemas import (
    AnalysisJobCreateResponse,
    AnalysisJobRequest,
    AnalysisJobResponse,
    ClarificationRequest,
    ClarificationResponse,
    DashboardTodayResponse,
    HealthResponse,
    MealLogRequest,
    OnboardingRequest,
    OnboardingResponse,
    SavedImpactResponse,
)
from app.services.mock_analysis import apply_mock_clarification, get_mock_analysis_job, get_mock_dashboard_today, save_mock_meal
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


@app.post("/v1/analysis-jobs", response_model=AnalysisJobCreateResponse)
def create_analysis_job(payload: AnalysisJobRequest) -> AnalysisJobCreateResponse:
    return AnalysisJobCreateResponse(analysis_job_id=f"mock-{payload.meal_type}-001", status="queued")


@app.get("/v1/analysis-jobs/{job_id}", response_model=AnalysisJobResponse)
def analysis_job(job_id: str) -> AnalysisJobResponse:
    return get_mock_analysis_job(job_id)


@app.post("/v1/analysis-jobs/{job_id}/clarifications", response_model=ClarificationResponse)
def clarify_analysis_job(job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
    rice_answer = next((answer.value for answer in payload.answers if answer.question_key == "rice_amount"), "unknown")
    return apply_mock_clarification(job_id, rice_answer)


@app.post("/v1/meal-logs", response_model=SavedImpactResponse)
def create_meal_log(payload: MealLogRequest) -> SavedImpactResponse:
    return save_mock_meal(payload.clarification_value, payload.analysis_job_id)
