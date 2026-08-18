export type GoalType = "lose" | "maintain" | "gain" | "recomp";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "high" | "athlete";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type ConfidenceLabel = "high" | "medium_high" | "medium" | "low" | "manual";
export type ConfidenceGroup = "certain" | "estimated" | "needs_check" | "manual";
export type AnalysisJobStatus = "queued" | "analyzing" | "needs_clarification" | "completed" | "failed";
export type ApiErrorKind = "provider" | "validation" | "not_found" | "server" | "unknown";
export type ClientErrorKind = ApiErrorKind | "network" | "http" | "timeout" | "job_failed";
export type ImageContentType = "image/jpeg" | "image/png" | "image/webp";

export interface NutritionTarget {
  caloriesKcal: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
}

export interface CalorieRange {
  low: number;
  midpoint: number;
  high: number;
}

export interface OnboardingRequest {
  age: number;
  sex: "male" | "female" | "other";
  heightCm: number;
  currentWeightKg: number;
  targetWeightKg?: number;
  goalType: GoalType;
  activityLevel: ActivityLevel;
  trainingFrequency?: "none" | "1-2" | "3-4" | "5+";
  experienceLevel?: "beginner" | "intermediate" | "advanced";
  availableEquipment?: ("bodyweight" | "dumbbells" | "gym")[];
  sessionMinutes?: number;
}

export interface OnboardingResponse {
  profileId: string;
  target: NutritionTarget;
  warnings: string[];
}

export interface NutrientGap {
  nutrient: "protein_g" | "carbs_g" | "fat_g" | "calories_kcal";
  amount: number;
  severity: "low" | "medium" | "high";
}

export interface NextMealGuidance {
  deficits: NutrientGap[];
  excesses: NutrientGap[];
  menuTypeRecommendations: string[];
  explanation: string;
}

export interface DashboardMeal {
  id: string;
  name: string;
  mealType: MealType;
  caloriesKcal: number;
  confidenceLabel: ConfidenceLabel;
}

export interface DashboardTodayResponse {
  date: string;
  target: NutritionTarget;
  consumed: NutritionTarget;
  nextMealGuidance: NextMealGuidance;
  meals: DashboardMeal[];
}

export interface DetectedFoodItem {
  id: string;
  name: string;
  assumptionLabel: string;
  confidenceLabel: ConfidenceLabel;
}

export interface ClarificationOption {
  label: string;
  value: string;
  helperText?: string;
}

export interface ClarificationQuestion {
  questionKey: string;
  question: string;
  helperText: string;
  type: "single_choice";
  options: ClarificationOption[];
}

export interface AnalysisResultSummary {
  caloriesKcal: number;
  calorieRange: CalorieRange;
  proteinG: number;
  carbsG: number;
  fatG: number;
  confidence: number;
  confidenceLabel: ConfidenceLabel;
  confidenceGroup: ConfidenceGroup;
}

export interface AnalysisResult {
  id: string;
  mealName: string;
  mealType: MealType;
  stageText: string;
  summary: AnalysisResultSummary;
  detectedFoods: DetectedFoodItem[];
  uncertaintyReasons: string[];
  primaryExplanation: string;
  clarificationQuestion?: ClarificationQuestion;
}

export interface RangeNarrowingResult {
  before: CalorieRange;
  after: CalorieRange;
  copy: string;
}

export interface SavedImpactViewModel {
  confirmation: string;
  remainingCaloriesKcal: number;
  nextMealSuggestion: string;
  dashboard: DashboardTodayResponse;
}

export interface AnalysisJobError {
  code: string;
  message: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  retryable: boolean;
  kind: ApiErrorKind;
}

export interface AnalysisJobViewModel {
  id: string;
  status: AnalysisJobStatus;
  result?: AnalysisResult;
  error?: AnalysisJobError;
}

export interface ImageUploadViewModel {
  imageUploadId: string;
  imageReference: string;
  status: "ready";
}

export interface ImageUploadPresignViewModel {
  imageUploadId: string;
  objectKey: string;
  uploadUrl: string;
  headers: Record<string, string>;
  expiresAt: string;
  maxBytes: number;
  softLimitBytes: number;
  softLimitExceeded: boolean;
  ttlDays: number;
}

export interface MockAnalysisJobResponse {
  id: string;
  status: AnalysisJobStatus;
  result?: AnalysisResult;
  error?: AnalysisJobError;
}

export interface ApiNutritionTarget {
  calories_kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface ApiOnboardingRequest {
  age: number;
  sex: "male" | "female" | "other";
  height_cm: number;
  current_weight_kg: number;
  target_weight_kg?: number | null;
  goal_type: GoalType;
  activity_level: ActivityLevel;
  training_frequency?: "none" | "1-2" | "3-4" | "5+" | null;
  experience_level?: "beginner" | "intermediate" | "advanced";
  available_equipment?: ("bodyweight" | "dumbbells" | "gym")[];
  session_minutes?: number;
}

export interface ApiOnboardingResponse {
  profile_id: string;
  target: ApiNutritionTarget;
  warnings: string[];
}

export interface ApiNutrientGap {
  nutrient: "protein_g" | "carbs_g" | "fat_g" | "calories_kcal";
  amount: number;
  severity: "low" | "medium" | "high";
}

export interface ApiNextMealGuidance {
  deficits: ApiNutrientGap[];
  excesses: ApiNutrientGap[];
  menu_type_recommendations: string[];
  explanation: string;
}

export interface ApiDashboardMeal {
  id: string;
  name: string;
  meal_type: MealType;
  calories_kcal: number;
  confidence_label: ConfidenceLabel;
}

export interface ApiDashboardTodayResponse {
  date: string;
  target: ApiNutritionTarget;
  consumed: ApiNutritionTarget;
  next_meal_guidance: ApiNextMealGuidance;
  meals: ApiDashboardMeal[];
}

export interface ApiCalorieRange {
  low: number;
  midpoint: number;
  high: number;
}

export interface ApiAnalysisSummary {
  calories_kcal: number;
  calorie_range: ApiCalorieRange;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  confidence: number;
  confidence_label: ConfidenceLabel;
  confidence_group: ConfidenceGroup;
}

export interface ApiDetectedFoodItem {
  id: string;
  name: string;
  assumption_label: string;
  confidence_label: ConfidenceLabel;
}

export interface ApiClarificationOption {
  label: string;
  value: string;
  helper_text?: string | null;
}

export interface ApiClarificationQuestion {
  question_key: string;
  question: string;
  helper_text: string;
  type: "single_choice";
  options: ApiClarificationOption[];
}

export interface ApiAnalysisResult {
  id: string;
  meal_name: string;
  meal_type: MealType;
  stage_text: string;
  summary: ApiAnalysisSummary;
  detected_foods: ApiDetectedFoodItem[];
  uncertainty_reasons: string[];
  primary_explanation: string;
  clarification_question?: ApiClarificationQuestion | null;
}

export interface ApiAnalysisJobError {
  code: string;
  message: string;
}

export interface ApiAnalysisJobCreateResponse {
  analysis_job_id: string;
  status: "queued";
}

export interface ApiImageUploadRequest {
  local_asset_id: string;
  file_name: string;
  content_type: ImageContentType;
  byte_size: number;
  simulate_failure?: boolean;
}

export interface ApiImageUploadResponse {
  image_upload_id: string;
  image_reference: string;
  status: "ready";
}

export interface ApiImageUploadPresignRequest {
  local_asset_id: string;
  file_name: string;
  content_type: ImageContentType;
  byte_size: number;
}

export interface ApiImageUploadPresignResponse {
  image_upload_id: string;
  object_key: string;
  upload_url: string;
  headers: Record<string, string>;
  expires_at: string;
  max_bytes: number;
  soft_limit_bytes: number;
  soft_limit_exceeded: boolean;
  ttl_days: number;
}

export interface ApiImageUploadCompleteRequest {
  image_upload_id: string;
  object_key: string;
  local_asset_id?: string;
  file_name: string;
  content_type: ImageContentType;
  byte_size: number;
  etag?: string | null;
}

export interface ApiAnalysisJobResponse {
  id: string;
  status: AnalysisJobStatus;
  result: ApiAnalysisResult | null;
  error?: ApiAnalysisJobError | null;
}

export interface ApiRangeNarrowingResult {
  before: ApiCalorieRange;
  after: ApiCalorieRange;
  copy?: string;
  copy_text?: string;
}

export interface ApiClarificationResponse {
  status: "completed";
  result: ApiAnalysisResult;
  range_narrowing?: ApiRangeNarrowingResult | null;
}

export interface ApiMealLogRequest {
  analysis_job_id: string;
  result_id: string;
  clarification_value: string;
  profile_id?: string | null;
  logged_on?: string | null;
  nutrition_override?: ApiMealNutritionOverride | null;
}

export interface MealNutritionOverride {
  mealName?: string;
  caloriesKcal: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
}

export interface ApiMealNutritionOverride {
  meal_name?: string | null;
  calories_kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface ApiSavedImpact {
  confirmation: string;
  remaining_calories_kcal: number;
  next_meal_suggestion: string;
}

export interface ApiSavedImpactResponse extends ApiSavedImpact {
  dashboard: ApiDashboardTodayResponse;
}

export function mapApiNutritionTarget(target: ApiNutritionTarget): NutritionTarget {
  return {
    caloriesKcal: target.calories_kcal,
    proteinG: target.protein_g,
    carbsG: target.carbs_g,
    fatG: target.fat_g
  };
}

export function mapApiOnboardingResponse(response: ApiOnboardingResponse): OnboardingResponse {
  return {
    profileId: response.profile_id,
    target: mapApiNutritionTarget(response.target),
    warnings: response.warnings
  };
}

export function mapApiDashboardToday(response: ApiDashboardTodayResponse): DashboardTodayResponse {
  return {
    date: response.date,
    target: mapApiNutritionTarget(response.target),
    consumed: mapApiNutritionTarget(response.consumed),
    nextMealGuidance: {
      deficits: response.next_meal_guidance.deficits,
      excesses: response.next_meal_guidance.excesses,
      menuTypeRecommendations: response.next_meal_guidance.menu_type_recommendations,
      explanation: response.next_meal_guidance.explanation
    },
    meals: response.meals.map((meal) => ({
      id: meal.id,
      name: meal.name,
      mealType: meal.meal_type,
      caloriesKcal: meal.calories_kcal,
      confidenceLabel: meal.confidence_label
    }))
  };
}

export function mapApiCalorieRange(range: ApiCalorieRange): CalorieRange {
  return { low: range.low, midpoint: range.midpoint, high: range.high };
}

export function mapApiAnalysisResult(result: ApiAnalysisResult): AnalysisResult {
  return {
    id: result.id,
    mealName: result.meal_name,
    mealType: result.meal_type,
    stageText: result.stage_text,
    summary: {
      caloriesKcal: result.summary.calories_kcal,
      calorieRange: mapApiCalorieRange(result.summary.calorie_range),
      proteinG: result.summary.protein_g,
      carbsG: result.summary.carbs_g,
      fatG: result.summary.fat_g,
      confidence: result.summary.confidence,
      confidenceLabel: result.summary.confidence_label,
      confidenceGroup: result.summary.confidence_group
    },
    detectedFoods: result.detected_foods.map((food) => ({
      id: food.id,
      name: food.name,
      assumptionLabel: food.assumption_label,
      confidenceLabel: food.confidence_label
    })),
    uncertaintyReasons: result.uncertainty_reasons,
    primaryExplanation: result.primary_explanation,
    clarificationQuestion: result.clarification_question
      ? {
          questionKey: result.clarification_question.question_key,
          question: result.clarification_question.question,
          helperText: result.clarification_question.helper_text,
          type: result.clarification_question.type,
          options: result.clarification_question.options.map((option) => ({
            label: option.label,
            value: option.value,
            helperText: option.helper_text ?? undefined
          }))
        }
      : undefined
  };
}

export function mapApiAnalysisJob(response: ApiAnalysisJobResponse): AnalysisJobViewModel {
  return {
    id: response.id,
    status: response.status,
    result: response.result ? mapApiAnalysisResult(response.result) : undefined,
    error: response.error ? { code: response.error.code, message: response.error.message } : undefined
  };
}

export function mapApiImageUpload(response: ApiImageUploadResponse): ImageUploadViewModel {
  return {
    imageUploadId: response.image_upload_id,
    imageReference: response.image_reference,
    status: response.status
  };
}

export function mapApiImageUploadPresign(response: ApiImageUploadPresignResponse): ImageUploadPresignViewModel {
  return {
    imageUploadId: response.image_upload_id,
    objectKey: response.object_key,
    uploadUrl: response.upload_url,
    headers: response.headers,
    expiresAt: response.expires_at,
    maxBytes: response.max_bytes,
    softLimitBytes: response.soft_limit_bytes,
    softLimitExceeded: response.soft_limit_exceeded,
    ttlDays: response.ttl_days
  };
}

export function mapApiRangeNarrowing(result: ApiRangeNarrowingResult): RangeNarrowingResult {
  return {
    before: mapApiCalorieRange(result.before),
    after: mapApiCalorieRange(result.after),
    copy: result.copy ?? result.copy_text ?? "범위를 다시 계산했어요."
  };
}

export function mapApiClarificationResponse(response: ApiClarificationResponse): {
  status: "completed";
  result: AnalysisResult;
  rangeNarrowing?: RangeNarrowingResult;
} {
  return {
    status: response.status,
    result: mapApiAnalysisResult(response.result),
    rangeNarrowing: response.range_narrowing ? mapApiRangeNarrowing(response.range_narrowing) : undefined
  };
}

export function mapApiSavedImpact(impact: ApiSavedImpact, dashboard: DashboardTodayResponse): SavedImpactViewModel {
  return {
    confirmation: impact.confirmation,
    remainingCaloriesKcal: impact.remaining_calories_kcal,
    nextMealSuggestion: impact.next_meal_suggestion,
    dashboard
  };
}

export function mapApiSavedImpactResponse(response: ApiSavedImpactResponse): SavedImpactViewModel {
  return mapApiSavedImpact(response, mapApiDashboardToday(response.dashboard));
}

export interface CoachNutritionSnapshot {
  target: NutritionTarget;
  consumed: NutritionTarget;
  remaining: NutritionTarget;
  proteinProgress: number;
  guidance: string;
}

export interface CoachTrainingSnapshot {
  plannedSessions: number;
  completedSessions: number;
  nextWorkoutTitle?: string;
  recoveryMessage: string;
}

export interface CoachDashboard {
  profileId: string;
  date: string;
  nutrition: CoachNutritionSnapshot;
  training: CoachTrainingSnapshot;
  meals: DashboardMeal[];
  nextAction: { type: "log_meal" | "start_workout" | "check_in" | "recover"; title: string; detail: string };
}

export interface ProfileDeletionResult {
  profileId: string;
  status: "deleted";
  deletedImages: number;
  deletedMealLogs: number;
}

export interface WeightLog {
  id: string;
  profileId: string;
  loggedOn: string;
  weightKg: number;
  createdAt: string;
}

export interface WellnessCheckIn {
  id: string;
  profileId: string;
  loggedOn: string;
  energy: number;
  sleepQuality: number;
  soreness: number;
  note?: string;
  createdAt: string;
}

export interface BodyCheckIn {
  id: string;
  profileId: string;
  capturedOn: string;
  imageUploadId: string;
  view: "front" | "side" | "back";
  analysis: {
    provider: "mock" | "openai";
    confidence: "limited";
    captureQuality: "good" | "retake_recommended";
    observations: { title: string; detail: string }[];
    trainingFocus: string[];
    comparisonNote: string;
    safetyNote: string;
  };
  createdAt: string;
}

export interface WorkoutExercise {
  id: string;
  name: string;
  sets: number;
  reps: string;
  targetRir: number;
  restSeconds: number;
  rationale: string;
}

export interface WorkoutDay {
  id: string;
  title: string;
  focus: string;
  exercises: WorkoutExercise[];
}

export interface WorkoutPlan {
  id: string;
  profileId: string;
  goalType: GoalType;
  daysPerWeek: number;
  sessionMinutes: number;
  days: WorkoutDay[];
  personalizationBasis: string[];
  progressionRule: string;
  safetyNote: string;
  generatedAt: string;
}

export interface WorkoutSession {
  id: string;
  profileId: string;
  planId: string;
  workoutDayId: string;
  performedOn: string;
  durationMinutes: number;
  completedExerciseIds: string[];
  exercisePerformance: WorkoutExercisePerformance[];
  sessionRpe: number;
  completed: boolean;
  feedback: string;
  createdAt: string;
}

export interface WorkoutExercisePerformance {
  exerciseId: string;
  setsCompleted: number;
  repsCompleted?: number;
  loadKg?: number;
}

export interface ProgressSummary {
  profileId: string;
  latestWeightKg?: number;
  weightChangeKg?: number;
  latestWellness?: WellnessCheckIn;
  bodyCheckIns: BodyCheckIn[];
  workoutsCompleted: number;
  targetAdjustment: TargetAdjustmentSuggestion;
}

export interface TargetAdjustmentSuggestion {
  status: "insufficient_data" | "no_change" | "suggested";
  calorieDelta: number;
  proposedCaloriesKcal?: number;
  reason: string;
  requiresConfirmation: boolean;
}

export interface WeeklyCoachReport {
  profileId: string;
  score: number;
  headline: string;
  wins: string[];
  focusItems: string[];
  nextWeekActions: string[];
  evidence: { mealsLogged: number; workoutsCompleted: number; weightLogs: number; wellnessCheckIns: number; bodyCheckIns: number };
  safetyNote: string;
}

export interface ApiCoachDashboard {
  profile_id: string;
  date: string;
  nutrition: { target: ApiNutritionTarget; consumed: ApiNutritionTarget; remaining: ApiNutritionTarget; protein_progress: number; guidance: string };
  training: { planned_sessions: number; completed_sessions: number; next_workout_title?: string | null; recovery_message: string };
  meals?: ApiDashboardMeal[];
  next_action: { type: CoachDashboard["nextAction"]["type"]; title: string; detail: string };
}

export interface ApiProfileDeletionResult {
  profile_id: string;
  status: "deleted";
  deleted_images: number;
  deleted_meal_logs: number;
}

export interface ApiWeightLog {
  id: string;
  profile_id: string;
  logged_on: string;
  weight_kg: number;
  created_at: string;
}

export interface ApiWellnessCheckIn {
  id: string;
  profile_id: string;
  logged_on: string;
  energy: number;
  sleep_quality: number;
  soreness: number;
  note?: string | null;
  created_at: string;
}

export interface ApiBodyCheckIn {
  id: string;
  profile_id: string;
  captured_on: string;
  image_upload_id: string;
  view: BodyCheckIn["view"];
  analysis: {
    provider: BodyCheckIn["analysis"]["provider"];
    confidence: "limited";
    capture_quality: BodyCheckIn["analysis"]["captureQuality"];
    observations: { title: string; detail: string }[];
    training_focus: string[];
    comparison_note: string;
    safety_note: string;
  };
  created_at: string;
}

export interface ApiWorkoutPlan {
  id: string;
  profile_id: string;
  goal_type: GoalType;
  days_per_week: number;
  session_minutes: number;
  days: { id: string; title: string; focus: string; exercises: { id: string; name: string; sets: number; reps: string; target_rir: number; rest_seconds: number; rationale: string }[] }[];
  personalization_basis: string[];
  progression_rule: string;
  safety_note: string;
  generated_at: string;
}

export interface ApiWorkoutSession {
  id: string;
  profile_id: string;
  plan_id: string;
  workout_day_id: string;
  performed_on: string;
  duration_minutes: number;
  completed_exercise_ids: string[];
  exercise_performance?: Array<{
    exercise_id: string;
    sets_completed: number;
    reps_completed?: number | null;
    load_kg?: number | null;
  }>;
  session_rpe: number;
  completed: boolean;
  feedback: string;
  created_at: string;
}

export interface ApiProgressSummary {
  profile_id: string;
  latest_weight_kg?: number | null;
  weight_change_kg?: number | null;
  latest_wellness?: ApiWellnessCheckIn | null;
  body_check_ins: ApiBodyCheckIn[];
  workouts_completed: number;
  target_adjustment: {
    status: TargetAdjustmentSuggestion["status"];
    calorie_delta: number;
    proposed_calories_kcal?: number | null;
    reason: string;
    requires_confirmation: boolean;
  };
}

export interface ApiWeeklyCoachReport {
  profile_id: string;
  score: number;
  headline: string;
  wins: string[];
  focus_items: string[];
  next_week_actions: string[];
  evidence: { meals_logged: number; workouts_completed: number; weight_logs: number; wellness_check_ins: number; body_check_ins: number };
  safety_note: string;
}

export function mapApiCoachDashboard(value: ApiCoachDashboard): CoachDashboard {
  return {
    profileId: value.profile_id,
    date: value.date,
    nutrition: {
      target: mapApiNutritionTarget(value.nutrition.target),
      consumed: mapApiNutritionTarget(value.nutrition.consumed),
      remaining: mapApiNutritionTarget(value.nutrition.remaining),
      proteinProgress: value.nutrition.protein_progress,
      guidance: value.nutrition.guidance
    },
    training: {
      plannedSessions: value.training.planned_sessions,
      completedSessions: value.training.completed_sessions,
      nextWorkoutTitle: value.training.next_workout_title ?? undefined,
      recoveryMessage: value.training.recovery_message
    },
    meals: (value.meals ?? []).map((meal) => ({
      id: meal.id,
      name: meal.name,
      mealType: meal.meal_type,
      caloriesKcal: meal.calories_kcal,
      confidenceLabel: meal.confidence_label
    })),
    nextAction: value.next_action
  };
}

export function mapApiProfileDeletionResult(value: ApiProfileDeletionResult): ProfileDeletionResult {
  return {
    profileId: value.profile_id,
    status: value.status,
    deletedImages: value.deleted_images,
    deletedMealLogs: value.deleted_meal_logs
  };
}

export function mapApiWeightLog(value: ApiWeightLog): WeightLog {
  return { id: value.id, profileId: value.profile_id, loggedOn: value.logged_on, weightKg: value.weight_kg, createdAt: value.created_at };
}

export function mapApiWellness(value: ApiWellnessCheckIn): WellnessCheckIn {
  return {
    id: value.id,
    profileId: value.profile_id,
    loggedOn: value.logged_on,
    energy: value.energy,
    sleepQuality: value.sleep_quality,
    soreness: value.soreness,
    note: value.note ?? undefined,
    createdAt: value.created_at
  };
}

export function mapApiBodyCheckIn(value: ApiBodyCheckIn): BodyCheckIn {
  return {
    id: value.id,
    profileId: value.profile_id,
    capturedOn: value.captured_on,
    imageUploadId: value.image_upload_id,
    view: value.view,
    analysis: {
      provider: value.analysis.provider,
      confidence: value.analysis.confidence,
      captureQuality: value.analysis.capture_quality,
      observations: value.analysis.observations,
      trainingFocus: value.analysis.training_focus,
      comparisonNote: value.analysis.comparison_note,
      safetyNote: value.analysis.safety_note
    },
    createdAt: value.created_at
  };
}

export function mapApiWorkoutPlan(value: ApiWorkoutPlan): WorkoutPlan {
  return {
    id: value.id,
    profileId: value.profile_id,
    goalType: value.goal_type,
    daysPerWeek: value.days_per_week,
    sessionMinutes: value.session_minutes,
    days: value.days.map((day) => ({
      id: day.id,
      title: day.title,
      focus: day.focus,
      exercises: day.exercises.map((exercise) => ({
        id: exercise.id,
        name: exercise.name,
        sets: exercise.sets,
        reps: exercise.reps,
        targetRir: exercise.target_rir,
        restSeconds: exercise.rest_seconds,
        rationale: exercise.rationale
      }))
    })),
    personalizationBasis: value.personalization_basis,
    progressionRule: value.progression_rule,
    safetyNote: value.safety_note,
    generatedAt: value.generated_at
  };
}

export function mapApiWorkoutSession(value: ApiWorkoutSession): WorkoutSession {
  return {
    id: value.id,
    profileId: value.profile_id,
    planId: value.plan_id,
    workoutDayId: value.workout_day_id,
    performedOn: value.performed_on,
    durationMinutes: value.duration_minutes,
    completedExerciseIds: value.completed_exercise_ids,
    exercisePerformance: (value.exercise_performance ?? []).map((item) => ({
      exerciseId: item.exercise_id,
      setsCompleted: item.sets_completed,
      repsCompleted: item.reps_completed ?? undefined,
      loadKg: item.load_kg ?? undefined
    })),
    sessionRpe: value.session_rpe,
    completed: value.completed,
    feedback: value.feedback,
    createdAt: value.created_at
  };
}

export function mapApiProgress(value: ApiProgressSummary): ProgressSummary {
  return {
    profileId: value.profile_id,
    latestWeightKg: value.latest_weight_kg ?? undefined,
    weightChangeKg: value.weight_change_kg ?? undefined,
    latestWellness: value.latest_wellness ? mapApiWellness(value.latest_wellness) : undefined,
    bodyCheckIns: value.body_check_ins.map(mapApiBodyCheckIn),
    workoutsCompleted: value.workouts_completed,
    targetAdjustment: {
      status: value.target_adjustment.status,
      calorieDelta: value.target_adjustment.calorie_delta,
      proposedCaloriesKcal: value.target_adjustment.proposed_calories_kcal ?? undefined,
      reason: value.target_adjustment.reason,
      requiresConfirmation: value.target_adjustment.requires_confirmation
    }
  };
}

export function mapApiWeeklyCoach(value: ApiWeeklyCoachReport): WeeklyCoachReport {
  return {
    profileId: value.profile_id,
    score: value.score,
    headline: value.headline,
    wins: value.wins,
    focusItems: value.focus_items,
    nextWeekActions: value.next_week_actions,
    evidence: {
      mealsLogged: value.evidence.meals_logged,
      workoutsCompleted: value.evidence.workouts_completed,
      weightLogs: value.evidence.weight_logs,
      wellnessCheckIns: value.evidence.wellness_check_ins,
      bodyCheckIns: value.evidence.body_check_ins
    },
    safetyNote: value.safety_note
  };
}
