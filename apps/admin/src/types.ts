export type AdminMetricKey =
  | "today_users"
  | "new_users"
  | "active_5m"
  | "active_24h"
  | "food_analyses"
  | "meal_saves"
  | "workouts";

export type AdminMetricMap = Record<AdminMetricKey, number>;

export type AdminFunnelStep = {
  step: string;
  users: number;
  conversion_rate: number;
  dropoff_rate: number;
};

export type AdminActivity = {
  id: string;
  user_id: string;
  user_email?: string | null;
  event_type: string;
  occurred_at: string;
  summary: string;
  status?: "success" | "warning" | "error" | "info" | string;
};

export type AdminUserSummary = {
  user_id: string;
  email: string;
  display_name?: string | null;
  created_at: string;
  last_seen_at?: string | null;
  subscription_status?: string | null;
  analyses_count: number;
  meal_saves_count: number;
  workouts_count: number;
};

export type AdminPayment = {
  id: string;
  user_id: string;
  user_email?: string | null;
  provider: string;
  status: string;
  plan_name?: string | null;
  amount_cents: number;
  currency: string;
  occurred_at: string;
};

export type AdminPaymentSummary = {
  total_revenue_cents: number;
  mrr_cents: number;
  active_subscriptions: number;
  failed_payments: number;
  payments: AdminPayment[];
};

export type AdminAiOperationSummary = {
  provider: string;
  model: string;
  requests_24h: number;
  error_rate: number;
  p95_latency_ms: number | null;
  estimated_cost_cents: number | null;
};

export type AdminOverview = {
  generated_at: string;
  metrics: AdminMetricMap;
  funnel: AdminFunnelStep[];
  recent_activity: AdminActivity[];
  users: AdminUserSummary[];
  payments: AdminPaymentSummary;
  ai_operations: AdminAiOperationSummary[];
};

export type AdminTimelineEvent = {
  id: string;
  event_type: string;
  occurred_at: string;
  summary: string;
  metadata?: Record<string, unknown> | null;
};

export type AdminUserDetail = {
  user: AdminUserSummary;
  timeline: AdminTimelineEvent[];
  payments: AdminPayment[];
  ai_operations: AdminAiOperationSummary[];
};
