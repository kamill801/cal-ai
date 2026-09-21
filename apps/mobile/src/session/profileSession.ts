import AsyncStorage from "@react-native-async-storage/async-storage";
import { ownerStorageKey } from "./ownerScope";

const PROFILE_ID_KEY = "cal-ai/profile-id";

export async function loadProfileId(scope = "local"): Promise<string | undefined> {
  const profileId = await AsyncStorage.getItem(ownerStorageKey(PROFILE_ID_KEY, scope));
  return profileId?.trim() || undefined;
}

export async function saveProfileId(profileId: string, scope = "local"): Promise<void> {
  await AsyncStorage.setItem(ownerStorageKey(PROFILE_ID_KEY, scope), profileId);
}

export async function clearProfileId(scope = "local"): Promise<void> {
  await AsyncStorage.removeItem(ownerStorageKey(PROFILE_ID_KEY, scope));
}
