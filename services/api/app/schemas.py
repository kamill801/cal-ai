from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GoalType(StrEnum):
    lose = "lose"
    maintain = "maintain"
    gain = "gain"
    recomp = "recomp"


class ActivityLevel(StrEnum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    high = "high"
    athlete = "athlete"


class OnboardingRequest(BaseModel):
    age: int = Field(ge=14, le=100)
    sex: Literal["male", "female", "other"]
    height_cm: float = Field(ge=100, le=230)
    current_weight_kg: float = Field(ge=30, le=250)
    target_weight_kg: float | None = Field(default=None, ge=30, le=250)
    goal_type: GoalType
    activity_level: ActivityLevel
    training_frequency: Literal["none", "1-2", "3-4", "5+"] | None = None


class NutritionTarget(BaseModel):
    calories_kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int


class OnboardingResponse(BaseModel):
    profile_id: UUID
    target: NutritionTarget
    warnings: list[str]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class DashboardMeal(BaseModel):
    id: str
    name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    calories_kcal: int
    confidence_label: Literal["high", "medium_high", "medium", "low", "manual"]


class NutrientGap(BaseModel):
    nutrient: Literal["protein_g", "carbs_g", "fat_g", "calories_kcal"]
    amount: int
    severity: Literal["low", "medium", "high"]


class NextMealGuidance(BaseModel):
    deficits: list[NutrientGap]
    excesses: list[NutrientGap]
    menu_type_recommendations: list[str]
    explanation: str


class DashboardTodayResponse(BaseModel):
    date: str
    target: NutritionTarget
    consumed: NutritionTarget
    next_meal_guidance: NextMealGuidance
    meals: list[DashboardMeal]
