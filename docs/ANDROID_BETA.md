# Android Beta Readiness

This repo is configured for Android-first Expo/EAS builds. Keep account access, credentials, and store uploads user-owned; do not put Expo tokens, keystores, Google service account files, or Play Console secrets in this repository.

## App Identity

- Expo app slug: `trust-first-nutrition`
- Android package id: `com.trustfirstnutrition.app`
- Version source: local `apps/mobile/app.json`
- Current version: `0.1.0`

The Android package id is a permanent Play Console identity. Do not change it after the first Play app is created unless a new Play listing is intended.

## Permissions And Backup

The app explicitly requests these product permissions for meal photo capture and upload:

- `CAMERA` - take a meal photo for nutrition analysis.
- `READ_MEDIA_IMAGES` - choose a meal photo from the device gallery.

Korean permission rationales are configured through the `expo-image-picker` plugin in `apps/mobile/app.json`.
`RECORD_AUDIO` is explicitly blocked because this beta does not need video or microphone capture.
Expo and React Native can add platform permissions such as `INTERNET` or `VIBRATE` to the generated manifest. Inspect the final AAB manifest instead of treating `app.json` as the complete permission list.
Android app backup is disabled for the internal beta so the AsyncStorage profile identifier is not carried into device backup/restore.

## Local Config Validation

Run these from the repo root:

```sh
npm --workspace apps/mobile exec -- expo config --type public
npm --workspace apps/mobile exec -- expo export --platform android --output-dir export-validation
```

The export command is a config/bundling validation step. It does not create a Play-ready binary.
Remove `apps/mobile/export-validation` after local validation.

## EAS Build Profiles

Root `eas.json` defines:

- `development` - internal Android APK.
- `preview` - internal Android APK for tester distribution.
- `production` - Android App Bundle (`.aab`) for Play Console upload.

For cost-sensitive food-photo testing, `AI_MODEL_VISION=gpt-5.4-mini` is the recommended starting point. The server-side environment value remains authoritative.

Typical build commands, run by the account owner after Expo login:

```sh
eas login
eas build --platform android --profile preview
eas build --platform android --profile production
```

## User-Owned Expo Steps

1. Log in to the Expo account that should own the app.
2. Run `eas init` if the project has not been linked yet.
3. Confirm the Expo project owner and project id shown by EAS.
4. Configure Android credentials through EAS when prompted.
5. Keep generated credentials in Expo/EAS credential storage unless there is a specific reason to manage them manually.

## User-Owned Play Console Steps

1. Create the Play Console app using package id `com.trustfirstnutrition.app`.
2. Complete app category, store listing, privacy policy, data safety, content rating, and target audience forms.
3. Upload the production `.aab` from EAS Build to an internal testing track first.
4. Add tester emails or Google Groups in Play Console.
5. Install from the Play internal testing link on a real Android device.
6. Smoke test camera capture, gallery selection, API reachability, upload, analysis, and save flow before wider beta distribution.

## Release Gates Not Proven By Config

- Expo account ownership and project linking.
- Android signing credential ownership.
- Play Console app creation and policy approval.
- Production API URL and environment configuration.
- Real-device camera/gallery/upload smoke test.
- Final APK/AAB manifest inspection for permissions and `android:allowBackup="false"`.
- Google Play internal testing availability.
