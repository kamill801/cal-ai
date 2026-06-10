from __future__ import annotations

from app.schemas import ActivityLevel, GoalType, NutritionTarget, OnboardingRequest


ACTIVITY_MULTIPLIER = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.light: 1.375,
    ActivityLevel.moderate: 1.55,
    ActivityLevel.high: 1.725,
    ActivityLevel.athlete: 1.9,
}


def calculate_initial_target(profile: OnboardingRequest) -> tuple[NutritionTarget, list[str]]:
    """Estimate an initial target without pretending it is medically exact."""
    warnings: list[str] = []
    bmr = _mifflin_st_jeor(profile)
    tdee = bmr * ACTIVITY_MULTIPLIER[profile.activity_level]

    if profile.goal_type == GoalType.lose:
        calories = tdee - 400
    elif profile.goal_type == GoalType.gain:
        calories = tdee + 250
    elif profile.goal_type == GoalType.recomp:
        calories = tdee - 150
    else:
        calories = tdee

    calories = int(round(_clamp(calories, 1200, 4200) / 10) * 10)

    if profile.target_weight_kg is not None:
        delta = profile.target_weight_kg - profile.current_weight_kg
        if profile.goal_type == GoalType.lose and delta > 0:
            warnings.append("감량 목표와 목표 체중 방향이 맞지 않아 초기 목표를 보수적으로 계산했어요.")
        if profile.goal_type == GoalType.gain and delta < 0:
            warnings.append("증량 목표와 목표 체중 방향이 맞지 않아 초기 목표를 보수적으로 계산했어요.")

    protein_factor = 1.8 if profile.training_frequency in {"3-4", "5+"} else 1.6
    protein_g = int(round(profile.current_weight_kg * protein_factor))
    fat_g = int(round(max(45, calories * 0.27 / 9)))
    carbs_g = int(round(max(80, (calories - protein_g * 4 - fat_g * 9) / 4)))

    if calories <= 1300:
        warnings.append("초기 칼로리 목표가 낮아 안전 범위 안에서 보수적으로 제안했어요.")

    return NutritionTarget(
        calories_kcal=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    ), warnings


def _mifflin_st_jeor(profile: OnboardingRequest) -> float:
    sex_adjustment = 5 if profile.sex == "male" else -161 if profile.sex == "female" else -78
    return (
        10 * profile.current_weight_kg
        + 6.25 * profile.height_cm
        - 5 * profile.age
        + sex_adjustment
    )


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
