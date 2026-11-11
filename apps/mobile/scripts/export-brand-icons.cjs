const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const path = require("node:path");
const Jimp = require("jimp-compact");

const appRoot = path.resolve(__dirname, "..");
const brandRoot = path.join(appRoot, "assets/brand");
const storeRoot = path.resolve(appRoot, "../../docs/google-play/assets");

async function main() {
  await fs.mkdir(storeRoot, { recursive: true });
  const icon = await Jimp.read(path.join(brandRoot, "source/icon-master.png"));
  icon.scan(0, 0, icon.bitmap.width, icon.bitmap.height, (_, __, index) => {
    assert.equal(icon.bitmap.data[index + 3], 255, "Launcher/store master must be opaque");
  });
  for (const [size, destination] of [
    [1024, path.join(brandRoot, "app-icon.png")],
    [512, path.join(storeRoot, "play-icon-512.png")],
    [128, path.join(storeRoot, "kakao-icon-128.png")],
    [48, path.join(brandRoot, "favicon.png")],
  ]) {
    await icon.clone().resize(size, size, Jimp.RESIZE_BICUBIC).writeAsync(destination);
  }

  const foreground = await Jimp.read(path.join(brandRoot, "source/foreground-master.png"));
  const { width, height, data } = foreground.bitmap;
  let left = width, top = height, right = -1, bottom = -1;
  foreground.scan(0, 0, width, height, (x, y, index) => {
    if (data[index + 3] <= 8) return;
    left = Math.min(left, x);
    top = Math.min(top, y);
    right = Math.max(right, x);
    bottom = Math.max(bottom, y);
  });
  assert.ok(right > left && bottom > top, "Adaptive foreground must contain a subject");
  assert.ok(right - left < width - 1, "Adaptive foreground must have real transparent margins");
  foreground.crop(left, top, right - left + 1, bottom - top + 1);
  let radius = 0;
  foreground.scan(0, 0, foreground.bitmap.width, foreground.bitmap.height, (x, y, index) => {
    if (foreground.bitmap.data[index + 3] <= 8) return;
    radius = Math.max(radius, Math.hypot(x - (foreground.bitmap.width - 1) / 2, y - (foreground.bitmap.height - 1) / 2));
  });
  // Keep every visible pixel in the central adaptive-icon circle, including leaf tips.
  const scale = 296 / radius;
  foreground.resize(Math.round(foreground.bitmap.width * scale), Math.round(foreground.bitmap.height * scale), Jimp.RESIZE_BICUBIC);
  const adaptive = new Jimp(1024, 1024, 0x00000000);
  adaptive.composite(foreground, Math.floor((1024 - foreground.bitmap.width) / 2), Math.floor((1024 - foreground.bitmap.height) / 2));
  await adaptive.writeAsync(path.join(brandRoot, "adaptive-foreground.png"));
  const kakao = await fs.stat(path.join(storeRoot, "kakao-icon-128.png"));
  assert.ok(kakao.size <= 250 * 1024, "Kakao icon must remain below its upload limit");
  console.log("Exported opaque launcher/store/Kakao icons and transparent adaptive foreground.");
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
