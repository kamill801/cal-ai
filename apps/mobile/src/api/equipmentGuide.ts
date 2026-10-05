import type { EquipmentCatalog, EquipmentGuide, EquipmentIdentification, EquipmentId } from "@cal-ai/shared";
import type { SelectedMealImage } from "../flow/scanToSaveFlow";
import { ApiClientError, type CalAiApiClient } from "./client";
import { throwIfUploadCancelled, uploadImageToStorage } from "./imageUpload";

export interface EquipmentGuideActions {
  getCatalog(): Promise<EquipmentCatalog>;
  identify(image: SelectedMealImage, signal?: AbortSignal): Promise<EquipmentIdentification>;
  getGuide(id: EquipmentId): Promise<EquipmentGuide>;
}

export function createEquipmentGuideActions(client: CalAiApiClient, profileId?: string): EquipmentGuideActions {
  return {
    getCatalog: () => client.getEquipmentCatalog(),
    getGuide: (id) => client.getEquipmentGuide(id),
    async identify(image, signal) {
      if (!profileId) throw new ApiClientError({ message: "목표 설정을 마친 뒤 기구 사진을 분석할 수 있어요.", code: "profile_required" });
      const extension = { "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp" }[image.contentType];
      let uploadId: string | undefined;
      try {
        const uploaded = await uploadImageToStorage(
          { type: "UPLOAD_IMAGE", requestId: 1, ...image, fileName: `equipment-guide.${extension}`, localAssetId: `equipment-${Date.now()}` },
          client,
          (input) => client.presignEquipmentImage(profileId, input),
          { signal, onPresigned: (id) => { uploadId = id; } }
        );
        throwIfUploadCancelled(signal);
        return await client.identifyEquipment(profileId, uploaded.imageUploadId, signal);
      } catch (error) {
        if (uploadId) await client.discardEquipmentImage(profileId, uploadId).catch(() => undefined);
        throw error;
      }
    }
  };
}

export function isYoutubeGuideUrl(value: string): boolean {
  // React Native's built-in URL lacks parsing getters; accept only server-issued formats.
  return value.length <= 1024 && /^https:\/\/www\.youtube\.com\/(?:watch\?v=[A-Za-z0-9_-]{11}|results\?search_query=(?:[A-Za-z0-9_.~+-]|%[0-9A-Fa-f]{2})+)$/.test(value);
}
