import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import { runInNewContext } from "node:vm";

const ts = createRequire(import.meta.url)("typescript");
const source = ts.createSourceFile("TrainingScreen.tsx", readFileSync(new URL("../src/screens/TrainingScreen.tsx", import.meta.url), "utf8"), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const screen = source.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "TrainingScreen");
const handlers = ["startWorkout", "saveWorkout", "clearDraft"].map((name) => {
  const handler = screen.body.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === name);
  return handler.getText(source);
});
const code = ts.transpileModule(handlers.join("\n"), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;

function harness() {
  const draft = { load: "22.5", reps: "8", completed: true };
  const context = {
    session: { planId: "plan-a", day: { id: "day-a" } }, nextDay: { id: "day-b", exercises: [] },
    plan: { id: "plan-a" }, refreshPending: false, savingRef: { current: false }, completedSets: 1,
    validDuration: true, hasInvalidSet: false, duration: "30", intensity: undefined,
    drafts: { squat: [draft] }, performance: [{ exerciseId: "squat" }], scroll: { current: null },
    onStart() {}, onComplete: async () => true
  };
  for (const name of ["Drafts", "Session", "Rest", "Efforts", "Finishing", "Discarding", "OpenExercise", "Saved", "Saving", "Duration", "DurationEdited", "Intensity"]) {
    const key = name[0].toLowerCase() + name.slice(1);
    context[`set${name}`] = (value) => { context[key] = value; };
  }
  runInNewContext(code, context);
  return context;
}

test("a failed POST preserves edited sets and permits a retry", async () => {
  const state = harness();
  state.onComplete = async () => false;
  await state.saveWorkout();
  assert.equal(state.drafts.squat[0].load, "22.5");
  assert.equal(state.savingRef.current, false);
  assert.equal(state.session.day.id, "day-a");
});

test("an acknowledged partial workout clears the draft and ends its rest timer", async () => {
  const state = harness();
  state.rest = { deadline: 45_000 };
  await state.saveWorkout();
  assert.equal(state.saved, true);
  assert.equal(state.session, undefined);
  assert.equal(state.rest, undefined);
  assert.equal(Object.keys(state.drafts).length, 0);
});

test("pending refresh blocks both session start and a duplicate save", async () => {
  const state = harness();
  state.refreshPending = true;
  state.onComplete = async () => assert.fail("duplicate workout POST");
  await state.saveWorkout();
  state.session = undefined;
  state.startWorkout();
  assert.equal(state.session, undefined);
  assert.equal(state.drafts.squat[0].completed, true);
});
