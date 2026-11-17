# Kongbi Android And Play Registration: 2026-11-17

Scope: rebuild the approved Kongbi character/icon Android app, provide the owner
an installation link, and continue the existing Play registration drafts. This
does not authorize Play distribution/review, a paid plan or AI test, general-user
erasure, retention activation, account conversion, or legal attestations.

## Source And Repair

- Branch `codex/kongbi-mascot-20261116`; build source
  `434bda1acbb037c4ac88221aa761b5b62064545c`, pushed to the same remote branch.
  The dirty main and other feature/release worktrees were preserved, not merged.
- Version `0.1.2`, versionCode `4`, package `com.trustfirstnutrition.app`.
- First code3 builds completed but the cloud Doctor log exposed duplicated
  native packages: SVG 15.12.1/15.15.5 and three copies of Expo constants 18.0.14.
  Code3 is superseded; it is not the current owner test artifact.
- Hoisted the already locked mobile SVG 15.12.1 and identical constants
  18.0.14 into single root installations. Existing resolved URLs/integrities and
  manifest constraints were preserved; no new dependency or SDK upgrade.
  Normal `npm dedupe` could not resolve registry metadata, so the bounded
  lockfile relocation was independently validated by a clean offline `npm ci`.
- Regression checks assert single locked installations and identical resolution
  from the mobile app and the actual native-library consumers. All 59 store
  tests, 39 mobile smoke regressions, shared/mobile types, diff checks, and
  Android autolinking verification passed. An independent native Codex review
  found no actionable issue and explicitly did not claim device execution.
- Expo's [monorepo guidance](https://docs.expo.dev/guides/monorepos/) explains
  why duplicated native packages should be deduplicated.

## Cloud Build Boundary

- Existing EAS owner `arche-trustfirstnutrition`, project
  `cd7254d2-d859-4992-8063-7f2492ba8351` reverified. Existing app-specific remote
  signing identity reused with frozen credentials; no key/password export.
- Billing readback: Free, $0/month, upcoming estimate $0. Android usage was
  7/15 before code3 and 9/15 before the corrective code4 requests. No upgrade,
  payment method, paid add-on or new service was selected.
- After completion, billing showed 11 Android builds used (11/30 total with
  zero iOS builds), still Free and an upcoming estimate of $0.00.
- Code4 archive: 80 files, no forbidden environment/server/credential/source-
  artwork paths or symlinks, and all 12 required inputs matched source hashes.
  This is targeted archive validation, not a universal security certification.
- The seven context-specific poses and launcher/adaptive artwork are bundled;
  their inclusion does not prove their physical-device rendering.

## Final Artifacts

Both builds finished on November 17 from the code4 archive. The first code3
artifacts are superseded and should not be used for the owner's current test.

| Artifact | Final build | Size | Completed (UTC) |
| --- | --- | --- | --- |
| [Install APK](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/0ed6f218-7210-4ecf-9238-c522fa669bed) | `0ed6f218-7210-4ecf-9238-c522fa669bed` | 68,154,085 bytes | 06:31:12 |
| [Play AAB](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/b09ec8ec-59bf-4c02-b85b-7cb6a6bfd6e0) | `b09ec8ec-59bf-4c02-b85b-7cb6a6bfd6e0` | 46,552,674 bytes | 06:31:28 |

- APK SHA-256: `498671c938b368c00ec74a6ce657bdfefb14bb39513fba8929a0f68b20259112`.
- AAB SHA-256: `062115384b7db184b55434a82b525d94c80c572be697985692f7e3965e6fb9a9`.
- Cloud Expo Doctor: **18/18, no issues detected**, following native dependency
  deduplication. APK page shows Succeeded and `0.1.2 (4)`; its Install dialog
  exposes the final link and QR. Availability showed 13 days at readback;
  this is not a permanent artifact-hosting promise.
- Actual ZIP CRC, manifests, package/version, min SDK 24, target SDK 36,
  backup disabled, non-debuggable state, 56 native payloads and their 16KB
  alignment gates passed. Official bundletool 1.17.2 `validate` exited zero.
- Official apksig 8.9.1 verified APK v2 with zero errors/warnings. AAB signed
  contents verified by reading all entries: 764 signed payload entries, zero
  unsigned entries, expected certificate. This is not a strict public-PKI
  certificate-trust or real Play-generated split/device verification claim.
- Expected certificate SHA-256:
  `C797C7DA080CB65B82BFB6789E7BADEA9AAA6660A3078205FE9955063244009F`.
- All seven bundled poses have exact source dimensions, alpha and visible RGB
  pixels in both binaries. AAPT changed only invisible RGB beneath alpha zero
  in meal/workout. Extracted launcher visually shows the approved green Kongbi.
- Binary payload contains canonical API/Supabase hosts and consent routes and
  fields. Policy version is loaded dynamically, not a hardcoded literal; static
  checks alone do not prove authenticated device consent behavior.
- Machine evidence: `assets/kongbi-android-verification-20261117.json` and
  `assets/kongbi-bundled-artwork-20261117.json`. Install proof:
  `assets/expo-kongbi-apk-install-20261117.jpg`.

## Play Draft Work

- Exact existing ARCHE Labs Personal developer `7707482448795132061`, app
  `4975788258134910868`. No new app/account, account conversion or tester
  invitation was created.
- Kongbi 512px icon uploaded, saved as the single listing icon, then reloaded
  and reopened with the new November 17 upload date. The former listing icon
  remains recoverable in the asset library. Proof:
  `assets/console-kongbi-icon-saved-20261117.jpg`.
- Replaced the former character in the feature graphic using the built-in image
  editing tool and the approved Kongbi meal reference. The original graphic is
  preserved. New 1024x500 PNG was uploaded, selected as the single listing
  graphic, saved, then independently reloaded and reopened with November 17
  upload date. Proof: `assets/console-kongbi-feature-saved-20261117.jpg`.
  Source prompt: `KONGBI-FEATURE-GRAPHIC-PROMPT-2026-11-17.md`.
- Final code4 AAB was accepted as `4 (0.1.2)`, min SDK 24 / target SDK 36.
  Superseded code3 was removed only from the existing internal draft, not its
  recoverable artifact library. Saved `0.1.2 - Kongbi validation` and Korean
  notes, then independently reloaded and verified that only code4 remained.
  Proof: `assets/console-code4-draft-saved-20261117.jpg`. No release or review
  action was taken; the internal track still requires testers and distribution.
- Data safety remains a **partial saved draft**, not a final declaration.
  The deletion URL is now `https://cal-ai-api.vercel.app/account-deletion`.
  Ten source-supported collection candidates were selected: name, email,
  user ID, other personal information, health, fitness, photos, app interactions,
  other user-generated content and diagnostics. No financial/location/contact/
  advertising collection was invented. Session-ID classification and final
  sharing, processing, purposes and optionality need final reconciliation.
- Account creation remains OAuth-only: source has reviewer email/password
  **sign-in**, not a public email/password signup. No false signup method added.
- Setup still has Data safety and genuine Android screenshots outstanding.
  A draft save is not policy approval or review submission.

## Owner Device Check

1. Open the final APK link on an Android phone, tap **Install**, and install the
   APK. It is a standalone preview, not Expo Go; no Metro server is needed.
   Check version 0.1.2/code4 and the new Kongbi launcher. If an older signed
   build is installed, try the normal update first; do not erase app data merely
   to bypass an unexplained installation error.
2. Test Kakao login and the health disclosure. Confirm choices start unchecked
   and optional usage analytics can stay off. Use only the tester's own account
   and data, not another person's photos or health information.
3. Set an adult goal, choose a food photo from the gallery, then take one with
   the camera. Verify compression/upload, analysis, correction, save, daily
   totals and restore after fully closing/reopening. Live food AI analysis may
   consume the existing API budget; no paid analysis was run by this build job.
4. Record one workout set/session and verify reopen/history. Check Android
   back navigation, keyboard, permission-denial recovery and Korean wrapping.
   Check the meal, analysis, workout, progress, coach and celebration poses.
5. Capture at least two genuine final-build Android screenshots without private
   details: today's dashboard and a synthetic/test meal result or workout view.
   Store phone screenshots must satisfy the Console's displayed dimensions and
   size rules. Web/generated marketing mockups are not substituted for them.

Body-photo provider remains mock. General account-deletion acceptance/workers,
write-once migration and automatic retention remain disabled. Their intentional
guards are not a claim that ordinary-user deletion/retention has been enabled.
Do not erase a real account or test general cleanup under these build steps.

## Remaining Release Gates

- Physical Android test result and authentic final screenshots from the owner.
- Enforceable retention/erasure policy, processor/country/contract facts and
  deletion fulfillment responsibilities; then truthful final Data safety and
  privacy declarations. Confirmed operator/contact facts are not asked again.
- General deletion/retention activation requires its separate approved rollout;
  earlier bounded lifecycle verification is not general activation authority.
- Personal health-app eligibility remains unresolved; do not convert the
  account, hide app functionality or claim a policy exemption.
- Play closed testing is not running. Current Console showed zero participants.
  Its required 12 continuously opted-in testers for 14 days is separate from
  direct APK testing; see [Google's testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en).
- Final distribution/review submission and legal acceptance remain human gates.

The production web/API already had the approved Kongbi UI before this Android
build. No production redeployment, environment/key mutation, user-data change,
cloud deletion or paid AI call was performed in this follow-up.
