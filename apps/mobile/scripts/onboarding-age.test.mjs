import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import test from "node:test";
import { runInNewContext } from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const source = ts.createSourceFile(
  "OnboardingScreen.tsx",
  readFileSync(new URL("../src/screens/OnboardingScreen.tsx", import.meta.url), "utf8"),
  ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX
);
// Exercise the screen's pure validators without loading the native UI runtime.
const names = ["parseOnboardingInput", "numericRangeWarning"];
const functions = source.statements.filter((node) => ts.isFunctionDeclaration(node) && names.includes(node.name?.text));
assert.equal(functions.length, names.length);
const context = { exports: {} };
const code = functions.map((node) => node.getText(source)).join("\n") + `\nObject.assign(exports, { ${names.join(", ")} });`;
runInNewContext(ts.transpileModule(code, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, context, { timeout: 1000 });
const { parseOnboardingInput, numericRangeWarning } = context.exports;

for (const [age, accepted] of [[17, false], [18, true], [100, true], [101, false]]) {
  test(`onboarding ${accepted ? "accepts" : "rejects"} age ${age}`, () => {
    const input = {
      age: String(age), heightCm: "172", currentWeightKg: "72", targetWeightKg: "68",
      sex: "male", goalType: "lose", activityLevel: "moderate", trainingFrequency: "3-4",
      experienceLevel: "beginner", availableEquipment: ["gym"], sessionMinutes: "60"
    };
    const parsed = parseOnboardingInput(input);
    assert.equal(parsed?.age, accepted ? age : undefined);
    assert.equal(numericRangeWarning(input), accepted ? undefined : "만 나이는 18~100세 사이의 정수로 입력해 주세요.");
  });
}

test("onboarding states the minimum age and asks for full age in Korean", () => {
  assert.ok(source.text.includes("만 18세 이상을 위한 서비스예요."));
  assert.ok(source.text.includes('label="만 나이"'));
});
