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


class CalorieRange(BaseModel):
    low: int
    midpoint: int
    high: int


class AnalysisSummary(BaseModel):
    calories_kcal: int
    calorie_range: CalorieRange
    protein_g: int
    carbs_g: int
    fat_g: int
    confidence: float = Field(ge=0, le=1)
    confidence_label: Literal["high", "medium_high", "medium", "low", "manual"]
    confidence_group: Literal["certain", "estimated", "needs_check", "manual"]


class DetectedFoodItem(BaseModel):
    id: str
    name: str
    assumption_label: str
    confidence_label: Literal["high", "medium_high", "medium", "low", "manual"]


class ClarificationOption(BaseModel):
    label: str
    value: str
    helper_text: str | None = None


class ClarificationQuestion(BaseModel):
    question_key: str
    question: str
    helper_text: str
    type: Literal["single_choice"]
    options: list[ClarificationOption]


class AnalysisResult(BaseModel):
    id: str
    meal_name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    stage_text: str
    summary: AnalysisSummary
    detected_foods: list[DetectedFoodItem]
    uncertainty_reasons: list[str]
    primary_explanation: str
    clarification_question: ClarificationQuestion | None = None


class AnalysisJobRequest(BaseModel):
    image_upload_id: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "lunch"
    optional_note: str | None = None


class AnalysisJobCreateResponse(BaseModel):
    analysis_job_id: str
    status: Literal["queued"]


class AnalysisJobResponse(BaseModel):
    id: str
    status: Literal["queued", "analyzing", "needs_clarification", "completed"]
    result: AnalysisResult


class ClarificationAnswer(BaseModel):
    question_key: str
    value: str


class ClarificationRequest(BaseModel):
    answers: list[ClarificationAnswer]


class RangeNarrowingResponse(BaseModel):
    before: CalorieRange
    after: CalorieRange
    copy_text: str = Field(serialization_alias="copy", validation_alias="copy")


class ClarificationResponse(BaseModel):
    status: Literal["completed"]
    result: AnalysisResult
    range_narrowing: RangeNarrowingResponse | None = None


class MealLogRequest(BaseModel):
    analysis_job_id: str
    result_id: str
    clarification_value: Literal["half_bowl", "one_bowl", "large_bowl", "unknown"]


class SavedImpactResponse(BaseModel):
    confirmation: str
    remaining_calories_kcal: int
    next_meal_suggestion: str
    dashboard: DashboardTodayResponse
