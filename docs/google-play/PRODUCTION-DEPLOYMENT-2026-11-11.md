# Limited Production Deployment: 2026-11-11

Result: approved deployment and bounded public smoke **PASS**. This is not
whole-service, Android, legal/privacy, deletion-lifecycle or Play release approval.

## Authority And Source

Owner explicitly approved deploying latest login/workout/18+ fixes and the
public privacy/terms/support/deletion guidance while preserving food AI.
Excluded: paid AI tests, account-deletion or cleanup activation, and Play review.

- Existing team/project: `upglow/cal-ai-api` /
  `prj_l6Bc70asN999j5aMlyUXpB9zxcCk`.
- Source: `/private/tmp/cal-ai-play-20261109`,
  `codex/android-play-readiness`, base `1edc99201622ac60c32e234128a82f0f4d2e59a8`.
  Dirty source snapshot, not committed or pushed. Original main remains untouched.
- Allowlisted source archive:110 files,10,695,357 bytes; no env/credential files,
  symlinks, Git history or build/test outputs. Targeted secret patterns were
  absent, not a general security guarantee.
- Locally verified source-manifest SHA-256:
  `50747684433b0d2ba20d14dad745530a1d162f0764ea003b02e4b96103a1145b`.
  This is local packaging provenance, not an externally attested source digest.

## Deployment And Promotion

Official cached Vercel CLI54.14.0 uploaded the archive to the existing project
with production environment and `--skip-domain`. The deployment was independently
matched and inspected after the operator wrapper could not extract its nested
JSON result; no duplicate deployment was requested.

- Deployment: `dpl_83W5jnu5m8XZMKfMfPRRWLAxw8UH`.
- Immutable candidate: `https://cal-ai-ntwvreb4r-upglow.vercel.app`.
- State/target:READY/production; region readbackiad1 (not changed).
- Previous canonical deployment: `dpl_Btcjp4G1XWKBcYERhoiXAWWrxKoF`.
- Candidate was checked in the existing authorized browser without weakening
  protection. Official Vercel promotion was then requested and a separate alias
  readback confirmed `cal-ai-api.vercel.app` points to the new deployment.
- Production origin: `https://cal-ai-api.vercel.app`.

Deployment overrides explicitly keep `ACCOUNT_DELETION_ENABLED=false`,
`ACCOUNT_DELETION_WORKER_ENABLED=false`, `R2_WRITE_ONCE_UPLOADS_ENABLED=false`.
No AI/DB/storage/auth credentials were pulled, decrypted, printed or replaced.
No `CRON_SECRET` was registered in the metadata-only inventory; no worker was run.

## Verification

Fresh local checks: API460 passed/1 optional-PG skip/1 existing deprecation
warning; mobile19 explicit regressions plus existing async/API harness passed;
shared/mobile TypeScript, store24 and `git diff --check` passed.

Public probe completed `2026-11-11T08:08:26.117Z`, nine of nine passed:

| Route | Observed |
| --- | --- |
| `/health` | 200 |
| `/ready` | 200/status ok; food openai, body mock, DB/R2/Supabase configured |
| `/privacy` | 200, actual privacy heading, technical-draft notice, public contact |
| `/terms` | 200, actual terms heading, technical-draft notice, public contact |
| `/support` | 200, actual support heading, technical-draft notice, public contact |
| `/account-deletion` | 200, actual deletion heading, technical-draft notice, public contact |
| `/v1/profiles/me` | 401/authentication_required |
| `/internal/admin/overview` | 401/admin_access_denied |
| `/internal/account-deletions/run` | 503/account_deletion_unavailable; disabled, no worker run |

All four public documents also returned no-store, nosniff, no-referrer and CSP
headers. Targeted secret-pattern checks of the responses found no matches;
this does not assert an exhaustive disclosure audit. Browser verification saw
the actual privacy document and normal Kakao/email login screen on the canonical
origin, without reading credentials, tokens, cookies or private reviewer forms.

Evidence:

- `/private/tmp/cal-ai-production-probe-20261111-public.json` (sanitized).
- `/private/tmp/cal-ai-production-privacy-live-20261111.png`.
- `/private/tmp/cal-ai-production-login-live-20261111.png`.

## Remaining Gates

No new authenticated login/save/reload test was performed after promotion.
No image upload, paid AI request, provider erasure, disposable account deletion,
explicit deletion migration or cleanup execution occurred. Readiness is only
configuration evidence. Ordinary startup may initialize additive schema; this
is not the explicit account-deletion migration or proof of its trigger fences.

Public documents remain technical drafts. Actual retention, legal/operator
details, health-data consent and external-processing arrangements need review.
Deletion activation requires separately authorized, disposable provider-lifecycle
verification and operational preparation, not the shared reviewer's deletion.

Signed artifacts have bounded static evidence, not Android runtime or Play
acceptance. No AAB upload, closed-test release or app review submission occurred.
The existing whole-service QA counter remains7/7 and blocked.

## Later committed-source promotion

This checkpoint supersedes the earlier dirty-source deployment above.

- Source commit `7068afe0af5e7047e700e748e503b7a7e977626b` was created and
  pushed to `codex/android-play-readiness`; remote `ls-remote` matched. No main
  merge or original-main change. The source correction explicitly preserves the
  existing seven CORS methods after a fresh library wildcard regression.
- Every file in the allowlisted110-file,10,695,412-byte archive was compared
  byte-for-byte with this commit before deployment. Manifest SHA-256:
  `8bac72af548a716c64a3314f632b798508498f3cc5429bd73f3b217b37c4ef35`.
  This is local provenance; deployment readback did not expose source metadata
  and is not independent source-SHA attestation.
- Deployment `dpl_6r4xPvRLAx4gibjpdhTWGTFo24L6`, immutable URL
  `https://cal-ai-1y3ifqvda-upglow.vercel.app`, matched the exact existing project,
  READY/production. Authorized browser verified readiness, public privacy HTML
  and disabled deletion worker before promotion. Separate alias readback after
  official promotion confirmed `cal-ai-api.vercel.app` points to this deployment.
- The same9 public GET probes passed at `2026-11-11T08:37:22.264Z` with food
  openai/body mock and all deletion flags still explicitly false. Additional
  canonical-origin preflight returned POST200 and QUERY400, exactly the seven
  allowed methods and no credential-allow header. No paid AI or data mutation.
- Fresh local API461 passed/7 optional-PG tests skipped/1 existing warning;
  mobile19 regressions plus async/API harness, shared/mobile types and store24
  passed. New independent bounded static review found no actionable P0/P1
  blockers. Provider lifecycle and Android device gates remain unverified.

Evidence: refreshed sanitized public probe JSON and
`/private/tmp/cal-ai-committed-production-privacy-20261111.png`.
Play AAB acceptance subsequently succeeded as a saved internal draft only; see
`PLAY-UPLOAD-2026-11-11.md`. Neither that upload nor this deployment closes
privacy approval, real erasure, tester participation or public-release gates.

## Subsequent Approved Schema Preparation

After explicit owner preparation approval, Neon schema3 was installed and
verified on the existing production database after cloned-branch testing.
Core records are unchanged; no tombstones or jobs were created and all runtime
deletion/write-once flags stay false. Fresh canonical public probes passed9/9.
An independently identified legacy-profile erasure-ordering compatibility issue
is repaired in source with full-set remote-image preflight before any mark or
external delete. The17 targeted regressions and full API478 pass locally
(7 optional PostgreSQL skips,1 existing warning). Production promotion of this
repair is recorded below when verified. See
`NEON-R2-PREPARATION-2026-11-11.md`; schema installation is not deletion E2E.
