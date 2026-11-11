import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { checkStoreBuild } from "./check-store-build.mjs";

function fixture() {
  return {
    app: { expo: { icon: "./assets/brand/app-icon.png", owner: "fixture-owner", extra: { eas: { projectId: "11111111-2222-4333-8444-555555555555" } }, android: { package: "com.trustfirstnutrition.app", versionCode: 1, adaptiveIcon: { foregroundImage: "./assets/brand/adaptive-foreground.png" } } } },
    pkg: { dependencies: { expo: "54.0.0" } },
    env: { EAS_BUILD_PLATFORM: "android", EAS_BUILD_PROFILE: "production", EXPO_PUBLIC_API_BASE_URL: "https://cal-ai-api.vercel.app", EXPO_PUBLIC_AUTH_PROVIDER: "supabase", EXPO_PUBLIC_SUPABASE_URL: "https://fixture.supabase.co", EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "fixture-publishable-value" }
  };
}

test("accepts a complete configuration without claiming a validated binary", () => {
  assert.deepEqual(checkStoreBuild(fixture()), []);
});

for (const name of ["EXPO_PUBLIC_AUTH_PROVIDER", "EXPO_PUBLIC_SUPABASE_URL", "EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "EXPO_PUBLIC_API_BASE_URL"]) {
  test(`fails closed without ${name}`, () => {
    const input = fixture();
    delete input.env[name];
    assert.ok(checkStoreBuild(input).some((issue) => issue.includes(name)));
  });
}

test("rejects disabled auth and unsafe API destinations", () => {
  for (const url of ["http://localhost:8015", "https://user:password@cal-ai-api.vercel.app", "https://cal-ai-api.vercel.app/?token=private", "not-a-url"]) {
    const input = fixture();
    input.env.EXPO_PUBLIC_API_BASE_URL = url;
    input.env.EXPO_PUBLIC_AUTH_PROVIDER = "disabled";
    const issues = checkStoreBuild(input);
    assert.ok(issues.some((issue) => issue.includes("EXPO_PUBLIC_API_BASE_URL")));
    assert.ok(issues.some((issue) => issue.includes("EXPO_PUBLIC_AUTH_PROVIDER")));
    assert.ok(issues.every((issue) => !issue.includes(url)));
  }
});

test("rejects missing EAS identity, package and local version code", () => {
  const input = fixture();
  input.app.expo = { android: {} };
  const issues = checkStoreBuild(input);
  for (const name of ["owner", "projectId", "package", "versionCode"]) {
    assert.ok(issues.some((issue) => issue.includes(name)));
  }
});

test("rejects the old SDK 53 baseline, not just successful JS bundling", () => {
  const input = fixture();
  input.pkg.dependencies.expo = "53.0.27";
  assert.ok(checkStoreBuild(input).some((issue) => issue.includes("API 36")));
});

test("blocks a store build without local launcher and adaptive artwork", () => {
  const input = fixture();
  delete input.app.expo.icon;
  delete input.app.expo.android.adaptiveIcon.foregroundImage;
  const issues = checkStoreBuild(input);
  assert.ok(issues.some((issue) => issue.includes("expo.icon")));
  assert.ok(issues.some((issue) => issue.includes("foregroundImage")));
});

test("diagnostics never echo supplied public values or potential secrets", () => {
  const input = fixture();
  input.env.EXPO_PUBLIC_SUPABASE_URL = "private-sentinel-value";
  input.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = "sb_secret_do-not-log";
  const output = JSON.stringify(checkStoreBuild(input));
  assert.ok(!output.includes("private-sentinel-value"));
  assert.ok(!output.includes("sb_secret_do-not-log"));
  assert.ok(output.includes("PUBLISHABLE_KEY"));
});

test("rejects a legacy service-role JWT but permits a legacy anon JWT", () => {
  const input = fixture();
  const key = (role) => `fixture.${Buffer.from(JSON.stringify({ role })).toString("base64url")}.fixture`;
  input.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = key("service_role");
  assert.ok(checkStoreBuild(input).some((issue) => issue.includes("PUBLISHABLE_KEY")));
  input.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY = key("anon");
  assert.deepEqual(checkStoreBuild(input), []);
});

const readJson = (path) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));

test("Vercel web exports use the same origin while native production keeps its API URL", () => {
  const vercel = readJson("../../../vercel.json");
  const eas = readJson("../eas.json");
  assert.equal(vercel.buildCommand, "EXPO_PUBLIC_API_BASE_URL=/ npm --workspace apps/mobile run export:web:vercel");
  assert.equal(eas.build.production.env.EXPO_PUBLIC_API_BASE_URL, "https://cal-ai-api.vercel.app");
});

test("keeps the intended app identity, version source and narrow permissions", () => {
  const { expo } = readJson("../app.json");
  const eas = readJson("../eas.json");
  assert.equal(expo.name, "Trust First Nutrition");
  assert.equal(expo.scheme, "trustfirstnutrition");
  assert.equal(expo.android.package, "com.trustfirstnutrition.app");
  assert.equal(expo.android.versionCode, 1);
  assert.equal(expo.android.allowBackup, false);
  assert.deepEqual(expo.android.permissions, ["CAMERA"]);
  for (const permission of ["SYSTEM_ALERT_WINDOW", "USE_BIOMETRIC", "USE_FINGERPRINT", "VIBRATE", "RECORD_AUDIO", "READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO", "READ_MEDIA_VISUAL_USER_SELECTED", "READ_EXTERNAL_STORAGE", "MANAGE_EXTERNAL_STORAGE"]) {
    assert.ok(expo.android.blockedPermissions.includes(`android.permission.${permission}`));
  }
  // SDK 54's native camera still requires write access on Android API 24-28.
  assert.ok(!expo.android.blockedPermissions.includes("android.permission.WRITE_EXTERNAL_STORAGE"));
  assert.equal(expo.plugins.find((plugin) => Array.isArray(plugin) && plugin[0] === "expo-image-picker")[1].microphonePermission, false);
  assert.equal(eas.cli.appVersionSource, "local");
  assert.equal(eas.build.production.android.buildType, "app-bundle");
  assert.equal(eas.build.preview.environment, "preview");
  assert.equal(eas.build.production.environment, "production");
  assert.ok(expo.plugins.includes("./plugins/with-legacy-camera-storage.cjs"));
});

test("legacy camera storage permission is scoped, idempotent and preserves unrelated permissions", async () => {
  const require = createRequire(import.meta.url);
  const plugin = require("../plugins/with-legacy-camera-storage.cjs");
  const camera = { $: { "android:name": "android.permission.CAMERA" } };
  for (const permissions of [undefined, [camera], [{ $: { "android:name": "android.permission.WRITE_EXTERNAL_STORAGE", "android:maxSdkVersion": "32" } }, camera]]) {
    const config = plugin({});
    const input = { modRequest: {}, modResults: { manifest: permissions ? { "uses-permission": structuredClone(permissions) } : {} } };
    const first = await config.mods.android.manifest(input);
    const second = await config.mods.android.manifest(first);
    const final = second.modResults.manifest["uses-permission"];
    const storage = final.filter((permission) => permission.$["android:name"] === "android.permission.WRITE_EXTERNAL_STORAGE");
    assert.equal(storage.length, 1);
    assert.equal(storage[0].$["android:maxSdkVersion"], "28");
    if (permissions?.includes(camera)) assert.deepEqual(final.find((permission) => permission.$["android:name"] === "android.permission.CAMERA"), camera);
  }
});

test("cloud archive excludes private material while preserving mobile build inputs", () => {
  const require = createRequire(import.meta.url);
  const ignore = require("ignore")().add(readFileSync(new URL("../../../.easignore", import.meta.url), "utf8"));
  for (const path of [
    ".git/config", ".omx/state/state.json", ".codex/config.toml",
    ".env.local", "apps/mobile/.env.local", "services/api/.env",
    "services/api/app/main.py", "docs/marketing/screenshots/user.png",
    "apps/admin/src/App.tsx", "apps/mobile/credentials.json",
    "apps/mobile/release.jks", "apps/mobile/release.keystore",
    "apps/mobile/service-account.key", "apps/mobile/private.pem",
    "apps/mobile/node_modules/module/index.js", "apps/mobile/src/dev/smokeRunner.ts",
    "apps/mobile/assets/brand/source/icon-master.png",
  ]) assert.ok(ignore.ignores(path), `${path} must stay local`);
  for (const path of [
    "package.json", "package-lock.json", "packages/shared/src/index.ts",
    "apps/mobile/App.tsx", "apps/mobile/app.json", "apps/mobile/eas.json",
    "apps/mobile/scripts/check-store-build.mjs",
    "apps/mobile/plugins/with-legacy-camera-storage.cjs",
    "apps/mobile/assets/brand/app-icon.png",
    "apps/mobile/assets/brand/adaptive-foreground.png",
    "apps/mobile/assets/mascot/mascot-meal.png",
  ]) assert.ok(!ignore.ignores(path), `${path} is a required build input`);
});

test("pins the installed Expo baseline and aligns root React overrides", () => {
  const pkg = readJson("../package.json");
  const root = readJson("../../../package.json");
  const require = createRequire(import.meta.url);
  const bundled = require("expo/bundledNativeModules.json");
  const semver = require("semver");
  assert.equal(pkg.dependencies.expo, "54.0.38");
  assert.equal(require("expo/package.json").version, pkg.dependencies.expo);
  for (const [name, version] of Object.entries(pkg.dependencies)) {
    if (!bundled[name]) continue;
    assert.ok(semver.valid(version), `${name} must be pinned`);
    assert.ok(semver.satisfies(version, bundled[name]), `${name} must match bundledNativeModules`);
  }
  for (const name of ["react", "react-dom", "react-native"]) {
    assert.equal(root.overrides[name], pkg.dependencies[name]);
    assert.equal(root.devDependencies[name], pkg.dependencies[name]);
  }
});

test("EAS hook blocks Android production without reading local credentials", () => {
  const env = { PATH: process.env.PATH, EAS_BUILD_PLATFORM: "android", EAS_BUILD_PROFILE: "production" };
  const run = (extra) => spawnSync(process.execPath, [new URL("./check-store-build.mjs", import.meta.url).pathname], { env: { ...env, ...extra }, encoding: "utf8" });
  const android = run({});
  assert.equal(android.status, 1);
  for (const name of ["EXPO_PUBLIC_AUTH_PROVIDER", "EXPO_PUBLIC_SUPABASE_URL", "EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY"]) {
    assert.ok(android.stderr.includes(name));
  }
  for (const extra of [{ EAS_BUILD_PROFILE: "preview" }, { EAS_BUILD_PLATFORM: "ios" }]) {
    const skipped = run(extra);
    assert.equal(skipped.status, 0);
    assert.equal(skipped.stdout + skipped.stderr, "");
  }
});

test("gallery opens the SDK system picker without requesting broad library permission", () => {
  const require = createRequire(import.meta.url);
  const ts = require("typescript");
  const source = ts.createSourceFile("mealImagePicker.ts", readFileSync(new URL("../src/media/mealImagePicker.ts", import.meta.url), "utf8"), ts.ScriptTarget.Latest, true);
  const picker = source.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "pickMealImageFromLibrary");
  assert.ok(picker?.body);
  const awaited = [];
  const inspect = (node) => {
    if (ts.isAwaitExpression(node) && ts.isCallExpression(node.expression)) awaited.push(node.expression.expression.getText(source));
    ts.forEachChild(node, inspect);
  };
  inspect(picker.body);
  assert.equal(awaited[0], "ImagePicker.launchImageLibraryAsync");
  assert.ok(!awaited.includes("ImagePicker.requestMediaLibraryPermissionsAsync"));
});
