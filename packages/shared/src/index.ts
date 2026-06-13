export type GoalType = "lose" | "maintain" | "gain" | "recomp";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "high" | "athlete";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type ConfidenceLabel = "high" | "medium_high" | "medium" | "low" | "manual";
export type ConfidenceGroup = "certain" | "estimated" | "needs_check" | "manual";

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

export interface MockAnalysisJobResponse {
  id: string;
  status: "queued" | "analyzing" | "needs_clarification" | "completed";
  result: AnalysisResult;
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

export interface ApiSavedImpact {
  confirmation: string;
  remaining_calories_kcal: number;
  next_meal_suggestion: string;
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

export function mapApiSavedImpact(impact: ApiSavedImpact, dashboard: DashboardTodayResponse): SavedImpactViewModel {
  return {
    confirmation: impact.confirmation,
    remainingCaloriesKcal: impact.remaining_calories_kcal,
    nextMealSuggestion: impact.next_meal_suggestion,
    dashboard
  };
}
