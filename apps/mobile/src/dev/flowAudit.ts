import type { AnalysisJobViewModel, AnalysisResult, RangeNarrowingResult, SavedImpactViewModel } from "@cal-ai/shared";
import { createInitialScanToSaveState, scanToSaveReducer, type ScanToSaveState } from "../flow/scanToSaveFlow";
import { createSavedImpact, getClarifiedAnalysisForValue, getRangeNarrowingForValue, initialAnalysis } from "../mockData";

function loadedInitial(state: ScanToSaveState): ScanToSaveState {
  const created = scanToSaveReducer(state, { type: "ANALYSIS_JOB_CREATED", analysisJobId: "mock-lunch-001" });
  const job: AnalysisJobViewModel = { id: "mock-lunch-001", status: "needs_clarification", result: initialAnalysis };
  return scanToSaveReducer(created, { type: "ANALYSIS_JOB_LOADED", job });
}

function completeSave(value: string, baseState: ScanToSaveState = createInitialScanToSaveState()): ScanToSaveState {
  const started = scanToSaveReducer(baseState, { type: "START_SCAN" });
  const analyzing = loadedInitial(started);
  const clarifying = scanToSaveReducer(analyzing, { type: "OPEN_CLARIFICATION" });
  const choosing = scanToSaveReducer(clarifying, { type: "CHOOSE_CLARIFICATION", value });
  const analysis: AnalysisResult = value === "unknown" ? initialAnalysis : getClarifiedAnalysisForValue(value);
  const rangeNarrowing: RangeNarrowingResult | undefined = getRangeNarrowingForValue(value);
  const reviewed = scanToSaveReducer(choosing, { type: "CLARIFICATION_SUBMITTED", analysis, rangeNarrowing });
  const saving = scanToSaveReducer(reviewed, { type: "SAVE_MEAL" });
  const impact: SavedImpactViewModel = createSavedImpact(analysis, saving.dashboard);
  return scanToSaveReducer(saving, { type: "MEAL_SAVED", impact });
}

const halfBowlSaved = completeSave("half_bowl");
const clarifiedSaved = completeSave("one_bowl");
const largeBowlSaved = completeSave("large_bowl");
const skippedSaved = completeSave("unknown");
const returnedAfterFirstSave = scanToSaveReducer(clarifiedSaved, { type: "RETURN_DASHBOARD" });
const secondSaved = completeSave("half_bowl", returnedAfterFirstSave);

function savedAnalysisCalories(state: ScanToSaveState): number {
  return state.screen === "saved" && state.analysis ? state.analysis.summary.caloriesKcal : 0;
}

function savedRemaining(state: ScanToSaveState): number {
  return state.screen === "saved" && state.impact ? state.impact.remainingCaloriesKcal : 0;
}

export const flowAudit = {
  halfBowlCalories: savedAnalysisCalories(halfBowlSaved),
  halfBowlRemaining: savedRemaining(halfBowlSaved),
  clarifiedCalories: savedAnalysisCalories(clarifiedSaved),
  clarifiedRemaining: savedRemaining(clarifiedSaved),
  largeBowlCalories: savedAnalysisCalories(largeBowlSaved),
  largeBowlRemaining: savedRemaining(largeBowlSaved),
  skippedCalories: savedAnalysisCalories(skippedSaved),
  skippedRemaining: savedRemaining(skippedSaved),
  secondSaveConsumed: secondSaved.screen === "saved" && secondSaved.impact ? secondSaved.impact.dashboard.consumed.caloriesKcal : 0,
  secondSaveMealCount: secondSaved.screen === "saved" && secondSaved.impact ? secondSaved.impact.dashboard.meals.length : 0,
  secondSaveTopMealIds: secondSaved.screen === "saved" && secondSaved.impact ? secondSaved.impact.dashboard.meals.slice(0, 2).map((meal) => meal.id).join(",") : "",
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
