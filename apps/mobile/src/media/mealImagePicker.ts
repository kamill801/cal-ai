import * as ImagePicker from "expo-image-picker";
import type { SelectedMealImage } from "../flow/scanToSaveFlow";
import { fallbackImageFileName, MealImageReadError, readMealImageBlob, resolveImageContentType } from "./mealImageFile";

export type MealImagePickerResult =
  | { readonly status: "selected"; readonly image: SelectedMealImage }
  | { readonly status: "cancelled" }
  | { readonly status: "permission_denied" }
  | { readonly status: "camera_unavailable" }
  | { readonly status: "unsupported_type" }
  | { readonly status: "read_failed" };

export async function pickMealImageFromLibrary(): Promise<MealImagePickerResult> {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    return { status: "permission_denied" };
  }

  const picked = await ImagePicker.launchImageLibraryAsync({
    allowsEditing: false,
    mediaTypes: ["images"],
    quality: 0.85
  });

  if (picked.canceled) {
    return { status: "cancelled" };
  }

  return createSelectedMealImage(picked.assets[0]);
}

export async function captureMealImageWithCamera(): Promise<MealImagePickerResult> {
  const permission = await ImagePicker.requestCameraPermissionsAsync();
  if (!permission.granted) {
    return { status: "permission_denied" };
  }

  try {
    const captured = await ImagePicker.launchCameraAsync({
      allowsEditing: false,
      mediaTypes: ["images"],
      quality: 0.85
    });

    if (captured.canceled) {
      return { status: "cancelled" };
    }

    return createSelectedMealImage(captured.assets[0]);
  } catch (error) {
    if (error instanceof Error && error.name === "UnavailabilityError") {
      return { status: "camera_unavailable" };
    }
    throw error;
  }
}

async function createSelectedMealImage(asset: ImagePicker.ImagePickerAsset | undefined): Promise<MealImagePickerResult> {
  if (!asset) {
    return { status: "cancelled" };
  }
  const contentType = resolveImageContentType(asset.mimeType, asset.fileName ?? undefined, asset.uri);
  if (!contentType) {
    return { status: "unsupported_type" };
  }

  try {
    const byteSize = typeof asset.fileSize === "number" && asset.fileSize > 0 ? asset.fileSize : await readImageByteSize(asset.uri);
    const fileName = (asset.fileName ?? fallbackImageFileName(contentType)).slice(0, 180);
    const assetId = asset.assetId?.trim();
    const localAssetId = assetId && assetId.length <= 120 ? assetId : `mobile-${Date.now()}-${byteSize}`;
    return {
      status: "selected",
      image: {
        localAssetId,
        uri: asset.uri,
        fileName,
        contentType,
        byteSize
      }
    };
  } catch (error) {
    if (error instanceof MealImageReadError) {
      return { status: "read_failed" };
    }
    throw error;
  }
}

async function readImageByteSize(uri: string): Promise<number> {
  const blob = await readMealImageBlob(uri);
  return blob.size;
}
