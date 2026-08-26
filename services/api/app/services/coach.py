from __future__ import annotations

import math
import re
from datetime import date
from uuid import uuid4

from app.coach_schemas import (
    BodyCheckInAnalysis,
    BodyCheckInRequest,
    BodyCheckInResponse,
    BodyAnalysisConsent,
    CoachDashboardResponse,
    CoachNextAction,
    CoachProfile,
    ExercisePerformance,
    ExercisePerformanceSnapshot,
    MealLogHistoryResponse,
    MealLogSummary,
    RepeatMealLogRequest,
    NutritionSnapshot,
    ProgressResponse,
    TargetAdjustmentSuggestion,
    TrainingSnapshot,
    WeightLogRequest,
    WeightLogResponse,
    WellnessCheckInRequest,
    WellnessCheckInResponse,
    WeeklyCoachEvidence,
    WeeklyCoachResponse,
    WorkoutDay,
    WorkoutExercise,
    WorkoutHistoryItem,
    WorkoutHistoryResponse,
    WorkoutPlanResponse,
    WorkoutSessionRequest,
    WorkoutSessionResponse,
)
from app.schemas import DashboardMeal, DashboardTodayResponse, MealLogRequest, NextMealGuidance, NutrientGap, NutritionTarget, OnboardingRequest, SavedImpactResponse
from app.services.coach_repository import CoachRepository, now_iso
from app.services.persistence import MealLogRecord, PersistenceRepository


class CoachNotFoundError(RuntimeError):
    pass


class CoachValidationError(ValueError):
    pass


def create_profile(
    *,
    profile_id: str,
    onboarding: OnboardingRequest,
    target: NutritionTarget,
    repository: CoachRepository,
    owner_id: str | None = None,
) -> CoachProfile:
    return repository.save_profile(
        CoachProfile(profile_id=profile_id, owner_id=owner_id, onboarding=onboarding, target=target, created_at=now_iso())
    )


def dashboard_today(
    profile_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
    logged_on: date | None = None,
) -> CoachDashboardResponse:
    profile = require_profile(profile_id, repository)
    dashboard_date = logged_on or date.today()
    meal_logs = _profile_meals_for_day(meal_repository.list_meal_logs(), profile_id, dashboard_date)
    meal_dashboard = _build_profile_meal_dashboard(profile, meal_logs, meal_repository, dashboard_date)
    consumed = meal_dashboard.consumed
    remaining = NutritionTarget(
        calories_kcal=max(0, profile.target.calories_kcal - consumed.calories_kcal),
        protein_g=max(0, profile.target.protein_g - consumed.protein_g),
        carbs_g=max(0, profile.target.carbs_g - consumed.carbs_g),
        fat_g=max(0, profile.target.fat_g - consumed.fat_g),
    )
    plan = repository.get_workout_plan(profile_id)
    sessions = repository.list_workout_sessions(profile_id)
    wellness = repository.list_wellness(profile_id)
    latest_wellness = wellness[-1] if wellness else None
    planned_sessions = plan.days_per_week if plan else 0
    completed_sessions = sum(1 for session in sessions if session.completed)
    recovery_message = _recovery_message(latest_wellness)
    next_action = _next_action(meal_logs=len(meal_logs), plan=plan, completed_sessions=completed_sessions, latest_wellness=latest_wellness)
    return CoachDashboardResponse(
        profile_id=profile_id,
        date=dashboard_date.isoformat(),
        nutrition=NutritionSnapshot(
            target=profile.target,
            consumed=consumed,
            remaining=remaining,
            protein_progress=round(consumed.protein_g / profile.target.protein_g, 2) if profile.target.protein_g else 0,
            guidance=_nutrition_guidance(remaining),
        ),
        training=TrainingSnapshot(
            planned_sessions=planned_sessions,
            completed_sessions=completed_sessions,
            next_workout_title=_next_workout_title(plan, completed_sessions),
            recovery_message=recovery_message,
        ),
        meals=meal_dashboard.meals,
        next_action=next_action,
    )


def log_weight(profile_id: str, payload: WeightLogRequest, *, repository: CoachRepository) -> WeightLogResponse:
    require_profile(profile_id, repository)
    return repository.save_weight_log(
        WeightLogResponse(id=f"weight-{uuid4()}", profile_id=profile_id, created_at=now_iso(), **payload.model_dump())
    )


def log_wellness(profile_id: str, payload: WellnessCheckInRequest, *, repository: CoachRepository) -> WellnessCheckInResponse:
    require_profile(profile_id, repository)
    return repository.save_wellness(
        WellnessCheckInResponse(id=f"wellness-{uuid4()}", profile_id=profile_id, created_at=now_iso(), **payload.model_dump())
    )


def create_body_check_in(
    profile_id: str,
    payload: BodyCheckInRequest,
    *,
    repository: CoachRepository,
    analysis: BodyCheckInAnalysis,
    consent: BodyAnalysisConsent,
) -> BodyCheckInResponse:
    require_profile(profile_id, repository)
    return repository.save_body_check_in(
        BodyCheckInResponse(
            id=f"body-{uuid4()}",
            profile_id=profile_id,
            created_at=now_iso(),
            analysis=analysis,
            consent=consent,
            **payload.model_dump(exclude={"consent_to_ai_analysis"}),
        )
    )


def generate_workout_plan(profile_id: str, *, repository: CoachRepository) -> WorkoutPlanResponse:
    profile = require_profile(profile_id, repository)
    body_check_ins = repository.list_body_check_ins(profile_id)
    latest_body_focus = body_check_ins[-1].analysis.training_focus if body_check_ins else []
    wellness = repository.list_wellness(profile_id)
    latest_wellness = wellness[-1] if wellness else None
    recovery_adjusted = _needs_recovery_adjustment(latest_wellness)
    days_per_week = {"none": 2, "1-2": 2, "3-4": 3, "5+": 5}.get(profile.onboarding.training_frequency or "none", 2)
    equipment_mode = _equipment_mode(profile.onboarding.available_equipment)
    exercise_limit = _exercise_limit(profile.onboarding.session_minutes, recovery_adjusted)
    sets_adjustment = _sets_adjustment(
        profile.onboarding.experience_level,
        profile.onboarding.session_minutes,
        recovery_adjusted,
    )
    target_rir = _target_rir(profile.onboarding.experience_level, recovery_adjusted)
    rest_seconds = _rest_seconds(profile.onboarding.experience_level, recovery_adjusted)
    body_focus_exercise = _body_focus_exercise(equipment_mode, latest_body_focus)
    day_specs = _workout_day_specs(equipment_mode)[:days_per_week]
    plan_id = f"plan-{uuid4()}"
    days: list[WorkoutDay] = []
    for index, (title, focus, exercises) in enumerate(day_specs):
        selected_exercises = list(exercises[:exercise_limit])
        if index == 0 and body_focus_exercise:
            body_focus_name = body_focus_exercise[0]
            if all(item[0] != body_focus_name for item in selected_exercises):
                selected_exercises[-1] = body_focus_exercise
        days.append(
            WorkoutDay(
                id=f"{plan_id}-day-{index + 1}",
                title=title,
                focus=f"{focus} · 회복 조절" if recovery_adjusted else focus,
                exercises=[
                    _exercise(
                        plan_id,
                        index,
                        exercise_index,
                        item,
                        sets_adjustment=sets_adjustment,
                        target_rir=target_rir,
                        rest_seconds=rest_seconds,
                    )
                    for exercise_index, item in enumerate(selected_exercises)
                ],
            )
        )

    personalization_basis = [
        f"목표: {_goal_label(profile.onboarding.goal_type)}",
        f"주당 가능 빈도: {days_per_week}회",
        f"운동 경력: {_experience_label(profile.onboarding.experience_level)}",
        f"사용 장비: {_equipment_label(profile.onboarding.available_equipment)}",
        f"세션 시간: {profile.onboarding.session_minutes}분",
    ]
    if recovery_adjusted and latest_wellness:
        personalization_basis.append(
            "최근 회복 상태에 따른 회복 조절: "
            f"에너지 {latest_wellness.energy}/5, 수면 {latest_wellness.sleep_quality}/5, 근육통 {latest_wellness.soreness}/5"
        )
    if latest_body_focus:
        personalization_basis.append(f"몸 체크인 초점: 최근 관찰 {len(latest_body_focus)}개를 운동 선택에 반영")
        personalization_basis.extend(latest_body_focus)

    progression_rule = _progression_rule(profile.onboarding.experience_level, recovery_adjusted)
    return repository.save_workout_plan(
        WorkoutPlanResponse(
            id=plan_id,
            profile_id=profile_id,
            goal_type=profile.onboarding.goal_type,
            days_per_week=days_per_week,
            session_minutes=profile.onboarding.session_minutes,
            days=days,
            personalization_basis=personalization_basis,
            progression_rule=progression_rule,
            safety_note="통증이 생기면 해당 동작을 중단하고, 부상이나 질환이 있다면 전문가에게 운동 가능 범위를 확인해 주세요.",
            generated_at=now_iso(),
        )
    )


def log_workout_session(
    profile_id: str,
    payload: WorkoutSessionRequest,
    *,
    repository: CoachRepository,
) -> WorkoutSessionResponse:
    plan = repository.get_workout_plan(profile_id)
    if plan is None or plan.id != payload.plan_id:
        raise CoachNotFoundError("workout_plan_not_found")
    workout_day = next((day for day in plan.days if day.id == payload.workout_day_id), None)
    if workout_day is None:
        raise CoachNotFoundError("workout_day_not_found")
    expected_ids = {exercise.id for exercise in workout_day.exercises}
    completed_ids = set(payload.completed_exercise_ids)
    performance_ids = {item.exercise_id for item in payload.exercise_performance}
    if not completed_ids.issubset(expected_ids) or not performance_ids.issubset(expected_ids):
        raise CoachNotFoundError("workout_exercise_not_found")
    if not performance_ids.issubset(completed_ids):
        raise CoachValidationError("workout_performance_not_completed")
    prior_sessions = repository.list_workout_sessions(profile_id)
    completed = expected_ids.issubset(completed_ids)
    if completed and payload.session_rpe >= 9:
        feedback = "계획을 마쳤지만 체감 강도가 높았어요. 다음 운동은 증량보다 회복과 동작 품질을 먼저 확인해요."
    elif completed:
        feedback = "오늘 계획을 완료했어요. 기록한 중량과 반복을 기준으로 다음 증량 여부를 판단할 수 있어요."
    else:
        feedback = "완료한 종목과 세트까지 기록했어요. 다음에는 남은 동작부터 이어가도 괜찮아요."
    saved_session = repository.save_workout_session(
        WorkoutSessionResponse(
            id=f"session-{uuid4()}",
            profile_id=profile_id,
            completed=completed,
            feedback=feedback,
            created_at=now_iso(),
            **payload.model_dump(),
        )
    )
    latest_wellness = repository.list_wellness(profile_id)
    repository.save_workout_plan(
        _update_workout_recommendations(
            plan,
            payload,
            prior_sessions=prior_sessions,
            recovery_adjusted=_needs_recovery_adjustment(latest_wellness[-1] if latest_wellness else None),
        )
    )
    return saved_session


def workout_history(profile_id: str, *, repository: CoachRepository, limit: int = 6) -> WorkoutHistoryResponse:
    require_profile(profile_id, repository)
    plan = repository.get_workout_plan(profile_id)
    day_titles = {day.id: day.title for day in plan.days} if plan else {}
    sessions = repository.list_workout_sessions(profile_id)
    items = [
        WorkoutHistoryItem(
            session_id=session.id,
            performed_on=session.performed_on,
            workout_title=day_titles.get(session.workout_day_id, "운동 세션"),
            duration_minutes=session.duration_minutes,
            session_rpe=session.session_rpe,
            completed=session.completed,
            exercise_count=len(session.completed_exercise_ids),
            total_volume_kg=round(
                sum(
                    item.sets_completed * (item.reps_completed or 0) * (item.load_kg or 0)
                    for item in session.exercise_performance
                ),
                1,
            ),
        )
        for session in reversed(sessions[-limit:])
    ]
    summary = "첫 운동을 기록하면 최근 수행과 볼륨 변화가 여기에 쌓여요."
    if items:
        summary = f"최근 {len(items)}회 운동을 기록했어요. 마지막 세션 체감 강도는 RPE {items[0].session_rpe}였어요."
    return WorkoutHistoryResponse(profile_id=profile_id, total_sessions=len(sessions), sessions=items, summary=summary)


def meal_log_history(
    profile_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
    limit: int = 30,
) -> MealLogHistoryResponse:
    require_profile(profile_id, repository)
    records = [record for record in meal_repository.list_meal_logs() if record.request.profile_id == profile_id]
    meals = [_meal_log_summary(record, meal_repository) for record in reversed(records[-limit:])]
    return MealLogHistoryResponse(profile_id=profile_id, meals=meals)


def repeat_meal_log(
    profile_id: str,
    meal_log_id: str,
    payload: RepeatMealLogRequest,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
) -> SavedImpactResponse:
    require_profile(profile_id, repository)
    source = meal_repository.get_meal_log(meal_log_id)
    if source is None or source.request.profile_id != profile_id:
        raise CoachNotFoundError("meal_log_not_found")
    repeated_request = source.request.model_copy(
        update={
            "profile_id": profile_id,
            "logged_on": payload.logged_on,
        }
    )
    repeated_id = f"meal-log-{uuid4()}"
    response = merge_profile_meal_impact(
        profile_id,
        repeated_request,
        source.response,
        repository=repository,
        meal_repository=meal_repository,
        meal_log_id=repeated_id,
    )
    meal_repository.save_meal_log(payload=repeated_request, response=response, meal_log_id=repeated_id)
    return response


def delete_meal_log(
    profile_id: str,
    meal_log_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
) -> None:
    require_profile(profile_id, repository)
    source = meal_repository.get_meal_log(meal_log_id)
    if source is None or source.request.profile_id != profile_id:
        raise CoachNotFoundError("meal_log_not_found")
    if not meal_repository.delete_meal_log(meal_log_id):
        raise CoachNotFoundError("meal_log_not_found")


def progress(
    profile_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
) -> ProgressResponse:
    profile = require_profile(profile_id, repository)
    weights = repository.list_weight_logs(profile_id)
    wellness = repository.list_wellness(profile_id)
    meal_count = len([record for record in meal_repository.list_meal_logs() if record.request.profile_id == profile_id])
    change = round(weights[-1].weight_kg - weights[0].weight_kg, 1) if len(weights) > 1 else None
    return ProgressResponse(
        profile_id=profile_id,
        latest_weight_kg=weights[-1].weight_kg if weights else None,
        weight_change_kg=change,
        latest_wellness=wellness[-1] if wellness else None,
        body_check_ins=repository.list_body_check_ins(profile_id),
        workouts_completed=sum(1 for session in repository.list_workout_sessions(profile_id) if session.completed),
        target_adjustment=_target_adjustment(profile, weights, meal_count),
    )


def weekly_coach(
    profile_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
) -> WeeklyCoachResponse:
    profile = require_profile(profile_id, repository)
    meals = [record for record in meal_repository.list_meal_logs() if record.request.profile_id == profile_id]
    sessions = repository.list_workout_sessions(profile_id)
    completed_sessions = [session for session in sessions if session.completed]
    weights = repository.list_weight_logs(profile_id)
    wellness = repository.list_wellness(profile_id)
    bodies = repository.list_body_check_ins(profile_id)
    evidence = WeeklyCoachEvidence(
        meals_logged=len(meals), workouts_completed=len(completed_sessions), weight_logs=len(weights), wellness_check_ins=len(wellness), body_check_ins=len(bodies)
    )
    plan = repository.get_workout_plan(profile_id)
    planned_sessions = plan.days_per_week if plan else {
        "none": 2,
        "1-2": 2,
        "3-4": 3,
        "5+": 5,
    }.get(profile.onboarding.training_frequency or "none", 2)
    score = _weekly_evidence_score(evidence, planned_sessions)
    latest_wellness = wellness[-1] if wellness else None
    total_records = sum(evidence.model_dump().values())
    has_baseline = len(meals) >= 3 and (len(completed_sessions) >= 1 or len(wellness) >= 2 or len(weights) >= 2)
    if total_records == 0:
        headline = "아직 주간 코칭을 만들 기록이 없어요. 먼저 기준선을 만들어요."
    elif not has_baseline:
        headline = "기록이 아직 적어, 이번 주는 패턴 평가보다 기준선을 만드는 단계예요."
    else:
        headline = "이번 주 기록에서 다음 행동을 정할 만큼의 패턴이 보이기 시작했어요."

    wins = _weekly_evidence_facts(evidence)
    focus_items = _weekly_focus_items(evidence, latest_wellness)
    next_week_actions = _weekly_next_actions(evidence, planned_sessions)
    return WeeklyCoachResponse(
        profile_id=profile_id,
        score=score,
        headline=headline,
        wins=wins,
        focus_items=focus_items,
        next_week_actions=next_week_actions,
        evidence=evidence,
        safety_note="이 코칭은 기록 기반 일반 가이드이며 의료 진단이나 치료를 대신하지 않아요.",
    )


def merge_profile_meal_impact(
    profile_id: str,
    payload: MealLogRequest,
    response: SavedImpactResponse,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
    meal_log_id: str | None = None,
) -> SavedImpactResponse:
    profile = require_profile(profile_id, repository)
    logged_on = payload.logged_on or date.today()
    profile_meals = _profile_meals_for_day(meal_repository.list_meal_logs(), profile_id, logged_on)
    pending = MealLogRecord(
        meal_log_id=meal_log_id or f"meal-log-{uuid4()}",
        analysis_job_id=payload.analysis_job_id,
        result_id=payload.result_id,
        clarification_value=payload.clarification_value,
        request=payload,
        response=response,
        created_at=now_iso(),
    )
    dashboard = _build_profile_meal_dashboard(profile, [*profile_meals, pending], meal_repository, logged_on)
    guidance = dashboard.next_meal_guidance.explanation
    return SavedImpactResponse(
        confirmation=response.confirmation,
        remaining_calories_kcal=max(0, profile.target.calories_kcal - dashboard.consumed.calories_kcal),
        next_meal_suggestion=guidance,
        dashboard=dashboard,
    )


def require_profile(profile_id: str, repository: CoachRepository) -> CoachProfile:
    profile = repository.get_profile(profile_id)
    if profile is None:
        raise CoachNotFoundError("profile_not_found")
    return profile


def _build_profile_meal_dashboard(
    profile: CoachProfile,
    meal_logs: list[MealLogRecord],
    meal_repository: PersistenceRepository,
    logged_on: date,
) -> DashboardTodayResponse:
    nutrition_by_log = [(record, _meal_nutrition(record, meal_repository)) for record in meal_logs]
    consumed = NutritionTarget(
        calories_kcal=sum(nutrition.calories_kcal for _, nutrition in nutrition_by_log),
        protein_g=sum(nutrition.protein_g for _, nutrition in nutrition_by_log),
        carbs_g=sum(nutrition.carbs_g for _, nutrition in nutrition_by_log),
        fat_g=sum(nutrition.fat_g for _, nutrition in nutrition_by_log),
    )
    protein_gap = max(0, profile.target.protein_g - consumed.protein_g)
    guidance = "단백질 목표를 채웠어요. 남은 식사는 채소와 탄수화물을 균형 있게 맞춰요."
    if protein_gap > 0:
        guidance = f"오늘 단백질이 {protein_gap}g 남았어요. 다음 식사는 지방이 낮은 단백질을 먼저 챙겨요."
    meals = []
    for record, nutrition in reversed(nutrition_by_log):
        source = record.response.dashboard.meals[0]
        meals.append(
            DashboardMeal(
                id=record.meal_log_id,
                name=source.name,
                meal_type=source.meal_type,
                calories_kcal=nutrition.calories_kcal,
                confidence_label=source.confidence_label,
                nutrition=nutrition,
            )
        )
    return DashboardTodayResponse(
        date=logged_on.isoformat(),
        target=profile.target,
        consumed=consumed,
        next_meal_guidance=NextMealGuidance(
            deficits=[NutrientGap(nutrient="protein_g", amount=protein_gap, severity="high" if protein_gap > 40 else "medium")] if protein_gap else [],
            excesses=[],
            menu_type_recommendations=["닭가슴살 또는 살코기", "두부와 계란", "기름 적은 생선구이"],
            explanation=guidance,
        ),
        meals=meals,
    )


def _meal_nutrition(record: MealLogRecord, meal_repository: PersistenceRepository) -> NutritionTarget:
    saved_meal = record.response.dashboard.meals[0]
    if saved_meal.nutrition:
        return saved_meal.nutrition
    override = record.request.nutrition_override
    if override:
        return NutritionTarget(
            calories_kcal=override.calories_kcal,
            protein_g=override.protein_g,
            carbs_g=override.carbs_g,
            fat_g=override.fat_g,
        )
    job = meal_repository.get_analysis_job(record.analysis_job_id)
    summary = job.response.result.summary if job and job.response and job.response.result else None
    if summary:
        return NutritionTarget(
            calories_kcal=summary.calories_kcal,
            protein_g=summary.protein_g,
            carbs_g=summary.carbs_g,
            fat_g=summary.fat_g,
        )
    source = record.response.dashboard
    meal = source.meals[0]
    return NutritionTarget(
        calories_kcal=meal.calories_kcal,
        protein_g=source.consumed.protein_g,
        carbs_g=source.consumed.carbs_g,
        fat_g=source.consumed.fat_g,
    )


def _meal_log_summary(record: MealLogRecord, meal_repository: PersistenceRepository) -> MealLogSummary:
    source = record.response.dashboard.meals[0]
    logged_on = record.request.logged_on.isoformat() if record.request.logged_on else record.response.dashboard.date
    return MealLogSummary(
        id=record.meal_log_id,
        profile_id=record.request.profile_id or "",
        logged_on=logged_on,
        name=source.name,
        meal_type=source.meal_type,
        nutrition=_meal_nutrition(record, meal_repository),
        confidence_label=source.confidence_label,
        created_at=record.created_at,
    )


def _profile_meals_for_day(meal_logs: list[MealLogRecord], profile_id: str, logged_on: date) -> list[MealLogRecord]:
    expected_date = logged_on.isoformat()
    return [
        record
        for record in meal_logs
        if record.request.profile_id == profile_id
        and (record.request.logged_on.isoformat() if record.request.logged_on else record.response.dashboard.date) == expected_date
    ]


def _nutrition_guidance(remaining: NutritionTarget) -> str:
    if remaining.protein_g > 40:
        return f"오늘 단백질이 {remaining.protein_g}g 남았어요. 다음 식사는 살코기, 생선, 두부 같은 저지방 단백질을 먼저 챙겨요."
    return "단백질 목표에 가까워요. 남은 식사는 채소와 탄수화물을 균형 있게 맞춰요."


def _target_adjustment(profile: CoachProfile, weights: list[WeightLogResponse], meal_count: int) -> TargetAdjustmentSuggestion:
    if len(weights) < 2 or meal_count < 5:
        return TargetAdjustmentSuggestion(
            status="insufficient_data",
            calorie_delta=0,
            proposed_calories_kcal=None,
            reason=f"목표 조정 전 식사 5회와 체중 2회가 필요해요. 현재 식사 {meal_count}회, 체중 {len(weights)}회예요.",
            requires_confirmation=False,
        )

    weight_change = weights[-1].weight_kg - weights[0].weight_kg
    delta = 0
    reason = "현재 기록 흐름은 목표와 크게 어긋나지 않아 기존 칼로리를 유지해요."
    if profile.onboarding.goal_type == "lose" and weight_change > -0.2:
        delta = -100
        reason = "감량 목표에 비해 체중 흐름이 정체되어 하루 목표를 100kcal 낮추는 안을 제안해요."
    elif profile.onboarding.goal_type == "lose" and weight_change < -1.0:
        delta = 100
        reason = "체중 변화가 빠른 편이라 회복과 지속성을 위해 하루 목표를 100kcal 높이는 안을 제안해요."
    elif profile.onboarding.goal_type == "gain" and weight_change < 0.2:
        delta = 100
        reason = "증량 목표에 비해 체중 흐름이 정체되어 하루 목표를 100kcal 높이는 안을 제안해요."

    if delta == 0:
        return TargetAdjustmentSuggestion(
            status="no_change",
            calorie_delta=0,
            proposed_calories_kcal=profile.target.calories_kcal,
            reason=reason,
            requires_confirmation=False,
        )

    proposed = min(4500, max(1400, profile.target.calories_kcal + delta))
    actual_delta = proposed - profile.target.calories_kcal
    return TargetAdjustmentSuggestion(
        status="suggested" if actual_delta else "no_change",
        calorie_delta=actual_delta,
        proposed_calories_kcal=proposed,
        reason=reason,
        requires_confirmation=bool(actual_delta),
    )


def _recovery_message(wellness: WellnessCheckInResponse | None) -> str:
    if wellness and (wellness.soreness >= 4 or wellness.sleep_quality <= 2):
        return "회복 신호가 낮아요. 오늘은 강도를 낮추거나 휴식을 우선해요."
    return "현재 기록상 계획된 운동을 진행해도 괜찮은 흐름이에요."


def _next_action(*, meal_logs: int, plan: WorkoutPlanResponse | None, completed_sessions: int, latest_wellness: WellnessCheckInResponse | None) -> CoachNextAction:
    if latest_wellness and (latest_wellness.soreness >= 4 or latest_wellness.sleep_quality <= 2):
        return CoachNextAction(type="recover", title="오늘은 회복을 먼저", detail="가벼운 걷기와 충분한 수면을 권장해요.")
    if meal_logs == 0:
        return CoachNextAction(type="log_meal", title="첫 식사를 기록해요", detail="사진 한 장이면 오늘 단백질 잔여량을 계산할 수 있어요.")
    if plan and completed_sessions < plan.days_per_week:
        return CoachNextAction(type="start_workout", title=_next_workout_title(plan, completed_sessions) or "다음 운동", detail="세트와 반복 수를 확인하고 시작해요.")
    return CoachNextAction(type="check_in", title="오늘 상태를 남겨요", detail="체중과 회복 상태를 기록하면 다음 주 조언이 더 구체적이에요.")


def _next_workout_title(plan: WorkoutPlanResponse | None, completed_sessions: int) -> str | None:
    if not plan or not plan.days:
        return None
    return plan.days[completed_sessions % len(plan.days)].title


def _goal_label(goal_type: str) -> str:
    return {
        "lose": "체지방 감량",
        "maintain": "현재 상태 유지",
        "gain": "근육량 증가",
        "recomp": "체성분 개선",
    }.get(goal_type, "개인 목표")


def _exercise(
    plan_id: str,
    day_index: int,
    exercise_index: int,
    item: tuple[str, int, str, str],
    *,
    sets_adjustment: int,
    target_rir: int,
    rest_seconds: int,
) -> WorkoutExercise:
    name, sets, reps, rationale = item
    return WorkoutExercise(
        id=f"{plan_id}-exercise-{day_index + 1}-{exercise_index + 1}",
        name=name,
        sets=min(6, max(2, sets + sets_adjustment)),
        reps=reps,
        target_rir=target_rir,
        rest_seconds=rest_seconds,
        rationale=rationale,
    )


def _workout_day_specs(equipment_mode: str) -> list[tuple[str, str, list[tuple[str, int, str, str]]]]:
    if equipment_mode == "bodyweight":
        return [
            ("전신 A", "무릎 우세와 수평 밀기", [("템포 스쿼트", 3, "8-12회", "천천히 내려가 하체 동작 품질 확보"), ("인클라인 푸시업", 3, "8-15회", "난도를 조절할 수 있는 상체 밀기"), ("글루트 브리지", 3, "10-15회", "둔근과 골반 안정"), ("데드버그", 2, "8-10회/측", "허리에 부담을 낮춘 몸통 안정"), ("카프 레이즈", 2, "12-20회", "종아리 기초 볼륨")]),
            ("전신 B", "한쪽 하체와 등 뒤쪽", [("리버스 런지", 3, "8-12회/측", "좌우 하체 균형"), ("파이크 푸시업", 3, "6-12회", "맨몸 수직 밀기"), ("프론 Y-T 레이즈", 3, "8-12회", "등 상부와 견갑 움직임"), ("사이드 플랭크", 2, "20-40초/측", "측면 몸통 안정"), ("싱글 레그 브리지", 2, "8-12회/측", "둔근 좌우 조절")]),
            ("전신 C", "하체 볼륨과 밀기 조절", [("스플릿 스쿼트", 3, "8-12회/측", "기구 없이 하체 자극 확보"), ("푸시업", 3, "여유 2-3회 남기기", "상체 밀기 반복"), ("힙 힌지 연습", 3, "10-15회", "등을 중립으로 유지하는 힌지 학습"), ("버드독", 2, "8-10회/측", "몸통과 골반 제어"), ("월싯", 2, "30-45초", "하체 등척성 지구력")]),
            ("상체 보완", "어깨와 견갑의 낮은 피로 볼륨", [("니 푸시업", 3, "10-15회", "부담을 낮춘 상체 밀기"), ("리버스 스노우 엔젤", 3, "10-15회", "후면 어깨와 등 상부"), ("스캡 푸시업", 3, "10-15회", "견갑 움직임 연습"), ("할로우 홀드", 2, "20-40초", "앞쪽 몸통 안정"), ("숄더 탭", 2, "8-12회/측", "어깨와 몸통 협응")]),
            ("기술과 회복", "낮은 피로의 전신 반복", [("박스 스쿼트", 3, "10-15회", "깊이를 통제하는 스쿼트"), ("월 푸시업", 3, "12-20회", "낮은 부담의 밀기"), ("프론 W 레이즈", 3, "10-15회", "등 상부 동작 품질"), ("글루트 브리지 홀드", 2, "20-40초", "둔근 등척성 제어"), ("호흡 데드버그", 2, "6-8회/측", "호흡과 몸통 안정")]),
        ]
    if equipment_mode == "dumbbells":
        return [
            ("전신 A", "스쿼트와 수평 밀기", [("고블릿 스쿼트", 3, "8-12회", "덤벨 한 개로 안전하게 하체 훈련"), ("덤벨 플로어 프레스", 3, "8-12회", "바닥에서 범위를 통제하는 가슴 운동"), ("원암 덤벨 로우", 3, "8-12회/측", "등 좌우 균형"), ("덤벨 루마니안 데드리프트", 2, "8-12회", "둔근과 햄스트링"), ("데드버그", 2, "8-10회/측", "몸통 안정")]),
            ("전신 B", "힌지와 수직 밀기", [("덤벨 루마니안 데드리프트", 3, "8-12회", "둔근과 햄스트링 강화"), ("덤벨 숄더프레스", 3, "8-12회", "어깨와 상체 밀기"), ("리버스 런지", 3, "8-10회/측", "좌우 하체 균형"), ("덤벨 풀오버", 2, "10-15회", "등과 몸통 협응"), ("수트케이스 홀드", 2, "30-45초/측", "측면 몸통 안정")]),
            ("전신 C", "하체 볼륨과 상체 균형", [("덤벨 스플릿 스쿼트", 3, "8-12회/측", "하체 좌우 볼륨"), ("인클라인 덤벨프레스", 3, "8-12회", "상부 가슴과 어깨"), ("체스트 서포티드 덤벨 로우", 3, "8-12회", "허리 부담을 낮춘 등 운동"), ("덤벨 레터럴 레이즈", 2, "12-20회", "측면 어깨 보완"), ("덤벨 카프 레이즈", 2, "12-20회", "종아리 볼륨")]),
            ("상체 보완", "등과 팔의 낮은 피로 볼륨", [("덤벨 플로어 프레스", 3, "10-15회", "통제된 상체 밀기"), ("덤벨 리버스 플라이", 3, "12-20회", "후면 어깨와 등 상부"), ("덤벨 컬", 2, "10-15회", "팔 굽힘 보완"), ("덤벨 트라이셉스 익스텐션", 2, "10-15회", "팔 폄 보완"), ("파머 캐리", 2, "30-60초", "그립과 몸통 안정")]),
            ("기술과 회복", "낮은 피로의 전신 반복", [("덤벨 박스 스쿼트", 3, "10-15회", "깊이를 통제하는 하체 운동"), ("뉴트럴 그립 플로어 프레스", 3, "10-15회", "어깨 부담을 낮춘 밀기"), ("덤벨 로우 정지 반복", 3, "8-12회/측", "등 수축 위치 제어"), ("덤벨 힙 브리지", 2, "10-15회", "둔근 반복 품질"), ("수트케이스 캐리", 2, "30-45초/측", "몸통 안정")]),
        ]
    return [
        ("전신 A", "스쿼트와 수평 밀기", [("스쿼트", 3, "6-10회", "하체 힘과 근육의 기본 동작"), ("벤치프레스", 3, "6-10회", "가슴과 삼두의 기본 밀기"), ("시티드 로우", 3, "8-12회", "등과 후면 어깨 균형"), ("플랭크", 2, "30-45초", "몸통 안정성"), ("레그 컬", 2, "10-15회", "햄스트링 보완")]),
        ("전신 B", "힌지와 수직 당기기", [("루마니안 데드리프트", 3, "6-10회", "둔근과 햄스트링 강화"), ("랫풀다운", 3, "8-12회", "등 너비와 견갑 움직임"), ("덤벨 숄더프레스", 3, "8-12회", "어깨와 상체 밀기"), ("불가리안 스플릿 스쿼트", 2, "8-10회/측", "좌우 하체 균형"), ("팔로프 프레스", 2, "10-12회/측", "회전에 저항하는 몸통 안정")]),
        ("전신 C", "하체 볼륨과 상체 균형", [("레그프레스", 3, "10-15회", "안정적인 하체 볼륨"), ("인클라인 덤벨프레스", 3, "8-12회", "상부 가슴과 어깨"), ("케이블 로우", 3, "8-12회", "등 중앙부와 자세 유지"), ("레터럴 레이즈", 2, "12-20회", "측면 어깨 보완"), ("스탠딩 카프 레이즈", 2, "12-20회", "종아리 볼륨")]),
        ("상체 보완", "약점 보완과 낮은 피로", [("푸시업", 3, "여유 2회 남기기", "상체 밀기 반복"), ("케이블 하이 로우", 3, "10-15회", "등 상부와 견갑 제어"), ("케이블 컬", 2, "10-15회", "팔 굽힘 보완"), ("트라이셉스 프레스다운", 2, "10-15회", "팔 폄 보완"), ("케이블 외회전", 2, "12-20회", "어깨 회전근 보완")]),
        ("기술과 회복", "낮은 피로의 전신 반복", [("핵 스쿼트", 3, "10-15회", "안정적인 하체 반복"), ("체스트 프레스 머신", 3, "10-15회", "통제된 상체 밀기"), ("체스트 서포티드 로우", 3, "10-15회", "허리 부담을 낮춘 등 운동"), ("힙 쓰러스트", 2, "8-12회", "둔근 수축 제어"), ("케이블 데드버그", 2, "8-10회/측", "몸통 안정")]),
    ]


def _equipment_mode(available_equipment: list[str]) -> str:
    if "gym" in available_equipment:
        return "gym"
    if "dumbbells" in available_equipment:
        return "dumbbells"
    return "bodyweight"


def _equipment_label(available_equipment: list[str]) -> str:
    labels = {"bodyweight": "맨몸", "dumbbells": "덤벨", "gym": "헬스장"}
    return ", ".join(labels[item] for item in available_equipment)


def _experience_label(experience_level: str) -> str:
    return {"beginner": "입문", "intermediate": "중급", "advanced": "숙련"}.get(experience_level, "입문")


def _needs_recovery_adjustment(wellness: WellnessCheckInResponse | None) -> bool:
    return bool(wellness and (wellness.energy <= 2 or wellness.sleep_quality <= 2 or wellness.soreness >= 4))


def _exercise_limit(session_minutes: int, recovery_adjusted: bool) -> int:
    limit = 3 if session_minutes <= 35 else 4 if session_minutes < 80 else 5
    return max(3, limit - 1) if recovery_adjusted else limit


def _sets_adjustment(experience_level: str, session_minutes: int, recovery_adjusted: bool) -> int:
    adjustment = {"beginner": -1, "intermediate": 0, "advanced": 1}.get(experience_level, -1)
    if session_minutes <= 35:
        adjustment -= 1
    elif session_minutes >= 80:
        adjustment += 1
    if recovery_adjusted:
        adjustment -= 1
    return adjustment


def _target_rir(experience_level: str, recovery_adjusted: bool) -> int:
    target = {"beginner": 3, "intermediate": 2, "advanced": 1}.get(experience_level, 3)
    return min(4, target + 1) if recovery_adjusted else target


def _rest_seconds(experience_level: str, recovery_adjusted: bool) -> int:
    rest = {"beginner": 90, "intermediate": 120, "advanced": 150}.get(experience_level, 90)
    return min(180, rest + 30) if recovery_adjusted else rest


def _progression_rule(experience_level: str, recovery_adjusted: bool) -> str:
    if recovery_adjusted:
        return "최근 회복 기록이 낮아 이번 계획에서는 증량하지 않아요. 회복 신호가 돌아온 뒤 목표 반복 상단을 여유 있게 달성하면 중량을 2.5% 이내로 올려요."
    if experience_level == "beginner":
        return "같은 동작을 2회 연속 안정적으로 마치고 목표 반복 상단에서 3회 정도 여유가 남으면 가장 작은 단위로 중량을 올려요."
    if experience_level == "advanced":
        return "모든 세트에서 목표 반복 상단을 여유 1회로 달성하면 다음 운동에서 중량을 2.5-5% 올리고, 수행이 무너지면 이전 중량을 유지해요."
    return "모든 세트에서 목표 반복 상단을 여유 2회로 달성하면 다음 운동에서 중량을 2.5-5% 올려요."


def _update_workout_recommendations(
    plan: WorkoutPlanResponse,
    payload: WorkoutSessionRequest,
    *,
    prior_sessions: list[WorkoutSessionResponse],
    recovery_adjusted: bool,
) -> WorkoutPlanResponse:
    performance_by_id = {item.exercise_id: item for item in payload.exercise_performance}
    updated_days: list[WorkoutDay] = []
    for day in plan.days:
        if day.id != payload.workout_day_id:
            updated_days.append(day)
            continue
        exercises: list[WorkoutExercise] = []
        for exercise in day.exercises:
            performance = performance_by_id.get(exercise.id)
            if performance is None:
                exercises.append(exercise)
                continue
            action, load, reps, reason = _next_exercise_target(
                exercise,
                performance,
                session_rpe=payload.session_rpe,
                prior_sessions=prior_sessions,
                recovery_adjusted=recovery_adjusted,
            )
            exercises.append(
                exercise.model_copy(
                    update={
                        "last_performance": ExercisePerformanceSnapshot(
                            sets_completed=performance.sets_completed,
                            reps_completed=performance.reps_completed,
                            load_kg=performance.load_kg,
                            effort=performance.effort,
                            performed_on=payload.performed_on,
                        ),
                        "progression_action": action,
                        "recommended_load_kg": load,
                        "recommended_reps": reps,
                        "recommendation_reason": reason,
                    }
                )
            )
        updated_days.append(day.model_copy(update={"exercises": exercises}))
    return plan.model_copy(update={"days": updated_days})


def _next_exercise_target(
    exercise: WorkoutExercise,
    performance: ExercisePerformance,
    *,
    session_rpe: int,
    prior_sessions: list[WorkoutSessionResponse],
    recovery_adjusted: bool,
) -> tuple[str, float | None, int | None, str]:
    load = performance.load_kg
    reps = performance.reps_completed
    rep_range = _parse_rep_range(exercise.reps)
    if load is None or load <= 0 or reps is None or rep_range is None:
        return (
            "collect_baseline",
            load,
            reps,
            "중량과 반복을 한 번 더 기록하면 수행 범위에 맞춘 다음 목표를 계산해요.",
        )

    lower, upper = rep_range
    if recovery_adjusted:
        return (
            "hold",
            load,
            min(upper, max(lower, reps)),
            "최근 회복 기록이 낮아 이번에는 증량하지 않고 같은 강도에서 동작 품질을 확인해요.",
        )

    if performance.effort == "hard" or session_rpe >= 9 or reps < lower:
        if performance.effort == "hard" and reps < lower:
            increment = _load_increment_kg(exercise.name)
            reduction = _round_up_to_increment(max(increment, load * 0.05), increment)
            reduced = max(0, round(load - reduction, 1))
            return (
                "reduce",
                reduced,
                lower,
                "목표 반복에 못 미쳤고 체감 난도가 높아 다음 세션은 가능한 중량 한 단계만 낮춰요.",
            )
        return (
            "hold",
            load,
            max(lower, min(upper, reps)),
            "오늘 체감 강도가 높아 중량을 유지하고 같은 범위를 더 안정적으로 완성해요.",
        )

    reached_top = performance.sets_completed >= exercise.sets and reps >= upper
    prior_top = _has_prior_top_set(exercise.id, upper, prior_sessions)
    if reached_top and (performance.effort == "easy" or prior_top):
        increment = _load_increment_kg(exercise.name)
        increase = _round_up_to_increment(max(increment, load * 0.025), increment)
        if increase / load > 0.15:
            return (
                "hold",
                load,
                upper,
                "사용 가능한 다음 중량의 증가 폭이 커서 이번에는 같은 중량과 반복을 한 번 더 확인해요.",
            )
        increased = round(load + increase, 1)
        return (
            "increase",
            increased,
            lower,
            "목표 반복 상단을 안정적으로 달성해 다음 세션은 가장 작은 단계로 증량해요.",
        )

    next_reps = min(upper, max(lower, reps + 1))
    return (
        "hold",
        load,
        next_reps,
        "중량은 유지하고 다음 세션에서 같은 동작의 반복을 1회 늘려요.",
    )


def _parse_rep_range(value: str) -> tuple[int, int] | None:
    match = re.match(r"^\s*(\d+)(?:-(\d+))?회", value)
    if match is None:
        return None
    lower = int(match.group(1))
    upper = int(match.group(2) or match.group(1))
    return lower, upper


def _has_prior_top_set(exercise_id: str, upper_reps: int, sessions: list[WorkoutSessionResponse]) -> bool:
    for session in reversed(sessions):
        for item in session.exercise_performance:
            if item.exercise_id == exercise_id:
                return bool(item.reps_completed is not None and item.reps_completed >= upper_reps and item.effort != "hard")
    return False


def _load_increment_kg(exercise_name: str) -> float:
    if "덤벨" in exercise_name:
        return 2.0
    if any(keyword in exercise_name for keyword in ("스쿼트", "벤치프레스", "데드리프트", "프레스", "로우", "풀다운", "레그")):
        return 2.5
    return 1.0


def _round_up_to_increment(value: float, increment: float) -> float:
    return round(math.ceil(value / increment) * increment, 1)


def _body_focus_exercise(equipment_mode: str, body_focus: list[str]) -> tuple[str, int, str, str] | None:
    focus_text = " ".join(body_focus)
    if not focus_text:
        return None
    if any(keyword in focus_text for keyword in ("등", "후면", "견갑")):
        return {
            "bodyweight": ("프론 Y-T 레이즈", 2, "8-12회", "최근 몸 체크인의 등·후면 어깨 훈련 초점 반영"),
            "dumbbells": ("덤벨 리버스 플라이", 2, "12-20회", "최근 몸 체크인의 등·후면 어깨 훈련 초점 반영"),
            "gym": ("리버스 펙덱", 2, "12-20회", "최근 몸 체크인의 등·후면 어깨 훈련 초점 반영"),
        }[equipment_mode]
    if any(keyword in focus_text for keyword in ("하체", "스쿼트", "둔근")):
        return {
            "bodyweight": ("스플릿 스쿼트", 2, "8-12회/측", "최근 몸 체크인의 하체 훈련 초점 반영"),
            "dumbbells": ("덤벨 스플릿 스쿼트", 2, "8-12회/측", "최근 몸 체크인의 하체 훈련 초점 반영"),
            "gym": ("레그프레스", 2, "10-15회", "최근 몸 체크인의 하체 훈련 초점 반영"),
        }[equipment_mode]
    if any(keyword in focus_text for keyword in ("코어", "몸통", "안정")):
        return {
            "bodyweight": ("데드버그", 2, "8-10회/측", "최근 몸 체크인의 몸통 안정 초점 반영"),
            "dumbbells": ("수트케이스 홀드", 2, "30-45초/측", "최근 몸 체크인의 몸통 안정 초점 반영"),
            "gym": ("팔로프 프레스", 2, "10-12회/측", "최근 몸 체크인의 몸통 안정 초점 반영"),
        }[equipment_mode]
    return None


def _weekly_evidence_score(evidence: WeeklyCoachEvidence, planned_sessions: int) -> int:
    meal_points = min(40, evidence.meals_logged * 8)
    workout_points = round(30 * min(evidence.workouts_completed, planned_sessions) / max(1, planned_sessions))
    weight_points = min(10, evidence.weight_logs * 5)
    wellness_points = min(15, evidence.wellness_check_ins * 5)
    body_points = min(5, evidence.body_check_ins * 5)
    return min(100, meal_points + workout_points + weight_points + wellness_points + body_points)


def _weekly_evidence_facts(evidence: WeeklyCoachEvidence) -> list[str]:
    facts: list[str] = []
    if evidence.meals_logged:
        facts.append(f"식사 기록 {evidence.meals_logged}회를 확인했어요.")
    if evidence.workouts_completed:
        facts.append(f"운동 기록 {evidence.workouts_completed}회를 확인했어요.")
    if evidence.weight_logs:
        facts.append(f"체중 기록 {evidence.weight_logs}회를 확인했어요.")
    if evidence.wellness_check_ins:
        facts.append(f"회복 상태 기록 {evidence.wellness_check_ins}회를 확인했어요.")
    if evidence.body_check_ins:
        facts.append(f"몸 변화 사진 기록 {evidence.body_check_ins}회를 확인했어요.")
    return facts


def _weekly_focus_items(
    evidence: WeeklyCoachEvidence,
    latest_wellness: WellnessCheckInResponse | None,
) -> list[str]:
    items: list[str] = []
    if evidence.meals_logged < 3:
        items.append("식사 기록이 3회 미만이라 단백질 섭취 패턴은 아직 판단하지 않아요.")
    else:
        items.append("식사 기록을 이어가며 단백질이 부족해지는 시간대를 확인해요.")
    if evidence.workouts_completed == 0:
        items.append("운동 수행 기록이 없어 운동 강도나 진행 속도는 아직 평가하지 않아요.")
    if latest_wellness and (latest_wellness.soreness >= 4 or latest_wellness.sleep_quality <= 2 or latest_wellness.energy <= 2):
        items.append("최근 회복 신호가 낮아 중량보다 수면과 동작 품질을 우선해요.")
    return items[:3]


def _weekly_next_actions(evidence: WeeklyCoachEvidence, planned_sessions: int) -> list[str]:
    actions: list[str] = []
    if evidence.meals_logged < 3:
        actions.append(f"식사 사진 {3 - evidence.meals_logged}회 더 기록하기")
    if evidence.workouts_completed < planned_sessions:
        actions.append(f"계획한 운동 중 {planned_sessions - evidence.workouts_completed}회 실행하고 기록하기")
    if evidence.weight_logs < 2:
        actions.append(f"같은 조건으로 체중 {2 - evidence.weight_logs}회 더 기록하기")
    if evidence.wellness_check_ins < 2:
        actions.append(f"수면·에너지·근육통 상태 {2 - evidence.wellness_check_ins}회 더 남기기")
    return actions[:3]
