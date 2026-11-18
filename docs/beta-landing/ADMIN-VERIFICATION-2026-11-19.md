# Beta applicant admin verification

## Scope

Approved owner-only listing on the existing separate `cal-ai-admin` project.
Email, original application time in Asia/Seoul, and total retained active unique
applications are visible. No public admin link, new secret, permission, provider,
migration, export, email send, application mutation, or general erasure activation.

`GET /internal/admin/beta-applications?limit=50&offset=0` requires the existing
asymmetric admin JWT and owner allowlist. It returns `generated_at`, `total`,
`limit`, `offset`, and `applications` containing only `id`, `email`, `created_at`.
Count is independent of the current page and app user registration. Expired
applications are excluded, not purged by this read; 30-day retention is unchanged.

## Local evidence

- Full API suite: 757 passed, 47 skipped, one existing TestClient deprecation warning.
- New endpoint/repository coverage: 19 passed, including disabled/missing/non-owner
  auth, no consumer-auth fallback, absent intake table, newest-first/tie ordering,
  global total, duplicate email, expiry boundary without deletion, bounded page,
  minimal response, email-free audit, sanitized storage/audit failure, and bound SQL.
- Admin TypeScript check and production build passed.
- Admin API/request-gate fixture smoke: 28 checks passed.
- Chrome fixture browser smoke: 15 scenarios passed at 320, 390, 1440 widths.
  Checks include Asia/Seoul time, total vs row count, paging, 30-second/manual
  refresh, expired-last-page recovery, overview failure isolation, loading, empty,
  retry, all three data sources' 401/403, late success after denial, logout,
  signed-out and missing-auth-configuration states. All addresses are synthetic;
  fixture requests are intercepted and external requests blocked.
- Shared/mobile TypeScript checks passed; mobile 39 tests plus async/API harness passed.
- Landing unit tests: 5 passed; Expo web/landing export passed.
- Python compilation and git whitespace checks passed.
- Independent read-only review found no actionable issues.

PostgreSQL query tests use a mock connection. Fixture tests are not proof of real
owner login, real Neon reads, or production behavior. Production authentication
readback and deployment evidence must be recorded separately after release.

## Reproduction

```sh
cd apps/admin
npm ci --ignore-scripts --no-audit --no-fund
npm run typecheck
npm run smoke
npm run build
PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node scripts/beta-browser-smoke.mjs
```

Browser checks use an existing Playwright installation and Chrome; no new test
dependency or real authentication token is needed. Do not capture real applicant
emails in release artifacts, logs, or screenshots.

## Release target

User approved commit, push, and production release of these two existing projects:

- API: `cal-ai-api` / `prj_l6Bc70asN999j5aMlyUXpB9zxcCk`, `upglow`.
- Admin: `cal-ai-admin` / `prj_K8zM9z9cYfogrN9hyVIhBeHWj1Xe`, `upglow`.

Use staged production deployments, verify API's anonymous 401/no-store and admin
CORS, confirm existing landing/recruitment state, verify admin bundle/API target,
then promote API before admin. Previous admin deployment:
`dpl_CPxN1ryrYou4AdZK6dfevqDYK5mN`; previous API deployment:
`dpl_A6kymQU42Gj6c1u4Usf1t3AAg3B2`. No environment changes are required.

Original dirty main worktree is preserved; feature work is isolated on
`codex/beta-landing-20261118`.
