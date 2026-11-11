import { profileIdForRestore, profileRestoreAction, shouldWaitForInitialDashboard } from "../session/profileRestore";
import { ownerScope, ownerStorageKey } from "../session/ownerScope";

export function runSessionRestoreSmoke(): void {
  for (const status of ["idle", "loading", "success"] as const) {
    if (!shouldWaitForInitialDashboard({ profileId: "fixture-profile", hasDashboard: false, status })) {
      throw new Error("an owned profile without real dashboard data must not display demo meals");
    }
    if (shouldWaitForInitialDashboard({ profileId: "fixture-profile", hasDashboard: true, status })) {
      throw new Error("background refresh must not hide an already loaded real dashboard");
    }
    if (shouldWaitForInitialDashboard({ hasDashboard: false, status })) {
      throw new Error("a new user without a profile must be able to reach onboarding");
    }
  }
  if (shouldWaitForInitialDashboard({ profileId: "fixture-profile", hasDashboard: false, status: "error" })) {
    throw new Error("initial dashboard failure must reach the retry screen, not indefinite loading");
  }
  const first = ownerScope(true, "first-user");
  const second = ownerScope(true, "second-user");
  if (first === second || first === ownerScope(true) || first === ownerScope(false)) {
    throw new Error("account switch and logout must remount owner state");
  }
  for (const key of ["cal-ai/profile-id", "cal-ai/analytics-session-id"]) {
    if (ownerStorageKey(key, first) === ownerStorageKey(key, second)) {
      throw new Error("profile and analytics storage must be isolated per owner");
    }
    if (ownerStorageKey(key, first) === key || ownerStorageKey(key, "local") !== key) {
      throw new Error("authenticated users must not inherit anonymous storage");
    }
  }
  if (profileRestoreAction("ok") !== "open") {
    throw new Error("successful restore must open the saved profile");
  }
  if (profileRestoreAction("not_found") !== "clear") {
    throw new Error("confirmed missing profile must clear the saved handle");
  }
  if (profileRestoreAction("failed") !== "retry") {
    throw new Error("transient restore failure must retain the saved handle for retry");
  }
  if (profileRestoreAction("age_restricted") !== "restrict") {
    throw new Error("age restrictions must retain the profile and open account controls, not retry or onboarding");
  }
  if (profileIdForRestore({ authEnabled: true, cachedProfileId: "device-profile", serverProfileId: "server-profile" }) !== "server-profile") {
    throw new Error("authenticated restore must prefer the server-owned profile over device cache");
  }
  if (profileIdForRestore({ authEnabled: true, cachedProfileId: "device-profile", serverProfileId: null }) !== undefined) {
    throw new Error("authenticated restore must treat no owned server profile as no profile");
  }
  if (profileIdForRestore({ authEnabled: false, cachedProfileId: "device-profile", serverProfileId: "server-profile" }) !== "device-profile") {
    throw new Error("local unauthenticated restore must keep device-cache behavior");
  }
}
