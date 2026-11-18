# Cal AI Admin

Standalone Vite React admin app for internal Cal AI operations. It is intended to deploy as its own Vercel project/domain and has no route or link from the main Cal AI app.

## Environment

Copy `.env.example` to `.env.local` and set:

- `VITE_API_BASE_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`

The publishable key is safe for browser use. Never put a Supabase service-role key in this app.

## Dedicated Owner Account

1. Create one email/password user manually in Supabase Auth. Enter a new password directly in the dashboard, never in chat, source code or environment variables. This app has no signup or password-reset UI.
2. Copy that user's UUID into the API-only `ADMIN_USER_IDS` environment variable.
3. Enable the API with `ADMIN_DASHBOARD_ENABLED=true` and configure `ADMIN_SUPABASE_URL` plus `ADMIN_SUPABASE_JWT_ALGORITHM`.
4. Set API-only `ADMIN_FRONTEND_ORIGIN` to the deployed admin origin. This extends the existing `CORS_ALLOWED_ORIGINS` list without replacing it.
5. Set API-only `ADMIN_LOGIN_USERNAME` to your chosen login ID, `ADMIN_LOGIN_EMAIL` to the created account's email, and `ADMIN_SUPABASE_PUBLISHABLE_KEY` to that project's publishable key. Never prefix these with `VITE_` or `EXPO_PUBLIC_`.

The login form accepts the chosen ID and password. `POST /internal/admin/login` maps the ID to the email on the server, asks Supabase to verify the password, and verifies the returned JWT and owner allowlist before returning session tokens. Neither password nor tokens are persisted by this endpoint. Responses are non-cacheable and provider errors are redacted. A database-backed global owner budget permits 10 attempts per 15-minute fixed window across API replicas. Unknown IDs are rejected without using that budget or contacting Supabase. An attacker who knows the ID can temporarily lock the owner out; the budget does not replace platform source-based throttling, provider rate limits or MFA. Database failures fail closed. Do not enable request/response body capture on this endpoint in monitoring.

The browser login is only the first gate. Every admin API request verifies the Supabase JWT and checks its subject against `ADMIN_USER_IDS`. A valid non-admin Supabase account receives `403`.

## Local Commands

```bash
npm install
npm run dev
npm run typecheck
npm run smoke
npm run build
```

## API Contract

After owner login and Supabase session initialization, requests include the Supabase `access_token` as:

```http
Authorization: Bearer <access_token>
```

The app calls:

- `GET /internal/admin/overview`
- `GET /internal/admin/users/{user_id}`
- `GET /internal/admin/beta-applications?limit=50&offset=0`

Unauthorized or forbidden responses force a session-safe admin state and show an access message. The UI avoids displaying raw image URLs, tokens, keys, or secret-like metadata values.

User `First seen` is the first authenticated product event stored by Cal AI. Exact Supabase account creation timestamps require a later trusted Auth event sync.

Reads time out after 20 seconds and are cancelled on user selection or session changes. A 401/403 hides previously loaded data. Metrics refresh every 30 seconds; recent-five-minute activity is heartbeat-based rather than a live socket count. The smoke command uses local fixtures only and does not prove real owner login.

## Beta Applications

The independent Korean beta section uses the same owner bearer token. It shows applicant email, full application time in `Asia/Seoul`, and the total of all unexpired retained unique emails, not a lifetime or current-page count. Rows follow the API's deterministic newest-first order. The read-only endpoint returns `{generated_at, total, limit, offset, applications: [{id, email, created_at}]}`; defaults are 50 rows and offset 0, with limits 1-100 and offsets 0-100000.

Previous/next controls change the page. Both 30-second and manual refreshes keep that page; if retention removes its last records, the UI loads the last remaining page (or page one when empty). Overview failures do not block the beta section. A 401/403 from any overview, user-detail or beta request clears protected data and aborts every outstanding read. Later responses cannot restore data within that session. Logout clears the data before waiting for sign-out. No email export, storage, logging, or applicant mutation was added.

Browser fixtures use an already installed Playwright module and Chrome, without starting a server or connecting authentication/providers:

```sh
PLAYWRIGHT_MODULE=/path/to/existing/playwright/index.mjs node scripts/beta-browser-smoke.mjs
```

The fixture bundles the real `App`/`AdminShell`, replaces only authentication and fetch with synthetic data, and checks 320/390/1440 layouts, Seoul time, total/page controls, manual and 30-second refresh, retention page recovery, loading/error/empty/signed-out states, and late responses after 401/403 or logout. Artifacts contain synthetic applicants only. Never capture production applicant emails in screenshots or logs. These checks do not prove real owner login or deployed API connectivity.
