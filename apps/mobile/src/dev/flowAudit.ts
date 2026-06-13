import { createInitialScanToSaveState, scanToSaveReducer } from "../flow/scanToSaveFlow";

const started = scanToSaveReducer(createInitialScanToSaveState(), { type: "START_SCAN" });
const halfBowl = scanToSaveReducer(scanToSaveReducer(started, { type: "OPEN_CLARIFICATION" }), {
  type: "CHOOSE_CLARIFICATION",
  value: "half_bowl"
});
const halfBowlSaved = scanToSaveReducer(halfBowl, { type: "SAVE_MEAL" });

const clarified = scanToSaveReducer(scanToSaveReducer(started, { type: "OPEN_CLARIFICATION" }), {
  type: "CHOOSE_CLARIFICATION",
  value: "one_bowl"
});
const clarifiedSaved = scanToSaveReducer(clarified, { type: "SAVE_MEAL" });

const largeBowl = scanToSaveReducer(scanToSaveReducer(started, { type: "OPEN_CLARIFICATION" }), {
  type: "CHOOSE_CLARIFICATION",
  value: "large_bowl"
});
const largeBowlSaved = scanToSaveReducer(largeBowl, { type: "SAVE_MEAL" });

const skipped = scanToSaveReducer(scanToSaveReducer(started, { type: "OPEN_CLARIFICATION" }), {
  type: "CHOOSE_CLARIFICATION",
  value: "unknown"
});
const skippedSaved = scanToSaveReducer(skipped, { type: "SAVE_MEAL" });

const returnedAfterFirstSave = scanToSaveReducer(clarifiedSaved, { type: "RETURN_DASHBOARD" });
const secondStarted = scanToSaveReducer(returnedAfterFirstSave, { type: "START_SCAN" });
const secondReview = scanToSaveReducer(scanToSaveReducer(secondStarted, { type: "OPEN_CLARIFICATION" }), {
  type: "CHOOSE_CLARIFICATION",
  value: "half_bowl"
});
const secondSaved = scanToSaveReducer(secondReview, { type: "SAVE_MEAL" });

export const flowAudit = {
  halfBowlCalories: halfBowlSaved.screen === "saved" ? halfBowlSaved.analysis.summary.caloriesKcal : 0,
  halfBowlRemaining: halfBowlSaved.screen === "saved" ? halfBowlSaved.impact.remainingCaloriesKcal : 0,
  clarifiedCalories: clarifiedSaved.screen === "saved" ? clarifiedSaved.analysis.summary.caloriesKcal : 0,
  clarifiedRemaining: clarifiedSaved.screen === "saved" ? clarifiedSaved.impact.remainingCaloriesKcal : 0,
  largeBowlCalories: largeBowlSaved.screen === "saved" ? largeBowlSaved.analysis.summary.caloriesKcal : 0,
  largeBowlRemaining: largeBowlSaved.screen === "saved" ? largeBowlSaved.impact.remainingCaloriesKcal : 0,
  skippedCalories: skippedSaved.screen === "saved" ? skippedSaved.analysis.summary.caloriesKcal : 0,
  skippedRemaining: skippedSaved.screen === "saved" ? skippedSaved.impact.remainingCaloriesKcal : 0,
  secondSaveConsumed: secondSaved.screen === "saved" ? secondSaved.impact.dashboard.consumed.caloriesKcal : 0,
  secondSaveMealCount: secondSaved.screen === "saved" ? secondSaved.impact.dashboard.meals.length : 0,
  secondSaveTopMealIds: secondSaved.screen === "saved" ? secondSaved.impact.dashboard.meals.slice(0, 2).map((meal) => meal.id).join(",") : "",
  expected: {
    halfBowlCalories: 595,
    halfBowlRemaining: 585,
    clarifiedCalories: 675,
    clarifiedRemaining: 505,
    largeBowlCalories: 765,
    largeBowlRemaining: 415,
    skippedCalories: 700,
    skippedRemaining: 480,
    secondSaveConsumed: 1940,
    secondSaveMealCount: 4,
    secondSaveTopMealIds: "meal-4,meal-3"
  }
} as const;
