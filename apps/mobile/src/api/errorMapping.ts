import { ApiClientError } from ".";
import type { FlowError } from "../flow/scanToSaveFlow";

export function onboardingFlowErrorFromUnknown(error: unknown): FlowError {
  return flowErrorFromUnknown(error, "온보딩을 저장하지 못했어요");
}

const coachErrorTitles = {
  refresh: "기록을 불러오지 못했어요",
  workoutPlan: "운동 계획을 만들지 못했어요",
  workoutSave: "운동 기록을 저장하지 못했어요",
  mealRepeat: "식사를 다시 기록하지 못했어요",
  mealDelete: "식사 기록을 삭제하지 못했어요",
  weightSave: "체중을 저장하지 못했어요",
  wellnessSave: "회복 상태를 저장하지 못했어요",
  bodySave: "신체 사진 기록을 저장하지 못했어요"
};

export function coachFlowErrorFromUnknown(error: unknown, action: keyof typeof coachErrorTitles): FlowError {
  return flowErrorFromUnknown(error, coachErrorTitles[action]);
}

function flowErrorFromUnknown(error: unknown, title: string): FlowError {
  if (error instanceof ApiClientError) {
    return {
      kind: error.kind,
      title,
      message: error.userMessage,
      code: error.code,
      retryable: error.retryable,
      status: error.status
    };
  }
  return { kind: "unknown", title, message: "잠시 뒤 다시 시도해 주세요.", code: "unknown_error", retryable: true };
}
