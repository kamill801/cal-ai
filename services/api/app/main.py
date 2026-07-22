from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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
from app.coach_routes import router as coach_router
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    AnalysisProviderDryRunError,
    AnalysisProviderUnavailableError,
    StructuredOutputMalformedError,
    failed_analysis_job,
    get_analysis_provider,
)
from app.services.analysis_results import apply_persisted_clarification, save_persisted_meal
from app.services.image_uploads import ImageUploadError, complete_presigned_image_upload, create_mock_image_upload, create_presigned_image_upload, resolve_analysis_image_reference, resolve_image_reference
from app.services.mock_analysis import get_mock_dashboard_today
from app.services.persistence import PersistenceError, PersistenceRepository, get_persistence_repository
from app.services.storage import get_storage_readiness
from app.services.targets import calculate_initial_target
from app.services.coach import CoachNotFoundError, create_profile, merge_profile_meal_impact
from app.services.coach_repository import get_coach_repository

ApiErrorKind = Literal["provider", "validation", "not_found", "server", "unknown"]
DEFAULT_CORS_ALLOWED_ORIGINS = ("http://localhost:8081", "http://127.0.0.1:8081")


def get_cors_allowed_origins(environ: Mapping[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    raw_value = env.get("CORS_ALLOWED_ORIGINS")
    if not raw_value:
        return list(DEFAULT_CORS_ALLOWED_ORIGINS)
    return [origin for origin in (value.strip() for value in raw_value.split(",")) if origin]


app = FastAPI(
    title="Trust-First AI Nutrition Logger API",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(coach_router)


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
    if exc.code == "image_upload_object_missing":
        return api_error(status_code=409, code=exc.code, message=exc.message, retryable=True, kind="validation")
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
    if isinstance(exc, AnalysisProviderUnavailableError):
        return api_error(
            status_code=503,
            code="analysis_provider_unavailable",
            message="AI 분석 서비스가 응답하지 않아요. 잠시 후 다시 시도해 주세요.",
            retryable=True,
            kind="provider",
        )
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
    provider_name = os.environ.get("AI_PROVIDER", "mock").strip().lower() or "mock"
    if provider_name == "mock":
        ai_status = ReadyDependencyResponse(status="ok", provider="mock", message="deterministic mock analysis enabled")
    elif provider_name == "openai" and (os.environ.get("AI_MODEL_VISION") or "").startswith("sk-"):
        ai_status = ReadyDependencyResponse(
            status="misconfigured",
            provider="openai",
            message="OpenAI vision model is invalid",
        )
    elif provider_name == "openai" and os.environ.get("AI_PROVIDER_API_KEY"):
        ai_status = ReadyDependencyResponse(
            status="ok",
            provider="openai",
            message="vision model configured",
        )
    elif provider_name == "openai":
        ai_status = ReadyDependencyResponse(status="misconfigured", provider="openai", message="OpenAI API key is missing")
    else:
        ai_status = ReadyDependencyResponse(status="misconfigured", provider=provider_name, message="unsupported AI provider")
    dependencies = (database_status, storage_status, ai_status)
    overall_status = "ok" if all(item.status == "ok" for item in dependencies) else "degraded"
    return ReadyResponse(
        status=overall_status,
        service="cal-ai-api",
        database=database_status,
        storage=storage_status,
        ai=ai_status,
    )


@app.post("/v1/onboarding", response_model=OnboardingResponse)
def create_onboarding(payload: OnboardingRequest) -> OnboardingResponse:
    target, warnings = calculate_initial_target(payload)
    profile_id = str(uuid4())
    try:
        create_profile(profile_id=profile_id, onboarding=payload, target=target, repository=get_coach_repository())
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    return OnboardingResponse(profile_id=profile_id, target=target, warnings=warnings)


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
        stored_image_reference = resolve_image_reference(payload.image_upload_id, repository=repository)
        provider = get_analysis_provider()
        response = provider.create_job(payload)
        repository.save_analysis_job(
            payload=payload,
            image_reference=stored_image_reference,
            create_response=response,
        )
        if provider.processes_jobs_synchronously:
            try:
                analysis_response = provider.analyze(
                    job_id=response.analysis_job_id,
                    payload=payload,
                    image_reference=resolve_analysis_image_reference(payload.image_upload_id, repository=repository),
                )
                repository.save_analysis_job_response(analysis_response)
            except (AnalysisProviderConfigurationError, AnalysisProviderUnavailableError, StructuredOutputMalformedError) as exc:
                repository.save_analysis_job_response(
                    failed_analysis_job(
                        response.analysis_job_id,
                        code="analysis_provider_failed",
                        message="사진 분석을 완료하지 못했어요. 다시 시도해 주세요.",
                    )
                )
                raise exc
        return response
    except ImageUploadError as exc:
        raise image_upload_error(exc) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, AnalysisProviderUnavailableError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.get("/v1/analysis-jobs/{job_id}", response_model=AnalysisJobResponse)
def analysis_job(
    job_id: str,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> AnalysisJobResponse:
    try:
        provider = get_analysis_provider()
        record = repository.get_analysis_job(job_id)
        if record and record.response:
            return record.response
        if provider.uses_persisted_result_operations:
            raise api_error(
                status_code=404,
                code="analysis_job_not_found",
                message="분석 작업을 찾을 수 없어요. 사진을 다시 분석해 주세요.",
                retryable=False,
                kind="not_found",
            )
        response = provider.get_job(job_id)
        repository.save_analysis_job_response(response)
        return response
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, AnalysisProviderUnavailableError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.post("/v1/analysis-jobs/{job_id}/clarifications", response_model=ClarificationResponse)
def clarify_analysis_job(
    job_id: str,
    payload: ClarificationRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> ClarificationResponse:
    try:
        provider = get_analysis_provider()
        record = repository.get_analysis_job(job_id)
        if provider.uses_persisted_result_operations and record and record.response and record.response.result:
            response = apply_persisted_clarification(record.response.result, payload)
        elif provider.uses_persisted_result_operations:
            raise api_error(
                status_code=404,
                code="analysis_job_not_found",
                message="분석 결과를 찾을 수 없어요. 사진을 다시 분석해 주세요.",
                retryable=False,
                kind="not_found",
            )
        else:
            response = provider.apply_clarification(job_id, payload)
        repository.save_clarification(analysis_job_id=job_id, payload=payload, response=response)
        return response
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, AnalysisProviderUnavailableError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc


@app.post("/v1/meal-logs", response_model=SavedImpactResponse)
def create_meal_log(
    payload: MealLogRequest,
    repository: PersistenceRepository = Depends(persistence_repository),
) -> SavedImpactResponse:
    try:
        provider = get_analysis_provider()
        record = repository.get_analysis_job(payload.analysis_job_id)
        if provider.uses_persisted_result_operations and record and record.response and record.response.result:
            if payload.result_id != record.response.result.id:
                raise api_error(
                    status_code=409,
                    code="analysis_result_mismatch",
                    message="저장하려는 결과가 최신 분석 결과와 일치하지 않아요.",
                    retryable=False,
                    kind="validation",
                )
            response = save_persisted_meal(record.response.result, payload)
        elif provider.uses_persisted_result_operations:
            raise api_error(
                status_code=404,
                code="analysis_job_not_found",
                message="저장할 분석 결과를 찾을 수 없어요.",
                retryable=False,
                kind="not_found",
            )
        else:
            response = provider.save_meal(payload)
        if payload.profile_id:
            response = merge_profile_meal_impact(
                payload.profile_id,
                payload,
                response,
                repository=get_coach_repository(),
                meal_repository=repository,
            )
        repository.save_meal_log(payload=payload, response=response)
        return response
    except CoachNotFoundError as exc:
        raise api_error(
            status_code=404,
            code=str(exc),
            message="프로필을 찾을 수 없어요.",
            retryable=False,
            kind="not_found",
        ) from exc
    except PersistenceError as exc:
        raise persistence_unavailable_error() from exc
    except (AnalysisProviderConfigurationError, AnalysisProviderDryRunError, AnalysisProviderUnavailableError, StructuredOutputMalformedError) as exc:
        raise provider_error_from_exception(exc) from exc
