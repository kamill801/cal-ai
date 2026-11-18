import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, writeFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { prepare } from "./prepare.mjs";

const source = await readFile(new URL("../../../services/api/app/web/beta/assets/landing.js", import.meta.url), "utf8");
const { validInstallUrl, validConfig, submissionPayload, failureMessage } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
const install = "https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/0ed6f218-7210-4ecf-9238-c522fa669bed";
const config = { accepting: true, policy_version: "2026-11-18.1", retention_days: 30, delivery: "on_page", min_age: 18, platform: "android" };

test("receipt only allows the approved Expo account and project", () => {
  assert.equal(validInstallUrl(install), true);
  for (const value of [undefined, "javascript:alert(1)", install.replace("expo.dev", "evil.test"), `${install}?token=secret`, `${install}#x`, install.replace("https://", "https://user:secret@"), install.replace("arche-trustfirstnutrition", "other"), install.replace("https:", "http:")]) {
    assert.equal(validInstallUrl(value), false);
  }
});
test("config must match visible consent and participation requirements", () => {
  assert.ok(validConfig(config));
  assert.ok(validConfig({ ...config, accepting: false }));
  for (const change of [{ accepting: "true" }, { policy_version: "old" }, { retention_days: 0 }, { retention_days: 31 }, { retention_days: 91 }, { delivery: "email" }, { min_age: 14 }, { platform: "ios" }]) assert.ok(!validConfig({ ...config, ...change }));
});
test("all participation confirmations are required and no extra profile data is sent", () => {
  const checks = { adult: true, android: true, privacy: true };
  assert.deepEqual(submissionPayload(" tester@example.invalid ", checks, config.policy_version), { email: "tester@example.invalid", adult_confirmed: true, platform: "android", privacy_consent: true, policy_version: config.policy_version, website: "" });
  for (const key of Object.keys(checks)) assert.throws(() => submissionPayload("x", { ...checks, [key]: false }, config.policy_version));
});
test("server errors are never reflected into the page", () => {
  assert.ok(failureMessage("<script>secret</script>").includes("완료하지 못했어요"));
  assert.ok(failureMessage("consent_changed").includes("동의"));
});
test("export privately preserves the SPA and publishes landing as the safe default", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "cal-ai-landing-build-"));
  try {
    await mkdir(path.join(root, "apps/mobile/dist-web-preview"), { recursive: true });
    await mkdir(path.join(root, "services/api/app/web/beta/assets"), { recursive: true });
    await writeFile(path.join(root, "apps/mobile/dist-web-preview/index.html"), "existing Expo app");
    await writeFile(path.join(root, "services/api/app/web/beta/assets/landing.js"), "landing");
    await writeFile(path.join(root, "services/api/app/web/beta/index.html"), "public landing");
    await prepare(root);
    assert.equal(await readFile(path.join(root, "public/index.html"), "utf8"), "public landing");
    assert.equal(await readFile(path.join(root, "services/api/app/web/preserved-app/index.html"), "utf8"), "existing Expo app");
    assert.equal(await readFile(path.join(root, "apps/mobile/dist-web-preview/index.html"), "utf8"), "existing Expo app");
    assert.equal(await readFile(path.join(root, "public/beta-assets/landing.js"), "utf8"), "landing");
  } finally { await rm(root, { recursive: true, force: true }); }
});
