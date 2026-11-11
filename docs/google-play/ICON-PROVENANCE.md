# Trust First Nutrition icon

Prepared 2026-11-09 from the existing approved mascot, not a new character.
Built-in image generation was used; no project API key or paid provider call
was used by the application. Binary masters remain in `assets/brand/source`.

## Art direction and generation prompts

Reference: `apps/mobile/assets/mascot/mascot-coach.png`.
Keep the ivory pear/rice-drop face, two dark eyes, curved smile, peach cheeks,
two green leaves, green neck scarf and ivory heart. Remove limbs, clipboard,
props and all text. Preserve the established soft-clay 3D identity.

Foreground prompt: transparent square with just the head and scarf; front view,
calm smile, generous clear margins, no shadow outside the subject. Generated
with real alpha. Adaptive-circle containment is enforced in the export step.

Opaque icon prompt: same head and scarf centered on a pale mint `#dcefe4`
full-bleed square; complete leaves/scarf visible, no pre-rounded corners,
letters, badges, mockups or borders. Keep a legible large face and balanced
margins. Generated background has soft material/studio variation, not UI art.

## Deterministic exports

Run `node apps/mobile/scripts/export-brand-icons.cjs` from the repository root.
This uses the existing Expo dependency `jimp-compact` only for export sizing
and adaptive safe-zone placement. No new runtime dependency was added.

| Asset | Purpose |
| --- | --- |
| `apps/mobile/assets/brand/app-icon.png` | 1024px opaque Expo/iOS fallback icon |
| `apps/mobile/assets/brand/adaptive-foreground.png` | 1024px alpha Android foreground; visible pixels inside central circle |
| `apps/mobile/assets/brand/favicon.png` | 48px web favicon |
| `docs/google-play/assets/play-icon-512.png` | 512px opaque Play listing icon |
| `docs/google-play/assets/kakao-icon-128.png` | 128px Kakao app icon, below 250KB |

Asset generation and source configuration are not proof of a native signed
build or an accepted store upload. Kakao upload requires save/readback;
Play assets remain local until app creation and the relevant upload gate.
