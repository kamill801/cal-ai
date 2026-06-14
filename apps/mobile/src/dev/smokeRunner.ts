declare const require: {
  extensions: Record<string, (module: unknown, filename: string) => void>;
  (id: string): unknown;
};

async function main() {
  require.extensions[".png"] = () => undefined;
  const { runAsyncFlowSmoke } = require("./asyncFlowSmoke") as { runAsyncFlowSmoke: () => void };
  const { runApiClientSmoke } = require("./apiClientSmoke") as { runApiClientSmoke: () => Promise<void> };
  runAsyncFlowSmoke();
  await runApiClientSmoke();
  console.log("mobile async/API smoke passed");
}

void main();
