import type { ImageUploadViewModel } from "@cal-ai/shared";
import type { ScanToSaveCommand } from "../flow/scanToSaveFlow";
import { MealImageReadError, readMealImageBlob } from "../media/mealImageFile";
import { ApiClientError, type CalAiApiClient } from "./client";

export async function uploadImageToStorage(activeCommand: Extract<ScanToSaveCommand, { type: "UPLOAD_IMAGE" }>, apiClient: CalAiApiClient, presign = apiClient.presignImageUpload, options: { signal?: AbortSignal; onPresigned?: (uploadId: string) => void } = {}): Promise<ImageUploadViewModel> {
  const imageBlob = await readUploadBlob(activeCommand.uri);
  throwIfUploadCancelled(options.signal);
  const presigned = await presign({
    localAssetId: activeCommand.localAssetId,
    fileName: activeCommand.fileName,
    contentType: activeCommand.contentType,
    byteSize: activeCommand.byteSize
  });
  options.onPresigned?.(presigned.imageUploadId);
  throwIfUploadCancelled(options.signal);
  let etag: string | undefined;
  if (!presigned.uploadUrl.startsWith("local-upload://")) {
    const uploadResponse = await fetch(presigned.uploadUrl, {
      method: "PUT",
      headers: presigned.headers,
      body: imageBlob,
      signal: options.signal
    });

    if (!uploadResponse.ok) {
      throw new ApiClientError({
        message: "이미지 저장소 업로드를 완료하지 못했어요. 다시 시도해 주세요.",
        status: uploadResponse.status,
        code: "image_upload_failed",
        kind: "server",
        retryable: uploadResponse.status === 408 || uploadResponse.status === 429 || uploadResponse.status >= 500
      });
    }
    etag = uploadResponse.headers.get("etag") ?? undefined;
  }

  throwIfUploadCancelled(options.signal);
  const uploaded = await apiClient.completeImageUpload({
    imageUploadId: presigned.imageUploadId,
    objectKey: presigned.objectKey,
    localAssetId: activeCommand.localAssetId,
    fileName: activeCommand.fileName,
    contentType: activeCommand.contentType,
    byteSize: activeCommand.byteSize,
    etag
  });
  throwIfUploadCancelled(options.signal);
  return uploaded;
}

export function throwIfUploadCancelled(signal?: AbortSignal): void {
  if (signal?.aborted) throw new Error("image_upload_cancelled");
}

async function readUploadBlob(uri: string): Promise<Blob> {
  try {
    return await readMealImageBlob(uri);
  } catch (error) {
    if (error instanceof MealImageReadError) {
      throw new ApiClientError({
        message: "선택한 사진을 읽지 못했어요. 다른 사진으로 다시 시도해 주세요.",
        status: error.status,
        code: "local_image_read_failed",
        kind: "validation",
        retryable: false
      });
    }
    throw error;
  }
}
