# Android rebuild checkpoint - 2026-11-11

Current build completion and bounded artifact checks are verified below. This
is not cryptographic signature, Android runtime or release signoff.
Worktree: `/private/tmp/cal-ai-play-20261109`, branch
`codex/android-play-readiness`, dirty snapshot from base `1edc992`.
The original main worktree and separate equipment feature remain untouched.

## Current build requests

| Format | EAS profile | Build ID | Last observed state |
| --- | --- | --- | --- |
| AAB | production | `3845bafe-01c2-4e15-9c49-8e289deda7ae` | FINISHED, downloaded and inspected |
| APK | preview | `4b96b896-ef91-42d7-9b1a-5a3c298aefac` | FINISHED, downloaded and inspected |

Official CLI readback on 2026-11-11 07:39 UTC matches the exact project,
owner and identifier below. AAB completed 2026-11-10T17:25:23.816Z and APK
2026-11-10T17:25:37.261Z. Full hashes, manifest/permission observations,
bundletool validation and 16 KB static checks are recorded in
[the current inspection report](ANDROID-INSPECTION-2026-11-11.md).

Official cached EAS CLI27.5, Android, `--freeze-credentials --non-interactive
--no-wait --json`, `EAS_NO_VCS=1`. Exact identifier/version read back:
`com.trustfirstnutrition.app`, `0.1.0`, code1. Existing dedicated remote key and
existing approved Free project used; no new key, credential export, billing
upgrade, auto-submit, Play upload or distribution. Output was limited to build
metadata; no signing secrets, provider keys or signed artifact URLs were printed.

Project UUID: `cd7254d2-d859-4992-8063-7f2492ba8351`.
Owner: `arche-trustfirstnutrition`; project: `trust-first-nutrition`.

The two earlier Nov11 queued builds were cancelled with no artifacts after
independent review findings. Nov10 downloaded binaries remain historical
evidence only and must not be distributed/uploaded as the current release.

## Source checkpoint

SHA-256 fingerprints of selected corrected files, not a claim that the entire
archive is cryptographically identified:

```text
1571cf591f1198624cd750ab80a0dffdd1fb1ccaf5ca77f968988afc19812a21  apps/mobile/App.tsx
27ef042d5b84ce77d9586658b0900604d748eff5d975bfee7a8c80130dba9464  apps/mobile/src/screens/TrainingScreen.tsx
70e345702313a96a542fafe3a44ba887ba19c11acdebd2002768e602b2368ebc  apps/mobile/src/screens/OnboardingScreen.tsx
01d1496de6b808edddc1d9cc0f63cef3d8d542203ddda08c338ff97430a15810  apps/mobile/src/session/profileRestore.ts
323f0b4f8d24926101dae45591247cd13a40c426a4f70f68a7fbf062b79756af  services/api/app/main.py
9a54486300255a058a163fcd5dbf64f30324a42a2e89ddc1007a2a977fabb9db  services/api/app/services/coach_repository.py
```

EAS excludes backend files; their fingerprints document the related local
release state, not inclusion in the mobile archive. Native API configuration
still targets the existing production hostname. Building mobile does not deploy
the backend or activate deletion/storage features.

## Fresh prebuild evidence and remaining gates

- Mobile19 explicit regressions plus existing async/API harness passed;
  shared/mobile TypeScript and store24 tests passed.
- Independent bounded review cleared age-block privacy access, confirmed-save
  reset, read-only retry, duplicate-save blocking and delayed default updates.
- API460 passed,1 optional-PG module skipped,1 existing deprecation warning;
  separate real isolated PostgreSQL16 run passed7 and was stopped/removed.
- Current artifact download, hashes, ZIP CRC, manifest/five permissions,
  bundletool validation, matching certificate metadata and 16 KB static
  alignment checks passed. Cryptographic signatures remain unverified: no
  usable cached jarsigner/apksigner CLI was found. Play-generated splits and
  16 KB runtime were not tested.
- Android installation and runtime remain unverified. No generated/web image
  substitutes for actual native store screenshots.
- Play app record exists, but no binary upload/test distribution/review/public
  release is established. Real provider erasure, public approved documents and
  production-source parity remain separate gates.

The earlier IN_QUEUE snapshot is superseded by the FINISHED readback above.
Neither static inspection nor a successful cloud build proves device behavior.
