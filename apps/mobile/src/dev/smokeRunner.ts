declare const require: {
  extensions: Record<string, (module: unknown, filename: string) => void>;
  (id: string): unknown;
};

async function main() {
  require.extensions[".png"] = () => undefined;
  const { runAsyncFlowSmoke } = require("./asyncFlowSmoke") as { runAsyncFlowSmoke: () => void };
  const { runApiClientSmoke } = require("./apiClientSmoke") as { runApiClientSmoke: () => Promise<void> };
  const { runSessionRestoreSmoke } = require("./sessionRestoreSmoke") as { runSessionRestoreSmoke: () => void };
  const { runAuthAccessSmoke } = require("./authAccessSmoke") as { runAuthAccessSmoke: () => Promise<void> };
  runAsyncFlowSmoke();
  runSessionRestoreSmoke();
  await runApiClientSmoke();
  await runAuthAccessSmoke();
  console.log("mobile async/API smoke passed");
}

void main();
