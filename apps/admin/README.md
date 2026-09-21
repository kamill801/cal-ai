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

Unauthorized or forbidden responses force a session-safe admin state and show an access message. The UI avoids displaying raw image URLs, tokens, keys, or secret-like metadata values.

User `First seen` is the first authenticated product event stored by Cal AI. Exact Supabase account creation timestamps require a later trusted Auth event sync.

Reads time out after 20 seconds and are cancelled on user selection or session changes. A 401/403 hides previously loaded data. Metrics refresh every 30 seconds; recent-five-minute activity is heartbeat-based rather than a live socket count. The smoke command uses local fixtures only and does not prove real owner login.
