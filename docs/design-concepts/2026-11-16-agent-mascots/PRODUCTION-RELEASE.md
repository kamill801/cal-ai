# Kongbi production release - 2026-11-16

## Released

- Product: Trust First Nutrition, existing `upglow/cal-ai-api` project.
- Production: https://cal-ai-api.vercel.app/
- Deployment: `dpl_FiWHNS52GA2M9eaF4pryLEoa34W3`, READY / production.
- Immutable URL: https://cal-ai-c6c1sxq25-upglow.vercel.app/
- Source: `ca357c898ef17a9741edd81dec11b176b2e2947f` on
  `codex/kongbi-mascot-20261116`.
- Parent release branch: `codex/play-release-finish-20261115`.
  The dirty main worktree and separate equipment feature were not merged or edited.
- A sealed, committed-source allowlist contained 104 runtime source files.
  Manifest SHA-256:
  `d24416aa93c1d4a3b77a17a191119cbbcfd279467a7d7b1878a1129c927fd320`.
  Local environment files, credentials, test helpers, design masters and the
  inert visual-preview entry were not included in the deployment source.
- The production alias was promoted only after the new deployment reached READY
  and passed read-only health, readiness, policy and web-bundle checks.

## Character Scope

- Kongbi is the sole runtime mascot and primary launcher/favicon design.
- Seven poses: welcome, meal, analysis, workout, progress, coach and celebration.
- Food logging uses the meal pose; analysis and clarification use the inspecting
  pose; training uses the flexing pose; progress uses the measuring pose;
  coaching uses the coaching pose; saved impact uses celebration.
- Approved concepts 01 Kongbi and 02 Duri remain byte-identical to the originals.
  Revised 03 Moa is an alternate design draft, not deployed in the app.
- Existing layout, palette, auth, consent and backend behavior were preserved.
  The 320px onboarding header was adjusted to avoid cramped word wrapping.

## Fresh Evidence

- Shared and mobile TypeScript checks passed.
- Mobile smoke: 39 passed. Store/artwork regression suite: 58 passed.
- Production web export and final Android JavaScript export passed.
- Independent bounded source review: no actionable findings.
- Local inert fixture: 13 actual screen components at 320x800, 390x844 and
  1365x900. All 39 cases had loaded images, no document horizontal overflow,
  and no detected mascot/text overlap. See `qa/layout-results.json`.
- Real production browser: login rendered Kongbi with working image loading at
  all three viewport sizes and no document horizontal overflow. See
  `qa/production-login-390.jpg` and `qa/production-layout-results.json`.
- Canonical production metadata resolved to the new deployment after promotion.
- Both immutable and canonical `/health` and `/ready` returned HTTP 200 / ok.
  Database, R2, food OpenAI, body mock, Supabase auth and admin configuration
  checks remained ok. Readiness does not establish real provider analysis.
- The canonical web bundle matched the immutable deployment bundle SHA-256:
  `8d9e2c6e1be78063323cdc77c90cc639ba4851b5ffc3502f188ea36db6f20243`.
- All seven live mascot PNGs matched the committed local files byte-for-byte.
  The live favicon matched the production web-export favicon. See
  `qa/production-release-results.json` for hashes and timestamps.

## Safety And Limits

The existing production lifecycle settings were explicitly preserved as false
for this deployment and independently read back through the public policy page:

```text
ACCOUNT_DELETION_ENABLED=false
ACCOUNT_DELETION_WORKER_ENABLED=false
R2_WRITE_ONCE_UPLOADS_ENABLED=false
IMAGE_RETENTION_ENABLED=false
```

No user records, uploaded photos, account consent or remote keys were changed.
No real AI analysis, new EAS build, Play release, external Kakao icon upload,
account deletion or retention cleanup was performed. CLI health checking needed
an argument-order workaround; no product code or protection setting was changed
to resolve that local CLI issue.

The updated native icon files will take effect in a subsequent APK/AAB/iOS
build. This web deployment does not update already installed native binaries.
Authenticated record writes and physical-device behavior were not retested as
part of this visual-only release. The unchanged full API suite was not rerun.
