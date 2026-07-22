import type { ImageContentType } from "@cal-ai/shared";

export async function readMealImageBlob(uri: string): Promise<Blob> {
  const response = await fetch(uri);
  if (!response.ok) {
    throw new MealImageReadError(response.status);
  }
  return response.blob();
}

export function resolveImageContentType(mimeType: string | undefined, fileName: string | undefined, uri: string): ImageContentType | undefined {
  if (isSupportedImageContentType(mimeType)) {
    return mimeType;
  }
  const name = (fileName ?? uri).toLowerCase();
  if (name.endsWith(".jpg") || name.endsWith(".jpeg")) {
    return "image/jpeg";
  }
  if (name.endsWith(".png")) {
    return "image/png";
  }
  if (name.endsWith(".webp")) {
    return "image/webp";
  }
  return undefined;
}

export function fallbackImageFileName(contentType: ImageContentType): string {
  switch (contentType) {
    case "image/jpeg":
      return "meal-photo.jpg";
    case "image/png":
      return "meal-photo.png";
    case "image/webp":
      return "meal-photo.webp";
  }
}

export class MealImageReadError extends Error {
  readonly status?: number;

  constructor(status?: number) {
    super("Selected meal image could not be read.");
    this.name = "MealImageReadError";
    this.status = status;
  }
}

function isSupportedImageContentType(value: string | undefined): value is ImageContentType {
  return value === "image/jpeg" || value === "image/png" || value === "image/webp";
}
