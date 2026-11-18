import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import ts from "typescript";

const directory = await mkdtemp(join(tmpdir(), "cal-ai-admin-smoke-"));
const originalFetch = globalThis.fetch;
let passed = 0;
try {
  const outfile = join(directory, "api.mjs");
  async function compile(source, target) {
    const { outputText, diagnostics } = ts.transpileModule(await readFile(new URL(source, import.meta.url), "utf8"), {
      compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
      reportDiagnostics: true,
      transformers: { before: [(context) => {
        function visit(node) {
          if (ts.isPropertyAccessExpression(node) && node.name.text === "VITE_API_BASE_URL" &&
              ts.isPropertyAccessExpression(node.expression) && node.expression.name.text === "env" &&
              ts.isMetaProperty(node.expression.expression)) {
            return ts.factory.createStringLiteral("https://fixture.invalid");
          }
          return ts.visitEachChild(node, visit, context);
        }
        return (sourceFile) => ts.visitNode(sourceFile, visit);
      }] }
    });
    assert.equal(diagnostics.length, 0);
    await writeFile(target, outputText);
    return import(pathToFileURL(target).href);
  }
  await compile("../src/api.ts", outfile);
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
    await assert.rejects(api.getBetaApplications("test-only-token"), (error) =>
      error instanceof api.AdminApiError && error.status === status && !error.message.includes("private"));
    passed++;
  }
  globalThis.fetch = async () => new Response("<!doctype html>", { headers: { "Content-Type": "text/html" } });
  await assert.rejects(api.getOverview("test-only-token"), (error) => error.status === 502);
  passed++;
  await assert.rejects(api.getBetaApplications("test-only-token"), (error) => error.status === 502);
  passed++;
  const controller = new AbortController();
  controller.abort();
  globalThis.fetch = async (_url, options) => {
    options.signal.throwIfAborted();
    throw new Error("Aborted request was not stopped");
  };
  await assert.rejects(api.getUserDetail("fixture-user", "test-only-token", controller.signal), { name: "AbortError" });
  passed++;
  await assert.rejects(api.getBetaApplications("test-only-token", {}, controller.signal), { name: "AbortError" });
  passed++;
  const receipt = {
    generated_at: "2026-11-19T00:00:00Z", total: 101, limit: 50, offset: 0,
    applications: [{ id: "fixture-1", email: "fixture+alias@example.invalid", created_at: "2026-11-18T23:45:10Z" }]
  };
  globalThis.fetch = async (url, options) => {
    assert.equal(url, "https://fixture.invalid/internal/admin/beta-applications?limit=50&offset=0");
    assert.equal(options.headers.Authorization, "Bearer test-only-token");
    assert.equal(options.cache, "no-store");
    assert.ok(options.signal instanceof AbortSignal);
    return Response.json(receipt);
  };
  assert.deepEqual(await api.getBetaApplications("test-only-token"), receipt);
  passed++;
  globalThis.fetch = async (url) => {
    assert.equal(url, "https://fixture.invalid/internal/admin/beta-applications?limit=100&offset=100000");
    return Response.json({ ...receipt, offset: 100_000, limit: 100, applications: [] });
  };
  assert.equal((await api.getBetaApplications("test-only-token", { limit: 100, offset: 100_000 })).total, 101);
  passed++;
  globalThis.fetch = async () => { throw new Error("Invalid bounds must not fetch"); };
  for (const options of [{ limit: 0 }, { limit: 101 }, { limit: 1.5 }, { offset: -1 }, { offset: 100_001 }, { offset: 0.5 }]) {
    await assert.rejects(api.getBetaApplications("test-only-token", options), (error) => error.status === 400);
    passed++;
  }
  for (const invalid of [{ ...receipt, total: -1 }, { ...receipt, offset: 50 }, { ...receipt, applications: null },
    { ...receipt, applications: [{ id: "fixture", email: "private diagnostic", created_at: "invalid" }] }]) {
    globalThis.fetch = async () => Response.json(invalid);
    await assert.rejects(api.getBetaApplications("test-only-token"), (error) => error.status === 502 && !error.message.includes("private"));
    passed++;
  }
  globalThis.fetch = async () => new Response("private diagnostic", { status: 429 });
  await assert.rejects(api.loginAdmin("fixture-owner", "fixture-password"), (error) =>
    error.message.includes("15") && !error.message.includes("private"));
  passed++;
  const { AdminRequestGate } = await compile("../src/adminRequestGate.ts", join(directory, "gate.mjs"));
  for (const denialSource of ["overview", "user-detail", "beta", "logout"]) {
    const gate = new AdminRequestGate();
    const readers = [gate.open(), gate.open(), gate.open()];
    let publish;
    const late = new Promise((resolve) => { publish = resolve; });
    let pii = "previous@example.invalid";
    const pending = late.then((email) => { if (gate.accepts(readers[2])) pii = email; });
    gate.revoke();
    pii = null;
    publish("late@example.invalid");
    await pending;
    assert.equal(pii, null, `${denialSource}: late response must not restore PII`);
    assert.ok(readers.every((controller) => controller.signal.aborted));
    assert.equal(gate.accepts(gate.open()), false);
    assert.equal(gate.denied, true);
    passed++;
  }
  const gate = new AdminRequestGate();
  const oldRead = gate.open();
  gate.release(oldRead);
  assert.equal(gate.accepts(oldRead), false);
  assert.equal(gate.accepts(gate.open()), true, "effect cleanup must not revoke a live session (including StrictMode)");
  passed++;
  console.log(`Admin API smoke: ${passed} checks passed (fixture requests only).`);
} finally {
  globalThis.fetch = originalFetch;
  await rm(directory, { recursive: true, force: true });
}
