# Android artifact verification: 2026-11-10

Branch: `codex/android-play-readiness`, isolated worktree
`/private/tmp/cal-ai-play-20261109`. Main and the equipment-feature worktree
were not edited. These are build/metadata checks, not Play acceptance or
whole-service runtime approval. No commit, push, production deployment,
Play upload, policy acceptance or public release occurred.

## Identity and signing

Official EAS CLI readback matched organization `arche-trustfirstnutrition`,
project `trust-first-nutrition`, UUID `cd7254d2-d859-4992-8063-7f2492ba8351`.
The current OAuth credentials are limited to Developer in that organization.
After explicit owner approval, EAS generated an app-specific keystore remotely.
The corrected APK and AAB reused that same key with `--freeze-credentials`.
No private key, key password or server credentials were exported or printed.
No paid plan or payment method was added.

The build/upload certificate SHA-256 is public verification material:

`C797C7DA080CB65B82BFB6789E7BADEA9AAA6660A3078205FE9955063244009F`

This is not evidence of a Google Play App Signing certificate. Play has not
assigned/read back one for this app. Do not use the two interchangeably.

## Artifacts

Both builds report FINISHED, version 0.1.0 / versionCode 1, package
`com.trustfirstnutrition.app`. Downloaded only after project/package readback.
No ephemeral signed download/log URLs were saved.

| Artifact | Preview APK | Play AAB |
| --- | --- | --- |
| Build ID | `3eeb8b00-bf3f-4d2b-bf55-8097c42918f8` | `96f4e5a6-d7ec-4870-9af7-c6a1ac2b0777` |
| Completed UTC | 2026-11-10 11:37:47 | 2026-11-10 11:37:50 |
| Bytes | 68,385,453 | 46,794,802 |
| Local file | `/private/tmp/trust-first-nutrition-preview-minimal-20261110.apk` | `/private/tmp/trust-first-nutrition-play-20261110.aab` |
| SHA-256 | `7e2d6b39aa524af3664ae9bbedc0761940e19138ceaa27546a9cea0fceafd6ce` | `6ec86a5f30ce8e3187ceb741f78a34953986936358b92a087654a3852054715b` |

[APK build/install page](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/3eeb8b00-bf3f-4d2b-bf55-8097c42918f8)

[AAB build/download page](https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/96f4e5a6-d7ec-4870-9af7-c6a1ac2b0777)

The first APK, `e8741dcd-a358-44f0-8efa-8fa07a55f9aa`, is superseded, not the
tester artifact. Actual binary inspection found unnecessary overlay,
biometric/fingerprint and vibration permissions, plus unscoped legacy storage.
Source was repaired and rebuilt before these final artifacts were selected.

## Checks and repair

- Actual APK and AAB package, version, min SDK 24, target SDK 36 match.
  AAB compile SDK is also 36.
- The final manifest contains CAMERA, INTERNET, legacy WRITE_EXTERNAL_STORAGE
  only through API 28, and dependency-specific install-referrer/dynamic-receiver
  permissions. No overlay, biometric, fingerprint, vibration, recording-audio,
  broad media reads, READ_EXTERNAL_STORAGE or MANAGE_EXTERNAL_STORAGE remain.
- `allowBackup=false`; no debuggable release flag. Native login scheme
  `trustfirstnutrition` is present. This is not native OAuth behavior proof.
- Added a config plugin scoping legacy write permission to API 28. Installed
  SDK 54 image-picker code requires it for camera capture on API 24-28;
  removing it entirely would break those devices. Modern Android gallery uses
  the system picker without a broad-library permission preflight.
- Both ZIP CRC checks pass. APK v2 signature block and AAB PKCS#7 signature
  block contain the expected same build certificate. Metadata parsing does
  not cryptographically verify signatures or establish store acceptance.
- Official Google bundletool 1.18.3 `validate` passes on the AAB, and
  `dump manifest` supplies the inspected final manifest. Bundle config requests
  uncompressed native libraries with `PAGE_ALIGNMENT_16K`.
- Using pyelftools 0.33, all 28 64-bit shared libraries in each artifact have
  PT_LOAD alignment of at least 16,384 bytes and matching offset/address
  congruence. This is static ELF evidence, not `zipalign` or a 16 KB device test.
- Temporary official bundletool and Temurin JRE downloads matched their
  published SHA-256 values. No Android Studio/system SDK installation or app
  dependency addition was needed for these inspections.
- The hardened EAS source archive has 77 files, zero forbidden paths,
  symlinks or missing required inputs. It excludes env/private signing files,
  server/admin source, QA data and local tooling state. An earlier archive
  also passed targeted private-key pattern checks, not a general security audit.
- Store/icon/archive/permission tests pass 23/23; mobile/shared typechecks,
  mobile smoke and whitespace checks pass after the source repair.

Reproduce with the corresponding artifacts and trusted tools:

```sh
java -jar bundletool-all-1.18.3.jar validate --bundle=trust-first-nutrition-play-20261110.aab
java -jar bundletool-all-1.18.3.jar dump manifest --bundle=trust-first-nutrition-play-20261110.aab --module=base
java -jar bundletool-all-1.18.3.jar dump config --bundle=trust-first-nutrition-play-20261110.aab
npm --workspace apps/mobile run test:store
npm run typecheck:mobile
npm run typecheck:shared
npm --workspace apps/mobile run smoke
git diff --check
```

## Remaining gates

No Android device/emulator installation, runtime launch, keyboard/back behavior,
camera/gallery/URI/permission E2E, native OAuth, R2 transfer or real provider
quality was verified by these static checks. APK cryptographic verification,
zip alignment tooling and a real 16 KB runtime remain separate checks.

Production fixture cleanup is still blocked by the deployed web delete button;
the source fix is not deployed. Account deletion is disabled and has unresolved
real PostgreSQL/provider/storage/worker/retention proof. Public policies remain
unapproved source drafts, and normal reviewer access is not provider-verified.
Google Play account-type applicability, declarations, app creation, accepted
upload, tester participation, review and public release remain open. See
`RELEASE-GATES.md` and `POLICY-CHECK-2026-11-09.md`.

Pass 7 is the final batch under the owner's seven-pass QA limit. It fixes and
checks native packaging only; it does not turn the remaining gates into passes.
