from __future__ import annotations

from typing import Literal, cast

from app.schemas import (
    AnalysisJobResponse,
    AnalysisResult,
    AnalysisSummary,
    CalorieRange,
    ClarificationOption,
    ClarificationQuestion,
    ClarificationResponse,
    DashboardTodayResponse,
    DashboardMeal,
    DetectedFoodItem,
    NextMealGuidance,
    NutrientGap,
    NutritionTarget,
    RangeNarrowingResponse,
    SavedImpactResponse,
)


def get_mock_dashboard_today() -> DashboardTodayResponse:
    return DashboardTodayResponse(
        date="2026-06-10",
        target=NutritionTarget(calories_kcal=1850, protein_g=130, carbs_g=190, fat_g=55),
        consumed=NutritionTarget(calories_kcal=670, protein_g=38, carbs_g=126, fat_g=29),
        next_meal_guidance=NextMealGuidance(
            deficits=[NutrientGap(nutrient="protein_g", amount=42, severity="high")],
            excesses=[NutrientGap(nutrient="fat_g", amount=8, severity="medium")],
            menu_type_recommendations=[
                "두부/계란 위주 한식",
                "기름 적은 생선구이류",
                "닭가슴살 샐러드",
            ],
            explanation="단백질은 보충하고 지방은 가볍게 가는 쪽이 좋아요.",
        ),
        meals=[
            {
                "id": "meal-1",
                "name": "그릭요거트 볼",
                "meal_type": "breakfast",
                "calories_kcal": 410,
                "confidence_label": "high",
            },
            {
                "id": "meal-2",
                "name": "아메리카노",
                "meal_type": "snack",
                "calories_kcal": 8,
                "confidence_label": "manual",
            },
        ],
    )


MealType = Literal["breakfast", "lunch", "dinner", "snack"]


def get_mock_analysis_job(job_id: str = "analysis-job-demo") -> AnalysisJobResponse:
    meal_type = _meal_type_from_job_id(job_id)
    return AnalysisJobResponse(id=job_id, status="needs_clarification", result=_initial_analysis(meal_type))


def apply_mock_clarification(job_id: str = "analysis-job-demo", rice_amount: str = "one_bowl") -> ClarificationResponse:
    result = _clarified_analysis(rice_amount, _meal_type_from_job_id(job_id))
    narrowing = _range_narrowing(result) if rice_amount in {"half_bowl", "one_bowl", "large_bowl"} else None
    return ClarificationResponse(
        status="completed",
        result=result,
        range_narrowing=narrowing,
    )


def save_mock_meal(rice_amount: str = "one_bowl", analysis_job_id: str = "mock-lunch-001") -> SavedImpactResponse:
    dashboard = get_mock_dashboard_today()
    clarified = _clarified_analysis(rice_amount, _meal_type_from_job_id(analysis_job_id))
    updated_dashboard = dashboard.model_copy(
        update={
            "consumed": NutritionTarget(
                calories_kcal=dashboard.consumed.calories_kcal + clarified.summary.calories_kcal,
                protein_g=dashboard.consumed.protein_g + clarified.summary.protein_g,
                carbs_g=dashboard.consumed.carbs_g + clarified.summary.carbs_g,
                fat_g=dashboard.consumed.fat_g + clarified.summary.fat_g,
            ),
            "meals": [
                DashboardMeal(
                    id="meal-3",
                    name=clarified.meal_name,
                    meal_type=clarified.meal_type,
                    calories_kcal=clarified.summary.calories_kcal,
                    confidence_label=clarified.summary.confidence_label,
                ),
                *dashboard.meals,
            ],
        }
    )
    return SavedImpactResponse(
        confirmation="기록했어요",
        remaining_calories_kcal=updated_dashboard.target.calories_kcal - updated_dashboard.consumed.calories_kcal,
        next_meal_suggestion="저녁은 단백질을 조금 더 챙기면 좋아요.",
        dashboard=updated_dashboard,
    )


def _meal_type_from_job_id(job_id: str) -> MealType:
    maybe_meal_type = job_id.removeprefix("mock-").removesuffix("-001")
    if maybe_meal_type in {"breakfast", "lunch", "dinner", "snack"}:
        return cast(MealType, maybe_meal_type)
    return "lunch"


def _initial_analysis(meal_type: MealType = "lunch") -> AnalysisResult:
    return AnalysisResult(
        id=f"analysis-{meal_type}-001",
        meal_name="닭고기 덮밥",
        meal_type=meal_type,
        stage_text="음식 구성 확인 중",
        summary=AnalysisSummary(
            calories_kcal=700,
            calorie_range=CalorieRange(low=620, midpoint=700, high=780),
            protein_g=34,
            carbs_g=86,
            fat_g=22,
            confidence=0.72,
            confidence_label="medium",
            confidence_group="estimated",
        ),
        detected_foods=[
            DetectedFoodItem(id="food-rice", name="흰밥", assumption_label="양은 사진상 추정", confidence_label="medium"),
            DetectedFoodItem(id="food-chicken", name="닭고기", assumption_label="구성은 확실", confidence_label="high"),
            DetectedFoodItem(id="food-sauce", name="간장 소스", assumption_label="소스 양은 추정", confidence_label="low"),
        ],
        uncertainty_reasons=["밥 양과 소스가 범위를 크게 바꿀 수 있어요."],
        primary_explanation="밥 양과 소스가 범위를 크게 바꿀 수 있어요.",
        clarification_question=ClarificationQuestion(
            question_key="rice_amount",
            question="밥 양이 어느 정도였나요?",
            helper_text="이것만 확인하면 범위가 꽤 줄어요.",
            type="single_choice",
            options=[
                ClarificationOption(label="반 공기", value="half_bowl", helper_text="가볍게 먹었어요"),
                ClarificationOption(label="한 공기", value="one_bowl", helper_text="보통 양이에요"),
                ClarificationOption(label="많음", value="large_bowl", helper_text="밥이 넉넉했어요"),
                ClarificationOption(label="잘 모르겠어요", value="unknown", helper_text="그대로 저장해도 돼요"),
            ],
        ),
    )


def _clarified_analysis(rice_amount: str = "one_bowl", meal_type: MealType = "lunch") -> AnalysisResult:
    variants = {
        "half_bowl": {
            "calories_kcal": 595,
            "calorie_range": CalorieRange(low=560, midpoint=595, high=630),
            "carbs_g": 64,
            "explanation": "밥 양을 반 공기로 반영했고, 소스는 사진상 추정했어요.",
        },
        "one_bowl": {
            "calories_kcal": 675,
            "calorie_range": CalorieRange(low=640, midpoint=675, high=710),
            "carbs_g": 79,
            "explanation": "밥 양은 확인했고, 소스는 사진상 추정했어요.",
        },
        "large_bowl": {
            "calories_kcal": 765,
            "calorie_range": CalorieRange(low=720, midpoint=765, high=810),
            "carbs_g": 101,
            "explanation": "밥 양을 넉넉한 편으로 반영했고, 소스는 사진상 추정했어요.",
        },
    }
    if rice_amount not in variants:
        return _initial_analysis(meal_type).model_copy(update={"clarification_question": None})

    variant = variants[rice_amount]
    initial = _initial_analysis(meal_type)
    return initial.model_copy(
        update={
            "stage_text": "범위를 좁혔어요",
            "summary": AnalysisSummary(
                calories_kcal=variant["calories_kcal"],
                calorie_range=variant["calorie_range"],
                protein_g=34,
                carbs_g=variant["carbs_g"],
                fat_g=22,
                confidence=0.88,
                confidence_label="medium_high",
                confidence_group="certain",
            ),
            "primary_explanation": variant["explanation"],
            "uncertainty_reasons": [variant["explanation"]],
            "clarification_question": None,
        }
    )


def _range_narrowing(result: AnalysisResult) -> RangeNarrowingResponse:
    before = CalorieRange(low=620, midpoint=700, high=780)
    after = result.summary.calorie_range
    before_width = before.high - before.low
    after_width = after.high - after.low
    return RangeNarrowingResponse(
        before=before,
        after=after,
        copy=f"밥 양 확인으로 범위가 {before_width}kcal에서 {after_width}kcal로 줄었어요.",
    )
