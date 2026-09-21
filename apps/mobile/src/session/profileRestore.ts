export type ProfileRefreshResult = "ok" | "not_found" | "failed";
export type ProfileRestoreAction = "open" | "clear" | "retry";

export function profileIdForRestore(input: { authEnabled: boolean; cachedProfileId?: string; serverProfileId?: string | null }): string | undefined {
  if (input.authEnabled) {
    return input.serverProfileId ?? undefined;
  }
  return input.cachedProfileId;
}

export function profileRestoreAction(result: ProfileRefreshResult): ProfileRestoreAction {
  if (result === "ok") {
    return "open";
  }
  return result === "not_found" ? "clear" : "retry";
}
