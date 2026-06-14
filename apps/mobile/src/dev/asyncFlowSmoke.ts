import type { AnalysisJobViewModel, AnalysisResult, SavedImpactViewModel } from "@cal-ai/shared";
import { createInitialScanToSaveState, scanToSaveReducer, type ScanToSaveState } from "../flow/scanToSaveFlow";
import { createSavedImpact, initialAnalysis } from "../mockData";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

function startAndCreateJob(): ScanToSaveState {
  const started = scanToSaveReducer(createInitialScanToSaveState(), { type: "START_SCAN" });
  assert(started.pendingCommand?.type === "CREATE_ANALYSIS_JOB", "start creates analysis job command");
  const created = scanToSaveReducer(started, { type: "ANALYSIS_JOB_CREATED", analysisJobId: "mock-lunch-001" });
  assert(created.pendingCommand?.type === "FETCH_ANALYSIS_JOB", "created job schedules fetch");
  return created;
}

function queuedJob(): AnalysisJobViewModel {
  return { id: "mock-lunch-001", status: "queued" };
}

export function runAsyncFlowSmoke(): void {
  const created = startAndCreateJob();
  const failedTransport = scanToSaveReducer(created, {
    type: "COMMAND_FAILED",
    command: created.pendingCommand!,
    message: "API 서버에 연결할 수 없어요.",
    code: "network_error"
  });
  assert(failedTransport.status === "error", "transport failure sets error status");
  assert(failedTransport.error?.kind === "transport", "transport failure is distinct");
  const retried = scanToSaveReducer(failedTransport, { type: "RETRY_LAST" });
  assert(retried.status === "loading" && retried.pendingCommand?.type === "FETCH_ANALYSIS_JOB", "retry replays failed command");

  const failedJob = scanToSaveReducer(created, {
    type: "ANALYSIS_JOB_LOADED",
    job: { id: "job-failed", status: "failed", error: { code: "provider_unavailable", message: "분석을 다시 시도해 주세요." } }
  });
  assert(failedJob.status === "error", "failed job sets error status");
  assert(failedJob.error?.kind === "job_failed", "failed job is distinct from transport");

  let polling = created;
  for (let attempt = 1; attempt <= 5; attempt += 1) {
    polling = scanToSaveReducer(polling, { type: "ANALYSIS_JOB_LOADED", job: queuedJob() });
    assert(polling.status === "loading", `queued attempt ${attempt} remains loading`);
    assert(polling.pendingCommand?.type === "FETCH_ANALYSIS_JOB", `queued attempt ${attempt} schedules fetch`);
    assert(polling.pendingCommand.delayMs !== undefined && polling.pendingCommand.delayMs > 0, `queued attempt ${attempt} has delay`);
  }
  const timedOut = scanToSaveReducer(polling, { type: "ANALYSIS_JOB_LOADED", job: queuedJob() });
  assert(timedOut.status === "error", "poll cap times out to error");
  assert(timedOut.error?.code === "analysis_poll_timeout", "poll timeout has user-safe code");

  const completed: AnalysisJobViewModel = { id: "mock-lunch-001", status: "needs_clarification", result: initialAnalysis };
  const loaded = scanToSaveReducer(created, { type: "ANALYSIS_JOB_LOADED", job: completed });
  assert(loaded.analysis?.id === "analysis-lunch-001", "job result loads analysis");
  const saving = scanToSaveReducer({ ...loaded, screen: "review", clarificationValue: "unknown" }, { type: "SAVE_MEAL" });
  assert(saving.status === "loading" && saving.pendingCommand?.type === "SAVE_MEAL", "save schedules API command");
  const failedSave = scanToSaveReducer(saving, {
    type: "COMMAND_FAILED",
    command: saving.pendingCommand!,
    message: "저장을 완료하지 못했어요.",
    code: "http_error"
  });
  assert(failedSave.screen === "review" && failedSave.status === "error", "save failure stays on review");
  assert(failedSave.lastFailedCommand?.type === "SAVE_MEAL", "save failure preserves retry command");
  const retriedSave = scanToSaveReducer(failedSave, { type: "RETRY_LAST" });
  assert(retriedSave.status === "loading" && retriedSave.pendingCommand?.type === "SAVE_MEAL", "save retry replays save command");
  const impact: SavedImpactViewModel = createSavedImpact(saving.analysis as AnalysisResult, saving.dashboard);
  const saved = scanToSaveReducer(retriedSave, { type: "MEAL_SAVED", impact });
  assert(saved.screen === "saved" && saved.impact?.confirmation === "기록했어요", "save success reaches saved screen");
}
