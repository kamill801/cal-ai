export type GoalType = "lose" | "maintain" | "gain" | "recomp";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "high" | "athlete";
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";
export type ConfidenceLabel = "high" | "medium_high" | "medium" | "low" | "manual";

export interface NutritionTarget {
  caloriesKcal: number;
  proteinG: number;
  carbsG: number;
  fatG: number;
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
