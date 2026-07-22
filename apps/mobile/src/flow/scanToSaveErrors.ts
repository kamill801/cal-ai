import type { ClientErrorKind } from "@cal-ai/shared";

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

export function titleForApiError(kind: ClientErrorKind, code?: string): string {
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
