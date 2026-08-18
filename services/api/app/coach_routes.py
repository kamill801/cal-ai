from __future__ import annotations

import os
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.coach_schemas import (
    BodyAnalysisConsent,
    BodyCheckInRequest,
    BodyCheckInResponse,
    CoachDashboardResponse,
    ProfileDeletionResponse,
    ProgressResponse,
    WeightLogRequest,
    WeightLogResponse,
    WellnessCheckInRequest,
    WellnessCheckInResponse,
    WeeklyCoachResponse,
    WorkoutPlanResponse,
    WorkoutSessionRequest,
    WorkoutSessionResponse,
)
from app.schemas import ApiErrorDetail
from app.services.coach import (
    CoachNotFoundError,
    create_body_check_in,
    dashboard_today,
    generate_workout_plan,
    log_weight,
    log_wellness,
    log_workout_session,
    progress,
    weekly_coach,
)
from app.services.coach_repository import CoachRepository, get_coach_repository
from app.services.analysis_provider import AnalysisProviderConfigurationError, AnalysisProviderUnavailableError, StructuredOutputMalformedError
from app.services.body_analysis_provider import get_body_analysis_provider
from app.services.image_uploads import ImageUploadError, resolve_analysis_image_reference
from app.services.persistence import PersistenceError, PersistenceRepository, get_persistence_repository
from app.services.storage import StorageConfigurationError, get_storage_adapter


router = APIRouter(prefix="/v1/profiles", tags=["coach"])


def coach_repository() -> CoachRepository:
    try:
        return get_coach_repository()
    except PersistenceError as exc:
        raise _error(503, "persistence_unavailable", "코칭 데이터를 불러오지 못했어요.", True, "server") from exc


def meal_repository() -> PersistenceRepository:
    try:
        return get_persistence_repository()
    except PersistenceError as exc:
        raise _error(503, "persistence_unavailable", "식사 기록을 불러오지 못했어요.", True, "server") from exc


def authorized_coach_repository(
    profile_id: str,
    request: Request,
    repository: CoachRepository = Depends(coach_repository),
) -> CoachRepository:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        profile = repository.get_profile(profile_id)
        if profile is not None and profile.owner_id != user_id:
            raise _error(404, "profile_not_found", "프로필을 찾을 수 없어요.", False, "not_found")
    return repository


@router.delete("/{profile_id}", response_model=ProfileDeletionResponse)
def delete_profile_data(
    profile_id: str,
    request: Request,
    repository: CoachRepository = Depends(authorized_coach_repository),
    meals: PersistenceRepository = Depends(meal_repository),
) -> ProfileDeletionResponse:
    try:
        profile = repository.get_profile(profile_id)
        if profile is None:
            raise CoachNotFoundError("profile_not_found")

        owner_id = getattr(request.state, "user_id", None)
        body_image_ids = [item.image_upload_id for item in repository.list_body_check_ins(profile_id)]
        meal_logs = [record for record in meals.list_meal_logs() if record.request.profile_id == profile_id]
        image_records = meals.list_profile_image_uploads(
            profile_id,
            owner_id=owner_id,
            additional_image_upload_ids=body_image_ids,
        )
        storage = get_storage_adapter()
        for image_record in image_records:
            if image_record.object_key:
                if image_record.storage_provider != storage.provider:
                    raise StorageConfigurationError("stored image provider does not match active storage provider")
                meals.mark_image_upload_deleting(image_record.image_upload_id)
                storage.delete_object(object_key=image_record.object_key)

        meals.delete_profile_artifacts(
            profile_id,
            owner_id=owner_id,
            additional_image_upload_ids=body_image_ids,
        )
        repository.delete_profile(profile_id)
        return ProfileDeletionResponse(
            profile_id=profile_id,
            status="deleted",
            deleted_images=len(image_records),
            deleted_meal_logs=len(meal_logs),
        )
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except StorageConfigurationError as exc:
        raise _error(503, "storage_delete_unavailable", "사진 삭제를 완료하지 못했어요. 잠시 후 다시 시도해 주세요.", True, "server") from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.get("/{profile_id}/dashboard/today", response_model=CoachDashboardResponse)
def get_dashboard(
    profile_id: str,
    logged_on: date | None = None,
    repository: CoachRepository = Depends(authorized_coach_repository),
    meals: PersistenceRepository = Depends(meal_repository),
) -> CoachDashboardResponse:
    try:
        return dashboard_today(profile_id, repository=repository, meal_repository=meals, logged_on=logged_on)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/weight-logs", response_model=WeightLogResponse)
def create_weight_log(
    profile_id: str,
    payload: WeightLogRequest,
    repository: CoachRepository = Depends(authorized_coach_repository),
) -> WeightLogResponse:
    try:
        return log_weight(profile_id, payload, repository=repository)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/wellness-check-ins", response_model=WellnessCheckInResponse)
def create_wellness_check_in(
    profile_id: str,
    payload: WellnessCheckInRequest,
    repository: CoachRepository = Depends(authorized_coach_repository),
) -> WellnessCheckInResponse:
    try:
        return log_wellness(profile_id, payload, repository=repository)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/body-check-ins", response_model=BodyCheckInResponse)
def create_body_photo_check_in(
    profile_id: str,
    payload: BodyCheckInRequest,
    request: Request,
    repository: CoachRepository = Depends(authorized_coach_repository),
    uploads: PersistenceRepository = Depends(meal_repository),
) -> BodyCheckInResponse:
    try:
        upload = uploads.get_image_upload(payload.image_upload_id)
        owner_id = getattr(request.state, "user_id", None)
        if upload is None or (owner_id and upload.owner_id != owner_id):
            raise _error(404, "image_upload_not_found", "업로드된 이미지를 찾을 수 없어요.", False, "not_found")
        if upload.upload_status != "ready":
            raise _error(400, "image_upload_not_ready", "이미지 업로드가 아직 완료되지 않았어요.", True, "validation")
        image_reference = resolve_analysis_image_reference(
            payload.image_upload_id,
            uploads,
            owner_id=owner_id,
        )
        provider = get_body_analysis_provider()
        analysis = provider.analyze(
            image_reference=image_reference,
            view=payload.view,
            has_previous=bool(repository.list_body_check_ins(profile_id)),
        )
        return create_body_check_in(
            profile_id,
            payload,
            repository=repository,
            analysis=analysis,
            consent=BodyAnalysisConsent(
                consented_at=datetime.now(UTC).isoformat(timespec="seconds"),
                provider=analysis.provider,
                model=provider.model_name,
                policy_version=os.environ.get("BODY_AI_CONSENT_POLICY_VERSION", "2026-07-23"),
            ),
        )
    except AnalysisProviderConfigurationError as exc:
        raise _error(503, "body_analysis_provider_unavailable", "신체 사진 분석 설정을 확인해 주세요.", False, "provider") from exc
    except StructuredOutputMalformedError as exc:
        raise _error(503, "body_analysis_output_malformed", "신체 사진 분석 결과를 확인하지 못했어요. 다시 시도해 주세요.", True, "provider") from exc
    except AnalysisProviderUnavailableError as exc:
        raise _error(503, "body_analysis_provider_unavailable", "신체 사진 분석 서비스가 응답하지 않아요. 잠시 후 다시 시도해 주세요.", True, "provider") from exc
    except ImageUploadError as exc:
        raise _error(400, exc.code, exc.message, exc.retryable, "validation") from exc
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/workout-plans/generate", response_model=WorkoutPlanResponse)
def create_workout_plan(
    profile_id: str,
    repository: CoachRepository = Depends(authorized_coach_repository),
) -> WorkoutPlanResponse:
    try:
        return generate_workout_plan(profile_id, repository=repository)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.get("/{profile_id}/workout-plan", response_model=WorkoutPlanResponse)
def get_workout_plan(
    profile_id: str,
    repository: CoachRepository = Depends(authorized_coach_repository),
) -> WorkoutPlanResponse:
    try:
        plan = repository.get_workout_plan(profile_id)
        if plan is None:
            raise CoachNotFoundError("workout_plan_not_found")
        return plan
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/workout-sessions", response_model=WorkoutSessionResponse)
def create_workout_session(
    profile_id: str,
    payload: WorkoutSessionRequest,
    repository: CoachRepository = Depends(authorized_coach_repository),
) -> WorkoutSessionResponse:
    try:
        return log_workout_session(profile_id, payload, repository=repository)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.get("/{profile_id}/progress", response_model=ProgressResponse)
def get_progress(
    profile_id: str,
    repository: CoachRepository = Depends(authorized_coach_repository),
    meals: PersistenceRepository = Depends(meal_repository),
) -> ProgressResponse:
    try:
        return progress(profile_id, repository=repository, meal_repository=meals)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.get("/{profile_id}/weekly-coach", response_model=WeeklyCoachResponse)
def get_weekly_coach(
    profile_id: str,
    repository: CoachRepository = Depends(authorized_coach_repository),
    meals: PersistenceRepository = Depends(meal_repository),
) -> WeeklyCoachResponse:
    try:
        return weekly_coach(profile_id, repository=repository, meal_repository=meals)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


def _not_found(exc: CoachNotFoundError) -> HTTPException:
    code = str(exc)
    messages = {
        "profile_not_found": "프로필을 찾을 수 없어요. 온보딩을 다시 완료해 주세요.",
        "workout_plan_not_found": "운동 계획을 찾을 수 없어요. 새 계획을 만들어 주세요.",
        "workout_day_not_found": "운동 일정을 찾을 수 없어요. 계획을 다시 확인해 주세요.",
        "workout_exercise_not_found": "운동 계획에 없는 종목이 포함되어 있어요. 계획을 다시 불러와 주세요.",
    }
    return _error(404, code, messages.get(code, "요청한 코칭 데이터를 찾을 수 없어요."), False, "not_found")


def _persistence_error() -> HTTPException:
    return _error(503, "persistence_unavailable", "코칭 데이터를 저장하지 못했어요. 다시 시도해 주세요.", True, "server")


def _error(status: int, code: str, message: str, retryable: bool, kind: str) -> HTTPException:
    detail = ApiErrorDetail(code=code, message=message, retryable=retryable, kind=kind)
    return HTTPException(status_code=status, detail=detail.model_dump())
