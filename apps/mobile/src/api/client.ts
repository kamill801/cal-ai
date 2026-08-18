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
  ApiProfileDeletionResult,
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
  mapApiProfileDeletionResult,
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
  type ProfileDeletionResult,
  type MealNutritionOverride,
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
  createAnalysisJob(input: { imageUploadId: string; profileId?: string; mealType?: MealType; optionalNote?: string }): Promise<{ analysisJobId: string; status: "queued" }>;
  getAnalysisJob(jobId: string): Promise<AnalysisJobViewModel>;
  submitClarification(input: { jobId: string; questionKey: string; value: string }): Promise<{ result: AnalysisResult; rangeNarrowing?: RangeNarrowingResult }>;
  saveMealLog(input: { analysisJobId: string; resultId: string; clarificationValue: string; profileId?: string; loggedOn?: string; nutritionOverride?: MealNutritionOverride }): Promise<SavedImpactViewModel>;
  getCoachDashboard(profileId: string, loggedOn?: string): Promise<CoachDashboard>;
  logWeight(profileId: string, input: { loggedOn: string; weightKg: number }): Promise<WeightLog>;
  logWellness(profileId: string, input: { loggedOn: string; energy: number; sleepQuality: number; soreness: number; note?: string }): Promise<WellnessCheckIn>;
  createBodyCheckIn(profileId: string, input: { capturedOn: string; imageUploadId: string; view: "front" | "side" | "back"; consentToAiAnalysis: true }): Promise<BodyCheckIn>;
  generateWorkoutPlan(profileId: string): Promise<WorkoutPlan>;
  getWorkoutPlan(profileId: string): Promise<WorkoutPlan>;
  logWorkoutSession(profileId: string, input: { planId: string; workoutDayId: string; performedOn: string; durationMinutes: number; completedExerciseIds: string[]; exercisePerformance: { exerciseId: string; setsCompleted: number; repsCompleted?: number; loadKg?: number }[]; sessionRpe: number }): Promise<WorkoutSession>;
  getProgress(profileId: string): Promise<ProgressSummary>;
  getWeeklyCoach(profileId: string): Promise<WeeklyCoachReport>;
  deleteProfile(profileId: string): Promise<ProfileDeletionResult>;
}

export function createCalAiApiClient(baseUrl = getApiBaseUrl(), accessToken?: string): CalAiApiClient {
  const root = baseUrl.replace(/\/+$/, "");
  const call = <T>(path: string, options: { method?: "GET" | "POST" | "DELETE"; body?: unknown } = {}) => request<T>(root, path, options, accessToken);

  return {
    async getTodayDashboard() {
      return mapApiDashboardToday(await call<ApiDashboardTodayResponse>("/v1/dashboard/today"));
    },
    async createOnboarding(input) {
      return mapApiOnboardingResponse(
        await call<ApiOnboardingResponse>("/v1/onboarding", {
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
        await call<ApiImageUploadResponse>("/v1/image-uploads", {
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
        await call<ApiImageUploadPresignResponse>("/image-uploads/presign", {
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
        await call<ApiImageUploadResponse>("/image-uploads/complete", {
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
      const response = await call<ApiAnalysisJobCreateResponse>("/v1/analysis-jobs", {
        method: "POST",
        body: {
          image_upload_id: input.imageUploadId,
          profile_id: input.profileId ?? null,
          meal_type: input.mealType ?? "lunch",
          optional_note: input.optionalNote ?? null
        }
      });
      return { analysisJobId: response.analysis_job_id, status: response.status };
    },
    async getAnalysisJob(jobId) {
      return mapApiAnalysisJob(await call<ApiAnalysisJobResponse>(`/v1/analysis-jobs/${encodeURIComponent(jobId)}`));
    },
    async submitClarification(input) {
      const response = await call<ApiClarificationResponse>(`/v1/analysis-jobs/${encodeURIComponent(input.jobId)}/clarifications`, {
        method: "POST",
        body: { answers: [{ question_key: input.questionKey, value: input.value }] }
      });
      const mapped = mapApiClarificationResponse(response);
      return { result: mapped.result, rangeNarrowing: mapped.rangeNarrowing };
    },
    async saveMealLog(input) {
      return mapApiSavedImpactResponse(
        await call<ApiSavedImpactResponse>("/v1/meal-logs", {
          method: "POST",
          body: {
            analysis_job_id: input.analysisJobId,
            result_id: input.resultId,
            clarification_value: input.clarificationValue,
            profile_id: input.profileId ?? null,
            logged_on: input.loggedOn ?? null,
            nutrition_override: input.nutritionOverride
              ? {
                  meal_name: input.nutritionOverride.mealName ?? null,
                  calories_kcal: input.nutritionOverride.caloriesKcal,
                  protein_g: input.nutritionOverride.proteinG,
                  carbs_g: input.nutritionOverride.carbsG,
                  fat_g: input.nutritionOverride.fatG
                }
              : null
          }
        })
      );
    },
    async getCoachDashboard(profileId, loggedOn) {
      const query = loggedOn ? `?logged_on=${encodeURIComponent(loggedOn)}` : "";
      return mapApiCoachDashboard(await call<ApiCoachDashboard>(`/v1/profiles/${encodeURIComponent(profileId)}/dashboard/today${query}`));
    },
    async logWeight(profileId, input) {
      return mapApiWeightLog(
        await call<ApiWeightLog>(`/v1/profiles/${encodeURIComponent(profileId)}/weight-logs`, {
          method: "POST",
          body: { logged_on: input.loggedOn, weight_kg: input.weightKg }
        })
      );
    },
    async logWellness(profileId, input) {
      return mapApiWellness(
        await call<ApiWellnessCheckIn>(`/v1/profiles/${encodeURIComponent(profileId)}/wellness-check-ins`, {
          method: "POST",
          body: { logged_on: input.loggedOn, energy: input.energy, sleep_quality: input.sleepQuality, soreness: input.soreness, note: input.note ?? null }
        })
      );
    },
    async createBodyCheckIn(profileId, input) {
      return mapApiBodyCheckIn(
        await call<ApiBodyCheckIn>(`/v1/profiles/${encodeURIComponent(profileId)}/body-check-ins`, {
          method: "POST",
          body: { captured_on: input.capturedOn, image_upload_id: input.imageUploadId, view: input.view, consent_to_ai_analysis: input.consentToAiAnalysis }
        })
      );
    },
    async generateWorkoutPlan(profileId) {
      return mapApiWorkoutPlan(
        await call<ApiWorkoutPlan>(`/v1/profiles/${encodeURIComponent(profileId)}/workout-plans/generate`, { method: "POST" })
      );
    },
    async getWorkoutPlan(profileId) {
      return mapApiWorkoutPlan(await call<ApiWorkoutPlan>(`/v1/profiles/${encodeURIComponent(profileId)}/workout-plan`));
    },
    async logWorkoutSession(profileId, input) {
      return mapApiWorkoutSession(
        await call<ApiWorkoutSession>(`/v1/profiles/${encodeURIComponent(profileId)}/workout-sessions`, {
          method: "POST",
          body: {
            plan_id: input.planId,
            workout_day_id: input.workoutDayId,
            performed_on: input.performedOn,
            duration_minutes: input.durationMinutes,
            completed_exercise_ids: input.completedExerciseIds,
            exercise_performance: input.exercisePerformance.map((item) => ({
              exercise_id: item.exerciseId,
              sets_completed: item.setsCompleted,
              reps_completed: item.repsCompleted ?? null,
              load_kg: item.loadKg ?? null
            })),
            session_rpe: input.sessionRpe
          }
        })
      );
    },
    async getProgress(profileId) {
      return mapApiProgress(await call<ApiProgressSummary>(`/v1/profiles/${encodeURIComponent(profileId)}/progress`));
    },
    async getWeeklyCoach(profileId) {
      return mapApiWeeklyCoach(await call<ApiWeeklyCoachReport>(`/v1/profiles/${encodeURIComponent(profileId)}/weekly-coach`));
    },
    async deleteProfile(profileId) {
      return mapApiProfileDeletionResult(
        await call<ApiProfileDeletionResult>(`/v1/profiles/${encodeURIComponent(profileId)}`, { method: "DELETE" })
      );
    }
  };
}

async function request<T>(root: string, path: string, options: { method?: "GET" | "POST" | "DELETE"; body?: unknown } = {}, accessToken?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${root}${path}`, {
      method: options.method ?? "GET",
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
      },
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
