import assert from "node:assert/strict";
import { mkdir } from "node:fs/promises";

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const origin = process.env.LANDING_QA_ORIGIN || "http://localhost:8024";
if (!/^http:\/\/(localhost|127\.0\.0\.1):\d+$/.test(origin)) throw new Error("QA synthetic writes are restricted to local fixtures");
const output = process.env.LANDING_QA_OUTPUT || "/private/tmp/cal-ai-beta-landing-qa-20261118";
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || "chrome" });
const failures = [];
try {
  for (const [name, width, height] of [["desktop", 1440, 1000], ["mobile", 390, 844], ["small", 320, 740], ["wide", 1920, 1080]]) {
    const page = await browser.newPage({ viewport: { width, height }, reducedMotion: "reduce" });
    page.on("pageerror", (error) => failures.push(error.message));
    await page.goto(origin, { waitUntil: "networkidle" });
    assert.equal(await page.locator('a[href="/app"]').count(), 0, "web app must not be linked");
    await page.locator("#beta-form").waitFor({ state: "visible" });
    await page.locator("img").evaluateAll((images) => images.forEach((image) => { image.loading = "eager"; }));
    await page.waitForFunction(() => Array.from(document.images).every((image) => image.complete && image.naturalWidth > 0));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${name} horizontal overflow`);
    assert.ok(await page.locator("img").evaluateAll((images) => images.every((image) => image.complete && image.naturalWidth > 0)), `${name} missing assets`);
    await page.screenshot({ path: `${output}/${name}-first.png` });
    await page.screenshot({ path: `${output}/${name}-full.png`, fullPage: true });
    const hero = await page.locator(".hero").boundingBox();
    assert.ok(hero.y + hero.height < height - 80, `${name} must hint at the next section`);
    console.log(JSON.stringify({ viewport: name, hero_bottom: Math.round(hero.y + hero.height), height }));
    await page.locator("#tab-meal").focus();
    await page.keyboard.press("ArrowRight");
    assert.equal(await page.locator("#tab-nutrition").getAttribute("aria-selected"), "true");
    assert.equal(await page.locator("#feature-meal").isVisible(), false);
    await page.locator("#tab-training").click();
    assert.equal(await page.locator("#feature-training").isVisible(), true);
    for (const id of ["beta-adult", "beta-android", "beta-privacy"]) assert.equal(await page.locator(`#${id}`).isChecked(), false);
    await page.locator("#beta-email").fill("synthetic-landing@example.invalid");
    let posts = 0;
    page.on("request", (request) => { if (request.method() === "POST" && request.url().endsWith("/recruitment/applications")) posts++; });
    await page.locator("#submit-beta").click();
    assert.equal(posts, 0, "unchecked consent must not submit");
    for (const id of ["beta-adult", "beta-android", "beta-privacy"]) await page.locator(`#${id}`).check();
    if (name === "desktop") {
      await page.route("**/recruitment/applications", (route) => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: { code: "recruitment_unavailable" } }) }));
      await page.locator("#submit-beta").click();
      await page.locator("#form-error").waitFor({ state: "visible" });
      assert.equal(await page.locator("#beta-success").isVisible(), false);
      assert.equal(await page.locator("#beta-email").inputValue(), "synthetic-landing@example.invalid");
      await page.screenshot({ path: `${output}/desktop-retry.png`, fullPage: true });
      await page.unroute("**/recruitment/applications");
    }
    await page.locator("#submit-beta").click();
    await page.locator("#beta-success").waitFor({ state: "visible" });
    assert.ok((await page.locator("#install-link").getAttribute("href")).startsWith("https://expo.dev/accounts/arche-trustfirstnutrition/"));
    assert.equal(await page.locator("#beta-email").inputValue(), "");
    assert.equal(posts, name === "desktop" ? 2 : 1);
    await page.locator("#beta-success").scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${output}/${name}-success.png` });
    await page.close();
  }
  const page = await browser.newPage();
  await page.route("**/recruitment/config", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ accepting: false, policy_version: "2026-11-18.1", retention_days: 30, delivery: "on_page", min_age: 18, platform: "android" }) }));
  await page.goto(origin, { waitUntil: "networkidle" });
  assert.equal(await page.locator("#beta-form").isVisible(), false);
  assert.ok((await page.locator("#form-state").textContent()).includes("저장하지 않습니다"));
  await page.close();
  const invalid = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await invalid.goto(origin, { waitUntil: "networkidle" });
  await invalid.locator("#beta-form").waitFor({ state: "visible" });
  await invalid.locator("#beta-email").fill("synthetic-landing@example.invalid");
  for (const id of ["beta-adult", "beta-android", "beta-privacy"]) await invalid.locator(`#${id}`).check();
  let requests = 0;
  await invalid.route("**/recruitment/applications", async (route) => {
    requests++;
    await new Promise((resolve) => setTimeout(resolve, 300));
    await route.fulfill({ status: 202, contentType: "application/json", body: JSON.stringify({ accepted: true, delivery: "on_page", install_url: "https://evil.example.invalid/" }) });
  });
  await invalid.locator("#submit-beta").evaluate((button) => { button.click(); button.click(); });
  await invalid.locator("#form-error").waitFor({ state: "visible" });
  assert.equal(requests, 1, "double submit must be bounded");
  assert.equal(await invalid.locator("#beta-success").isVisible(), false, "unsafe receipt cannot show success");
  assert.equal(await invalid.locator("#install-link").getAttribute("href"), null);
  assert.equal(await invalid.locator("#beta-email").inputValue(), "synthetic-landing@example.invalid");
  await invalid.unroute("**/recruitment/applications");
  await invalid.route("**/recruitment/applications", (route) => route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ detail: { code: "recruitment_policy_changed" } }) }));
  await invalid.locator("#submit-beta").click();
  await invalid.waitForFunction(() => !document.getElementById("beta-privacy").checked);
  assert.equal(await invalid.locator("#config-retry").isVisible(), true);
  assert.deepEqual(failures, []);
  console.log("PASS: responsive assets, tabs, consent, persisted receipts, retry, closed intake, double-submit, unsafe receipt and stale policy");
} finally { await browser.close(); }
