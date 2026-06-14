from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

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
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    AnalysisProviderDryRunError,
    StructuredOutputMalformedError,
    get_analysis_provider,
)
from app.services.mock_analysis import get_mock_dashboard_today
from app.services.targets import calculate_initial_target

app = FastAPI(
    title="Trust-First AI Nutrition Logger API",
    version="0.1.0",
)


def provider_unavailable_error() -> HTTPException:
    return HTTPException(status_code=503, detail={"code": "analysis_provider_unavailable", "message": "분석 제공자를 사용할 수 없어요. 로컬 mock 설정을 확인해 주세요."})


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
    try:
        return get_analysis_provider().create_job(payload)
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_unavailable_error() from exc


@app.get("/v1/analysis-jobs/{job_id}", response_model=AnalysisJobResponse)
def analysis_job(job_id: str) -> AnalysisJobResponse:
    try:
        return get_analysis_provider().get_job(job_id)
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_unavailable_error() from exc


@app.post("/v1/analysis-jobs/{job_id}/clarifications", response_model=ClarificationResponse)
def clarify_analysis_job(job_id: str, payload: ClarificationRequest) -> ClarificationResponse:
    try:
        return get_analysis_provider().apply_clarification(job_id, payload)
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_unavailable_error() from exc


@app.post("/v1/meal-logs", response_model=SavedImpactResponse)
def create_meal_log(payload: MealLogRequest) -> SavedImpactResponse:
    try:
        return get_analysis_provider().save_meal(payload)
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_unavailable_error() from exc
