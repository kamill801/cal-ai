# Android Play readiness and deployed QA

Run: `cal-ai-play-2026-11-09`. New explicit owner request after the previous
seven-pass run closed. The old run is not reset or extended. Native Codex only.

Branch: `codex/android-play-readiness`, based on main `1edc992`. Do not merge
the equipment feature, overwrite the dirty main checkout, promote production,
accept legal declarations or publish a Play release implicitly.

Approved: name `Trust First Nutrition`; create/delete disposable test-only
application records through the user's authenticated test workflow. Do not
delete pre-existing records or the user's Auth identity. No real personal
photo transmission or paid provider calls. Provider attempt budget: 0.

Maximum passes: 7. Started: 6. Completed: 6. Phase: Pass 6 closed with source checks passing and external release gates blocked. One final repair/verification pass remains; do not consume it polling authentication.

Required matrix remains the full retained nutrition, goals, workout, body,
coaching, history, analytics/admin, auth, data lifecycle, Android and visual
coverage. Successful source/config checks do not close external gates.

| Gate | Current evidence | Required result |
| --- | --- | --- |
| Production entry/auth | Optional scopes repaired; actual Kakao login and authenticated app reload verified | Logout, review-user and Android auth remain separate gates |
| Fixtures | Synthetic profile, partial workout session, weight and wellness persist after reload | Cleanup blocked by deployed web delete no-op; fixtures remain; never erase prior data |
| Android build | SDK 54 source/config/JS export verified; EAS not logged in | Valid signed AAB, final manifest and real Android execution |
| Account deletion | Durable local/mocked source and regressions, disabled; explicit storage/SQL/provider gates | Self-only retry-safe production identity/data deletion and revoked-token protection |
| Policy/support | New local HTML routes and approved public contact, draft/not deployed | Accurate, legally reviewed data/retention notices and working deployed deletion path |
| Reviewer access | Ordinary password login source/smoke, not deployed | Real non-admin review-user login without personal OAuth or admin bypass |
| Core service | Prior source tests; not whole-service proof | Actual Vercel feature journeys and retention/design regression evidence |
| Play registration | Name/package form prepared, app not created | Owner legal review, app creation readback, accepted AAB and track status separately |

Pass 1 findings batch: Android target baseline and build config need repair;
account identity deletion is absent; public legal routes and usable review
login are absent. Planned scoped implementation across independent file sets.
Inspection batch frozen. Implement SDK baseline, complete self-account deletion,
normal password login for review access, and public policy/support/deletion
routes. Public operator/contact approved by owner: 아르케 /
`areche.ai.kr@gmail.com`. This does not attest verified legal identity, approve
the policy text, or authorize a production release.
No release readiness claim until required matrix clears.

Pass 1 implementation: SDK 54 compatible package baseline and Android config
guard; server-only, durable self-account deletion with app integration;
ordinary password login; real public HTML notices and account-deletion intent;
cross-platform explicit deletion confirmation. Operator/contact are approved,
but policy legality and external identity deletion remain unapproved/unverified.

Queued for pass 2: gallery still asks broad media-library permission before the
system picker despite the reduced Android manifest permissions. Do not repair
this during pass 1 verification. Independent review/test failures join that batch.

Pass 1 closed: 237 API tests, 13 store guard tests and shared typecheck passed.
Mobile typecheck failed on a web-only global and smoke could not locate the
now-hoisted TypeScript compiler. Independent review confirmed a pre-existing
profile deletion ownership-scope bug, client false pending state, and deletion
retry/deadline gaps. No release approval. Production Kakao navigation and a
keyless DNS check both failed resolving the configured Supabase host; the exact
project dashboard needs the correct owner account, not another project's session.

Pass 2 inspection batch: repair web intent typing, compiler resolution, system
photo picker permissions, profile-only artifact isolation and false pending UI.
Repair durable deletion resumption/bounded progress where safely possible;
presigned PUT races require an honest pending state or external lifecycle gate,
not an unproved finite grace-period guarantee. Freeze this batch before Fix.
Inspection batch frozen. Backend repair has a separate owned write set from
mobile compatibility/UX work. External auth, real providers and release stay gated.

Investigated and rejected a suspected account-switch flag defect before making
any edit: both HEAD and the working revision already mount `OwnerApp key={scope}`
with `ownerScope(auth.enabled, auth.session?.user.id)`. That remount resets the
new deletion flags as well as the existing private state. Existing session smoke
checks distinct user, signed-out and local scopes. No speculative state refactor
or extra repair pass is needed for this suspicion; native interaction stays unverified.

Queued for pass 3: current Supabase API-key documentation says opaque secret
keys belong on `apikey`, not `Authorization: Bearer`. The new raw admin request
copies either key format into both. Add a request-header regression and repair
the opaque-versus-legacy header handling after pass 2 closes. No provider call
or key rotation is authorized by this finding.

Pass 2 closed on frozen source: full API suite 259 passed / 2 failed. Both
failures repeat already-swept local object DELETEs; retain R2 re-sweeps, but
exclude completed local entries. Mobile typecheck/smoke, 14 store guards,
admin typecheck/build/six fixture checks, Web and Android JavaScript exports
passed. Native Android, real PostgreSQL, provider and deployed UI gates remain
open. Worker SQL scale, atomic fencing, R2 terminal cleanup and daily-cron
capacity are explicit disabled-feature release blockers, not passing claims.

Pass 3 inspection batch frozen: discriminating opaque/legacy admin-key header
regressions and completed-local-object selection repair. No provider calls or
configuration activation. Existing failing object-progress tests are the
regressions for the latter. Phase: Fix.

Fresh external readback: owner signed into the existing project
`nojddnajbrowtcvcjvxv` under organization `laeseopkkxsbbhbgobjt`; dashboard
explicitly showed paused. Requested Resume without upgrading the plan.
Resuming is not yet proof of healthy Auth or a completed login.

Pass 3 implementation frozen after targeted regressions: the new request-header
test first failed for opaque keys, and the existing object-progress test first
failed on a duplicate local DELETE. Both scoped repairs now pass; account
deletion plus cron targets: 61 passed, one dependency deprecation warning.
Final integration verification is running on the frozen source revision.

Pass 3 closed: full API 263 passed / one deprecation warning, shared/mobile
typechecks and mobile smoke passed, store guards 14 passed, admin typecheck,
build and six fixture checks passed, diff whitespace check passed. Independent
focused review found one native-startup regression: React Native defines
`window = global` without `location`, which the web deletion-intent initializer
dereferences during mount. Queued for the next pass, not repaired during Verify.

Pass 4 inspection batch frozen: guard a present native window without location
and add the exact native-global-shape smoke regression. External production
auth inspection also found KOE205: configured Kakao app 1561523 has disabled
nickname/photo and no email permission, while Supabase requests all three.
Supabase is now Healthy in Seoul and reaches Kakao. Provider scope changes
await action-time consent; business verification/terms remain owner-only.

Pass 4 implementation frozen: an added `window = globalThis` regression first
reproduced the native initializer crash. Guard missing browser location before
reading intent and never repeat an unsafe location dereference in a catch.
Mobile smoke and typecheck pass after the repair. Final guard/export checks
are running; a JS export is not native device proof.

Pass 4 closed: mobile smoke/typecheck, 14 store guards, fresh Web (2151 modules)
and Android/Hermes (2598 modules) exports and whitespace checks passed. Final
backend source is unchanged since pass-3 263-test verification. A narrow
source/docs key-pattern scan returned no matches; this is not an exhaustive
secret audit. No source fixes are queued from this pass. Seven-pass ceiling
retains three unused passes; do not spend them polling blocked authentication.

Checkpoint: Supabase restoration completed and read back Healthy, same ref,
Seoul/Nano, no upgrade. Actual production OAuth reaches Kakao, then KOE205
explicitly lists account_email/profile_image/profile_nickname as unconfigured.
Kakao app 1561523 is not a Biz App, has no app icon or email permission, and
nickname/photo are disabled. Supabase's Allow users without an email is already
enabled, but the actual request still includes account_email; no speculative
client-scope override was applied. Owner action-time consent requested before
enabling optional profile grants. Business verification and legal acceptance
remain owner-only. No test records or real photos were created/transmitted.

No commit, push, production deployment, EAS cloud build, AAB upload, Play app
creation, legal declaration or release submission was performed. The dirty
main checkout and equipment branch were not merged or overwritten. Continue
from this checkpoint after approved provider setup, not from an invented
successful login or completed Android/store release.

Approved provider-configuration follow-up (no additional code QA pass): owner
explicitly approved optional nickname and profile-photo consent. In Kakao app
1561523, saved `profile_nickname` and `profile_image` as optional, then read
both statuses back in the consent table. `account_email` still shows no
permission and was not changed; all other grants, credentials and billing
settings were left untouched. Screenshot:
`/private/tmp/cal-ai-kakao-optional-consent-20261109.jpg`.
Login success has not been established after this partial repair. Biz App
eligibility, icon and owner identity/terms steps remain the email-permission
gate. Pass counts remain four started/four completed, maximum seven.

## Retained-feature coverage

Pass 5 resumed and closed: all 21 icon/store regression tests now pass after
the adaptive export alpha-threshold repair. Inspected the opaque launcher and
transparent foreground visually; the test checks central-circle containment.
Shared/mobile typechecks, mobile async/API smoke, Android/Hermes export
(2598 modules), Web export (2151 modules), and diff whitespace checks passed.
Web export includes the configured favicon. These are source/artwork/JS checks,
not signed-native installation or real service E2E evidence.

External readback on resume: Kakao app configuration requires a fresh login;
the prior unsaved upload is not treated as persisted. Opened a handoff login
tab for the same app ID 1561523. EAS `whoami --non-interactive` returned
`Not logged in`. Store preflight intentionally rejects missing public auth
configuration, expo.owner and EAS project ID; it was not bypassed.

Play developer 7707482448795132061 is still ARCHE Labs / personal. Fresh home
readback shows an unrelated `com.arche.ilsang` draft and the existing UPGLOW
closed test, but no Trust First Nutrition record. Neither app was changed.
Policy/account-type applicability needs a decision before app creation; see
`docs/google-play/POLICY-CHECK-2026-11-09.md`. No conversion, legal consent,
app creation, cloud build, commit/push or production deployment was performed.

Pass 5 inspection/fix scope: owner approved creating an app icon from the
existing mascot and continuing Play registration. Add opaque launcher/store
exports, alpha adaptive foreground with explicit mask-safe placement, Kakao
icon and web favicon. Wire asset paths and add regression checks. Do not
change credentials, accept terms, create signing keys or attest compliance.
Other worktrees remain untouched. Two code QA passes remain after pass 5.

Provider follow-up after owner login (no extra code QA pass): verified Owner
access to existing Kakao app 1561523. Uploaded `kakao-icon-128.png`, clicked
Save, reloaded and visually confirmed the new mascot icon in app basic info.
Biz conversion controls are now enabled. App name/company/domain/category,
keys, consent scopes and billing were not changed. Saved-icon screenshot:
`/private/tmp/cal-ai-kakao-icon-saved-20261109.jpg`.

Opened the domestic business-number form for direct owner entry; all three
number fields were empty when handed off. No number was entered, no business
lookup submitted, no identity/terms accepted and no conversion performed.
Visible handoff screenshot (empty fields):
`/private/tmp/cal-ai-kakao-biz-owner-handoff-20261109.jpg`.
Do not record the registration number or identity information in project docs.
If the owner has no business registration, use the displayed personal-developer
route only after clarifying that choice; never invent business information.
Email permission and actual app-login E2E remain open gates.

Owner business follow-up: owner reported completing the direct setup. Read
only the consent page for exact app 1561523, which now displays the Biz App
badge. Nickname/photo remain optional. Email changed from unavailable to
configurable, but is still disabled. Opened its settings without selecting
or saving anything; requested action-time approval for optional email access
only, purpose planned as member identification/login/account management.
The missing-email collection checkbox is off and must remain off. No marketing,
friends, phone-number, message, calendar or other access was enabled.
Business registration numbers and identity data were not collected or recorded.
Approval screenshot: `/private/tmp/cal-ai-kakao-email-optional-approval-20261109.jpg`.
App OAuth success is not yet reverified. QA counts remain five/five, maximum
seven; provider setup is not an extra code repair pass or full-service signoff.

Approved email-scope follow-up: the owner explicitly authorized optional
account_email activation. Saved OPTIONAL with purpose
`회원 식별 및 로그인·계정 관리`, reopened the persisted settings, and verified
the missing-email collection checkbox remains OFF. All unrelated grants,
credentials, billing and account identity data were left untouched. Evidence:
`/private/tmp/cal-ai-kakao-email-optional-saved-20261109.jpg`.
Actual production navigation from `https://cal-ai-api.vercel.app/` now reaches
the normal Kakao consent screen with all three optional items unchecked,
instead of KOE205. Handed consent/terms completion to the owner. No authenticated
app-session success, test-record writes, paid AI calls or photo uploads are
claimed. No OAuth callback codes, tokens or transaction URLs were saved.
QA counters remain five started/five completed, maximum seven.

All rows remain required for a whole-service readiness claim; source fixtures
cannot be substituted for the missing authenticated deployed/Android evidence.

| Journey | Existing/local coverage | Current deployed/device gate |
| --- | --- | --- |
| Kakao login, session restore, logout | Auth middleware/profile tests and client smoke; optional scopes saved with approval; actual production login and session reload verified | Logout, review-user access and Android OAuth remain unverified |
| Normal email review login | New ordinary-auth helper and smoke | No disposable review user or deployed login proof |
| Onboarding and nutrition goals | Targets/onboarding API fixtures; synthetic production onboarding and goal persistence verified | Initial demo-dashboard flash repaired only in source; deployed repair unverified |
| Camera/gallery, compress, presign, direct PUT, complete | API/storage mocks and mobile contracts | Actual Android photo permissions/URI/R2 transport unverified |
| Analyze, clarify, edit nutrition, save | API/provider fixtures and reducer/client smoke | Paid provider budget 0; no final-revision real analysis proof |
| Meal history, repeat/delete, reload | Coach/API and client fixtures | No new deployed meal write/delete test or real AI proof in this run |
| Workout plan, session sets, history | Coach/product-quality fixtures; production plan, partial squat session and reload verified | Full session, Android input and cleanup remain unverified |
| Weight, wellness, body view/consent | Coach/body-provider fixtures; synthetic production weight/wellness save and reload verified | No personal photo transmission; body provider/consent and Android remain unverified |
| Progress and weekly coaching | Coach/quality fixtures | Interpretation quality and long-term user value not established by schemas |
| Billing status and separate admin analytics | API fixtures; admin typecheck and six fixture smoke checks after locked install | Real payment out of scope; isolated owner admin/telemetry flow unverified |
| Profile data deletion | Scoped isolation regressions and explicit web confirmation repaired locally | Deployed delete button produces no action/dialog; disposable fixtures remain; no prior owner data deletion authorized |
| Account identity/data deletion | New durable server-only lifecycle under repair | Disabled; provider/PG/concurrency/scheduler/storage recovery not yet proven |
| Notices, deletion link, review access | New source routes and tests | Draft policy not approved/deployed; mandatory health-data decisions remain |
| Visual consistency, keyboard, accessibility | Existing tokens/assets retained, source fixes | No final deployed responsive/Android visual signoff |
| Play artifact/track/publication | Prepared form only | No created app, signed AAB, upload, tester participation or submission |

## Pass 6: Authenticated Production And Isolation Repair

The owner completed Kakao login. On the actual production origin, created only
authorized synthetic fixtures: age 30, height 170, weight 70, maintenance,
moderate activity, beginner, gym, 45 minutes, three to four days per week.
The calculated target was 2510 kcal and 126 g protein. Created a rule-based
workout plan, then saved only the squat portion (two sets, eight reps, 20 kg).
The persisted session volume was 320 kg. Reload retained the session, goals,
70.2 kg weight and one wellness entry. These are web/provider-persistence
checks, not native Android, complete-workout, meal analysis or AI-quality proof.
A partial one-of-four-exercise session does not count as a completed workout;
the weekly completed-workout count of zero was not treated as a defect.

The deployed data-delete button produced no visible transition or browser
dialog. Cleanup did not occur: the synthetic profile, plan, partial session,
weight and wellness records remain. No owner Auth identity or prior data was
deleted, no photos were transmitted and no paid provider calls were made.
The branch's explicit cross-platform confirmation is not deployed. Do not
claim a successful production create/read/delete journey.

Two source repairs were frozen and verified in this pass. The initial dashboard
now waits for owned data instead of briefly showing demo meals; error/retry,
onboarding, background refresh and safety routes stay accessible. Account-wide
artifact deletion now excludes uploads still referenced by retained foreign
jobs or body events, following the existing profile-only isolation pattern.
Four new regressions failed before that repair. No deletion activation flags
or external lifecycle settings were changed.

Fresh verification: full API 267 passed / one dependency deprecation warning;
deletion target 61 passed; shared/mobile typechecks and mobile smoke passed;
store/icon guards 21/21 passed; web export (2143 modules) and whitespace check
passed. Independent review found no new actionable issues in these two changes
and exercised ten isolated shared-upload cases. PostgreSQL fencing, stage-0
scale, R2 terminal cleanup, scheduler throughput and real provider deletion
remain disabled-feature release blockers.

Reused only the four approved public mobile auth/API fields from the existing
configuration in child processes without printing values. Store preflight now
fails only on absent EAS owner and project linkage; no public-key re-entry is
needed. Fresh EAS whoami still returned Not logged in. The owner reported a
sole proprietorship, not independent legal verification or a request to convert
the existing personal Play account. Prepared Play's app/free/Korean/name/package
form and verified package availability. Policy/export boxes remain unchecked;
Create was not clicked. Availability does not reserve the package.

Evidence: `/private/tmp/cal-ai-production-workout-test-20261109.jpg`,
`/private/tmp/cal-ai-production-workout-reloaded-20261109.jpg`, and
`/private/tmp/cal-ai-play-create-prepared-20261109.jpg`.
No commit, push, production deployment, signed AAB, upload, legal acceptance,
review submission or public release was performed. One pass remains reserved
for a final authorized repair/deployed-or-native verification batch.

EAS setup follow-up, not an extra QA pass: the owner chose the retained native
app plus cloud-build route. The existing Google-authenticated Expo onboarding
produced organization `arche-trustfirstnutrition` and project
`trust-first-nutrition`, both read back in the live dashboard. Actual Billing
shows Free / $0 per month, upcoming $0 and no builds. The public project UUID
from Expo's visible connection command was added to app.json with the confirmed
organization owner. OAuth is restricted to this organization with Developer
role and awaits owner approval; the agent did not approve it. No keystore,
source archive, APK/AAB, paid plan, store upload or production change occurred.
With the existing four whitelisted public settings, store preflight now passes.
The isolated hook regression previously assumed the real app would remain
unlinked and expected missing owner/project diagnostics. After legitimate EAS
linkage that assumption failed; it now asserts the intentionally absent auth
fields instead. The independent missing-owner/project fixture remains covered.
This is a narrow setup-test adjustment, not another whole-service QA cycle.

## EAS Packaging Follow-Up: 2026-11-10

Owner-completed OAuth is now confirmed by fresh CLI identity: this organization
only, credentials limited to Developer. Project readback matches the recorded
UUID. Configured and independently compared four whitelisted public client
fields in project-only preview/production environments with values suppressed.
Sensitive display does not turn client configuration into a server secret.

Root `.easignore` and regression coverage now exclude private files, server/admin
sources and QA material while retaining mobile/shared build inputs. Official
local archive inspection found 77 files, no symlinks, no forbidden files, no
missing required inputs, and no matches for targeted private-key patterns.
Store/icon/archive tests pass 22/22 and whitespace checks pass. This setup check
does not reset the QA counters or substitute for a deployed journey.

No existing Android signing credentials were configured. The owner explicitly
approved creation/storage of this app's dedicated EAS keystore and free APK
build. EAS reported key creation and source upload (5.1 MB), then accepted build
`e8741dcd-a358-44f0-8efa-8fa07a55f9aa`; fresh status IN_PROGRESS. No key/password
was exported, no paid upgrade or provider call occurred, and no Play app,
submission, production deployment or legal acceptance was completed. Artifact
and Android runtime proof remain pending; production synthetic records and
all provider/deletion/policy gates are unchanged.

## Pass 7: Actual Android Artifacts And Permission Repair

Started and completed 2026-11-10 as the final batch under the maximum seven
passes. Do not start an eighth loop or treat this as whole-service signoff.

The first cloud APK finished and was downloaded/inspected rather than equating
EAS project configuration or JS export with a native binary. It retained
unnecessary SYSTEM_ALERT_WINDOW, USE_BIOMETRIC, USE_FINGERPRINT and VIBRATE
permissions plus unscoped WRITE_EXTERNAL_STORAGE. Removed the four unused
permissions and added an idempotent config plugin limiting legacy camera
storage to API 28. Installed SDK 54 ImagePicker requires that permission only
on API 24-28, so blanket removal would regress supported old devices. Added
regressions for the plugin, preserved camera permission, archive inclusion,
environment profile selection and blocked permissions.

Rebuilt APK and Play AAB with frozen existing remote credentials, not another
keystore. Both official EAS build IDs are FINISHED:

- APK: `3eeb8b00-bf3f-4d2b-bf55-8097c42918f8`.
- AAB: `96f4e5a6-d7ec-4870-9af7-c6a1ac2b0777`.

Actual downloaded manifests match intended package, version 0.1.0/code 1,
target SDK 36, disabled backup/debugging and minimal permission policy. Both
ZIP CRC checks and expected certificate metadata pass. Official Google
bundletool 1.18.3 validates the AAB; its config requests PAGE_ALIGNMENT_16K.
All 28 64-bit libraries in each artifact have PT_LOAD alignment at least 16 KB
and correct offset/address congruence. This is static evidence, not a zipalign
tool, cryptographic-signature or real 16 KB device check. No Android runtime,
native OAuth/camera/gallery/R2 transport or paid provider success is claimed.

Fresh source checks after repair: 23 store/icon/archive/permission tests,
mobile/shared typechecks, mobile smoke, native Expo config assertions, hardened
77-file archive path checks, and whitespace validation pass. Temporary binary
inspection tools do not alter app dependencies or install Android Studio.
No server secret, private signing key or password was exported. Build record,
hashes and test/install links: `docs/google-play/ANDROID-ARTIFACTS-2026-11-10.md`.

The initial APK is superseded and must not be shared as the final tester APK.
No commit, push, production deployment, Play creation/upload/submission, policy
acceptance, paid upgrade or extra QA loop occurred. The production synthetic
records still remain; real deletion/storage/worker/policy/reviewer/device and
Play-account eligibility gates are unchanged. Result: seven completed out of
seven; whole-service/public-release readiness remains blocked.
