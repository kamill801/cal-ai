import { cp, mkdir, readFile, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

export async function prepare(root) {
  const app = path.join(root, "apps/mobile/dist-web-preview");
  const output = path.join(root, "public");
  // Preserve the original shell privately; the public default is always landing.
  const shell = path.join(root, "services/api/app/web/preserved-app");
  await readFile(path.join(app, "index.html"));
  await mkdir(shell, { recursive: true });
  await cp(path.join(app, "index.html"), path.join(shell, "index.html"));
  await rm(output, { recursive: true, force: true });
  await mkdir(output, { recursive: true });
  await cp(app, output, { recursive: true });
  await cp(path.join(root, "services/api/app/web/beta/index.html"), path.join(output, "index.html"));
  await cp(path.join(root, "services/api/app/web/beta/assets"), path.join(output, "beta-assets"), { recursive: true });
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await prepare(fileURLToPath(new URL("../../../", import.meta.url)));
}
