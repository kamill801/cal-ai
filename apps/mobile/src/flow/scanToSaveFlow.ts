import type { AnalysisResult, DashboardTodayResponse, RangeNarrowingResult, SavedImpactViewModel } from "@cal-ai/shared";
import { createSavedImpact, getClarifiedAnalysisForValue, getRangeNarrowingForValue, initialAnalysis, todayDashboard } from "../mockData";

export type ScanToSaveState =
  | { screen: "today"; dashboard: DashboardTodayResponse }
  | { screen: "analyzing"; dashboard: DashboardTodayResponse; analysis: AnalysisResult }
  | { screen: "clarifying"; dashboard: DashboardTodayResponse; analysis: AnalysisResult; rangeNarrowing?: RangeNarrowingResult; selectedValue?: string }
  | { screen: "review"; dashboard: DashboardTodayResponse; analysis: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }
  | { screen: "saved"; dashboard: DashboardTodayResponse; analysis: AnalysisResult; impact: SavedImpactViewModel };

export type ScanToSaveAction =
  | { type: "START_SCAN" }
  | { type: "OPEN_CLARIFICATION" }
  | { type: "CHOOSE_CLARIFICATION"; value: string }
  | { type: "SKIP_CLARIFICATION" }
  | { type: "EDIT_RESULT" }
  | { type: "SAVE_MEAL" }
  | { type: "RETURN_DASHBOARD" };

export function createInitialScanToSaveState(): ScanToSaveState {
  return { screen: "today", dashboard: todayDashboard };
}

export function scanToSaveReducer(state: ScanToSaveState, action: ScanToSaveAction): ScanToSaveState {
  switch (action.type) {
    case "START_SCAN":
      return { screen: "analyzing", dashboard: state.dashboard, analysis: initialAnalysis };
    case "OPEN_CLARIFICATION":
      if (state.screen !== "analyzing" && state.screen !== "review") {
        return state;
      }
      return { screen: "clarifying", dashboard: state.dashboard, analysis: initialAnalysis };
    case "CHOOSE_CLARIFICATION":
      if (state.screen !== "clarifying") {
        return state;
      }
      return {
        screen: "review",
        dashboard: state.dashboard,
        analysis: getClarifiedAnalysisForValue(action.value),
        rangeNarrowing: getRangeNarrowingForValue(action.value)
      };
    case "SKIP_CLARIFICATION":
      if (state.screen !== "clarifying") {
        return state;
      }
      return { screen: "review", dashboard: state.dashboard, analysis: initialAnalysis };
    case "EDIT_RESULT":
      if (state.screen !== "review") {
        return state;
      }
      return { screen: "clarifying", dashboard: state.dashboard, analysis: initialAnalysis };
    case "SAVE_MEAL":
      if (state.screen !== "review") {
        return state;
      }
      const impact = createSavedImpact(state.analysis, state.dashboard);
      return { screen: "saved", dashboard: impact.dashboard, analysis: state.analysis, impact };
    case "RETURN_DASHBOARD":
      return { screen: "today", dashboard: state.screen === "saved" ? state.impact.dashboard : state.dashboard };
    default:
      return state;
  }
}
