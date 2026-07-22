import { ApiClientError, createCalAiApiClient } from "../api";
import { uploadImageToStorage } from "../api/imageUpload";
import type { ScanToSaveCommand } from "../flow/scanToSaveFlow";

async function expectNetworkError(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() => Promise.reject(new TypeError("connection refused"))) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:0").getTodayDashboard();
    throw new Error("expected network error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "network_error" || error.kind !== "network" || !error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectProviderUnavailable(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 503,
      json: () =>
        Promise.resolve({
          detail: {
            code: "analysis_provider_unavailable",
            message: "분석 제공자를 사용할 수 없어요.",
            retryable: false,
            kind: "provider"
          }
        })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected http error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "analysis_provider_unavailable" || error.status !== 503 || error.kind !== "provider" || error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectImageUploadMapsResponse(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((url, init) => {
    if (String(url).endsWith("/v1/image-uploads") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            image_upload_id: "local-upload-local-demo-meal-preview",
            image_reference: "local-image://local-upload-local-demo-meal-preview",
            status: "ready"
          })
      } as Response);
    }
    return Promise.reject(new Error("unexpected request"));
  }) as typeof fetch;
  try {
    const uploaded = await createCalAiApiClient("http://127.0.0.1:8015").uploadImage({
      localAssetId: "local-demo-meal-preview",
      fileName: "meal-preview.png",
      contentType: "image/png",
      byteSize: 420000
    });
    if (uploaded.imageUploadId !== "local-upload-local-demo-meal-preview" || uploaded.imageReference !== "local-image://local-upload-local-demo-meal-preview") {
      throw new Error("image upload response did not map");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectOnboardingMapsResponse(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((url, init) => {
    if (String(url).endsWith("/v1/onboarding") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            profile_id: "profile-1",
            target: {
              calories_kcal: 1850,
              protein_g: 130,
              carbs_g: 190,
              fat_g: 55
            },
            warnings: ["감량 속도는 천천히 조정하는 편이 좋아요."]
          })
      } as Response);
    }
    return Promise.reject(new Error("unexpected request"));
  }) as typeof fetch;
  try {
    const onboarded = await createCalAiApiClient("http://127.0.0.1:8015").createOnboarding({
      age: 29,
      sex: "male",
      heightCm: 172,
      currentWeightKg: 72,
      targetWeightKg: 68,
      goalType: "lose",
      activityLevel: "moderate",
      trainingFrequency: "3-4"
    });
    if (onboarded.profileId !== "profile-1" || onboarded.target.caloriesKcal !== 1850 || onboarded.warnings.length !== 1) {
      throw new Error("onboarding response did not map");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectPresignedUploadContract(): Promise<void> {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((url, init) => {
    calls.push(String(url));
    if (String(url).endsWith("/image-uploads/presign") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            image_upload_id: "image-upload-1",
            object_key: "uploads/image-upload-1/meal-preview.png",
            upload_url: "https://r2.example/uploads/image-upload-1/meal-preview.png?X-Amz-Signature=abc",
            headers: { "Content-Type": "image/png" },
            expires_at: "2026-06-20T00:15:00+00:00",
            max_bytes: 8000000,
            soft_limit_bytes: 4000000,
            soft_limit_exceeded: false,
            ttl_days: 30
          })
      } as Response);
    }
    if (String(url).endsWith("/image-uploads/complete") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            image_upload_id: "image-upload-1",
            image_reference: "r2://cal-ai-meal-images/uploads/image-upload-1/meal-preview.png",
            status: "ready"
          })
      } as Response);
    }
    return Promise.reject(new Error("unexpected request"));
  }) as typeof fetch;
  try {
    const client = createCalAiApiClient("http://127.0.0.1:8015");
    const presigned = await client.presignImageUpload({
      localAssetId: "local-demo-meal-preview",
      fileName: "meal-preview.png",
      contentType: "image/png",
      byteSize: 420000
    });
    if (presigned.objectKey !== "uploads/image-upload-1/meal-preview.png" || presigned.headers["Content-Type"] !== "image/png") {
      throw new Error("presign response did not map");
    }

    const completed = await client.completeImageUpload({
      imageUploadId: presigned.imageUploadId,
      objectKey: presigned.objectKey,
      localAssetId: "local-demo-meal-preview",
      fileName: "meal-preview.png",
      contentType: "image/png",
      byteSize: 420000
    });
    if (completed.imageUploadId !== "image-upload-1" || completed.imageReference !== "r2://cal-ai-meal-images/uploads/image-upload-1/meal-preview.png") {
      throw new Error("complete response did not map");
    }
    if (calls.length !== 2) {
      throw new Error("presigned upload contract should call presign and complete");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectLocalPresignedUploadSkipsNetworkPut(): Promise<void> {
  const calls: string[] = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((url, init) => {
    const target = String(url);
    calls.push(target);
    if (target === "blob:local-meal") {
      return Promise.resolve({ ok: true, status: 200, blob: () => Promise.resolve(new Blob(["meal"])) } as Response);
    }
    if (target.endsWith("/image-uploads/presign") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          image_upload_id: "image-upload-local",
          object_key: "uploads/image-upload-local/meal.png",
          upload_url: "local-upload://uploads/image-upload-local/meal.png",
          headers: { "Content-Type": "image/png" },
          expires_at: "2026-07-20T00:15:00+00:00",
          max_bytes: 8_000_000,
          soft_limit_bytes: 8_000_000_000,
          soft_limit_exceeded: false,
          ttl_days: 30
        })
      } as Response);
    }
    if (target.endsWith("/image-uploads/complete") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ image_upload_id: "image-upload-local", image_reference: "local-image://uploads/image-upload-local/meal.png", status: "ready" })
      } as Response);
    }
    return Promise.reject(new Error(`unexpected request: ${target}`));
  }) as typeof fetch;
  try {
    const command: Extract<ScanToSaveCommand, { type: "UPLOAD_IMAGE" }> = {
      type: "UPLOAD_IMAGE",
      requestId: 1,
      localAssetId: "local-meal",
      uri: "blob:local-meal",
      fileName: "meal.png",
      contentType: "image/png",
      byteSize: 4
    };
    const result = await uploadImageToStorage(command, createCalAiApiClient("http://127.0.0.1:8015"));
    if (result.imageUploadId !== "image-upload-local" || calls.some((call) => call.startsWith("local-upload://"))) {
      throw new Error("local presigned upload should skip direct network PUT");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectProviderDryRun(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 503,
      json: () =>
        Promise.resolve({
          detail: {
            code: "analysis_provider_dry_run",
            message: "실제 AI 분석 호출은 아직 비활성화되어 있어요.",
            retryable: false,
            kind: "provider"
          }
        })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected dry-run provider error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "analysis_provider_dry_run" || error.kind !== "provider" || error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectMalformedOutput(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 503,
      json: () =>
        Promise.resolve({
          detail: {
            code: "analysis_output_malformed",
            message: "분석 결과 형식이 올바르지 않아 다시 시도해야 해요.",
            retryable: true,
            kind: "provider"
          }
        })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected malformed-output provider error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "analysis_output_malformed" || error.kind !== "provider" || !error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectValidationError(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          detail: {
            code: "validation_error",
            message: "요청 형식이 올바르지 않아요.",
            retryable: false,
            kind: "validation"
          }
        })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected validation error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "validation_error" || error.kind !== "validation" || error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectMalformedErrorFallback(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 500,
      json: () => Promise.reject(new SyntaxError("invalid json"))
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected fallback server error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "http_500" || error.kind !== "server" || !error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectInvalidKindFallsBackToStatus(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 503,
      json: () =>
        Promise.resolve({
          detail: {
            code: "bad_proxy_error",
            message: "do not trust this message",
            retryable: false,
            kind: "bad_kind"
          }
        })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected invalid-kind fallback error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "http_503" || error.kind !== "server" || !error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectTimeoutStatusFallback(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 408,
      json: () => Promise.resolve({ detail: "Request Timeout" })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected timeout fallback error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "http_408" || error.kind !== "timeout" || !error.retryable) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectCoachContractsMap(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((url, init) => {
    const path = String(url);
    if (path.endsWith("/v1/profiles/profile-1/dashboard/today")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          profile_id: "profile-1",
          date: "2026-07-20",
          nutrition: {
            target: { calories_kcal: 2100, protein_g: 150, carbs_g: 240, fat_g: 60 },
            consumed: { calories_kcal: 800, protein_g: 62, carbs_g: 90, fat_g: 24 },
            remaining: { calories_kcal: 1300, protein_g: 88, carbs_g: 150, fat_g: 36 },
            protein_progress: 0.41,
            guidance: "단백질이 88g 남았어요."
          },
          training: { planned_sessions: 3, completed_sessions: 1, next_workout_title: "전신 B", recovery_message: "계획을 진행해도 괜찮아요." },
          next_action: { type: "start_workout", title: "전신 B", detail: "다음 운동을 시작해요." }
        })
      } as Response);
    }
    if (path.endsWith("/v1/profiles/profile-1/workout-plans/generate") && init?.method === "POST") {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          id: "plan-1",
          profile_id: "profile-1",
          goal_type: "recomp",
          days_per_week: 3,
          session_minutes: 60,
          days: [{ id: "day-1", title: "전신 A", focus: "기본", exercises: [{ id: "exercise-1", name: "스쿼트", sets: 3, reps: "6-10회", target_rir: 2, rest_seconds: 120, rationale: "하체 기본" }] }],
          personalization_basis: ["목표: 체성분 개선"],
          progression_rule: "반복 상단 달성 후 증량",
          safety_note: "통증 시 중단",
          generated_at: "2026-07-20T00:00:00+00:00"
        })
      } as Response);
    }
    return Promise.reject(new Error("unexpected request"));
  }) as typeof fetch;
  try {
    const client = createCalAiApiClient("http://127.0.0.1:8015");
    const dashboard = await client.getCoachDashboard("profile-1");
    const plan = await client.generateWorkoutPlan("profile-1");
    if (dashboard.nutrition.remaining.proteinG !== 88 || dashboard.training.nextWorkoutTitle !== "전신 B") {
      throw new Error("coach dashboard response did not map");
    }
    if (plan.daysPerWeek !== 3 || plan.days[0]?.exercises[0]?.targetRir !== 2) {
      throw new Error("workout plan response did not map");
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

export async function runApiClientSmoke(): Promise<void> {
  await expectNetworkError();
  await expectOnboardingMapsResponse();
  await expectImageUploadMapsResponse();
  await expectPresignedUploadContract();
  await expectLocalPresignedUploadSkipsNetworkPut();
  await expectProviderUnavailable();
  await expectProviderDryRun();
  await expectMalformedOutput();
  await expectValidationError();
  await expectMalformedErrorFallback();
  await expectInvalidKindFallsBackToStatus();
  await expectTimeoutStatusFallback();
  await expectCoachContractsMap();
}
