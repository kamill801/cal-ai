import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import type { SelectedMealImage } from "../flow/scanToSaveFlow";
import { MealImageReadError, readMealImageBlob } from "./mealImageFile";

const TARGET_UPLOAD_BYTES = 900_000;
const PREPARATION_STEPS = [
  { maxEdge: 1600, compress: 0.78 },
  { maxEdge: 1280, compress: 0.7 },
  { maxEdge: 1024, compress: 0.62 },
  { maxEdge: 800, compress: 0.54 }
] as const;

export class ImagePreparationError extends Error {
  constructor(readonly code: "read_failed" | "too_large") {
    super(code);
    this.name = "ImagePreparationError";
  }
}

export async function prepareImageForUpload(input: {
  uri: string;
  width: number;
  height: number;
  localAssetId: string;
}): Promise<SelectedMealImage> {
  let latestUri = input.uri;
  let latestSize = Number.POSITIVE_INFINITY;

  for (const step of PREPARATION_STEPS) {
    const context = ImageManipulator.manipulate(input.uri);
    const resize = resizeWithin(input.width, input.height, step.maxEdge);
    if (resize) {
      context.resize(resize);
    }
    const rendered = await context.renderAsync();
    const saved = await rendered.saveAsync({ compress: step.compress, format: SaveFormat.JPEG });
    latestUri = saved.uri;
    latestSize = await readByteSize(saved.uri);
    if (latestSize <= TARGET_UPLOAD_BYTES) {
      break;
    }
  }

  if (latestSize > TARGET_UPLOAD_BYTES) {
    throw new ImagePreparationError("too_large");
  }

  return {
    localAssetId: `${input.localAssetId}-prepared-${latestSize}`.slice(0, 120),
    uri: latestUri,
    fileName: `cal-ai-${Date.now()}.jpg`,
    contentType: "image/jpeg",
    byteSize: latestSize
  };
}

function resizeWithin(width: number, height: number, maxEdge: number): { width: number; height: number } | undefined {
  const longestEdge = Math.max(width, height);
  if (!Number.isFinite(longestEdge) || longestEdge <= 0 || longestEdge <= maxEdge) {
    return undefined;
  }
  const scale = maxEdge / longestEdge;
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale))
  };
}

async function readByteSize(uri: string): Promise<number> {
  try {
    return (await readMealImageBlob(uri)).size;
  } catch (error) {
    if (error instanceof MealImageReadError) {
      throw new ImagePreparationError("read_failed");
    }
    throw error;
  }
}
