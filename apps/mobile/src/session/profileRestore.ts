export type ProfileRefreshResult = "ok" | "not_found" | "failed" | "age_restricted";
export type ProfileRestoreAction = "open" | "clear" | "retry" | "restrict";

export function shouldWaitForInitialDashboard(input: {
  profileId?: string;
  hasDashboard: boolean;
  status: "idle" | "loading" | "success" | "error";
}): boolean {
  return Boolean(input.profileId) && !input.hasDashboard && input.status !== "error";
}

export function profileIdForRestore(input: { authEnabled: boolean; cachedProfileId?: string; serverProfileId?: string | null }): string | undefined {
  if (input.authEnabled) {
    return input.serverProfileId ?? undefined;
  }
  return input.cachedProfileId;
}

export function profileRestoreAction(result: ProfileRefreshResult): ProfileRestoreAction {
  if (result === "age_restricted") {
    return "restrict";
  }
  if (result === "ok") {
    return "open";
  }
  return result === "not_found" ? "clear" : "retry";
}
