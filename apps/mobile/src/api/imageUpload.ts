import type { ImageUploadViewModel } from "@cal-ai/shared";
import type { ScanToSaveCommand } from "../flow/scanToSaveFlow";
import { MealImageReadError, readMealImageBlob } from "../media/mealImageFile";
import { ApiClientError, type CalAiApiClient } from "./client";

export async function uploadImageToStorage(activeCommand: Extract<ScanToSaveCommand, { type: "UPLOAD_IMAGE" }>, apiClient: CalAiApiClient): Promise<ImageUploadViewModel> {
  const imageBlob = await readUploadBlob(activeCommand.uri);
  const presigned = await apiClient.presignImageUpload({
    localAssetId: activeCommand.localAssetId,
    fileName: activeCommand.fileName,
    contentType: activeCommand.contentType,
    byteSize: activeCommand.byteSize
  });
  let etag: string | undefined;
  if (!presigned.uploadUrl.startsWith("local-upload://")) {
    const uploadResponse = await fetch(presigned.uploadUrl, {
      method: "PUT",
      headers: presigned.headers,
      body: imageBlob
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

  return apiClient.completeImageUpload({
    imageUploadId: presigned.imageUploadId,
    objectKey: presigned.objectKey,
    localAssetId: activeCommand.localAssetId,
    fileName: activeCommand.fileName,
    contentType: activeCommand.contentType,
    byteSize: activeCommand.byteSize,
    etag
  });
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
