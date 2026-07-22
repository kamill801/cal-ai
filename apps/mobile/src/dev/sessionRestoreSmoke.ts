import { profileRestoreAction } from "../session/profileRestore";

export function runSessionRestoreSmoke(): void {
  if (profileRestoreAction("ok") !== "open") {
    throw new Error("successful restore must open the saved profile");
  }
  if (profileRestoreAction("not_found") !== "clear") {
    throw new Error("confirmed missing profile must clear the saved handle");
  }
  if (profileRestoreAction("failed") !== "retry") {
    throw new Error("transient restore failure must retain the saved handle for retry");
  }
}
