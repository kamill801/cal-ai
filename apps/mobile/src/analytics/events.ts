export const ANALYTICS_EVENT_NAMES = [
  "app_opened",
  "login_completed",
  "onboarding_started",
  "onboarding_completed",
  "meal_photo_selected",
  "analysis_started",
  "analysis_completed",
  "analysis_failed",
  "clarification_shown",
  "clarification_answered",
  "meal_saved",
  "workout_plan_viewed",
  "workout_started",
  "workout_completed",
  "progress_viewed",
  "coach_viewed",
  "plan_viewed",
  "checkout_started"
] as const;

const ANALYTICS_EVENT_NAME_SET = new Set<string>(ANALYTICS_EVENT_NAMES);

export type AnalyticsEventName = (typeof ANALYTICS_EVENT_NAMES)[number];
export type AnalyticsPrimitive = string | number | boolean | null;
export type AnalyticsProperties = Record<string, AnalyticsPrimitive | undefined>;

export interface AnalyticsEventInput {
  readonly eventName: AnalyticsEventName;
  readonly screen: string;
  readonly profileId?: string;
  readonly properties?: AnalyticsProperties;
  readonly occurredAt?: string;
}

export interface AnalyticsEventPayload {
  readonly event_name: AnalyticsEventName;
  readonly session_id: string;
  readonly screen: string;
  readonly profile_id?: string;
  readonly properties: Record<string, AnalyticsPrimitive>;
  readonly occurred_at: string;
}

export function isAnalyticsEventName(value: string): value is AnalyticsEventName {
  return ANALYTICS_EVENT_NAME_SET.has(value);
}

const OPERATIONAL_PROPERTY_KEYS = new Set(["provider", "source", "status", "stage", "code", "content_type", "byte_size"]);

export function sanitizeAnalyticsProperties(properties: AnalyticsProperties = {}): Record<string, AnalyticsPrimitive> {
  return Object.entries(properties).reduce<Record<string, AnalyticsPrimitive>>((safe, [key, value]) => {
    if (!OPERATIONAL_PROPERTY_KEYS.has(key) || value === undefined) {
      return safe;
    }
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean" || value === null) {
      safe[key] = value;
    }
    return safe;
  }, {});
}
