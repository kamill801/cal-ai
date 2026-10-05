# Equipment guide verification (2026-10-05)

Branch: `codex/equipment-photo-guide`. No main merge or production deployment.

## Local evidence

- Shared and mobile TypeScript checks: pass.
- API suite: 232 passed, one pre-existing Starlette TestClient deprecation warning.
- Equipment-specific cases: 36 passed. Ownership, unsupported MIME, disabled/retention activation gates, unknown/malformed model output, CAS completion race, atomic SQLite budget/concurrency, duplicate result receipt, cleanup failure, PUT replay tombstone, authenticated discard, safe YouTube output and negative caching are covered. Additional regressions prove budget continuity after profile deletion, owner-scrubbed replay cleanup after profile deletion, cancel/claim competition, committed-result recovery after acknowledgment failure, and monotonic terminal receipts.
- Mobile smoke: pass, including direct PUT without app Authorization, fixed upload filename, completed upload reference, cancellation before provider invocation with discard, URL allowlist and local/deployed API origin rules.
- Expo Web export: pass. No dependencies added.
- `git diff --check`: pass.
- Independent bounded review: clear after six local/synthetic checks of the final concurrency, deletion, acknowledgment and pruning fixes. No live provider activation was approved by this review.

## Browser evidence

Playwright with a fresh installed-Chrome profile tested a local static export and isolated SQLite/mock FastAPI. Authentication was disabled only in the local QA export. No real credentials, external image transmission or paid AI call was used.

Verified:

- Onboarding → personalized workout plan → mark an exercise → open equipment guide.
- Catalog search → selection → YouTube search guide → return to workout; the selected exercise remains checked.
- 390px, 320px and 1280px viewports; no horizontal document overflow at 320px.
- Consent disables photo selection before acceptance.
- Synthetic one-pixel image fixture and mocked equipment-only upload/identification requests → confirmation → manual correction → guide.
- No uncaught browser JavaScript errors in the tested flow.

Screenshots: `/private/tmp/cal-ai-equipment-qa/`. Browser script: `/private/tmp/cal-ai-equipment-qa.mjs`. These are local verification artifacts, not evidence of real recognition quality.

## Not Yet Proven

- Live OpenAI recognition accuracy or real YouTube API results/quota.
- Authenticated Preview end-to-end, Supabase Preview redirect allowlist and real R2 browser CORS.
- PostgreSQL concurrency against a live database. PostgreSQL CAS/advisory-lock implementation is present; concurrency tests used SQLite.
- Android/iPhone camera permissions, file URIs, back navigation and video app handoff on physical devices.
- Automatic cleanup executor or R2 lifecycle for a Preview environment. Photo AI remains disabled and `EQUIPMENT_RETENTION_VERIFIED=false` until this is verified.

Before activation, follow the checklist in `docs/EQUIPMENT-PHOTO-GUIDE.md`. Server secrets and paid provider activation are separate approval gates. Existing production state is not used as local test evidence.

## Preview isolation

The manual Preview deployment uses deployment-only runtime overrides: empty `DATABASE_URL`, `/tmp/cal-ai-equipment-preview.db` for SQLite, local storage, mock food/body providers, disabled equipment AI, disabled admin/payment, and an empty YouTube API key. Supabase authentication stays enabled using the project's existing Preview configuration. No project-level or Production environment variables are modified. Preview data is intentionally temporary and is not a durable multi-instance database; do not use it for user data or photo-provider activation. This isolates feature review from Production Neon/R2 and paid APIs. Authenticated/device/live provider checks remain separate.
