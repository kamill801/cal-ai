import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import { runInNewContext } from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const source = ts.createSourceFile("TrainingScreen.tsx", readFileSync(new URL("../src/screens/TrainingScreen.tsx", import.meta.url), "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const screen = source.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "TrainingScreen");
const effects = screen.body.statements.filter((node) => ts.isExpressionStatement(node) && ts.isCallExpression(node.expression) && node.expression.expression.getText(source) === "useEffect");
assert.ok(effects.length, "training draft reset effect must exist");
const helpers = source.statements.filter((node) => ts.isFunctionDeclaration(node) && node.name?.text === "performanceDefaults");
const updates = screen.body.statements.filter((node) => ts.isFunctionDeclaration(node) && ["updatePerformance", "updateEffort"].includes(node.name?.text));
// Execute the real effects and edit handlers without a native UI runtime.
const code = ts.transpileModule([...helpers, ...updates, ...effects].map((node) => node.getText(source)).join("\n"), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;

function harness(recommendations = {}) {
  const draft = {};
  const previous = [];
  let effectIndex = 0;
  const context = {
    nextDay: { id: "day-a", exercises: [{ id: "squat", sets: 2, ...recommendations }] },
    plan: { sessionMinutes: 30 },
    history: { sessions: [] },
    savedSessionId: undefined,
    editedPerformance: { current: {} },
    useEffect(callback, dependencies) {
      const index = effectIndex++;
      if (!previous[index] || dependencies.some((value, position) => !Object.is(value, previous[index][position]))) callback();
      previous[index] = dependencies;
    },
    setCompletedExerciseIds(value) { draft.selected = value; },
    setPerformance(value) { draft.performance = typeof value === "function" ? value(draft.performance) : value; },
    setDurationMinutes(value) { draft.duration = value; },
    setSessionRpe(value) { draft.rpe = value; },
    setStartTracked(value) { draft.started = value; }
  };
  const render = () => { effectIndex = 0; return runInNewContext(code, context, { timeout: 1000 }); };
  const edit = () => {
    Object.assign(draft, { selected: ["squat"], duration: "45", rpe: 8, started: true });
    for (const [field, value] of [["sets", "1"], ["reps", "8"], ["load", "20"]]) context.updatePerformance("squat", field, value);
    context.updateEffort("squat", "hard");
  };
  render();
  return { context, draft, render, edit };
}

test("a saved partial session resets the draft even when the next routine is unchanged", () => {
  const { context, draft, render, edit } = harness();
  edit();
  context.history = { sessions: [{ sessionId: "saved-1" }] };
  render();
  assert.equal(draft.selected.length, 0);
  assert.equal(draft.duration, "30");
  assert.equal(draft.rpe, 7);
  assert.equal(draft.started, false);
});

test("refreshing the same saved session does not clear a new draft", () => {
  const { context, draft, render, edit } = harness();
  context.history = { sessions: [{ sessionId: "saved-1" }] };
  render();
  edit();
  context.history = { sessions: [{ sessionId: "saved-1" }] };
  render();
  assert.equal(draft.selected.length, 1);
  assert.equal(draft.duration, "45");
});

test("failed saves without a new history entry retain the retry draft", () => {
  const { draft, render, edit } = harness();
  edit();
  render();
  assert.equal(draft.selected.length, 1);
  assert.equal(draft.rpe, 8);
  assert.equal(draft.performance.squat.load, "20");
});

test("changing the routine still resets its exercise draft", () => {
  const { context, draft, render, edit } = harness();
  edit();
  context.nextDay = { id: "day-b", exercises: [] };
  render();
  assert.equal(draft.selected.length, 0);
});

test("a confirmed save resets the draft even when refreshing history failed", () => {
  const { context, draft, render, edit } = harness();
  edit();
  context.savedSessionId = "saved-1";
  render();
  assert.equal(draft.selected.length, 0);
  assert.equal(draft.duration, "30");
  assert.equal(draft.rpe, 7);
  assert.equal(draft.started, false);
  assert.equal(draft.performance.squat.load, "");
});

test("the same save response and delayed matching history preserve a new draft", () => {
  const { context, draft, render, edit } = harness();
  context.savedSessionId = "saved-1";
  render();
  edit();
  render();
  assert.equal(draft.selected.length, 1);
  context.history = { sessions: [{ sessionId: "saved-1" }] };
  render();
  assert.equal(draft.selected.length, 1);
  assert.equal(draft.duration, "45");
  assert.equal(draft.performance.squat.load, "20");
});

test("a confirmed save awaiting refreshed resources cannot enable another save", () => {
  const declaration = screen.body.statements.find((node) => ts.isVariableStatement(node) && node.declarationList.declarations.some((item) => item.name.getText(source) === "canSaveSession"));
  assert.ok(declaration);
  const check = ts.transpileModule(`${declaration.getText(source)}\ncanSaveSession;`, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  const context = { refreshPending: true, completedExerciseIds: ["squat"], parsedDuration: 30 };
  assert.equal(runInNewContext(check, context), false);
  assert.equal(runInNewContext(check, { ...context, refreshPending: false }), true);
});

function refreshRecommendations(context) {
  context.nextDay = { ...context.nextDay, exercises: [{ id: "squat", sets: 3, recommendedReps: 10, recommendedLoadKg: 22.5 }] };
  context.history = { sessions: [{ sessionId: "saved-1" }] };
}

test("recommendations arriving after the save acknowledgement update untouched defaults", () => {
  const { context, draft, render, edit } = harness({ recommendedReps: 8, recommendedLoadKg: 20 });
  edit();
  context.savedSessionId = "saved-1";
  render();
  assert.equal(draft.performance.squat.load, "20");
  assert.equal(draft.performance.squat.reps, "8");
  refreshRecommendations(context);
  render();
  assert.equal(draft.performance.squat.load, "22.5");
  assert.equal(draft.performance.squat.reps, "10");
  assert.equal(draft.performance.squat.sets, "3");
  assert.equal(draft.selected.length, 0);
});

test("refreshed defaults preserve edited fields, selections and session inputs", () => {
  const { context, draft, render } = harness({ recommendedReps: 8, recommendedLoadKg: 20 });
  context.savedSessionId = "saved-1";
  render();
  context.updatePerformance("squat", "load", "21");
  context.updateEffort("squat", "hard");
  Object.assign(draft, { selected: ["squat"], duration: "45", rpe: 8, started: true });
  refreshRecommendations(context);
  render();
  assert.equal(draft.performance.squat.load, "21");
  assert.equal(draft.performance.squat.effort, "hard");
  assert.equal(draft.performance.squat.reps, "10");
  assert.equal(draft.performance.squat.sets, "3");
  assert.equal(draft.selected.length, 1);
  assert.equal(draft.duration, "45");
  assert.equal(draft.rpe, 8);
  assert.equal(draft.started, true);
});

test("explicit edits matching old defaults and cleared inputs remain user-owned", () => {
  const { context, draft, render } = harness({ recommendedReps: 8, recommendedLoadKg: 20 });
  context.savedSessionId = "saved-1";
  render();
  context.updatePerformance("squat", "load", "20");
  context.updatePerformance("squat", "reps", "");
  refreshRecommendations(context);
  render();
  assert.equal(draft.performance.squat.load, "20");
  assert.equal(draft.performance.squat.reps, "");
  assert.equal(draft.performance.squat.sets, "3");
});
