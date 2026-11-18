import assert from "node:assert/strict";
import { mkdir, readFile } from "node:fs/promises";
import { build } from "esbuild";

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const output = process.env.ADMIN_QA_OUTPUT || "/private/tmp/cal-ai-admin-beta-qa-20261119";
await mkdir(output, { recursive: true });
const bundle = await build({
  stdin: {
    contents: 'import React from "react"; import { createRoot } from "react-dom/client"; import { App } from "./App"; createRoot(document.getElementById("root")).render(<React.StrictMode><App /></React.StrictMode>);',
    resolveDir: new URL("../src", import.meta.url).pathname,
    loader: "tsx"
  },
  bundle: true, write: false, format: "iife", platform: "browser", jsx: "automatic",
  define: { "import.meta.env.VITE_API_BASE_URL": JSON.stringify("https://fixture.invalid"), "process.env.NODE_ENV": JSON.stringify("development") },
  plugins: [{
    name: "fixture-auth-only",
    setup(builder) {
      builder.onLoad({ filter: /[/\\]supabase\.ts$/ }, () => ({
        loader: "js",
        contents: `export const supabase = window.fixture.authConfigured === false ? null : { auth: {
          getSession: async () => ({ data: { session: window.fixture.session } }),
          onAuthStateChange: (callback) => { window.fixture.authChanged = callback; return { data: { subscription: { unsubscribe() {} } } }; },
          signOut: async () => { window.fixture.authChanged?.("SIGNED_OUT", null); return {}; }
        } };`
      }));
    }
  }]
});
const css = await readFile(new URL("../src/styles.css", import.meta.url), "utf8");
const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || "chrome" });
const errors = [];
let passed = 0;

async function fixturePage(width = 1440, options = {}) {
  const page = await browser.newPage({ viewport: { width, height: 1000 }, reducedMotion: "reduce" });
  page.setDefaultTimeout(10_000);
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/*", (route) => route.abort());
  await page.setContent('<!doctype html><html lang="ko"><head></head><body><div id="root"></div></body></html>');
  await page.addStyleTag({ content: css });
  await page.evaluate((config) => {
    const session = { access_token: "fixture-owner-token", user: { id: "fixture-owner", email: "owner@example.invalid" } };
    const state = window.fixture = {
      total: 101, session: config.signedOut ? null : session, authConfigured: config.authConfigured ?? true,
      behavior: { overview: { status: config.overviewStatus || 200 }, beta: { status: config.betaStatus || 200, hold: config.betaHold || false }, detail: { status: 200 } },
      calls: [], releases: { overview: [], beta: [], detail: [] }, timers: new Map(), timerId: 0
    };
    const user = {
      user_id: "fixture-product-user", email: "product@example.invalid", display_name: "픽스처 사용자",
      first_seen_at: "2026-11-18T23:45:10Z", last_seen_at: "2026-11-18T23:45:10Z", online: true,
      analysis_count: 0, meal_save_count: 0, workout_count: 0, plan: "free"
    };
    state.tick = () => [...state.timers.values()].forEach((timer) => timer.callback());
    state.release = (name) => { state.releases[name].splice(0).forEach((resolve) => resolve()); };
    window.setInterval = (callback, delay) => {
      const id = ++state.timerId;
      state.timers.set(id, { callback, delay });
      return id;
    };
    window.clearInterval = (id) => state.timers.delete(id);
    window.fetch = async (input, request) => {
      const url = new URL(input);
      const name = url.pathname.endsWith("beta-applications") ? "beta" : url.pathname.endsWith("overview") ? "overview" : "detail";
      const offset = Number(url.searchParams.get("offset") || 0);
      const limit = Number(url.searchParams.get("limit") || 50);
      state.calls.push({ name, offset, authorization: request.headers.Authorization, cache: request.cache });
      const behavior = state.behavior[name];
      const status = behavior.status;
      const payload = name === "beta" ? {
        generated_at: "2026-11-19T00:00:00Z", total: state.total, offset, limit,
        applications: Array.from({ length: Math.max(0, Math.min(limit, state.total - offset)) }, (_, index) => ({
          id: `fixture-${offset + index}`, email: `beta-fixture-${offset + index}@example.invalid`,
          created_at: new Date(Date.parse("2026-11-18T23:45:10Z") - (offset + index) * 1000).toISOString()
        }))
      } : name === "overview" ? {
        generated_at: "2026-11-19T00:00:00Z",
        metrics: { today_users: 1, new_users_today: 1, realtime_users: 1, active_users_24h: 1, food_analyses_today: 0, meals_saved_today: 0, workouts_completed_today: 0 },
        funnel: [], recent_activity: [], users: [user],
        payments: { gross_revenue_krw: 0, active_subscriptions: 0, failed_count: 0, recent_payments: [] },
        ai_operations: { started_today: 0, completed_today: 0, failed_today: 0, success_rate: 0 }
      } : { user, recent_activity: [], payments: [] };
      // Deliberately ignore AbortSignal: late successful responses must still be rejected by the UI.
      if (behavior.hold) await new Promise((resolve) => state.releases[name].push(resolve));
      return Response.json(status === 200 ? payload : { detail: "private-provider-detail" }, { status });
    };
  }, options);
  await page.addScriptTag({ content: bundle.outputFiles[0].text });
  return page;
}

async function ready(page) {
  await page.locator(".beta-email").first().waitFor();
  await page.waitForFunction(() => document.querySelector(".beta-section")?.getAttribute("aria-busy") === "false");
}

async function tick(page) {
  await page.evaluate(() => window.fixture.tick());
  await page.waitForFunction(() => document.querySelector(".beta-section")?.getAttribute("aria-busy") === "false");
}

try {
  for (const width of [320, 390, 1440]) {
    const page = await fixturePage(width, { overviewStatus: 503 });
    await ready(page);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${width}: page overflow`);
    assert.match(await page.locator(".beta-section").textContent(), /전체 신청자 101명/);
    assert.equal(await page.locator(".beta-email").count(), 50);
    assert.match(await page.locator(".beta-table time").first().textContent(), /2026.*11.*19.*08:45:10/);
    assert.match(await page.locator(".beta-table th").last().textContent(), /Asia\/Seoul/);
    assert.equal(await page.getByRole("button", { name: "이전 페이지", exact: true }).isDisabled(), true);
    assert.equal(await page.locator("body").textContent().then((text) => text.includes("private-provider-detail")), false);
    await page.screenshot({ path: `${output}/beta-${width}.png`, fullPage: true });
    assert.equal(await page.evaluate(() => window.fixture.calls.every((call) => call.authorization === "Bearer fixture-owner-token" && call.cache === "no-store")), true);
    await page.getByRole("button", { name: "다음 페이지", exact: true }).click();
    await page.getByText("beta-fixture-50@example.invalid", { exact: true }).waitFor();
    await ready(page);
    await page.getByRole("button", { name: "베타 신청자 새로고침", exact: true }).click();
    await ready(page);
    assert.equal(await page.evaluate(() => window.fixture.calls.filter((call) => call.name === "beta").at(-1).offset), 50);
    const before = await page.evaluate(() => window.fixture.calls.filter((call) => call.name === "beta").length);
    await tick(page);
    assert.equal(await page.evaluate(() => window.fixture.calls.filter((call) => call.name === "beta").length), before + 1, "one beta read per 30-second tick");
    assert.equal(await page.evaluate(() => [...window.fixture.timers.values()].every((timer) => timer.delay === 30_000)), true);
    assert.equal(await page.evaluate(() => window.fixture.timers.size), 2, "refresh must not accumulate loops");
    assert.match(await page.locator(".beta-pagination").textContent(), /2 \/ 3페이지/);
    await page.getByRole("button", { name: "다음 페이지", exact: true }).click();
    await page.getByText("beta-fixture-100@example.invalid", { exact: true }).waitFor();
    await ready(page);
    await page.evaluate(() => { window.fixture.total = 50; });
    await tick(page);
    await page.getByText("beta-fixture-0@example.invalid", { exact: true }).waitFor();
    await ready(page);
    assert.match(await page.locator(".beta-pagination").textContent(), /1 \/ 1페이지/);
    await page.evaluate(() => { window.fixture.total = 0; });
    await tick(page);
    await page.getByText("보관 중인 베타 신청자가 없어요.", { exact: true }).waitFor();
    assert.equal(await page.locator(".beta-email").count(), 0);
    await page.close();
    passed++;
  }

  const loading = await fixturePage(390, { betaHold: true });
  await loading.getByText("신청자 목록을 불러오는 중이에요.", { exact: true }).waitFor();
  assert.equal(await loading.getByRole("button", { name: "베타 신청자 새로고침", exact: true }).isDisabled(), true);
  await loading.evaluate(() => { window.fixture.behavior.beta.hold = false; window.fixture.release("beta"); });
  await ready(loading);
  await loading.close();
  passed++;

  const retry = await fixturePage(390, { betaStatus: 503 });
  await retry.getByRole("button", { name: "다시 시도", exact: true }).waitFor();
  assert.equal((await retry.locator("body").textContent()).includes("private-provider-detail"), false);
  await retry.evaluate(() => { window.fixture.behavior.beta.status = 200; });
  await retry.getByRole("button", { name: "다시 시도", exact: true }).click();
  await ready(retry);
  await retry.close();
  passed++;

  for (const source of ["overview", "detail", "beta"]) {
    for (const status of [401, 403]) {
      const page = await fixturePage();
      await ready(page);
      await page.locator(".table-link").first().click();
      await page.waitForFunction(() => window.fixture.calls.some((call) => call.name === "detail"));
      await page.evaluate(({ source, status }) => {
        for (const name of ["overview", "detail", "beta"]) {
          window.fixture.behavior[name] = { status: name === source ? status : 200, hold: name !== source };
        }
        window.fixture.tick();
      }, { source, status });
      await page.getByText("관리자 접근 권한이 없거나 세션이 만료됐어요. 다시 로그인해 주세요.", { exact: true }).waitFor();
      assert.equal(await page.locator(".beta-email").count(), 0);
      await page.evaluate(() => ["overview", "detail", "beta"].forEach((name) => window.fixture.release(name)));
      await page.waitForTimeout(50);
      assert.equal(await page.locator(".beta-email").count(), 0, `${source} ${status}: late response restored beta PII`);
      assert.equal(await page.locator(".table-link").count(), 0, "late overview must remain hidden");
      const before = await page.evaluate(() => window.fixture.calls.length);
      await page.evaluate(() => window.fixture.tick());
      await page.waitForTimeout(50);
      assert.equal(await page.evaluate(() => window.fixture.calls.length), before, "denied session must stop polling");
      await page.close();
      passed++;
    }
  }

  const lateBeta = await fixturePage();
  await ready(lateBeta);
  await lateBeta.evaluate(() => { window.fixture.behavior.beta.hold = true; window.fixture.tick(); });
  await lateBeta.waitForFunction(() => window.fixture.releases.beta.length > 0);
  await lateBeta.evaluate(() => { window.fixture.behavior.beta = { status: 403 }; });
  await lateBeta.getByRole("button", { name: "전체 새로고침", exact: true }).click();
  await lateBeta.getByText("관리자 접근 권한이 없거나 세션이 만료됐어요. 다시 로그인해 주세요.", { exact: true }).waitFor();
  await lateBeta.evaluate(() => window.fixture.release("beta"));
  await lateBeta.waitForTimeout(50);
  assert.equal(await lateBeta.locator(".beta-email").count(), 0, "old beta success cannot override a later beta denial");
  await lateBeta.close();
  passed++;

  const logout = await fixturePage();
  await ready(logout);
  await logout.evaluate(() => { window.fixture.behavior.beta.hold = true; window.fixture.tick(); });
  await logout.getByRole("button", { name: "로그아웃", exact: true }).click();
  await logout.getByRole("heading", { name: "Cal AI Admin", exact: true }).waitFor();
  await logout.evaluate(() => window.fixture.release("beta"));
  await logout.waitForTimeout(50);
  assert.equal(await logout.locator(".beta-section").count(), 0);
  await logout.close();
  passed++;

  for (const options of [{ signedOut: true }, { authConfigured: false }]) {
    const page = await fixturePage(390, options);
    await page.getByText(options.signedOut ? "관리자 전용 로그인" : "관리자 로그인 설정이 아직 완료되지 않았어요.", { exact: true }).waitFor();
    assert.equal(await page.locator(".beta-section").count(), 0);
    assert.equal(await page.evaluate(() => window.fixture.calls.length), 0);
    await page.close();
    passed++;
  }
  assert.deepEqual(errors, []);
  console.log(`Admin beta browser smoke: ${passed} scenarios passed (synthetic fixtures only; no server or production requests).`);
} finally {
  await browser.close();
}
