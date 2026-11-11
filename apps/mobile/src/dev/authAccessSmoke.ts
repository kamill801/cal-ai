import { signInWithPassword } from "../auth/passwordLogin";
import { captureAccountDeletionIntent, clearAccountDeletionIntent, dismissWebAccountDeletionIntent, readWebAccountDeletionIntent } from "../session/accountDeletionIntent";

export async function runAuthAccessSmoke(): Promise<void> {
  let calls = 0;
  const client = { auth: { async signInWithPassword(input: { email: string; password: string }) {
    calls += 1;
    if (input.email !== "review@example.test" || input.password !== " fixture pass ") throw new Error("unexpected normalization");
    return { error: null };
  } } };
  await signInWithPassword(client, " review@example.test ", " fixture pass ");
  if (calls !== 1) throw new Error("password login must use ordinary auth exactly once");
  for (const email of ["", "bad", "a@b", "a b@example.test"]) {
    let rejected = false;
    try { await signInWithPassword(client, email, "fixture"); } catch { rejected = true; }
    if (!rejected || calls !== 1) throw new Error("invalid input reached auth provider");
  }
  try {
    await signInWithPassword({ auth: { async signInWithPassword() { return { error: new Error("sentinel-sensitive-provider-detail") }; } } }, "review@example.test", "fixture");
    throw new Error("provider failure not rejected");
  } catch (error) {
    if (!(error instanceof Error) || error.message !== "로그인하지 못했어요. 입력한 정보를 확인하고 다시 시도해 주세요.") throw new Error("auth error was not sanitized");
  }
  const values = new Map<string, string>();
  const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => { values.set(key, value); }, removeItem: (key: string) => { values.delete(key); } };
  if (captureAccountDeletionIntent("https://app.example.test/", storage)) throw new Error("unexpected deletion intent");
  if (!captureAccountDeletionIntent("https://app.example.test/?action=delete-account", storage)) throw new Error("deletion link ignored");
  if (!captureAccountDeletionIntent("https://app.example.test/auth/callback", storage)) throw new Error("intent lost during OAuth callback");
  clearAccountDeletionIntent(storage);
  if (captureAccountDeletionIntent("https://app.example.test/auth/callback", storage)) throw new Error("deletion intent not dismissed");
  if (captureAccountDeletionIntent("not a URL", storage)) throw new Error("invalid URL accepted");
  if (readWebAccountDeletionIntent()) throw new Error("native environment cannot contain web intent");
  dismissWebAccountDeletionIntent();
  const runtime = globalThis as unknown as { window?: object };
  runtime.window = globalThis;
  try {
    if (readWebAccountDeletionIntent()) throw new Error("native global cannot contain web intent");
    dismissWebAccountDeletionIntent();
  } finally { delete runtime.window; }
  let replacedUrl = "";
  runtime.window = { location: { href: "https://app.example.test/?action=delete-account&keep=1" }, sessionStorage: storage, history: { replaceState(_data: unknown, _unused: string, url: string) { replacedUrl = url; } } };
  try {
    if (!readWebAccountDeletionIntent()) throw new Error("web intent not captured");
    dismissWebAccountDeletionIntent();
    if (replacedUrl !== "/?keep=1" || values.size !== 0) throw new Error("web intent not cleared");
    replacedUrl = "";
    runtime.window = {
      location: { href: "https://app.example.test/?action=delete-account&keep=1#section" },
      get sessionStorage() { throw new Error("storage disabled"); },
      history: { replaceState(_data: unknown, _unused: string, url: string) { replacedUrl = url; } },
    };
    if (!readWebAccountDeletionIntent()) throw new Error("storage failure suppressed explicit intent");
    dismissWebAccountDeletionIntent();
    if (replacedUrl !== "/?keep=1#section") throw new Error("storage failure prevented deletion link dismissal");
  } finally { delete runtime.window; }
}
