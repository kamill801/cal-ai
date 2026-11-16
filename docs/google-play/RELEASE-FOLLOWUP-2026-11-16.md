# Release Follow-up: 2026-11-16

Status: candidate implementation and saved registration drafts. Not a review
submission, Android runtime signoff, or legal/operating-policy approval.

## Live Readback

- Existing ARCHE Labs Personal developer `7707482448795132061`, existing app
  `4975788258134910868`, package `com.trustfirstnutrition.app`; no new app/account.
- Console setup is **9/11**. Privacy URL saved with success confirmation and
  independent reload readback: `https://cal-ai-api.vercel.app/privacy`.
- Internal testing is **1/3**, now updated to accepted AAB **2 (0.1.1)** in the
  existing saved draft, reloaded with the title `0.1.1 - Consent validation`.
  Code1 was removed only from this draft and remains in the artifact library.
  No distribution was performed. Closed-test
  participation is **0**. Console requires 12 opted-in testers continuously for
  14 days before applying for production access. Direct APK use does not count
  as closed-test opt-in.
- Remaining setup: Data safety and listing phone screenshots. The existing
  Data safety draft is still at step 2: collection=yes, encrypted transit=yes,
  OAuth creation selected, deletion URL blank. No final declaration was made.
- Korean description and 1024x500 feature graphic were saved November 15.
  At least two actual privacy-safe Android phone screenshots remain owner input.
  Generated designs and web captures must not substitute for device evidence.
- Production `dpl_HNfxviUm9pmDQ3Rjos7J3bbHEcBq` is now promoted and the
  canonical alias independently read back; it supersedes
  `dpl_8teiWGLvAmebMhG1ynNkjKzwNWts`. Exact source/build evidence is in
  `PRODUCTION-ANDROID-2026-11-16.md`.
  Public GET `/ready` reports configured R2, OpenAI food analysis, mock body
  analysis and Supabase auth. `/privacy` and `/account-deletion` return HTML.
  Public notices report account acceptance/worker off and new-upload TTL 7 days.
  These responses do not establish provider execution or actual erasure.
- No ordinary-user record/image changes or paid AI calls were made in this
  follow-up. Prior 7/7 whole-app QA and bounded synthetic repair budgets stay
  exhausted; narrow regression work is not an eighth whole-app pass.

## Candidate Changes

- Separate, server-owned, versioned health-data consent and optional analytics
  consent. Production/preview health features fail closed before accepted current
  consent. Optional analytics starts off and is not a core-feature requirement.
- Consent belongs to the authenticated owner, not a payload owner ID. Policy
  changes require re-consent. GET does not create event/session records.
- The event/heartbeat transaction rechecks consent; PostgreSQL row locking
  serializes a concurrent analytics opt-out. Analytics rejects goal, clarification
  answers and workout duration/intensity/frequency properties.
- Admin activity/funnel/user metrics are based on retained analytics records,
  not an authoritative Supabase account census. With optional analytics off,
  subsequent activity is not counted; existing historical rows are not erased
  merely by opting out. Do not advertise these counts as all real users/signups.
- Public technical notices describe consent, withdrawal and pending-upload
  expiry, while retaining explicit unknown operating facts. Consent withdrawal
  does not pretend to erase existing data.
- Independent default-off `IMAGE_RETENTION_ENABLED` plus cron authentication;
  pending-upload cleanup/quota and fair bounded retry handling.
- Atomic, owner-fenced deletion inventory/preflight and post-erasure DB scope
  checks. Unsupported legacy/provider/namespace data must fail closed before
  identity deletion or irreversible source loss.

The new code is now live on the canonical web/API origin, with deletion,
worker, retention and write-once flags explicitly off. The old Play draft
binary has no new consent UI and must not be described as compatible with the
new required server gate. New Android builds are tracked separately in
`PRODUCTION-ANDROID-2026-11-16.md`; no Play distribution is authorized here.

## Candidate Verification

Fresh, isolated checks on November 16:

- Full API suite: **652 passed**, one existing Starlette TestClient deprecation
  warning. `CAL_AI_TEST_PG_DSN` was restricted to a local Unix socket, with random
  disposable schemas dropped after tests; no Neon or real-user DB was used.
- PostgreSQL revocation-first regression observes `pg_blocking_pids` before
  releasing the owner lock; the waiting analytics event is rejected after the
  revocation commits. SQLite also reserves a write transaction before checking.
- Shared/mobile TypeScript checks passed. Mobile smoke: **39 passed**, plus
  async/API smoke. Store/icon/archive configuration checks: **24 passed**.
- Web and Android JavaScript/Hermes exports passed using explicit local/mock
  configuration and `EXPO_NO_DOTENV=1`. These are not signed APK/AAB artifacts,
  cloud builds, production configuration proof or Android runtime tests.
- Local browser fixture at 390px and 320px: unchecked controls, disabled continue
  before health selection, health-only acceptance without analytics, management
  access, withdrawal and return-to-gate passed. At 320px document width remained
  320px. The final shortened heading was re-exported and visually rechecked.
- Independent fixture DB readback after withdrawal: both consent flags false,
  zero analytics user/session/event rows, health/profile/upload tables not yet
  initialized. No actual health input or photo was supplied in this browser check.
- Review found consent/owner lock inversion, SQLite revocation serialization
  and local-cleanup blocking server deletion. All three received scoped repairs
  and regression coverage. A further profile-erasure/writer lock inversion was
  repaired with an owner fence, NOWAIT subordinate locks and a transaction-local
  250ms lock timeout covering final deletes. Contention must return retryable
  503 with the inventory retained, including after external erasure; only a
  committed finalizer reports completion. This is bounded-contention handling,
  not proof of globally acyclic locking or contention-free operation. Four forced
  local PostgreSQL schedules cover parent, analytics-owner, image-first and
  post-erasure child-row contention: 503 while blocked, successful fresh retry.

Browser fixture captures are **not store screenshots**:
`assets/local-consent-default-390-20261116.png` and
`assets/local-consent-revoked-320-20261116.png`.

The owner approved guarded production code promotion and two free-quota Android
builds on November 16. Preparation uses version 0.1.1/code 2 and the existing
app-specific remote signing identity. The exact existing Expo project was
reverified on Free ($0/month, upcoming estimate $0); current usage was 5 Android
builds, below its 15-build allowance. General deletion/retention activation,
new paid AI calls, Play distribution and submission are excluded. Deployment
and build completion must be recorded separately after actual readback.

Completion readback is now in `PRODUCTION-ANDROID-2026-11-16.md`: canonical
promotion verified, both builds FINISHED/downloaded, bounded signatures and
static native/manifest checks completed, new AAB accepted/saved/reloaded in the
existing inactive Play draft. This does not close runtime or policy gates.

## Safe Activation Runbook

1. Finish candidate regression tests, real isolated PostgreSQL checks, mobile
   smoke/typechecks, source review and exact artifact provenance.
2. Confirm operating facts below, finalize the policy text/version and compare
   the exact binary/backend with Data safety. Do not certify unsupported answers.
3. Obtain exact promotion/activation scope approval. Keep acceptance, worker,
   retention and write-once flags off during an ordinary code-only promotion.
4. **Do not add `CRON_SECRET` to the old production revision.** Its photo cleanup
   does not have the candidate's independent retention gate. Deploy/read back
   the guarded code first; a cron secret is not a harmless account-only change.
5. Enabling new write-once uploads changes future signed PUTs, not the safety of
   every legacy object. Confirm client headers, private namespace and migration
   coverage without enumerating or changing general-user data.
6. Verify a newly authorized disposable scope only. Existing synthetic budgets
   and old disposable objects are not authorization for further deletes.
7. Activate general acceptance/worker/retention only after explicit scope and
   operational ownership are approved. Verify scheduled auth, completion and
   independent DB/storage readback; pending/202/logout/zero rows is not completion.
8. Prepare new APK/AAB using the existing app-specific remote signing identity,
   never export private credentials. Re-run Android physical testing and capture
   genuine final screenshots before distributing the closed test.
9. Save the final declarations for owner verification. Do not accept legal
   attestations or submit/release merely to clear a dashboard checkbox.

## Owner Facts / Remaining Decisions

| Item | Needed fact or decision; no guessed value |
| --- | --- |
| Public identity/contact | Owner confirmed on November 16 that the responsible operator name on the business registration is `아르케` and that `areche.ai.kr@gmail.com` is directly managed and can receive privacy/deletion requests. No registration number or credentials collected. This confirms contact facts, not the unresolved processing/retention decisions below. |
| Category retention | Confirm periods and purpose for ordinary health/meal/workout records, usage analytics, support correspondence, and minimal deletion/replay-prevention state. New photo metadata currently uses 7 days; this is not an approved all-copy erasure deadline. Do not promise a retention period lacking enforcement. |
| External processing | Confirm actual processor entities, processing countries/regions, contracts, subprocessors, provider logs/backups and applicable overseas-transfer basis. Source configuration alone is insufficient. |
| Fulfillment | Assign who handles ownership checks, unavailable-login requests, retries, provider requests and completion notices. A contact link alone is not a working deletion service. |
| Personal health-app eligibility | Owner chose Personal closed testing and declined conversion. Current official health-app account wording has no verified existing-account exception for this app. Keep eligibility unresolved; do not change account type or hide health functionality. An unsent support question is below. |
| Android | Owner performs install/camera/gallery/login/upload/analysis/save/restore/workout/deletion-flow QA. Supply two or more genuine final-build screenshots without real sensitive records. |

### Unsent Play Support Question

> We operate Trust First Nutrition (`com.trustfirstnutrition.app`) under the
> existing ARCHE Labs Personal developer account. It provides food/nutrition,
> fitness/workout and weight/recovery logging, is 18+, and is not a medical device.
> We plan closed testing, not an account conversion. Does the current mandatory
> Organization wording for health apps apply to this existing Personal account
> and this app before closed testing? Please identify any applicable transition
> or account-specific requirements. No account-type change is authorized.

Not sent. Obtain approval before contacting Google on the owner's behalf.

## References And Evidence

- [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en)
- [Account deletion](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en)
- [Data safety](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en)
- [Personal-account testing](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en)
- [Play Console requirements](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en)
- `assets/console-privacy-url-saved-20261116.jpg`
- `assets/console-dashboard-20261116.jpg`
- `PRIVACY-RELEASE-REVIEW-2026-11-15.md` for the earlier official-source review.
- `SCHEDULED-RETENTION-AUTH-2026-11-14.md` and
  `LIFECYCLE-COMPLETION-2026-11-13.md` for bounded historical provider evidence.

The earlier review's missing feature graphic, missing privacy URL and cron-only
candidate behavior are superseded by this checkpoint. Historical provider tests
are not rerun here; their narrow scope and general activation limits remain.
