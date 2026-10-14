declare const require: {
  extensions: Record<string, (module: unknown, filename: string) => void>;
  (id: string): unknown;
};

async function main() {
  require.extensions[".png"] = () => undefined;
  const { runAsyncFlowSmoke } = require("./asyncFlowSmoke") as { runAsyncFlowSmoke: () => void };
  const { runApiClientSmoke } = require("./apiClientSmoke") as { runApiClientSmoke: () => Promise<void> };
  const { runSessionRestoreSmoke } = require("./sessionRestoreSmoke") as { runSessionRestoreSmoke: () => void };
  const { runEquipmentGuideSmoke } = require("./equipmentGuideSmoke") as { runEquipmentGuideSmoke: () => Promise<void> };
  const { runNumericValidationSmoke } = require("./numericValidationSmoke") as { runNumericValidationSmoke: () => void };
  const { runErrorMappingSmoke } = require("./errorMappingSmoke") as { runErrorMappingSmoke: () => void };
  const { runWorkoutAnalyticsSmoke } = require("./workoutAnalyticsSmoke") as { runWorkoutAnalyticsSmoke: () => void };
  runWorkoutAnalyticsSmoke();
  runErrorMappingSmoke();
  runNumericValidationSmoke();
  runAsyncFlowSmoke();
  runSessionRestoreSmoke();
  await runApiClientSmoke();
  await runEquipmentGuideSmoke();
  console.log("mobile async/API smoke passed");
}

void main();
