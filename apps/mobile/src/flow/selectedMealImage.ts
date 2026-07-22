import type { ImageContentType } from "@cal-ai/shared";

export interface SelectedMealImage {
  readonly localAssetId: string;
  readonly uri: string;
  readonly fileName: string;
  readonly contentType: ImageContentType;
  readonly byteSize: number;
}
