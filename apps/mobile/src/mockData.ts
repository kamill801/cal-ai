import type { ImageSourcePropType } from "react-native";
import type { AnalysisResult, DashboardTodayResponse, RangeNarrowingResult, SavedImpactViewModel } from "@cal-ai/shared";

const mealPreview = require("../assets/meal-preview.png") as ImageSourcePropType;

export const todayDashboard: DashboardTodayResponse = {
  date: "2026-06-10",
  target: {
    caloriesKcal: 1850,
    proteinG: 130,
    carbsG: 190,
    fatG: 55
  },
  consumed: {
    caloriesKcal: 670,
    proteinG: 38,
    carbsG: 126,
    fatG: 29
  },
  nextMealGuidance: {
    deficits: [{ nutrient: "protein_g", amount: 42, severity: "high" }],
    excesses: [{ nutrient: "fat_g", amount: 8, severity: "medium" }],
    menuTypeRecommendations: ["두부/계란 위주 한식", "기름 적은 생선구이류", "닭가슴살 샐러드"],
    explanation: "단백질은 보충하고 지방은 가볍게 가는 쪽이 좋아요."
  },
  meals: [
    { id: "meal-1", name: "그릭요거트 볼", mealType: "breakfast", caloriesKcal: 410, confidenceLabel: "high" },
    { id: "meal-2", name: "아메리카노", mealType: "snack", caloriesKcal: 8, confidenceLabel: "manual" }
  ]
};

export const scanPhotoSource = mealPreview;

export const initialAnalysis: AnalysisResult = {
  id: "analysis-lunch-001",
  mealName: "닭고기 덮밥",
  mealType: "lunch",
  stageText: "음식 구성 확인 중",
  summary: {
    caloriesKcal: 700,
    calorieRange: { low: 620, midpoint: 700, high: 780 },
    proteinG: 34,
    carbsG: 86,
    fatG: 22,
    confidence: 0.72,
    confidenceLabel: "medium",
    confidenceGroup: "estimated"
  },
  detectedFoods: [
    { id: "food-rice", name: "흰밥", assumptionLabel: "양은 사진상 추정", confidenceLabel: "medium" },
    { id: "food-chicken", name: "닭고기", assumptionLabel: "구성은 확실", confidenceLabel: "high" },
    { id: "food-sauce", name: "간장 소스", assumptionLabel: "소스 양은 추정", confidenceLabel: "low" }
  ],
  uncertaintyReasons: ["밥 양과 소스가 범위를 크게 바꿀 수 있어요."],
  primaryExplanation: "밥 양과 소스가 범위를 크게 바꿀 수 있어요.",
  clarificationQuestion: {
    questionKey: "rice_amount",
    question: "밥 양이 어느 정도였나요?",
    helperText: "이것만 확인하면 범위가 꽤 줄어요.",
    type: "single_choice",
    options: [
      { label: "반 공기", value: "half_bowl", helperText: "가볍게 먹었어요" },
      { label: "한 공기", value: "one_bowl", helperText: "보통 양이에요" },
      { label: "많음", value: "large_bowl", helperText: "밥이 넉넉했어요" },
      { label: "잘 모르겠어요", value: "unknown", helperText: "그대로 저장해도 돼요" }
    ]
  }
};

const clarifiedAnalysisByRiceAmount: Record<string, AnalysisResult> = {
  half_bowl: createRiceClarifiedAnalysis({
    caloriesKcal: 595,
    calorieRange: { low: 560, midpoint: 595, high: 630 },
    carbsG: 64,
    explanation: "밥 양을 반 공기로 반영했고, 소스는 사진상 추정했어요."
  }),
  one_bowl: createRiceClarifiedAnalysis({
    caloriesKcal: 675,
    calorieRange: { low: 640, midpoint: 675, high: 710 },
    carbsG: 79,
    explanation: "밥 양은 확인했고, 소스는 사진상 추정했어요."
  }),
  large_bowl: createRiceClarifiedAnalysis({
    caloriesKcal: 765,
    calorieRange: { low: 720, midpoint: 765, high: 810 },
    carbsG: 101,
    explanation: "밥 양을 넉넉한 편으로 반영했고, 소스는 사진상 추정했어요."
  })
};

function createRiceClarifiedAnalysis({
  caloriesKcal,
  calorieRange,
  carbsG,
  explanation
}: {
  caloriesKcal: number;
  calorieRange: AnalysisResult["summary"]["calorieRange"];
  carbsG: number;
  explanation: string;
}): AnalysisResult {
  return {
    ...initialAnalysis,
    stageText: "범위를 좁혔어요",
    summary: {
      caloriesKcal,
      calorieRange,
      proteinG: 34,
      carbsG,
      fatG: 22,
      confidence: 0.88,
      confidenceLabel: "medium_high",
      confidenceGroup: "certain"
    },
    primaryExplanation: explanation,
    uncertaintyReasons: [explanation],
    clarificationQuestion: undefined
  };
}

export function getClarifiedAnalysisForValue(value: string): AnalysisResult {
  return clarifiedAnalysisByRiceAmount[value] ?? initialAnalysis;
}

export function getRangeNarrowingForValue(value: string): RangeNarrowingResult | undefined {
  const clarified = clarifiedAnalysisByRiceAmount[value];
  if (!clarified) {
    return undefined;
  }
  const beforeWidth = initialAnalysis.summary.calorieRange.high - initialAnalysis.summary.calorieRange.low;
  const afterWidth = clarified.summary.calorieRange.high - clarified.summary.calorieRange.low;
  return {
    before: initialAnalysis.summary.calorieRange,
    after: clarified.summary.calorieRange,
    copy: `밥 양 확인으로 범위가 ${beforeWidth}kcal에서 ${afterWidth}kcal로 줄었어요.`
  };
}

export const clarifiedAnalysis: AnalysisResult = getClarifiedAnalysisForValue("one_bowl");
export const rangeNarrowing: RangeNarrowingResult = getRangeNarrowingForValue("one_bowl")!;

export function createSavedImpact(analysis: AnalysisResult, baseDashboard: DashboardTodayResponse = todayDashboard): SavedImpactViewModel {
  const nextMealId = `meal-${baseDashboard.meals.length + 1}`;
  const dashboard: DashboardTodayResponse = {
    ...baseDashboard,
    consumed: {
      caloriesKcal: baseDashboard.consumed.caloriesKcal + analysis.summary.caloriesKcal,
      proteinG: baseDashboard.consumed.proteinG + analysis.summary.proteinG,
      carbsG: baseDashboard.consumed.carbsG + analysis.summary.carbsG,
      fatG: baseDashboard.consumed.fatG + analysis.summary.fatG
    },
    meals: [
      {
        id: nextMealId,
        name: analysis.mealName,
        mealType: analysis.mealType,
        caloriesKcal: analysis.summary.caloriesKcal,
        confidenceLabel: analysis.summary.confidenceLabel
      },
      ...baseDashboard.meals
    ],
    nextMealGuidance: {
      ...baseDashboard.nextMealGuidance,
      explanation: "저녁은 단백질을 조금 더 챙기고 지방은 가볍게 가면 좋아요."
    }
  };

  return {
    confirmation: "기록했어요",
    remainingCaloriesKcal: dashboard.target.caloriesKcal - dashboard.consumed.caloriesKcal,
    nextMealSuggestion: "저녁은 단백질을 조금 더 챙기면 좋아요.",
    dashboard
  };
}

export const savedImpact: SavedImpactViewModel = createSavedImpact(clarifiedAnalysis);
