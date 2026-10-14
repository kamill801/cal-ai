# Cal AI Vercel repairs and verification

Run: `cal-ai-vercel-2026-10-14`. User-requested new run after the previous
seven-pass run stopped. Native Codex, maximum seven passes; no OMX or Goal.

Preserve every feature/design and unrelated main changes. Use branch
`codex/equipment-photo-guide`; no main merge or production promotion. Fix
weekly windows and action-specific errors. Verify actual production entry
and repaired Vercel Preview, not a local browser substitute. Local unit/build
regressions are not service E2E evidence. Paid calls budget 0; no credentials,
personal photos, real user data mutations or auth/provider changes.

| Pass | Phase | Scope | Evidence |
| --- | --- | --- | --- |
| 1 | Complete | Weekly window, coach errors, current Vercel environment | Error mapping RED then 33 GREEN; mobile smoke 47 numeric cases and typecheck pass. Weekly regression RED then seven focused tests GREEN; integration review found server-date/KST mismatch and created-at vs performed/captured date semantics requiring another pass. Production login screen and ready endpoint verified; authenticated flow pending user login |
| 2 | Complete | Explicit KST current-week clock and activity-date boundaries; retain partial score and reject misleading period evidence | Regression RED: 3 failed, 2 passed. Focused coach quality 11 and coach API 11 GREEN; full API suite 249 passed, one pre-existing warning. Review found legacy meal fallback parsing and one date-dependent test needing hardening |
| 3 | Complete | Preserve legacy meal-date fallback without raising before weekly validation; freeze partial-workout regression date | Legacy meal regression RED with ValueError, repaired. Full suite 249 passed / one concurrency-fixture failure after 95s; isolated concurrency 2 passed. Provider fixture's five-second release deadline can expire during loaded full-suite requests. Mobile smoke 33 action-error + 47 numeric cases, shared/mobile typechecks and diff check pass |
| 4 | Complete | Keep concurrency privacy assertions unchanged while increasing bounded test synchronization allowance; independent source review | Full API 250 passed, one existing warning, in 7.30s. No privacy assertion removed. Independent review confirmed date/error repairs and found partial workout saves incorrectly emit workout_completed analytics |
| 5 | Verify | Emit completed-workout analytics only from backend-confirmed completion; regression-test partial/complete event behavior; deploy repaired branch for Vercel verification | Partial event API regression RED (422), then final API 251 GREEN, one existing warning. Mobile smoke: four workout event cases, 33 action errors and 47 numeric cases; mobile/shared/admin typechecks and six admin fixture checks pass. Cloud verification pending |

Started: 5. Completed: 4. Limit: 7. Previous run remains closed at 7/7.

Authenticated deployed flows and real upload/paid analysis are unknown or
blocked until login/data/call authority is available. Earlier branch
commit/push/Preview authorization remains; no production release authorized.

## Actual service evidence before Preview deployment

- Production: `https://cal-ai-api.vercel.app`; deployment
  `dpl_Btcjp4G1XWKBcYERhoiXAWWrxKoF`, state READY, source main
  `1edc99201622ac60c32e234128a82f0f4d2e59a8`.
- Actual browser reaches the Kakao sign-in screen. No authenticated session
  exists in the test tab yet; user sign-in/terms acceptance is a handoff.
- Actual production `/ready`: database and R2 report ok, food AI configured
  as openai, body AI still mock, Supabase auth and dedicated admin allowlist
  report ok. These are configuration/readiness signals, not provider E2E.
- Actual unauthenticated `GET /v1/profiles/me`: 401, protection retained.
- Runtime-log connector output could not be parsed; no zero-error claim.
- No live records, private images or paid analyses were created.

## Preview testing boundary

Deployment-only overrides will retain the previous branch's isolated SQLite,
local storage, deterministic food/body providers, disabled equipment provider,
disabled billing/admin and empty YouTube key. Supabase authentication is kept.
No project-level or Production environment variable is changed. This cloud
Preview proves packaging/routing/UI compatibility, not real Neon/R2/OpenAI
flows. No main merge or production promotion is permitted by this run.

| Required flow | Deployed evidence | Remaining gate |
| --- | --- | --- |
| Entry and authentication protection | Production sign-in page and 401 verified | Kakao callback and authenticated owner session |
| Goals, Today, meal history and workout logging | Unit/integration regressions only so far | Authorized test account records in actual deployment |
| Weekly coaching and completion analytics | KST/date/partial regressions passed | Authenticated deployed activity and admin view |
| Food image to save | Production provider configuration ready | Private R2 upload and bounded paid food analysis approval |
| Body image, deletion and equipment photo | Existing contracts retained | Authenticated consent/photo lifecycle, provider/quality checks |
| Billing and separate admin | Six fixture checks and typecheck, protections unchanged | Real admin login; billing remains disabled |
| Mobile/desktop design and native permissions | Previous local screenshots only | Repaired cloud UI and actual device checks |
