const fs = require("node:fs/promises");
const path = require("node:path");
const Jimp = require("jimp-compact");

const root = path.resolve(__dirname, "../assets/mascot");
const poses = ["welcome", "meal", "analysis", "workout", "progress", "coach", "celebrate"];

async function main() {
  for (const pose of poses) {
    const image = await Jimp.read(path.join(root, "source", `kongbi-${pose}.png`));
    await image.resize(512, 512, Jimp.RESIZE_BICUBIC).writeAsync(path.join(root, `mascot-${pose}.png`));
  }
  const sizes = await Promise.all(poses.map(async (pose) => ({
    pose,
    bytes: (await fs.stat(path.join(root, `mascot-${pose}.png`))).size
  })));
  console.log(JSON.stringify(sizes));
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
