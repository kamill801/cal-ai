import { Platform } from "react-native";
declare const process: {
  env: Record<string, string | undefined>;
};


export function getApiBaseUrl(): string {
  const envValue = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (envValue && envValue.trim().length > 0) {
    return trimTrailingSlash(envValue.trim());
  }

  if (Platform.OS === "android") {
    return "http://10.0.2.2:8015";
  }

  return "http://localhost:8015";
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}
