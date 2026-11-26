import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { runInNewContext } from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const root = resolve(dirname(new URL(import.meta.url).pathname), "../../..");
const mobile = resolve(root, "apps/mobile");
const shared = resolve(root, "packages/shared/src/index.ts");

function moduleFrom(file, overrides = {}, append = "") {
  const exports = {};
  const context = { exports, React: overrides.react, process: { env: {} }, Date, Math, JSON, Promise, setInterval, clearInterval,
    require(id) {
      if (id in overrides) return overrides[id];
      if (id === "@cal-ai/shared") return moduleFrom(shared);
      if (id.endsWith("config")) return { getApiBaseUrl: () => "https://fixture.invalid" };
      if (id.startsWith(".")) {
        const path = resolve(dirname(file), id);
        const resolved = [path + ".ts", path + ".tsx", resolve(path, "index.ts")].find(existsSync);
        if (resolved) return moduleFrom(resolved, overrides);
      }
      throw new Error(`Unexpected module ${id}`);
    },
    fetch: (...args) => overrides.fetch(...args)
  };
  runInNewContext(ts.transpileModule(readFileSync(file, "utf8") + append, {
    fileName: file,
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React }
  }).outputText, context);
  return exports;
}

const status = (health = false, analytics = false, version = "2026-11-16.1") => ({
  policy_version: version, health_data_consent: health, analytics_consent: analytics,
  consented_at: health ? "2026-11-16T00:00:00Z" : null
});
const response = (body, code = 200) => ({ ok: code < 400, status: code, json: async () => body });
const denied = (error) => error.code === "health_data_consent_required";

test("API blocks health inputs, profile restore and reads before consent, but permits account deletion", async () => {
  const calls = [];
  const { createCalAiApiClient } = moduleFrom(resolve(mobile, "src/api/client.ts"), {
    fetch: async (url) => { calls.push(url); return response({ status: "pending" }); }
  });
  const client = createCalAiApiClient("https://fixture.invalid", "owner-a");
  for (const operation of [() => client.getAuthenticatedProfile(), () => client.createOnboarding({ age: 29 }),
    () => client.logWeight("p", { weightKg: 70 }), () => client.getProgress("p"),
    () => client.presignImageUpload({ fileName: "photo.png" })]) await assert.rejects(operation, denied);
  assert.equal(calls.length, 0);
  assert.equal((await client.deleteAccount()).status, "pending");
  assert.equal(calls.length, 1);
});

test("GET/PUT use current server version, exact snake_case, and independent analytics choice", async () => {
  const calls = [];
  const { createCalAiApiClient } = moduleFrom(resolve(mobile, "src/api/client.ts"), {
    fetch: async (url, init) => {
      calls.push({ url, init });
      if (url.endsWith("privacy-consent")) return response(init.method === "PUT" ? status(true, false, "future-policy") : status(false, false, "future-policy"));
      return response({ profile_id: "p" });
    }
  });
  const client = createCalAiApiClient("https://fixture.invalid", "owner-a");
  const initial = await client.getPrivacyConsent();
  await assert.rejects(() => client.getAuthenticatedProfile(), denied);
  const accepted = await client.updatePrivacyConsent({ policyVersion: initial.policyVersion, healthDataConsent: true, analyticsConsent: false });
  assert.equal(accepted.analyticsConsent, false);
  assert.equal(JSON.stringify(JSON.parse(calls[1].init.body)), JSON.stringify({ policy_version: "future-policy", health_data_consent: true, analytics_consent: false }));
  assert.equal(calls[1].init.headers.Authorization, "Bearer owner-a");
  assert.equal((await client.getAuthenticatedProfile()).profileId, "p");
  client.clearPrivacyConsent();
  await assert.rejects(() => client.getAuthenticatedProfile(), denied);
  const ownerB = createCalAiApiClient("https://fixture.invalid", "owner-b");
  await assert.rejects(() => ownerB.getAuthenticatedProfile(), denied);
});

test("malformed booleans, failed GET/PUT and server 403 never leave health access open", async () => {
  let next = response(status(true));
  let invalidations = 0;
  const { createCalAiApiClient } = moduleFrom(resolve(mobile, "src/api/client.ts"), { fetch: async () => next });
  const client = createCalAiApiClient("https://fixture.invalid", "owner", () => { invalidations += 1; });
  await client.getPrivacyConsent();
  next = response({ ...status(), health_data_consent: "true" });
  await assert.rejects(() => client.getPrivacyConsent(), (error) => error.code === "privacy_consent_response_invalid");
  await assert.rejects(() => client.getProgress("p"), denied);
  next = response(status(true));
  await client.getPrivacyConsent();
  next = response({ detail: { code: "privacy_consent_unavailable", message: "retry", kind: "server", retryable: true } }, 503);
  await assert.rejects(() => client.updatePrivacyConsent({ policyVersion: "2026-11-16.1", healthDataConsent: false, analyticsConsent: false }));
  await assert.rejects(() => client.getProgress("p"), denied);
  next = response(status(true));
  await client.getPrivacyConsent();
  next = response({ detail: { code: "health_data_consent_required", message: "consent", kind: "validation", retryable: false } }, 403);
  await assert.rejects(() => client.getProgress("p"), denied);
  assert.equal(invalidations, 1);
  await assert.rejects(() => client.getProgress("p"), denied);
});

test("signed image upload rechecks consent after presign and never sends bytes after revoke", async () => {
  let allowed = true;
  let uploads = 0;
  const { uploadImageToStorage } = moduleFrom(resolve(mobile, "src/api/imageUpload.ts"), {
    "../media/mealImageFile": { readMealImageBlob: async () => "fixture-blob", MealImageReadError: Error },
    fetch: async () => { uploads += 1; return response({}); }
  });
  const api = {
    assertHealthConsent() { if (!allowed) throw Object.assign(new Error("denied"), { code: "health_data_consent_required" }); },
    presignImageUpload: async () => { allowed = false; return { uploadUrl: "https://fixture.invalid/signed" }; },
    completeImageUpload: async () => { throw new Error("must not complete"); }
  };
  await assert.rejects(() => uploadImageToStorage({ uri: "fixture" }, api), denied);
  assert.equal(uploads, 0);
});

function analyticsHarness() {
  const values = new Map();
  const counts = { reads: 0, writes: 0, removes: 0, posts: [] };
  let read = async (key) => values.get(key) ?? null;
  const storage = { getItem: async (key) => { counts.reads += 1; return read(key); },
    setItem: async (key, value) => { counts.writes += 1; values.set(key, value); },
    removeItem: async (key) => { counts.removes += 1; values.delete(key); } };
  const exports = moduleFrom(resolve(mobile, "src/analytics/client.ts"), {
    "@react-native-async-storage/async-storage": { default: storage },
    "react-native": { AppState: { currentState: "active", addEventListener: () => ({ remove() {} }) } },
    "../api": moduleFrom(resolve(mobile, "src/api/client.ts")),
    fetch: async (_url, init) => { counts.posts.push(JSON.parse(init.body)); return response({}); }
  });
  return { ...exports, counts, values, delayRead: (callback) => { read = callback; } };
}

test("analytics is inert by default, strips health properties, and erases owner-scoped IDs on revoke", async () => {
  const h = analyticsHarness();
  let allowed = false;
  const client = h.createAnalyticsEventClient("https://fixture.invalid", "a", "user:a", () => allowed);
  await client.trackEvent({ eventName: "app_opened", screen: "onboarding" });
  await client.sendHeartbeat();
  assert.equal(await client.getSessionId(), undefined);
  assert.deepEqual([h.counts.reads, h.counts.writes, h.counts.posts.length], [0, 0, 0]);
  allowed = true;
  await client.trackEvent({ eventName: "onboarding_completed", screen: "onboarding", properties: {
    answer: "half", clarification: "half", duration_minutes: 30, goal_type: "lose", session_rpe: 7, training_frequency: "5+", weight_kg: 70, note: "private", code: "ok", status: "completed"
  } });
  assert.deepEqual(h.counts.posts[0].properties, { code: "ok", status: "completed" });
  allowed = false;
  await client.clearSession();
  await client.sendHeartbeat();
  assert.equal(h.values.size, 0);
  assert.equal(h.counts.posts.length, 1);
  const ownerB = h.createAnalyticsEventClient("https://fixture.invalid", "b", "user:b");
  await ownerB.trackEvent({ eventName: "app_opened", screen: "onboarding" });
  assert.equal(h.counts.posts.length, 1);
});

test("revocation during a pending storage read cannot recreate an ID or post", async () => {
  const h = analyticsHarness();
  let resolveRead;
  h.delayRead(() => new Promise((resolve) => { resolveRead = resolve; }));
  let allowed = true;
  const client = h.createAnalyticsEventClient("https://fixture.invalid", "a", "user:a", () => allowed);
  const sending = client.sendHeartbeat();
  await Promise.resolve();
  allowed = false;
  const clearing = client.clearSession();
  resolveRead(null);
  await Promise.all([sending, clearing]);
  assert.equal(h.counts.writes, 0);
  assert.equal(h.counts.posts.length, 0);
  assert.equal(h.values.size, 0);
});

function hooksHarness() {
  const slots = [];
  let cursor = 0;
  let dirty = true;
  const pending = [];
  const same = (left, right) => left && right && left.length === right.length && left.every((item, index) => Object.is(item, right[index]));
  const React = {
    createElement: (type, props, ...children) => ({ type, props: props ?? {}, children }),
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = typeof initial === "function" ? initial() : initial;
      return [slots[index], (value) => {
        const next = typeof value === "function" ? value(slots[index]) : value;
        if (!Object.is(next, slots[index])) { slots[index] = next; dirty = true; }
      }];
    },
    useRef(initial) { const index = cursor++; return slots[index] ??= { current: initial }; },
    useMemo(factory, dependencies) {
      const index = cursor++;
      if (!same(slots[index]?.dependencies, dependencies)) slots[index] = { value: factory(), dependencies };
      return slots[index].value;
    },
    useEffect(effect, dependencies) {
      const index = cursor++;
      if (!same(slots[index]?.dependencies, dependencies)) {
        const previous = slots[index];
        slots[index] = { dependencies, cleanup: previous?.cleanup };
        pending.push(() => { previous?.cleanup?.(); slots[index].cleanup = effect(); });
      }
    }
  };
  React.useCallback = (callback, dependencies) => React.useMemo(() => callback, dependencies);
  React.useReducer = (reducer, initial, initialize) => {
    const [value, setValue] = React.useState(() => initialize ? initialize(initial) : initial);
    return [value, (action) => setValue((current) => reducer(current, action))];
  };
  return { React, render(component, props) { cursor = 0; dirty = false; return component(props); },
    effects() { pending.splice(0).forEach((effect) => effect()); }, isDirty: () => dirty,
    unmount() { slots.forEach((slot) => slot?.cleanup?.()); } };
}

function nativeComponents() {
  return Object.fromEntries(["View", "Text", "TouchableOpacity", "ScrollView", "SafeAreaView", "ActivityIndicator", "Modal", "TextInput", "KeyboardAvoidingView"].map((name) => [name, name]));
}
function nodes(tree) {
  if (!tree || typeof tree !== "object") return [];
  return [tree, ...tree.children.flat(Infinity).flatMap(nodes)];
}

test("consent UI starts unchecked, permits health without analytics, exposes management/error/retry", () => {
  const h = hooksHarness();
  const screen = moduleFrom(resolve(mobile, "src/screens/PrivacyConsentScreen.tsx"), {
    react: h.React, "react-native": { ...nativeComponents(), StyleSheet: { create: (value) => value } },
    "lucide-react-native": { Check: "Check" }, "../components/TrustBuddy": { TrustBuddy: "TrustBuddy" }
  });
  const submitted = [];
  const props = { policyVersion: "future", status: "success", onSubmit: (value) => submitted.push(value), onManage() {}, onRetry() {}, onSignOut() {} };
  let tree = h.render(screen.PrivacyConsentScreen, props);
  let checkboxes = nodes(tree).filter((node) => node.type === screen.ConsentCheckbox);
  assert.deepEqual(checkboxes.map((node) => node.props.checked), [false, false]);
  assert.equal(nodes(tree).find((node) => node.props.accessibilityLabel === "선택한 동의 저장 후 계속").props.disabled, true);
  checkboxes[0].props.onChange();
  tree = h.render(screen.PrivacyConsentScreen, props);
  nodes(tree).find((node) => node.props.accessibilityLabel === "선택한 동의 저장 후 계속").props.onPress();
  assert.deepEqual(submitted, [false]);
  const checkbox = h.render(screen.ConsentCheckbox, { label: "필수", checked: false, onChange() {} });
  assert.equal(checkbox.props.accessibilityRole, "checkbox");
  assert.equal(checkbox.props.accessibilityState.checked, false);
  tree = h.render(screen.PrivacyConsentScreen, { ...props, status: "loading", error: "retry" });
  assert.equal(nodes(tree).find((node) => node.props.accessibilityLabel === "선택한 동의 저장 후 계속").props.disabled, true);
  assert.ok(nodes(tree).find((node) => node.props.accessibilityRole === "alert"));
  assert.ok(nodes(tree).find((node) => node.props.onPress === props.onManage));
  assert.ok(nodes(tree).find((node) => node.props.onPress === props.onRetry));
});

function appHarness(initialStatus, deletionIntent = false) {
  const h = hooksHarness();
  const calls = { health: 0, events: 0, heartbeat: 0, clears: 0, puts: [], deletion: 0, profileDeletion: [], profileClears: 0, signOut: 0 };
  let readStatus = async () => initialStatus;
  let writeStatus = async (input) => ({ ...input, consentedAt: "now" });
  let clearSession = async () => {};
  let clearProfile = async () => {};
  let storedProfileId;
  let accountResult = { status: "pending" };
  const healthData = async (value) => { calls.health += 1; return value; };
  const api = {
    getPrivacyConsent: () => readStatus(), updatePrivacyConsent: async (input) => { calls.puts.push(input); return writeStatus(input); }, clearPrivacyConsent() {},
    getAuthenticatedProfile: () => healthData({ profileId: storedProfileId ?? null }),
    getCoachDashboard: () => healthData({}), getProgress: () => healthData({ bodyCheckIns: [] }),
    getWeeklyCoach: () => healthData({}), getWorkoutPlan: () => healthData({}), getWorkoutHistory: () => healthData({}),
    createOnboarding: async () => { calls.health += 1; return {}; },
    deleteProfile: async (profileId) => { calls.profileDeletion.push(profileId); },
    deleteAccount: async () => { calls.deletion += 1; return accountResult; }
  };
  const analytics = { trackEvent: async () => { calls.events += 1; }, clearSession: async () => { calls.clears += 1; await clearSession(); } };
  const apiExports = moduleFrom(resolve(mobile, "src/api/client.ts"));
  const overrides = {
    react: h.React, "react-native": { ...nativeComponents(), StyleSheet: { create: (value) => value }, Platform: { OS: "web" }, Alert: {}, useWindowDimensions: () => ({ width: 390, height: 844 }) },
    "expo-status-bar": { StatusBar: "StatusBar" },
    "./src/api": { ...apiExports, createCalAiApiClient: () => api },
    "./src/analytics": { createAnalyticsEventClient: () => analytics, createForegroundHeartbeat: () => ({ start() { calls.heartbeat += 1; }, stop() {} }) },
    "./src/auth/useAuthSession": {}, "./src/api/imageUpload": {}, "./src/media/mealImagePicker": {},
    "./src/flow/scanToSaveFlow": { createInitialScanToSaveState: () => ({ screen: "today" }), scanToSaveReducer: (state) => state },
    "./src/session/profileSession": { loadProfileId: async () => storedProfileId, clearProfileId: async () => { calls.profileClears += 1; await clearProfile(); }, saveProfileId: async () => {} },
    "./src/session/accountDeletionIntent": { readWebAccountDeletionIntent: () => deletionIntent, dismissWebAccountDeletionIntent() {} }
  };
  for (const name of ["AnalyzeEvidenceScreen", "ClarificationScreen", "OnboardingScreen", "PrivacyConsentScreen", "PlanScreen", "LoginScreen", "ReviewResultScreen", "SafetyPrivacyScreen", "SavedImpactScreen", "TodayDashboardScreen", "TrainingScreen", "ProgressScreen", "WeeklyCoachScreen"]) overrides[`./src/screens/${name}`] = { [name]: name };
  overrides["./src/components/AppBottomNav"] = { AppBottomNav: "AppBottomNav" };
  const { OwnerApp } = moduleFrom(resolve(mobile, "App.tsx"), overrides, "\nexport { OwnerApp };\n");
  const props = { auth: { ready: true, enabled: true, session: { access_token: "a", user: { id: "a" } }, signOut: async () => { calls.signOut += 1; return true; } }, scope: "user:a" };
  let tree;
  async function flush() {
    for (let iteration = 0; iteration < 15; iteration += 1) {
      tree = h.render(OwnerApp, props);
      h.effects();
      await new Promise((resolve) => setImmediate(resolve));
      if (!h.isDirty()) return tree;
    }
    throw new Error("App did not settle");
  }
  return { calls, flush, props, ApiClientError: apiExports.ApiClientError, unmount: h.unmount,
    component: (name) => nodes(tree).find((node) => node.type === name),
    cleanup: (callback) => { clearSession = callback; },
    profileCleanup: (callback) => { clearProfile = callback; },
    profile: (profileId) => { storedProfileId = profileId; },
    accountResult: (result) => { accountResult = result; },
    read: (callback) => { readStatus = callback; }, write: (callback) => { writeStatus = callback; } };
}

const clientStatus = (health = false, analytics = false) => ({ policyVersion: "future-policy", healthDataConsent: health, analyticsConsent: analytics, consentedAt: health ? "now" : null });

test("existing-user startup waits for GET and affirmative PUT; analytics stays off; management remains reachable", async () => {
  const h = appHarness(clientStatus());
  let finishGet;
  h.read(() => new Promise((resolve) => { finishGet = resolve; }));
  await h.flush();
  assert.deepEqual([h.calls.health, h.calls.events, h.calls.heartbeat], [0, 0, 0]);
  h.component("PrivacyConsentScreen").props.onManage();
  await h.flush();
  assert.ok(h.component("SafetyPrivacyScreen").props.onDeleteAccount);
  h.component("SafetyPrivacyScreen").props.onBack();
  finishGet(clientStatus());
  await h.flush();
  h.component("PrivacyConsentScreen").props.onSubmit(false);
  await h.flush();
  assert.equal(h.calls.puts[0].policyVersion, "future-policy");
  assert.equal(h.calls.puts[0].analyticsConsent, false);
  assert.equal(h.calls.health, 1);
  assert.equal(h.calls.events + h.calls.heartbeat, 0);
});

test("settings revoke health with both flags false, stop analytics, preserve deletion and never auto-delete", async () => {
  const h = appHarness(clientStatus());
  await h.flush();
  h.component("PrivacyConsentScreen").props.onSubmit(true);
  await h.flush();
  assert.ok(h.calls.events > 0 && h.calls.heartbeat > 0);
  const onboarding = h.component("OnboardingScreen");
  assert.ok(onboarding);
  // The ordinary onboarding page also exposes the management entry.
  const tree = await h.flush();
  const entry = nodes(tree).find((node) => node.type === "TouchableOpacity" && node.children.flat(Infinity).some((child) => child?.children?.includes("개인정보와 계정 관리")));
  entry.props.onPress();
  await h.flush();
  const before = h.calls.events + h.calls.heartbeat;
  h.component("SafetyPrivacyScreen").props.onRevokeHealth();
  await h.flush();
  assert.equal(h.calls.puts.at(-1).healthDataConsent, false);
  assert.equal(h.calls.puts.at(-1).analyticsConsent, false);
  assert.equal(h.calls.events + h.calls.heartbeat, before);
  assert.equal(h.calls.deletion, 0);
  h.component("SafetyPrivacyScreen").props.onBack();
  await h.flush();
  assert.ok(h.component("PrivacyConsentScreen"));
});

test("late consent after owner unmount cannot restore or start analytics", async () => {
  const h = appHarness(clientStatus());
  let finish;
  h.read(() => new Promise((resolve) => { finish = resolve; }));
  await h.flush();
  h.unmount();
  finish(clientStatus(true, true));
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual([h.calls.health, h.calls.events, h.calls.heartbeat], [0, 0, 0]);
});

test("direct deletion intent and signed-out login never require health consent", async () => {
  const deletion = appHarness(clientStatus(), true);
  deletion.read(async () => { throw new Error("deletion should not need GET consent"); });
  await deletion.flush();
  assert.ok(deletion.component("SafetyPrivacyScreen"));
  deletion.component("SafetyPrivacyScreen").props.onDeleteAccount();
  await deletion.flush();
  assert.equal(deletion.calls.deletion, 1);
  assert.equal(deletion.calls.health + deletion.calls.events + deletion.calls.heartbeat, 0);
  const signedOut = appHarness(clientStatus());
  signedOut.props.auth.session = undefined;
  await signedOut.flush();
  assert.ok(signedOut.component("LoginScreen"));
  assert.equal(signedOut.calls.health + signedOut.calls.events + signedOut.calls.heartbeat, 0);
});

async function openManagement(h) {
  const tree = await h.flush();
  const dashboard = h.component("TodayDashboardScreen");
  if (dashboard) dashboard.props.onOpenSafety();
  else {
    const entry = nodes(tree).find((node) => node.type === "TouchableOpacity" && node.children.flat(Infinity).some((child) => child?.children?.includes("개인정보와 계정 관리")));
    entry.props.onPress();
  }
  await h.flush();
}

test("analytics-only revoke retains health consent; failed save stays stopped and retries the same choice", async () => {
  const h = appHarness(clientStatus(true, true));
  await openManagement(h);
  let fail = true;
  h.write(async (input) => {
    if (fail) throw new Error("offline");
    return { ...input, consentedAt: "now" };
  });
  h.component("SafetyPrivacyScreen").props.onChangeAnalytics(false);
  await h.flush();
  const blocked = h.calls.events + h.calls.heartbeat;
  assert.ok(h.component("SafetyPrivacyScreen").props.consentError);
  assert.equal(h.component("SafetyPrivacyScreen").props.analyticsEnabled, false);
  assert.equal(h.calls.puts.at(-1).healthDataConsent, true);
  fail = false;
  h.component("SafetyPrivacyScreen").props.onRetryConsent();
  await h.flush();
  assert.equal(h.calls.puts.at(-1).healthDataConsent, true);
  assert.equal(h.calls.puts.at(-1).analyticsConsent, false);
  assert.equal(h.component("SafetyPrivacyScreen").props.canChangeAnalytics, true);
  assert.equal(h.calls.events + h.calls.heartbeat, blocked);
});

test("policy changes between GET and PUT refresh disclosure without implicit acceptance", async () => {
  const h = appHarness(clientStatus());
  await h.flush();
  h.write(async () => { throw new h.ApiClientError({ message: "changed", code: "privacy_policy_version_changed" }); });
  h.read(async () => ({ ...clientStatus(), policyVersion: "future-policy-2" }));
  h.component("PrivacyConsentScreen").props.onSubmit(false);
  await h.flush();
  assert.equal(h.component("PrivacyConsentScreen").props.policyVersion, "future-policy-2");
  assert.equal(h.calls.health, 0);
  assert.equal(h.calls.puts.length, 1);
});

test("device storage failure does not prevent server revocation and leaves local gates closed", async () => {
  const h = appHarness(clientStatus(true, true));
  await openManagement(h);
  h.cleanup(async () => { throw new Error("storage unavailable"); });
  h.component("SafetyPrivacyScreen").props.onRevokeHealth();
  await h.flush();
  assert.equal(h.calls.puts.at(-1).healthDataConsent, false);
  assert.equal(h.calls.puts.at(-1).analyticsConsent, false);
  assert.equal(h.component("SafetyPrivacyScreen").props.canChangeAnalytics, false);
  assert.ok(h.component("SafetyPrivacyScreen").props.consentError);
});

for (const kind of ["data", "account"]) {
  test(`${kind} deletion sends DELETE once despite analytics cleanup rejection, without telemetry`, async () => {
    const h = appHarness(clientStatus(true, true));
    h.profile("deleted-profile");
    await openManagement(h);
    const before = h.calls.events + h.calls.heartbeat;
    h.cleanup(async () => { throw new Error("storage unavailable"); });
    const action = kind === "data" ? "onDeleteData" : "onDeleteAccount";
    h.component("SafetyPrivacyScreen").props[action]();
    await h.flush();
    await h.flush();
    assert.equal(h.calls.profileDeletion.length + h.calls.deletion, 1);
    assert.equal(h.calls.profileDeletion.length, kind === "data" ? 1 : 0);
    assert.equal(h.calls.events + h.calls.heartbeat, before);
    h.component("PrivacyConsentScreen")?.props.onManage();
    await h.flush();
    const management = h.component("SafetyPrivacyScreen");
    assert.equal(management.props.analyticsEnabled, false);
    assert.equal(management.props.deletionStatus, kind === "data" ? "success" : "idle");
  });

  test(`${kind} deletion still stops at the owner guard after a pending cleanup rejects`, async () => {
    const h = appHarness(clientStatus(true, true));
    h.profile("old-owner-profile");
    await openManagement(h);
    let rejectCleanup;
    const cleanup = new Promise((_, reject) => { rejectCleanup = reject; });
    h.cleanup(() => cleanup);
    const before = h.calls.events + h.calls.heartbeat;
    h.component("SafetyPrivacyScreen").props[kind === "data" ? "onDeleteData" : "onDeleteAccount"]();
    h.unmount();
    rejectCleanup(new Error("old owner storage unavailable"));
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(h.calls.profileDeletion.length + h.calls.deletion, 0);
    assert.equal(h.calls.events + h.calls.heartbeat, before);
    assert.equal(h.calls.signOut, 0);
  });
}

test("confirmed profile deletion survives cache cleanup failure and cannot restore that cached profile", async () => {
  const h = appHarness(clientStatus(true, true));
  h.props.auth.enabled = false;
  h.props.auth.session = undefined;
  h.props.scope = "local";
  h.profile("deleted-profile");
  await openManagement(h);
  h.profileCleanup(async () => { throw new Error("profile cache unavailable"); });
  h.read(async () => clientStatus());
  const before = h.calls.events + h.calls.heartbeat;
  h.component("SafetyPrivacyScreen").props.onDeleteData();
  await h.flush();
  assert.deepEqual(h.calls.profileDeletion, ["deleted-profile"]);
  assert.equal(h.calls.events + h.calls.heartbeat, before);
  h.component("PrivacyConsentScreen").props.onManage();
  await h.flush();
  assert.equal(h.component("SafetyPrivacyScreen").props.deletionStatus, "success");
  assert.equal(h.component("SafetyPrivacyScreen").props.deletionError, undefined);
  assert.equal(h.component("SafetyPrivacyScreen").props.hasProfile, false);
  h.component("SafetyPrivacyScreen").props.onBack();
  await h.flush();
  const healthReads = h.calls.health;
  h.component("PrivacyConsentScreen").props.onSubmit(false);
  await h.flush();
  assert.ok(h.component("OnboardingScreen"));
  assert.equal(h.calls.health, healthReads);
  assert.equal(h.calls.events + h.calls.heartbeat, before);
  assert.equal(h.calls.profileDeletion.length, 1);
});

test("confirmed account deletion survives profile cache cleanup failure and still signs out", async () => {
  const h = appHarness(clientStatus(true, true));
  await openManagement(h);
  h.accountResult({ status: "deleted" });
  h.profileCleanup(async () => { throw new Error("profile cache unavailable"); });
  const before = h.calls.events + h.calls.heartbeat;
  h.component("SafetyPrivacyScreen").props.onDeleteAccount();
  const tree = await h.flush();
  assert.ok(nodes(tree).some((node) => node.children.includes("계정 삭제가 완료됐어요")));
  assert.equal(h.calls.deletion, 1);
  assert.equal(h.calls.signOut, 1);
  assert.equal(h.calls.events + h.calls.heartbeat, before);
  assert.equal(h.component("OnboardingScreen"), undefined);
});
