import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const outDir = "/tmp/cal-ai-mobile-smoke";
const tsconfigPath = "/tmp/cal-ai-smoke-tsconfig.json";

const tsconfig = {
  extends: join(repoRoot, "apps/mobile/tsconfig.json"),
  compilerOptions: {
    module: "Node16",
    moduleResolution: "node16",
    customConditions: [],
    outDir,
    noEmit: false,
    skipLibCheck: true
  },
  include: [
    join(repoRoot, "apps/mobile/src/dev/smokeRunner.ts"),
    join(repoRoot, "apps/mobile/src/dev/apiClientSmoke.ts"),
    join(repoRoot, "apps/mobile/src/dev/asyncFlowSmoke.ts"),
    join(repoRoot, "apps/mobile/src/api/**/*.ts"),
    join(repoRoot, "apps/mobile/src/flow/**/*.ts"),
    join(repoRoot, "apps/mobile/src/mockData.ts"),
    join(repoRoot, "packages/shared/src/**/*.ts")
  ]
};

writeFileSync(tsconfigPath, `${JSON.stringify(tsconfig, null, 2)}\n`);

const tsc = spawnSync(join(repoRoot, "apps/mobile/node_modules/typescript/bin/tsc"), ["-p", tsconfigPath], { stdio: "inherit" });
if (tsc.status !== 0) {
  process.exit(tsc.status ?? 1);
}

mkdirSync(join(outDir, "node_modules/@cal-ai/shared"), { recursive: true });
writeFileSync(join(outDir, "node_modules/@cal-ai/shared/package.json"), '{"name":"@cal-ai/shared","main":"../../../packages/shared/src/index.js"}\n');

mkdirSync(join(outDir, "node_modules/react-native"), { recursive: true });
writeFileSync(join(outDir, "node_modules/react-native/package.json"), '{"name":"react-native","main":"index.js"}\n');
writeFileSync(join(outDir, "node_modules/react-native/index.js"), "exports.Platform = { OS: process.env.REACT_NATIVE_PLATFORM || 'web' };\n");

mkdirSync(join(outDir, "apps/mobile/assets"), { recursive: true });
writeFileSync(join(outDir, "apps/mobile/assets/meal-preview.png"), "");

const smoke = spawnSync(process.execPath, [join(outDir, "apps/mobile/src/dev/smokeRunner.js")], {
  stdio: "inherit",
  env: { ...process.env, NODE_PATH: join(outDir, "node_modules") }
});
process.exit(smoke.status ?? 1);
