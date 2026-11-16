import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const require = createRequire(import.meta.url);
const sharp = require("sharp");
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const output = path.join(here, "assets/feature-graphic-1024x500.png");

// Compose approved product artwork, without inventing a device screenshot.
const typography = Buffer.from(`<svg width="1024" height="500" xmlns="http://www.w3.org/2000/svg">
  <rect width="1024" height="500" fill="#F5FAF5"/>
  <rect x="0" y="0" width="14" height="500" fill="#317345"/>
  <rect x="58" y="48" width="42" height="6" rx="3" fill="#EBAC42"/>
  <g font-family="Arial, Apple SD Gothic Neo, sans-serif" letter-spacing="0">
    <text x="56" y="122" font-size="45" font-weight="700" fill="#1D3727">Trust First</text>
    <text x="56" y="177" font-size="45" font-weight="700" fill="#1D3727">Nutrition</text>
    <text x="58" y="249" font-size="29" font-weight="600" fill="#263D2F">식사도 운동도,</text>
    <text x="58" y="291" font-size="29" font-weight="600" fill="#263D2F">나를 위한 좋은 기록.</text>
    <text x="58" y="416" font-size="20" fill="#52665A">식사 기록 · 영양 목표 · 운동 루틴</text>
  </g>
</svg>`);

const mascot = await sharp(path.join(root, "apps/mobile/assets/mascot/mascot-meal.png"))
  .resize(450, 440, { fit: "contain", background: "#00000000" })
  .png().toBuffer();

await sharp(typography)
  .composite([{ input: mascot, left: 558, top: 32 }])
  .flatten({ background: "#F5FAF5" })
  .removeAlpha()
  .png({ palette: false })
  .toFile(output);

const metadata = await sharp(output).metadata();
if (metadata.width !== 1024 || metadata.height !== 500 || metadata.hasAlpha) {
  throw new Error("Invalid Google Play feature graphic dimensions or alpha");
}
process.stdout.write(`${output}\n`);
