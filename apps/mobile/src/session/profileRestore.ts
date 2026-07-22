export type ProfileRefreshResult = "ok" | "not_found" | "failed";
export type ProfileRestoreAction = "open" | "clear" | "retry";

export function profileRestoreAction(result: ProfileRefreshResult): ProfileRestoreAction {
  if (result === "ok") {
    return "open";
  }
  return result === "not_found" ? "clear" : "retry";
}
