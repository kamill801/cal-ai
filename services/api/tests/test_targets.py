from app.schemas import ActivityLevel, GoalType, OnboardingRequest
from app.services.targets import calculate_initial_target


def test_calculate_initial_target_for_weight_loss_user() -> None:
    target, warnings = calculate_initial_target(
        OnboardingRequest(
            age=29,
            sex="male",
            height_cm=176,
            current_weight_kg=82,
            target_weight_kg=75,
            goal_type=GoalType.lose,
            activity_level=ActivityLevel.moderate,
            training_frequency="3-4",
        )
    )

    assert 1600 <= target.calories_kcal <= 2400
    assert target.protein_g >= 130
    assert target.carbs_g > 0
    assert target.fat_g >= 45
    assert warnings == []


def test_direction_warning_when_goal_and_target_weight_conflict() -> None:
    _, warnings = calculate_initial_target(
        OnboardingRequest(
            age=29,
            sex="male",
            height_cm=176,
            current_weight_kg=82,
            target_weight_kg=86,
            goal_type=GoalType.lose,
            activity_level=ActivityLevel.moderate,
            training_frequency="1-2",
        )
    )

    assert warnings
