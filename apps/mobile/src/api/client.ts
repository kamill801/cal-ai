import type {
  ApiErrorDetail,
  ClientErrorKind,
  ApiAnalysisJobCreateResponse,
  ApiAnalysisJobResponse,
  ApiClarificationResponse,
  ApiDashboardTodayResponse,
  ApiImageUploadPresignResponse,
  ApiImageUploadResponse,
  ApiOnboardingResponse,
  OnboardingRequest,
  ApiSavedImpactResponse,
  ApiBodyCheckIn,
  ApiCoachDashboard,
  ApiProgressSummary,
  ApiWeightLog,
  ApiWeeklyCoachReport,
  ApiWellnessCheckIn,
  ApiWorkoutPlan,
  ApiWorkoutSession,
  ImageContentType,
  MealType
} from "@cal-ai/shared";
import {
  mapApiAnalysisJob,
  mapApiClarificationResponse,
  mapApiDashboardToday,
  mapApiImageUploadPresign,
  mapApiImageUpload,
  mapApiOnboardingResponse,
  mapApiSavedImpactResponse,
  mapApiBodyCheckIn,
  mapApiCoachDashboard,
  mapApiProgress,
  mapApiWeightLog,
  mapApiWeeklyCoach,
  mapApiWellness,
  mapApiWorkoutPlan,
  mapApiWorkoutSession,
  type AnalysisJobViewModel,
  type DashboardTodayResponse,
  type ImageUploadPresignViewModel,
  type ImageUploadViewModel,
  type OnboardingResponse,
  type RangeNarrowingResult,
  type SavedImpactViewModel,
  type AnalysisResult,
  type BodyCheckIn,
  type CoachDashboard,
  type ProgressSummary,
  type WeightLog,
  type WeeklyCoachReport,
  type WellnessCheckIn,
  type WorkoutPlan,
  type WorkoutSession
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
  createOnboarding(input: OnboardingRequest): Promise<OnboardingResponse>;
  uploadImage(input: { localAssetId: string; fileName: string; contentType: ImageContentType; byteSize: number; simulateFailure?: boolean }): Promise<ImageUploadViewModel>;
  presignImageUpload(input: { localAssetId: string; fileName: string; contentType: ImageContentType; byteSize: number }): Promise<ImageUploadPresignViewModel>;
  completeImageUpload(input: {
    imageUploadId: string;
    objectKey: string;
    localAssetId?: string;
    fileName: string;
    contentType: ImageContentType;
    byteSize: number;
    etag?: string;
  }): Promise<ImageUploadViewModel>;
  createAnalysisJob(input: { imageUploadId: string; mealType?: MealType; optionalNote?: string }): Promise<{ analysisJobId: string; status: "queued" }>;
  getAnalysisJob(jobId: string): Promise<AnalysisJobViewModel>;
  submitClarification(input: { jobId: string; questionKey: string; value: string }): Promise<{ result: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }>;
  saveMealLog(input: { analysisJobId: string; resultId: string; clarificationValue: string; profileId?: string; loggedOn?: string }): Promise<SavedImpactViewModel>;
  getCoachDashboard(profileId: string, loggedOn?: string): Promise<CoachDashboard>;
  logWeight(profileId: string, input: { loggedOn: string; weightKg: number }): Promise<WeightLog>;
  logWellness(profileId: string, input: { loggedOn: string; energy: number; sleepQuality: number; soreness: number; note?: string }): Promise<WellnessCheckIn>;
  createBodyCheckIn(profileId: string, input: { capturedOn: string; imageUploadId: string; view: "front" | "side" | "back" }): Promise<BodyCheckIn>;
  generateWorkoutPlan(profileId: string): Promise<WorkoutPlan>;
  getWorkoutPlan(profileId: string): Promise<WorkoutPlan>;
  logWorkoutSession(profileId: string, input: { planId: string; workoutDayId: string; performedOn: string; durationMinutes: number; completedExerciseIds: string[]; sessionRpe: number }): Promise<WorkoutSession>;
  getProgress(profileId: string): Promise<ProgressSummary>;
  getWeeklyCoach(profileId: string): Promise<WeeklyCoachReport>;
}

export function createCalAiApiClient(baseUrl = getApiBaseUrl()): CalAiApiClient {
  const root = baseUrl.replace(/\/+$/, "");

  return {
    async getTodayDashboard() {
      return mapApiDashboardToday(await request<ApiDashboardTodayResponse>(root, "/v1/dashboard/today"));
    },
    async createOnboarding(input) {
      return mapApiOnboardingResponse(
        await request<ApiOnboardingResponse>(root, "/v1/onboarding", {
          method: "POST",
          body: {
            age: input.age,
            sex: input.sex,
            height_cm: input.heightCm,
            current_weight_kg: input.currentWeightKg,
            target_weight_kg: input.targetWeightKg ?? null,
            goal_type: input.goalType,
            activity_level: input.activityLevel,
            training_frequency: input.trainingFrequency ?? null,
            experience_level: input.experienceLevel ?? "beginner",
            available_equipment: input.availableEquipment ?? ["gym"],
            session_minutes: input.sessionMinutes ?? 60
          }
        })
      );
    },
    async uploadImage(input) {
      return mapApiImageUpload(
        await request<ApiImageUploadResponse>(root, "/v1/image-uploads", {
          method: "POST",
          body: {
            local_asset_id: input.localAssetId,
            file_name: input.fileName,
            content_type: input.contentType,
            byte_size: input.byteSize,
            simulate_failure: input.simulateFailure ?? false
          }
        })
      );
    },
    async presignImageUpload(input) {
      return mapApiImageUploadPresign(
        await request<ApiImageUploadPresignResponse>(root, "/image-uploads/presign", {
          method: "POST",
          body: {
            local_asset_id: input.localAssetId,
            file_name: input.fileName,
            content_type: input.contentType,
            byte_size: input.byteSize
          }
        })
      );
    },
    async completeImageUpload(input) {
      return mapApiImageUpload(
        await request<ApiImageUploadResponse>(root, "/image-uploads/complete", {
          method: "POST",
          body: {
            image_upload_id: input.imageUploadId,
            object_key: input.objectKey,
            local_asset_id: input.localAssetId ?? "mobile-upload",
            file_name: input.fileName,
            content_type: input.contentType,
            byte_size: input.byteSize,
            etag: input.etag ?? null
          }
        })
      );
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
            clarification_value: input.clarificationValue,
            profile_id: input.profileId ?? null,
            logged_on: input.loggedOn ?? null
          }
        })
      );
    },
    async getCoachDashboard(profileId, loggedOn) {
      const query = loggedOn ? `?logged_on=${encodeURIComponent(loggedOn)}` : "";
      return mapApiCoachDashboard(await request<ApiCoachDashboard>(root, `/v1/profiles/${encodeURIComponent(profileId)}/dashboard/today${query}`));
    },
    async logWeight(profileId, input) {
      return mapApiWeightLog(
        await request<ApiWeightLog>(root, `/v1/profiles/${encodeURIComponent(profileId)}/weight-logs`, {
          method: "POST",
          body: { logged_on: input.loggedOn, weight_kg: input.weightKg }
        })
      );
    },
    async logWellness(profileId, input) {
      return mapApiWellness(
        await request<ApiWellnessCheckIn>(root, `/v1/profiles/${encodeURIComponent(profileId)}/wellness-check-ins`, {
          method: "POST",
          body: { logged_on: input.loggedOn, energy: input.energy, sleep_quality: input.sleepQuality, soreness: input.soreness, note: input.note ?? null }
        })
      );
    },
    async createBodyCheckIn(profileId, input) {
      return mapApiBodyCheckIn(
        await request<ApiBodyCheckIn>(root, `/v1/profiles/${encodeURIComponent(profileId)}/body-check-ins`, {
          method: "POST",
          body: { captured_on: input.capturedOn, image_upload_id: input.imageUploadId, view: input.view }
        })
      );
    },
    async generateWorkoutPlan(profileId) {
      return mapApiWorkoutPlan(
        await request<ApiWorkoutPlan>(root, `/v1/profiles/${encodeURIComponent(profileId)}/workout-plans/generate`, { method: "POST" })
      );
    },
    async getWorkoutPlan(profileId) {
      return mapApiWorkoutPlan(await request<ApiWorkoutPlan>(root, `/v1/profiles/${encodeURIComponent(profileId)}/workout-plan`));
    },
    async logWorkoutSession(profileId, input) {
      return mapApiWorkoutSession(
        await request<ApiWorkoutSession>(root, `/v1/profiles/${encodeURIComponent(profileId)}/workout-sessions`, {
          method: "POST",
          body: {
            plan_id: input.planId,
            workout_day_id: input.workoutDayId,
            performed_on: input.performedOn,
            duration_minutes: input.durationMinutes,
            completed_exercise_ids: input.completedExerciseIds,
            session_rpe: input.sessionRpe
          }
        })
      );
    },
    async getProgress(profileId) {
      return mapApiProgress(await request<ApiProgressSummary>(root, `/v1/profiles/${encodeURIComponent(profileId)}/progress`));
    },
    async getWeeklyCoach(profileId) {
      return mapApiWeeklyCoach(await request<ApiWeeklyCoachReport>(root, `/v1/profiles/${encodeURIComponent(profileId)}/weekly-coach`));
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
