import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

function isHttpsOrigin(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password && !url.search && !url.hash && url.pathname === "/" && !["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  } catch {
    return false;
  }
}

function isServerKey(value) {
  if (value?.startsWith("sb_secret_")) return true;
  try {
    const payload = JSON.parse(Buffer.from(value.split(".")[1], "base64url").toString("utf8"));
    return payload.role === "service_role";
  } catch {
    return false;
  }
}

export function checkStoreBuild({ app, pkg, env }) {
  const issues = [];
  const config = app.expo ?? {};
  if (!isHttpsOrigin(env.EXPO_PUBLIC_API_BASE_URL)) issues.push("EXPO_PUBLIC_API_BASE_URL must be an HTTPS API origin without credentials or query parameters.");
  if (env.EXPO_PUBLIC_AUTH_PROVIDER !== "supabase") issues.push("EXPO_PUBLIC_AUTH_PROVIDER must be supabase for store builds.");
  if (!isHttpsOrigin(env.EXPO_PUBLIC_SUPABASE_URL)) issues.push("EXPO_PUBLIC_SUPABASE_URL must be an HTTPS origin.");
  if (!env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY?.trim() || isServerKey(env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY)) issues.push("EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY must contain a client publishable/anon key, never a server secret.");
  if (!config.owner?.trim()) issues.push("expo.owner must identify the approved EAS owner.");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(config.extra?.eas?.projectId ?? "")) issues.push("expo.extra.eas.projectId must identify the linked EAS project.");
  if (config.android?.package !== "com.trustfirstnutrition.app") issues.push("expo.android.package must match the existing intended Play identity; review before changing it.");
  if (!Number.isSafeInteger(config.android?.versionCode) || config.android.versionCode < 1) issues.push("expo.android.versionCode must be a positive integer with the current local version source.");
  if (!config.icon?.startsWith("./assets/")) issues.push("expo.icon must reference the local opaque launcher icon.");
  if (!config.android?.adaptiveIcon?.foregroundImage?.startsWith("./assets/")) issues.push("expo.android.adaptiveIcon.foregroundImage must reference the local transparent foreground.");
  // SDK 54 is the first Expo baseline targeting API 36. The final AAB still needs inspection.
  const sdk = Number(/^(?:[~^])?(\d+)\./.exec(pkg.dependencies?.expo ?? "")?.[1]);
  if (!Number.isInteger(sdk) || sdk < 54) issues.push("Use an API 36-capable Expo baseline (SDK 54 or newer), then inspect the final AAB target SDK and native compatibility.");
  return issues;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const manual = process.argv.includes("--check");
  const androidStoreBuild = process.env.EAS_BUILD_PROFILE === "production" && process.env.EAS_BUILD_PLATFORM !== "ios";
  if (manual || androidStoreBuild) {
    const appRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
    const readJson = (name) => JSON.parse(readFileSync(join(appRoot, name), "utf8"));
    try {
      const issues = checkStoreBuild({ app: readJson("app.json"), pkg: readJson("package.json"), env: { ...readJson("eas.json").build.production.env, ...process.env } });
      for (const issue of issues) process.stderr.write(`Store build blocked: ${issue}\n`);
      if (issues.length) process.exitCode = 1;
      else process.stdout.write("Store configuration preflight passed. Signing, final AAB, policy and device verification are still required.\n");
    } catch {
      process.stderr.write("Store build blocked: unable to read the app/package/EAS JSON configuration.\n");
      process.exitCode = 1;
    }
  }
}
