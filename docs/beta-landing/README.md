# Trust First Nutrition beta landing

## Scope and reference

Standalone Korean introduction and Android beta application flow, built from the
current Kongbi assets and product capabilities. Reference implementation inspected:
`/Users/dd/Documents/ChatGPT/ai-agents/apps/web/src/LandingPage.tsx`, its site-surface
routing, intake contract and repository. Reused the journey, not the other product's
claims, screenshots, Google Group, email provider, credentials or policies.

Flow: introduction -> feature tabs -> installation explanation -> FAQ -> unchecked
participation/collection consent -> persisted application -> APK build page.
No automatic email, payment, Expo account creation, Play opt-in, app account creation,
health-photo collection, analytics SDK or marketing consent occurs here.

## Routes and compatibility

- `/` and `/beta`: standalone landing by default.
- `WEB_APP_ENABLED=false` (default): `/app`, `/app/*`, `/index.html` and
  `/auth/callback` redirect to `/`; the landing does not link to the web app.
- `WEB_APP_ENABLED=true` restores the original Expo shell at `/`, `/app` and its
  OAuth callback. `/beta` continues to show the landing.
- `/?action=delete-account`: redirects to the public deletion instructions while
  web is hidden; when restored, redirects to `/app?action=delete-account`.
- Existing privacy, terms, support, deletion, `/v1`, uploads and internal routes remain.
- `/beta-assets/*`: first-party Kongbi and meal assets, CSS and JavaScript.
- `GET /recruitment/config`: public intake state; no DB access or install URL.
- `POST /recruitment/applications`: anonymous same-origin, JSON-only application.

Request:

```json
{
  "email": "tester@example.invalid",
  "platform": "android",
  "adult_confirmed": true,
  "privacy_consent": true,
  "policy_version": "2026-11-18.1",
  "website": ""
}
```

Success is HTTP 202 with `accepted: true`, `delivery: "on_page"`, a server-validated
`install_url` and `app_version: "0.1.2"`. The UI only displays an install link after
this receipt. Repeated email submissions receive the same response without
extending the original consent or expiry while intake capacity permits. At capacity,
existing and unknown addresses receive the same rejection. Email ownership is not verified.

## Data and safeguards

Separate `beta_recruitment_applications` and aggregate `beta_recruitment_admission`
tables use the existing SQLite/Postgres selection. No app user or health tables are
modified. Stored: normalized email (aliases preserved), affirmative adult/privacy
consent, version, ID, creation and expiry times. Android is fixed by this endpoint.
No names, bodies, photos, passwords, raw IP or user agents are stored by this feature.
Hosting/network providers may independently retain operational logs.

Limits: 4096-byte request body, strict fields, same-origin validation, honeypot,
database-serialized 100 submissions/hour and 1000 active unique applications.
Origin checks/honeypots are abuse friction, not proof of humanity or email ownership.
Admission is global, so abusive traffic can temporarily exhaust the intake budget;
public-scale deployment may require an approved edge challenge/rate-limit service.

No public applicant-list endpoint exists. Responses never echo email, DSN or secret.
Install links are public links restricted to this Expo account/project, not credentials.
No admin entry point was added to the landing.

## Activation and current release

Production intake was approved and opened on 2026-11-19. See
`RELEASE-2026-11-19.md` for deployment and live verification evidence. The source
defaults below stay closed so a new unconfigured environment cannot accept data.

All intake and beta-retention flags default OFF. Production/Vercel intake additionally
requires a PostgreSQL `DATABASE_URL`; an ephemeral SQLite fallback cannot accept it.
Before public opening, approve the
application notice (operator Arche / public contact, 30-day policy), confirm current
APK and existing Neon, and verify the existing authenticated Vercel schedule.

```dotenv
BETA_RECRUITMENT_ENABLED=true
BETA_RECRUITMENT_RETENTION_ENABLED=true
BETA_RECRUITMENT_POLICY_APPROVED_VERSION=2026-11-18.1
BETA_RECRUITMENT_RETENTION_DAYS=30
BETA_RECRUITMENT_PUBLIC_ORIGIN=https://cal-ai-api.vercel.app
```

Production also has a server-only sensitive `CRON_SECRET`, generated and registered
with explicit user approval. Do not copy it into the mobile app, docs, chat or Git.
The existing daily schedule is enabled and linked to the landing release; its
authenticated handler returned 200. This does not prove a future scheduled run or
that 30 days have elapsed. Monitor successful runs and errors before assuming
expiry cleanup has completed. No general photo/account erasure flag was enabled.

`BETA_ANDROID_INSTALL_URL` defaults to the previously verified 0.1.2 Kongbi build.
It must be an HTTPS Expo build URL for the exact account/project, without query,
fragment or embedded credentials. No new API keys or paid providers are needed.
Changing retention requires a policy/UI version update, not just an env change.

Beta expiry cleanup is added to the **existing** authenticated
`/internal/cleanup-images` schedule, independently gated by
`BETA_RECRUITMENT_RETENTION_ENABLED`. It deletes expired beta applications only;
the original image/account flags and schedule are unchanged. POST also purges
expired beta records. Cleanup failure returns a sanitized 503 for monitoring.
30 days means expiry followed by the next successful cleanup, not simultaneous
erasure of provider logs/backups. Pause new intake without stopping retention by
setting only `BETA_RECRUITMENT_ENABLED=false`.

Never enable image/account erasure flags to activate beta-application retention.
Do not send real applicants to a preview with an ephemeral SQLite database.

## Build and local preview

```sh
EXPO_PUBLIC_API_BASE_URL=/ npm --workspace apps/mobile run export:web:vercel
```

The export script preserves the original Expo export in `apps/mobile/dist-web-preview`
and copies its shell into the private generated Python bundle directory
`services/api/app/web/preserved-app/index.html`. It publishes landing HTML as
`public/index.html` and keeps the Expo asset files for restoration. Vercel routes
web entries through the server flag **before** filesystem matching; unknown paths
do not fall through to the Expo shell. This is a reversible public-surface switch,
not an authentication boundary: non-secret frontend assets remain public.

### Restore or roll back

Set the non-secret `WEB_APP_ENABLED=true` on the existing `cal-ai-api` Production
environment and redeploy this commit to restore the web app. Set it back to `false`
and redeploy to return to landing-only. No source deletion or migration is needed;
native API routes and the separate admin project are unaffected.

Pre-landing production rollback candidate: `dpl_FiWHNS52GA2M9eaF4pryLEoa34W3`
(`cal-ai-c6c1sxq25-upglow.vercel.app`). Verify the current alias before any rollback.

For a local-only fixture, set a temporary `CAL_AI_API_DATA_PATH`, unset `DATABASE_URL`,
set the intake gates above and use `BETA_RECRUITMENT_PUBLIC_ORIGIN=http://localhost:8024`.
Then run `PYTHONPATH=services/api python -m uvicorn preview:app --app-dir apps/landing
--host 127.0.0.1 --port 8024`. Do not use real addresses in fixtures.

Tests:

```sh
python -m pytest services/api/tests/test_recruitment.py services/api/tests/test_landing_pages.py
node --test apps/landing/scripts/landing.test.mjs
node apps/landing/scripts/browser-qa.mjs
```

Browser QA uses local synthetic addresses only; set `PLAYWRIGHT_MODULE` to an
already installed Playwright module when it is not locally available. It uses the
installed Chrome by default, adds no dependencies, and never writes production.

## Release gates

- Local fixture evidence is not real Neon or production signup proof.
- Existing authenticated app and Android behavior are unchanged, not newly certified.
- Body-photo AI remains explicitly described as not operational real-photo analysis.
- Public promotion, 30-day collection notice/intake and safe cron-secret registration
  were explicitly approved. Any future email provider connection remains a separate
  gate. No mail was sent during implementation or release.

Deployment configuration reference checked against Vercel's official
[vercel.json function configuration](https://vercel.com/docs/project-configuration/vercel-json#functions).
Cron authentication and promotion behavior were checked against
[Vercel's cron management documentation](https://vercel.com/docs/schedules/cron-jobs/manage-cron-jobs).
