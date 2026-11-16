# Cal AI mascot concepts - 2026-11-16

Status: owner selected Kongbi as primary mascot and app icon on 2026-11-16.
Concepts 01/02 are preserved byte-for-byte. Only concept 03 was regenerated.
Generated with the built-in image_gen tool. Names are provisional creative labels, not trademark-cleared product names.

## Reference review

- Pickle official press kit: https://pickle.com/press-kit
  Observed: compact soft volumes, simple eyes, a recognizable family of silhouettes.
  Do not copy: Hangul-consonant silhouettes, the four-lobed representative character, or existing face proportions.
- vooy official service and character-system page: https://vooy.com/ko and https://recruit.vooy.com/
  Observed: geometric companions and expressions/motion tied to task state.
  Interpretation: the user's "보이" was treated as vooy (부이), not independently confirmed by the user.
  Do not copy: existing geometric body outlines, specific faces, or brand marks.
- Keyring official landing page: https://agentic.shopport.ai/keyring/landing
  Observed: tactile collectible charm rendering and distinct character silhouettes/accessories.
  Do not copy: the cloud, penguin or cherry characters, eyewear, or keychain composition.

Borrowed principles only: ownable silhouette, restrained expressive face, approachable tactile finish,
and actions that reflect food logging and exercise rather than generic celebration.

## Candidates

1. Kongbi / 콩비: asymmetric pistachio bean, subtle yellow wristband, food-and-health warmth.
2. Duri / 두리: ivory rounded tofu cushion, green inset tag, calm friendly everyday coaching.
3. Moa / 모아: original pointed droplet rejected; `03-moa-v2.png` is the revised
   squat sky-blue pudding pebble with a tiny yellow patch. Draft only, not in-app.

Each PNG includes a hero, app-icon study, food pose, and exercise pose.
The app-icon studies are previews, not release-ready Android adaptive icon exports.

## Production Application

- Kongbi is the sole in-app mascot. Duri remains an unchanged alternate concept.
- Seven transparent 512px rasters: welcome, meal, analysis, workout, progress,
  coach and celebration. Their generation masters remain in
  `apps/mobile/assets/mascot/source/`; run
  `node apps/mobile/scripts/export-kongbi-assets.cjs` to reproduce exports.
- Primary icon exports use an opaque mint Kongbi master. The adaptive foreground
  uses the welcome cutout within the existing mask-safe circle. Run
  `node apps/mobile/scripts/export-brand-icons.cjs` to reproduce them.
- Launcher, favicon, Play 512px and Kakao 128px files are updated locally.
  This does not mean an existing APK, Play draft or Kakao developer setting has
  been updated. Those external/native release steps are separate.

## Original Concept Review

- Three distinct body silhouettes and palettes, not color-only variants.
- Each full-body view visibly has two arms and two feet.
- The identity is consistent across each sheet's poses.
- Icon studies are recognizable at presentation size; real 32px raster QA has not been run.
- The original concept generation did not change UI or release settings.
  The subsequent owner-approved Kongbi application is recorded below.

## Deliverables

- 01-kongbi.png and 01-kongbi.prompt.md
- 02-duri.png and 02-duri.prompt.md
- 03-moa.png and 03-moa.prompt.md
- 03-moa-v2.png and 03-moa-v2.prompt.md
- kongbi-production.prompt.md and QA evidence in `qa/`

## Verification

- `01-kongbi.png` SHA-256:
  `ce833964f26ee06070d3ac7fd04c7f22add9dd12de0a64fb4a5d5e1ca9a4db3d`.
- `02-duri.png` SHA-256:
  `777d3af9fedc3b38b24c2d8150eb71ce2bc0a0f46f357d13e02827a586b1202e`.
  Both independently match the original main-worktree copies.
- Browser fixture: 13 scenes at 320x800, 390x844 and 1365x900; 39 layout checks
  found no document horizontal overflow, unloaded images or mascot/text overlap.
  A cramped 320px onboarding heading was fixed and rechecked at all three sizes.
- `qa/layout-results.json` and mobile JPEGs are local inert-fixture evidence,
  not proof of authenticated production writes, paid analysis or device behavior.
- Isolated entry `apps/mobile/scripts/kongbi-visual-preview.tsx` uses real screen
  components with fixture props and inert callbacks. To reproduce, temporarily
  point `apps/mobile/index.js` at it, export to a temporary web directory, then
  restore the production entry before any release. A regression test enforces
  the real production entry, and release packaging excludes the fixture entry.
- Independent bounded review found no actionable source regressions. Auth,
  consent, API, database, deletion flags and signing configuration are unchanged.
