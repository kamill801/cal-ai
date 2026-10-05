export type EquipmentId = "lat_pulldown" | "leg_press" | "chest_press" | "seated_row" | "cable_machine" | "smith_machine" | "squat_rack" | "dumbbell" | "treadmill" | "leg_curl" | "leg_extension" | "hack_squat" | "pec_deck" | "shoulder_press" | "assisted_pullup" | "hip_abduction" | "stationary_bike" | "rowing_machine";

export interface EquipmentItem {
  id: EquipmentId;
  name: string;
  exercises: string[];
  safetyNote: string;
}

export interface EquipmentCatalog {
  items: EquipmentItem[];
  photoIdentificationAvailable: boolean;
}

export interface EquipmentIdentification {
  equipmentId: EquipmentId | null;
  confidence: "high" | "medium" | "low" | "none";
  visibleEvidence: string[];
  needsConfirmation: true;
  cleanupPending: boolean;
}

export interface EquipmentGuide {
  equipmentId: EquipmentId;
  name: string;
  exercises: string[];
  safetyNote: string;
  searchUrl: string;
  source: "youtube_api" | "search_link";
  videos: { videoId: string; title: string; channelTitle: string; url: string }[];
}

export interface ApiEquipmentCatalog {
  items: { id: EquipmentId; name: string; exercises: string[]; safety_note: string }[];
  photo_identification_available: boolean;
}

export interface ApiEquipmentIdentification {
  equipment_id: EquipmentId | null;
  confidence: EquipmentIdentification["confidence"];
  visible_evidence: string[];
  needs_confirmation: true;
  cleanup_pending?: boolean;
}

export interface ApiEquipmentGuide {
  equipment_id: EquipmentId;
  name: string;
  exercises: string[];
  safety_note: string;
  search_url: string;
  source: EquipmentGuide["source"];
  videos: { video_id: string; title: string; channel_title: string; url: string }[];
}

export function mapApiEquipmentCatalog(value: ApiEquipmentCatalog): EquipmentCatalog {
  return {
    items: value.items.map((item) => ({ id: item.id, name: item.name, exercises: item.exercises, safetyNote: item.safety_note })),
    photoIdentificationAvailable: value.photo_identification_available
  };
}

export function mapApiEquipmentIdentification(value: ApiEquipmentIdentification): EquipmentIdentification {
  return { equipmentId: value.equipment_id, confidence: value.confidence, visibleEvidence: value.visible_evidence, needsConfirmation: value.needs_confirmation, cleanupPending: value.cleanup_pending ?? false };
}

export function mapApiEquipmentGuide(value: ApiEquipmentGuide): EquipmentGuide {
  return {
    equipmentId: value.equipment_id, name: value.name, exercises: value.exercises, safetyNote: value.safety_note,
    searchUrl: value.search_url, source: value.source,
    videos: value.videos.map((item) => ({ videoId: item.video_id, title: item.title, channelTitle: item.channel_title, url: item.url }))
  };
}
