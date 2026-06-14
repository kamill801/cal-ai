import type { AnalysisJobViewModel, AnalysisResult, DashboardTodayResponse, MealType, RangeNarrowingResult, SavedImpactViewModel } from "@cal-ai/shared";
import { todayDashboard } from "../mockData";

export type RequestStatus = "idle" | "loading" | "success" | "error";
export type FlowErrorKind = "transport" | "job_failed";

export interface FlowError {
  kind: FlowErrorKind;
  title: string;
  message: string;
  code?: string;
}

export type ScanToSaveCommand =
  | { type: "CREATE_ANALYSIS_JOB"; requestId: number; imageUploadId: string; mealType: MealType }
  | { type: "FETCH_ANALYSIS_JOB"; requestId: number; jobId: string; pollAttempt: number; delayMs?: number }
  | { type: "SUBMIT_CLARIFICATION"; requestId: number; jobId: string; questionKey: string; value: string }
  | { type: "SAVE_MEAL"; requestId: number; analysisJobId: string; resultId: string; clarificationValue: string };

export interface ScanToSaveState {
  screen: "today" | "analyzing" | "clarifying" | "review" | "saved";
  dashboard: DashboardTodayResponse;
  status: RequestStatus;
  analysis?: AnalysisResult;
  rangeNarrowing?: RangeNarrowingResult;
  selectedValue?: string;
  clarificationValue?: string;
  impact?: SavedImpactViewModel;
  analysisJobId?: string;
  error?: FlowError;
  pendingCommand?: ScanToSaveCommand;
  lastFailedCommand?: ScanToSaveCommand;
  requestSeq: number;
  pollAttempt: number;
}

export type ScanToSaveAction =
  | { type: "START_SCAN" }
  | { type: "ANALYSIS_JOB_CREATED"; analysisJobId: string }
  | { type: "ANALYSIS_JOB_LOADED"; job: AnalysisJobViewModel }
  | { type: "OPEN_CLARIFICATION" }
  | { type: "CHOOSE_CLARIFICATION"; value: string }
  | { type: "CLARIFICATION_SUBMITTED"; analysis: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }
  | { type: "SKIP_CLARIFICATION" }
  | { type: "EDIT_RESULT" }
  | { type: "SAVE_MEAL" }
  | { type: "MEAL_SAVED"; impact: SavedImpactViewModel }
  | { type: "COMMAND_FAILED"; command: ScanToSaveCommand; message: string; code?: string }
  | { type: "RETRY_LAST" }
  | { type: "RETURN_DASHBOARD" };

const LOCAL_DEMO_IMAGE_UPLOAD_ID = "local-demo-meal-preview";
const MAX_ANALYSIS_POLL_ATTEMPTS = 5;

export function createInitialScanToSaveState(): ScanToSaveState {
  return { screen: "today", dashboard: todayDashboard, status: "idle", requestSeq: 0, pollAttempt: 0 };
}

export function scanToSaveReducer(state: ScanToSaveState, action: ScanToSaveAction): ScanToSaveState {
  switch (action.type) {
    case "START_SCAN":
      if (state.status === "loading") {
        return state;
      }
      return withCommand(
        {
          ...state,
          screen: "analyzing",
          status: "loading",
          analysis: undefined,
          rangeNarrowing: undefined,
          selectedValue: undefined,
          clarificationValue: undefined,
          impact: undefined,
          error: undefined,
          lastFailedCommand: undefined,
          analysisJobId: undefined
        },
        (requestId) => ({ type: "CREATE_ANALYSIS_JOB", requestId, imageUploadId: LOCAL_DEMO_IMAGE_UPLOAD_ID, mealType: "lunch" })
      );
    case "ANALYSIS_JOB_CREATED":
      return withCommand(
        { ...state, screen: "analyzing", status: "loading", analysisJobId: action.analysisJobId, error: undefined, pendingCommand: undefined },
        (requestId) => ({ type: "FETCH_ANALYSIS_JOB", requestId, jobId: action.analysisJobId, pollAttempt: 0 })
      );
    case "ANALYSIS_JOB_LOADED":
      return applyLoadedJob(state, action.job);
    case "OPEN_CLARIFICATION":
      if ((state.screen !== "analyzing" && state.screen !== "review") || !state.analysis) {
        return state;
      }
      if (!state.analysis.clarificationQuestion) {
        return { ...state, screen: "review", status: "success", error: undefined };
      }
      return { ...state, screen: "clarifying", status: "idle", error: undefined };
    case "CHOOSE_CLARIFICATION":
      if (state.screen !== "clarifying" || state.status === "loading" || !state.analysis?.clarificationQuestion || !state.analysisJobId) {
        return state;
      }
      return withCommand(
        { ...state, status: "loading", selectedValue: action.value, error: undefined, lastFailedCommand: undefined },
        (requestId) => ({
          type: "SUBMIT_CLARIFICATION",
          requestId,
          jobId: state.analysisJobId!,
          questionKey: state.analysis!.clarificationQuestion!.questionKey,
          value: action.value
        })
      );
    case "CLARIFICATION_SUBMITTED":
      return {
        ...state,
        screen: "review",
        status: "success",
        analysis: action.analysis,
        rangeNarrowing: action.rangeNarrowing,
        clarificationValue: state.selectedValue ?? "unknown",
        pendingCommand: undefined,
        error: undefined
      };
    case "SKIP_CLARIFICATION":
      if (state.screen !== "clarifying" || !state.analysis || state.status === "loading") {
        return state;
      }
      return { ...state, screen: "review", status: "success", clarificationValue: "unknown", selectedValue: undefined, error: undefined };
    case "EDIT_RESULT":
      if (state.screen !== "review" || !state.analysis) {
        return state;
      }
      return state.analysis.clarificationQuestion ? { ...state, screen: "clarifying", status: "idle", error: undefined } : state;
    case "SAVE_MEAL":
      if (state.screen !== "review" || state.status === "loading" || !state.analysis || !state.analysisJobId) {
        return state;
      }
      return withCommand(
        { ...state, screen: "review", status: "loading", error: undefined, lastFailedCommand: undefined },
        (requestId) => ({
          type: "SAVE_MEAL",
          requestId,
          analysisJobId: state.analysisJobId!,
          resultId: state.analysis!.id,
          clarificationValue: state.clarificationValue ?? state.selectedValue ?? "unknown"
        })
      );
    case "MEAL_SAVED":
      return {
        ...state,
        screen: "saved",
        status: "success",
        dashboard: action.impact.dashboard,
        impact: action.impact,
        pendingCommand: undefined,
        error: undefined
      };
    case "COMMAND_FAILED":
      return {
        ...state,
        screen: state.screen,
        status: "error",
        pendingCommand: undefined,
        lastFailedCommand: action.command,
        error: {
          kind: "transport",
          title: "연결에 실패했어요",
          message: action.message,
          code: action.code
        }
      };
    case "RETRY_LAST":
      if (!state.lastFailedCommand || state.status === "loading") {
        return state;
      }
      return withCommand(
        { ...state, status: "loading", pollAttempt: state.lastFailedCommand.type === "FETCH_ANALYSIS_JOB" ? 0 : state.pollAttempt, error: undefined, pendingCommand: undefined },
        (requestId) => ({ ...state.lastFailedCommand!, requestId, ...(state.lastFailedCommand!.type === "FETCH_ANALYSIS_JOB" ? { pollAttempt: 0, delayMs: undefined } : {}) })
      );
    case "RETURN_DASHBOARD":
      return { screen: "today", dashboard: state.screen === "saved" && state.impact ? state.impact.dashboard : state.dashboard, status: "idle", requestSeq: state.requestSeq, pollAttempt: 0 };
    default:
      return state;
  }
}

function applyLoadedJob(state: ScanToSaveState, job: AnalysisJobViewModel): ScanToSaveState {
  if (job.status === "failed") {
    return {
      ...state,
      screen: "analyzing",
      status: "error",
      analysisJobId: job.id,
      analysis: undefined,
      pendingCommand: undefined,
      error: {
        kind: "job_failed",
        title: "분석을 완료하지 못했어요",
        message: job.error?.message ?? "사진 분석 중 문제가 생겼어요. 다시 시도해 주세요.",
        code: job.error?.code
      },
      lastFailedCommand: { type: "CREATE_ANALYSIS_JOB", requestId: state.requestSeq + 1, imageUploadId: LOCAL_DEMO_IMAGE_UPLOAD_ID, mealType: "lunch" }
    };
  }

  if (!job.result && (job.status === "queued" || job.status === "analyzing")) {
    const nextAttempt = state.pollAttempt + 1;
    if (nextAttempt > MAX_ANALYSIS_POLL_ATTEMPTS) {
      return {
        ...state,
        screen: "analyzing",
        status: "error",
        analysisJobId: job.id,
        pendingCommand: undefined,
        error: {
          kind: "job_failed",
          title: "분석 시간이 길어지고 있어요",
          message: "잠시 뒤 다시 시도해 주세요.",
          code: "analysis_poll_timeout"
        },
        lastFailedCommand: { type: "FETCH_ANALYSIS_JOB", requestId: state.requestSeq + 1, jobId: job.id, pollAttempt: 0 }
      };
    }

    return withCommand(
      { ...state, screen: "analyzing", status: "loading", analysisJobId: job.id, pollAttempt: nextAttempt, pendingCommand: undefined, error: undefined },
      (requestId) => ({ type: "FETCH_ANALYSIS_JOB", requestId, jobId: job.id, pollAttempt: nextAttempt, delayMs: pollDelayMs(nextAttempt) })
    );
  }

  if (!job.result) {
    return {
      ...state,
      status: "error",
      pendingCommand: undefined,
      error: { kind: "job_failed", title: "분석 결과가 비어 있어요", message: "결과를 다시 불러와 주세요.", code: "missing_result" },
      lastFailedCommand: { type: "FETCH_ANALYSIS_JOB", requestId: state.requestSeq + 1, jobId: job.id, pollAttempt: 0 }
    };
  }

  if (job.status === "completed" || !job.result.clarificationQuestion) {
    return { ...state, screen: "review", status: "success", analysisJobId: job.id, analysis: job.result, pollAttempt: 0, pendingCommand: undefined, error: undefined };
  }

  return { ...state, screen: "analyzing", status: "success", analysisJobId: job.id, analysis: job.result, pollAttempt: 0, pendingCommand: undefined, error: undefined };
}

function pollDelayMs(attempt: number): number {
  return Math.min(3000, 500 * attempt);
}

function withCommand(state: ScanToSaveState, createCommand: (requestId: number) => ScanToSaveCommand): ScanToSaveState {
  const requestId = state.requestSeq + 1;
  return { ...state, requestSeq: requestId, pendingCommand: createCommand(requestId) };
}
