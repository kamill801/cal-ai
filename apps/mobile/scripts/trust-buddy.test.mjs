import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import { runInNewContext } from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const readSource = (file) => readFileSync(new URL(`../src/${file}`, import.meta.url), "utf8");
const createElement = (type, props, ...children) => ({ type, props: props ?? {}, children: children.flat(Infinity) });

function loadComponent(file, overrides = {}) {
  const exports = {};
  runInNewContext(ts.transpileModule(readSource(file), {
    fileName: file,
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.React }
  }).outputText, {
    exports,
    React: { createElement },
    require(id) {
      if (id in overrides) return overrides[id];
      if (id.startsWith("../../assets/mascot/")) return id;
      if (id === "react-native") return { Image: "Image" };
      throw new Error(`Unexpected module ${id}`);
    }
  }, { timeout: 1000 });
  return exports;
}

const { TrustBuddy } = loadComponent("components/TrustBuddy.tsx");
const poses = ["welcome", "meal", "analysis", "workout", "progress", "coach", "celebrate"];

test("production entry never imports the inert visual preview", () => {
  const entry = readFileSync(new URL("../index.js", import.meta.url), "utf8");
  assert.match(entry, /import App from "\.\/App"/);
  assert.match(entry, /registerRootComponent\(App\)/);
  assert.doesNotMatch(entry, /kongbi-visual-preview/);
});

for (const pose of poses) {
  test(`Kongbi ${pose} uses its bundled image and a meaningful Korean image label`, () => {
    const image = TrustBuddy({ pose, size: 64 });
    assert.equal(image.type, "Image");
    assert.equal(image.props.source, `../../assets/mascot/mascot-${pose}.png`);
    assert.match(image.props.accessibilityLabel, /콩비/);
    assert.ok(image.props.accessibilityLabel.length > "콩비".length);
    assert.equal(image.props.accessible, true);
    assert.equal(image.props.accessibilityRole, "image");
    assert.equal(image.props.resizeMode, "contain");
    assert.equal(image.props.style.width, 64);
    assert.equal(image.props.style.height, 64);
    assert.equal(image.props.style.flexShrink, 0);
  });
}

test("Kongbi keeps the existing default size and meal pose, with distinct scene labels", () => {
  const image = TrustBuddy({});
  assert.equal(image.props.style.width, 82);
  assert.equal(image.props.style.height, 82);
  assert.equal(image.props.source, "../../assets/mascot/mascot-meal.png");
  assert.equal(new Set(poses.map((pose) => TrustBuddy({ pose }).props.accessibilityLabel)).size, poses.length);
});

function buddyInstances(file) {
  const source = ts.createSourceFile(file, readSource(file), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const instances = [];
  function visit(node) {
    if ((ts.isJsxSelfClosingElement(node) || ts.isJsxOpeningElement(node)) && node.tagName.getText(source) === "TrustBuddy") {
      const attributes = node.attributes.properties;
      const pose = attributes.find((attribute) => ts.isJsxAttribute(attribute) && attribute.name.text === "pose")?.initializer;
      const size = attributes.find((attribute) => ts.isJsxAttribute(attribute) && attribute.name.text === "size")?.initializer;
      assert.ok(pose && ts.isStringLiteral(pose), `${file} must select an explicit pose`);
      assert.ok(size && ts.isJsxExpression(size) && size.expression && ts.isNumericLiteral(size.expression), `${file} must reserve a fixed mascot size`);
      instances.push({ pose: pose.text, size: Number(size.expression.text) });
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  return instances;
}

for (const [file, pose] of [
  ["screens/LoginScreen.tsx", "welcome"],
  ["screens/OnboardingScreen.tsx", "welcome"],
  ["screens/TodayDashboardScreen.tsx", "meal"],
  ["screens/AnalyzeEvidenceScreen.tsx", "analysis"],
  ["screens/ReviewResultScreen.tsx", "analysis"],
  ["screens/ClarificationScreen.tsx", "analysis"],
  ["screens/TrainingScreen.tsx", "workout"],
  ["screens/ProgressScreen.tsx", "progress"],
  ["screens/PlanScreen.tsx", "coach"],
  ["screens/WeeklyCoachScreen.tsx", "coach"],
  ["screens/SafetyPrivacyScreen.tsx", "coach"],
  ["screens/PrivacyConsentScreen.tsx", "coach"],
  ["components/SavedImpact.tsx", "celebrate"]
]) {
  test(`${file} has one context-appropriate Kongbi without duplicates`, () => {
    const instances = buddyInstances(file);
    assert.equal(instances.length, 1);
    assert.equal(instances[0].pose, pose);
    assert.ok(instances[0].size > 0 && instances[0].size <= 112);
  });
}

test("saved screen uses its existing celebration component without adding a second mascot", () => {
  assert.equal(buddyInstances("screens/SavedImpactScreen.tsx").length, 0);
  assert.match(readSource("screens/SavedImpactScreen.tsx"), /<SavedImpact\s/);
});

test("login replaces the generic shield with Kongbi", () => {
  assert.ok(!readSource("screens/LoginScreen.tsx").includes("ShieldCheck"));
});

function loginHarness(input = {}) {
  const state = [];
  const calls = [];
  let cursor = 0;
  const { LoginScreen } = loadComponent("screens/LoginScreen.tsx", {
    react: { useState(initial) {
      const index = cursor++;
      if (!(index in state)) state[index] = initial;
      return [state[index], (value) => { state[index] = value; }];
    } },
    "react-native": { ...Object.fromEntries(["ActivityIndicator", "KeyboardAvoidingView", "ScrollView", "Text", "TextInput", "TouchableOpacity", "View"].map((name) => [name, name])),
      Platform: { OS: "ios" }, StyleSheet: { create: (styles) => styles } },
    "lucide-react-native": { ChevronDown: "ChevronDown", ChevronUp: "ChevronUp", Eye: "Eye", EyeOff: "EyeOff" },
    "../components/TrustBuddy": { TrustBuddy: "TrustBuddy" },
    "../api/config": { getApiBaseUrl: () => "https://fixture.invalid" },
    "../theme": { colors: {}, radii: {}, shadows: {}, spacing: {}, typography: {} }
  });
  const props = { configured: true, loading: false, onKakaoLogin: () => calls.push("kakao"),
    onEmailLogin: async (email, password) => { calls.push([email, password]); }, ...input };
  function render() {
    cursor = 0;
    return LoginScreen(props);
  }
  function nodes(node) {
    return node && typeof node === "object" ? [node, ...node.children.flatMap(nodes)] : [];
  }
  const find = (predicate) => nodes(render()).find(predicate);
  const field = (label) => find((node) => node.type === "TextInput" && node.props.accessibilityLabel === label);
  const button = (label) => find((node) => node.type === "TouchableOpacity" && node.children.some((child) => child?.type === "Text" && child.children.includes(label)));
  const action = (label) => find((node) => node.type === "TouchableOpacity" && node.props.accessibilityLabel === label);
  return { props, calls, field, button, action };
}

test("login branding preserves Kakao, email, password visibility and password clearing", async () => {
  const h = loginHarness();
  h.button("카카오로 시작하기").props.onPress();
  assert.equal(h.calls[0], "kakao");
  h.button("이메일로 로그인").props.onPress();
  assert.equal(h.button("로그인").props.disabled, true);
  h.field("이메일").props.onChangeText("owner@example.invalid");
  h.field("비밀번호").props.onChangeText("fixture-password");
  assert.equal(h.field("비밀번호").props.secureTextEntry, true);
  h.action("비밀번호 표시").props.onPress();
  assert.equal(h.field("비밀번호").props.secureTextEntry, false);
  h.action("비밀번호 숨기기").props.onPress();
  assert.equal(h.field("비밀번호").props.secureTextEntry, true);
  assert.equal(h.button("로그인").props.disabled, false);
  await h.field("비밀번호").props.onSubmitEditing();
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(h.calls[1], ["owner@example.invalid", "fixture-password"]);
  assert.equal(h.field("비밀번호").props.value, "");
});

test("login remains blocked while unconfigured or busy", () => {
  const h = loginHarness();
  h.button("이메일로 로그인").props.onPress();
  h.field("이메일").props.onChangeText("owner@example.invalid");
  h.field("비밀번호").props.onChangeText("fixture-password");
  for (const pending of [{ configured: false, loading: false }, { configured: true, loading: true }]) {
    Object.assign(h.props, pending);
    assert.equal(h.button("로그인").props.disabled, true);
    assert.equal(h.field("비밀번호").props.editable, false);
    h.field("비밀번호").props.onSubmitEditing();
    assert.equal(h.calls.length, 0);
  }
});
