# Trust First Nutrition: Play release gates

Prepared 2026-11-09 on `codex/android-play-readiness`, from main `1edc992`.
The separately implemented equipment-photo feature is not included. This is a
full-product release preparation branch, not a change to the product's scope.

## Latest checkpoint - 2026-11-11

This section supersedes older progress snapshots below, not their evidence.
The owner explicitly declined developer-account conversion and chose the
existing ARCHE Labs Personal account with closed testing. Do not convert or
create a paid account. Prepare truthful draft declarations; any actual
account-specific Google eligibility gate remains separate from draft preparation.

Initial 18+ targeting is approved. New source API/mobile onboarding accepts
self-reported 18-100; public source drafts are aligned. This is not verified age.
Known-underage owners are blocked from feature APIs in local source, with
privacy/deletion/logout preserved. Local allowed-origin CORS and real isolated
PostgreSQL checks passed. This source is now deployed; authenticated production
age-error behavior has not been retested after promotion.

Same-origin staged deployment `dpl_2zshhCd7NWGgk7pGFpJsxsybh2Xn` repaired the
reviewer's cross-origin profile failure. Fresh login, synthetic profile/target
save, reload restoration, workout plan and partial session save passed. Normal
reviewer data remains; effective admin rejection is not independently verified.
AI is mock, deletion flags are false, and no production alias was assigned.

New mobile source fixes confirmed-save reset independently of refresh, read-only
refresh retry without duplicate POST, and delayed recommendation defaults while
preserving edits. Independent bounded review is clear; mobile smoke19 and
store24 tests, both typechecks, API460 (1 optional-PG module skip) and real local
PostgreSQL7 passed. The first two Nov11 queued rebuilds were cancelled before
artifact creation. Replacement current-source APK/AAB are FINISHED and downloaded;
manifest/permissions, ZIP CRC, bundletool and 16 KB static checks passed. Actual
cryptographic signature verification, Play-generated splits and Android runtime
remain separate gates; see `ANDROID-INSPECTION-2026-11-11.md`.

The owner completed creation acknowledgments and created the Play app. App ID
`4975788258134910868` is verified under the unchanged Personal account. Eight
draft declarations are saved: no ads, no advertising ID, not government, no
financial features, fitness/nutrition/sleep-quality health features, reviewer
login details, 18+ audience and content rating. The owner entered and saved the private review
password/access attestation; only the separate overview completion status was
read, not the credential form. The 18+ target and known-minor discovery,
download and purchase restriction show a saved confirmation. The owner reviewed
IARC terms and pressed Start; questionnaire answers and the completed rating were
saved (Korea3+/PEGI3/ESRB Everyone, separate from 18+ targeting). Privacy and Data
safety remain. Data safety is only a partial saved draft: collection/encryption
yes and OAuth creation; deletion URL is not entered and no final submission exists. No AAB
upload, closed-test opt-in or app review submission exists.

After explicit owner approval, latest source snapshot
`dpl_83W5jnu5m8XZMKfMfPRRWLAxw8UH` is READY and promoted to
`https://cal-ai-api.vercel.app`. Exact project and canonical alias were read back.
Nine unauthenticated GET probes passed: health/readiness, four real policy
documents, profile/admin access rejection and disabled deletion-worker response.
Public document headings, technical-draft notices, public contact and security
headers were checked; browser privacy and login rendering also passed.
Food AI remains openai and body AI mock. No paid analysis, new authenticated
record test, storage erasure, deletion migration or worker activation occurred.
All three deletion/worker/write-once flags are explicitly false. This is a
deployed uncommitted branch snapshot, not a main merge or committed Git release.
See `PRODUCTION-DEPLOYMENT-2026-11-11.md` for bounded evidence.

Policy text, deployed deletion/storage/retention evidence, actual Android QA,
truthful declarations and real tester participation remain release gates. The
previous whole-service QA run remains 7/7 with readiness blocked; targeted fixes
do not reset that counter. See `FOLLOWUP-2026-11-11.md` for exact evidence.

## Approved public contact

- App name: Trust First Nutrition.
- Operator display name: 아르케.
- Per-app support email: areche.ai.kr@gmail.com (exact owner-provided spelling).
- A per-app public support address need not be the Google account login. The
  verified legal developer identity remains separate and must be accurate.
- Mailbox delivery/ownership, actual legal entity details and required public
  legal information have not been independently verified.
- The owner reports operating as a sole proprietor. The Console still shows
  a personal developer account; neither that report nor paid-app support is
  by itself an account-type eligibility determination or conversion approval.

## Public documents, not legal approval

The new API HTML routes are `/privacy`, `/terms`, `/support`, and
`/account-deletion`, routed before the Vercel SPA fallback. Login and privacy
screens link to them. Public production rendering is now verified, but the
documents explicitly remain technical drafts, not approved legal policies.

Owner review is still required for the actual legal operator, policy effective
date, purposes and lawful bases, required/optional health-data consent,
processors versus third-party sharing, overseas-transfer recipient/country/
items/purpose/timing/method/retention/refusal details, actual photo TTL and
cleanup failures, minimum account-deletion tombstone retention, backups,
analytics/admin audit retention, complaint routes and any statutory retention.
Do not submit the draft as legally complete or check a compliance declaration
merely because these routes return HTTP 200. Obtain qualified review where needed.

No claim is made that account deletion cancels an external subscription,
deletes a Kakao identity, erases all backups, or guarantees a deletion time
that has not been operationally tested. Do not request photos or secrets by email.

## Technical release gates

| Gate | Evidence required before passing |
| --- | --- |
| Authenticated deployed app | Owner Kakao login; disposable scoped fixture creation, persistence/reload and cleanup |
| Account deletion | Backend tests and client confirmation; disposable PostgreSQL trigger/migration/concurrency test; authorized disposable Supabase identity/storage lifecycle test, not owner's identity |
| Review access | Ordinary non-admin Supabase email/password user, credential delivery only through approved secret handling, real login on deployed build |
| Android | SDK-compatible dependencies, permissions, signed AAB/manifest inspection, Android installation and camera/gallery/login/upload behavior |
| EAS | Owner CLI login, verified project/owner linkage, existing signing credentials reused or separately approved creation |
| Play app record | Owner review/acceptance of required policy/export declarations; creation readback and assigned package/app identity |
| Store content | Real app screenshots and truthful description; data safety, health, content rating, audience, ads/payment and app-access answers grounded in the final deployed app |
| Testing and launch | Actual account-specific track requirements, genuine tester participation and feedback; separate approval for submission/public launch |

The new password login uses normal Supabase `signInWithPassword`. There is no
embedded reviewer password, privileged role, service key, or auth bypass. A user
must be created/managed through the correct Supabase project's existing secure
account flow. Do not enable public sign-up or loosen redirect allowlists just
to pass review. Personal OAuth alone is not adequate reviewer-access evidence.

## Safe next sequence

1. Complete local branch verification and independent review without changing
   the current production service or the dirty main worktree.
2. Repair the verified Kakao KOE205 consent mismatch after owner approval:
   app 1561523 has optional nickname/photo saved. The owner completed business
   setup and the same app now visibly carries the Biz App badge. The saved
   icon remains applied. After explicit action-time owner approval, saved
   account_email as optional for member identification/login/account management.
   Reopened the settings and verified optional consent, the saved purpose, and
   missing-email collection OFF. No marketing or unrelated grants were enabled;
   no credentials changed. Actual production OAuth now reaches the normal Kakao
   optional-consent screen instead of KOE205. The owner completed login;
   authenticated production onboarding, session restore, synthetic partial
   workout, weight and wellness persistence are now verified. Cleanup remains
   blocked: the deployed web delete button produces no action/dialog. Test
   fixtures remain, and the branch's confirmation repair is not deployed.
   Supabase's Allow users without an email is already enabled, but the observed
   request still asks for email; do not claim a client override fixes this.
   EAS CLI login is still required once; no repeated Kakao setup is needed.
3. Validate the account lifecycle against disposable provider data and the
   actual PostgreSQL engine, with explicit authority for each external effect.
4. Approve policy text and exact release/configuration scope; deploy and read
   back the precise revision/URLs before updating Play declarations.
5. Build/inspect a signed Android artifact and test Android behavior; only then
   upload a draft/test release in the approved Play app.

## Official references

- [Developer contact details](https://support.google.com/googleplay/android-developer/answer/13628312?hl=en)
- [Target API policy](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en)
- [Account deletion requirements](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en)
- [Expo SDK 54](https://expo.dev/changelog/sdk-54)
- [Password login](https://supabase.com/docs/reference/javascript/auth-signinwithpassword)

These references explain requirements; they are not proof this app has passed
Play review, provider E2E, or legal compliance.

Resume evidence: icon/store tests 21/21, shared/mobile types, smoke and fresh
Android/Web JavaScript exports passed. Signed AAB remains absent. The actual
store preflight, with the four existing whitelisted public auth/API settings,
now fails only on missing EAS owner/project linkage. Do not disable it to start
a build or ask the owner to re-enter available public values. Fresh Play home
readback confirms a personal
developer account and no Trust First Nutrition record. Review the account-type
policy ambiguity recorded in `POLICY-CHECK-2026-11-09.md` before app creation;
do not automatically convert the account or register another paid account.
Pass 6 additionally passed 267 API tests, 61 deletion-target tests, mobile smoke,
both typechecks, 21 store/icon tests, independent narrow review and web export.
These do not close real PostgreSQL/provider deletion, retention or Android gates.

EAS follow-up: owner approved retaining React Native and EAS cloud builds.
Created and read back organization `arche-trustfirstnutrition` and project
`trust-first-nutrition`; the live Billing page shows Free / $0 per month and
zero builds. Wrote only the observed public owner/project UUID to app.json.
Official CLI OAuth is prepared for this organization only with Developer role
and awaits the owner's Approve action. No personal-account access, billing
upgrade, signing-key creation, source upload or cloud build was performed.
Do not confuse a configured project ID or passing local preflight with CLI
authentication, signing credentials, a built artifact or Play registration.

2026-11-10 follow-up supersedes the earlier pending CLI/signing observations:
the owner completed scoped OAuth, and fresh CLI identity plus project readback
match this organization/project. The four public mobile settings are configured
and independently matched in project-only preview/production environments.
After explicit key-creation/storage approval, EAS created this app's dedicated
Android keystore and accepted preview build
`e8741dcd-a358-44f0-8efa-8fa07a55f9aa`, observed IN_PROGRESS. The targeted
77-file archive check and 22 store/icon/archive tests passed. No private key or
server credential was exported. A running build is not APK/AAB, Android runtime
or Play acceptance evidence. All unrelated deletion, policy, reviewer-access,
production-repair and device gates above remain open.

Final 2026-11-10 artifact evidence supersedes the IN_PROGRESS/absent-AAB notes:
the first APK is superseded after actual manifest inspection. Final APK
`3eeb8b00-bf3f-4d2b-bf55-8097c42918f8` and AAB
`96f4e5a6-d7ec-4870-9af7-c6a1ac2b0777` are FINISHED and downloaded. Both use
the same approved app-specific EAS key; unnecessary permissions are removed,
legacy camera storage is API-28-only, target SDK is 36, and package/version and
certificate metadata match. Official bundletool validates the AAB; its config
requests 16 KB native packaging and 28 64-bit libraries in each artifact pass
static ELF alignment checks. Store tests are now 23/23. No Android runtime,
cryptographic-signature or zipalign-tool proof, Play upload/acceptance, public
release or production repair is implied. See `ANDROID-ARTIFACTS-2026-11-10.md`.
The seventh/final QA pass is complete with whole-service readiness still blocked.
