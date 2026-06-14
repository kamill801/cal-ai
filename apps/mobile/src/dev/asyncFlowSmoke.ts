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
  assert(started.pendingCommand?.type === "UPLOAD_IMAGE", "start creates image upload command");
  const uploaded = scanToSaveReducer(started, { type: "IMAGE_UPLOADED", imageUploadId: "local-upload-local-demo-meal-preview" });
  assert(uploaded.pendingCommand?.type === "CREATE_ANALYSIS_JOB", "uploaded image schedules analysis job command");
  const created = scanToSaveReducer(uploaded, { type: "ANALYSIS_JOB_CREATED", analysisJobId: "mock-lunch-001" });
  assert(created.pendingCommand?.type === "FETCH_ANALYSIS_JOB", "created job schedules fetch");
  return created;
}

function queuedJob(): AnalysisJobViewModel {
  return { id: "mock-lunch-001", status: "queued" };
}

export function runAsyncFlowSmoke(): void {
  const uploading = scanToSaveReducer(createInitialScanToSaveState(), { type: "START_SCAN" });
  const failedUpload = scanToSaveReducer(uploading, {
    type: "COMMAND_FAILED",
    command: uploading.pendingCommand!,
    message: "이미지를 업로드하지 못했어요.",
    code: "image_upload_failed",
    kind: "server",
    retryable: true,
    status: 503
  });
  assert(failedUpload.error?.code === "image_upload_failed", "upload failure preserves code");
  const retriedUpload = scanToSaveReducer(failedUpload, { type: "RETRY_LAST" });
  assert(retriedUpload.status === "loading" && retriedUpload.pendingCommand?.type === "UPLOAD_IMAGE", "upload retry replays upload command");

  const created = startAndCreateJob();
  const failedTransport = scanToSaveReducer(created, {
    type: "COMMAND_FAILED",
    command: created.pendingCommand!,
    message: "API 서버에 연결할 수 없어요.",
    code: "network_error",
    kind: "network",
    retryable: true
  });
  assert(failedTransport.status === "error", "transport failure sets error status");
  assert(failedTransport.error?.kind === "network", "network failure is distinct");
  assert(failedTransport.error?.retryable === true, "network failure is retryable");
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
    code: "validation_error",
    kind: "validation",
    retryable: false,
    status: 422
  });
  assert(failedSave.screen === "review" && failedSave.status === "error", "save failure stays on review");
  assert(failedSave.error?.kind === "validation" && failedSave.error.retryable === false, "validation failure is non-retryable");
  assert(failedSave.lastFailedCommand?.type === "SAVE_MEAL", "save failure preserves retry command");
  const blockedValidationRetry = scanToSaveReducer(failedSave, { type: "RETRY_LAST" });
  assert(blockedValidationRetry === failedSave, "non-retryable save failure blocks retry command");
  const blockedValidationResave = scanToSaveReducer(failedSave, { type: "SAVE_MEAL" });
  assert(blockedValidationResave === failedSave, "non-retryable save failure blocks repeated save command");
  const retryableSaveError = scanToSaveReducer(saving, {
    type: "COMMAND_FAILED",
    command: saving.pendingCommand!,
    message: "저장을 완료하지 못했어요.",
    code: "analysis_output_malformed",
    kind: "provider",
    retryable: true,
    status: 503
  });
  assert(retryableSaveError.error?.title === "분석 결과를 확인하지 못했어요", "malformed output has distinct provider title");
  const retriedSave = scanToSaveReducer(retryableSaveError, { type: "RETRY_LAST" });
  assert(retriedSave.status === "loading" && retriedSave.pendingCommand?.type === "SAVE_MEAL", "retryable save failure replays save command");
  const dryRunSaveError = scanToSaveReducer(saving, {
    type: "COMMAND_FAILED",
    command: saving.pendingCommand!,
    message: "실제 AI 분석 호출은 아직 비활성화되어 있어요.",
    code: "analysis_provider_dry_run",
    kind: "provider",
    retryable: false,
    status: 503
  });
  assert(dryRunSaveError.error?.title === "실제 AI 호출은 꺼져 있어요", "dry-run provider error has distinct title");
  assert(scanToSaveReducer(dryRunSaveError, { type: "RETRY_LAST" }) === dryRunSaveError, "dry-run provider error blocks retry");
  const impact: SavedImpactViewModel = createSavedImpact(saving.analysis as AnalysisResult, saving.dashboard);
  const saved = scanToSaveReducer(retriedSave, { type: "MEAL_SAVED", impact });
  assert(saved.screen === "saved" && saved.impact?.confirmation === "기록했어요", "save success reaches saved screen");
}
