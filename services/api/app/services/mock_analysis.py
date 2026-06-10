from __future__ import annotations

from app.schemas import DashboardTodayResponse, NextMealGuidance, NutrientGap, NutritionTarget


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
