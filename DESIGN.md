# Design

## Source of truth

- Status: Draft, active for MVP implementation until Figma review replaces or refines it.
- Last refreshed: 2026-06-13
- Primary product surfaces:
  - Mobile app first: onboarding, today dashboard, scan/camera, analysis result, clarification, meal save, insight/coach, settings/privacy.
  - Optional web/PWA surfaces later: landing page, account, support, privacy.
- Evidence reviewed:
  - `docs/PRD.md`
  - `docs/TECHSPEC.md`
  - `docs/PLAN.md`
  - `concept.html`
  - `assets/meal-preview.png`
  - `/Users/dd/Downloads/DESIGN-clay.md`
  - Figma MVP screen board: https://www.figma.com/design/Sr0MXFZ5U6kOk69lcqu5Je
  - Cal AI App Store page, FatSecret App Store/site, DoingLab FoodLens product page for product-pattern benchmarking only.
- Important boundary:
  - Competitor references inform common user expectations, not visual cloning. Do not copy Cal AI, FatSecret, FoodLens, Clay, or any other product's trade dress, exact layout, screenshots, logo, wording, or distinctive brand assets.
- Figma status:
  - Initial editable MVP screen board exists in Figma.
  - Created screens: Onboarding, Today Dashboard, Scan Loading, Analysis Result, Clarification Sheet, Coach Insight.
  - Redesign loop boards exist in Figma:
    - Pass 1 `19:2`: direction exploration.
    - Pass 2 `20:2`: real meal evidence and review flow.
    - Pass 3 `21:2`: native sheet refinement.
    - Pass 4 `23:2`: confidence/range system refinement.
  - Treat Pass 3 as the main implementation baseline and borrow Pass 4's confidence/range semantics selectively.

## Brand

- Working name:
  - Product name is still TBD.
  - `HANIP AI` may be used as a temporary concept label only.
- Personality:
  - Calm, precise, body-aware, warm, practical.
  - Professional but not stiff: the app should feel like a careful coach who notices details, not a clinical dashboard.
  - More like a careful nutrition assistant than a loud diet challenge app.
  - Friendly enough for daily use, but restrained enough to make calorie estimates feel trustworthy.
- Trust signals:
  - Calorie ranges instead of false precision.
  - Confidence labels with plain-language uncertainty reasons.
  - Visible assumptions such as rice amount, sauce/oil, broth, eaten ratio.
  - One or two high-impact correction questions before save.
  - Clear privacy controls for food photos and body data.
  - Target changes are suggested and user-approved, not silently applied.
- Avoid:
  - Exact competitor UI/brand mimicry.
  - Shame, guilt, punishment, or "you failed" language.
  - Overpromising exact calories from photos.
  - Long quiz aesthetics.
  - Medical diagnosis, disease-specific advice, or guaranteed body outcomes.
  - Heavy gamification as the main retention system.
  - App surfaces dominated by one hue family; the UI should not become all-green, all-cream, or all-purple.

## Product goals

- Goals:
  - Make food logging feel fast enough to repeat daily while being more trustworthy than instant photo guesses.
  - Let the user confirm rather than manually build a meal from database search.
  - Make personalization visible within the first several days through target correction, nutrient-gap insight, and next-meal menu-type guidance.
  - Support both fat-loss and muscle-gain users under one promise: "your body-aware nutrition plan."
- Non-goals:
  - Do not design a generic landing page as the primary experience.
  - Do not prioritize recipe generation, grocery shopping, barcode-first logging, voice-first logging, or multi-day meal plans in MVP.
  - Do not make a clinic, trainer console, or medical dashboard in V1.
- Success signals:
  - User understands the estimate and why it may be uncertain.
  - User can complete scan-to-save in about 30 seconds when the photo is good.
  - Clarification feels like one helpful tap, not extra manual work.
  - Today dashboard makes the next best meal direction obvious without nutritional overload.

## Personas and jobs

- Primary personas:
  - Body recomposition user: wants to lose fat or gain muscle without obsessing over every gram.
  - Gym user: cares about protein and macro consistency, repeats many meals, wants faster logging.
  - Diet restart user: has tried calorie apps, churned because manual logging was annoying or AI estimates felt wrong.
- User jobs:
  - "I took a meal photo. Help me turn it into a believable log quickly."
  - "Tell me which variable matters most for this estimate."
  - "Remember how I usually eat and stop asking the same thing."
  - "Based on today, tell me what kind of next meal fits my goal."
  - "Adjust my target when my actual body trend says the first estimate was off."
- Key contexts of use:
  - One-handed logging before eating, after eating, or while outside.
  - Korean/Asian mixed meals with rice, soup, sauce, side dishes, and hidden oil.
  - Post-workout or dieting moments where protein and calories matter.
  - Low patience moments; the design must assume the user may abandon if asked to type.

## Information architecture

- Primary navigation:
  - Home: today dashboard, remaining calories/macros, next-meal guidance, recent meals.
  - Scan: camera/upload entry point. This should be the most prominent repeated action.
  - Log: saved meals, daily/weekly history, weight logs.
  - Coach: target adjustment suggestions, nutrient insights, personalization explanations.
  - Profile/Settings: goal, body info, privacy, notifications, subscription later.
- Core routes/screens:
  - Onboarding start
  - Body/goal/activity setup
  - Initial target confirmation
  - Today dashboard
  - Camera/upload
  - Analysis loading
  - Analysis result
  - Clarification bottom sheet
  - Corrected result confirmation
  - Meal detail/edit
  - Weight log
  - Coach insight
  - Privacy/settings
  - Paywall later
- Content hierarchy:
  - Level 1: Current action or decision, such as scan, confirm, save, adjust target.
  - Level 2: Main nutrition number or recommendation.
  - Level 3: Confidence, range, macros, assumptions, and correction controls.
  - Level 4: Explanation, safety notes, provenance, and advanced details.

## Design principles

- Principle 1: Trust beats speed theater.
  - The app may take roughly 30 seconds if that produces a more believable log.
  - Never hide uncertainty just to look smarter.
- Principle 2: Ask only when the answer changes the estimate.
  - Max two clarification questions before save.
  - Default controls are choice chips, segmented controls, steppers, or sliders.
  - Freeform text is optional and secondary.
- Principle 3: Make correction feel like confirmation.
  - The user should feel they are validating AI work, not doing manual data entry.
  - Show the calorie/macro effect after a correction.
- Principle 4: Personalization should be earned visibly.
  - Explain when the app is learning from repeated corrections or weight trends.
  - Suggested target changes require explicit accept/decline.
- Principle 5: Calm health language.
  - Avoid guilt. Use directional guidance.
  - Focus on the next useful choice rather than judging the previous meal.
- Principle 6: Warm professionalism.
  - Keep the analysis expert-level, but make the surface feel human, appetizing, and easy to return to every day.
  - Avoid sterile report-card layouts, heavy tables, and overly clinical confidence language on the main path.
  - Use warmth through food photography, soft contrast, optimistic microcopy, and small completion moments rather than mascots or decorative clutter.
- Tradeoffs:
  - Use fewer decorative elements inside the app than Clay-style marketing pages.
  - Prefer dense, scannable controls over oversized editorial sections.
  - Prioritize clarity of numbers and correction controls over expressive illustration.

## Visual language

- Target visual position:
  - `Warm Trust Nutrition`: trustworthy enough for nutrition decisions, warm enough for daily consumer use.
  - The strongest axis is trust plus cleanliness. The missing axis to strengthen before implementation is visual warmth.
  - Do not chase cuteness as the main identity. Add lightness through rounded food thumbnails, friendly Korean copy, saved-state delight, and generous breathing room.
  - The app should not feel like a medical report, spreadsheet, or generic AI assistant.
- Color:
  - The palette borrows warmth from the Clay reference but shifts toward a food/nutrition product.
  - Base canvas: `#fffaf0` for warm app background where appropriate.
  - App paper: `#fbfaf6` for main mobile screen background.
  - Surface: `#ffffff` for cards, panels, sheets, and controls.
  - Surface soft: `#f5f0e0` or `#eef4ec` for low-emphasis bands.
  - Ink: `#0a0a0a` or `#20221f` for primary text.
  - Body: `#3a3a3a`; muted: `#6a6a6a`; soft muted: `#9a9a9a`.
  - Hairline: `#e5e5e5` or `#d8ded2`.
  - Primary CTA: near-black `#0a0a0a` for final confirmation and paywall actions.
  - Nutrition primary: deep leaf `#2f6540` for positive progress, confidence, and scan action.
  - Protein accent: blue `#4b8397`.
  - Carbs accent: ochre `#e8b94a` or `#cc8a25`.
  - Fat accent: coral/tomato `#d35b45` or `#ff6b5a`.
  - Energy accent: peach `#ffb084`.
  - Insight accent: lavender `#b8a4ed`, used sparingly.
  - Warning: `#f59e0b`; error: `#ef4444`; success: `#22c55e`.
  - Do not use gradient-orb or bokeh backgrounds.
  - Color usage:
    - Use warm off-white as the ambient base, but keep primary content cards white so the app does not become beige.
    - Use deep leaf only for meaningful progress, confidence, and primary scan/save actions.
    - Use protein blue, carbs ochre, and fat coral as small semantic accents, not page-wide themes.
    - Add small peach or amber warmth around meal context and saved-state moments; do not overuse it in analysis panels.
- Typography:
  - App UI should use Inter or the platform system stack: `Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.
  - Korean rendering should be verified with a Korean-capable fallback such as `Apple SD Gothic Neo`, `Pretendard`, or system sans if installed.
  - Clay's display personality can inform marketing headlines, but product UI should stay more functional.
  - Letter spacing is `0` in product UI.
  - Use large numerals for calories and compact labels for macros.
  - Suggested mobile type scale:
    - Display number: 48-56px, weight 750-850, line-height 0.95.
    - Screen title: 22-28px, weight 700-800, line-height 1.15.
    - Section title: 16-18px, weight 650-750, line-height 1.3.
    - Body: 14-16px, weight 400-550, line-height 1.45-1.55.
    - Caption: 11-13px, weight 600-750, line-height 1.35.
    - Button: 14-16px, weight 700-850.
- Spacing/layout rhythm:
  - Base unit: 4px.
  - Mobile horizontal padding: 16px.
  - Tight repeated UI gaps: 8px.
  - Section gaps: 12-20px.
  - Major screen blocks: 24-32px.
  - Marketing or presentation screens may use larger 48-96px rhythm, but the app should not.
- Shape/radius/elevation:
  - Product UI card radius: 8px by default.
  - Buttons/inputs: 8px by default.
  - Photo/camera frame: 8-12px.
  - Device mockups or marketing illustrations may use larger radii, but in-app cards should stay compact.
  - Elevation should be minimal: hairline borders first, soft shadows only for modals/sheets/device mockups.
- Motion:
  - Use motion to explain analysis progress, confidence narrowing, and saved-state confirmation.
  - Keep motion short, interruptible, and reduced-motion friendly.
  - Avoid decorative loops during repeated daily logging.
- Imagery/iconography:
  - Food photos are the primary visual asset.
  - Generated/illustrated assets may support onboarding and marketing, but should not compete with meal evidence.
  - Use simple line icons from the implementation icon set, preferably lucide if available.
  - Use icons for camera, close, back, save, info, edit, settings, privacy, and chart actions.
  - Never use another app's screenshots or product UI fragments as in-app assets.
- Warmth and delight:
  - Use a real meal photo thumbnail in analysis, clarification, result, and saved states so the interface keeps a connection to the user's food.
  - Add a small positive saved confirmation, such as `기록했어요` plus the updated remaining calories, rather than a large celebratory screen.
  - Use one friendly sentence per decision point. Example: `밥 양만 확인하면 범위가 꽤 줄어요.`
  - Keep animation functional: range narrowing, selected chip response, saved confirmation. Avoid decorative loops.
  - Avoid cartoon mascots, emoji-heavy UI, confetti, and childish copy unless a later brand decision explicitly chooses a cute identity.

## Components

- Existing components to reuse:
  - No production component library exists yet.
  - `concept.html` provides provisional screen direction and token inspiration only.
- New/changed components:
  - `AppShell`: mobile safe-area wrapper with warm paper background.
  - `TopBar`: title/subtitle plus one icon action.
  - `BottomNav`: Home, Scan, Log, Coach/Profile.
  - `ScanCTA`: primary camera action, visually stronger than other dashboard cards.
  - `MealPhotoFrame`: image preview, crop/quality overlay, confidence badge.
  - `AnalysisResultPanel`: calorie range, confidence, detected foods, assumptions.
  - `ConfidenceMeter`: label plus progress visualization; must include text, not color only.
  - `MacroSummaryGrid`: protein/carbs/fat values with separate accent colors.
  - `ClarificationSheet`: one focused question, answer chips/slider, skip affordance, recalculated summary.
  - `PortionChoice`: selectable chip/row with estimated grams or portion labels.
  - `PortionSlider`: bounded slider for eaten ratio, rice amount, sauce/oil level when needed.
  - `NutritionGapCard`: deficient/excess nutrients with next-meal direction.
  - `TargetAdjustmentCard`: proposed calorie/macro target adjustment with accept/decline.
  - `MealLogRow`: thumbnail, meal name, confidence/source state, kcal.
  - `WeightLogInput`: simple numeric input with date.
  - `PrivacyControlRow`: image retention, delete image, delete account.
  - `Paywall`: later; must not block first design iteration unless pricing is decided.
- Variants and states:
  - Buttons: primary, secondary, ghost/icon, destructive, disabled, loading.
  - Cards: default, selected, warning, insight, low-confidence, error.
  - Scan: idle, uploading, queued, analyzing, needs clarification, completed, failed, retry.
  - Clarification: unanswered, answered, recalculating, skipped, saved.
  - Confidence: high, medium_high, medium, low.
  - Recommendation: deficit, excess, balanced, unavailable.
- Token/component ownership:
  - `DESIGN.md` owns product-level design decisions until a coded theme file exists.
  - Future implementation should move tokens into a shared design-token file and keep names traceable to this document.
  - Figma components should use the same component names where possible.

## Accessibility

- Target standard:
  - Mobile-friendly WCAG AA as the practical baseline.
  - Touch targets at least 44px high/wide, with 48px preferred for primary actions.
- Keyboard/focus behavior:
  - Web/PWA surfaces must have visible focus states.
  - Mobile forms must support hardware keyboard and screen-reader navigation where applicable.
- Contrast/readability:
  - Color is never the only signal for confidence, error, warning, or macro state.
  - All key numbers must include labels and units.
  - Body copy must remain readable in Korean and English.
- Screen-reader semantics:
  - Camera actions, confidence labels, calorie ranges, and macro values need descriptive accessibility labels.
  - Progress bars need text equivalents.
  - Icon-only buttons need accessible names.
- Reduced motion and sensory considerations:
  - Respect reduced-motion settings.
  - Do not use flashing, pulsing urgency, or diet-shame visual signals.

## Responsive behavior

- Supported breakpoints/devices:
  - Primary: common iOS/Android phone sizes.
  - Secondary: small phones around 320-360px wide.
  - Later: tablet and web/PWA.
- Layout adaptations:
  - Phone: single-column, bottom nav, bottom sheets for clarification.
  - Small phone: reduce card padding before reducing font size; keep action labels intact.
  - Tablet/web: dashboard may become two columns with today summary left and log/coach right.
  - Do not scale font size with viewport width.
- Touch/hover differences:
  - Touch surfaces need clear pressed/selected states.
  - Hover states are optional and secondary for web.
  - Do not depend on hover to reveal critical nutrition or safety information.

## Interaction states

- Loading:
  - Scan upload: show image thumbnail and upload state.
  - AI analysis: show current stage, such as checking photo, identifying foods, narrowing estimate.
  - Avoid fake precision like a constantly changing kcal number.
- Empty:
  - Dashboard: one primary scan CTA, no guilt language.
  - Log: invite first meal scan, no blank table.
  - Coach: explain that insights unlock after enough logs without sounding like a paywall.
- Error:
  - Non-food image: clear retry action.
  - Low-quality image: retake guidance.
  - AI timeout: retry and optional save-as-note fallback.
  - Nutrition mapping failed: low-confidence estimate with clear caveat or retry.
- Success:
  - Meal saved: brief confirmation and dashboard update.
  - Clarification answered: show narrowed range or changed kcal/macros.
  - Target accepted: show new target and effective date.
- Disabled:
  - Disabled actions must explain missing requirement when tapped or nearby.
  - Do not make disabled primary actions look like low-contrast text.
- Offline/slow network:
  - Allow queued image upload if feasible later.
  - Show retry and preserve user-selected answers.
  - Dashboard should load saved local/previous data even if recommendations fail.

## Content voice

- Tone:
  - Calm, precise, nonjudgmental, Korean-first.
  - Expert in substance, warm in delivery.
  - Speak like a careful coach, not a hype-driven influencer.
- Terminology:
  - Use `예상`, `범위`, `신뢰도`, `사진상 확인 어려운 부분`, `보정`, `다음 식사`.
  - Use `단백질`, `탄수화물`, `지방`, `칼로리`, `나트륨`, `식이섬유` for common nutrition labels.
  - Use `목표 조정 제안`, not `자동 변경`.
- Microcopy rules:
  - Prefer "약 540-710kcal로 보여요. 밥 양이 가장 큰 변수예요."
  - Avoid "정확히 623kcal입니다."
  - Prefer "밥 양만 확인하면 범위가 꽤 줄어요."
  - Avoid "정확도 개선을 위해 추가 입력이 필요합니다."
  - Prefer "기록했어요. 저녁은 단백질을 조금 더 챙기면 좋아요."
  - Avoid "저장 완료. 일일 목표 대비 잔여 영양소를 확인하세요."
  - Prefer "다음 식사는 단백질을 보충하고 지방은 낮추는 쪽이 좋아요."
  - Avoid "오늘 식단은 실패했어요."
  - Keep primary button text action-based: `식사로 기록`, `정확도 높이기`, `목표 조정 확인`.
  - Do not use visible onboarding/tutorial copy to explain every feature inside the core app UI.

## Implementation constraints

- Framework/styling system:
  - Recommended implementation remains React Native Expo for mobile and FastAPI for API unless the techspec changes.
  - Use repo-native styling once scaffolded; avoid introducing a design-system dependency before the app exists.
- Design-token constraints:
  - Start with the tokens in `Visual language`.
  - Put colors, radii, spacing, and typography in a central theme module once the mobile app is scaffolded.
  - Keep token names semantic, such as `color.background.app`, `color.action.primary`, `radius.card`, `space.screenX`.
  - Avoid hard-coded random hex values in component files after the theme module exists.
- Performance constraints:
  - Camera and analysis screens must feel responsive on common phones.
  - Food images need reasonable resizing/compression before upload.
  - Dashboard should not block on recommendation generation.
- Compatibility constraints:
  - Korean text must not overflow buttons/cards.
  - Large numbers must reserve stable dimensions so layout does not jump.
  - Safe areas must be respected on iOS and Android.
- Test/screenshot expectations:
  - Before calling UI work done, verify at least one small phone, one modern iPhone-sized viewport, and one Android-sized viewport.
  - Check no horizontal overflow, no clipped Korean text, no overlapping fixed bottom nav, and visible loading/error states.

## Open questions

- [ ] Final brand name / owner: founder / impact: logo, app store listing, tone.
- [ ] Figma visual direction / owner: founder + Codex / impact: final palette, icons, screen layouts.
- [ ] Korean font decision / owner: design/dev / impact: typography fidelity across Android and iOS.
- [ ] Paywall pricing and trial / owner: founder / impact: subscription screens and copy.
- [ ] Food image retention default / owner: product/legal / impact: privacy UI and settings.
- [ ] Whether MVP includes web/PWA alongside Expo / owner: product/dev / impact: responsive component scope.
- [ ] Final macro/micronutrient depth for dashboard / owner: product / impact: information density.
