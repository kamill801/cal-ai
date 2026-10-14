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
| 5 | Complete | Emit completed-workout analytics only from backend-confirmed completion; regression-test partial/complete event behavior; deploy repaired branch for Vercel verification | Partial event API regression RED (422), then API 251 GREEN, one existing warning. Mobile smoke: four workout event cases, 33 action errors and 47 numeric cases; mobile/shared/admin typechecks and six admin fixture checks pass. Commit/push cf1ab94; Vercel Preview dpl_4qaiFLj6xv5mnv3gWv7GNKaon1rt READY. Actual /ready 200 confirms local/mock isolation and Supabase auth; 390px entry has no horizontal overflow. 1280px browser screenshot found full-width login/CTA needing responsive containment |
| 6 | Complete | Constrain the existing login screen on PC while preserving mobile layout, colors, fonts and legal/auth gates; re-deploy and verify actual Vercel rendering | Actual 1280px screenshot reproduced a 1232px CTA; final cloud candidate has a centered 432px CTA. 320px has 272px CTA and no horizontal overflow; 390px retained. Commit/push 4823723; final Preview dpl_H9w42PnJrhe15iWubGQBC4oAPoiG READY; /health and /ready 200, profile 401, disabled admin 404. Required authenticated/provider/native rows remain blocked, not passed |

Started: 6. Completed: 6. Limit: 7. Previous run remains closed at 7/7.
Stop reason: safe source/Preview checks complete; actual authenticated flows
await user sign-in and test-record authority. One pass remains reserved for
future authorized continuation; no pass 7 has started and the count is not reset.

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
| Mobile/desktop design and native permissions | Final cloud entry verified at 320/390/1280; PC width repaired; existing tokens/fonts/copy retained | Authenticated screens and actual device checks |

First repaired Preview: `https://cal-ai-oo013459i-upglow.vercel.app`.
Cloud build READY, `/health` 200, `/ready` 200, protected profile endpoint 401.
The initial CLI curl attempt failed because this CLI forwarded the scope flag;
rerun using the already verified linked project succeeded. No endpoint pass was
claimed from the failed command. This Preview uploaded the clean worktree at
`cf1ab9467992b57e0b9ac0028aa0ef320e401ed2`; connector Git metadata was absent,
so provenance is the local commit/upload evidence, not an independent cloud
Git-SHA match.

Screenshots: `/private/tmp/cal-ai-vercel-preview-login-390.jpg` and
`/private/tmp/cal-ai-vercel-preview-login-1280.jpg`. Neither contains user data.

## Final candidate and current stop

Final Preview: `https://cal-ai-ao5blcc0g-upglow.vercel.app`.
Deployment: `dpl_H9w42PnJrhe15iWubGQBC4oAPoiG`, target Preview, READY.
Uploaded clean source: `48237230d2ffade849a6c8b535108c8d83a805d0`.
Code and earlier flow repairs are pushed on `codex/equipment-photo-guide`.
This subsequent evidence-only report update is not an application change and
does not alter the uploaded source identity.

- Final deployed `/health`: 200; `/ready`: 200.
- Final `/ready` confirms local storage, mock food/body, retained Supabase
  auth and disabled admin. Database check passes but its public generic label
  is not independent Neon proof. Deployment overrides explicitly use SQLite.
- Final unauthenticated `/v1/profiles/me`: 401. Disabled admin overview: 404.
- Actual browser: entry button width 432px at 1280, 272px at 320. Document
  widths equal viewport widths, with no sampled horizontal overflow. Saved
  320/390/1280 screenshots. Temporary viewport override reset.
- Production alias was checked after Preview deployment: still points to
  `dpl_Btcjp4G1XWKBcYERhoiXAWWrxKoF`; no promotion/main merge occurred.
- Production browser still exposes its sign-in button, not an authenticated
  app session. No real account/test records or paid calls were created.
- Current API regressions: 251 pass, one pre-existing TestClient warning;
  mobile smoke (4 workout analytics, 33 error mapping, 47 numeric cases),
  shared/mobile/admin typechecks and six admin fixture checks pass. The API
  and analytics code are unchanged by the final login-only layout commit.
- Scoped secret-pattern and staged-path checks found no matches; environment
  files, DB files and build output were not staged. No key values were read
  from dashboards or printed. This is a scoped check, not an absolute guarantee.

Final screenshots (local evidence, not published):
`/private/tmp/cal-ai-vercel-final-login-320.jpg`,
`/private/tmp/cal-ai-vercel-final-login-390.jpg`,
`/private/tmp/cal-ai-vercel-final-login-1280.jpg`.

**HOLD for public/production release.** Required authenticated UI flows,
Kakao callback, real Postgres/R2 upload lifecycle, bounded paid AI/semantic
quality, admin login and native device paths are not proven by these checks.
The current task-specific fixes and cloud candidate are ready for the next
authorized test stage, not a declaration of a bug-free complete product.

User next action: sign into `https://cal-ai-api.vercel.app` with a test-only
account, completing credentials and legal consent directly, and confirm
whether QA-only goal/meal/workout/weight records may be created. Real personal
photos and paid provider calls still require separate bounded authority.
