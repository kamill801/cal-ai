# Hosted Lifecycle Fixture Preparation

Status: **prepared, not erased**. This is the separately approved named
`cal-ai-lifecycle-20261111` workflow, not an eighth whole-service QA pass.
The historical full-app run remains 7/7 blocked. Android testing stays with
the owner; no Play declaration or submission is authorized by this result.

## Authority And Identity

- Owner approved preparation of a disposable Auth identity and synthetic
  non-personal image in the existing Cal AI infrastructure. Permanent erasure
  still requires exact-target confirmation immediately before the action.
- Supabase dashboard reverified the existing `cal-ai` project
  `nojddnajbrowtcvcjvxv`, organization `laeseopkkxsbbhbgobjt`, Free plan and
  Seoul region. The owner created the named disposable user and entered its
  test password themselves. Creation was read back at 19:12:02 KST.
- The Supabase connector lists other projects, not Cal AI, and was not used
  for account mutation. No unrelated project was selected.
- Existing Neon project `cal-ai` / `young-star-29502860`, organization
  `org-still-star-83110814`, `free_v3`, production branch
  `br-shy-credit-ahx1w07b` / `main` was freshly described. The initial metadata
  query was denied because its account identity differed from Supabase.
  After the owner explicitly approved this exact Neon target, only the exact
  new fixture row was selected. No credentials or unrelated records were read.

Exact disposable identity, object key and result hash are in private local
evidence, not this public repository. Existing owner, administrator, reviewer
and historical upload records were not used as fixtures or changed.

## Real Upload Evidence

An upload-only local browser tool used the existing public Supabase client key
and a password entered by the owner. It pinned both Auth UUID and email before
allowing any API mutation. Passwords, access/refresh tokens and signed upload
URLs were not written to logs, evidence or Git. No privileged key was read.

The production upload/database path was verified with these operations:

1. `POST /image-uploads/presign`: HTTP 200, one fixture reservation.
2. Direct browser PUT to the exact existing private R2 account/bucket/key:
   HTTP 200, one generated PNG, **351 bytes**, no personal photo.
3. `POST /image-uploads/complete`: HTTP 200 and `ready`; the existing server
   performed its R2 HEAD type/size verification and metadata update.
4. A separately approved Neon SELECT constrained by exact owner, upload ID
   and fixture label returned precisely the expected row.

Neon readback: `image/png`, 351 bytes, provider `r2`, status `ready`, owner
and fixture label match, namespace matches the SHA-256 of the exact known
endpoint/account/bucket tuple. Created at `2026-11-11T10:21:55+00:00`,
upload URL expiry `10:36:55+00:00`, cleanup scheduled metadata
`2026-11-18T10:21:57+00:00`. The seven days start at completion, not reservation.
This proves the configured expiry value is persisted, **not actual expiry
execution or automatic photo erasure**.

The browser origin was `http://localhost:8081`, matching existing R2 CORS.
An initial local tool address used `127.0.0.1`; it was corrected before the
fixture operation without widening production CORS. The browser completed
one upload, not both addresses. No production service code or environment
setting was changed by this preparation.

## Local Tool Safety Checks

- Five guard tests passed: exact identity, exact R2 destination/key, expected
  headers/TTL/size, rejection of secret/signed-URL evidence fields and owner
  binding. Client syntax check passed.
- Five local HTTP checks passed: public config, page/CSP, module serving,
  foreign-origin rejection and absence of an analysis endpoint. These checks
  did not perform authentication or production writes.
- The local server bound loopback only, accepted only the expected Host and
  Origin, used no external scripts, kept sessions in memory and recorded only
  sanitized metadata. An exclusive claim file prevented duplicate issuance
  across reloads. There were no automated production retries.
- The temporary tool process was stopped after the result was captured.
  Tool source and public client configuration were not added to the app or Git.

## Explicit Remaining Gates

- The resulting object is **not sealed-v1**, consistent with the previously
  verified production write-once setting being off. This is ordinary upload
  evidence, not a conditional-PUT/overwrite-race/empty-guard deletion test.
- Do not enable production-wide deletion, write-once uploads or scheduled
  cleanup merely to test this fixture. No flag or `CRON_SECRET` was changed.
- A narrowly isolated fixture-only runtime and sealed synthetic fixture need
  a concrete activation boundary before testing the erasure protocol. Confirm
  exact objects and disposable Auth subject immediately before permanent
  erasure; do not treat preparation approval as erasure approval.
- No account-deletion request, tombstone, worker sweep, storage delete,
  Supabase hard delete, paid AI call or automatic retention run occurred.
- Category-specific retention/overseas-transfer decisions, support-mailbox
  receipt/handling, final owner policy approval and actual Android results
  remain separate release gates.

Private evidence:

- `/private/tmp/cal-ai-lifecycle-harness-20261111/evidence.json`
- `/private/tmp/cal-ai-lifecycle-account-created-20261111.jpg`
- `/private/tmp/cal-ai-lifecycle-upload-completed-20261111.jpg`
- `/private/tmp/cal-ai-lifecycle-neon-readback-20261111.json`

These files contain no test password, bearer/refresh token, server key or
presigned URL. Screenshots and fixture identifiers are not final legal or
whole-app release approval.
