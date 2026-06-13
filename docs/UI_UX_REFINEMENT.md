# UI/UX Refinement: Warm Trust Nutrition

## Status

- Date: 2026-06-13
- Purpose: final design direction before mobile implementation.
- Decision: use Figma Pass 3 as the base and selectively add Pass 4 confidence/range semantics.
- Implementation should wait for founder review, then move into the coded mobile app.

## Design Judgment

The current redesign is strong on trust and clarity, but it still needs more consumer-app warmth. The product should not become cute-first, because calorie and nutrition estimates need credibility. It also should not become clinical, because daily food logging is emotional, repetitive, and easy to abandon.

The target is:

```text
Expert analysis, warm surface.
Precise enough to trust, soft enough to use every day.
```

## What Is Already Working

- Trust-first structure: photo evidence, calorie range, confidence, and one high-impact correction.
- User role: the user confirms the AI work instead of manually building a meal.
- MVP realism: the flow is implementable without inventing a huge design system.
- Pass 3 visual direction: more native, cleaner, and less AI-template-like than the original Figma screen.

## What Needs To Be Filled

- Add warmth through food photography, microcopy, and saved-state feedback.
- Reduce clinical language in the main path.
- Make colors feel appetizing without becoming all-cream or all-green.
- Make confidence/range information glanceable instead of report-like.
- Give the final save moment a small emotional reward.

## Final Visual Direction

### Personality

- Professional, calm, and precise.
- Warm, daily, and food-aware.
- Not cute as a mascot-heavy app.
- Not clinical as a medical dashboard.
- Not glossy as a generic AI productivity app.

### Color

- Base: warm off-white, but use white cards for clarity.
- Primary: deep leaf green for scan, save, progress, and confidence.
- Accents:
  - Protein blue for protein.
  - Ochre for carbs.
  - Coral for fat.
  - Peach/amber only for small warmth moments.
- Avoid:
  - Full-screen green themes.
  - Beige-on-beige low contrast.
  - Purple AI gradients.
  - Decorative orbs, blobs, and bokeh.

### Layout

- Keep Pass 3's native mobile feel.
- Use fewer, stronger sections instead of many cards.
- Use one primary action per screen.
- Keep photo evidence visible across analysis, clarification, and result.
- Bottom sheets should feel like quick confirmation, not forms.

### Typography

- Large, confident calorie range.
- Small, plain confidence labels.
- Korean copy should have enough line height and should not be squeezed into tiny chips.
- Avoid oversized marketing-style headings inside app screens.

## Main Flow To Implement

### 1. Analyze Evidence

Primary feeling: "The app is carefully checking my food."

Required elements:

- Real meal photo thumbnail.
- Stage text such as `음식 구성 확인 중`.
- Confidence grouping:
  - `확실`
  - `추정`
  - `확인 필요`
- Initial range such as `약 620-780 kcal`.
- One calm explanation: `밥 양과 소스가 범위를 크게 바꿀 수 있어요.`
- Primary action only when ready: `밥 양만 확인하기`.

Avoid:

- Fake exact progress percentages.
- Constantly changing kcal numbers.
- Long AI-generated explanations.

### 2. One-Tap Clarification

Primary feeling: "This is quick, not manual logging."

Required elements:

- Question: `밥 양이 어느 정도였나요?`
- Friendly helper: `이것만 확인하면 범위가 꽤 줄어요.`
- Three or four chips:
  - `반 공기`
  - `한 공기`
  - `많음`
  - optional `잘 모르겠어요`
- Show immediate effect:
  - Before: `620-780 kcal`
  - After: `640-710 kcal`
- Primary action: `결과 확인`.

Avoid:

- Asking multiple things at once.
- Gram entry as the primary control.
- Form-like visual density.

### 3. Review Result

Primary feeling: "I understand the estimate and can trust it enough to save."

Required elements:

- Main range or center estimate with range nearby.
- Confidence label, not just a color.
- Macro row with protein, carbs, fat.
- Detected foods with assumption labels.
- Small explanation: `밥 양은 확인했고, 소스는 사진상 추정했어요.`
- Primary action: `식사로 기록`.
- Secondary action: `수정`.

Avoid:

- Hiding uncertainty in a tooltip only.
- Showing too many nutrition details before save.
- Making the user feel judged.

### 4. Saved Impact

Primary feeling: "Good, I logged it. Now what?"

Required elements:

- Small saved confirmation: `기록했어요`.
- Updated remaining calories.
- One next-meal suggestion:
  - `저녁은 단백질을 조금 더 챙기면 좋아요.`
- A clear way back to dashboard.

Avoid:

- Confetti or celebration-heavy UI.
- A sterile success toast with no useful next step.

## Microcopy Rules

Use:

- `약 640-710kcal로 보여요.`
- `밥 양만 확인하면 범위가 꽤 줄어요.`
- `사진상 소스 양은 추정했어요.`
- `기록했어요. 저녁은 단백질을 조금 더 챙기면 좋아요.`
- `잘 모르겠다면 그대로 저장해도 돼요.`

Avoid:

- `정확히 673kcal입니다.`
- `추가 입력이 필요합니다.`
- `분석 정확도 개선을 위해 값을 선택하세요.`
- `일일 목표 대비 잔여 영양소를 확인하세요.`
- `오늘 식단은 실패했습니다.`

## Component Decisions

- `MealPhotoFrame`: always include the actual meal image when available.
- `ConfidencePill`: text plus color; never color-only.
- `CalorieRange`: stable width and large numerals.
- `ClarificationSheet`: one question per sheet.
- `RangeNarrowing`: small before/after visual, not a full chart.
- `SavedImpact`: replaces generic toast with useful next step.
- `MacroSummary`: compact row, accent colors only.

## Acceptance Criteria Before Development Is Called Done

- The scan-to-save path feels warm and human, not clinical.
- The user can understand why the number is a range.
- The clarification step feels like one helpful tap.
- Korean text does not clip on small phones.
- The palette is not dominated by one hue family.
- The result screen has one primary action and one secondary edit path.
- The saved state shows both confirmation and next useful guidance.

## Founder Review Prompt

Review for these questions:

1. Does this feel trustworthy enough for calorie logging?
2. Does it feel warm enough to use every day?
3. Is the app too clinical, too cute, or about right?
4. Should the final brand lean more premium, friendly, or minimal?
