from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas import (
    ApiErrorDetail,
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

ApiErrorKind = Literal["provider", "validation", "not_found", "server", "unknown"]

app = FastAPI(
    title="Trust-First AI Nutrition Logger API",
    version="0.1.0",
)


def api_error(*, status_code: int, code: str, message: str, retryable: bool, kind: ApiErrorKind) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ApiErrorDetail(code=code, message=message, retryable=retryable, kind=kind).model_dump(),
    )


def provider_unavailable_error() -> HTTPException:
    return api_error(
        status_code=503,
        code="analysis_provider_unavailable",
        message="분석 제공자를 사용할 수 없어요. 로컬 mock 설정을 확인해 주세요.",
        retryable=True,
        kind="provider",
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    detail = ApiErrorDetail(
        code="validation_error",
        message="요청 형식이 올바르지 않아요. 입력값을 확인해 주세요.",
        retryable=False,
        kind="validation",
    )
    return JSONResponse(status_code=422, content={"detail": detail.model_dump()})


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
