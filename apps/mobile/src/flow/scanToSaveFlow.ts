import type { AnalysisJobViewModel, AnalysisResult, ClientErrorKind, DashboardTodayResponse, MealType, RangeNarrowingResult, SavedImpactViewModel } from "@cal-ai/shared";
import { todayDashboard } from "../mockData";

export type RequestStatus = "idle" | "loading" | "success" | "error";
export type FlowErrorKind = ClientErrorKind;

export interface FlowError {
  kind: FlowErrorKind;
  title: string;
  message: string;
  code?: string;
  retryable: boolean;
  status?: number;
}

export type ScanToSaveCommand =
  | { type: "UPLOAD_IMAGE"; requestId: number; localAssetId: string; fileName: string; contentType: "image/jpeg" | "image/png" | "image/webp"; byteSize: number }
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
  | { type: "IMAGE_UPLOADED"; imageUploadId: string }
  | { type: "ANALYSIS_JOB_CREATED"; analysisJobId: string }
  | { type: "ANALYSIS_JOB_LOADED"; job: AnalysisJobViewModel }
  | { type: "OPEN_CLARIFICATION" }
  | { type: "CHOOSE_CLARIFICATION"; value: string }
  | { type: "CLARIFICATION_SUBMITTED"; analysis: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }
  | { type: "SKIP_CLARIFICATION" }
  | { type: "EDIT_RESULT" }
  | { type: "SAVE_MEAL" }
  | { type: "MEAL_SAVED"; impact: SavedImpactViewModel }
  | { type: "COMMAND_FAILED"; command: ScanToSaveCommand; message: string; code?: string; kind?: ClientErrorKind; retryable?: boolean; status?: number }
  | { type: "RETRY_LAST" }
  | { type: "RETURN_DASHBOARD" };

const LOCAL_DEMO_IMAGE_ASSET_ID = "local-demo-meal-preview";
const LOCAL_DEMO_IMAGE_FILE_NAME = "meal-preview.png";
const LOCAL_DEMO_IMAGE_BYTE_SIZE = 420_000;
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
        (requestId) => ({
          type: "UPLOAD_IMAGE",
          requestId,
          localAssetId: LOCAL_DEMO_IMAGE_ASSET_ID,
          fileName: LOCAL_DEMO_IMAGE_FILE_NAME,
          contentType: "image/png",
          byteSize: LOCAL_DEMO_IMAGE_BYTE_SIZE
        })
      );
    case "IMAGE_UPLOADED":
      return withCommand(
        { ...state, screen: "analyzing", status: "loading", error: undefined, pendingCommand: undefined },
        (requestId) => ({ type: "CREATE_ANALYSIS_JOB", requestId, imageUploadId: action.imageUploadId, mealType: "lunch" })
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
      if (state.screen !== "review" || state.status === "loading" || state.error?.retryable === false || !state.analysis || !state.analysisJobId) {
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
          kind: action.kind ?? "unknown",
          title: titleForApiError(action.kind ?? "unknown", action.code),
          message: action.message,
          code: action.code,
          retryable: action.retryable ?? true,
          status: action.status
        }
      };
    case "RETRY_LAST":
      if (!state.lastFailedCommand || state.status === "loading" || state.error?.retryable === false) {
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
        code: job.error?.code,
        retryable: true
      },
      lastFailedCommand: {
        type: "UPLOAD_IMAGE",
        requestId: state.requestSeq + 1,
        localAssetId: LOCAL_DEMO_IMAGE_ASSET_ID,
        fileName: LOCAL_DEMO_IMAGE_FILE_NAME,
        contentType: "image/png",
        byteSize: LOCAL_DEMO_IMAGE_BYTE_SIZE
      }
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
          code: "analysis_poll_timeout",
          retryable: true
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
      error: { kind: "job_failed", title: "분석 결과가 비어 있어요", message: "결과를 다시 불러와 주세요.", code: "missing_result", retryable: true },
      lastFailedCommand: { type: "FETCH_ANALYSIS_JOB", requestId: state.requestSeq + 1, jobId: job.id, pollAttempt: 0 }
    };
  }

  if (job.status === "completed" || !job.result.clarificationQuestion) {
    return { ...state, screen: "review", status: "success", analysisJobId: job.id, analysis: job.result, pollAttempt: 0, pendingCommand: undefined, error: undefined };
  }

  return { ...state, screen: "analyzing", status: "success", analysisJobId: job.id, analysis: job.result, pollAttempt: 0, pendingCommand: undefined, error: undefined };
}

function titleForApiError(kind: ClientErrorKind, code?: string): string {
  switch (kind) {
    case "network":
      return "API 서버에 연결할 수 없어요";
    case "provider":
      return titleForProviderError(code);
    case "validation":
      return "요청 형식을 확인해 주세요";
    case "not_found":
      return "결과를 찾을 수 없어요";
    case "server":
      return "서버에서 문제가 생겼어요";
    case "timeout":
      return "요청 시간이 길어지고 있어요";
    case "job_failed":
      return "분석을 완료하지 못했어요";
    case "http":
    case "unknown":
      return "요청을 처리하지 못했어요";
  }
}

function titleForProviderError(code?: string): string {
  switch (code) {
    case "analysis_provider_dry_run":
      return "실제 AI 호출은 꺼져 있어요";
    case "analysis_output_malformed":
      return "분석 결과를 확인하지 못했어요";
    case "analysis_provider_unavailable":
    default:
      return "분석 제공자를 사용할 수 없어요";
  }
}

function pollDelayMs(attempt: number): number {
  return Math.min(3000, 500 * attempt);
}

function withCommand(state: ScanToSaveState, createCommand: (requestId: number) => ScanToSaveCommand): ScanToSaveState {
  const requestId = state.requestSeq + 1;
  return { ...state, requestSeq: requestId, pendingCommand: createCommand(requestId) };
}
