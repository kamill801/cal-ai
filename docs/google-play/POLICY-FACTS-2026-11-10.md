# Public Policy and Support Facts - 2026-11-10

Status: source-grounded technical documentation, not an attested final privacy
policy, legal compliance opinion, account-eligibility approval, or release approval.

Scope: `/privacy`, `/terms`, `/support`, `/account-deletion`, their focused tests,
and this document in `/private/tmp/cal-ai-play-20261109`. Other contributors own
the storage, persistence, deletion, authentication and mobile implementations.
This change does not enable those features or change their behavior.

## Evidence Boundary

- Read current storage/upload, authentication, analytics, account deletion,
  persistence, health/profile schemas and related route implementations below.
- Read mobile login, session storage, analytics, image selection and deletion UI
  source only to document the existing paths; no mobile files were changed.
- Read `services/api/.env.example`, not actual secret environment files or values.
  Example settings do not prove live configuration. No provider account was
  inspected, mutated, connected or provisioned by this documentation task.
- Read Google's public primary policy/help pages linked below. Their definitions
  do not prove this app or developer account has been accepted by Google.
- Local tests establish rendered content, configuration validation, safe public
  reads and regression behavior. They do not establish live storage erasure,
  scheduler execution, support mailbox ownership/delivery, reviewer login, or
  legal sufficiency.

## Public Document Metadata

Implemented only in `services/api/app/public_routes.py::policy_metadata`:

| Public setting | Default | Accepted value |
| --- | --- | --- |
| `PUBLIC_POLICY_EFFECTIVE_DATE` | `2026-11-10` | A real calendar date in canonical `YYYY-MM-DD` form |
| `PUBLIC_POLICY_VERSION` | `2026-11-10.1` | `YYYY-MM-DD.N`, with a one-to-four-digit numeric revision |

Values are read when rendering, so configuring a later approved revision does not
require changing page templates. Missing/invalid values fall back to the public
defaults; invalid input is not echoed. No arbitrary environment configuration or
request parameters are rendered. These are new public document settings, not
changes to `.env.example` or live configuration. Never put credentials in them.

All four pages show the document effective date and version, plus a visible notice
that actual operations, provider contracts and deletion execution require separate
verification. The effective date is a document date, not proof of approved legal
terms or a recorded user consent. `BODY_AI_CONSENT_POLICY_VERSION` is separate;
changing the public version does not update historical consent or collect consent.

## Source-Verified Facts

Paths below are relative to the release worktree. These are code facts, not claims
that the corresponding production configuration is active.

| Area | Implemented behavior and disclosure | Evidence |
| --- | --- | --- |
| Public notices | Unauthenticated read-only HTML; Korean language, headings, document links, skip link, focus styling, wrapping; no credential form or third-party scripts. Existing operator/contact text is retained. | `services/api/app/public_routes.py::render_page`; `services/api/app/main.py::optional_authentication` |
| Identity | Supabase JWT verification uses asymmetric signatures, issuer, audience, expiry and subject. Provider, email and display name may be extracted. No explicit verified-email-ownership check is made here. | `services/api/app/services/auth.py::_authenticate_supabase_bearer_token` |
| Login | Kakao OAuth and existing-account email/password login paths exist. Password login invokes Supabase directly, not the app record API. UI availability and real account access still depend on configuration. | `apps/mobile/src/auth/useAuthSession.ts`; `apps/mobile/src/auth/passwordLogin.ts`; `apps/mobile/src/screens/LoginScreen.tsx` |
| Device state | Native auth sessions use SecureStore; web auth uses AsyncStorage. Profile and analytics session identifiers also use AsyncStorage. Logout/uninstall is not server erasure. | `apps/mobile/src/auth/supabase.ts`; `apps/mobile/src/session/profileSession.ts`; `apps/mobile/src/analytics/client.ts` |
| Health-related inputs | Age, sex, height, weight, goals, activity and training preferences feed target/plan calculation. Weight, meals/nutrition, exercise performance, energy, sleep quality, soreness and notes can be stored. Health/body information can be sensitive; a comprehensive legal basis is not established by these schemas. | `services/api/app/schemas.py::OnboardingRequest`; `services/api/app/coach_schemas.py`; `services/api/app/services/coach_repository.py` |
| Age | Owner approved an initial 18+ audience on 2026-11-11. New onboarding accepts self-reported integer ages 18 through 100; stored legacy ages 14 through 17 remain readable to preserve data. Authenticated owners with any stored underage profile are blocked from feature APIs while profile read/deletion and account management remain accessible. Mobile age-block UI preserves privacy/deletion/logout. These are local-source/test facts, not deployed enforcement or verified age. | `services/api/app/schemas.py::OnboardingRequest`, `StoredOnboardingData`; `services/api/app/main.py::optional_authentication`; `services/api/app/services/coach_repository.py::has_underage_profile`; `apps/mobile/App.tsx` |
| Optional images | Library selection uses the system image picker; camera capture requests permission. Cancellation/denial stops that image operation. The upload API records filename/type/size, image and object identifiers, status, ownership and timestamps. It is not a whole-library upload implementation. | `apps/mobile/src/media/mealImagePicker.ts`; `services/api/app/services/image_uploads.py`; `services/api/app/services/persistence.py::ImageUploadRecord` |
| Body consent | A body check-in requires an authenticated owner and `consent_to_ai_analysis=True`. A successful check-in records timestamp, provider, model and body-consent policy version. This is not evidence of comprehensive health-data consent, guardian consent, or an independently verified email. | `services/api/app/coach_schemas.py::BodyCheckInRequest`, `BodyAnalysisConsent`; `services/api/app/coach_routes.py::create_body_photo_check_in` |
| Meal AI | If `AI_PROVIDER=openai`, the built request includes the analysis image reference, meal type and optional user note. The R2 path issues a short-lived read URL. Mock analysis is also implemented. | `services/api/app/services/analysis_provider.py::build_responses_payload`, `get_analysis_provider`; `services/api/app/services/image_uploads.py::resolve_analysis_image_reference` |
| Body AI | If `BODY_AI_PROVIDER=openai`, the request includes the selected image reference, requested view and whether a previous check-in exists, not the previous image itself. Prompts limit observations and forbid identity, diagnosis, body-fat and attractiveness inference. This describes intended safeguards, not perfect model behavior. | `services/api/app/services/body_analysis_provider.py::build_responses_payload`, `validate_safe_body_analysis` |
| AI storage option | Both OpenAI request builders set `store=False`. This alone proves neither zero provider retention nor absence of security/abuse logs, training use, backups or regional processing. | Both AI providers' `build_responses_payload` methods |
| App storage | `DATABASE_URL` selects Postgres; otherwise a configured/default local SQLite path is used. Generic Postgres code does not prove a Neon binding or its region. Storage selects local/mock or R2 adapters. | `services/api/app/services/persistence.py::_create_persistence_repository`; `services/api/app/services/storage.py::get_storage_adapter` |
| Analytics | Own API stores allowlisted product events, session/profile/account IDs, screen/time/properties and heartbeat activity. Authenticated email/display name can be copied into `app_users`; admin views can show per-account activity. Some properties contain goal, clarification or workout context, so this is not necessarily anonymous. | `services/api/app/admin_schemas.py::AnalyticsEventRequest`; `services/api/app/analytics_routes.py`; `services/api/app/services/analytics_repository.py::record_event`, `heartbeat`, `_upsert_user`; `apps/mobile/src/analytics/client.ts` |
| External analytics | The inspected application source does not implement PostHog/Sentry forwarding just because their names occur in the example environment. Do not infer deployment, logs or global tracking absence from this limited inspection. | `services/api/.env.example`; application analytics paths above |
| Photo expiration | Default/example `IMAGE_TTL_DAYS=30`. Completing an upload calculates `cleanup_after`; an authenticated cleanup API attempts object deletion and marks upload records deleted. This does not erase every metadata row, analysis result or meal record. | `services/api/app/services/storage.py::get_image_ttl_days`; `services/api/app/services/image_uploads.py::complete_presigned_image_upload`; `services/api/app/main.py::cleanup_expired_images`; `services/api/app/services/persistence.py::mark_image_upload_deleted` |
| Scheduling | `vercel.json` declares `/internal/cleanup-images` at `0 18 * * *`. An enabled account worker can be called from that endpoint and has its own protected route. Checked-in configuration is not proof of deployed cron execution or successful cleanup. | `vercel.json`; `services/api/app/main.py::cleanup_expired_images`; `services/api/app/account_routes.py::run_account_deletion_worker` |
| Record deletion | Profile deletion covers current-profile artifacts and connected images; it preserves the authentication identity. It also removes account-wide analytics events, sessions and the analytics user row, not only current-profile analytics. Deleting a meal row is not equivalent to erasing its image or the whole account. | `services/api/app/coach_routes.py::delete_profile_data`; `services/api/app/services/analytics_repository.py::delete_profile_data`; `services/api/app/services/persistence.py::delete_meal_log`; `apps/mobile/src/screens/SafetyPrivacyScreen.tsx` |
| Account request | Authenticated `DELETE /v1/account` requires explicit confirmation. Disabled/missing server configuration rejects before acceptance. Accepted durable requests return pending (`202`), unless a terminal checkpoint already exists (`200`). Public GET pages and the navigation link do not execute deletion. | `services/api/app/account_routes.py::AccountDeletionRequest`, `delete_current_account`; `services/api/app/services/account_deletion.py::delete_account` |
| Account worker | An explicit versioned migration installs owner-scoped write guards before enablement. Acceptance takes a durable tombstone; leased, bounded SQL phases inventory before removing owned app/analytics/billing records, then request Supabase identity deletion and sweep objects. Auth identity deletion may precede object cleanup. Atomic lease fencing and original storage namespace checks protect checkpoints. Worker configuration and actual provider results still require independent operational verification. | `services/api/app/services/account_deletion.py::_resume_account_deletion`; `services/api/app/services/persistence.py::prepare_account_deletion`, `begin_account_deletion`, `process_account_deletion_batch` |
| R2 erasure gate | Default-off `R2_WRITE_ONCE_UPLOADS_ENABLED` signs atomic create-once conditional uploads for server-generated sealed keys. Erasure overwrites photo bytes with a permanent zero-byte guard and verifies its metadata in the original storage namespace. Completion requires a durable verified checkpoint. Legacy/unknown-namespace uploads remain pending; expiry/HEAD/DELETE alone is insufficient. Conditional writes, CORS, concurrent uploads, absence of lifecycle guard removal and real provider behavior remain unverified. Guards and random keys remain; do not call this complete erasure of every object/copy. | `services/api/app/services/storage.py::erase_account_object`; `services/api/app/services/persistence.py::account_storage_cleanup_complete`, `list_account_deletion_objects`; `services/api/app/services/account_deletion.py::_resume_account_deletion` |
| Retained deletion state | Account ID, stage/timestamps, worker identity/lease state, image IDs, storage provider, object keys and sweep history can remain in deletion tables. Even a stage-3 `deleted` result retains the account marker and access block. No automatic expiry is implemented and no final retention period is established. These are not just anonymous counters. | `services/api/app/services/persistence.py::_account_worker_schema`, `begin_account_deletion`, `advance_account_deletion`, `_save_account_deletion_objects`; `services/api/app/services/account_deletion.py::account_access_blocked` |
| Support and rights | Public pages retain operator `아르케` and contact `areche.ai.kr@gmail.com`, describe app controls and email escalation, require safe ownership verification and warn against sending secrets/body photos. Publishing the address does not verify mailbox ownership/delivery or provide an automated rights workflow. | `services/api/app/public_routes.py`; existing login/deletion UI above |

## Google Play Classification and Account Gate

Confirmed from public primary sources on 2026-11-10:

- Google's health-app definition includes health/fitness apps and examples such as
  nutrition, fitness, wellness and sleep tracking. Being non-medical does not, by
  itself, exclude an app from that published definition.
  [Health app categories](https://support.google.com/googleplay/android-developer/answer/13996367?hl=en).
- The declaration guide includes Activity and Fitness, and Nutrition and Weight
  Management. This product's meal, weight and workout functionality must be
  considered when the owner completes the declaration; final selections need
  review against all actual features.
  [Health apps declaration](https://support.google.com/googleplay/android-developer/answer/14738291?hl=en).
- Published Console requirements list health apps among services requiring an
  Organization account and separately require review access resources. The
  account-type guide repeats the health-app category and describes organization
  verification.
  [Play Console Requirements](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en),
  [Choose a developer account type](https://support.google.com/googleplay/android-developer/answer/13634885?hl=en).

Application to this release: **UNRESOLVED, NOT APPROVED**. Fresh Console readback
on 2026-11-11 confirms the existing developer account is `PERSONAL`. The owner
declined account conversion and selected existing-account closed-test draft
preparation. The Console requirements' section 1 starts with account creation;
the cited pages do not expressly establish a blanket prohibition on every
existing-account draft/upload preparation step or an exemption for closed tests.
Proceed with truthful declarations and record any actual eligibility gate rather
than treating automatic account conversion as a prerequisite to all draft work.
Do not treat a non-medical disclaimer, a
wellness label, community advice, tests, document completion or an available
Console action as an approved exception. The owner must resolve account
eligibility with authoritative Google guidance and any actual Console gate before
claiming submission eligibility. No account conversion,
registration, payment, declaration submission or review submission is authorized
by this document.

## Remaining Owner Decisions and Evidence

1. Confirm the legally responsible operator/entity, privacy contact and mailbox
   control/delivery. The existing display name and address are not an attestation.
2. Establish the applicable legal bases and necessary disclosures/consent for
   health/sensitive data and optional images. Body-AI consent alone is insufficient
   evidence for every purpose. Set the final audience, minors/guardian process,
   Play target age and health declarations consistently. Initial 18+ targeting is
   now owner-approved; self-reported age input is not identity/age verification.
3. Confirm actual providers, recipient legal entities, processing countries,
   transfer mechanisms/timing, subcontractors, contracts, purposes and safeguards.
   `R2_REGION=auto`, a database brand, and `store=False` do not prove geography,
   legal transfer terms, no training, zero retention or deletion of all copies.
4. Set and verify retention by category: records/results/events, photo bytes and
   metadata, auth data, deletion ledgers/object keys, support emails, provider logs
   and backups. Identify any genuinely applicable statutory retention before
   specifying it. No fixed legal retention period is invented here.
5. Verify image TTL configuration and deployed scheduler authentication, repeated
   execution, failures/retries and readback. Verify account acceptance, guarded
   writes, identity deletion and real storage sweeps separately. R2 deletion
   remains pending until verified revocation/drain/lifecycle; a successful DELETE,
   expired URL, logout or deleted Auth identity is not full-erasure proof. No
   deletion deadline or finite grace period is established by the current source.
6. Operate a safe rights-request/identity-verification process and decide response
   timing, scope, escalation and email retention. Do not request passwords, OTPs,
   tokens, API keys or original body photos by email. A sender address alone is
   not account ownership proof.
7. Provision and test reviewer access separately using a dedicated account with
   synthetic data. Put actual credentials and any additional access instructions
   only in Play Console's private app-access surface, never these pages, this
   document, fixtures or source control. Do not assume successful login, verified
   email ownership or MFA exemption. No account was provisioned in this task.
8. Preserve the owner-selected existing Personal closed-test draft route. Resolve
   any actual account-specific eligibility gate before claiming approval or
   release; account conversion remains unapproved. Health/fitness coverage and
   nutrition functionality are not an approved exemption. Review final policies,
   Data safety, health declarations and actual app behavior together before release.

## Verification

Use the existing venv, with imports explicitly bound to this release worktree:

```sh
PYTHONPATH=/private/tmp/cal-ai-play-20261109/services/api /Users/dd/Documents/cal-ai/services/api/.venv/bin/python -m pytest /private/tmp/cal-ai-play-20261109/services/api/tests/test_public_pages.py -q
```

The focused tests cover public access even with auth enabled/misconfigured,
document metadata defaults/overrides and invalid-input fallback, document
structure/security headers, no secret/request reflection or account side effects,
honest sensitive-data/provider/age disclosures, example-only TTL, R2 pending
semantics, private reviewer credential handling and unresolved Play account gates.

Verification on 2026-11-10:

- Baseline public-page suite: 6 passed before edits.
- Updated public-page suite: 39 passed (included in the combined run below).
- Related account deletion, cleanup worker, release auth and release analytics
  tests ran together with the public-page suite: 163 passed in 5.99 seconds, with
  isolated local data and provider fixtures. They are not live provider or erasure
  evidence.
- Whitespace checks on all three owned files emitted no diagnostics. These files
  were already untracked or newly added, so checks used `git diff --no-index
  --check /dev/null <path>` (difference exit status 1, no whitespace errors).
- Existing Starlette TestClient/httpx deprecation warning remains. No dependency
  was added or upgraded to address it.
- Ruff is not installed in the existing venv (`No module named ruff`); lint was
  not run. No browser/device rendering or live operational check was performed.
- No production deployment, commit, push, cloud writes, new dependency or
  persistence/deletion logic change is part of this work.
