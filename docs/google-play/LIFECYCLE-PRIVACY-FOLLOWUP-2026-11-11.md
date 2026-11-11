# Deletion, Retention And Privacy Follow-up

## Scope And Authority

Owner requested targeted lifecycle verification and privacy-document completion
while personally handling Android testing. This is a new explicitly requested
work package, not a reset or an eighth pass of the capped whole-service QA run.
That historical result remains 7/7 blocked. Android and Play submission are not
part of this work package's success claim.

Starting release branch: `codex/android-play-readiness`, commit `d3464c1`.
Original dirty main and the separate equipment feature remain untouched.

Allowed: isolated fixture/real-local-PostgreSQL checks, read-only provider
configuration/preflight checks, source-grounded document repairs and existing
authorized release actions on this branch. No paid AI, credential extraction,
new provider, real user/photo deletion, feature activation or final legal
attestation. A named disposable provider lifecycle requires separate authority.

## Required Evidence

| Claim | Required check | Current state |
| --- | --- | --- |
| Local deletion/retention contracts | Fresh related API tests, including isolation/failure/retry cases | Passed: 252 related tests before final copy refinements; final suite recorded below |
| Real SQL lifecycle | Fresh isolated PostgreSQL guards, ownership, fencing and cleanup tests | Passed: 7/7 on a private PostgreSQL 16.15 cluster; stopped and socket/process absence verified |
| R2 browser request permission | Actual read-only preflight from approved origin; no object write | Passed: 3/3 HTTP OPTIONS cases; not an actual browser PUT |
| Public policy accuracy | Tests distinguish configured capability from acceptance, execution and legal approval | Passed: regressions and independent review; final legal policy remains a separate owner gate |
| Real provider erasure | Named disposable Auth/storage target, separate destructive approval, readback | Blocked: not authorized |
| Operational retention | Approved category schedule, real TTL and authenticated scheduled execution | Blocked: activation/periods not approved |
| Final policy | Confirm operator/legal bases/recipients/locations/retention and owner review | Blocked: owner decisions/contracts |

No credential, signed URL, raw personal record or private provider response is
to be included in this report. Provider configuration is not runtime evidence.

## Fresh Evidence And Limits

- Related regression suite: 252 passed, one existing Starlette/httpx warning.
  SQLite and provider fixtures do not prove live erasure.
- Final API regression suite after all source/test changes: **489 passed,
  7 skipped, 1 existing warning in 58.57 seconds**. The seven PostgreSQL-only
  cases were intentionally skipped by the default run and separately passed on
  the isolated real engine below; do not describe them as hosted Neon tests.
- Independent read-only source review found no actionable new issue in the
  public rendering, safe config parsing, age-gate alignment or regression scope.
  Reviewer did not rerun tests or attest live deletion/mailbox/legal readiness.
- `git diff --check` passed. No package or dependency version changed.
- Optional PostgreSQL suite: 7 passed in 4.65 seconds on PostgreSQL 16.15,
  Unix socket permissions 0700, TCP disabled. The sidecar stopped its own cluster
  in `finally`; PID/socket/lock were absent. Neon uses a different hosted runtime,
  so this is real SQL behavior, not a fresh hosted deletion test.
- R2 preflight at `2026-11-11T09:30:23.597Z`: canonical production and
  localhost:8081 origins returned 204 with exact allowed origin, PUT and
  content-type/if-none-match headers. An unrelated example.invalid origin returned
  403 without allow-origin. No credential or signed URL was used; no object was
  read, created, changed or deleted.
- Transport history preserved: three Python HTTPS attempts failed with
  `URLError`; Node's standard TLS transport then succeeded once diagnostically
  and in the final three-case verification. No disabled TLS validation or
  settings change was used. Seven logical OPTIONS attempts total, zero mutations.
- A fresh exact-project Supabase metadata read returned `INVALID_ARGUMENT`.
  No alternative project was selected or user/credential data read. Hosted Auth
  erasure remains unverified; an old account inventory is not fresh verification.

Local private evidence (not committed; no personal/provider secrets):

- `/private/tmp/cal-ai-r2-preflight-20261111.json` (failed Python transport)
- `/private/tmp/cal-ai-r2-preflight-node-20261111.json` (3/3 final HTTP checks)
- `/private/tmp/cal-ai-pg16-account-deletion-z678i07x/report.json`
- `/private/tmp/cal-ai-pg16-account-deletion-z678i07x/pytest-results.xml`

## Narrow Change And Release Plan

The public pages now disclose current nonsecret deletion flags and validated
photo TTL without treating configuration as acceptance/runtime/legal proof. They
prominently offer off-app email requests, distinguish provider retention from
`store=False`, and align age wording with the existing stored-profile gate. No
mobile, deletion, provider, database or storage behavior is changed.

Operational decisions, verification steps and official references are in
`PRIVACY-OPERATIONS-DECISIONS-2026-11-11.md`. This completes the technical privacy
inventory, not the owner's final retention/transfer decisions or legal review.

Before commit: final API suite, focused independent source review, whitespace
and staged secret/unrelated-file checks. Existing authorized release branch and
scoped draft-policy production release only; no merge to main. Keep all three
flags false and `CRON_SECRET` absent. Verify source SHA/archive before release.

Reserved read-only deployed confirmations: maximum two, not additional repair
passes of the historical whole-service run. Check 1: exact staged production
candidate documents and authorization/configuration boundaries. Check 2: exact
canonical alias after promotion, policy content/security headers and reloaded
desktop/mobile rendering. No paid AI or destructive endpoint invocation.
