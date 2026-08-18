# PLAN: Trust-First AI Nutrition Logger

## Current Goal

Build a trust-first body transformation MVP that connects food-photo logging, protein tracking, recovery and weight check-ins, optional body-photo observations, workout prescription, progress, and weekly coaching. Keep real AI providers, authentication, and production privacy operations behind explicit approval gates.

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

- [x] Connect mobile scan flow to FastAPI analysis job API using a deterministic local image reference.
- [x] Add API client and shared snake_case to camelCase mappers for analysis jobs.
- [x] Add OpenAI backend analysis provider interface with deterministic mock default.
- [x] Add malformed structured-output retry/fail-closed tests.
- [x] Standardize provider/validation API error details for mobile consumption.
- [x] Preserve distinct provider error codes for provider unavailable, dry-run scaffold, and malformed structured output.
- [x] Keep OpenAI disabled unless `AI_PROVIDER=openai` and a server-side API key are configured.
- [x] Add image picker/camera UI.
- [x] Add mock/local upload endpoint and upload-ready mobile analysis flow.
- [x] Add private R2 presigned upload API flow with local fallback.
- [x] Add local persistence repository boundary for analysis jobs and image upload metadata.
- [x] Add Neon Postgres persistence for upload metadata and analysis job references.
- [x] Create persistence-backed production `analysis_jobs` storage through Neon/Postgres.
- [ ] Add a queue/worker if production latency or traffic outgrows the synchronous Vercel MVP path.
- [x] Implement the first OpenAI Responses API vision call with strict schema validation.
- [x] Return analysis result with confidence and range.

Acceptance:

- User can submit a meal photo.
- Job status transitions through queued/running/completed or failed.
- Malformed AI output does not crash the app.
- Result includes calories, macros, items, confidence/range, and uncertainty reasons.

### Milestone 4: Clarification and Correction

Goal: User can improve estimate with 1-2 lightweight corrections.

Tasks:

- [x] Build first rice-amount clarification UI in the scan-to-save slice.
- [x] Submit clarification answers through the FastAPI mock API.
- [x] Apply clarification result and range narrowing in mobile state.
- [x] Add loading/error/retry handling for clarification submission.
- [ ] Implement clarification planner.
- [ ] Add eaten ratio, broth, and sauce/oil controls.
- [x] Add local persistence repository boundary for clarification events.
- [ ] Store production correction events.

Acceptance:

- App asks at most 2 questions.
- User can answer with taps/sliders.
- Calories/macros update after answers.
- Correction deltas are persisted.

### Milestone 5: Meal Save and Today Dashboard

Goal: User can save corrected meal and see daily progress.

Tasks:

- [x] Add mock meal log save API contract and mobile client call.
- [x] Save meal through the scan-to-save flow and reflect saved impact.
- [x] Show updated mock Today dashboard after save.
- [x] Add loading/error/retry handling for meal save.
- [x] Preserve provider error codes through mobile `ApiClientError` and reducer state.
- [x] Add local persistence repository boundary for meal log records.
- [ ] Add production meal log item persistence.
- [ ] Build production Today dashboard.
- [ ] Show calorie and macro progress.
- [ ] Show meal list.

Acceptance:

- Saved meals appear on dashboard.
- Daily totals update correctly.
- User can view saved meal details.
- Dashboard loads even if recommendation service fails.

### Milestone 6: Progressive Personalization

Goal: App begins to feel body-adaptive.

Tasks:

- [x] Add weight log UI/API.
- [x] Implement basic target adjustment suggestion.
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

- [x] Implement nutrient gap calculation.
- [x] Implement menu-type recommendation rules.
- Add controlled AI phrasing if needed.
- Build dashboard recommendation card.
- Add feedback event.

Acceptance:

- App identifies deficient/excess macros.
- App recommends menu types, not full recipes.
- Recommendation is goal-aware.
- User can mark recommendation helpful/not helpful.

### Milestone 9: Training and Recovery Coach

Goal: Turn profile and recovery context into an actionable training week.

Tasks:

- [x] Add training frequency, experience, equipment, and session time context.
- [x] Generate persisted workout days with exercises, sets, reps, RIR, rest, and rationale.
- [x] Record completed exercises, session duration, and RPE.
- [x] Add energy, sleep, and soreness check-ins.
- [x] Reduce training emphasis when recovery signals are low.

### Milestone 10: Body Progress Check-in

Goal: Support optional body-photo progress without unsafe visual claims.

Tasks:

- [x] Reuse private direct upload for body check-in images.
- [x] Persist front/side/back check-ins and limited observations.
- [x] Feed training-focus observations into workout-plan rationale.
- [x] Explicitly exclude body-fat estimation, diagnosis, and pain-cause inference.
- [ ] Replace mock body observation provider after separate privacy and paid-call approval.

### Milestone 11: Integrated Weekly Coach

Goal: Combine nutrition, training, weight, recovery, and body-check-in evidence.

Tasks:

- [x] Add Today, Training, Progress, and Weekly Coach navigation.
- [x] Show protein target, consumed amount, remaining amount, and next action.
- [x] Generate evidence-counted weekly wins, focus items, and next-week actions.
- [x] Gate calorie adjustment suggestions behind minimum evidence.
- [x] Require confirmation instead of automatically changing nutrition targets.

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
- Expo mobile app includes onboarding, scan-to-save, Today, Training, Progress, Weekly Coach, and safety/privacy screens using the Cute Trust visual system.
- FastAPI scaffold exists with health, onboarding target calculation, and mock dashboard endpoints.
- Shared TypeScript contracts cover nutrition, uploads, coach dashboard, body check-ins, workout plans, progress, and weekly reports.
- API tests and mobile/shared typechecks pass.

Body transformation loop summary — 2026-07-20:

- Implemented: persisted coach profiles/events/workout plans; local profile session restore; profile/day-scoped meal accumulation; protein remaining guidance; weight and recovery logs; private-upload body check-ins with safe mock observations; personalized workout basis; workout completion; progress and weekly coach; evidence-gated target-adjustment suggestions.
- Storage hardening: R2 completion now checks the private object with server-side HEAD and verifies existence, content length, and content type before metadata becomes ready.
- Verified locally: 57 API tests, shared/mobile typechecks, mobile API/async/session smoke, iOS Expo export, 320px/390px rendered visual QA, and browser scan-to-save interaction QA.
- Provider boundary: real OpenAI food vision is implemented behind server-side env configuration; body-photo AI remains mock and food vision still needs deployed live-call QA before production claims.
- Product boundary: authentication/user scoping, account/image deletion, analytics/monitoring, and store/device beta validation remain release-readiness work.

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

- [x] Implement analysis job API client integration for the mock vertical slice.
- [x] Add backend analysis provider interface and deterministic mock provider.
- [x] Add OpenAI Responses API food-vision adapter and structured-output validation tests.
- [x] Add mobile loading/error/retry semantics for create/fetch/poll.
- [x] Implement mock/local image upload seam.
- [x] Integrate the first real AI structured result behind explicit server-side provider configuration.

### Session 5: Clarification and Save

- [x] Build correction UI for rice amount.
- [x] Apply correction logic through FastAPI mock API.
- [x] Save meal and update dashboard through FastAPI mock API.
- [x] Standardize API/mobile error semantics for provider, validation, network, timeout, and retryability.
- [x] Refine provider errors so mobile distinguishes `analysis_provider_unavailable`, `analysis_provider_dry_run`, `analysis_output_malformed`, and `network_error`.

Session summary — 2026-06-14:

- Implemented: mobile scan-to-save now runs through FastAPI mock APIs; backend has mock-first/OpenAI-ready provider boundaries; API/mobile error semantics now use structured `detail.code/message/retryable/kind` and mobile retry behavior distinguishes retryable vs non-retryable failures.
- Verified: mobile smoke, shared/mobile typecheck, API tests, `git diff --check`, code-review lanes, and UltraQA-style verifier were run during the session.
- Historical next step at that time: image storage, persisted jobs, and real OpenAI calls were still deferred. These are now implemented as described in the 2026-07-22 summary below.

Follow-up summary — 2026-06-14:

- Implemented at that time: provider exception mapping established safe unavailable, dry-run, and malformed-output codes; mobile `ApiClientError` and reducer state preserved retry behavior. The provider has since advanced to a real opt-in OpenAI adapter.
- Verified: mobile smoke, shared/mobile typecheck, API tests, and `git diff --check` pass; final review/QA evidence is attached to the Ultragoal ledger for this session.
- Historical next step at that time: OpenAI, storage, auth, DB, and payment were gated. OpenAI food vision, R2, and Neon are now implemented; auth and payment remain gated.

Persistence foundation summary — 2026-06-14:

- Implemented: server-local sqlite repository boundary for image upload metadata, analysis jobs, clarification events, and meal log records while preserving mock provider/API contract behavior.
- Verified: persistence records survive new repository instances; final command/review evidence is attached to the Ultragoal ledger for this session.
- Historical next step at that time: production DB, object storage, auth, and OpenAI were gated. Neon, R2, and OpenAI food vision are now implemented; auth/user scoping remains gated.

MVP readiness summary — 2026-07-15:

- Implemented: mobile onboarding target flow, camera/photo-library entry points, selected meal image propagation through analyze/review/saved screens, safety/privacy checkpoint screen, direct-upload API adapter use, and env-based CORS for Expo Web preview.
- Verified: local API plus Expo Web click QA covers onboarding calculation, dashboard entry, and safety screen navigation; mobile smoke, shared/mobile typecheck, API tests, and `git diff --check` pass.
- Remaining from that checkpoint: production/device verification, auth/user scoping, and retention/deletion APIs. The R2 and OpenAI food-vision code paths are now implemented but still require one deployed Android live-flow verification.

### Session 6: Personalization and Recommendation

- [x] Add weight logs.
- [x] Add evidence-gated target adjustment suggestions that require confirmation.
- [x] Add nutrient gap and next-meal recommendation.
- [x] Add workout plan/session, recovery, body check-in, progress, and weekly coach loops.

OpenAI food-vision integration summary — 2026-07-22:

- Implemented: private R2 images are read through short-lived presigned GET URLs; the FastAPI OpenAI provider sends an image input to the Responses API with a strict JSON schema and `store: false`; normalized results are persisted for fetch, clarification, and meal save.
- Reliability: malformed structured output is retried once and then fails closed; provider/configuration failures return safe structured errors without exposing credentials or signed URLs.
- Runtime: Vercel uses a bounded synchronous MVP path with a 60-second function limit. A queue/worker remains a scale-up decision rather than an internal-beta blocker.
- Remaining proof: deploy the current code and run one real Android meal-photo flow against production. Body-photo AI, authentication, monitoring, Supabase identity deletion, and Play release remain separate approval/readiness gates.

### Session 7: QA and Private Beta Prep

- [x] Safety guardrails for nutrition, body-image observations, and workout guidance.
- [ ] Analytics and monitoring.
- [x] Structured error handling and retry semantics.
- [x] Deterministic test fixtures and rendered browser QA.
- [ ] Real-device private beta checklist.
- [x] Profile-scoped app-data deletion controls for meal, coach, and image records.

### Session 8: Trust and Repetition Quality Pass

- [x] Empty-safe onboarding with experience, equipment, and session-duration inputs.
- [x] Honest dashboard and weekly-coach empty states without fabricated praise or baseline scores.
- [x] Persisted daily meal history on the coach dashboard.
- [x] User-confirmed meal name, calories, and macro correction before save.
- [x] Equipment-, experience-, duration-, recovery-, and body-focus-aware deterministic workout plans.
- [x] Front, side, and back body-photo capture selection with explicit consent.
- [x] Profile/account-scoped app-data deletion, including unsaved scans and linked private storage objects.
- [x] Retryable image-deletion tombstones plus a daily TTL cleanup endpoint and Vercel Cron schedule protected by `CRON_SECRET`.
- [x] Deterministic post-validation rejects schema-valid body-analysis output containing sensitive inferences.
- [x] Legacy body check-ins without consent metadata remain readable during rolling deployment.
- [ ] Supabase Auth identity deletion after re-authentication.
- [ ] Production deployment verification and Android real-device E2E.

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
