import type { DashboardTodayResponse } from "@cal-ai/shared";

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
