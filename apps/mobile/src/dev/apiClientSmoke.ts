import { ApiClientError, createCalAiApiClient } from "../api";

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

export async function runApiClientSmoke(): Promise<void> {
  await expectNetworkError();
  await expectImageUploadMapsResponse();
  await expectPresignedUploadContract();
  await expectProviderUnavailable();
  await expectProviderDryRun();
  await expectMalformedOutput();
  await expectValidationError();
  await expectMalformedErrorFallback();
  await expectInvalidKindFallsBackToStatus();
  await expectTimeoutStatusFallback();
}
