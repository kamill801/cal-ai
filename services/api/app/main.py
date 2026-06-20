from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
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
    ImageUploadCompleteRequest,
    ImageUploadPresignRequest,
    ImageUploadPresignResponse,
    ImageUploadRequest,
    ImageUploadResponse,
    MealLogRequest,
    OnboardingRequest,
    OnboardingResponse,
    ReadyDependencyResponse,
    ReadyResponse,
    SavedImpactResponse,
)
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    AnalysisProviderDryRunError,
    StructuredOutputMalformedError,
    get_analysis_provider,
)
from app.services.image_uploads import ImageUploadError, complete_presigned_image_upload, create_mock_image_upload, create_presigned_image_upload, resolve_image_reference
from app.services.mock_analysis import get_mock_dashboard_today
from app.services.persistence import PersistenceError, PersistenceRepository, get_persistence_repository
from app.services.storage import get_storage_readiness
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
        retryable=False,
        kind="provider",
    )


def provider_dry_run_error() -> HTTPException:
    return api_error(
        status_code=503,
        code="analysis_provider_dry_run",
        message="실제 AI 분석 호출은 아직 비활성화되어 있어요. 로컬 mock 설정을 확인해 주세요.",
        retryable=False,
        kind="provider",
    )


def malformed_output_error() -> HTTPException:
    return api_error(
        status_code=503,
        code="analysis_output_malformed",
        message="분석 결과 형식이 올바르지 않아 다시 시도해야 해요.",
        retryable=True,
        kind="provider",
    )


def persistence_unavailable_error() -> HTTPException:
    return api_error(
        status_code=503,
        code="persistence_unavailable",
        message="로컬 저장소를 사용할 수 없어요. API 설정을 확인한 뒤 다시 시도해 주세요.",
        retryable=True,
        kind="server",
    )


def image_upload_error(exc: ImageUploadError) -> HTTPException:
    if exc.code == "image_upload_not_found":
        return api_error(status_code=404, code=exc.code, message=exc.message, retryable=False, kind="not_found")
    return api_error(
        status_code=400 if not exc.retryable else 503,
        code=exc.code,
        message=exc.message,
        retryable=exc.retryable,
        kind="validation" if not exc.retryable else "server",
    )


def provider_error_from_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, StructuredOutputMalformedError):
        return malformed_output_error()
    if isinstance(exc, AnalysisProviderDryRunError):
        return provider_dry_run_error()
    return provider_unavailable_error()


def persistence_repository() -> PersistenceRepository:
    try:
        return get_persistence_repository()
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc


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


@app.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    database_status = ReadyDependencyResponse(status="ok", provider="sqlite-or-postgres")
    try:
        get_persistence_repository().check_ready()
    except PersistenceError:
        database_status = ReadyDependencyResponse(status="degraded", provider="sqlite-or-postgres", message="database unavailable")

    storage_readiness = get_storage_readiness()
    storage_status = ReadyDependencyResponse(
        status=storage_readiness.status,
        provider=storage_readiness.provider,
        message=storage_readiness.message,
    )
    overall_status = "ok" if database_status.status == "ok" and storage_status.status == "ok" else "degraded"
    return ReadyResponse(status=overall_status, service="cal-ai-api", database=database_status, storage=storage_status)


@app.post("/v1/onboarding", response_model=OnboardingResponse)
def create_onboarding(payload: OnboardingRequest) -> OnboardingResponse:
    target, warnings = calculate_initial_target(payload)
    return OnboardingResponse(profile_id=uuid4(), target=target, warnings=warnings)


@app.get("/v1/dashboard/today", response_model=DashboardTodayResponse)
def dashboard_today() -> DashboardTodayResponse:
    return get_mock_dashboard_today()


@app.post("/v1/image-uploads", response_model=ImageUploadResponse)
def create_image_upload(
    payload: ImageUploadRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> ImageUploadResponse:
    try:
        return create_mock_image_upload(payload, repository=repository)
    except ImageUploadError as exc:
        raise image_upload_error(exc) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc


@app.post("/image-uploads/presign", response_model=ImageUploadPresignResponse)
def presign_image_upload(payload: ImageUploadPresignRequest) -> ImageUploadPresignResponse:
    try:
        return create_presigned_image_upload(payload)
    except ImageUploadError as exc:
        raise image_upload_error(exc) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc


@app.post("/image-uploads/complete", response_model=ImageUploadResponse)
def complete_image_upload(
    payload: ImageUploadCompleteRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> ImageUploadResponse:
    try:
        return complete_presigned_image_upload(payload, repository=repository)
    except ImageUploadError as exc:
        raise image_upload_error(exc) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc


@app.post("/v1/analysis-jobs", response_model=AnalysisJobCreateResponse)
def create_analysis_job(
    payload: AnalysisJobRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> AnalysisJobCreateResponse:
    try:
        image_reference = resolve_image_reference(payload.image_upload_id, repository=repository)
        response = get_analysis_provider().create_job(payload)
        repository.save_analysis_job(
            payload=payload,
            image_reference=image_reference,
            create_response=response,
        )
        return response
    except ImageUploadError as exc:
        raise image_upload_error(exc) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.get("/v1/analysis-jobs/{job_id}", response_model=AnalysisJobResponse)
def analysis_job(
    job_id: str,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> AnalysisJobResponse:
    try:
        response = get_analysis_provider().get_job(job_id)
        repository.save_analysis_job_response(response)
        return response
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.post("/v1/analysis-jobs/{job_id}/clarifications", response_model=ClarificationResponse)
def clarify_analysis_job(
    job_id: str,
    payload: ClarificationRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> ClarificationResponse:
    try:
        response = get_analysis_provider().apply_clarification(job_id, payload)
        repository.save_clarification(analysis_job_id=job_id, payload=payload, response=response)
        return response
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.post("/v1/meal-logs", response_model=SavedImpactResponse)
def create_meal_log(
    payload: MealLogRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> SavedImpactResponse:
    try:
        response = get_analysis_provider().save_meal(payload)
        repository.save_meal_log(payload=payload, response=response)
        return response
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc
