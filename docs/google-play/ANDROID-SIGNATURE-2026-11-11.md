# Android cryptographic signature verification: 2026-11-11

## Result

- **APK: PASS**. Official AOSP apksigner verified the v2 signature with
  warnings treated as errors, requested API range 24-36; exit 0, no stderr.
- **AAB: cryptographic integrity verified via JarFile, with caveats**.
  Official Temurin jarsigner reported `jar verified.` and exited 0.
  Strict mode exited **4**, reporting an untrusted/self-signed certificate.
  A separate JarFile/JarInputStream layout warning remains, detailed below.
  This is not an unconditional strict-verification pass or Play acceptance.

This was only the approved artifact-signature gate, not another whole-service
QA pass or a reset of the seven-pass cap. Worktree:
`/private/tmp/cal-ai-play-20261109`, branch `codex/android-play-readiness`.
Only this new repository report and temporary tools were written. Main,
source, prior reports, registration-state and leader-owned documents were
not edited. No private keystore was read/exported, no signing command/key,
cloud build/write/upload, commit/push, SDK installation or runtime test occurred.

## Exact Inputs

These existing files were hashed to bind the verification to the previously
inspected builds; no CRC, manifest-policy or alignment gate was repeated.
Both files retained identical bytes, SHA-256 and modification time afterward.

| Artifact | Bytes | SHA-256 |
| --- | --- | --- |
| AAB `3845bafe-01c2-4e15-9c49-8e289deda7ae` | 46,796,266 | `ac6f91e572167b77a6a4ede3216bb616d287af69468d4f78e1a2e96e20c9dce0` |
| APK `4b96b896-ef91-42d7-9b1a-5a3c298aefac` | 68,389,309 | `7fd186faf6393166b8dffc34b28e6d8b1b865e956c0948e1d408cefb1c375036` |

- AAB: `/private/tmp/current/trust-first-nutrition-3845bafe-01c2-4e15-9c49-8e289deda7ae.aab`
- APK: `/private/tmp/current/trust-first-nutrition-4b96b896-ef91-42d7-9b1a-5a3c298aefac.apk`

Package/version identity is recorded in `ANDROID-INSPECTION-2026-11-11.md`;
no new EAS query or artifact download was needed.

## Tools, Bytes And Provenance

Existing installations/caches had no usable jarsigner/apksigner CLI; the
cached apksig 8.9.1 library alone was not used as a substitute CLI. The existing
Temurin JRE also lacks the `jdk.jartool` module. To avoid an Android SDK,
downloaded only an official JDK archive and a single official prebuilt JAR:

| Download | Received bytes | Verification |
| --- | --- | --- |
| Temurin JDK archive | 186,192,554 | SHA-256 matched official API metadata and checksum file |
| Official JDK checksum file | 118 | Published checksum agreed with the API |
| AOSP apksigner JAR, base64 transport | 1,432,072 | Decoded 1,074,052-byte JAR matched pinned Git blob |

Tool/checksum payload total: **187,624,744 bytes**. Including the 3,415 bytes
of curl-read metadata: **187,628,159 bytes**, below 250,000,000. No automatic
download retries occurred. Counts exclude HTTP/TLS overhead and documentation
browsing. Nothing was installed into system Java/Android locations or the app.

Temporary directory: `/private/tmp/cal-ai-android-signature-20261111/`.

- JDK: Temurin **17.0.21+9**, macOS aarch64 HotSpot, unpacked under
  `jdk-17.0.21+9/Contents/Home/`. Archive retained as `temurin-jdk.tar.gz`.
  [Official release asset](https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jdk_aarch64_mac_hotspot_17.0.21_9.tar.gz),
  [published checksum](https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.21%2B9/OpenJDK17U-jdk_aarch64_mac_hotspot_17.0.21_9.tar.gz.sha256.txt).
  Archive SHA-256:
  `78b08c7f5a0598242d5719c022e19479cb4a3aa45c37c19726a757a469ed1c15`.
- APK tool: official AOSP prebuilt `apksigner.jar`, reports version **0.9**;
  no custom compilation, API adapter or cryptography implementation.
  [Pinned source](https://android.googlesource.com/platform/prebuilts/sdk/+/3af7c93524be6f51e092b87b17f009f13ee98b43/tools/darwin/lib/apksigner.jar).
  Published Git blob: `222614191f2cc4131dbe0241e3f8687103ef7de9`, matched by
  computing the standard Git blob hash of the downloaded bytes.
  JAR SHA-256:
  `9469c60e5e40fc5c44a2f2338509cb6600cdf065e9b50f9fa3ca6c5be5bae6a9`.

Tool provenance is official HTTPS distribution plus matching published
checksums/content hash, not independent publisher GPG/attestation verification.
The pinned AOSP snapshot is not a claim to be the latest SDK Build Tools.

## Verification Commands And Output

The following variables denote exact local paths. `user.home` was redirected
to an empty temporary directory so verification did not inspect a personal
default keystore. No certificate was imported to suppress trust errors.

```sh
TOOLS=/private/tmp/cal-ai-android-signature-20261111
JDK="$TOOLS/jdk-17.0.21+9/Contents/Home"
AAB=/private/tmp/current/trust-first-nutrition-3845bafe-01c2-4e15-9c49-8e289deda7ae.aab
APK=/private/tmp/current/trust-first-nutrition-4b96b896-ef91-42d7-9b1a-5a3c298aefac.apk
"$JDK/bin/jarsigner" -J-Duser.home="$TOOLS/verify-home" -verify -verbose:summary -certs "$AAB"
"$JDK/bin/jarsigner" -J-Duser.home="$TOOLS/verify-home" -J-Duser.language=en -J-Duser.country=US -verify -strict -verbose:summary -certs "$AAB"
"$JDK/bin/java" -Duser.home="$TOOLS/verify-home" -jar "$TOOLS/apksigner.jar" verify --verbose --print-certs --min-sdk-version 24 --max-sdk-version 36 -Werr "$APK"
"$JDK/bin/keytool" -J-Duser.home="$TOOLS/verify-home" -J-Duser.language=en -J-Duser.country=US -printcert -jarfile "$AAB"
```

**APK:** exit 0; `Verifies`; v2 verified `true`; v1, v3, v3.1, v4 and
SourceStamp reported `false`; one signer, RSA 2048-bit. No warning/stderr.
The v2 success is actual artifact signature verification, not certificate
parsing. Other schemes/SourceStamp were not verified by this invocation.
See the [official apksigner verification options](https://developer.android.com/tools/apksigner#verify).

**AAB:** normal jarsigner exit 0, `jar verified.`; SHA-256 digests and
SHA256withRSA/2048-bit signatures verified. The summary marked all 763 payload
entries `sm` and the manifest `s`; the other two entries are signature metadata.
Strict mode exit 4, `jar verified, with signer errors.`; no stderr.
Errors were PKIX chain validation failure (`unable to find valid certification
path to requested target`) and a self-signed signer certificate. This is
cryptographic verification with a failed trust-chain gate, not a digest/signature
mismatch. [JDK jarsigner documentation](https://docs.oracle.com/en/java/javase/17/docs/specs/man/jarsigner.html)
defines these strict-mode certificate warnings as code 4.

Additional AAB warnings were retained, not suppressed:

- No trusted signature timestamp; future validation after certificate expiry
  or revocation is not established. No online revocation check was requested.
- POSIX permission/symlink attributes are outside JAR signature protection.
- Internal reader inconsistency: `Manifest is missing when reading via
  JarInputStream`; 764 entries were signed via JarFile but not JarInputStream.
  Narrow diagnosis found `META-INF/MANIFEST.MF` is the **last** local entry
  (index 765 of 766), following `.SF` and `.RSA`; all 766 central/local header
  entry names agree. The verified JDK's bundled `JarInputStream.java` expects
  the manifest first, or second after a `META-INF/` directory. This explains
  the streaming-reader limitation; it does not establish a clean result for
  streaming consumers. No archive was reordered, repacked or re-signed.

Official keytool `-printcert -jarfile` exited 0 and confirmed that the AAB's
signer fingerprint matches apksigner's verified APK signer and the previously
recorded build/upload certificate:

`C797C7DA080CB65B82BFB6789E7BADEA9AAA6660A3078205FE9955063244009F`

Keytool's fingerprint output alone is metadata; the integrity evidence above
comes from jarsigner/apksigner. This is not a Play App Signing certificate.

## Remaining Boundaries

APK signature integrity and AAB JarFile signature integrity are now verified
for the exact hashes above. AAB strict trust-chain success and clean streaming
verification are **not** claimed. Play upload acceptance, signing-certificate
enrollment, generated splits, device/16 KB runtime and whole-service readiness
remain outside this gate. Release/Play UI work remains with the leader.
