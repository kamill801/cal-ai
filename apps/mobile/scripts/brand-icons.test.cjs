const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const test = require("node:test");
const Jimp = require("jimp-compact");
const appRoot = path.resolve(__dirname, "..");
const storeRoot = path.resolve(appRoot, "../../docs/google-play/assets");

for (const [size, file] of [
  [1024, path.join(appRoot, "assets/brand/app-icon.png")],
  [512, path.join(storeRoot, "play-icon-512.png")],
  [128, path.join(storeRoot, "kakao-icon-128.png")],
  [48, path.join(appRoot, "assets/brand/favicon.png")],
]) {
  test(`${size}px opaque square export has visible artwork`, async () => {
    const image = await Jimp.read(file);
    assert.equal(image.bitmap.width, size);
    assert.equal(image.bitmap.height, size);
    const colors = new Set();
    image.scan(0, 0, size, size, (_, __, index) => {
      assert.equal(image.bitmap.data[index + 3], 255);
      if (index % 64 === 0) colors.add(image.bitmap.data.readUInt32BE(index));
    });
    assert.ok(colors.size > 20, "Icon must not be a blank square");
    if (size === 128) assert.ok((await fs.stat(file)).size <= 250 * 1024);
    if (size === 512) assert.ok((await fs.stat(file)).size <= 1024 * 1024);
  });
}

test("adaptive foreground has genuine alpha and fits the central mask-safe circle", async () => {
  const image = await Jimp.read(path.join(appRoot, "assets/brand/adaptive-foreground.png"));
  assert.equal(image.bitmap.width, 1024);
  assert.equal(image.bitmap.height, 1024);
  let visible = 0, clear = 0;
  image.scan(0, 0, 1024, 1024, (x, y, index) => {
    const alpha = image.bitmap.data[index + 3];
    if (!alpha) clear++;
    if (alpha > 8) {
      visible++;
      assert.ok(Math.hypot(x - 511.5, y - 511.5) <= 305, "Artwork must not be clipped by adaptive masks");
    }
  });
  assert.ok(visible > 100000 && clear > 600000);
});

test("Expo uses the checked launcher, adaptive and web assets", async () => {
  const { expo } = JSON.parse(await fs.readFile(path.join(appRoot, "app.json"), "utf8"));
  assert.equal(expo.icon, "./assets/brand/app-icon.png");
  assert.equal(expo.android.adaptiveIcon.foregroundImage, "./assets/brand/adaptive-foreground.png");
  assert.equal(expo.android.adaptiveIcon.backgroundColor, "#dcefe4");
  assert.equal(expo.web.favicon, "./assets/brand/favicon.png");
});
