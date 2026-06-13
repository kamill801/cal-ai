import type { ApiAnalysisResult } from "@cal-ai/shared";
import { mapApiAnalysisResult } from "@cal-ai/shared";

const representativeApiAnalysis: ApiAnalysisResult = {
  id: "analysis-lunch-001",
  meal_name: "닭고기 덮밥",
  meal_type: "lunch",
  stage_text: "음식 구성 확인 중",
  summary: {
    calories_kcal: 700,
    calorie_range: { low: 620, midpoint: 700, high: 780 },
    protein_g: 34,
    carbs_g: 86,
    fat_g: 22,
    confidence: 0.72,
    confidence_label: "medium",
    confidence_group: "estimated"
  },
  detected_foods: [{ id: "food-rice", name: "흰밥", assumption_label: "양은 사진상 추정", confidence_label: "medium" }],
  uncertainty_reasons: ["밥 양과 소스가 범위를 크게 바꿀 수 있어요."],
  primary_explanation: "밥 양과 소스가 범위를 크게 바꿀 수 있어요.",
  clarification_question: {
    question_key: "rice_amount",
    question: "밥 양이 어느 정도였나요?",
    helper_text: "이것만 확인하면 범위가 꽤 줄어요.",
    type: "single_choice",
    options: [{ label: "한 공기", value: "one_bowl", helper_text: "보통 양이에요" }]
  }
};

const mapped = mapApiAnalysisResult(representativeApiAnalysis);

export const apiContractAudit = {
  mealName: mapped.mealName,
  caloriesKcal: mapped.summary.caloriesKcal,
  rangeHigh: mapped.summary.calorieRange.high,
  helperText: mapped.clarificationQuestion?.options[0]?.helperText,
  detectedAssumption: mapped.detectedFoods[0]?.assumptionLabel,
  expected: {
    mealName: "닭고기 덮밥",
    caloriesKcal: 700,
    rangeHigh: 780,
    helperText: "보통 양이에요",
    detectedAssumption: "양은 사진상 추정"
  }
} as const;
