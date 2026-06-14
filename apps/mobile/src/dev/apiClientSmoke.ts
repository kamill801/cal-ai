import { ApiClientError, createCalAiApiClient } from "../api";

async function expectNetworkError(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() => Promise.reject(new TypeError("connection refused"))) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:0").getTodayDashboard();
    throw new Error("expected network error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "network_error") {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function expectHttpError(): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() =>
    Promise.resolve({
      ok: false,
      status: 503,
      json: () => Promise.resolve({ detail: { code: "analysis_provider_unavailable" } })
    } as Response)) as typeof fetch;
  try {
    await createCalAiApiClient("http://127.0.0.1:8015").getTodayDashboard();
    throw new Error("expected http error");
  } catch (error) {
    if (!(error instanceof ApiClientError) || error.code !== "http_error" || error.status !== 503) {
      throw error;
    }
  } finally {
    globalThis.fetch = originalFetch;
  }
}

export async function runApiClientSmoke(): Promise<void> {
  await expectNetworkError();
  await expectHttpError();
}
