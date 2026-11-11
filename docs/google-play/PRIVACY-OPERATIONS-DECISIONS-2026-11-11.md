# Privacy Operations And Required Decisions

Status: reviewed technical inventory and operating checklist, **not a final legal
policy, a declaration submission, or permission to activate deletion**.
Operator/contact already selected by the owner: 아르케 / areche.ai.kr@gmail.com.
No credential, personal case content, signed URL or authentication token belongs
in this document or in the public pages.

## Public Documents Updated

- `/privacy`: data/purpose inventory, optional photos and health inputs, actual
  provider paths, AI-input/output handling caveats, retention limitations,
  retained deletion state, rights and inappropriate-AI-result reporting.
- `/account-deletion`: prominent off-app email request without reinstalling,
  authenticated in-app flow, ownership checks, acceptance versus completion,
  exact data scope and retained minimal state.
- `/terms`: existing adult-only scope and current source age gate, without
  claiming verified age or legal approval.
- `/support`: existing contact and private reviewer-access instructions, with
  warnings against sending passwords, OTPs, tokens, keys or body photographs.

Privacy/deletion pages now read only two boolean capability settings and a
validated photo TTL. They label these as settings, not actual erasure proof or
approved retention periods. Public GET never authenticates, runs cleanup, writes
records or calls a provider. Existing policy version/date remain unchanged until
the owner approves final operating terms; body-consent version is independent.

## Retention Matrix To Finalize

The table distinguishes current implementation from decisions still required.
No proposed period below has been enabled or represented as a legal obligation.

| Data | Current implementation | Required operating decision/evidence |
| --- | --- | --- |
| Auth identity and account-linked app records | Durable until explicit supported deletion; no universal age-based purge | Confirm service-purpose duration, account-closure handling and any genuinely applicable legal exceptions |
| Meal/body image bytes | Per-upload `cleanup_after`, configured from `IMAGE_TTL_DAYS` on completion; positive default 30 days | Confirm final period; test actual R2 writes/expiry/cleanup with an approved isolated fixture; enable only after retry/backlog monitoring is ready |
| Upload metadata, nutrition/AI results and meal records | Photo cleanup does not imply metadata/result/meal deletion | Choose separate periods and purge behavior; avoid retaining original filenames unnecessarily |
| Product events and analytics account/session rows | Stored by the app; profile/account deletion has explicit removal paths; no general event TTL | Approve a purpose-limited event period and implement/test a matching purge before promising one |
| Deletion tombstone, work/manifest and sweep history | Account/key identifiers and status retained; no automatic expiry | Document access-block/retry justification, minimum fields, restricted access, end condition and disposal design; these are personal identifiers, not anonymous totals |
| Optional R2 zero-byte guards | Default-off create-once erasure design keeps an empty object/key permanently to prevent delayed uploads restoring photo bytes | Verify provider atomicity, namespace, CORS and absence of lifecycle removal. Do not apply an arbitrary blanket bucket-expiry rule that removes guards or revive deleted keys |
| Support email/case information | Mailbox processing is outside app storage cleanup | Owner confirms mailbox access, receipt, case owner, safe verification, response/escalation process and case retention/disposal |
| Provider logs and backups | App source cannot erase or attest all provider copies | Verify contracts/account settings, applicable exceptions and backup/restore controls; publish accurate provider-specific limits |

A photo TTL is not an automatic-deletion completion promise. A daily schedule
with three account visits is not three completed accounts or a response-time SLA.
Before acceptance, document expected request volume, worst-case object count,
failure/retry capacity, queue-age alerts and a justified processing target. Do not
invent a statutory deadline or promise an untested numeric completion time.

## Provider And Overseas-Transfer Worksheet

Use actual settings/contracts, not a brand name or `R2_REGION=auto`, to complete
each recipient. A selected project region is not proof that all logs, support,
subprocessors or AI handling stay in that country.

| Provider path in source | Data/purpose to verify | Still required before final policy |
| --- | --- | --- |
| Vercel | Web/API request handling, execution and operational diagnostics | Recipient legal entity/contact, processing/log countries, subprocessors, applicable terms and retention |
| Supabase / Kakao | Account IDs, optional profile/email, credentials/session handling | Exact project and scopes, recipient entities, regions beyond primary storage, processing roles and retention. Never publish reviewer credentials |
| Neon Postgres | Profiles, nutrition, workouts, body/consent metadata, analytics, deletion state | Actual region and runtime target, backup retention, recovery after deletion, legal entity/contact and applicable contract |
| Cloudflare R2 | Selected photos, random object keys and storage metadata | Bucket jurisdiction/location policy, legal entity/contact, replica/log handling and validated image/guard lifecycle |
| OpenAI (only when activated) | Food photo reference/type/note; body photo reference/view/previous-check-in boolean; analysis output | Account-level sharing/training/data controls, abuse-monitoring exceptions, recipients/countries/retention and available deletion controls |

For every actual overseas transfer record: legal ground, data items, destination
countries, timing and method, recipient legal name/contact, purpose, retention,
refusal method/effects and relevant outsourcing versus third-party classification.
The owner must approve the final facts/legal basis; a generic AI checkbox does
not establish all sensitive-data or transfer permissions.

The Supabase router's historical inventory identifies `nojddnajbrowtcvcjvxv` in
`laeseopkkxsbbhbgobjt`; a fresh read-only connector request on 2026-11-11 returned
`INVALID_ARGUMENT`, so this follow-up does **not** newly verify live Auth region,
account authority or administrative deletion permission. No user/key was read.
Prior Neon/R2 preparation evidence remains in the release checkpoint, not a
substitute for the missing Auth deletion evidence.

### AI Retention And Reporting

- Source sets Responses API `store=False`. This controls response application
  state, not all abuse-monitoring or safety-retention paths.
- OpenAI documents normally up-to-30-day abuse-monitoring retention with
  exceptions. Image safety flags can require manual-review retention even with
  special data controls. Do not claim Zero Data Retention approval, no training,
  no copies, or immediate provider erasure without verified account terms.
- Removing the R2 source does not erase a request already processed by OpenAI.
- The public support route accepts reports of inappropriate/wrong AI results;
  request time/screen/problem type, not resubmission of original body photos.
  Reporting is not automatic model-training opt-out or provider erasure.

## Rights-Request Operating Checklist

This is a proposed manual operating procedure, not an already-running ticket
system or an authorization for destructive action.

1. Owner verifies control of the published mailbox and receipt through an
   owner-approved test; no email has been sent by this task.
2. Record a minimal private case ID, received time, requested action and status;
   do not copy a full health history into Git, logs or a public admin view.
3. Acknowledge receipt without disclosing whether an arbitrary address owns an
   account. Email sender identity alone is insufficient ownership evidence.
4. When possible, direct the owner to the authenticated in-app confirmation.
   For login loss, choose a provider-supported secure recovery/verification path;
   never request passwords, OTPs, bearer tokens, API keys or body photos by email.
5. Verify exact subject/scope before authorizing deletion; keep support and
   reviewer/admin accounts out of disposable tests. Record exceptions and retained
   minimal items with justification, not a blanket claim of full erasure.
6. Track accepted, pending, failed/retry and completed separately. Read back
   Auth state, protected-route rejection, app rows and storage checkpoints before
   marking a case complete; do not use logout or HTTP 202 as completion proof.
7. Apply the owner-approved case retention/disposal and escalation procedure.

## Approved Disposable Verification Still Needed

Do not run this against existing users, the owner or the Play reviewer.

1. Confirm exact Cal AI account/org/project, DB, bucket/namespace, flags and
   administrative authorization without exporting secret values.
2. Establish a named disposable Auth identity and synthetic non-personal image
   fixture; record intended object keys privately, with no production-wide sweeps.
3. Obtain explicit authority for its fixture creation, permanent erasure and any
   isolated activation. No paid AI is needed. A shared production cleanup route
   is unsafe as an isolated test: it has no account selector and can process real
   expired uploads/jobs.
4. Verify conditional PUT accepts once and rejects overwrite, browser preflight,
   complete/ownership and namespace binding. Inject failure, retry and concurrent
   write cases only in an isolated namespace/environment.
5. Verify acceptance blocks existing access tokens on protected app routes;
   independently check Supabase hard deletion and failed refresh/relogin. Supabase
   identity deletion alone does not invalidate all already issued access JWTs.
6. Read back owned record removal and verified empty guards without exposing
   unrelated rows. Distinguish byte erasure from retained key/status/backup data.
7. Prove bounded cleanup/retry and actual scheduled executions on an approved
   fixture before enabling general acceptance. Check old ownerless/legacy uploads
   separately; never backfill current namespace as historical provenance.

Leave both deletion flags and `R2_WRITE_ONCE_UPLOADS_ENABLED` false, and leave
`CRON_SECRET` absent until the relevant activation/retention authority exists.
Adding that secret also enables ordinary expired-photo retention regardless of
the two deletion flags.

## Google Play Data Safety Draft Mapping

This maps implementation inventory to the form, not a submitted declaration.

| Inventory | Candidate form category/purpose for owner review |
| --- | --- |
| Account IDs, optional email/display name | Personal info; account management/security and any actual analytics use |
| Weight, goals, recovery, nutrition and workout records | Health and fitness; app functionality/personalization and actual analytics |
| Selected food/body photos | Photos and videos; requested analysis/check-in functionality |
| User notes and other free text | Relevant user-generated content/health categories according to actual contents |
| Screen/action/heartbeat events and diagnostics | App activity/app info and performance as actually collected, with account linkage disclosed |

Off-device provider processing still counts as collection; `store=False` is not
proof of ephemeral processing. A service-provider sharing exception depends on
actual on-behalf processing and terms, not merely calling an API. Confirm each
field's purposes, optionality, sharing and retention, and compare the release
binary, public policy, prominent consent and Console answers before submission.

## Current Official References

Checked 2026-11-11. These sources inform the checklist, not this app's legal or
Google approval. No third-party summary is treated as a legal determination.

- [Google account deletion](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en): off-app request route, retained-data disclosure and prompt deletion expectations.
- [Google Data safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en): collection, ephemeral processing and service-provider classifications.
- [Supabase user deletion](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users) and [sessions](https://supabase.com/docs/guides/auth/sessions): identity deletion versus already issued tokens; paid session controls are not assumed enabled.
- [Supabase changelog](https://supabase.com/changelog.md): checked before provider work; no SDK or CLI upgrade was made.
- [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data#data-retention-controls-for-abuse-monitoring) and [image inputs](https://developers.openai.com/api/docs/guides/your-data#image-and-file-inputs): separate retention paths and safety exceptions.
- [Cloudflare R2 CORS](https://developers.cloudflare.com/r2/buckets/cors/) and [consistency](https://developers.cloudflare.com/r2/reference/consistency/): allowed request metadata versus conditional-write runtime proof.
- [PIPC 2026 policy-guide announcement](https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&nttId=12021): AI-related disclosure guidance; the full PDF was not reviewed in this task.
- [PIPC overseas-transfer explanation](https://pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS292&mCode=I040010000&nttId=10972): verify actual transfer facts and applicable legal basis.
