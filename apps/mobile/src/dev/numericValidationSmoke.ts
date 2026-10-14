import type { WorkoutPlan } from "@cal-ai/shared";
import type { ProgressScreen } from "../screens/ProgressScreen";
import type { TrainingScreen } from "../screens/TrainingScreen";

declare const require: {
  (id: string): unknown;
  resolve(id: string): string;
};

interface Element {
  type: string | symbol | ((props: Props) => unknown);
  props: Props;
}
type Props = Record<string, unknown>;
type ScreenProps = Parameters<typeof TrainingScreen>[0] | Parameters<typeof ProgressScreen>[0];
type SavedSession = Parameters<Parameters<typeof TrainingScreen>[0]["onComplete"]>[0];

const { readFileSync } = require("node:fs") as { readFileSync: (path: string, encoding: "utf8") => string };
const { runInNewContext } = require("node:vm") as { runInNewContext: (source: string, context: Props) => void };

// Execute the compiled screens with local hook/host doubles; no native or network services run.
function mountScreen(name: "TrainingScreen" | "ProgressScreen", initialProps: ScreenProps) {
  const states: unknown[] = [];
  const refs: { current: unknown }[] = [];
  const effectDeps: (readonly unknown[] | undefined)[] = [];
  let stateIndex = 0;
  let refIndex = 0;
  let effectIndex = 0;
  let pendingEffects: (() => void)[] = [];
  let dirty = false;
  let props = initialProps;
  let elements: Element[] = [];
  const jsx = (type: Element["type"], properties: Props): Element => ({ type, props: properties });
  const hooks = {
    useRef(initial: unknown) {
      const index = refIndex++;
      return refs[index] ?? (refs[index] = { current: initial });
    },
    useState(initial: unknown) {
      const index = stateIndex++;
      if (!(index in states)) states[index] = typeof initial === "function" ? initial() : initial;
      return [states[index], (value: unknown) => {
        const next = typeof value === "function" ? value(states[index]) : value;
        if (!Object.is(states[index], next)) dirty = true;
        states[index] = next;
      }];
    },
    useEffect(effect: () => void, deps?: readonly unknown[]) {
      const index = effectIndex++;
      const previous = effectDeps[index];
      if (!deps || !previous || deps.some((value, offset) => !Object.is(value, previous[offset]))) {
        pendingEffects.push(effect);
        effectDeps[index] = deps;
      }
    }
  };
  const exports: Record<string, (properties: ScreenProps) => unknown> = {};
  runInNewContext(readFileSync(require.resolve(`../screens/${name}`), "utf8"), {
    exports,
    require(id: string) {
      if (id === "react") return hooks;
      if (id === "react/jsx-runtime") return { jsx, jsxs: jsx, Fragment: Symbol.for("fragment") };
      if (id === "react-native") return {
        Platform: { OS: "web" }, StyleSheet: { create: (styles: Props) => styles },
        ScrollView: "ScrollView", Text: "Text", TextInput: "TextInput", TouchableOpacity: "TouchableOpacity", View: "View"
      };
      if (id === "lucide-react-native") return { Check: () => null };
      if (id.startsWith("../components/")) return { [id.split("/").at(-1)!]: (properties: Props) => properties.children };
      if (id === "../theme") return require("../theme");
      if (id === "../validation/numericInput") return require("../validation/numericInput");
      throw new Error(`Unexpected numeric smoke dependency: ${id}`);
    }
  });

  function visit(value: unknown): void {
    if (Array.isArray(value)) { value.forEach(visit); return; }
    if (!value || typeof value !== "object" || !("type" in value)) return;
    const element = value as Element;
    if (typeof element.type === "function") { visit(element.type(element.props)); return; }
    elements.push(element);
    visit(element.props.children);
  }
  function render(): void {
    for (let attempt = 0; attempt < 6; attempt++) {
      stateIndex = 0;
      refIndex = 0;
      effectIndex = 0;
      pendingEffects = [];
      dirty = false;
      const tree = exports[name](props);
      pendingEffects.forEach((effect) => effect());
      if (!dirty) { elements = []; visit(tree); return; }
    }
    throw new Error("Numeric smoke render did not settle");
  }
  function find(type: string, label?: string): Element {
    const matches = elements.filter((element) => element.type === type && (label === undefined || element.props.accessibilityLabel === label));
    if (matches.length !== 1) throw new Error(`Expected one ${type} ${label ?? ""}, found ${matches.length}`);
    return matches[0];
  }
  render();
  return {
    input(label: string) { return find("TextInput", label); },
    button(label?: string) {
      return label ? find("TouchableOpacity", label) : elements.find((element) => element.type === "TouchableOpacity" && element.props.children && (element.props.children as Element).props?.children === "기록")!;
    },
    checkbox(label: string) {
      return elements.find((element) => element.type === "input" && element.props["aria-label"] === label)!;
    },
    enter(label: string, value: string) { (find("TextInput", label).props.onChangeText as (value: string) => void)(value); render(); },
    press(label: string) {
      const result = (find("TouchableOpacity", label).props.onPress as () => void | Promise<void>)();
      render();
      return Promise.resolve(result).then(() => { render(); });
    },
    text() { return elements.filter((element) => element.type === "Text").map((element) => element.props.children).flat().join(" "); },
    update(next: ScreenProps) { props = next; render(); }
  };
}

const plan: WorkoutPlan = {
  id: "numeric-smoke-plan", profileId: "local-fixture", goalType: "gain", daysPerWeek: 2, sessionMinutes: 60,
  days: [{ id: "day-one", title: "Local fixture", focus: "full_body", exercises: ["first", "second"].map((id) => ({
    id, name: id, sets: 3, reps: "8-12", targetRir: 2, restSeconds: 60, rationale: "fixture", progressionAction: "collect_baseline", recommendationReason: "fixture"
  })) }], personalizationBasis: [], progressionRule: "fixture", safetyNote: "fixture", generatedAt: "2026-10-14T00:00:00Z"
};
const saveLabel = "오늘 운동 수행 기록 저장";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
function training(fixture = plan, complete: (input: SavedSession) => Promise<boolean> = async () => false) {
  const saved: SavedSession[] = [];
  const started: string[] = [];
  const props: Parameters<typeof TrainingScreen>[0] = {
    plan: fixture, status: "idle", equipmentActions: {} as Parameters<typeof TrainingScreen>[0]["equipmentActions"],
    onGenerate() {}, onStart(id) { started.push(id); }, onComplete(input) { saved.push(input); return complete(input); }
  };
  const screen = mountScreen("TrainingScreen", props);
  screen.press("first 완료 체크");
  return { screen, saved, started, props };
}
function progress() {
  const saved: number[] = [];
  const props: Parameters<typeof ProgressScreen>[0] = {
    status: "idle", bodyPhotoEnabled: false, onOpenSafety() {}, onLogWeight(value) { saved.push(value); }, onLogWellness() {}, onCaptureBody() {}, onPickBody() {}
  };
  return { screen: mountScreen("ProgressScreen", props), saved, props };
}

export function runNumericValidationSmoke(): void {
  const failures: string[] = [];
  let cases = 0;
  function test(name: string, run: () => void): void {
    cases++;
    try { run(); } catch (error) { failures.push(`${name}: ${error instanceof Error ? error.message : String(error)}`); }
  }

  test("blank weight is disabled without an inline error", () => {
    const { screen, saved } = progress();
    for (const value of ["", "   "]) {
      screen.enter("현재 체중", value);
      assert(screen.button().props.disabled === true, "blank weight must not become zero");
      (screen.button().props.onPress as () => void)();
      assert(saved.length === 0, "blank weight callback must be guarded");
      assert(!screen.text().includes("30~250"), "blank weight must not show a validation error");
    }
  });
  for (const value of ["0", "29.9", "250.1", "-1", "oops", "NaN", "Infinity", "0x40", "7e1"]) {
    test(`invalid weight ${value}`, () => {
      const { screen, saved } = progress();
      screen.enter("현재 체중", value);
      assert(screen.button().props.disabled === true, "invalid weight must disable save");
      (screen.button().props.onPress as () => void)();
      assert(saved.length === 0, "invalid weight must not reach the callback");
      assert(screen.input("현재 체중").props.value === value, "invalid weight draft must remain editable");
      assert(screen.text().includes("30~250"), "entered invalid weight needs a concise field error");
    });
  }
  for (const value of ["30", "72.5", "250", " 72.5 "]) {
    test(`valid weight ${value}`, () => {
      const { screen, saved } = progress();
      screen.enter("현재 체중", value);
      assert(screen.button().props.disabled === false, "in-range decimal weight must stay enabled");
      (screen.button().props.onPress as () => void)();
      assert(saved[0] === Number(value), "valid weight must be saved unchanged");
      assert(!screen.text().includes("30~250"), "valid weight must not show a field error");
    });
  }
  for (const [label, invalid, errorText] of [
    ["세트 수행값", ["-1", "1.5", "21", "oops", "Infinity", "0x10"], "0~20"],
    ["반복 수행값", ["-1", "1.5", "101", "oops", "NaN", "0x10"], "0~100"],
    ["kg 수행값", ["-0.5", "500.1", "oops", "Infinity", "1e2"], "0~500"]
  ] as const) {
    for (const value of invalid) {
      test(`invalid ${label} ${value}`, () => {
        const { screen, saved } = training();
        screen.enter(label, value);
        assert(screen.button(saveLabel).props.disabled === true, "invalid completed performance must disable save");
        screen.press(saveLabel);
        assert(saved.length === 0, "invalid performance must never be clamped or discarded into a payload");
        assert(screen.input(label).props.value === value, "invalid performance draft must remain editable");
        assert(screen.text().includes(errorText), "entered invalid performance needs a field error");
      });
    }
  }
  for (const value of ["", "   ", "4", "241", "5.5", "oops", "Infinity", "0x10"]) {
    test(`invalid duration ${JSON.stringify(value)}`, () => {
      const { screen, saved } = training();
      screen.enter("운동 시간, 분", value);
      assert(screen.button(saveLabel).props.disabled === true, "duration must be an integer from 5 through 240");
      screen.press(saveLabel);
      assert(saved.length === 0, "invalid duration must not reach the callback");
      assert(screen.text().includes("5~240") === Boolean(value.trim()), "only entered invalid duration needs a field error");
    });
  }
  test("required blank sets stays blank and disabled", () => {
    const { screen, saved } = training();
    screen.enter("세트 수행값", " ");
    assert(screen.button(saveLabel).props.disabled === true, "required blank sets must not become zero");
    screen.press(saveLabel);
    assert(saved.length === 0 && screen.input("세트 수행값").props.value === " ", "blank sets must remain a draft");
    assert(!screen.text().includes("0~20"), "blank sets must not show an entered-value error");
  });
  test("default sets and optional blanks preserve the session", () => {
    const { screen, saved, started } = training();
    screen.enter("반복 수행값", "   ");
    screen.enter("kg 수행값", "");
    assert(screen.button(saveLabel).props.disabled === false, "optional blanks must permit save");
    screen.press(saveLabel);
    const input = saved[0];
    assert(input.completedExerciseIds.join() === "first" && started.join() === "day-one", "completion and start tracking must remain intact");
    assert(input.exercisePerformance[0].setsCompleted === 3 && input.durationMinutes === 60 && input.sessionRpe === 7, "default sets, duration and RPE must remain intact");
    assert(input.exercisePerformance[0].repsCompleted === undefined && input.exercisePerformance[0].loadKg === undefined, "optional blanks must stay absent");
  });
  for (const [sets, reps, load, duration] of [["0", "0", "0", "5"], ["20", "100", "500", "240"], ["3", "8", "42.5", "60"]]) {
    test(`valid performance boundaries ${sets}/${reps}/${load}/${duration}`, () => {
      const { screen, saved } = training();
      screen.enter("세트 수행값", sets); screen.enter("반복 수행값", reps); screen.enter("kg 수행값", load); screen.enter("운동 시간, 분", duration);
      screen.press("first 체감 버거움"); screen.press("체감 강도 9");
      assert(screen.button(saveLabel).props.disabled === false, "valid zeros, boundaries and fractional loads must permit save");
      screen.press(saveLabel);
      const item = saved[0].exercisePerformance[0];
      assert(item.setsCompleted === Number(sets) && item.repsCompleted === Number(reps) && item.loadKg === Number(load), "valid performance must be saved unchanged");
      assert(item.effort === "hard" && saved[0].sessionRpe === 9 && saved[0].durationMinutes === Number(duration), "effort, RPE and duration must remain intact");
    });
  }
  test("unselected invalid drafts do not block selected exercises", () => {
    const { screen, saved, started } = training();
    screen.enter("반복 수행값", "oops");
    screen.press("first 완료 취소"); screen.press("second 완료 체크");
    assert(screen.button(saveLabel).props.disabled === false, "unselected performance must not block save");
    screen.press("second 완료 취소"); screen.press("first 완료 체크");
    assert(screen.input("반복 수행값").props.value === "oops" && screen.button(saveLabel).props.disabled === true, "reselecting must restore and revalidate the draft");
    screen.enter("반복 수행값", "12");
    assert(screen.button(saveLabel).props.disabled === false && !screen.text().includes("0~100"), "correcting the draft must clear the field error");
    assert(started.length === 1, "draft validation must not repeat start tracking");
    screen.press("first 완료 취소"); screen.press("second 완료 체크");
    screen.press(saveLabel);
    assert(saved[0].completedExerciseIds.join() === "second" && saved[0].exercisePerformance[0].exerciseId === "second", "only selected exercises must be submitted");
  });
  test("recommended zero load remains an explicit zero", () => {
    const fixture = { ...plan, days: [{ ...plan.days[0], exercises: plan.days[0].exercises.map((exercise) => ({ ...exercise, recommendedLoadKg: 0 })) }] };
    const { screen } = training(fixture);
    assert(screen.input("kg 수행값").props.value === "0", "recommended zero load must not become blank");
  });
  test("loading guards both callbacks", () => {
    const workout = training();
    workout.screen.update({ ...workout.props, status: "loading" });
    assert(workout.screen.button(saveLabel).props.disabled === true, "loading workout must stay disabled");
    workout.screen.press(saveLabel);
    assert(workout.saved.length === 0, "loading workout callback must be guarded");
    const weight = progress();
    weight.screen.enter("현재 체중", "72"); weight.screen.update({ ...weight.props, status: "loading" });
    assert(weight.screen.button().props.disabled === true, "loading weight must stay disabled");
    (weight.screen.button().props.onPress as () => void)();
    assert(weight.saved.length === 0, "loading weight callback must be guarded");
  });
  if (failures.length) throw new Error(`Numeric validation smoke: ${failures.length}/${cases} regressions\n${failures.join("\n")}`);
  console.log(`numeric screen validation smoke passed (${cases} cases)`);
}

export async function runWorkoutAcknowledgementSmoke(): Promise<void> {
  const failures: string[] = [];
  let cases = 0;
  async function test(name: string, run: () => Promise<void>): Promise<void> {
    cases++;
    try { await run(); } catch (error) { failures.push(`${name}: ${error instanceof Error ? error.message : String(error)}`); }
  }
  function deferred() {
    let resolve!: (value: boolean) => void;
    let reject!: (error: Error) => void;
    const promise = new Promise<boolean>((accept, fail) => { resolve = accept; reject = fail; });
    return { promise, resolve, reject };
  }
  function enterDraft(screen: ReturnType<typeof training>["screen"]): void {
    screen.enter("세트 수행값", "2");
    screen.enter("반복 수행값", "8");
    screen.enter("kg 수행값", "42.5");
    screen.enter("운동 시간, 분", "75");
    screen.press("first 체감 버거움");
    screen.press("체감 강도 9");
  }
  function assertDraft(screen: ReturnType<typeof training>["screen"]): void {
    assert(screen.checkbox("first 수행 완료").props.checked === true, "selected exercise must remain checked");
    assert(screen.input("세트 수행값").props.value === "2" && screen.input("반복 수행값").props.value === "8" && screen.input("kg 수행값").props.value === "42.5", "performance draft must remain unchanged");
    assert(screen.input("운동 시간, 분").props.value === "75", "duration draft must remain unchanged");
    assert((screen.button("first 체감 버거움").props.accessibilityState as Props).selected === true && (screen.button("체감 강도 9").props.accessibilityState as Props).selected === true, "effort and RPE must remain unchanged");
  }

  await test("true acknowledgement clears a partial draft even when refresh fails", async () => {
    const ack = deferred();
    const { screen, saved, started, props } = training(plan, () => ack.promise);
    enterDraft(screen);
    const submitting = screen.press(saveLabel);
    assert(saved.length === 1 && saved[0].completedExerciseIds.join() === "first", "partial workout must be submitted exactly once");
    const refreshedPlan = { ...plan, days: [{ ...plan.days[0], exercises: plan.days[0].exercises.map((exercise) => ({ ...exercise, recommendedLoadKg: 45 })) }] };
    screen.update({ ...props, plan: refreshedPlan, status: "error" });
    ack.resolve(true);
    await submitting;
    assert(screen.checkbox("first 수행 완료").props.checked === false && screen.button(saveLabel).props.disabled === true, "acknowledged selections must clear without a new day ID");
    screen.update({ ...props, plan: refreshedPlan, status: "idle" });
    await screen.press(saveLabel);
    assert(saved.length === 1, "tab-style rerender must not allow stale partial submission");
    await screen.press("first 완료 체크");
    assert(screen.input("kg 수행값").props.value === "45" && screen.input("운동 시간, 분").props.value === "60", "reset must use the latest recommendations and default duration");
    assert((screen.button("체감 강도 7").props.accessibilityState as Props).selected === true && started.length === 2, "acknowledged RPE and start tracking must reset");
  });

  await test("false acknowledgement preserves the failed draft across rerenders", async () => {
    const ack = deferred();
    const { screen, saved, props } = training(plan, () => ack.promise);
    enterDraft(screen);
    const submitting = screen.press(saveLabel);
    screen.update({ ...props, status: "error" });
    ack.resolve(false);
    await submitting;
    screen.update({ ...props });
    assertDraft(screen);
    assert(saved.length === 1 && screen.button(saveLabel).props.disabled === false, "failed draft must unlock for retry");
  });

  await test("rejected acknowledgement preserves and unlocks the draft", async () => {
    const ack = deferred();
    const { screen } = training(plan, () => ack.promise);
    enterDraft(screen);
    const submitting = screen.press(saveLabel);
    ack.reject(new Error("local save failure"));
    await submitting;
    assertDraft(screen);
    assert(screen.button(saveLabel).props.disabled === false, "unexpected rejection must release the submit lock");
  });

  await test("pending submission blocks stale double presses and all draft changes", async () => {
    const ack = deferred();
    const { screen, saved, props } = training(plan, () => ack.promise);
    enterDraft(screen);
    const stalePress = screen.button(saveLabel).props.onPress as () => void | Promise<void>;
    const submitting = screen.press(saveLabel);
    const duplicate = stalePress();
    assert(saved.length === 1, "same-render double press must not submit twice");
    assert(screen.button(saveLabel).props.disabled === true && (screen.button(saveLabel).props.accessibilityState as Props).busy === true, "own pending state must lock save without parent loading");
    assert(screen.checkbox("first 수행 완료").props.disabled === true, "web checkbox must be disabled");
    for (const label of ["세트 수행값", "반복 수행값", "kg 수행값", "운동 시간, 분"]) {
      assert(screen.input(label).props.editable === false, "pending numeric input must not be editable");
      screen.enter(label, "1");
    }
    for (const label of ["first 완료 취소", "second 완료 체크", "first 체감 여유", "체감 강도 5"]) {
      assert(screen.button(label).props.disabled === true, "pending toggle must be disabled");
      screen.press(label);
    }
    const checkboxChange = screen.checkbox("first 수행 완료").props.onChange as () => void;
    checkboxChange();
    screen.update({ ...props });
    assertDraft(screen);
    ack.resolve(false);
    await submitting;
    await duplicate;
    assertDraft(screen);
    assert(screen.checkbox("first 수행 완료").props.disabled === false && screen.input("kg 수행값").props.editable === true, "failed acknowledgement must unlock every control");
  });

  await test("unsaved draft survives unrelated status and tab-style rerenders", async () => {
    const { screen, saved, props } = training();
    enterDraft(screen);
    screen.update({ ...props, status: "loading" });
    screen.update({ ...props, status: "success" });
    assertDraft(screen);
    assert(saved.length === 0 && screen.button(saveLabel).props.disabled === false, "unsaved navigation must not clear or submit the draft");
  });

  if (failures.length) throw new Error(`Workout acknowledgement smoke: ${failures.length}/${cases} regressions\n${failures.join("\n")}`);
  console.log(`workout acknowledgement smoke passed (${cases} cases)`);
}
