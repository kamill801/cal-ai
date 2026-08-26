from __future__ import annotations

from app.schemas import (
    AnalysisResult,
    AnalysisSummary,
    CalorieRange,
    ClarificationRequest,
    ClarificationResponse,
    DashboardMeal,
    MealLogRequest,
    MealNutritionOverride,
    NutritionTarget,
    RangeNarrowingResponse,
    SavedImpactResponse,
)
from app.services.mock_analysis import get_mock_dashboard_today


PORTION_FACTORS = {
    "half_bowl": 0.8,
    "one_bowl": 1.0,
    "large_bowl": 1.2,
    "unknown": 1.0,
}


def apply_manual_nutrition_override(
    result: AnalysisResult,
    override: MealNutritionOverride,
) -> AnalysisResult:
    calories = override.calories_kcal
    margin = min(50, max(15, round(calories * 0.04)))
    summary = AnalysisSummary(
        calories_kcal=calories,
        calorie_range=CalorieRange(low=max(0, calories - margin), midpoint=calories, high=calories + margin),
        protein_g=override.protein_g,
        carbs_g=override.carbs_g,
        fat_g=override.fat_g,
        confidence=1,
        confidence_label="manual",
        confidence_group="manual",
    )
    return result.model_copy(
        update={
            "meal_name": override.meal_name or result.meal_name,
            "stage_text": "직접 확인한 값을 반영했어요",
            "summary": summary,
            "primary_explanation": "사용자가 확인하고 수정한 열량과 영양소 값으로 저장해요.",
            "clarification_question": None,
        }
    )


def apply_persisted_clarification(
    result: AnalysisResult,
    payload: ClarificationRequest,
) -> ClarificationResponse:
    question = result.clarification_question
    answer = next(
        (
            item.value
            for item in payload.answers
            if question is not None and item.question_key == question.question_key
        ),
        "unknown",
    )
    factor = PORTION_FACTORS.get(answer, 1.0)
    clarified = result.model_copy(update={"clarification_question": None})
    if answer == "unknown":
        return ClarificationResponse(status="completed", result=clarified)

    before = result.summary.calorie_range
    midpoint = max(1, round(result.summary.calories_kcal * factor))
    margin = max(25, round(midpoint * 0.055))
    after = CalorieRange(low=max(0, midpoint - margin), midpoint=midpoint, high=midpoint + margin)
    summary = AnalysisSummary(
        calories_kcal=midpoint,
        calorie_range=after,
        protein_g=max(0, round(result.summary.protein_g * factor)),
        carbs_g=max(0, round(result.summary.carbs_g * factor)),
        fat_g=max(0, round(result.summary.fat_g * factor)),
        confidence=max(result.summary.confidence, 0.86),
        confidence_label="medium_high",
        confidence_group="certain",
    )
    clarified = clarified.model_copy(
        update={
            "stage_text": "확인한 양을 반영했어요",
            "summary": summary,
            "primary_explanation": "선택한 섭취량을 반영해 열량과 영양소 범위를 좁혔어요.",
        }
    )
    return ClarificationResponse(
        status="completed",
        result=clarified,
        range_narrowing=RangeNarrowingResponse(
            before=before,
            after=after,
            copy=f"섭취량 확인으로 범위가 {before.high - before.low}kcal에서 {after.high - after.low}kcal로 줄었어요.",
        ),
    )


def save_persisted_meal(result: AnalysisResult, payload: MealLogRequest) -> SavedImpactResponse:
    dashboard = get_mock_dashboard_today()
    consumed = NutritionTarget(
        calories_kcal=dashboard.consumed.calories_kcal + result.summary.calories_kcal,
        protein_g=dashboard.consumed.protein_g + result.summary.protein_g,
        carbs_g=dashboard.consumed.carbs_g + result.summary.carbs_g,
        fat_g=dashboard.consumed.fat_g + result.summary.fat_g,
    )
    updated_dashboard = dashboard.model_copy(
        update={
            "date": payload.logged_on.isoformat() if payload.logged_on else dashboard.date,
            "consumed": consumed,
            "meals": [
                DashboardMeal(
                    id=f"meal-{payload.analysis_job_id}",
                    name=result.meal_name,
                    meal_type=result.meal_type,
                    calories_kcal=result.summary.calories_kcal,
                    confidence_label=result.summary.confidence_label,
                    nutrition=NutritionTarget(
                        calories_kcal=result.summary.calories_kcal,
                        protein_g=result.summary.protein_g,
                        carbs_g=result.summary.carbs_g,
                        fat_g=result.summary.fat_g,
                    ),
                ),
                *dashboard.meals,
            ],
        }
    )
    remaining = max(0, updated_dashboard.target.calories_kcal - consumed.calories_kcal)
    protein_gap = max(0, updated_dashboard.target.protein_g - consumed.protein_g)
    suggestion = (
        f"오늘 단백질이 {protein_gap}g 남았어요. 다음 식사는 저지방 단백질을 먼저 챙겨요."
        if protein_gap
        else "단백질 목표를 채웠어요. 남은 식사는 채소와 탄수화물을 균형 있게 맞춰요."
    )
    return SavedImpactResponse(
        confirmation="기록했어요",
        remaining_calories_kcal=remaining,
        next_meal_suggestion=suggestion,
        dashboard=updated_dashboard,
    )
