# Android Beta Readiness

Updated: 2026-11-09. One bounded local dependency/configuration verification batch in `/private/tmp/cal-ai-play-20261109`, branch `codex/android-play-readiness`. This is not a release approval, native build, AAB, signing or device result. Other agents' source changes are outside this batch's ownership.

## App Identity And Build Boundary

- Display name: `Trust First Nutrition`.
- Expo slug: `trust-first-nutrition`; URL scheme: `trustfirstnutrition`.
- Android package: `com.trustfirstnutrition.app`. Preserve this permanent intended Play identity.
- Local app version: `0.1.0`; Android `versionCode`: `1`.
- `apps/mobile/eas.json` retains `cli.appVersionSource: local` and development/preview APK plus production `app-bundle` profiles. It was already configured this way and is unchanged.
- Production API origin remains `https://cal-ai-api.vercel.app`; this batch does not prove its runtime readiness.
- EAS is not logged in, as reported at handoff. Account state was not queried, credentials were not read, and no login, project creation/linking, signing, cloud build or upload was attempted.
- `expo.owner` and `expo.extra.eas.projectId` remain absent because their approved values are unknown. Do not invent them.

Those two account/linkage statements describe the initial dependency batch,
not the later account setup. See the follow-up below for current EAS evidence.

## Pinned SDK 54 Baseline

The published Expo `54.0.38` package's `bundledNativeModules.json` was read before editing and checked again from the installed package. React Native `0.81.5` is its exact baseline, not an independently selected newer RN patch. SDK 54/RN 0.81 defaults to Android compile/target API 36; final binary values still require inspection.

| Package | Exact version |
| --- | --- |
| `expo` | `54.0.38` |
| `react`, `react-dom` | `19.1.0` |
| `react-native` | `0.81.5` |
| `react-native-web` | `0.21.0` |
| `@expo/metro-runtime` | `6.1.2` |
| `@react-native-async-storage/async-storage` | `2.2.0` |
| `expo-auth-session` | `7.0.11` |
| `expo-image-manipulator` | `14.0.8` |
| `expo-image-picker` | `17.0.11` |
| `expo-secure-store` | `15.0.8` |
| `expo-status-bar` | `3.0.9` |
| `expo-web-browser` | `15.0.11` |
| `react-native-svg` | `15.12.1` |
| `@types/react` (root/mobile) | `19.1.10` |
| `typescript` (mobile) | `5.9.2` |

Root `overrides` and root development copies of React, React DOM and React Native match the mobile versions. AsyncStorage moves from the previous unsupported `^3.1.1` range back to Expo's native-compatible `2.2.0`; this is an intentional compatibility alignment. Other direct libraries are unchanged; no new direct library was added. The root lockfile was regenerated with lifecycle scripts, audit and funding calls disabled. Transitive deprecation warnings for `glob`, `inflight` and `rimraf` were observed; no security audit was run and vulnerability clearance is not claimed.

Local tools: Node `24.15.0`, npm `11.12.1`. RN 0.81's minimum Node version is `20.19.4`; separate dependencies can impose a higher minimum. No native JDK, Gradle, Android SDK or NDK build was exercised.

Official sources checked for this batch:

- [Expo SDK 54 release notes](https://expo.dev/changelog/sdk-54).
- [Expo SDK 54 compatibility table](https://raw.githubusercontent.com/expo/expo/sdk-54/packages/expo/bundledNativeModules.json); the installed `54.0.38` artifact was authoritative for these pins.
- [React Native 0.81 Android 16 and toolchain changes](https://reactnative.dev/blog/2025/08/12/react-native-0.81).
- [Expo permission removal configuration](https://docs.expo.dev/guides/permissions/).
- [SDK 54 ImagePicker API](https://raw.githubusercontent.com/expo/expo/sdk-54/packages/expo-image-picker/src/ImagePicker.ts) and [config plugin](https://raw.githubusercontent.com/expo/expo/sdk-54/packages/expo-image-picker/plugin/src/withImagePicker.ts). The versioned documentation URL redirected to current/latest docs, so SDK-specific behavior was checked in SDK 54 source and the installed package instead.

## Permissions And Backup

Explicit product permission: `CAMERA`, for meal/body photo capture. The existing Korean camera/photo rationales are preserved. `microphonePermission: false` disables the ImagePicker microphone permission, including its unused iOS microphone rationale.

Blocked package/plugin permissions:

- `android.permission.RECORD_AUDIO`.
- `android.permission.READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO`, `READ_MEDIA_AUDIO` and `READ_MEDIA_VISUAL_USER_SELECTED`.
- `android.permission.READ_EXTERNAL_STORAGE` and `MANAGE_EXTERNAL_STORAGE`.

Android system image selection does not require broad library reads. Do not add read permissions merely to satisfy a runtime permission preflight. The source owner must make the Android gallery flow open the system picker directly without first calling `requestMediaLibraryPermissionsAsync()`.

Legacy-camera exception: `WRITE_EXTERNAL_STORAGE` is not blocked. Installed `expo-image-picker@17.0.11` calls `ensureCameraPermissionsAreGranted()` and explicitly requires it below Android API 29. SDK 54 supports API 24 onward; blanket removal would break camera capture on Android 7-9. Retaining this dependency-required permission is not approval for broad storage access. Its final manifest declaration and runtime behavior need review on old and modern devices before release. Raising minimum OS or replacing camera implementation is a separate product/native decision, not a silent configuration change.

Android `allowBackup` remains `false` so the AsyncStorage profile identity is not restored from device backup. Expo config introspection verified it and all seven permission-removal directives. The introspected template also contains `INTERNET`, `VIBRATE`, `SYSTEM_ALERT_WINDOW`, `CAMERA` and the retained `WRITE_EXTERNAL_STORAGE`. This is not a final merged release manifest: inspect the actual AAB, including whether development-only template entries remain.

## Fail-Closed Store Guard

Ported `apps/mobile/scripts/check-store-build.mjs` and its regression tests from the equipment worktree without modifying that worktree. Mobile scripts now expose `check:store`, `test:store` and the `eas-build-pre-install` hook. The hook checks Android production builds before dependency installation and skips preview/iOS builds.

The guard requires HTTPS API/auth origins, Supabase auth, a public client key (never a server secret/service-role key), approved EAS owner/project, intended package, positive local version code and an API-36-capable Expo baseline. Diagnostics do not echo supplied values. Additional tests pin the installed dependency table/root overrides, identity/backup/permissions and hook behavior. Passing fixture tests does not verify real credentials or a real EAS project.

The sanitized local `check:store` run exits `1` as expected for exactly five unresolved fields:

- `EXPO_PUBLIC_AUTH_PROVIDER` must be `supabase`.
- `EXPO_PUBLIC_SUPABASE_URL` is absent.
- `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` is absent.
- `expo.owner` is absent.
- `expo.extra.eas.projectId` is absent.

These values must be supplied through an approved account/configuration process later. No credentials or fabricated owner/project were introduced here.

## Fresh Verification

All commands were run in this worktree. Expo dotenv loading and telemetry were disabled; exports additionally used offline mode and an isolated temporary HOME. No real provider call was made.

| Check | Result |
| --- | --- |
| `npm install --ignore-scripts --no-audit --no-fund` | PASS; 739 packages installed; public npm access required a sandbox network escalation |
| `npm --workspace apps/mobile run test:store` | PASS; 13 tests after the final permission adjustment |
| Sanitized `npm --workspace apps/mobile run check:store` | EXPECTED BLOCK; exit 1, five missing auth/EAS fields listed above |
| `npm --workspace apps/mobile exec -- expo install --check` | PASS; `Dependencies are up to date` |
| `npm run typecheck:mobile` | PASS |
| `npm run typecheck:shared` | PASS |
| `npm run typecheck:admin` | FAIL; separate admin dependencies are not installed: missing `lucide-react` (TS2307) and `react-dom/client` declarations (TS7016); no admin package/lock/source edits attempted |
| Web JS export | PASS; 2143 modules; `/private/tmp/cal-ai-play-web-export-20261109` |
| Android JS/Hermes export | PASS; 2596 modules; `/private/tmp/cal-ai-play-android-export-20261109` |
| `expo config --type introspect --json` with structured assertions | PASS; `allowBackup=false` and all blocked permission `tools:node=remove` directives |
| `node --check apps/mobile/scripts/check-store-build.mjs` | PASS |
| `git diff --check` (owned paths) | PASS after documentation |

Reproduction commands from the repository root:

```sh
npm --workspace apps/mobile run test:store
npm --workspace apps/mobile run check:store
EXPO_NO_DOTENV=1 EXPO_NO_TELEMETRY=1 CI=1 npm --workspace apps/mobile exec -- expo install --check
npm run typecheck:mobile
npm run typecheck:shared
npm run typecheck:admin
EXPO_NO_DOTENV=1 EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 CI=1 npm --workspace apps/mobile exec -- expo export --platform web --output-dir /private/tmp/cal-ai-play-web-export-20261109
EXPO_NO_DOTENV=1 EXPO_NO_TELEMETRY=1 EXPO_OFFLINE=1 CI=1 npm --workspace apps/mobile exec -- expo export --platform android --output-dir /private/tmp/cal-ai-play-android-export-20261109
```

## Handoff And Unproven Gates

- At source inspection, `apps/mobile/src/media/mealImagePicker.ts` still requested library permission before launching the system picker. With broad reads blocked this can prevent gallery selection, particularly Android API 24-32. This file is outside dependency/config ownership; the source owner must remove the Android preflight and test the flow. Successful bundling does not validate that interaction.
- Admin typecheck remains a fresh reported failure, not silently repaired by installing/changing another owner's dependencies.
- Other agents continued editing disjoint source files during this batch. These are fresh local check results, not a frozen final integration snapshot; the leader owns verification after combining source changes.
- EAS owner/project, public production auth configuration and Android signing remain blocked/unknown. EAS app-bundle profile configuration is not evidence of an AAB.
- No APK/AAB, native Gradle compilation, 16 KB binary alignment check, target/compile SDK binary inspection, manifest merge inspection, device/emulator installation, camera/gallery/upload E2E, persistence/provider proof, or API 36 edge-to-edge/back-navigation UI validation was performed.
- Play Console creation, listing/policy/legal declarations, reviewer access, account deletion, closed-test eligibility and store submission remain separate approval/evidence gates.
- No credentials were read, no cloud project/signing/build was created, and there was no paid call, commit, push, deployment or store upload. Main and equipment worktrees were not edited.

## Owner-Approved EAS Cloud Follow-Up

On 2026-11-09 the owner selected the recommended retained React Native plus
EAS cloud-build route. No conversion to the UPGLOW web/TWA wrapper was made.
The already-open Google-authenticated Expo onboarding was completed with the
public operator name, commercial Business account type, organization
`arche-trustfirstnutrition` and project `trust-first-nutrition`. No team members
were invited. This Expo account choice is not a Google Play account conversion.

The new organization's actual Billing page read back Free, $0/month, an
upcoming estimate of $0 and zero builds out of 30. No payment data, paid plan
or add-on was selected. The project was independently read back under that
organization. Expo's visible project connection command returned public UUID
`cd7254d2-d859-4992-8063-7f2492ba8351`; owner and UUID were written into this
branch's app.json, not fabricated or copied from another app.

Official CLI OAuth is awaiting owner action. Limit access is ON; Only selected
accounts selects this organization only with Developer role. The personal
account is unchecked, and the agent did not click Approve. CLI authentication
and project-info readback remain unverified. No signing key was created,
exported or replaced; no source archive, APK/AAB or server credentials were
uploaded. Free-tier build execution will still require archive hygiene,
approved signing setup and final artifact/runtime verification. Public client
auth configuration already exists and is not a request for new API keys.

Evidence: `/private/tmp/cal-ai-expo-free-plan-20261109.jpg` and
`/private/tmp/cal-ai-expo-cli-scope-20261109.jpg`. Account setup is not an
additional QA repair pass; the run remains six completed out of seven.

## EAS Authorization And APK Build: 2026-11-10

The owner completed the existing CLI approval. Fresh `eas whoami` confirms
access only to `arche-trustfirstnutrition`, limited to Developer by the current
credentials. `eas project:info` matches the public owner/project UUID above.
No broader account permission was requested.

Configured only the four existing public mobile API/auth settings in this
project's preview and production environments, with Sensitive display to reduce
log exposure. Independent readback matched every value without printing it.
These values are embedded in the client and are not server secrets. No OpenAI,
database, R2, Supabase service-role or admin key was copied. Build profiles now
select their environments explicitly.

Added root `.easignore` to preserve the existing Git exclusions and additionally
exclude server/admin code, documentation, test data, local env files, signing
files and private tooling state. Official archive inspection produced 77 files,
zero forbidden paths/symlinks/missing required inputs, and zero matches for the
targeted private-key patterns. This is a targeted check, not a security audit.
The archive was 5.1 MB as reported by EAS. Store/icon/archive guards pass 22/22.

The credentials screen initially reported no Android credentials for this app.
After explicit owner approval, official EAS generated and stored a new dedicated
Android keystore. No key/password download, output or Git storage occurred.
The preview build uses the intended package, version 0.1.0 / versionCode 1:

`e8741dcd-a358-44f0-8efa-8fa07a55f9aa`

[Build status](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/e8741dcd-a358-44f0-8efa-8fa07a55f9aa)

Fresh readback reached IN_PROGRESS. APK completion, binary inspection, Android
runtime/device behavior, AAB and Play registration remain separate gates.
No paid upgrade, production deployment, Play submission or legal acceptance
was performed. Main and the equipment-feature worktree remain untouched.

## Final APK And AAB Readback: 2026-11-10

The preceding IN_PROGRESS observation is superseded. The first completed APK
exposed unnecessary native permissions during real artifact inspection and is
not the tester artifact. Removed overlay, biometric/fingerprint and vibration
permissions; scoped camera write access to Android API 28 and below rather than
breaking older-device capture. Store guards now pass 23/23, with mobile/shared
typechecks and mobile smoke passing.

Corrected APK `3eeb8b00-bf3f-4d2b-bf55-8097c42918f8` and production-profile AAB
`96f4e5a6-d7ec-4870-9af7-c6a1ac2b0777` both report FINISHED. Downloaded and
checked final manifests, package/version/API 36, restricted permissions,
matching build certificates and ZIP integrity. Official bundletool validates
the AAB; its native packaging requests 16 KB alignment, and all 28 64-bit shared
libraries in each artifact pass static ELF alignment checks. No cryptographic
signature, zipalign-tool or native runtime success is implied.

Use the corrected [APK install/build page](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/3eeb8b00-bf3f-4d2b-bf55-8097c42918f8)
for an authorized Android tester. It is approximately 68.4 MB; iPhone cannot
install it. No Android Studio is required on the owner's Mac to share this
already-built APK. An actual Android tester still needs to verify core flows.
Artifact hashes, exact inspection scope and remaining release gates are in
`docs/google-play/ANDROID-ARTIFACTS-2026-11-10.md`. Play has not received an
upload or created an app record. QA is now seven of seven, not a whole-service
approval; no extra loop or main/equipment merge was started.
