from __future__ import annotations

from datetime import date
from uuid import uuid4

from app.coach_schemas import (
    BodyCheckInAnalysis,
    BodyCheckInRequest,
    BodyCheckInResponse,
    BodyObservation,
    CoachDashboardResponse,
    CoachNextAction,
    CoachProfile,
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
    WorkoutPlanResponse,
    WorkoutSessionRequest,
    WorkoutSessionResponse,
)
from app.schemas import DashboardMeal, DashboardTodayResponse, MealLogRequest, NextMealGuidance, NutrientGap, NutritionTarget, OnboardingRequest, SavedImpactResponse
from app.services.coach_repository import CoachRepository, now_iso
from app.services.persistence import MealLogRecord, PersistenceRepository


class CoachNotFoundError(RuntimeError):
    pass


def create_profile(
    *,
    profile_id: str,
    onboarding: OnboardingRequest,
    target: NutritionTarget,
    repository: CoachRepository,
) -> CoachProfile:
    return repository.save_profile(
        CoachProfile(profile_id=profile_id, onboarding=onboarding, target=target, created_at=now_iso())
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
    latest_dashboard = _latest_accumulated_dashboard(meal_logs)
    consumed = latest_dashboard.consumed if latest_dashboard else NutritionTarget(calories_kcal=0, protein_g=0, carbs_g=0, fat_g=0)
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
    completed_sessions = len(sessions)
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
) -> BodyCheckInResponse:
    require_profile(profile_id, repository)
    previous = repository.list_body_check_ins(profile_id)
    comparison_note = "첫 체크인이에요. 같은 조명과 거리로 기록하면 주간 변화를 비교하기 쉬워요."
    if previous:
        comparison_note = "이전 기록과 함께 보되, 사진 차이는 조명과 자세의 영향도 커서 주간 추세로 확인해요."
    analysis = BodyCheckInAnalysis(
        provider="mock",
        confidence="limited",
        capture_quality="good",
        observations=[
            BodyObservation(title="기록 조건", detail="전신이 프레임 안에 들어와 비교용 기록으로 사용할 수 있어요."),
            BodyObservation(title="해석 범위", detail="사진에서 보이는 자세와 윤곽만 참고하고 건강 상태를 판단하지 않아요."),
        ],
        training_focus=["등과 후면 어깨를 주 2회 균형 있게 훈련", "하체 기본 동작의 반복 품질 유지"],
        comparison_note=comparison_note,
        safety_note="사진만으로 체지방률, 질환, 통증 원인을 판단하지 않아요. 통증이 있으면 전문가와 상의해 주세요.",
    )
    return repository.save_body_check_in(
        BodyCheckInResponse(
            id=f"body-{uuid4()}",
            profile_id=profile_id,
            created_at=now_iso(),
            analysis=analysis,
            **payload.model_dump(),
        )
    )


def generate_workout_plan(profile_id: str, *, repository: CoachRepository) -> WorkoutPlanResponse:
    profile = require_profile(profile_id, repository)
    body_check_ins = repository.list_body_check_ins(profile_id)
    latest_body_focus = body_check_ins[-1].analysis.training_focus if body_check_ins else []
    days_per_week = {"none": 2, "1-2": 2, "3-4": 3, "5+": 4}.get(profile.onboarding.training_frequency or "none", 2)
    day_specs = _workout_day_specs()[:days_per_week]
    plan_id = f"plan-{uuid4()}"
    days = [
        WorkoutDay(
            id=f"{plan_id}-day-{index + 1}",
            title=title,
            focus=focus,
            exercises=[_exercise(plan_id, index, exercise_index, item) for exercise_index, item in enumerate(exercises)],
        )
        for index, (title, focus, exercises) in enumerate(day_specs)
    ]
    return repository.save_workout_plan(
        WorkoutPlanResponse(
            id=plan_id,
            profile_id=profile_id,
            goal_type=profile.onboarding.goal_type,
            days_per_week=days_per_week,
            session_minutes=profile.onboarding.session_minutes,
            days=days,
            personalization_basis=[
                f"목표: {_goal_label(profile.onboarding.goal_type)}",
                f"주당 가능 빈도: {days_per_week}회",
                *latest_body_focus,
            ],
            progression_rule="모든 세트에서 목표 반복 상단을 여유 2회로 달성하면 다음 운동에서 중량을 2.5-5% 올려요.",
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
    completed = expected_ids.issubset(set(payload.completed_exercise_ids))
    feedback = "오늘 계획을 완료했어요. 다음 운동 전까지 단백질과 수면을 챙겨주세요." if completed else "일부만 해도 기록은 남아요. 다음에는 남은 동작부터 이어가도 괜찮아요."
    return repository.save_workout_session(
        WorkoutSessionResponse(
            id=f"session-{uuid4()}",
            profile_id=profile_id,
            completed=completed,
            feedback=feedback,
            created_at=now_iso(),
            **payload.model_dump(),
        )
    )


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
        workouts_completed=len(repository.list_workout_sessions(profile_id)),
        target_adjustment=_target_adjustment(profile, weights, meal_count),
    )


def weekly_coach(
    profile_id: str,
    *,
    repository: CoachRepository,
    meal_repository: PersistenceRepository,
) -> WeeklyCoachResponse:
    require_profile(profile_id, repository)
    meals = [record for record in meal_repository.list_meal_logs() if record.request.profile_id == profile_id]
    sessions = repository.list_workout_sessions(profile_id)
    weights = repository.list_weight_logs(profile_id)
    wellness = repository.list_wellness(profile_id)
    bodies = repository.list_body_check_ins(profile_id)
    evidence = WeeklyCoachEvidence(
        meals_logged=len(meals), workouts_completed=len(sessions), weight_logs=len(weights), wellness_check_ins=len(wellness), body_check_ins=len(bodies)
    )
    score = min(100, 35 + len(meals) * 5 + len(sessions) * 15 + len(weights) * 5 + len(wellness) * 5 + len(bodies) * 5)
    latest_wellness = wellness[-1] if wellness else None
    focus_items = ["식사 사진 기록을 3일 이상 남겨 단백질 패턴을 확인해요."] if len(meals) < 3 else ["단백질 섭취를 하루 전체에 나누어 유지해요."]
    if latest_wellness and latest_wellness.soreness >= 4:
        focus_items.append("근육통이 높은 날은 중량보다 회복과 동작 품질을 우선해요.")
    wins = ["운동 기록을 시작해 실행 데이터를 만들었어요."] if sessions else ["목표와 운동 가능 조건을 설정했어요."]
    return WeeklyCoachResponse(
        profile_id=profile_id,
        score=score,
        headline="이번 주는 기록의 기반을 만들고, 다음 행동을 더 구체적으로 정한 주예요.",
        wins=wins,
        focus_items=focus_items,
        next_week_actions=["운동 계획을 일정에 먼저 배치하기", "운동 후 식사에서 단백질 25-40g 챙기기", "주 2회 같은 조건으로 체중 기록하기"],
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
) -> SavedImpactResponse:
    profile = require_profile(profile_id, repository)
    logged_on = payload.logged_on or date.today()
    profile_meals = _profile_meals_for_day(meal_repository.list_meal_logs(), profile_id, logged_on)
    previous_dashboard = _latest_accumulated_dashboard(profile_meals)
    previous_consumed = previous_dashboard.consumed if previous_dashboard else NutritionTarget(calories_kcal=0, protein_g=0, carbs_g=0, fat_g=0)
    latest_meal = response.dashboard.meals[0]
    job = meal_repository.get_analysis_job(payload.analysis_job_id)
    summary = job.response.result.summary if job and job.response and job.response.result else None
    meal_macros = NutritionTarget(
        calories_kcal=summary.calories_kcal if summary else latest_meal.calories_kcal,
        protein_g=summary.protein_g if summary else 34,
        carbs_g=summary.carbs_g if summary else 79,
        fat_g=summary.fat_g if summary else 22,
    )
    consumed = NutritionTarget(
        calories_kcal=previous_consumed.calories_kcal + meal_macros.calories_kcal,
        protein_g=previous_consumed.protein_g + meal_macros.protein_g,
        carbs_g=previous_consumed.carbs_g + meal_macros.carbs_g,
        fat_g=previous_consumed.fat_g + meal_macros.fat_g,
    )
    protein_gap = max(0, profile.target.protein_g - consumed.protein_g)
    guidance = "단백질 목표를 채웠어요. 남은 식사는 채소와 탄수화물을 균형 있게 맞춰요."
    if protein_gap > 0:
        guidance = f"오늘 단백질이 {protein_gap}g 남았어요. 다음 식사는 지방이 낮은 단백질을 먼저 챙겨요."
    meal = DashboardMeal(
        id=f"meal-{len(profile_meals) + 1}",
        name=latest_meal.name,
        meal_type=latest_meal.meal_type,
        calories_kcal=latest_meal.calories_kcal,
        confidence_label=latest_meal.confidence_label,
    )
    dashboard = DashboardTodayResponse(
        date=logged_on.isoformat(),
        target=profile.target,
        consumed=consumed,
        next_meal_guidance=NextMealGuidance(
            deficits=[NutrientGap(nutrient="protein_g", amount=protein_gap, severity="high" if protein_gap > 40 else "medium")] if protein_gap else [],
            excesses=[],
            menu_type_recommendations=["닭가슴살 또는 살코기", "두부와 계란", "기름 적은 생선구이"],
            explanation=guidance,
        ),
        meals=[meal, *(previous_dashboard.meals if previous_dashboard else [])],
    )
    return SavedImpactResponse(
        confirmation=response.confirmation,
        remaining_calories_kcal=max(0, profile.target.calories_kcal - consumed.calories_kcal),
        next_meal_suggestion=guidance,
        dashboard=dashboard,
    )


def require_profile(profile_id: str, repository: CoachRepository) -> CoachProfile:
    profile = repository.get_profile(profile_id)
    if profile is None:
        raise CoachNotFoundError("profile_not_found")
    return profile


def _latest_accumulated_dashboard(meal_logs: list[MealLogRecord]) -> DashboardTodayResponse | None:
    if not meal_logs:
        return None
    return max(
        (record.response.dashboard for record in meal_logs),
        key=lambda dashboard: dashboard.consumed.calories_kcal,
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


def _exercise(plan_id: str, day_index: int, exercise_index: int, item: tuple[str, int, str, str]) -> WorkoutExercise:
    name, sets, reps, rationale = item
    return WorkoutExercise(
        id=f"{plan_id}-exercise-{day_index + 1}-{exercise_index + 1}", name=name, sets=sets, reps=reps, target_rir=2, rest_seconds=120, rationale=rationale
    )


def _workout_day_specs() -> list[tuple[str, str, list[tuple[str, int, str, str]]]]:
    return [
        ("전신 A", "스쿼트와 수평 밀기", [("스쿼트", 3, "6-10회", "하체 힘과 근육의 기본 동작"), ("벤치프레스", 3, "6-10회", "가슴과 삼두의 기본 밀기"), ("시티드 로우", 3, "8-12회", "등과 후면 어깨 균형"), ("플랭크", 2, "30-45초", "몸통 안정성")]),
        ("전신 B", "힌지와 수직 당기기", [("루마니안 데드리프트", 3, "6-10회", "둔근과 햄스트링 강화"), ("랫풀다운", 3, "8-12회", "등 너비와 견갑 움직임"), ("덤벨 숄더프레스", 3, "8-12회", "어깨와 상체 밀기"), ("불가리안 스플릿 스쿼트", 2, "8-10회/측", "좌우 하체 균형")]),
        ("전신 C", "하체 볼륨과 상체 균형", [("레그프레스", 3, "10-15회", "안정적인 하체 볼륨"), ("인클라인 덤벨프레스", 3, "8-12회", "상부 가슴과 어깨"), ("케이블 로우", 3, "8-12회", "등 중앙부와 자세 유지"), ("레터럴 레이즈", 2, "12-20회", "측면 어깨 보완")]),
        ("상체 보완", "약점 보완과 낮은 피로", [("푸시업", 3, "여유 2회 남기기", "상체 밀기 반복"), ("페이스풀", 3, "12-20회", "후면 어깨와 견갑 안정"), ("케이블 컬", 2, "10-15회", "팔 굽힘 보완"), ("트라이셉스 프레스다운", 2, "10-15회", "팔 폄 보완")]),
    ]
