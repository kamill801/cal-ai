# PLAN: Trust-First AI Nutrition Logger

## Current Goal

Create developer-ready product, technical, and execution documents, then build an MVP that proves the trust-first food logging loop: photo scan, AI analysis, lightweight clarification, corrected meal save, dashboard update, and next-meal nutrient guidance.

## Development Principles

- Use `docs/PRD.md` for product decisions.
- Use `docs/TECHSPEC.md` for architecture, schemas, APIs, and safety contracts.
- Keep implementation sequence in this `docs/PLAN.md`.
- Do not hard-code final brand, colors, or pricing before Figma/design review.
- Prefer a working vertical slice over broad incomplete features.
- Preserve user trust: uncertainty, editability, and safety language are required.
- Do not implement medical diagnosis or competitor-clone UI.

## Milestones

### Milestone 0: Spec and Design Readiness

Goal: Lock the development brief before implementation.

Deliverables:

- `docs/PRD.md`
- `docs/TECHSPEC.md`
- `docs/PLAN.md`
- `DESIGN.md`
- Figma/design brief or generated design reference: https://www.figma.com/design/Sr0MXFZ5U6kOk69lcqu5Je
- Updated design decisions in PRD/TECHSPEC/PLAN

Verification:

- PRD has target user, MVP scope, non-goals, and user flows.
- TECHSPEC has architecture, data model, API contracts, AI pipeline, safety/privacy.
- PLAN has implementation milestones and acceptance criteria.

### Milestone 1: Project Scaffold

Goal: Create the base app/API workspace.

Recommended structure:

```text
apps/mobile/
services/api/
packages/shared/
docs/
```

Deliverables:

- Expo app scaffold
- FastAPI service scaffold
- shared schema package or generated OpenAPI types
- local env examples
- basic lint/type/test commands

Verification:

- Mobile app boots locally.
- API health check works.
- Repository has clear README run commands.

### Milestone 2: Onboarding and Target Calculation

Goal: User can create profile and receive initial nutrition target.

Tasks:

- Build onboarding screens.
- Implement profile API.
- Implement target calculation service.
- Add unsafe goal warnings.
- Persist profile and active target.

Acceptance:

- User completes onboarding in under 3 minutes.
- Required fields validate.
- Target calculation returns calories and macros.
- Unsafe/extreme goal input is softened or blocked.

### Milestone 3: Food Image Analysis Vertical Slice

Goal: User can upload a food image and receive structured analysis.

Tasks:

- Add image picker/camera UI.
- Add upload endpoint and object storage integration.
- Create `analysis_jobs` table.
- Implement queue/worker.
- Implement first AI vision analysis call with schema validation.
- Return analysis result with confidence and range.

Acceptance:

- User can submit a meal photo.
- Job status transitions through queued/running/completed or failed.
- Malformed AI output does not crash the app.
- Result includes calories, macros, items, confidence/range, and uncertainty reasons.

### Milestone 4: Clarification and Correction

Goal: User can improve estimate with 1-2 lightweight corrections.

Tasks:

- Implement clarification planner.
- Build clarification UI.
- Add rice amount, eaten ratio, broth, and sauce/oil controls.
- Apply corrections to analysis result.
- Store correction events.

Acceptance:

- App asks at most 2 questions.
- User can answer with taps/sliders.
- Calories/macros update after answers.
- Correction deltas are persisted.

### Milestone 5: Meal Save and Today Dashboard

Goal: User can save corrected meal and see daily progress.

Tasks:

- Add meal log save API.
- Add meal log item persistence.
- Build Today dashboard.
- Show calorie and macro progress.
- Show meal list.

Acceptance:

- Saved meals appear on dashboard.
- Daily totals update correctly.
- User can view saved meal details.
- Dashboard loads even if recommendation service fails.

### Milestone 6: Progressive Personalization

Goal: App begins to feel body-adaptive.

Tasks:

- Add weight log UI/API.
- Implement basic target adjustment suggestion.
- Implement correction history summary.
- Use recent logs to improve defaults.

Acceptance:

- User can log weight.
- After enough logs, app can suggest a calorie target adjustment.
- Adjustment includes plain-language explanation.
- User must accept before target changes.

### Milestone 7: Next-Meal Nutrient Guidance

Goal: App recommends nutrient/menu-type direction for the next meal.

Tasks:

- Implement nutrient gap calculation.
- Implement menu-type recommendation rules.
- Add controlled AI phrasing if needed.
- Build dashboard recommendation card.
- Add feedback event.

Acceptance:

- App identifies deficient/excess macros.
- App recommends menu types, not full recipes.
- Recommendation is goal-aware.
- User can mark recommendation helpful/not helpful.

### Milestone 8: Privacy, Safety, and QA Hardening

Goal: MVP is safe enough for private beta.

Tasks:

- Add image deletion controls.
- Add account/data deletion path.
- Add safety disclaimers.
- Add outlier detection.
- Add test fixtures for common meal types.
- Add analytics and error monitoring.

Acceptance:

- User can delete logs/images.
- Non-food or low-quality image is handled gracefully.
- Extreme calorie estimates are flagged.
- Core flows have automated tests and manual QA checklist.

## Task Checklist

### Spec Tasks

- Status: DONE
- Files: `docs/PRD.md`, `docs/TECHSPEC.md`, `docs/PLAN.md`
- Acceptance: three-file spec structure exists and separates product, technical, and execution concerns.
- Test method: manual review.

### Design Tasks

- Status: IN_PROGRESS
- Files likely affected: `DESIGN.md`, `docs/PRD.md`, `docs/TECHSPEC.md`, `docs/PLAN.md`, future Figma file
- Acceptance:
  - provisional design contract exists in `DESIGN.md`
  - editable Figma MVP screen board exists
  - final or provisional brand name selected
  - color palette and typography selected or explicitly marked provisional
  - core screens designed or referenced
  - component states defined in `DESIGN.md`
  - docs updated with design contract
- Test method: design review and screenshot comparison.

### Implementation Tasks

- Status: IN_PROGRESS
- Files affected so far: `apps/mobile`, `services/api`, `packages/shared`, `README.md`, root workspace config
- Acceptance: milestones 1-8 completed.
- Test method: local dev, API tests, app smoke tests, manual mobile flow QA.

Current scaffold status:

- Root npm workspace exists.
- Expo mobile scaffold exists with provisional `DESIGN.md` tokens and mock Today screen.
- FastAPI scaffold exists with health, onboarding target calculation, and mock dashboard endpoints.
- Shared TypeScript API contract package exists.
- API tests and mobile/shared typechecks pass.

## Session Plan

### Session 1: Design Alignment

- Use Figma plugin or design tooling to create app direction.
- Decide final visual language and core screens.
- Update the three docs with design decisions.

### Session 2: Scaffold

- Create Expo and FastAPI project structure.
- Add database and env templates.
- Add health checks and basic CI-ready commands.

### Session 3: Onboarding and Targets

- Implement onboarding flow.
- Implement target calculation.
- Persist profile and target.

### Session 4: Food Analysis Slice

- Implement image upload.
- Implement analysis job.
- Integrate first AI structured result.

### Session 5: Clarification and Save

- Build correction UI.
- Apply correction logic.
- Save meal and update dashboard.

### Session 6: Personalization and Recommendation

- Add weight logs.
- Add target adjustment.
- Add nutrient gap and next-meal recommendation.

### Session 7: QA and Private Beta Prep

- Safety guardrails.
- Analytics.
- Error handling.
- Test fixtures.
- Private beta checklist.

## Risks

### Product Risks

- Users may still find 30 seconds too slow.
- Users may distrust AI estimates even with clarification.
- Too much nutrition detail may feel overwhelming.

### Technical Risks

- Vision model estimates may vary across calls.
- Nutrition DB mapping for Korean foods may be weak.
- Portion estimation is inherently uncertain.
- Async job UX can feel slow if not designed well.

### Privacy and Legal Risks

- Food logs and body data are sensitive.
- Medical-adjacent user expectations must be managed.
- Image retention must be explicit.

### Design Risks

- Final UI/design may change component assumptions.
- Paywall and pricing are intentionally deferred.

## Done Definition for MVP

MVP is done when:

- User can complete short onboarding.
- User can scan/upload a meal photo.
- AI returns structured food/nutrition result.
- Result shows uncertainty and confidence/range.
- User can answer 1-2 clarification questions or adjust with sliders.
- User can save the meal.
- Dashboard updates daily calories/macros.
- User can log weight.
- App can suggest a calorie target adjustment after enough data.
- App can suggest next-meal nutrient/menu-type guidance.
- Privacy deletion path exists.
- Safety guardrails prevent medical overclaims and extreme restriction encouragement.

## Handoff Prompt for Codex CLI / OMX

```text
You are working in /Users/dd/Documents/cal-ai.

Read these files first:
- docs/PRD.md
- docs/TECHSPEC.md
- docs/PLAN.md
- DESIGN.md
- .omx/specs/deep-interview-cal-ai-ideation.md

Build according to docs/PLAN.md. Preserve the product direction:
- trust-first food logging
- AI clarification instead of manual entry
- progressive personalization
- next-meal nutrient/menu-type guidance

Do not implement final pricing, final brand/colors, or a competitor-clone UI unless the docs have been updated after design review.

Start with the current milestone requested by the user, make a small verified change, run relevant checks, and report changed files and verification evidence.
```

## Quality Standards

### UX

- Main flow must be mobile-first.
- Corrections must be tap/slider based.
- User should not need to manually search multiple foods for a normal scan.

### AI Output

- Structured JSON only for saved nutrition estimates.
- Confidence/range required.
- Uncertainty reasons required.
- Malformed output must be rejected or retried.

### Data Privacy

- Images private by default.
- Sensitive profile data protected.
- Delete controls available.
- No training use without opt-in.

### Error Handling

- Non-food image: clear retry message.
- Low-quality image: ask to retake.
- AI timeout: retry or save manual note.
- DB mapping failure: fallback with low confidence.

### Mobile Behavior

- Works on common iOS/Android viewport sizes.
- Large tap targets.
- No text overflow in buttons/cards.
- Slow network states are visible.

### Test Coverage

- Unit tests for target calculation.
- Unit tests for correction math.
- API tests for onboarding, analysis job, meal save.
- Fixture tests for AI result schema validation.
- Manual QA for full scan-to-save flow.
