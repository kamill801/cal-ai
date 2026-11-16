# Android Artifact Inspection: 2026-11-16

## Scope And Result

Read-only local inspection of the leader-downloaded APK and AAB. ZIP integrity,
manifest settings, APK native ZIP alignment, and both archives' native ELF gates
passed. Payload endpoint/consent-field literal checks passed; the current policy
version literal is absent, with the dynamic-version limitation explained below.

Reported release source: `9d2dbe4`. This inspection does not independently bind
cloud build provenance to that commit. No cloud calls, builds, installs, signing
operations, credentials, artifact mutation, or ordinary-user-data access occurred.
Cryptographic signature verification belongs to the leader and was not repeated.

## Artifact Identity

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `/private/tmp/trust-first-nutrition-0.1.1-2-20261116.apk` | 68,403,713 | `db0f70e61d4cd2b4ebaad6f01edc554466afcd4220765b70cb5aa23b1864fd16` |
| `/private/tmp/trust-first-nutrition-0.1.1-2-20261116.aab` | 46,803,839 | `2e6187390c00aff77d0169023f1c284ee39f5fa795bf16ae1972c6a52b378984` |

Both independently measured identities match the leader's supplied values. File
inode, size, and modification time remained unchanged during inspection.

## ZIP And Manifest

- APK: 729 ZIP entries; all CRC/decompression checks passed; no duplicate names.
- AAB: 766 ZIP entries; all CRC/decompression checks passed; no duplicate names.
- Local ZIP entry headers agree with central filenames/compression methods; entry
  payload extents do not overlap the central directory. No archive was extracted.
- AAB has one manifest module, `base`.

Both actual manifests contain:

| Setting | Observed |
| --- | --- |
| Package | `com.trustfirstnutrition.app` |
| Version name / code | `0.1.1` / `2` |
| Minimum / target SDK | `24` / `36` |
| `android:allowBackup` | Explicit `false` |
| `android:debuggable` | Absent; effective Android default `false` |
| `android:extractNativeLibs` | Explicit `false` |

Actual requested permissions are identical in both artifacts:

| Permission | Maximum SDK |
| --- | --- |
| `android.permission.CAMERA` | Not restricted |
| `android.permission.INTERNET` | Not restricted |
| `android.permission.WRITE_EXTERNAL_STORAGE` | `28` |
| `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE` | Not restricted |
| `com.trustfirstnutrition.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Not restricted |

This is the complete requested-permission inventory, not a runtime grant test or
an assessment of Google Play policy acceptance. The legacy write-storage request
remains present only through API 28.

## Native Alignment

Each archive contains 56 native ELF libraries: 14 each for `arm64-v8a`,
`armeabi-v7a`, `x86`, and `x86_64`. ELF class and machine agree with each ABI path.

- APK: all 56 native entries are uncompressed; every actual local-header-derived
  data offset is divisible by 16,384. No native ZIP alignment failures.
- Both archives: all 28 ELF64 files passed, covering 86 `PT_LOAD` segments per
  archive. Minimum `p_align` is 16,384; every alignment is a power of two and every
  segment is congruent in `p_offset` and `p_vaddr` modulo its alignment and 16,384.
- ELF program-table/file extents and LOAD file/memory sizes were checked;
  28 ELF32 files per archive also passed structural/ABI/congruence checks. The
  ELF64 16 KB minimum is not falsely asserted for ELF32.
- Native-entry sets and all native-library bytes are identical between artifacts.
- AAB ELF compatibility is not proof of the ZIP offsets of future Play-generated
  APK splits. This inspection did not generate APKs from the AAB or run on a device.

## JS/Hermes Literal Checks

Only boolean payload-check results are reported. Payload contents, keys, tokens,
and decoded strings were not printed or persisted.

| Check | APK | AAB |
| --- | --- | --- |
| Payload present | true | true |
| Canonical API origin present | true | true |
| Expected public Supabase hostname present | true | true |
| Current consent route present | true | true |
| `policy_version` field present | true | true |
| Health-consent field present | true | true |
| Analytics-consent field present | true | true |
| Current policy version literal present | false | false |
| JS/Hermes payload bytes identical between artifacts | true | true |

The absent version literal is not presented as a successful literal assertion.
Committed source at `9d2dbe4` corroborates a dynamic contract: the shared mapper
reads the response policy version (`packages/shared/src/index.ts:68`), the API
client reads consent and returns that mapped response (`apps/mobile/src/api/client.ts:179`),
and the app sends the received version on submission (`apps/mobile/App.tsx:175`).
No live API request or device consent interaction was made; the server's currently
served policy version and end-to-end consent behavior remain outside this proof.
The expected endpoint/route/field literals were detectable, so their checks did
not encounter a Hermes string-compression ambiguity.

## Tools And Reproduction

Inspector: `/private/tmp/cal-ai-inspect-android-20261116.py`. It accepts only the
two explicitly authorized artifact paths and prints JSON to stdout. It does not
write or extract artifacts.

The supplied Python parser cache directories still exist, but their module files
are missing: neither `pyaxmlparser` nor `pyelftools` is importable. No dependency
was downloaded or installed. The APK manifest and ELF tables were therefore read
with explicitly identified bounded stdlib decoders. Self-checks passed for UTF-8
and UTF-16 binary XML, ELF32/ELF64 in both byte orders, rejected truncation and
incongruence, and detection of insufficient ELF page alignment. This is not an
independent execution of the missing cached Python parsers.

The AAB protobuf manifest was independently decoded by existing cached bundletool
1.17.2 and Java 17 using only cached Gradle JARs; its settings and requested
permissions agree with the APK manifest. Bundletool's `dump manifest` was used,
not a build, validation/signature command, or dependency resolution.

```sh
/private/tmp/cal-ai-release-venv-20261110/bin/python -B \
  /private/tmp/cal-ai-inspect-android-20261116.py --self-test --preflight

/private/tmp/cal-ai-release-venv-20261110/bin/python -B \
  /private/tmp/cal-ai-inspect-android-20261116.py \
  /private/tmp/trust-first-nutrition-0.1.1-2-20261116.apk \
  /private/tmp/trust-first-nutrition-0.1.1-2-20261116.aab
```

Both commands exited 0. Static identity/ZIP/manifest/native gates passed, with the
explicit dynamic-policy-version limitation retained rather than reported as an
unqualified release, runtime, signature, or Google Play readiness pass.
