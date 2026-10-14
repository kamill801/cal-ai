import { ApiClientError } from "../api";
import { coachFlowErrorFromUnknown, onboardingFlowErrorFromUnknown } from "../api/errorMapping";

const actionTitles = {
  refresh: "기록을 불러오지 못했어요",
  workoutPlan: "운동 계획을 만들지 못했어요",
  workoutSave: "운동 기록을 저장하지 못했어요",
  mealRepeat: "식사를 다시 기록하지 못했어요",
  mealDelete: "식사 기록을 삭제하지 못했어요",
  weightSave: "체중을 저장하지 못했어요",
  wellnessSave: "회복 상태를 저장하지 못했어요",
  bodySave: "신체 사진 기록을 저장하지 못했어요"
};

export function runErrorMappingSmoke(): void {
  for (const action of Object.keys(actionTitles) as (keyof typeof actionTitles)[]) {
    for (const detail of [
      { kind: "network" as const, code: "network_error", retryable: true },
      { kind: "validation" as const, code: "invalid_record", retryable: false },
      { kind: "server" as const, code: "persistence_unavailable", retryable: true }
    ]) {
      const mapped = coachFlowErrorFromUnknown(new ApiClientError({ ...detail, message: "안전한 오류 안내", status: 503 }), action);
      if (mapped.title !== actionTitles[action] || mapped.kind !== detail.kind || mapped.code !== detail.code || mapped.retryable !== detail.retryable || mapped.status !== 503 || mapped.message !== "안전한 오류 안내") {
        throw new Error(`coach ${action} lost error context or structured details`);
      }
    }
    const unknown = coachFlowErrorFromUnknown(new Error("private error detail must not appear"), action);
    if (unknown.title !== actionTitles[action] || unknown.message !== "잠시 뒤 다시 시도해 주세요." || unknown.code !== "unknown_error" || !unknown.retryable) {
      throw new Error(`coach ${action} unknown error leaked detail or lost context`);
    }
  }
  if (onboardingFlowErrorFromUnknown(new Error()).title !== "온보딩을 저장하지 못했어요") {
    throw new Error("onboarding error copy changed unexpectedly");
  }
  console.log("action-specific error mapping smoke passed (33 cases)");
}
