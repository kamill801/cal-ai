from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import DashboardMeal, NutritionTarget, OnboardingRequest


class CoachProfile(BaseModel):
    profile_id: str
    owner_id: str | None = None
    onboarding: OnboardingRequest
    target: NutritionTarget
    created_at: str


class NutritionSnapshot(BaseModel):
    target: NutritionTarget
    consumed: NutritionTarget
    remaining: NutritionTarget
    protein_progress: float = Field(ge=0)
    guidance: str


class TrainingSnapshot(BaseModel):
    planned_sessions: int = Field(ge=0)
    completed_sessions: int = Field(ge=0)
    next_workout_title: str | None = None
    recovery_message: str


class CoachNextAction(BaseModel):
    type: Literal["log_meal", "start_workout", "check_in", "recover"]
    title: str
    detail: str


class CoachDashboardResponse(BaseModel):
    profile_id: str
    date: str
    nutrition: NutritionSnapshot
    training: TrainingSnapshot
    meals: list[DashboardMeal]
    next_action: CoachNextAction


class ProfileDeletionResponse(BaseModel):
    profile_id: str
    status: Literal["deleted"]
    deleted_images: int = Field(ge=0)
    deleted_meal_logs: int = Field(ge=0)


class WeightLogRequest(BaseModel):
    logged_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    weight_kg: float = Field(ge=30, le=250)


class WeightLogResponse(WeightLogRequest):
    id: str
    profile_id: str
    created_at: str


class WellnessCheckInRequest(BaseModel):
    logged_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    energy: int = Field(ge=1, le=5)
    sleep_quality: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    note: str | None = Field(default=None, max_length=500)


class WellnessCheckInResponse(WellnessCheckInRequest):
    id: str
    profile_id: str
    created_at: str


class BodyCheckInRequest(BaseModel):
    captured_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    image_upload_id: str = Field(min_length=1, max_length=180)
    view: Literal["front", "side", "back"]
    consent_to_ai_analysis: Literal[True]


class BodyObservation(BaseModel):
    title: str
    detail: str


class BodyCheckInAnalysis(BaseModel):
    provider: Literal["mock", "openai"]
    confidence: Literal["limited"]
    capture_quality: Literal["good", "retake_recommended"]
    observations: list[BodyObservation]
    training_focus: list[str]
    comparison_note: str
    safety_note: str


class BodyAnalysisConsent(BaseModel):
    consented_at: str
    provider: Literal["mock", "openai"]
    model: str
    policy_version: str


class BodyCheckInResponse(BaseModel):
    id: str
    profile_id: str
    captured_on: str
    image_upload_id: str
    view: Literal["front", "side", "back"]
    analysis: BodyCheckInAnalysis
    consent: BodyAnalysisConsent | None = None
    created_at: str


class WorkoutExercise(BaseModel):
    id: str
    name: str
    sets: int = Field(ge=1, le=10)
    reps: str
    target_rir: int = Field(ge=0, le=5)
    rest_seconds: int = Field(ge=30, le=300)
    rationale: str


class WorkoutDay(BaseModel):
    id: str
    title: str
    focus: str
    exercises: list[WorkoutExercise]


class WorkoutPlanResponse(BaseModel):
    id: str
    profile_id: str
    goal_type: str
    days_per_week: int = Field(ge=1, le=6)
    session_minutes: int
    days: list[WorkoutDay]
    personalization_basis: list[str]
    progression_rule: str
    safety_note: str
    generated_at: str


class ExercisePerformance(BaseModel):
    exercise_id: str = Field(min_length=1, max_length=180)
    sets_completed: int = Field(ge=0, le=20)
    reps_completed: int | None = Field(default=None, ge=0, le=100)
    load_kg: float | None = Field(default=None, ge=0, le=500)


class WorkoutSessionRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=180)
    workout_day_id: str = Field(min_length=1, max_length=180)
    performed_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_minutes: int = Field(ge=5, le=240)
    completed_exercise_ids: list[str]
    exercise_performance: list[ExercisePerformance] = Field(default_factory=list)
    session_rpe: int = Field(ge=1, le=10)


class WorkoutSessionResponse(WorkoutSessionRequest):
    id: str
    profile_id: str
    completed: bool
    feedback: str
    created_at: str


class TargetAdjustmentSuggestion(BaseModel):
    status: Literal["insufficient_data", "no_change", "suggested"]
    calorie_delta: int
    proposed_calories_kcal: int | None
    reason: str
    requires_confirmation: bool


class ProgressResponse(BaseModel):
    profile_id: str
    latest_weight_kg: float | None
    weight_change_kg: float | None
    latest_wellness: WellnessCheckInResponse | None
    body_check_ins: list[BodyCheckInResponse]
    workouts_completed: int
    target_adjustment: TargetAdjustmentSuggestion


class WeeklyCoachEvidence(BaseModel):
    meals_logged: int = Field(ge=0)
    workouts_completed: int = Field(ge=0)
    weight_logs: int = Field(ge=0)
    wellness_check_ins: int = Field(ge=0)
    body_check_ins: int = Field(ge=0)


class WeeklyCoachResponse(BaseModel):
    profile_id: str
    score: int = Field(ge=0, le=100)
    headline: str
    wins: list[str]
    focus_items: list[str]
    next_week_actions: list[str]
    evidence: WeeklyCoachEvidence
    safety_note: str
