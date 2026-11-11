import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import { runInNewContext } from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const source = ts.createSourceFile("App.tsx", readFileSync(new URL("../App.tsx", import.meta.url), "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const owner = source.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "OwnerApp");
const functions = [];
const names = ["restoreSession", "refreshCoachData", "completeWorkout", "refreshSavedWorkout", "submitOnboarding", "continueFromOnboarding", "retrySessionRestore", "leavePrivacy"];
const collect = (node) => {
  if (ts.isFunctionDeclaration(node) && names.includes(node.name?.text)) functions.push(node.getText(source));
  ts.forEachChild(node, collect);
};
collect(owner);
const renderStart = owner.body.statements.findIndex((node) => ts.isVariableStatement(node) && node.declarationList.declarations.some((declaration) => declaration.name.getText(source) === "waitingForDashboard"));
assert.ok(renderStart >= 0);
const render = owner.body.statements.slice(renderStart, -1).map((node) => node.getText(source)).join("\n");
const code = ts.transpileModule(`${functions.join("\n")}\nfunction renderRecovery() { ${render}\nreturn "features"; }`, { compilerOptions: { target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React } }).outputText;
const profileCode = ts.transpileModule(readFileSync(new URL("../src/session/profileRestore.ts", import.meta.url), "utf8"), { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const profileExports = { exports: {} };
runInNewContext(profileCode, profileExports);

class ApiClientError extends Error {
  constructor(code, status = 403) { super(code); Object.assign(this, { code, status, retryable: true, userMessage: code, kind: "validation" }); }
}

function harness() {
  const calls = { posts: 0, clears: 0, deleteAccount: 0, signOut: 0 };
  const context = {
    ...profileExports.exports, ApiClientError, isCurrent: true, scope: "fixture-owner",
    auth: { ready: true, enabled: true, session: { user: { id: "owner" } } },
    sessionReady: true, appScreen: "today", coachStatus: "idle", deletionStatus: "idle",
    profileId: undefined, coachDashboard: undefined, sessionRestoreError: undefined, deletionError: undefined,
    ageRestricted: false, workoutRefreshPending: false, workoutSaveInFlight: { current: false },
    accountDeletionPending: false, accountDeleted: false, accountDeletionIntent: false,
    styles: {}, colors: {}, React: { createElement: (type, props, ...children) => ({ type, props: props ?? {}, children }) },
    ...Object.fromEntries(["SafeAreaView", "StatusBar", "View", "Text", "TouchableOpacity", "ActivityIndicator", "LoginScreen", "SafetyPrivacyScreen"].map((name) => [name, name])),
    apiClient: {
      getAuthenticatedProfile: async () => ({ profileId: "owned-profile" }),
      getCoachDashboard: async () => ({}), getProgress: async () => ({ bodyCheckIns: [] }),
      getWeeklyCoach: async () => ({}), getWorkoutPlan: async () => ({}), getWorkoutHistory: async () => ({ sessions: [] }),
      logWorkoutSession: async () => { calls.posts += 1; return { id: "saved-session" }; },
      createOnboarding: async () => { calls.posts += 1; return { profileId: "adult-reentry" }; }
    },
    loadProfileId: async () => undefined,
    clearProfileId: async () => { calls.clears += 1; },
    trackEvent() {}, todayIso: () => "2026-11-11", dispatch() {}, dismissWebAccountDeletionIntent() {},
    onboardingFlowErrorFromUnknown: (error) => ({ code: error.code, title: "save failed", message: error.message, retryable: error.retryable ?? true }),
    signOut: () => { calls.signOut += 1; }, deleteAccount: () => { calls.deleteAccount += 1; }, deleteAppData() {}
  };
  for (const name of ["ProfileId", "SessionReady", "SessionRestoreError", "SessionRestoreAttempt", "AgeRestricted", "AppScreen", "CoachStatus", "CoachError", "CoachDashboard", "WorkoutPlan", "WorkoutHistory", "Progress", "WeeklyCoach", "LatestBodyCheckIn", "OnboardingResult", "OnboardingStatus", "OnboardingError", "AccountDeletionPending", "SavedWorkoutSessionId", "WorkoutRefreshPending"]) {
    const key = name[0].toLowerCase() + name.slice(1);
    context[`set${name}`] = (value) => { context[key] = typeof value === "function" ? value(context[key]) : value; };
  }
  runInNewContext(code, context);
  return { context, calls };
}

function nodes(tree) {
  if (tree === null || typeof tree !== "object") return [];
  return [tree, ...tree.children.flat(Infinity).flatMap(nodes)];
}

function text(tree) {
  if (tree === null || tree === undefined) return "";
  if (typeof tree !== "object") return String(tree);
  return tree.children.flat(Infinity).map(text).join(" ");
}

test("returning age-restricted profiles keep privacy, deletion and logout without retry or reentry", async () => {
  const { context, calls } = harness();
  context.apiClient.getProgress = async () => { throw new ApiClientError("age_restricted"); };
  await context.restoreSession();
  assert.equal(context.profileId, "owned-profile");
  assert.equal(calls.clears, 0);
  assert.equal(context.ageRestricted, true);
  assert.equal(context.coachError.retryable, false);
  assert.equal(context.profileRestoreAction("age_restricted"), "restrict");
  const restricted = context.renderRecovery();
  assert.match(text(restricted), /만 18세/);
  assert.doesNotMatch(text(restricted), /다시 불러오기|다시 시도|나이.*입력/);
  const privacy = nodes(restricted).find((node) => node.type === "TouchableOpacity" && text(node).includes("개인정보와 계정 관리"));
  assert.ok(privacy);
  privacy.props.onPress();
  const safety = nodes(context.renderRecovery()).find((node) => node.type === "SafetyPrivacyScreen");
  assert.equal(safety.props.hasProfile, true);
  safety.props.onDeleteAccount();
  safety.props.onSignOut();
  assert.equal(calls.deleteAccount, 1);
  assert.equal(calls.signOut, 1);
  safety.props.onBack();
  assert.match(text(context.renderRecovery()), /만 18세/);
  await context.retrySessionRestore();
  assert.equal(context.sessionReady, true);
  await context.submitOnboarding({ age: 30 });
  assert.equal(calls.posts, 0);
  assert.equal(context.profileId, "owned-profile");
});

test("an age restriction during profile discovery also reaches account controls", async () => {
  const { context } = harness();
  context.apiClient.getAuthenticatedProfile = async () => { throw new ApiClientError("age_restricted"); };
  await context.restoreSession();
  assert.equal(context.ageRestricted, true);
  assert.equal(context.sessionRestoreError, undefined);
  assert.match(text(context.renderRecovery()), /개인정보와 계정 관리/);
});

const workout = { plan: { id: "plan-a" }, workoutDayId: "day-a", durationMinutes: 30, completedExerciseIds: ["squat"], exercisePerformance: [], sessionRpe: 7 };

test("confirmed workout save survives refresh failure and retries only reads", async () => {
  const { context, calls } = harness();
  context.profileId = "owned-profile";
  let rejectRefresh;
  let startRefresh;
  const refreshing = new Promise((resolve) => { startRefresh = resolve; });
  context.apiClient.getProgress = () => new Promise((_resolve, reject) => { rejectRefresh = reject; startRefresh(); });
  const saving = context.completeWorkout(workout);
  await refreshing;
  assert.equal(context.savedWorkoutSessionId, "saved-session", "acknowledge the POST before waiting for refresh");
  assert.equal(context.workoutRefreshPending, true);
  rejectRefresh(new Error("offline refresh"));
  await saving;
  assert.equal(calls.posts, 1);
  assert.equal(context.workoutRefreshPending, true);
  assert.equal(context.coachError.code, "workout_saved_refresh_failed");
  assert.equal(context.coachError.retryable, false);
  await context.completeWorkout(workout);
  assert.equal(calls.posts, 1, "a pending refresh must not resubmit a confirmed save");
  context.apiClient.getProgress = async () => ({ bodyCheckIns: [] });
  await context.refreshSavedWorkout();
  assert.equal(context.workoutRefreshPending, false);
  assert.equal(context.savedWorkoutSessionId, "saved-session");
  assert.equal(calls.posts, 1);
});

test("a failed workout POST has no confirmation and remains retryable", async () => {
  const { context, calls } = harness();
  context.profileId = "owned-profile";
  context.apiClient.logWorkoutSession = async () => { calls.posts += 1; throw new Error("offline POST"); };
  await context.completeWorkout(workout);
  assert.equal(context.savedWorkoutSessionId, undefined);
  assert.equal(context.workoutRefreshPending, false);
  assert.equal(context.coachStatus, "error");
  await context.completeWorkout(workout);
  assert.equal(calls.posts, 2);
});
