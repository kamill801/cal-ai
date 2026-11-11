# Android artifact inspection: 2026-11-11

Result: **PASS for the bounded static checks below**, not cryptographic
signature verification, device/runtime approval or Google Play acceptance.

Scope: `/private/tmp/cal-ai-play-20261109`, branch
`codex/android-play-readiness`. The only repository file written by this
sidecar is this new report. Main `/Users/dd/Documents/cal-ai` and other agents'
changes were not edited or reverted. No build, signing-key/environment change,
credential export, backend mutation, upload, distribution, installation,
commit or push was performed.

## Current artifact identity

Read-only official cached EAS CLI 27.5.0 `build:view <id> --json` readbacks at
2026-11-11 07:39:11-07:39:17 UTC confirmed both builds FINISHED/ANDROID:
owner `arche-trustfirstnutrition`, slug `trust-first-nutrition`, project
`cd7254d2-d859-4992-8063-7f2492ba8351`, package
`com.trustfirstnutrition.app`, version `0.1.0`, versionCode `1`.
CLI: `/Users/dd/.npm/_npx/6bc7bae5c2059953/node_modules/eas-cli/bin/run`.
These are not the earlier builds inspected in `ANDROID-ARTIFACTS-2026-11-10.md`.

| Item | Play AAB | Preview APK |
| --- | --- | --- |
| Build ID | `3845bafe-01c2-4e15-9c49-8e289deda7ae` | `4b96b896-ef91-42d7-9b1a-5a3c298aefac` |
| Completed UTC | `2026-11-10T17:25:23.816Z` | `2026-11-10T17:25:37.261Z` |
| Profile / distribution | `production` / `STORE` | `preview` / `INTERNAL` |
| Actual bytes | 46,796,266 | 68,389,309 |
| SHA-256 | `ac6f91e572167b77a6a4ede3216bb616d287af69468d4f78e1a2e96e20c9dce0` | `7fd186faf6393166b8dffc34b28e6d8b1b865e956c0948e1d408cefb1c375036` |

Local downloaded files, at distinct new paths without overwriting older files:

- AAB: `/private/tmp/current/trust-first-nutrition-3845bafe-01c2-4e15-9c49-8e289deda7ae.aab`
- APK: `/private/tmp/current/trust-first-nutrition-4b96b896-ef91-42d7-9b1a-5a3c298aefac.apk`

Downloads used only artifact URLs returned by the matched official CLI
metadata, with HTTPS/TLS verification. Signed URLs and raw EAS metadata/logs
were not saved; no credential files were inspected. Hashes above are locally
computed identifiers, not comparison with an independently published digest.

## Actual checks

- Complete ZIP CRC/decompression checks passed: APK 729 entries, AAB 766;
  neither archive contains duplicate entry names.
- Actual manifests match package/version/code above, min SDK 24 and target
  SDK 36. AAB compile SDK is 36. Both have `allowBackup=false`,
  `extractNativeLibs=false`, no explicit `debuggable` attribute (false default),
  backup-rule references, and the `trustfirstnutrition` login scheme.
  These are static manifest observations, not backup/restore or OAuth tests.
- Both manifests contain exactly these five permissions:
  `android.permission.CAMERA`, `android.permission.INTERNET`,
  `android.permission.WRITE_EXTERNAL_STORAGE` with `maxSdkVersion=28`,
  `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE`, and
  `com.trustfirstnutrition.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`.
  No overlay, biometric/fingerprint, vibration, recording-audio, broad media
  read, READ_EXTERNAL_STORAGE or MANAGE_EXTERNAL_STORAGE permissions remain.
- Official bundletool 1.18.3 `validate` exited 0 on this AAB; `dump manifest`
  and `dump config` were parsed. Config enables uncompressed native libraries
  with `PAGE_ALIGNMENT_16K`; its producer version field is 1.18.1, distinct
  from the inspection tool version.
- Each artifact has 56 native libraries across arm64-v8a, armeabi-v7a, x86
  and x86_64. Existing pyelftools inspection passed all 28 **64-bit** libraries
  per artifact: every PT_LOAD has `p_align >= 16384` and
  `(p_vaddr - p_offset) % 16384 == 0`; minimum alignment is 16,384 bytes.
  This ELF gate did not inspect the 32-bit libraries.
- APK ZIP alignment was additionally calculated from actual local headers:
  `data_offset = header_offset + 30 + filename_length + extra_length`.
  All 56 native libraries are ZIP_STORED; every data offset is divisible by
  16,384, with zero header/compression-method mismatches. This is an
  independent static offset check, **not execution of Android zipalign**.
  All 56 AAB libraries are DEFLATED; their container offsets are not an
  installable-APK alignment test. No APK splits were generated from the AAB.

## Certificate metadata

APK parser detects a v2 signature block, no v1/v3 blocks. AAB contains
`META-INF/C7DDD270.RSA` (PKCS#7). Both expose the same certificate DER and
the expected prior build/upload certificate SHA-256:

`C797C7DA080CB65B82BFB6789E7BADEA9AAA6660A3078205FE9955063244009F`

RSA 2048-bit public key; certificate signature algorithm
`sha256WithRSAEncryption`; validity `2026-11-10T11:18:57Z` through
`2054-03-28T11:18:57Z`. Subject and issuer DN attribute values are empty.
These are parsed certificate fields, not verification of the certificate or
artifact signatures. This is not a Google Play App Signing certificate.

## Tools And Remaining Gaps

Reused the existing scripts `/private/tmp/cal-ai-inspect-apk-20261110.py`,
`/private/tmp/cal-ai-inspect-aab-20261110.py` and
`/private/tmp/cal-ai-inspect-elf-20261110.py`, plus an in-memory Python
ZIP-header/certificate inspection. No scripts or dependencies were changed.
The specified release venv lacked pyaxmlparser/pyelftools; existing cached
packages were loaded from `/private/tmp/cal-ai-apk-parser-20261110`
(pyaxmlparser 0.3.31, asn1crypto 1.5.1) and
`/private/tmp/cal-ai-elf-parser-20261110` (pyelftools 0.33), using
`/private/tmp/cal-ai-release-venv-20261110/bin/python`.

Reused Temurin 17.0.21+9 JRE and bundletool under
`/private/tmp/cal-ai-android-inspection-20261110/`; prior download provenance
and limitations are documented in `ANDROID-ARTIFACTS-2026-11-10.md`.
Current bundletool JAR SHA-256:
`a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e29`.
Published tool digests were not independently re-fetched in this sidecar.

No apksigner cryptographic verification, AAB JAR-signature verification,
official zipalign check, Play-generated split validation, emulator/device
execution or 16 KB runtime test was performed. No large Android SDK was
installed. Camera/gallery, native login, provider/storage behavior,
backup/restore behavior and Play acceptance remain unverified by this work.
Leader-owned registration-state and release/policy documents were not changed;
these static passes do not close their remaining gates.

## Additional Signature-Tool Gate: 2026-11-11

Result: **UNAVAILABLE in the bounded locations checked**. No previous static
artifact checks were repeated, and neither cryptographic signature gap closed.

- Checked system/user `JavaVirtualMachines`, Android Studio JBR/JRE,
  Homebrew OpenJDK `opt`/`Cellar`, and `~/.gradle/jdks`: no usable JDK
  `jarsigner` found. The existing temporary Temurin JRE also lacks it.
  `/usr/libexec/java_home -V` exited 1: `Unable to locate a Java Runtime.`
- Attempted `/usr/bin/jarsigner -verify /private/tmp/current/trust-first-nutrition-3845bafe-01c2-4e15-9c49-8e289deda7ae.aab`.
  Exit 1, no stdout; startup error: `Unable to locate a Java Runtime.`
  This macOS launcher failure occurred before verification; it is **not** an
  AAB signature failure or a verification pass.
- No `apksigner` executable or `apksigner.jar` was found in standard user,
  Homebrew, `/opt/android-sdk` or `/usr/local/lib/android/sdk` build-tools
  locations, PATH, or the exact Gradle `com.android.tools.build/apksigner`
  module cache. SDK/JAVA_HOME location variables were unset.
- Existing Gradle cache contains
  `/Users/dd/.gradle/caches/modules-2/files-2.1/com.android.tools.build/apksig/8.9.1/f005788487574c7d6ba23dea63bf8cb3a4f164a6/apksig-8.9.1.jar`.
  Its SHA-1 matches the cache-directory name. It contains the `ApkVerifier`
  library API, but no `Main-Class` or `com.android.apksigner.ApkSignerTool`
  CLI; it was not treated as an installed apksigner or used to claim a pass.

No network access, downloads, dependency/SDK installation, custom verifier,
private-project search, cloud writes or runtime tests were performed for this
additional gate. AAB JAR-signature and APK cryptographic signature verification
remain unperformed. Only this report was edited.
