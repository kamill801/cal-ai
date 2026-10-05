import { createCalAiApiClient } from "../api/client";
import { createEquipmentGuideActions, isYoutubeGuideUrl } from "../api/equipmentGuide";
import { getApiBaseUrl } from "../api/config";

export async function runEquipmentGuideSmoke(): Promise<void> {
  const originalFetch = globalThis.fetch;
  const calls: string[] = [];
  globalThis.fetch = (async (url, init) => {
    const target = String(url);
    calls.push(target);
    const body = init?.body && typeof init.body === "string" ? JSON.parse(init.body) : undefined;
    const response = (value: unknown) => ({ ok: true, status: 200, json: async () => value }) as Response;
    if (target === "blob:equipment") return { ok: true, status: 200, blob: async () => new Blob(["equipment"]) } as Response;
    if (target.endsWith("/equipment-guides/catalog")) return response({ items: [{ id: "lat_pulldown", name: "랫풀다운 머신", exercises: ["랫풀다운"], safety_note: "설정 확인" }], photo_identification_available: true });
    if (target.endsWith("/equipment-image-uploads/presign")) {
      if (body.file_name || body.local_asset_id || body.content_type !== "image/jpeg") throw new Error("equipment presign must send only validated metadata");
      return response({ image_upload_id: "equipment-upload", object_key: "uploads/equipment-upload/equipment-guide.jpg", upload_url: "https://storage.example/signed", headers: { "Content-Type": "image/jpeg" }, expires_at: "2026-10-05T12:00:00Z", max_bytes: 1000000, soft_limit_bytes: 8000000000, soft_limit_exceeded: false, ttl_days: 7 });
    }
    if (target === "https://storage.example/signed") {
      if (init?.method !== "PUT" || (init.headers as Record<string, string>).Authorization) throw new Error("storage PUT must not receive app credentials");
      return { ok: true, status: 200, headers: { get: () => "etag" } } as unknown as Response;
    }
    if (target.endsWith("/image-uploads/complete")) {
      if (body.file_name !== "equipment-guide.jpg") throw new Error("original image filename must not leave the device");
      return response({ image_upload_id: "equipment-upload", image_reference: "r2://private/equipment", status: "ready" });
    }
    if (target.endsWith("/equipment-identifications")) {
      if (body.image_upload_id !== "equipment-upload") throw new Error("analysis must reference the completed upload");
      return response({ equipment_id: "lat_pulldown", confidence: "medium", visible_evidence: ["상단 도르래"], needs_confirmation: true });
    }
    if (target.endsWith("/equipment-guides/lat_pulldown")) return response({ equipment_id: "lat_pulldown", name: "랫풀다운 머신", exercises: ["랫풀다운"], safety_note: "설정 확인", search_url: "https://www.youtube.com/results?search_query=lat+pulldown", source: "search_link", videos: [] });
    throw new Error("unexpected equipment request");
  }) as typeof fetch;
  try {
    const actions = createEquipmentGuideActions(createCalAiApiClient("https://app.example", "session-token"), "profile-a");
    const catalog = await actions.getCatalog();
    if (!catalog.photoIdentificationAvailable || catalog.items[0].safetyNote !== "설정 확인") throw new Error("catalog mapping failed");
    const identified = await actions.identify({ uri: "blob:equipment", localAssetId: "private-camera-id", fileName: "private-original.jpg", contentType: "image/jpeg", byteSize: 9 });
    if (identified.equipmentId !== "lat_pulldown" || !identified.needsConfirmation) throw new Error("identification mapping failed");
    const guide = await actions.getGuide("lat_pulldown");
    if (!isYoutubeGuideUrl(guide.searchUrl) || guide.source !== "search_link") throw new Error("guide fallback mapping failed");
    const putIndex = calls.indexOf("https://storage.example/signed");
    const completeIndex = calls.findIndex((value) => value.endsWith("/image-uploads/complete"));
    const identifyIndex = calls.findIndex((value) => value.endsWith("/equipment-identifications"));
    if (!(putIndex < completeIndex && completeIndex < identifyIndex)) throw new Error("equipment upload order failed");
  } finally {
    globalThis.fetch = originalFetch;
  }

  for (const invalid of ["http://www.youtube.com/watch?v=abc123XYZ_-", "https://www.youtube.com.evil.example/watch?v=abc123XYZ_-", "https://www.youtube.com@evil.example/results?search_query=machine", "javascript:alert(1)", "https://www.youtube.com/watch?v=bad", "https://www.youtube.com:8443/watch?v=abc123XYZ_-", "https://www.youtube.com/results?search_query=machine&redirect=https://evil.example", "https://www.youtube.com/results?search_query=%ZZ", "https://www.youtube.com/results?search_query="]) {
    if (isYoutubeGuideUrl(invalid)) throw new Error("unsafe guide link accepted");
  }
  if (!isYoutubeGuideUrl("https://www.youtube.com/watch?v=abc123XYZ_-")) throw new Error("valid video link rejected");
  const controller = new AbortController();
  const cancelledCalls: string[] = [];
  globalThis.fetch = (async (url) => {
    const target = String(url);
    cancelledCalls.push(target);
    if (target === "blob:equipment") return { ok: true, status: 200, blob: async () => new Blob(["equipment"]) } as Response;
    if (target.endsWith("/equipment-image-uploads/presign")) {
      controller.abort();
      return { ok: true, status: 200, json: async () => ({ image_upload_id: "cancelled-upload", object_key: "uploads/cancelled/equipment-guide.jpg", upload_url: "https://storage.example/signed", headers: {}, expires_at: "2099-01-01T00:00:00Z", max_bytes: 1000000, soft_limit_bytes: 8000000000, soft_limit_exceeded: false, ttl_days: 7 }) } as Response;
    }
    if (target.endsWith("/equipment-image-uploads/cancelled-upload")) return { ok: true, status: 200, json: async () => ({ status: "deleted" }) } as Response;
    throw new Error("cancelled upload must not PUT or identify");
  }) as typeof fetch;
  try {
    let rejected = false;
    try {
      await createEquipmentGuideActions(createCalAiApiClient("https://app.example", "session-token"), "profile-a").identify({ uri: "blob:equipment", localAssetId: "fixture", fileName: "fixture.jpg", contentType: "image/jpeg", byteSize: 9 }, controller.signal);
    } catch { rejected = true; }
    if (!rejected || !cancelledCalls.some((url) => url.endsWith("/equipment-image-uploads/cancelled-upload")) || cancelledCalls.some((url) => url.endsWith("/equipment-identifications"))) throw new Error("cancelled upload cleanup failed");
  } finally {
    globalThis.fetch = originalFetch;
  }
  const scope = globalThis as { location?: { origin: string } };
  const originalLocation = scope.location;
  scope.location = { origin: "https://feature-preview.example" };
  try {
    if (getApiBaseUrl() !== scope.location.origin) throw new Error("web preview must use its own API");
    scope.location = { origin: "http://localhost:8081" };
    if (getApiBaseUrl() !== "http://localhost:8015") throw new Error("local Expo web must keep its API fallback");
  } finally {
    if (originalLocation) scope.location = originalLocation;
    else delete scope.location;
  }
}
