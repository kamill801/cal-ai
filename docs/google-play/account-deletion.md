# Account Deletion Backend Contract

Current schema-v4 operating contract, source-audited 2026-11-17 at `948c09a`.
This supersedes this file's old schema-v3, no-inventory acceptance and
cron-secret-alone retention instructions. Local implementation/test evidence
is not provider-erasure or production activation approval. See
`DATA-SAFETY-2026-11-17.md` for the current policy/declaration matrix.
Operator: 아르케. Support: areche.ai.kr@gmail.com, independent of the Supabase admin account.

## HTTP Contract

`DELETE /v1/account` requires a verified user JWT and JSON `{"confirm":true}`.
The subject comes only from middleware identity. Extra target/body fields,
query parameters, missing confirmation, and non-boolean confirmation are rejected.

- `202 {"status":"pending"}`, `Retry-After: 30`: durable tombstone accepted
  after atomic inventory preflight; source metadata remains until bounded worker
  batches capture manifests before removal. This means accepted, not completed.
- `200 {"status":"deleted"}`: terminal checkpoint is durable. Authenticated
  completed retries do not require deletion configuration or provider calls.
- Before acceptance, configuration/persistence failure returns sanitized `503`,
  never `pending`. Offline/ambiguous transport errors do not prove acceptance.
- Missing/invalid JWT returns `401`; invalid request shape returns `422`.

Only confirmed acceptance authorizes pending/locked UI state. The worker can
delete the Auth identity before storage completion: UI must still say pending.
Expired JWTs cannot call the user retry endpoint, but do not stop worker retries.
There is no unauthenticated user deletion/status bypass.

`account_deletion_gate` runs after verified authentication, before route or
analytics writes. Tombstoned subjects cannot use other protected routes (`403`,
`account_deletion_in_progress`). Exact authenticated `DELETE /v1/account` is the
retry exception. Gate persistence failure returns `503 account_state_unavailable`.

## Flags-Off Staging

Keep the following server settings explicit on the staged deployment:

```text
ACCOUNT_DELETION_ENABLED=false
ACCOUNT_DELETION_WORKER_ENABLED=false
R2_WRITE_ONCE_UPLOADS_ENABLED=false
IMAGE_RETENTION_ENABLED=false
```

The canonical public privacy page read on November 17 reports all four switches
off and a seven-day new-upload expiry interval. This is not proof of automatic
erasure, nor an approved legal retention period. No cron credentials were added
or read in this audit. Production-only credentials do not establish availability
in Preview. Never copy credentials into documents, client variables or logs.

No concrete deletion-source blocker was identified for a flags-off staged
deploy. New deletion acceptance rejects before tombstoning, and the worker is
disabled. This does not disable existing tombstone access blocks or make the
whole app read-only. Schema-v4 guard installation is not a prerequisite merely
for deploying with these flags off. Repository initialization still performs
additive DDL, including namespace columns, so verify the exact Neon
database/schema and runtime role's existing initialization privileges.

Leader can deploy the auth-CORS repair and verify ordinary reviewer login
without enabling deletion. Deployed login, deletion activation and Play
submission remain separate gates. `/ready` or a successful build is not proof
of migration installation, scheduler progress or real provider erasure.

## Explicit Schema-v4 Migration

Before accepting any deletion, initialize the normal coach, analytics and
persistence schemas, then call `prepare_account_deletion()` explicitly. HTTP
acceptance and worker resumption do not install guards. A missing or outdated
schema marker fails closed with `account_deletion_schema_unavailable`.

For later authorized execution only, in a privately configured environment
targeting the independently verified database/schema and intended runtime role:

```bash
cd /private/tmp/cal-ai-kongbi-20261116/services/api
/private/tmp/cal-ai-release-venv-20261110/bin/python -B - <<'PY'
import os
from app.services.coach_repository import get_coach_repository
from app.services.analytics_repository import get_analytics_repository
from app.services.persistence import (
    PostgresPersistenceRepository, get_persistence_repository,
)

assert os.environ.get("DATABASE_URL")
for flag in ("ACCOUNT_DELETION_ENABLED", "ACCOUNT_DELETION_WORKER_ENABLED",
             "R2_WRITE_ONCE_UPLOADS_ENABLED", "IMAGE_RETENTION_ENABLED"):
    assert os.environ.get(flag, "false").strip().lower() == "false"
get_coach_repository()
get_analytics_repository()
repo = get_persistence_repository()
assert isinstance(repo, PostgresPersistenceRepository)
repo.prepare_account_deletion()
with repo._connection() as conn:
    repo._require_account_schema(conn)
print("deletion_guard_schema=4")
PY
```

This command writes schema; it was not executed by the documentation update.
The interpreter is the existing local verification environment, not a deployed
runtime requirement. Do not supply a production URL in shell history or silently
fall back to SQLite. Verify the same role can initialize/use the protected worker
tables; success as a different privileged role alone is insufficient.

The migration uses a PostgreSQL advisory transaction lock, installs guards and
indexes, then commits marker version 4, including privacy-consent cleanup. Its statement/lock timeout is 10 seconds,
not a hard whole-migration deadline. Guard-installation table locks belong to
this explicit step; coordinate installation with traffic and verify the marker
after commit. A failure must not be bypassed by manually advancing the marker.

Guard installation changes ordinary writes/deletes even while flags remain
false. In particular, non-worker deletion of ownerless remote upload metadata
is blocked to prevent uninventoried key loss. Review legacy data before
installation; do not disable guards or discard metadata to force progress.

## Worker And Cron Contract

`GET /internal/cleanup-images` first authenticates exact Bearer `CRON_SECRET`.
When the worker flag is enabled, account work runs **before** retention: up to
three account visits, five objects per visited account, and at most 25 seconds
of cooperative account budget, reserving 20 seconds for retention within the
shared 45-second deadline. It does not admit account work with less than 20
seconds of account budget. Retention inventory is limited to 100 rows and
skips tombstoned uploads. Failures do not silently become successful cleanup.

**Photo retention additionally requires `IMAGE_RETENTION_ENABLED=true` on this
revision.** A cron secret alone no longer enables sweeping. The previous warning
still applies to older deployments without that independent gate. Do not invoke
cleanup or expose scheduler credentials until the exact deployed source and
retention/storage changes are authorized. A cron credential can authorize other
enabled work; it is not a harmless readiness probe.

The checked-in Vercel cron targets this route at `0 18 * * *` (daily, UTC).
At most three account visits per scheduled run is not three guaranteed completed
accounts or a deletion-time SLA. Verify actual deployed execution, retry/backlog
monitoring and a suitable cadence/capacity before accepting real jobs.

The separately wired `GET|POST /internal/account-deletions/run` requires exact
Bearer `CRON_SECRET`, not a user JWT, rejects query parameters, and has no owner
selector. Defaults are one account, five objects and a cooperative 45-second
budget. Results contain aggregate `processed/deleted/pending/failed` counts.
The route does not schedule itself and is not a harmless readiness probe.

Before enabling both account flags, also verify `AUTH_PROVIDER=supabase`, the
same project's `SUPABASE_URL` used for JWT verification, and a server-only
administrative key. `CRON_SECRET` must contain at least 32 non-whitespace
characters, with no surrounding whitespace to avoid route-auth mismatch.
Legacy `SUPABASE_SERVICE_ROLE_KEY` is a fallback and must declare JWT
`role=service_role`. Opaque `sb_secret_` keys are sent only in `apikey`; legacy
service-role JWTs also use `Authorization: Bearer`. Removing configuration
leaves accepted jobs gated and pending; it does not roll back their tombstones.

## Durability, Isolation, And Limits

`account_deletions` retains the owner tombstone/stage/timestamps permanently.
`account_deletion_work` retains identity and storage-uncertainty markers plus
a five-minute lease nonce/expiry. The nonce is not an authentication token.
`account_deletion_objects` retains owner/upload IDs, original provider/key and
storage namespace, sweep count/time and `erase_verified`. These identifiers are
retained deletion state, not anonymous counters. No user JWT, refresh token,
email or admin secret is persisted in these tables. Temporary reference rows
are pruned during cleanup; successfully swept local manifest entries are removed.

Acceptance drains same-owner writers through an owner-state row, enumerates and
validates the current erasure inventory in the same transaction, and only then
commits the deleting flag and tombstone/work record. Inventory failure rolls
back acceptance before identity deletion. It performs no guard DDL. Stage 0
uses durable phases/keyset cursors, including consent, and batches of at most 100 rows,
without account-sized `IN` lists. Upload keys/namespaces are captured in the
manifest in the same transaction before their source rows are deleted. Inventory
failure or a conflicting manifest rolls back that batch's source removal, not
the already accepted tombstone. Stage 1 attempts server-admin identity deletion
without a client JWT.
Stage 2 can mean storage remains pending. Its separate identity marker defaults
false for legacy stage-2 rows, so previously revoked sessions are not confused
with identity deletion. Stage 3 requires app/identity cleanup and storage
completion: local cleanup, or verified erasure for every remote manifest object,
with no unknown-key uncertainty. A remote checkpoint requires the adapter's
namespace to match the original nonempty manifest namespace. Unknown or changed
namespaces remain fail closed; never backfill them from current configuration
without independent historical provenance.
Only exact 404 plus `user_not_found` is idempotent admin deletion success.

The worker calls optional `erase_account_object(object_key=...)`, falling back
to `delete_object` without verified remote completion. A crash between erasure
and its fenced checkpoint may repeat the idempotent external operation. Lower
sweep counts are selected first; verified remote entries need no further sweep.

Worker SQL mutations lock the current lease row and require its token and
database-clock expiry in the same transaction. Expiry is revalidated before
commit, rolling back a stale batch/checkpoint. Claims are atomic; old tokens
cannot release replacement leases. External HTTP effects are not exactly-once
or atomic with SQL. Bounded batches use statement/lock timeouts and cooperative
checks; provider calls and the whole invocation have no hard wall-time guarantee.

Initial work is prioritized. Reconciliation without unswept objects receives a
one-hour retry delay; work last updated at least 24 hours ago ages into the
initial-priority tier. Queue timestamps rotate and abandoned leases expire after
five minutes. Fairness does not establish adequate daily scheduler throughput.

Profile A deletion now uses profile-scoped SQL, not the owner-wide account
selector. Same-owner B and foreign C jobs/logs/clarifications/body uploads and
unlinked owner uploads survive. Foreign explicit ownership wins; uploads used
by retained jobs or other body events survive, subject to the explicit legacy
metadata guard above.
Account-wide artifact selection now applies the same retained-reference guard:
owned or legacy ownerless uploads used by foreign retained jobs/body events are
not deletion authority. Local SQLite regressions cover isolation, batch rollback,
namespace binding, fencing, late writes and cron interaction. The leader reported
six passing isolated PostgreSQL 16 tests, including owner-writer drain with
foreign-writer progress and lease-expiry rollback. This is disposable local
database evidence, not deployed Neon-role or real provider-erasure proof.
Fresh focused regression results for this audit are recorded separately in
`DATA-SAFETY-2026-11-17.md`; historical suite counts above are not new runs.

## Storage And Owner Gates

- **Conditional upload barrier:** `R2_WRITE_ONCE_UPLOADS_ENABLED` is default-off.
  New server-generated `uploads/{image-upload-UUID}/sealed-v1/image.ext` keys use
  signed `If-None-Match: *`. The implemented erasure hook overwrites photo bytes
  with a permanent zero-byte guard and verifies its size/content type. It returns
  true only after verification; namespace matching and a durable
  `erase_verified=1` checkpoint gate remote completion. Guards/random keys remain:
  do not describe this as absence of every object or erasure of every copy.
- **Real R2 verification:** before enabling write-once uploads, prove conditional
  signing, actual browser CORS allowing `If-None-Match`, concurrent/in-flight PUT
  behavior, signed guard PUT and readback in the original account/bucket. Verify
  that no bucket lifecycle rule or other writer removes guards. Existing delete
  paths preserve sealed-key guards in code; actual bucket configuration and
  provider behavior require current scope-specific verification. Prior November
  13/14 owner-approved synthetic erasure/replay/scheduled-retention reports
  supersede the historical blanket claim that no provider verification occurred.
  They were not rerun here and do not authorize general-user cleanup. Negative HEAD, expiry and DELETE alone
  are not an authoritative drain barrier.
- **Legacy inventory:** unconditional legacy PUTs, missing keys and unknown
  namespaces remain pending/blocked. Enabling write-once for future uploads does
  not repair them. Owner must approve an authoritative legacy revocation/drain
  strategy; do not prune manifests or force completion to clear a backlog.
- **Disposable provider lifecycle:** independently verify the matching Supabase
  admin credential, hard deletion, refresh/session behavior, app access block,
  storage cleanup and recovery after interruption using only an authorized
  disposable account, never the owner's or reviewer's continuing identity.
- **Operational approval:** owner controls private secrets, exact provider
  targets, storage/CORS/lifecycle changes, retention activation, scheduler/SLA
  decisions and production flags. Agents can perform local source checks and
  prepare/run approved migration and disposable tests with authorized access;
  existing access alone is not permission for cloud mutations or activation.
- **Policy:** disclose retained tombstones, manifests and any permanent guards.
  Historical lost keys, backups, provider audit logs, billing retention and
  cancellation require separate review. This endpoint does not cancel paid
  subscriptions or erase backups; policy/terms acceptance remains the owner's gate.

No secrets, cloud erasure, permissions/terms acceptance, production deployment or
activation were performed by this documentation update. Keep all four flags off
until the applicable operational gates and approvals are independently closed.

## Expiry, Withdrawal And Request Handling

Presign records pending-upload expiry/cleanup metadata. Successful completion
resets `cleanup_after` from completion time using `IMAGE_TTL_DAYS`. Abandoned
pending uploads must satisfy both cleanup and signed-upload expiry requirements.
Expiry removes image content, not meal records, analysis, metadata, analytics or
provider logs. Existing records can have different expiry values.

Health/analytics withdrawal stops subsequent gated processing, not historical
row retention. Sign-out/uninstall also does not erase server records. There is
no general analytics auto-expiry. The latest owner consent/version/time is stored
on change; this is not an immutable full consent history.

The public `/account-deletion` page offers a managed email path without
reinstalling the app. Current disabled acceptance means an in-app attempt does
not accept a new request. Email intake is not proof of ownership or fulfillment.
Before launch, approve and staff the following procedure:

1. Receive only app name, desired action, sign-in method and reply contact.
   Never routinely request passwords, tokens, API keys, identity documents or
   body photos by email.
2. Verify app-account control through an authenticated session or agreed safe
   recovery process. Sender email alone is insufficient.
3. Distinguish whole-account versus current-profile scope and retained security
   state; profile deletion also removes account-wide analytics enrichment.
4. Use the separately approved operational erasure process; monitor pending and
   failed jobs and confirm storage/DB/Auth outcomes, not just logout or 202.
5. Reply with the actual outcome and remaining scope. Record minimal handling
   evidence under an approved support-case retention rule and staffed timeline.

Security necessity is not itself a final legal retention exception. Determine
minimum fields/access and a defensible end condition for tombstones/manifests
and guards. Do not invent a 30/90-day TTL that breaks replay/access protection.

## Official References

- [Google Play deletion requirements](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en)
- [Google Play Data safety definitions](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)
- [OpenAI API data controls](https://developers.openai.com/api/docs/guides/your-data)
- [Server-only deletion](https://supabase.com/docs/reference/python/auth-admin-deleteuser)
- [API-key types](https://supabase.com/docs/guides/getting-started/api-keys)
- [Auth implementation](https://github.com/supabase/auth/blob/master/internal/api/admin.go)
- [R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)
- [R2 conditional operations](https://developers.cloudflare.com/r2/api/s3/extensions/)
- [R2 consistency](https://developers.cloudflare.com/r2/reference/consistency/)
- [Supabase changelog](https://supabase.com/changelog)
