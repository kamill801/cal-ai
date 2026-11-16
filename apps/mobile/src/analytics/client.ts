import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppState, type AppStateStatus, type NativeEventSubscription } from "react-native";
import { getApiBaseUrl } from "../api/config";
import { ApiClientError } from "../api";
import { ownerStorageKey } from "../session/ownerScope";
import { sanitizeAnalyticsProperties, type AnalyticsEventInput, type AnalyticsEventPayload } from "./events";

const ANALYTICS_SESSION_ID_KEY = "cal-ai/analytics-session-id";
const HEARTBEAT_INTERVAL_MS = 60_000;
const SESSION_TIMEOUT_MS = 30 * 60_000;
const SESSION_TOUCH_INTERVAL_MS = 5 * 60_000;

export interface AnalyticsEventClient {
  trackEvent(input: AnalyticsEventInput): Promise<void>;
  sendHeartbeat(input?: { screen?: string; profileId?: string }): Promise<void>;
  getSessionId(): Promise<string | undefined>;
  clearSession(): Promise<void>;
}

export interface ForegroundHeartbeat {
  start(): void;
  stop(): void;
}

export function createAnalyticsEventClient(baseUrl = getApiBaseUrl(), accessToken?: string, scope = "local", isAllowed: () => boolean = () => false, onConsentRequired?: () => void): AnalyticsEventClient {
  const root = baseUrl.replace(/\/+$/, "");
  let sessionIdPromise: Promise<string | undefined> | undefined;
  let lastSessionTouchAt = 0;
  let storageWork: Promise<unknown> = Promise.resolve();
  let generation = 0;

  const getSessionId = async (): Promise<string | undefined> => {
    if (!isAllowed()) return undefined;
    const currentGeneration = generation;
    const stillAllowed = () => isAllowed() && currentGeneration === generation;
    if (!sessionIdPromise) {
      sessionIdPromise = storageWork.then(() => loadOrCreateSessionId(scope, stillAllowed));
      storageWork = sessionIdPromise.catch(() => undefined);
    }
    const sessionId = await sessionIdPromise;
    if (!stillAllowed() || !sessionId) return undefined;
    const now = Date.now();
    if (now - lastSessionTouchAt >= SESSION_TOUCH_INTERVAL_MS) {
      lastSessionTouchAt = now;
      storageWork = storageWork.then(() => stillAllowed() ? persistSession(sessionId, now, scope) : undefined).catch(() => undefined);
    }
    return sessionId;
  };

  const post = async (path: string, body: unknown): Promise<void> => {
    if (!isAllowed()) return;
    let response: Response;
    try {
      response = await fetch(`${root}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
        },
        body: JSON.stringify(body)
      });
    } catch {
      throw new ApiClientError({
        message: "분석 이벤트를 전송하지 못했어요. 네트워크 연결을 확인해 주세요.",
        code: "analytics_network_error",
        kind: "network",
        retryable: true
      });
    }

    if (!response.ok) {
      if (response.status === 403) onConsentRequired?.();
      throw new ApiClientError({
        message: "분석 이벤트를 저장하지 못했어요.",
        status: response.status,
        code: `analytics_http_${response.status}`,
        kind: response.status >= 500 ? "server" : "http",
        retryable: response.status === 408 || response.status === 429 || response.status >= 500
      });
    }
  };

  return {
    getSessionId,
    async clearSession() {
      generation += 1;
      sessionIdPromise = undefined;
      lastSessionTouchAt = 0;
      storageWork = storageWork.catch(() => undefined).then(() => AsyncStorage.removeItem(ownerStorageKey(ANALYTICS_SESSION_ID_KEY, scope)));
      await storageWork;
    },
    async trackEvent(input) {
      const sessionId = await getSessionId();
      if (!sessionId || !isAllowed()) return;
      const payload: AnalyticsEventPayload = {
        event_name: input.eventName,
        session_id: sessionId,
        screen: input.screen,
        ...(input.profileId ? { profile_id: input.profileId } : {}),
        properties: sanitizeAnalyticsProperties(input.properties),
        occurred_at: input.occurredAt ?? new Date().toISOString()
      };
      await post("/v1/analytics/events", payload);
    },
    async sendHeartbeat(input = {}) {
      const sessionId = await getSessionId();
      if (!sessionId || !isAllowed()) return;
      await post("/v1/analytics/heartbeat", {
        session_id: sessionId,
        screen: input.screen ?? "unknown",
        ...(input.profileId ? { profile_id: input.profileId } : {})
      });
    }
  };
}

export function createForegroundHeartbeat(client: AnalyticsEventClient, input: { screen?: string; profileId?: string } = {}): ForegroundHeartbeat {
  let interval: ReturnType<typeof setInterval> | undefined;
  let subscription: NativeEventSubscription | undefined;
  let appState: AppStateStatus = AppState.currentState;

  const send = (): void => {
    void client.sendHeartbeat(input).catch(() => undefined);
  };

  const startTimer = (): void => {
    if (interval) {
      return;
    }
    send();
    interval = setInterval(send, HEARTBEAT_INTERVAL_MS);
  };

  const stopTimer = (): void => {
    if (!interval) {
      return;
    }
    clearInterval(interval);
    interval = undefined;
  };

  const subscribe = (): void => {
    if (subscription) {
      return;
    }
    subscription = AppState.addEventListener("change", (nextState) => {
      appState = nextState;
      if (nextState === "active") {
        startTimer();
      } else {
        stopTimer();
      }
    });
  };

  return {
    start() {
      subscribe();
      if (appState === "active") {
        startTimer();
      }
    },
    stop() {
      stopTimer();
      subscription?.remove();
      subscription = undefined;
    }
  };
}

async function loadOrCreateSessionId(scope: string, isAllowed: () => boolean): Promise<string | undefined> {
  const existing = await AsyncStorage.getItem(ownerStorageKey(ANALYTICS_SESSION_ID_KEY, scope));
  if (!isAllowed()) return undefined;
  if (existing?.trim()) {
    try {
      const stored = JSON.parse(existing) as { id?: unknown; lastSeenAt?: unknown };
      if (
        typeof stored.id === "string" &&
        typeof stored.lastSeenAt === "number" &&
        Date.now() - stored.lastSeenAt < SESSION_TIMEOUT_MS
      ) {
        return stored.id;
      }
    } catch {
      // Legacy plain-text session ids are rotated into the bounded session format.
    }
  }
  const sessionId = createSessionId();
  await persistSession(sessionId, Date.now(), scope);
  return sessionId;
}

async function persistSession(sessionId: string, lastSeenAt: number, scope: string): Promise<void> {
  await AsyncStorage.setItem(
    ownerStorageKey(ANALYTICS_SESSION_ID_KEY, scope),
    JSON.stringify({ id: sessionId, lastSeenAt })
  );
}

function createSessionId(): string {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `mobile-${random}`;
}
