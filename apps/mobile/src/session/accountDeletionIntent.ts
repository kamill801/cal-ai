interface IntentStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

declare const window: {
  location?: { href: string };
  sessionStorage: IntentStorage;
  history: { replaceState(data: unknown, unused: string, url: string): void };
} | undefined;

// These web-only helpers also compile in the native ES-only type environment.
declare const URL: {
  new (url: string): {
    pathname: string;
    search: string;
    hash: string;
    searchParams: { get(key: string): string | null; delete(key: string): void };
  };
};

const INTENT_KEY = "trust-first:account-deletion-intent";

export function captureAccountDeletionIntent(url: string, storage?: IntentStorage): boolean {
  let requested = false;
  try {
    requested = new URL(url).searchParams.get("action") === "delete-account";
    if (requested) storage?.setItem(INTENT_KEY, "1");
    return requested || storage?.getItem(INTENT_KEY) === "1";
  } catch {
    return requested;
  }
}

export function clearAccountDeletionIntent(storage?: IntentStorage): void {
  try { storage?.removeItem(INTENT_KEY); } catch { /* Storage may be unavailable. */ }
}

export function readWebAccountDeletionIntent(): boolean {
  if (typeof window === "undefined") return false;
  let href: string | undefined;
  try { href = window.location?.href; } catch { return false; }
  if (!href) return false;
  try { return captureAccountDeletionIntent(href, window.sessionStorage); }
  catch { return captureAccountDeletionIntent(href); }
}

export function dismissWebAccountDeletionIntent(): void {
  if (typeof window === "undefined") return;
  try { clearAccountDeletionIntent(window.sessionStorage); } catch { /* Storage access itself may be blocked. */ }
  try {
    const href = window.location?.href;
    if (!href) return;
    const url = new URL(href);
    if (url.searchParams.get("action") === "delete-account") {
      url.searchParams.delete("action");
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    }
  } catch { /* A deletion link never grants authority or triggers deletion. */ }
}
