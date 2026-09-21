import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { build } from "esbuild";

const directory = await mkdtemp(join(tmpdir(), "cal-ai-admin-smoke-"));
const originalFetch = globalThis.fetch;
let passed = 0;
try {
  const outfile = join(directory, "api.mjs");
  await build({
    entryPoints: [new URL("../src/api.ts", import.meta.url).pathname],
    outfile, bundle: true, platform: "node", format: "esm",
    define: { "import.meta.env.VITE_API_BASE_URL": JSON.stringify("https://fixture.invalid") }
  });
  const api = await import(pathToFileURL(outfile).href);
  for (const status of [401, 403, 503]) {
    globalThis.fetch = async (_url, options) => {
      assert.equal(options.cache, "no-store");
      assert.ok(options.signal instanceof AbortSignal);
      return new Response("private provider diagnostic", { status });
    };
    await assert.rejects(api.getOverview("test-only-token"), (error) =>
      error instanceof api.AdminApiError && error.status === status && !error.message.includes("private"));
    passed++;
  }
  globalThis.fetch = async () => new Response("<!doctype html>", { headers: { "Content-Type": "text/html" } });
  await assert.rejects(api.getOverview("test-only-token"), (error) => error.status === 502);
  passed++;
  const controller = new AbortController();
  controller.abort();
  globalThis.fetch = async (_url, options) => {
    options.signal.throwIfAborted();
    throw new Error("Aborted request was not stopped");
  };
  await assert.rejects(api.getUserDetail("fixture-user", "test-only-token", controller.signal), { name: "AbortError" });
  passed++;
  globalThis.fetch = async () => new Response("private diagnostic", { status: 429 });
  await assert.rejects(api.loginAdmin("fixture-owner", "fixture-password"), (error) =>
    error.message.includes("15") && !error.message.includes("private"));
  passed++;
  console.log(`Admin API smoke: ${passed} checks passed (fixture requests only).`);
} finally {
  globalThis.fetch = originalFetch;
  await rm(directory, { recursive: true, force: true });
}
