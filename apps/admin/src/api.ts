import type {
  AdminActivity,
  AdminAiOperationSummary,
  AdminFunnelStep,
  AdminOverview,
  AdminPayment,
  AdminTimelineEvent,
  AdminUserDetail,
  AdminUserSummary
} from "./types";

export class AdminApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
  }
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

export async function loginAdmin(username: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
  if (!apiBaseUrl) throw new Error("관리자 로그인 설정을 확인해 주세요.");
  const response = await fetch(`${apiBaseUrl}/internal/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    cache: "no-store",
    signal: AbortSignal.timeout(20_000)
  });
  if (!response.ok) {
    throw new Error(response.status === 429
      ? "로그인 시도가 많아요. 15분 뒤 다시 시도해 주세요."
      : response.status === 401
        ? "아이디 또는 비밀번호를 확인해 주세요."
        : "관리자 로그인을 사용할 수 없어요. 설정을 확인해 주세요.");
  }
  return response.json();
}

async function requestJson<T>(path: string, accessToken: string, signal?: AbortSignal): Promise<T> {
  if (!apiBaseUrl) {
    throw new AdminApiError(500, "VITE_API_BASE_URL is not configured.");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: "application/json"
    },
    cache: "no-store",
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(20_000)]) : AbortSignal.timeout(20_000)
  });

  if (response.status === 401 || response.status === 403) {
    throw new AdminApiError(response.status, "관리자 접근 권한이 없거나 세션이 만료됐어요. 다시 로그인해 주세요.");
  }

  if (!response.ok) {
    throw new AdminApiError(response.status, "관리자 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.");
  }

  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new AdminApiError(502, "관리자 API 배포 상태를 확인해 주세요.");
  }

  return (await response.json()) as T;
}

export async function getOverview(accessToken: string, signal?: AbortSignal): Promise<AdminOverview> {
  return normalizeOverview(await requestJson<AdminOverviewResponse>("/internal/admin/overview", accessToken, signal));
}

export async function getUserDetail(userId: string, accessToken: string, signal?: AbortSignal): Promise<AdminUserDetail> {
  return normalizeUserDetail(
    await requestJson<AdminUserDetailResponse>(
      `/internal/admin/users/${encodeURIComponent(userId)}`,
      accessToken,
      signal
    )
  );
}

type AdminOverviewResponse = {
  generated_at: string;
  metrics: {
    today_users: number;
    new_users_today: number;
    realtime_users: number;
    active_users_24h: number;
    food_analyses_today: number;
    meals_saved_today: number;
    workouts_completed_today: number;
  };
  funnel: Array<{
    event_name: string;
    label: string;
    users: number;
    conversion_from_previous: number;
    dropoff_from_previous: number;
  }>;
  recent_activity: AdminActivityResponse[];
  users: AdminUserResponse[];
  payments: {
    gross_revenue_krw: number;
    active_subscriptions: number;
    failed_count: number;
    recent_payments: AdminPaymentResponse[];
  };
  ai_operations: {
    started_today: number;
    completed_today: number;
    failed_today: number;
    success_rate: number;
  };
};

type AdminUserDetailResponse = {
  user: AdminUserResponse;
  recent_activity: AdminActivityResponse[];
  payments: AdminPaymentResponse[];
};

type AdminActivityResponse = {
  event_id: string;
  user_id?: string | null;
  display_name?: string | null;
  event_name: string;
  occurred_at: string;
  screen: string;
};

type AdminUserResponse = {
  user_id: string;
  email?: string | null;
  display_name?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  online: boolean;
  analysis_count: number;
  meal_save_count: number;
  workout_count: number;
  plan: string;
};

type AdminPaymentResponse = {
  payment_id: string;
  user_id?: string | null;
  provider: string;
  product_id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
};

function normalizeOverview(response: AdminOverviewResponse): AdminOverview {
  return {
    generated_at: response.generated_at,
    metrics: {
      today_users: response.metrics.today_users,
      new_users: response.metrics.new_users_today,
      active_5m: response.metrics.realtime_users,
      active_24h: response.metrics.active_users_24h,
      food_analyses: response.metrics.food_analyses_today,
      meal_saves: response.metrics.meals_saved_today,
      workouts: response.metrics.workouts_completed_today
    },
    funnel: response.funnel.map(normalizeFunnel),
    recent_activity: response.recent_activity.map(normalizeActivity),
    users: response.users.map(normalizeUser),
    payments: {
      total_revenue_cents: response.payments.gross_revenue_krw * 100,
      mrr_cents: 0,
      active_subscriptions: response.payments.active_subscriptions,
      failed_payments: response.payments.failed_count,
      payments: response.payments.recent_payments.map(normalizePayment)
    },
    ai_operations: [normalizeAiOperations(response.ai_operations)]
  };
}

function normalizeUserDetail(response: AdminUserDetailResponse): AdminUserDetail {
  return {
    user: normalizeUser(response.user),
    timeline: response.recent_activity.map(normalizeTimeline),
    payments: response.payments.map(normalizePayment),
    ai_operations: []
  };
}

function normalizeFunnel(item: AdminOverviewResponse["funnel"][number]): AdminFunnelStep {
  return {
    step: item.label,
    users: item.users,
    conversion_rate: item.conversion_from_previous,
    dropoff_rate: item.dropoff_from_previous
  };
}

function normalizeActivity(item: AdminActivityResponse): AdminActivity {
  return {
    id: item.event_id,
    user_id: item.user_id ?? "",
    user_email: item.display_name ?? null,
    event_type: item.event_name,
    occurred_at: item.occurred_at,
    summary: `${eventLabel(item.event_name)} · ${item.screen}`,
    status: item.event_name.endsWith("_failed") ? "error" : "success"
  };
}

function normalizeTimeline(item: AdminActivityResponse): AdminTimelineEvent {
  return {
    id: item.event_id,
    event_type: item.event_name,
    occurred_at: item.occurred_at,
    summary: `${eventLabel(item.event_name)} · ${item.screen}`
  };
}

function normalizeUser(item: AdminUserResponse): AdminUserSummary {
  return {
    user_id: item.user_id,
    email: item.email ?? "",
    display_name: item.display_name,
    created_at: item.first_seen_at,
    last_seen_at: item.last_seen_at,
    subscription_status: item.online ? `${item.plan} · online` : item.plan,
    analyses_count: item.analysis_count,
    meal_saves_count: item.meal_save_count,
    workouts_count: item.workout_count
  };
}

function normalizePayment(item: AdminPaymentResponse): AdminPayment {
  return {
    id: item.payment_id,
    user_id: item.user_id ?? "",
    provider: item.provider,
    status: item.status,
    plan_name: item.product_id,
    amount_cents: item.currency === "KRW" ? item.amount * 100 : item.amount,
    currency: item.currency,
    occurred_at: item.created_at
  };
}

function normalizeAiOperations(item: AdminOverviewResponse["ai_operations"]): AdminAiOperationSummary {
  const attempts = item.completed_today + item.failed_today;
  return {
    provider: "food-analysis",
    model: "server aggregate",
    requests_24h: Math.max(item.started_today, attempts),
    error_rate: attempts ? item.failed_today / attempts : 0,
    p95_latency_ms: null,
    estimated_cost_cents: null
  };
}

function eventLabel(eventName: string): string {
  const labels: Record<string, string> = {
    app_opened: "App opened",
    login_completed: "Login completed",
    onboarding_completed: "Onboarding completed",
    meal_photo_selected: "Meal photo selected",
    analysis_started: "Analysis started",
    analysis_completed: "Analysis completed",
    analysis_failed: "Analysis failed",
    meal_saved: "Meal saved",
    workout_completed: "Workout completed",
    checkout_started: "Checkout started"
  };
  return labels[eventName] ?? eventName.replaceAll("_", " ");
}
