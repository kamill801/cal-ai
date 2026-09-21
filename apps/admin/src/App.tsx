import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import {
  Activity,
  AlertTriangle,
  Brain,
  ChevronRight,
  Clock3,
  CreditCard,
  LogOut,
  RefreshCw,
  Search,
  ShieldCheck,
  UserRound,
  UsersRound,
  Utensils,
  Dumbbell
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { AdminApiError, getOverview, getUserDetail, loginAdmin } from "./api";
import { supabase } from "./supabase";
import type {
  AdminActivity,
  AdminAiOperationSummary,
  AdminFunnelStep,
  AdminMetricKey,
  AdminOverview,
  AdminPayment,
  AdminTimelineEvent,
  AdminUserDetail,
  AdminUserSummary
} from "./types";

type LoadState = "idle" | "loading" | "refreshing" | "error";

const REFRESH_MS = 30_000;

const metricLabels: Record<AdminMetricKey, { label: string; icon: LucideIcon }> = {
  today_users: { label: "Today users", icon: UsersRound },
  new_users: { label: "오늘 첫 방문", icon: UserRound },
  active_5m: { label: "최근 5분 활동", icon: Activity },
  active_24h: { label: "24h active", icon: Clock3 },
  food_analyses: { label: "Food analyses", icon: Utensils },
  meal_saves: { label: "Meal saves", icon: ShieldCheck },
  workouts: { label: "Workouts", icon: Dumbbell }
};

const metricOrder = Object.keys(metricLabels) as AdminMetricKey[];

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    if (!supabase) {
      setAuthLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      if (mounted) {
        setSession(data.session);
        setAuthLoading(false);
      }
    }).catch(() => {
      if (mounted) setAuthLoading(false);
    });

    const {
      data: { subscription }
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setAuthLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  if (!supabase) {
    return <FullPageStatus label="관리자 로그인 설정이 아직 완료되지 않았어요." />;
  }

  if (authLoading) {
    return <FullPageStatus label="Checking admin session" />;
  }

  if (!session) {
    return <LoginView />;
  }

  return <AdminShell key={session.access_token} session={session} />;
}

function LoginView() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      if (!supabase) throw new Error("관리자 로그인 설정을 확인해 주세요.");
      const tokens = await loginAdmin(username, password);
      const { error: sessionError } = await supabase.auth.setSession(tokens);
      if (sessionError) throw new Error("로그인을 완료하지 못했어요. 다시 시도해 주세요.");
    } catch (requestError) {
      setError(requestError instanceof Error && requestError.name === "Error"
        ? requestError.message : "로그인을 완료하지 못했어요. 다시 시도해 주세요.");
    } finally {
      setPassword("");
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel" aria-labelledby="login-title">
        <div className="brand-mark" aria-hidden="true">
          <ShieldCheck size={24} />
        </div>
        <div>
          <p className="eyebrow">Internal operations</p>
          <h1 id="login-title">Cal AI Admin</h1>
          <p className="muted">관리자 전용 로그인</p>
        </div>

        <form className="login-form" onSubmit={onSubmit}>
          <label>
            <span>아이디</span>
            <input
              autoComplete="username"
              required
              type="text"
              value={username}
              onChange={(event) => setUsername(event.currentTarget.value)}
            />
          </label>
          <label>
            <span>비밀번호</span>
            <input
              autoComplete="current-password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.currentTarget.value)}
            />
          </label>
          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
          <button className="primary-button" disabled={submitting} type="submit">
            <ShieldCheck size={16} />
            {submitting ? "로그인 중" : "로그인"}
          </button>
        </form>
      </section>
    </main>
  );
}

function AdminShell({ session }: { session: Session }) {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [userDetail, setUserDetail] = useState<AdminUserDetail | null>(null);
  const [query, setQuery] = useState("");
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [accessIssue, setAccessIssue] = useState<string | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);

  const accessToken = session.access_token;

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    async function loadOverview() {
      if (pending) return;
      pending = true;
      setLoadState("refreshing");
      setError(null);
      try {
        const nextOverview = await getOverview(accessToken, controller.signal);
        if (controller.signal.aborted) return;
        setOverview(nextOverview);
        setAccessIssue(null);
      } catch (requestError) {
        if (controller.signal.aborted) return;
        if (requestError instanceof AdminApiError && [401, 403].includes(requestError.status)) {
          setOverview(null);
          setUserDetail(null);
          setSelectedUserId(null);
        }
        handleRequestError(requestError, setAccessIssue, setError);
      } finally {
        pending = false;
        if (!controller.signal.aborted) setLoadState("idle");
      }
    }
    void loadOverview();
    const interval = window.setInterval(() => void loadOverview(), REFRESH_MS);
    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [accessToken, refreshVersion]);

  useEffect(() => {
    setUserDetail(null);
    if (!selectedUserId || accessIssue) return;
    const userId = selectedUserId;
    const controller = new AbortController();
    let pending = false;
    async function loadUserDetail() {
      if (pending) return;
      pending = true;
      setError(null);
      try {
        const nextDetail = await getUserDetail(userId, accessToken, controller.signal);
        if (controller.signal.aborted) return;
        setUserDetail(nextDetail);
      } catch (requestError) {
        if (controller.signal.aborted) return;
        setUserDetail(null);
        if (requestError instanceof AdminApiError && [401, 403].includes(requestError.status)) {
          setOverview(null);
        }
        handleRequestError(requestError, setAccessIssue, setError);
      } finally {
        pending = false;
      }
    }
    void loadUserDetail();
    const interval = window.setInterval(() => void loadUserDetail(), REFRESH_MS);
    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [accessToken, selectedUserId, accessIssue, refreshVersion]);

  const selectUser = useCallback((userId: string) => {
    setSelectedUserId((currentUserId) => {
      if (currentUserId !== userId) {
        setUserDetail(null);
      }

      return userId;
    });
  }, []);

  const filteredUsers = useMemo(() => {
    const users = overview?.users ?? [];
    const normalizedQuery = query.trim().toLowerCase();

    if (!normalizedQuery) {
      return users;
    }

    return users.filter((user) => {
      return [user.email, user.display_name, user.user_id, user.subscription_status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(normalizedQuery));
    });
  }, [overview?.users, query]);

  const visibleDetail = userDetail?.user.user_id === selectedUserId ? userDetail : null;
  const selectedUser = visibleDetail?.user ?? overview?.users.find((user) => user.user_id === selectedUserId);

  return (
    <main className="admin-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Cal AI Admin</p>
          <h1>Operations cockpit</h1>
        </div>
        <div className="topbar-actions">
          <span className="session-email">{session.user.email}</span>
          <button
            className="icon-button"
            title="Refresh"
            type="button"
            onClick={() => setRefreshVersion((value) => value + 1)}
          >
            <RefreshCw size={16} className={loadState === "refreshing" ? "spin" : undefined} />
          </button>
          <button className="icon-button" title="Sign out" type="button" onClick={() => void supabase?.auth.signOut()}>
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {accessIssue ? <Banner tone="warning" message={accessIssue} /> : null}
      {error ? <Banner tone="error" message={error} /> : null}

      {loadState === "refreshing" && !overview && !accessIssue ? (
        <DashboardSkeleton />
      ) : overview ? (
        <div className="dashboard-grid">
          <section className="span-all metrics-strip" aria-label="Overview metrics">
            {metricOrder.map((key) => (
              <MetricTile key={key} metricKey={key} value={overview.metrics[key] ?? 0} />
            ))}
          </section>

          <section className="panel wide-panel" aria-labelledby="funnel-title">
            <SectionHeader id="funnel-title" title="Funnel and dropoff" meta={formatTimestamp(overview.generated_at)} />
            <FunnelTable rows={overview.funnel} />
          </section>

          <section className="panel" aria-labelledby="activity-title">
            <SectionHeader id="activity-title" title="최근 활동" meta="30초마다 갱신 · 최근 5분 활동 기준" />
            <ActivityList items={overview.recent_activity} onSelectUser={selectUser} />
          </section>

          <section className="panel wide-panel" aria-labelledby="users-title">
            <div className="section-heading with-search">
              <div>
                <h2 id="users-title">Users</h2>
                <p>{filteredUsers.length} shown</p>
              </div>
              <label className="search-box">
                <Search size={15} />
                <input
                  aria-label="Search users"
                  placeholder="Search users"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.currentTarget.value)}
                />
              </label>
            </div>
            <UsersTable users={filteredUsers} selectedUserId={selectedUserId} onSelectUser={selectUser} />
          </section>

          <section className="panel" aria-labelledby="payments-title">
            <SectionHeader id="payments-title" title="Payments" meta={money(overview.payments.total_revenue_cents, "KRW")} />
            <PaymentSummary summary={overview.payments} />
          </section>

          <section className="panel wide-panel" aria-labelledby="ai-title">
            <SectionHeader id="ai-title" title="AI operations" meta="Today" />
            <AiOpsTable operations={overview.ai_operations} />
          </section>

          <section className="panel" aria-labelledby="detail-title">
            <SectionHeader
              id="detail-title"
              title="User detail"
              meta={selectedUser ? shortId(selectedUser.user_id) : "Select a user"}
            />
            <UserDetailPanel detail={visibleDetail} fallbackUser={selectedUser} />
          </section>
        </div>
      ) : (
        <FullPageStatus label="No admin data returned" />
      )}
    </main>
  );
}

function handleRequestError(
  requestError: unknown,
  setAccessIssue: (value: string | null) => void,
  setError: (value: string | null) => void
) {
  if (requestError instanceof AdminApiError && (requestError.status === 401 || requestError.status === 403)) {
    setAccessIssue(requestError.message);
    return;
  }

  setError(requestError instanceof Error ? requestError.message : "Unexpected admin API error.");
}

function MetricTile({ metricKey, value }: { metricKey: AdminMetricKey; value: number }) {
  const metric = metricLabels[metricKey];
  const Icon = metric.icon;

  return (
    <div className="metric-tile">
      <div className="metric-label">
        <Icon size={15} />
        <span>{metric.label}</span>
      </div>
      <strong>{number(value)}</strong>
    </div>
  );
}

function SectionHeader({ id, title, meta }: { id: string; title: string; meta?: string }) {
  return (
    <div className="section-heading">
      <div>
        <h2 id={id}>{title}</h2>
        {meta ? <p>{meta}</p> : null}
      </div>
    </div>
  );
}

function FunnelTable({ rows }: { rows: AdminFunnelStep[] }) {
  if (rows.length === 0) {
    return <EmptyState label="No funnel events yet." />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Users</th>
            <th>Conversion</th>
            <th>Dropoff</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.step}>
              <td>{row.step}</td>
              <td>{number(row.users)}</td>
              <td>{percent(row.conversion_rate)}</td>
              <td>
                <span className={row.dropoff_rate > 0.35 ? "status danger" : "status"}>{percent(row.dropoff_rate)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ActivityList({
  items,
  onSelectUser
}: {
  items: AdminActivity[];
  onSelectUser: (userId: string) => void;
}) {
  if (items.length === 0) {
    return <EmptyState label="No recent activity." />;
  }

  return (
    <ol className="activity-list">
      {items.map((item) => (
        <li key={item.id}>
          <button type="button" disabled={!item.user_id} onClick={() => item.user_id && onSelectUser(item.user_id)}>
            <span className={`activity-dot ${statusClass(item.status)}`} />
            <span>
              <strong>{safeText(item.summary)}</strong>
              <small>
                {safeEmail(item.user_email)} · {formatTimestamp(item.occurred_at)}
              </small>
            </span>
            <ChevronRight size={14} />
          </button>
        </li>
      ))}
    </ol>
  );
}

function UsersTable({
  users,
  selectedUserId,
  onSelectUser
}: {
  users: AdminUserSummary[];
  selectedUserId: string | null;
  onSelectUser: (userId: string) => void;
}) {
  if (users.length === 0) {
    return <EmptyState label="No users match this search." />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>첫 앱 방문</th>
            <th>Last seen</th>
            <th>Status</th>
            <th>Activity</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr
              className={selectedUserId === user.user_id ? "selected-row" : undefined}
              key={user.user_id}
              onClick={() => onSelectUser(user.user_id)}
            >
              <td>
                <button className="table-link" type="button">
                  {safeText(user.display_name) || safeEmail(user.email)}
                  <small>{shortId(user.user_id)}</small>
                </button>
              </td>
              <td>{dateOnly(user.created_at)}</td>
              <td>{formatTimestamp(user.last_seen_at)}</td>
              <td>
                <span className="status">{user.subscription_status || "free"}</span>
              </td>
              <td>
                {number(user.analyses_count)} scans · {number(user.meal_saves_count)} meals · {number(user.workouts_count)} workouts
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PaymentSummary({ summary }: { summary: AdminOverview["payments"] }) {
  return (
    <div className="payment-stack">
      <dl className="summary-grid">
        <div>
          <dt>Revenue</dt>
          <dd>{money(summary.total_revenue_cents, "KRW")}</dd>
        </div>
        <div>
          <dt>Active subs</dt>
          <dd>{number(summary.active_subscriptions)}</dd>
        </div>
        <div>
          <dt>Failed</dt>
          <dd>{number(summary.failed_payments)}</dd>
        </div>
      </dl>
      <PaymentList payments={summary.payments} />
    </div>
  );
}

function PaymentList({ payments }: { payments: AdminPayment[] }) {
  if (payments.length === 0) {
    return <EmptyState label="No recent payments." />;
  }

  return (
    <ol className="compact-list">
      {payments.slice(0, 8).map((payment) => (
        <li key={payment.id}>
          <CreditCard size={15} />
          <span>
            <strong>{money(payment.amount_cents, payment.currency)}</strong>
            <small>
              {payment.status} · {safeEmail(payment.user_email)} · {formatTimestamp(payment.occurred_at)}
            </small>
          </span>
        </li>
      ))}
    </ol>
  );
}

function AiOpsTable({ operations }: { operations: AdminAiOperationSummary[] }) {
  if (operations.length === 0) {
    return <EmptyState label="No AI operations reported." />;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Model</th>
            <th>Requests</th>
            <th>Error rate</th>
            <th>P95</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          {operations.map((operation) => (
            <tr key={`${operation.provider}-${operation.model}`}>
              <td>{operation.provider}</td>
              <td>{operation.model}</td>
              <td>{number(operation.requests_24h)}</td>
              <td>
                <span className={operation.error_rate > 0.05 ? "status danger" : "status"}>
                  {percent(operation.error_rate)}
                </span>
              </td>
              <td>{operation.p95_latency_ms == null ? "Not tracked" : `${number(operation.p95_latency_ms)}ms`}</td>
              <td>{operation.estimated_cost_cents == null ? "Not tracked" : money(operation.estimated_cost_cents)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UserDetailPanel({
  detail,
  fallbackUser
}: {
  detail: AdminUserDetail | null;
  fallbackUser?: AdminUserSummary | null;
}) {
  const user = detail?.user ?? fallbackUser;

  if (!user) {
    return <EmptyState label="Pick a user to inspect timeline, payments, and AI operations." />;
  }

  return (
    <div className="detail-panel">
      <div className="identity-block">
        <UserRound size={17} />
        <span>
          <strong>{safeText(user.display_name) || safeEmail(user.email)}</strong>
          <small>{shortId(user.user_id)}</small>
        </span>
      </div>
      <dl className="summary-grid">
        <div>
          <dt>Scans</dt>
          <dd>{number(user.analyses_count)}</dd>
        </div>
        <div>
          <dt>Meals</dt>
          <dd>{number(user.meal_saves_count)}</dd>
        </div>
        <div>
          <dt>Workouts</dt>
          <dd>{number(user.workouts_count)}</dd>
        </div>
      </dl>
      {detail ? (
        <>
          <Timeline events={detail.timeline} />
          <PaymentList payments={detail.payments} />
          <AiOpsTable operations={detail.ai_operations} />
        </>
      ) : (
        <EmptyState label="Loading user detail." />
      )}
    </div>
  );
}

function Timeline({ events }: { events: AdminTimelineEvent[] }) {
  if (events.length === 0) {
    return <EmptyState label="No timeline events." />;
  }

  return (
    <ol className="timeline">
      {events.map((event) => (
        <li key={event.id}>
          <div>
            <strong>{safeText(event.summary)}</strong>
            <small>
              {event.event_type} · {formatTimestamp(event.occurred_at)}
            </small>
          </div>
          <MetadataPreview metadata={event.metadata} />
        </li>
      ))}
    </ol>
  );
}

function MetadataPreview({ metadata }: { metadata?: Record<string, unknown> | null }) {
  const safeEntries = Object.entries(metadata ?? {}).filter(([key, value]) => {
    const normalizedKey = key.toLowerCase();
    return (
      !normalizedKey.includes("url") &&
      !normalizedKey.includes("secret") &&
      !normalizedKey.includes("token") &&
      !normalizedKey.includes("key") &&
      typeof value !== "object" &&
      !looksLikeUrl(String(value))
    );
  });

  if (safeEntries.length === 0) {
    return null;
  }

  return (
    <dl className="metadata-list">
      {safeEntries.slice(0, 4).map(([key, value]) => (
        <div key={key}>
          <dt>{key}</dt>
          <dd>{safeText(String(value))}</dd>
        </div>
      ))}
    </dl>
  );
}

function Banner({ tone, message }: { tone: "warning" | "error"; message: string }) {
  return (
    <div className={`banner ${tone}`} role="alert">
      <AlertTriangle size={16} />
      <span>{message}</span>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="dashboard-grid" aria-label="Loading admin dashboard">
      <div className="span-all metrics-strip">
        {metricOrder.map((key) => (
          <div className="metric-tile skeleton" key={key} />
        ))}
      </div>
      <div className="panel wide-panel skeleton tall" />
      <div className="panel skeleton tall" />
      <div className="panel wide-panel skeleton tall" />
      <div className="panel skeleton tall" />
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <p className="empty-state">{label}</p>;
}

function FullPageStatus({ label }: { label: string }) {
  return (
    <main className="status-shell">
      <RefreshCw size={18} className="spin" />
      <span>{label}</span>
    </main>
  );
}

function statusClass(status?: string | null) {
  if (status === "error") {
    return "danger";
  }

  if (status === "warning") {
    return "warning";
  }

  return "";
}

function number(value: number | null | undefined) {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

function money(cents: number | null | undefined, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency
  }).format((cents ?? 0) / 100);
}

function percent(value: number | null | undefined) {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function dateOnly(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(date);
}

function shortId(value: string) {
  return value.length > 12 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value;
}

function safeEmail(value?: string | null) {
  return value || "Unknown user";
}

function safeText(value?: string | null) {
  if (!value) {
    return "";
  }

  return value
    .replace(/https?:\/\/\S+/gi, "[redacted-url]")
    .replace(/\b(?:sk|pk|sbp)_[A-Za-z0-9_-]{12,}\b/g, "[redacted-secret]")
    .replace(/\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\b/g, "[redacted-token]");
}

function looksLikeUrl(value: string) {
  return /^https?:\/\//i.test(value) || /\.(?:png|jpe?g|webp|gif|heic)(?:\?|$)/i.test(value);
}
