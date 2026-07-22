import { ApiClientError } from ".";
import type { FlowError } from "../flow/scanToSaveFlow";

export function onboardingFlowErrorFromUnknown(error: unknown): FlowError {
  if (error instanceof ApiClientError) {
    return {
      kind: error.kind,
      title: "온보딩을 저장하지 못했어요",
      message: error.userMessage,
      code: error.code,
      retryable: error.retryable,
      status: error.status
    };
  }
  return { kind: "unknown", title: "온보딩을 저장하지 못했어요", message: "잠시 뒤 다시 시도해 주세요.", code: "unknown_error", retryable: true };
}
