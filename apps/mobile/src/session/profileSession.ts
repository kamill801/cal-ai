import AsyncStorage from "@react-native-async-storage/async-storage";

const PROFILE_ID_KEY = "cal-ai/profile-id";

export async function loadProfileId(): Promise<string | undefined> {
  const profileId = await AsyncStorage.getItem(PROFILE_ID_KEY);
  return profileId?.trim() || undefined;
}

export async function saveProfileId(profileId: string): Promise<void> {
  await AsyncStorage.setItem(PROFILE_ID_KEY, profileId);
}

export async function clearProfileId(): Promise<void> {
  await AsyncStorage.removeItem(PROFILE_ID_KEY);
}
