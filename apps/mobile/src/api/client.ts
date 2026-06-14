import type {
  ApiErrorDetail,
  ClientErrorKind,
  ApiAnalysisJobCreateResponse,
  ApiAnalysisJobResponse,
  ApiClarificationResponse,
  ApiDashboardTodayResponse,
  ApiSavedImpactResponse,
  MealType
} from "@cal-ai/shared";
import {
  mapApiAnalysisJob,
  mapApiClarificationResponse,
  mapApiDashboardToday,
  mapApiSavedImpactResponse,
  type AnalysisJobViewModel,
  type DashboardTodayResponse,
  type RangeNarrowingResult,
  type SavedImpactViewModel,
  type AnalysisResult
} from "@cal-ai/shared";
import { getApiBaseUrl } from "./config";

const API_ERROR_KINDS: ApiErrorDetail["kind"][] = ["provider", "validation", "not_found", "server", "unknown"];

export class ApiClientError extends Error {
  readonly status?: number;
  readonly code: string;
  readonly kind: ClientErrorKind;
  readonly retryable: boolean;
  readonly userMessage: string;

  constructor({
    message,
    status,
    code = "api_request_failed",
    kind = "http",
    retryable = false
  }: {
    message: string;
    status?: number;
    code?: string;
    kind?: ClientErrorKind;
    retryable?: boolean;
  }) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.kind = kind;
    this.retryable = retryable;
    this.userMessage = message;
  }
}

export interface CalAiApiClient {
  getTodayDashboard(): Promise<DashboardTodayResponse>;
  createAnalysisJob(input: { imageUploadId: string; mealType?: MealType; optionalNote?: string }): Promise<{ analysisJobId: string; status: "queued" }>;
  getAnalysisJob(jobId: string): Promise<AnalysisJobViewModel>;
  submitClarification(input: { jobId: string; questionKey: string; value: string }): Promise<{ result: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }>;
  saveMealLog(input: { analysisJobId: string; resultId: string; clarificationValue: string }): Promise<SavedImpactViewModel>;
}

export function createCalAiApiClient(baseUrl = getApiBaseUrl()): CalAiApiClient {
  const root = baseUrl.replace(/\/+$/, "");

  return {
    async getTodayDashboard() {
      return mapApiDashboardToday(await request<ApiDashboardTodayResponse>(root, "/v1/dashboard/today"));
    },
    async createAnalysisJob(input) {
      const response = await request<ApiAnalysisJobCreateResponse>(root, "/v1/analysis-jobs", {
        method: "POST",
        body: {
          image_upload_id: input.imageUploadId,
          meal_type: input.mealType ?? "lunch",
          optional_note: input.optionalNote ?? null
        }
      });
      return { analysisJobId: response.analysis_job_id, status: response.status };
    },
    async getAnalysisJob(jobId) {
      return mapApiAnalysisJob(await request<ApiAnalysisJobResponse>(root, `/v1/analysis-jobs/${encodeURIComponent(jobId)}`));
    },
    async submitClarification(input) {
      const response = await request<ApiClarificationResponse>(root, `/v1/analysis-jobs/${encodeURIComponent(input.jobId)}/clarifications`, {
        method: "POST",
        body: { answers: [{ question_key: input.questionKey, value: input.value }] }
      });
      const mapped = mapApiClarificationResponse(response);
      return { result: mapped.result, rangeNarrowing: mapped.rangeNarrowing };
    },
    async saveMealLog(input) {
      return mapApiSavedImpactResponse(
        await request<ApiSavedImpactResponse>(root, "/v1/meal-logs", {
          method: "POST",
          body: {
            analysis_job_id: input.analysisJobId,
            result_id: input.resultId,
            clarification_value: input.clarificationValue
          }
        })
      );
    }
  };
}

async function request<T>(root: string, path: string, options: { method?: "GET" | "POST"; body?: unknown } = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${root}${path}`, {
      method: options.method ?? "GET",
      headers: options.body ? { "Content-Type": "application/json" } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined
    });
  } catch {
    throw new ApiClientError({
      message: "API 서버에 연결할 수 없어요. FastAPI 서버가 켜져 있는지 확인한 뒤 다시 시도해 주세요.",
      code: "network_error",
      kind: "network",
      retryable: true
    });
  }

  if (!response.ok) {
    throw await createApiClientError(response);
  }

  return (await response.json()) as T;
}

async function createApiClientError(response: Response): Promise<ApiClientError> {
  const detail = await readApiErrorDetail(response);
  if (detail) {
    return new ApiClientError({
      message: detail.message,
      status: response.status,
      code: detail.code,
      kind: detail.kind,
      retryable: detail.retryable
    });
  }

  return new ApiClientError({
    message: defaultMessageForStatus(response.status),
    status: response.status,
    code: `http_${response.status}`,
    kind: defaultKindForStatus(response.status),
    retryable: response.status === 408 || response.status === 429 || response.status >= 500
  });
}

async function readApiErrorDetail(response: Response): Promise<ApiErrorDetail | undefined> {
  try {
    const body = (await response.json()) as { detail?: Partial<ApiErrorDetail> | string };
    if (!body.detail || typeof body.detail === "string") {
      return undefined;
    }
    const { code, message, retryable, kind } = body.detail;
    if (typeof code !== "string" || typeof message !== "string" || typeof retryable !== "boolean" || typeof kind !== "string") {
      return undefined;
    }
    if (!isApiErrorKind(kind)) {
      return undefined;
    }
    return { code, message, retryable, kind };
  } catch {
    return undefined;
  }
}

function isApiErrorKind(kind: string): kind is ApiErrorDetail["kind"] {
  return API_ERROR_KINDS.includes(kind as ApiErrorDetail["kind"]);
}

function defaultKindForStatus(status: number): ClientErrorKind {
  if (status === 404) {
    return "not_found";
  }
  if (status === 408 || status === 429) {
    return "timeout";
  }
  if (status >= 500) {
    return "server";
  }
  return "http";
}

function defaultMessageForStatus(status: number): string {
  if (status === 404) {
    return "요청한 분석 결과를 찾을 수 없어요. 처음부터 다시 시도해 주세요.";
  }
  if (status === 422) {
    return "요청 형식이 올바르지 않아요. 입력값을 확인해 주세요.";
  }
  if (status === 408 || status === 429 || status >= 500) {
    return "요청을 처리하지 못했어요. 잠시 뒤 다시 시도해 주세요.";
  }
  return "요청을 처리하지 못했어요. 입력값을 확인한 뒤 다시 시도해 주세요.";
}
