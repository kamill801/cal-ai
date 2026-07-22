from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.coach_schemas import (
    BodyCheckInRequest,
    BodyCheckInResponse,
    CoachDashboardResponse,
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
from app.services.persistence import PersistenceError, PersistenceRepository, get_persistence_repository


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


@router.get("/{profile_id}/dashboard/today", response_model=CoachDashboardResponse)
def get_dashboard(
    profile_id: str,
    logged_on: date | None = None,
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
    uploads: PersistenceRepository = Depends(meal_repository),
) -> BodyCheckInResponse:
    try:
        upload = uploads.get_image_upload(payload.image_upload_id)
        if upload is None:
            raise _error(404, "image_upload_not_found", "업로드된 이미지를 찾을 수 없어요.", False, "not_found")
        if upload.upload_status != "ready":
            raise _error(400, "image_upload_not_ready", "이미지 업로드가 아직 완료되지 않았어요.", True, "validation")
        return create_body_check_in(profile_id, payload, repository=repository)
    except CoachNotFoundError as exc:
        raise _not_found(exc) from exc
    except PersistenceError as exc:
        raise _persistence_error() from exc


@router.post("/{profile_id}/workout-plans/generate", response_model=WorkoutPlanResponse)
def create_workout_plan(
    profile_id: str,
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    repository: CoachRepository = Depends(coach_repository),
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
    }
    return _error(404, code, messages.get(code, "요청한 코칭 데이터를 찾을 수 없어요."), False, "not_found")


def _persistence_error() -> HTTPException:
    return _error(503, "persistence_unavailable", "코칭 데이터를 저장하지 못했어요. 다시 시도해 주세요.", True, "server")


def _error(status: int, code: str, message: str, retryable: bool, kind: str) -> HTTPException:
    detail = ApiErrorDetail(code=code, message=message, retryable=retryable, kind=kind)
    return HTTPException(status_code=status, detail=detail.model_dump())
