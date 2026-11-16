# Guarded Web/API And Android Build: 2026-11-16

Scope: owner-approved code deployment and two existing Free-plan Android builds.
No ordinary-user erasure, automatic photo cleanup, paid AI test, Play test
distribution, legal attestation or review submission is authorized by this step.

## Source And Verification

- Branch `codex/play-release-finish-20261115`, source commit
  `9d2dbe4d9be0a83703e67c54767224e82ab469dc`; pushed and independently matched
  with `git ls-remote`. Main is not merged and the original dirty tree is intact.
- Full API suite: 652 passed, one existing TestClient deprecation warning;
  isolated local PostgreSQL tests ran without skips. The local cluster is stopped.
- Mobile smoke 39, store/archive/icon 24, shared/mobile types, web and Android
  JS exports passed. These do not establish native execution or provider erasure.
- Independent bounded source review cleared the final lock-contention repair;
  retryable 503 remains possible and does not mean deletion completed.
- A targeted staged-source pattern scan found no new credential matches. This
  is not a general security certification; no secret values were printed.

## Vercel Production

- Exact existing `upglow/cal-ai-api`, project
  `prj_l6Bc70asN999j5aMlyUXpB9zxcCk`.
- Committed source package: 106 files, 6,417,621 bytes, manifest digest
  `de240a1d4091753e88c2bf173a92352de8717e4b0ebeafdf14c3b365689f78e9`.
  No environment/credential files, repository history, tests or private keys.
  This is local packaging provenance, not independent source attestation.
- Deployment `dpl_HNfxviUm9pmDQ3Rjos7J3bbHEcBq`, immutable host
  `https://cal-ai-aic3odsk9-upglow.vercel.app`, READY/production.
- Initially created with `--skip-domain`, then promoted under the owner's
  explicit guarded-deployment approval. Independent alias readback confirms
  `cal-ai-api.vercel.app` points to this exact READY deployment.
- Runtime overrides explicitly set `ACCOUNT_DELETION_ENABLED`,
  `ACCOUNT_DELETION_WORKER_ENABLED`, `R2_WRITE_ONCE_UPLOADS_ENABLED` and
  `IMAGE_RETENTION_ENABLED` to false. No provider credential was replaced,
  decrypted or exported; no `CRON_SECRET` was added.
- Authorized browser checks: configuration readiness (R2, food OpenAI, body
  mock, Supabase), policy version 2026-11-16.1, all four flags off, new-upload
  TTL 7 days, unauthenticated consent route rejected, ordinary login UI rendered.
  These are read-only checks, not authenticated consent/save/provider execution.
- The same checks passed again at the canonical origin after promotion. Proof:
  `assets/production-privacy-flags-20261116.jpg` and
  `assets/production-login-20261116.jpg`. No production consent was accepted on
  behalf of an existing user and no account records were changed.

## Android Requests

- Exact existing EAS project `cd7254d2-d859-4992-8063-7f2492ba8351`, owner
  `arche-trustfirstnutrition`; CLI identity/project linkage reverified.
- Billing readback: Free, $0/month, estimated upcoming $0, Android usage 5/15
  before these two requests. No upgrade or paid quota was selected.
- Version 0.1.1/code 2, package `com.trustfirstnutrition.app`; existing dedicated
  remote signing identity reused with `--freeze-credentials`. No key export.
- Inspected EAS archive: 78 files, zero forbidden credential/server files,
  zero symlinks, all seven required inputs present, zero targeted key matches.
- Preview APK request `661463b7-08ca-41f9-aa2b-2ef384449204`.
- Production-format AAB request `07b4ecaa-e73d-4e22-8439-dcee76c516ea`.
- Both builds FINISHED: APK at 2026-11-16T12:39:56.993Z; AAB at
  2026-11-16T12:40:18.863Z. Downloaded only official matched HTTPS artifacts,
  without printing or persisting signed URLs or raw provider metadata.

| Actual artifact | APK | AAB |
| --- | --- | --- |
| Local path | `/private/tmp/trust-first-nutrition-0.1.1-2-20261116.apk` | `/private/tmp/trust-first-nutrition-0.1.1-2-20261116.aab` |
| Bytes | 68,403,713 | 46,803,839 |
| SHA-256 | `db0f70e61d4cd2b4ebaad6f01edc554466afcd4220765b70cb5aa23b1864fd16` | `2e6187390c00aff77d0169023f1c284ee39f5fa795bf16ae1972c6a52b378984` |

- APK: official cached Android `apksig` 8.9.1 `ApkVerifier` cryptographic
  verification passed, configured API range 24-36, v2=true, no errors/warnings.
  [Official verifier semantics](https://android.googlesource.com/platform/tools/apksig/+/refs/heads/main/src/main/java/com/android/apksig/ApkVerifier.java).
- AAB: JDK 17 verifying `JarFile` fully read all entries, 763 signed payload
  entries, zero unsigned payloads, no verification exception. `jarsigner
  -verify -strict` separately exited **4**, reporting self-signed/untrusted
  certificate chain, missing timestamp and JarInputStream/manifest-order
  inconsistencies. This is not an unqualified strict-jarsigner pass; it is
  distinct from the successful random-access signed-content verification.
- Both match existing EAS build/upload certificate SHA-256
  `C797C7DA080CB65B82BFB6789E7BADEA9AAA6660A3078205FE9955063244009F`.
  This is not a Play App Signing certificate or device/runtime result.
- No signing key or password was exported; the Java verifier reads only the
  public artifact/certificate. `ANDROID-INSPECTION-2026-11-16.md` records the
  completed ZIP/manifest/native checks: expected package/version/code and
  SDK24/36, five narrowly scoped requested permissions, no duplicate ZIP entries,
  all 56 APK native entries 16 KB aligned and all 28 ELF64 libraries per artifact
  passing 16 KB segment gates. Cached official bundletool 1.17.2 `validate`
  independently exited 0 on this AAB after the sidecar manifest dump.
- Actual matching Hermes payloads contain the production API origin, expected
  Supabase hostname and consent route/fields. The exact policy-version literal
  is absent: the committed client obtains/submits the current server response
  version dynamically. This is not an end-to-end device consent test.

## Play Draft Update

- Reused the exact existing app and inactive internal-test draft. Uploaded this
  matched AAB, accepted as **2 (0.1.1), min24/target36**. No signing/account
  changes, new app, tester invitations or release action.
- Removed code1 only from this draft. The confirmation explicitly states that
  it remains recoverable in the artifact library; no permanent artifact deletion.
- Saved title `0.1.1 - Consent validation` with truthful Korean notes including
  the still-disabled general account-deletion/automatic-cleanup behavior.
- Success readback followed by independent reload confirms code2 only and the
  saved title/notes. Screenshot:
  `assets/console-code2-draft-saved-20261116.jpg`.
- Did not click a release/submit action. Upload acceptance is not Android runtime,
  closed-test distribution, policy approval or review submission.

## Remaining Gates

The previous binary lacks the new required server consent gate and is not the
current test artifact. Replace it with the completed new APK before device QA.
Genuine Android screenshots, owner test feedback, final operating retention and
provider facts, deletion activation/migration scope and truthful Data safety
declarations remain separate gates. Personal health-app eligibility is still
unresolved; no account conversion or policy exemption was asserted.
