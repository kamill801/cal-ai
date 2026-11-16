# Cal AI Privacy And Play Release Review

Reviewed: 2026-11-15 (KST). Status: decision-ready technical draft, NOT release
clearance, legal advice, a submitted declaration, or acceptance of any terms.

## Decision In Brief

Continue preparing truthful drafts for the existing ARCHE Labs Personal account;
do not convert it or create another account. **Personal closed testing is the
owner's chosen route, not verified health-app account eligibility.** Current
Google policy does not establish an exception for this app. Closed testing does
not exempt health, privacy, Data safety, or account-deletion obligations.

The actual remaining gates are:

| Gate | Current evidence and next decision/action |
| --- | --- |
| Health-app account eligibility | Google requires an Organization account for health apps in its current account-type guidance; its taxonomy includes nutrition/fitness. No existing-personal-account exemption or app-specific clearance was verified. Obtain authoritative applicability clarification for this existing account/app before asserting eligibility. Respect the refusal to convert; do not hide health features or reclassify the app to evade the rule. |
| Usable account-and-data deletion | Source implements it, but ordinary acceptance/worker flags remain false. An unverified mailbox plus a disabled button is not an operational deletion service. Establish a working request/verification/fulfillment path and evidence of actual completion across the required scope before claiming support. A manual service can qualify; automation itself is not mandated. |
| Final privacy operating facts | Retention by category, retained deletion identifiers, actual provider entities/countries/controls and overseas legal basis remain unsettled. These need owner facts and applicable legal assessment, not another generic consent checkbox. |
| Accurate release declarations/content | Finish privacy URL, per-type Data safety, deletion URL/answers and health disclosures against the exact distributed binary and backend. Saved drafts and HTTP 200 are not compliance approval. |
| Android/listing/testing evidence | Latest records still lack real Android workflow signoff, feature graphic and phone screenshots. Genuine closed-test participation/feedback and any production-access application remain separate gates. |

No new decision is needed on public display operator **아르케**, public support
**areche.ai.kr@gmail.com**, initial **18+**, or the selected **food OpenAI / body
mock** mode. Those are approved inputs, not proof of legal-entity identity,
mailbox operation, verified age, provider contracts, or Play eligibility.

## Evidence Boundary And Precedence

Only source and non-secret documentation in `/private/tmp/cal-ai-play-20261109`
were reviewed, together with publicly accessible official policy/provider pages.
No Console/account dashboard, production configuration, mailbox, database, R2
object, private evidence JSON, environment file, credential or paid API was read.
No submission, cloud/public-page edit, terms acceptance, activation or erasure
was performed. The only authored file is this review.

Historical operational results below are reported by the named local records,
not independently rerun on November 15. Use this evidence order:

1. `SCHEDULED-RETENTION-AUTH-2026-11-14.md`: the latest bounded scheduled test
   passed. Vercel's actual scheduled request at 11:08 UTC authenticated; the due
   synthetic image became a content-free guard and persisted deleted state;
   independent Neon/R2 readback confirmed it and the then-not-due control was
   unchanged. Prior production/cron were restored, the temporary secret/keys
   removed, and the temporary deployment removed. Ordinary deletion/retention
   remain disabled. This was accelerated synthetic expiry, not seven elapsed days
   or a general-user/SLA proof. The control's later state was not checked here.
2. `LIFECYCLE-COMPLETION-2026-11-13.md`: later legacy-key guard/replay protection
   passed separately. Do not repeat the earlier legacy-recreation defect as
   wholly unresolved; do not infer a new account-level completed state either.
3. `ISOLATED-ERASURE-VERIFICATION-2026-11-13.md`: disposable Supabase identity
   deletion and removal of live upload rows were evidenced, but its last overall
   account readback was still pending, with retained manifests. No later full
   account-level completion readback was supplied by the scheduled-photo test.
4. `PLAY-UPLOAD-2026-11-11.md` and the final checkpoint in `RELEASE-GATES.md`:
   current AAB accepted into a saved internal draft, not distributed; listing
   text/icon saved; privacy/Data safety incomplete; no closed-test evidence.
   Earlier contradictory no-upload/provider-untested text is historical.
5. `PRIVACY-OPERATIONS-DECISIONS-2026-11-11.md`, `public_routes.py`, and current
   supporting source establish the inventory, not final operating/legal facts.

Earlier exhausted QA/repair budgets are not reset by this review. Neither the
successful narrow synthetic test nor this document clears whole-service QA.

Latest recorded ordinary settings remain `ACCOUNT_DELETION_ENABLED=false`,
`ACCOUNT_DELETION_WORKER_ENABLED=false`, `R2_WRITE_ONCE_UPLOADS_ENABLED=false`,
with the temporary project `CRON_SECRET` removed. Important source distinction:
`main.py:369` authenticates ordinary photo cleanup with `CRON_SECRET`; its photo
cleanup is not conditional on the two account-deletion flags. Adding that secret
is therefore not a harmless way to prepare account deletion while keeping all
ordinary retention off. No such setting change is authorized by this review.

## Current Official Google Requirements

### Account Type Versus Testing Eligibility

The full [Play Console Requirements](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en)
policy, section 1.2, requires developers offering health apps to register as an
Organization when creating an account. [Choose a developer account type](https://support.google.com/googleplay/android-developer/answer/13634885?hl=en)
also uses mandatory Organization wording for health apps, with medical and human
subjects research as examples, not an explicit exhaustive exception list.
[Google's health taxonomy](https://support.google.com/googleplay/android-developer/answer/13996367?hl=en)
includes fitness and nutrition trackers within health apps.

**Application/inference:** this code's meal, weight, fitness and recovery features
are health-related. Being non-medical or 18+ does not establish a personal-account
exception. The full policy's account-creation wording does not itself decide
grandfathering for this existing account. Account age, applicable transition
rules and exact account eligibility were not verified. Treat eligibility as
unresolved, not as confirmed permission or a claim that Google has rejected it.

The [new-personal-account testing rule](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en)
applies to accounts created after November 13, 2023: at least 12 opted-in testers
continuously for the preceding 14 days, then apply for production access with
testing/feedback/readiness answers. Meeting the count does not guarantee access.
The existing account's creation date and current production-access state are
unknown here. An internal draft or direct APK install does not prove that closed
test participation occurred. The rule is not a health-policy waiver; it is also
not a universal 12/14 requirement for every Organization or older account.

### Health Declaration And Privacy

The [Health apps declaration guidance](https://support.google.com/googleplay/android-developer/answer/14738291?hl=en)
includes closed tracks. Source supports Activity and Fitness, Nutrition and
Weight Management, and sleep-quality tracking; retain the recorded sleep
declaration unless the actual release inventory justifies changing it. Do not
declare medical diagnosis, regulated medical-device functionality or research
merely because the app stores health data.

[Health Content and Services](https://support.google.com/googleplay/android-developer/answer/16679511?hl=en)
requires health-data disclosures, relevant consent/permission handling and
non-misleading functionality. For non-regulated health apps, the description
must make the non-medical-device/no diagnosis-treatment-cure-prevention limits
clear and remind users to seek a healthcare professional for medical advice.
The local Korean listing draft has non-medical/diagnosis/treatment/prevention
language but no explicit healthcare-professional reminder. Review the final
description and in-app reminders; do not treat a privacy-page disclaimer alone
as a completed listing requirement.

The [User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en)
requires an identifiable privacy policy linked in Console and in-app, on a
public, active, non-geofenced, non-editable web resource rather than a PDF. It
must describe data, purposes/recipients, secure handling, retention/deletion and
privacy contact, consistently with actual behavior. Prominent disclosure and
affirmative consent are required where applicable; a camera permission or a
link to terms is not automatically equivalent. The code's technical-draft notice
is honest, but does not settle missing operating facts.

### Account Deletion Required Scope

[Google's account-deletion guidance](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en)
covers account creation through in-app or redirected flows, including OAuth.
Provide discoverable in-app initiation plus a Console-linked web request route
usable without reinstalling. An email/form can be the web route; it must work,
identify the app/developer, and actually support requests. Account freezing,
logout or deleting only a profile is insufficient. Delete associated collected
data, including health/photos/usage; ask processing service providers to delete
their copies. Legitimate security/fraud/regulatory exceptions require clear
retention disclosure. Explain timing and fulfill requests reasonably quickly;
Google does not prescribe one universal numeric deadline here.

**Code-specific scope:** Supabase app identity; all owned profiles, onboarding,
meal/analysis/clarification data, weight/recovery/body/consent records, workout
plans/sessions, analytics account/session/events and linked uploaded photos.
Deletion batching also includes owned billing rows if present; a billing table
does not prove payment collection is active. Support correspondence, provider
logs/backups and audit records need a separate scope/exception disposition.
The user's Kakao account and device-gallery originals are not app-owned accounts
or uploaded server copies; do not promise to delete them. External subscriptions
are not automatically canceled by app deletion.

`public_routes.py` exposes an off-app email path and distinguishes profile
deletion, pending acceptance and completion. Source acceptance depends on both
configured server-side admin capability and worker readiness. Do not attest
successful deletion from the presence of those pages, HTTP 202, logout, absent
live upload rows or one erased object. Minimal account-linked tombstones and
object manifests remain personal data, not anonymous totals. Necessary guards
must not be discarded merely to make an all-data-erased claim.

### Screenshot And Listing Asset Specifications

The current [preview-assets requirements](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en)
distinguish mandatory upload specifications from promotional recommendations:

| Item | Mandatory baseline / separate recommendation |
| --- | --- |
| Screenshots | At least two across device types to publish the listing; up to eight per supported type. For this phone listing prepare at least two actual Android phone captures, as the project's recorded gate. |
| Format/size | JPEG or 24-bit PNG without alpha; each dimension 320-3840 px; long side no more than twice the short side. A 1080 x 1920 capture fits; a 1080 x 2400 phone capture needs an honest crop/layout adjustment, not distortion. |
| Promotional recommendation | At least four app screenshots at 1080px minimum, 16:9 landscape or 9:16 portrait for the cited recommendation surfaces. This is not the two-image publication minimum. |
| Feature graphic | Required, 1024 x 500 px, JPEG or 24-bit PNG without alpha. |
| Icon | Required, 512 x 512 px, 32-bit PNG with alpha, at most 1024 KB. Existing icon saved per prior record, not re-uploaded/revalidated here. |

Capture the actual release UI with synthetic records. No real body photo,
credential, notification or unnecessary health/account data belongs in assets.
Do not depict mock body observations as verified live AI. This task generated
or uploaded no assets and did not verify any screenshot file.

## Privacy Draft Grounded In The Current Product

This is internal candidate wording, not an approved replacement for `/privacy`:

> Trust First Nutrition is operated under the public display name 아르케. Privacy
> inquiries and account-deletion requests can be directed to
> areche.ai.kr@gmail.com. The service targets adults aged 18 and above; the
> onboarding age check is self-reported, not verified identity or age.
>
> Account identifiers and, when supplied by the login provider, email/name support
> authentication, record ownership and account-linked operational analytics.
> Age, sex, height, weight/goals and exercise preferences support targets and
> personalized plans. Meal/nutrition, workout, weight and optional recovery/body
> check-in records support logging and coaching. Selected photos and optional
> notes are transmitted for the selected features. Screens/actions, timestamps,
> errors and sessions are recorded through our own API and can identify accounts.
>
> Food-photo analysis uses OpenAI in the selected operating mode; the request
> contains a photo reference, meal type and any optional note. Body analysis is
> currently mock, although an optional body upload/check-in still creates app
> data. It must not be represented as live OpenAI body analysis. A separate body
> consent record is implemented; it does not establish every legal permission.
> Photo/health inputs are not used for diagnosis, identity or appearance scoring.
>
> The source configures upload-specific photo expiry metadata, not a guarantee
> that photos are automatically erased on that date. General deletion/retention
> processing remains disabled under the latest recorded configuration. Account
> deletion, when operationally supported, must remove the app account and linked
> records/photos; profile deletion alone retains the login account. Minimal
> deletion/retry identifiers and content-free guards may remain. Provider copies
> and backups have separate controls; no immediate or universal erasure is promised.

Before publication, replace uncertainty with confirmed operating facts and an
effective date/version. In particular, establish an actually working request
service before presenting that contact as a fulfilled deletion mechanism. Do
not publish a guessed recipient entity, country, legal ground, retention period,
provider-training assertion or automatic completion promise.

## Data Safety Draft Worksheet

Under [Google's Data safety guidance](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en),
closed tracks require the form; exclusively internal tracks are exempt.
Off-device transmission is collection, including SDK/provider processing.
Ephemeral treatment needs memory-only handling limited to the request; our
persisted records do not qualify. A processor exception to sharing needs actual
on-behalf processing; an API call alone proves none. Optional means every user
can avoid that type and still use the app. Final labels cover distributed versions.

All rows below are **collection candidates supported by source**, not saved
Console selections. Sharing is unresolved per recipient until actual terms,
independent uses and any applicable exception are established. Nothing here
supports a blanket no-sharing declaration. Stored rows are non-ephemeral.

Purpose shorthand: F = App functionality; A = Analytics; P = Personalization;
M = Account management. These are proposed mappings of code behavior, not new
business purposes or authority for broader use.

| Candidate form type | Actual payload/storage and source evidence | Proposed purposes | Required/optional draft |
| --- | --- | --- | --- |
| Personal info: User IDs | Auth subject, profile ownership; `auth.py:132`, `analytics_repository.py:305` | F, M, A | Required for authenticated account features. |
| Personal info: Email address, Name | Claims copied into `app_users`, available to operator analytics; same sources | F, M, A | Provider/path-dependent; receiving a nullable claim is not proof that users can opt out. Verify OAuth scopes and password-login path. |
| Personal info: Other info | Age and sex in onboarding; `schemas.py:26` | F, P | Required fields in onboarding. 18-100 for new requests; stored legacy schema has a wider range. |
| Health and fitness: Health info | Weight/height, nutritional targets/meals, recovery/sleep/soreness, body observations/consent; `schemas.py:26`, `coach_schemas.py:56` | F, P; A only for health values actually used in event properties | Core onboarding is required; additional logs/check-ins are elective. Because the type also contains required inputs, do not mark the whole type optional. |
| Health and fitness: Fitness info | Workout preferences, sets/reps/load/intensity/duration and plans; `coach_schemas.py:121`, `admin_schemas.py:11` | F, P; A for actual workout event properties | Required exercise preferences plus elective logs; do not call the whole type optional without verifying every path. |
| Photos and videos: Photos | Food and body uploads, metadata and storage references; `image_uploads.py:62`, `coach_routes.py:272` | F | Proposed optional: photo features can be declined while other features remain. Verify this on the exact Android build. Body mock does not mean no photo collection. |
| App activity: Other user-generated content | Free-form meal/recovery notes where not already captured by a more specific health type; `schemas.py:215`, `coach_schemas.py:67` | F, P where coaching uses the note | Optional notes; content-specific health information still needs the appropriate health mapping. |
| App activity: App interactions | Screen/event names, heartbeat, timestamps, account/profile/session linkage; `apps/mobile/src/analytics/client.ts:24`, `analytics_repository.py:89` | A | Automatic while the client runs; no opt-out established. |
| App info and performance: Diagnostics | Analysis failure/status/error code events; `admin_schemas.py:11` | A, F for actual error handling | Review exact emitted payloads. An error event does not establish crash-stack collection. |
| Device or other IDs: needs resolution | App-generated analytics session ID stored in AsyncStorage and rotated after inactivity; `analytics/client.ts:148` | A if this subtype applies | Do not infer an advertising/device ID. Resolve whether this ID identifies an app/browser/device versus only a session; account linkage is already established above. |

Do not add collection solely because an environment example names PostHog/Sentry
or a schema contains billing fields. Conversely, lack of AD_ID/Health Connect
permissions does not establish no analytics or no health collection. No location,
contacts, microphone/audio, payment-card, advertising identifier or external
crash SDK flow was established by this bounded review. These are **not** universal
negative declarations for every release dependency/provider log.

The form's encryption answer needs verification of all actual release transfers
(API, Auth, uploads and provider legs), not merely an HTTPS page. Retained
identifiers, provider logs and backups prevent an all-data-ephemeral assertion.
Account creation: OAuth is supported; password sign-in for an existing account
does not prove password-based account creation. Deletion URL candidate:
`https://cal-ai-api.vercel.app/account-deletion`; do not attest usable fulfillment
until the operational gate is met. No independent security certification was
established. No ads/marketing/sale purpose was established by this code review.

## Provider And Overseas-Processing Matrix

Brands below identify technical paths, **not verified recipient legal entities**.
For each active recipient resolve legal entity/contact, actual data/purpose,
processing and support/log/backup countries, transfer timing/method, contract,
retention/deletion controls and subprocessors. Separately assess processing-role
classification and applicable overseas legal basis/refusal consequences. A Play
sharing exception does not decide those legal questions. Neither `R2_REGION=auto`
nor a primary database region proves every processing country.

| Path / mode | Data and purpose grounded in source | Retention/deletion evidence and missing facts |
| --- | --- | --- |
| Vercel web/API hosting | Request routing/API payload handling and operational diagnostics; hosting path recorded in release/scheduled-test docs | No account-specific request-log retention, region matrix, contractual entity or backup disposal verified here. Avoid asserting request bodies are always logged or never logged. |
| Supabase Auth | App identity, provider metadata, password-login credentials, sessions; `auth.py`, `account_deletion.py:38`, mobile `useAuthSession.ts` | Disposable hard identity deletion evidenced historically; no general-user activation. Auth logs/backups, project settings, contract/regions and retained provider copies unknown. |
| Kakao OAuth | User authentication and configured identity/profile/email scopes; mobile `useAuthSession.ts:141` | Exact granted scopes/recipient role/retention unknown. App Auth deletion does not delete the Kakao account. No Kakao admin settings were inspected. |
| Neon / configured Postgres | Profiles, health/fitness records, AI outputs, app analytics, deletion jobs/manifests; repository schemas and prior Neon readbacks | App-row cleanup is not proof of backup/log erasure. Region, restore window and safeguards against restoring deleted users need account/contract evidence. No universal app-row TTL found. |
| Cloudflare R2 | Selected image bytes, upload-linked object keys and storage metadata; `storage.py`, `image_uploads.py:227` | Narrow synthetic scheduled erasure/guards passed. Ordinary cleanup remains disabled. Legacy keys can include sanitized filenames; do not call every key random or anonymous. Jurisdiction, replicas/logs and general lifecycle policy need verification. |
| OpenAI food: selected live mode | Food image reference, meal type, optional note; `analysis_provider.py:171`; returned nutrition analysis persisted by app | `store=False` is present. Published defaults/limitations below are verified, but this account's sharing opt-ins, ZDR/MAM approval, contract, regions and deletion options are not. App does not implement a general provider-copy deletion workflow here. |
| Body mock: selected mode | Body photo/check-in and consent can still be stored in app/R2; mock provider generates observations. Optional OpenAI implementation would send image reference/view/prior-check-in boolean, not the prior image; `body_analysis_provider.py:103` | Do not claim body photos are currently sent to OpenAI. Enabling that provider would require new inventory/consent/declaration and account-controls review. |
| Public support Gmail address | Voluntary request/correspondence outside app repositories; `public_routes.py` | Owner-approved address only. Mailbox control/receipt, operator handling, storage countries, case retention, deletion escalation and provider retention not verified. Do not read/connect mail or send a test without authority. |

[OpenAI's current data-controls documentation](https://developers.openai.com/api/docs/guides/your-data)
states API content is not used for training by default unless the customer opts
in. Abuse-monitoring content is normally retained up to 30 days, with legal/safety
extensions; ZDR/MAM require approval. Responses storage and abuse monitoring are
different controls. Image safety flags can cause manual-review retention even
with special controls. This is published provider behavior, **not** confirmation
of this account's settings, no copies, or a binding 30-day maximum. Deleting the
R2 input does not retract a request already processed by OpenAI.

[Supabase user-management documentation](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users)
confirms hard user deletion and issued-token expiry are separate: already-issued
JWTs can remain valid until expiry. The source's durable account-access gate
(`account_routes.py:54`, `main.py:111`) is relevant, but deployed rejection plus
failed refresh/relogin still need their own operational evidence. Optional paid
[session controls](https://supabase.com/docs/guides/auth/sessions)
are not assumed configured or purchased.

## Retention And Deletion Decisions Still Open

| Category | What is established | Decision/evidence still needed |
| --- | --- | --- |
| Account and health/fitness/analysis records | Persisted in repositories; no universal age-based purge established | Purpose-limited duration, closure behavior and any genuinely applicable exception. Do not invent statutory retention. |
| Photo bytes | `storage.py:17` default is 30 days; per-upload `cleanup_after` set at completion (`image_uploads.py:154`); synthetic deadline differed | Confirm actual ordinary configuration and approved duration, then deploy/monitor justified enforcement. Neither default nor isolated shortened expiry is an approved retention policy. |
| Upload metadata/results/meal records | Photo-byte cleanup does not erase these rows | Separate retention and purge behavior; minimize filenames/references. |
| Product analytics/session/user rows and admin audits | Account-linked analytics stored; account purge covers app analytics; no general TTL established | Purpose/duration/access controls and matching purge. Audit schema exists, but no complete subject-related audit-log purge/exception assessment was established. |
| Deletion tombstone/work/manifests/guards | Account ID, state and remote keys can remain without automatic expiry | Minimum fields, justified access-block/retry need, restricted access, review/end condition and disposal design. Permanent guards protect against replay; do not remove them unsafely or describe their keys as anonymous. |
| Support correspondence/provider logs/backups | Outside the ordinary repository deletion path | Confirm each retention/disposal process, provider requests, legal/security exceptions and restore handling before promising a completion time/scope. |

These are operational/business facts and legal classifications to resolve, not a
new list of laws already determined to apply. Owner approval cannot by itself
make a processing basis lawful or override a provider/Google requirement. Formal
legal signoff is not represented as a universal Play form field; seek qualified
advice where the actual processing facts require it.

## Decision Handoff

No repeated approval is requested for the already selected display name/contact,
adult targeting, provider mode or refusal to convert accounts. The missing
owner-side facts are the actual responsible legal identity/contact if different
from the display name, service/record retention choices, mailbox staffing and
case handling, and authoritative provider/account contract/control evidence.
Overseas-transfer legal basis and any sensitive-data consent requirements remain
unknown, not accepted by this task.

The next technical work, outside this document-only authority, is to resolve the
account-eligibility question; complete a safe operational deletion service and
its cross-store readback; align approved public disclosures and per-type form
answers; capture/test the exact Android release; and verify genuine closed-test
eligibility/participation. Any activation, deletion, deployment, Console save,
submission, legal acceptance or publication needs its own applicable authority.
Do not reopen completed synthetic scheduled proof or spend exhausted QA budgets
merely to prepare this draft.

## Source Register And Review Method

All external sources below were opened as official pages during this review on
2026-11-15. Specific relevant sections, rather than unrelated linked policies,
were checked. Google-hosted community replies and third-party summaries were
not used as authoritative policy, including replies that contradict one another.

| Official source | Exact URL and relevant section |
| --- | --- |
| Play Console Requirements | [Official page](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en): full policy 1.2 and pre-submission requirements |
| Choose a developer account type | [Official page](https://support.google.com/googleplay/android-developer/answer/13634885?hl=en): Organization services |
| Health app categories and additional information | [Official page](https://support.google.com/googleplay/android-developer/answer/13996367?hl=en): fitness/nutrition versus medical/research |
| App testing requirements for new personal developer accounts | [Official page](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en): scope, closed testing, production application |
| Provide information for the Health apps declaration form | [Official page](https://support.google.com/googleplay/android-developer/answer/14738291?hl=en): track scope and feature categories |
| Health Content and Services | [Official page](https://support.google.com/googleplay/android-developer/answer/16679511?hl=en): Health and Medical Apps. The older linked answer/12261419 redirected to this page. |
| User Data | [Official page](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en): prominent disclosure, Privacy Policy, Account Deletion Requirement |
| Provide information for Google Play's Data safety section | [Official page](https://support.google.com/googleplay/android-developer/answer/10787469?hl=en): tracks, collection/sharing, handling and type/purpose taxonomy |
| Understanding Google Play's app account deletion requirements | [Official page](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en): scope, service-provider requests, timing and web-resource FAQ |
| Add preview assets to showcase your app | [Official page](https://support.google.com/googleplay/android-developer/answer/9866151?hl=en): screenshot requirements versus recommendations, icon, feature graphic |
| OpenAI data controls | [Official page](https://developers.openai.com/api/docs/guides/your-data): default training, abuse monitoring, Responses and image-input exceptions |
| Supabase User Management | [Official page](https://supabase.com/docs/guides/auth/managing-user-data#deleting-users): identity deletion and outstanding access tokens |
| Supabase User sessions | [Official page](https://supabase.com/docs/guides/auth/sessions): session lifecycle and optional plan-dependent controls |

Local evidence links (absolute paths; line numbers identify starting anchors):

- [Privacy operations decisions](/private/tmp/cal-ai-play-20261109/docs/google-play/PRIVACY-OPERATIONS-DECISIONS-2026-11-11.md)
- [Release gates and final checkpoint](/private/tmp/cal-ai-play-20261109/docs/google-play/RELEASE-GATES.md:224)
- [Latest successful scheduled test and restoration](/private/tmp/cal-ai-play-20261109/docs/google-play/SCHEDULED-RETENTION-AUTH-2026-11-14.md)
- [Earlier account-level partial result](/private/tmp/cal-ai-play-20261109/docs/google-play/ISOLATED-ERASURE-VERIFICATION-2026-11-13.md)
- [Separate later legacy guard evidence](/private/tmp/cal-ai-play-20261109/docs/google-play/LIFECYCLE-COMPLETION-2026-11-13.md)
- [Saved AAB/listing draft evidence](/private/tmp/cal-ai-play-20261109/docs/google-play/PLAY-UPLOAD-2026-11-11.md)
- [Direct Android handoff, not a runtime pass](/private/tmp/cal-ai-play-20261109/docs/google-play/ANDROID-DIRECT-TEST-2026-11-11.md)
- [Listing disclaimer draft](/private/tmp/cal-ai-play-20261109/docs/google-play/STORE-LISTING-DRAFT.ko.md)
- [Public privacy/deletion text and dynamic notices](/private/tmp/cal-ai-play-20261109/services/api/app/public_routes.py:16)
- [Food payload](/private/tmp/cal-ai-play-20261109/services/api/app/services/analysis_provider.py:171)
- [Body provider/payload](/private/tmp/cal-ai-play-20261109/services/api/app/services/body_analysis_provider.py:103)
- [Authenticated deletion/access gate](/private/tmp/cal-ai-play-20261109/services/api/app/account_routes.py:54)
- [Deletion capability, hard Auth removal and worker](/private/tmp/cal-ai-play-20261109/services/api/app/services/account_deletion.py:25)
- [Account purge batches](/private/tmp/cal-ai-play-20261109/services/api/app/services/persistence.py:718)
- [Analytics identity and event storage](/private/tmp/cal-ai-play-20261109/services/api/app/services/analytics_repository.py:89)
- [Automatic native analytics](/private/tmp/cal-ai-play-20261109/apps/mobile/src/analytics/client.ts:24)
- [Health schemas](/private/tmp/cal-ai-play-20261109/services/api/app/coach_schemas.py:56)
- [Onboarding schemas](/private/tmp/cal-ai-play-20261109/services/api/app/schemas.py:26)
- [Event/property inventory](/private/tmp/cal-ai-play-20261109/services/api/app/admin_schemas.py:11)
- [Native privacy/deletion UI](/private/tmp/cal-ai-play-20261109/apps/mobile/src/screens/SafetyPrivacyScreen.tsx:9)
- [Upload metadata/expiry](/private/tmp/cal-ai-play-20261109/services/api/app/services/image_uploads.py:154)

Verification for this deliverable is document/source consistency and write-scope
validation only. No application tests or provider calls were run, since this task
authorizes no code/runtime change and must not generate other files. This partial
temporary checkout is not proof of an exhaustive SDK/dependency/binary audit.
The Wiki contract was read; its `context` command was not invoked because source
inspection shows it may refresh/write an index outside the sole allowed output.
