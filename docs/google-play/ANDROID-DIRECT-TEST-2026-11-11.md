# Android Direct APK Test Handoff

The owner has a nearby Android tester and requested direct-install instructions.
No Google Play tester email, Expo Go, Android Studio or cable is needed for this
path. Direct APK testing is not Play closed-test participation.

Verified existing build: `4b96b896-ef91-42d7-9b1a-5a3c298aefac`, preview APK,
Trust First Nutrition / `com.trustfirstnutrition.app`, version0.1.0/code1.
The existing Expo build page shows Succeeded and an Install modal with the
shareable URL below. The page displayed13 days remaining at verification.

https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/4b96b896-ef91-42d7-9b1a-5a3c298aefac

1. Owner sends that link to the intended tester using their chosen messenger.
2. Tester opens it in Android Chrome, selects Install/download and opens the APK.
3. If Android requests installation permission, the tester may allow only that
   browser for this known app and turn it off afterwards. Do not disable Play
   Protect or bypass a blocked-app/security warning; report the exact warning.
4. Open Trust First Nutrition. If Expo sign-in is unexpectedly required, report
   it rather than sharing the owner's Expo credentials or weakening project access.

Initial test sequence: install/open; Kakao login/callback and18+ onboarding;
goals/dashboard; camera and gallery permissions; upload/analysis/save;
restart and restore; workout record/save/reset; logout/relogin. Do not exercise
account/profile deletion until separately cleared. Actual production food AI
analysis may use the owner's configured OpenAI billing; no agent-paid test was
performed. Body AI remains mock and must not be represented as live analysis.

Record phone model/Android version and the exact failed step if any. At least
two actual Android screenshots are needed for the store; prefer synthetic data
and exclude credentials, body photos and unnecessary personal information.
No Android installation/runtime result has been reported or verified yet.

Proof: `/private/tmp/cal-ai-android-install-20261111.png`.
Reference: https://docs.expo.dev/build/internal-distribution/
