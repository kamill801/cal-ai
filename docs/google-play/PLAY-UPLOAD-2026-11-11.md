# Play AAB Upload And Saved Draft

Result: exact current AAB accepted, internal draft saved, validation read back.
No test distribution, review submission, closed test or public release.

## Identity And Artifact

- Developer7707482448795132061, ARCHE Labs Personal; no account conversion.
- App4975788258134910868, Trust First Nutrition.
- Existing build3845bafe-01c2-4e15-9c49-8e289deda7ae; no new build or key.
- AAB SHA-256:
  `ac6f91e572167b77a6a4ede3216bb616d287af69468d4f78e1a2e96e20c9dce0`.
- Play artifact4860250194673485367; version1(0.1.0), minimum24, target36.
- Release `0.1.0 - Internal validation`, internal-test track. The Google Play
  signing and automatic protection settings already appeared active; no terms
  acceptance, key export or protection change was performed in this session.

File chooser uploaded the existing46.8MB AAB. Console reported one App Bundle
uploaded and displayed its version. Korean test notes were saved; the screen
confirmed changes saved. Next-step validation displayed two warnings, not
signature/SDK/16KB rejection:

1. No testers selected, so no user can access this release.
2. No R8/Proguard deobfuscation mapping file for the bundle.

Console's download estimate was15.8MB, not the AAB transfer size or a universal
per-device promise. Details report19,115 supported devices and16KB support with
an explicit runtime caveat. These are Console observations, not device tests.
Low DEX optimization is also shown; no untested R8/AGP migration was introduced
solely to suppress that nonblocking message.

## Permission Readback

The received-bundle details show7 permissions:

- `android.permission.CAMERA`
- `android.permission.INTERNET`
- `android.permission.READ_EXTERNAL_STORAGE`
- `android.permission.WRITE_EXTERNAL_STORAGE`
- `com.android.vending.CHECK_LICENSE`
- `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE`
- `com.trustfirstnutrition.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`

Compared with the source artifact's5-entry manifest, Console lists additional
Play license/install-referrer entries. No AD_ID, location or health-platform
permission is listed. This readback does not independently establish what
every transformed split transmits. Legacy storage API bounds were checked in
the actual source manifest previously, not inferred from this summary UI.

## Store Content And Release Boundaries

Truthful Korean short/full descriptions and the existing approved512px icon
were saved as a partial main-listing draft. Independent listing index shows
updated2026-11-11 and Temporary status. Missing: feature graphic and at least
two real Android phone screenshots. No fake device screenshots were supplied.
Privacy and Data safety remain incomplete; public documents are technical
drafts and production account-deletion flags remain off.

The visible Save and release button was **not clicked**. Requested the owner's
Android tester Google-account email or direct-APK delivery preference. No
tester list was invented and no other app's list or reviewer password was read.

Evidence:

- `/private/tmp/cal-ai-play-listing-draft-saved-20261111.png`
- `/private/tmp/cal-ai-play-aab-draft-validation-20261111.png`
- `ANDROID-SIGNATURE-2026-11-11.md`
- `PRODUCTION-DEPLOYMENT-2026-11-11.md`

The original whole-service QA remains7/7 and blocked. Provider lifecycle,
approved policies, Android camera/gallery/login/upload/restart and real tester
participation remain separate gates. The owner must review any later terms or
declarations; uploading a draft does not authorize false deletion assurances.
