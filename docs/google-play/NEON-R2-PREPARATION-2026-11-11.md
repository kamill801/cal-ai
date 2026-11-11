# Approved Neon And R2 Preparation

Scope: owner approved deletion-protection schema and storage preparation only.
No account or photo deletion, cleanup activation, paid AI or public release.
The original whole-service QA remains7/7 and blocked.

## Neon Target And Preflight

- Existing project `cal-ai` / `young-star-29502860`, organization
  `org-still-star-83110814`, verified subscription `free_v3`.
- Existing production default branch `br-shy-credit-ahx1w07b` / `main`.
- Database `neondb`, schema `public`, PostgreSQL17, role `neondb_owner`.
- All application tables are owned by that role; sampled guarded-table runtime
  privileges pass. Observed database connections use the same role. No Vercel
  connection string was decrypted or exported, so this is not a private-DSN
  equality attestation.
- Initially no version marker, installed guards, tombstones or deletion jobs.
- Core counts:5 profiles,6 analysis jobs,6 meal logs,11 upload metadata rows.
  Job/upload, coach/profile, meal/job and clarification/job orphan counts are0.
- Ten R2 rows (5 pending,5 ready) are legacy: owner and storage namespace are
  NULL, no sealed-v1 keys. One local row is also ownerless. No keys, payloads,
  credentials or personal records were printed or backfilled.

## Branch Verification And Production Installation

A free-plan validation branch `verify-deletion-guard-20261111` /
`br-dawn-recipe-ahmdpq94` was cloned from the existing production branch.
Requesting a custom suspend interval was rejected before creation; the retry
used the account's existing defaults, not a plan upgrade. The validation branch
is retained for follow-up; no branch deletion or new project was performed.

The exact74 SQL statements emitted by the committed
`PostgresPersistenceRepository.prepare_account_deletion()` method were recorded
offline with psycopg SQL literal rendering. Constructors were bypassed only for
recording; no credentials, connections or user payloads were used. Existing
initializer tables/columns were already present. One target/state assertion was
added after the advisory lock, requiring the exact database/schema/role, absent
marker and no deletion jobs. Functions were passed as whole statements, not
split on their internal semicolons. A single MCP SQL transaction first installed
the migration in the validation branch, then the same transaction in production.

- Readback in both branches: marker3 and12 enabled SECURITY INVOKER guards.
- Statement and lock timeout10 seconds, advisory transaction lock retained;
  these are not a whole-migration wall-time guarantee.
- A nested rollback-only synthetic probe verified normal image metadata writes
  and rejection of a deleting subject in both branches. No probe rows persisted.
  This was SQL behavior, not Auth, R2, HTTP or account-deletion E2E.
- Production core counts remained5/6/6/11; tombstones and deletion jobs remain0.
- All six inspected worker tables have RLS enabled and no PUBLIC grants; all
  six deletion-worker indexes are valid. No public grants were added.
- Post-install canonical public API checks passed9/9. The agent's first local
  probe hit sandbox DNS restrictions; the authorized network retry succeeded.

## Compatibility Finding

An independent source review identified that profile deletion could erase R2
bytes before the guard rejected deletion of ownerless metadata. Flags-off does
not prevent that route. The targeted source repair now preflights the entire
image set's owner/provider/key/original namespace before any mark or external
deletion. Unsafe remote records return sanitized, nonretryable503
`profile_image_verification_required`; local fallback and scoped owned deletion
are preserved. Guards were not disabled and no provenance was backfilled.

The regressions failed14/17 before repair and passed17/17 afterward, including
an unsafe record appearing after a valid one with zero partial deletion.
Account-deletion tests passed100 with7 optional PostgreSQL skips; fresh full
API tests passed478 with7 skips and one existing TestClient warning.
These are local fixture results, not real storage/account erasure. Source
`b0ffe1a` was pushed and promoted as `dpl_9NBnWviGKae877hTLjm9thau3jmA`;
canonical alias and9 public probes passed. No production profile deletion was
used to test the repair. Exact release evidence is recorded separately in
`PRODUCTION-DEPLOYMENT-2026-11-11.md`.

## R2 Handoff And Remaining Gates

Existing private bucket: `cal-ai-meal-images`. Dashboard sign-in initially
required the owner. After owner login, the current page is the optional
two-factor-authentication setup interstitial, not new account creation.
The owner must personally configure authentication or choose Skip for now.
No security setting, token, bucket, CORS or lifecycle rule was changed.

After access: independently verify exact account/bucket, private access,
existing CORS and lifecycle settings before merging conditional-header support.
Do not broaden origins or install an expiry rule that removes permanent sealed
guards. Conditional PUT/concurrency/guard readback and disposable Auth erasure
remain unverified. Legacy namespace provenance remains unresolved.

Keep `ACCOUNT_DELETION_ENABLED`, `ACCOUNT_DELETION_WORKER_ENABLED` and
`R2_WRITE_ONCE_UPLOADS_ENABLED` false. Leave `CRON_SECRET` absent. Permanent
deletion requires a separately named disposable identity and action-time
confirmation; never use the continuing owner or reviewer account.

R2 Standard free allowance is10GB-month storage,1 million Class A operations
and10 million Class B operations monthly. Usage above allowances is billable;
the application byte soft limit is not an account-wide request-cost hard cap.
No paid plan, payment or new key was requested.

References verified2026-11-11:
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/r2/buckets/cors/
- https://github.com/neondatabase/website/blob/main/content/docs/connect/connection-pooling.md
