import type {
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

export class ApiClientError extends Error {
  readonly status?: number;
  readonly code: string;
  readonly userMessage: string;

  constructor({ message, status, code = "api_request_failed" }: { message: string; status?: number; code?: string }) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
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
    throw new ApiClientError({ message: "API 서버에 연결할 수 없어요. FastAPI 서버가 켜져 있는지 확인한 뒤 다시 시도해 주세요.", code: "network_error" });
  }

  if (!response.ok) {
    throw new ApiClientError({ message: "요청을 처리하지 못했어요. 잠시 뒤 다시 시도해 주세요.", status: response.status, code: "http_error" });
  }

  return (await response.json()) as T;
}
