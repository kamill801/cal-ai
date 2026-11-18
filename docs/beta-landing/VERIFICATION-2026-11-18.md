# Local beta landing verification - 2026-11-18

Branch: `codex/beta-landing-20261118`, based on released Kongbi commit `0c633c5`.
The dirty original main worktree was preserved. User requested commit/push and
production landing replacement on 2026-11-18. Local verification below precedes
release; no cloud schema change, real applicant collection, email sending or paid
AI invocation occurred during these checks.

## Fresh checks

- API suite: 738 passed, 47 skipped, 1 existing TestClient deprecation warning.
- Landing JavaScript/unit build tests: 5 passed.
- Shared and mobile TypeScript checks: passed.
- Mobile smoke: 39 tests passed, async/API harness passed.
- Expo web export + landing asset preparation: passed, existing Expo SPA preserved.
- `git diff --check`: passed.
- Chrome: 1440x1000, 390x844, 320x740, 1920x1080; assets render and no horizontal overflow.
- Hero leaves next-section content visible in all four checked viewports.
- Keyboard tabs, unchecked required consent, persisted receipt, failure/retry,
  default-closed intake, double-submit lock, unsafe install receipt and stale policy passed.
- Independent SQLite readback: 1 unique synthetic address after repeated submissions;
  0 non-fixture addresses. Only `example.invalid` was used.
- Hidden web entries `/app`, `/app/*`, `/index.html`, `/auth/callback` redirect to
  landing by default. GET/HEAD, query-token non-reflection and cache controls passed.
- `WEB_APP_ENABLED=true` restoration serves the preserved Expo shell at root and
  old entries; `/beta` stays landing. Missing shell fails closed with sanitized 503.
- Original Expo export is unchanged; generated private shell and public landing
  are separately verified by the build test. Deletion instructions retain the
  app-independent email path while web is hidden.
- Beta expiry: authenticated scheduled-handler fixture purged expired beta rows,
  preserved an unrelated user-record table and did not activate photo/account erasure.
- Failure regressions: image cleanup failure cannot starve beta cleanup; beta failure
  does not prevent image cleanup. Errors are sanitized.

## Independent review

Found and repaired membership disclosure at capacity, rollback of rejected-request
quota, and photo-cleanup failure starving beta retention. Added production Postgres
requirement and fixed the policy to 30 days. Final bounded read-only review found no
remaining blockers in this change scope.

## Limits

This is local/fixture evidence, not live Neon persistence, real production cron,
authenticated OAuth, Android installation or Google Play approval evidence.
PostgreSQL adapter checks use mocks. The 47 skipped tests are not counted as passing.
Public intake remains OFF by default pending collection-notice approval and
production retention/authenticated-schedule verification.
Email automation is intentionally absent: the install URL appears on the receipt page.

Local screenshots are in `/private/tmp/cal-ai-beta-landing-qa-20261118/`.
Local preview: `http://localhost:8024`.
