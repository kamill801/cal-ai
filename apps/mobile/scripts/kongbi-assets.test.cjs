const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const test = require("node:test");
const Jimp = require("jimp-compact");

const root = path.resolve(__dirname, "../assets/mascot");
const poses = ["welcome", "meal", "analysis", "workout", "progress", "coach", "celebrate"];

for (const pose of poses) {
  test(`Kongbi ${pose} is a bounded, nonblank transparent production PNG`, async () => {
    const file = path.join(root, `mascot-${pose}.png`);
    const image = await Jimp.read(file);
    assert.equal(image.bitmap.width, 512);
    assert.equal(image.bitmap.height, 512);
    assert.ok((await fs.stat(file)).size < 400 * 1024, "Do not bundle unoptimized masters");
    let solid = 0;
    let clear = 0;
    image.scan(0, 0, 512, 512, (x, y, index) => {
      const alpha = image.bitmap.data[index + 3];
      if (alpha > 240) solid += 1;
      if (alpha === 0) clear += 1;
      if (x < 12 || y < 12 || x >= 500 || y >= 500) {
        assert.ok(alpha <= 8, "Keep a transparent margin so body/props are not clipped");
      }
    });
    assert.ok(solid > 50000, "The character must be visible");
    assert.ok(clear > 70000, "No opaque rectangle around the character");
  });
}

test("each situation uses different artwork", async () => {
  const { createHash } = require("node:crypto");
  const hashes = await Promise.all(poses.map(async (pose) =>
    createHash("sha256").update(await fs.readFile(path.join(root, `mascot-${pose}.png`))).digest("hex")));
  assert.equal(new Set(hashes).size, poses.length);
});
