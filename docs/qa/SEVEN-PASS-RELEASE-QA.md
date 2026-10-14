# Cal AI finite release QA

Run: `cal-ai-equipment-2026-10-14`, maximum **7** passes. Native Codex;
no OMX mode or Goal activated. Feature branch: `codex/equipment-photo-guide`.
Baseline: `23e372995fc65fd33722af8aec5c7158ef98f932`.

## Boundaries

- Preserve existing screens, features, tokens, approved mascots, user data,
  owner authorization, quotas and consent gates. Do not merge main.
- Local browser: `http://127.0.0.1:8098`; API: `http://127.0.0.1:8034`.
  Isolated SQLite fixture, local storage, deterministic providers, auth disabled
  only by this local process environment. No production settings changed.
- Paid provider attempt budget for this run: **0**. No credentials or signed
  upload URLs are recorded. The sample photo is the app's bundled meal asset.
- Public production/authenticated E2E, real Postgres/R2 and native device checks
  are separate gates. Passing mocks does not establish AI accuracy or release
  readiness. This run prepares code; it does not authorize production promotion.

## Pass ledger

The first four reservations below were reconstructed from this session's tool
evidence after the updated skill was saved. Their numbers are retained, not
reset; subsequent reservations are persisted before inspection. Backend and
numeric subagent work contribute to pass 3, not additional hidden passes.

| Pass | Phase | Finding / planned batch | Evidence / disposition |
| --- | --- | --- | --- |
| 1 | Complete | Baseline and retained-feature inspection; no fixes | API 232 passed; Expo web export; browser onboarding, targets, dashboard, workout plan, equipment catalog and guide |
| 2 | Complete | Stale equipment selection after a new/no-result search; component-local tokens differed | Browser reproduction: no-result proceed enabled before fix, disabled after; shared canvas/radius/type tokens applied |
| 3 | Complete | Invalid workout/weight fields; receipt persistence and cancellation cleanup retries | Numeric 37/47 red before fix, 47/47 green after; backend five regressions red before fix, 47 equipment and 157 targeted green; full API 243 passed |
| 4 | Complete | Blank meal macros accepted as zero; saving while manual edits unapplied | Browser recheck: both actions disabled for blank macro; cancel restores 34g; valid 600kcal/40g adjustment saved, 1970kcal/90g remaining |
| 5 | Complete | Cross-feature persistence/recovery; workout draft lost on tab return, no wellness save feedback | Recheck retained bench checkbox and 35kg across Today/Training; server-confirmed wellness 3/5/2 shown after reload. Privacy/back and payment-disabled paths verified; admin typecheck/six smoke checks pass |
| 6 | Complete | Responsive and independent review: inactive-screen modal, retry during meal editing, acknowledged partial workout draft | Browser before/after retry: visible -> count 0 while editor open, primary save disabled. Partial workout save now clears selection, remains disabled after tab return; history increased 1->2. Active-screen invalidation reviewed statically, authenticated refresh still unverified. Typecheck and web export pass. 320px last equipment CTA fits (379-431); 1280px guide has no overflow. Backend independent review: no actionable findings; real Postgres/R2 still unverified |
| 7 | Complete | Partial-workout coaching wording and final regression | Regression first failed on false no-record headline; repair acknowledges partial records without awarding completion/score. Final API 244 passed. Browser: two partial records recognized with completion count 0; forced API outage preserved four selected exercises across tab changes; retry after recovery saved one completed session, cleared selections, advanced to plan B and showed history 3 / completed 1. Weekly/all-time window and misleading workout error title remain unresolved. No further repair allowance |

Started: **7**. Completed: **7**. Stop reason: pass cap reached; required release
matrix is not clear. No eighth pass or automatic continuation run is permitted.
Verification of the frozen final batch is complete. New defects are recorded
below, not silently repaired outside the cap.

## Outcome

**HOLD: not ready for public release.** Local retained-feature checks improved,
but two confirmed defects and authenticated/provider/native evidence gaps remain.
No commit, push, merge or new deployment was performed in this run. The earlier
Preview and production deployments do not contain these uncommitted repairs.

The existing theme, typography definitions and approved bitmap assets were not
replaced. Equipment screens now reuse their tokens and the existing training
mascot. Features were not removed to achieve a pass. Local auth/provider flags
are test-process configuration, not changes to deployed protections.

## Unresolved defects

1. **Weekly aggregation uses all-time history.**
   `services/api/app/services/coach.py:387` reads all meal, workout, weight,
   wellness and body records without a week boundary. The UI labels the result
   "this week" and recommends next-week actions. Long-term users can receive
   misleading counts, scores and advice. Next repair: define a timezone-aware
   week window, filter consistently, and test previous-week/current-week/boundary
   records. This is a release defect, not an AI-quality pass.
2. **Workout transport failure is titled as onboarding failure.**
   The final browser fault test showed the onboarding-save error title on the
   Training screen. `apps/mobile/App.tsx` uses
   `onboardingFlowErrorFromUnknown` for coach mutations. Draft preservation and
   recovery work, but the message misidentifies the failed action. Next repair:
   use action-appropriate error mapping and regression-test workout, weight,
   wellness and meal-history mutation failures.

## Retained-feature matrix

| Scenario | Local evidence | External/remaining gate |
| --- | --- | --- |
| Goal onboarding and calculation | Browser: blank initial required inputs; goals returned and started | Nutrition recommendations are not medical diagnosis |
| Today totals, protein remaining, recent meals | Browser: personalized targets; three meals total 1900kcal / 122g protein; 670kcal / 8g remaining after refresh | Authenticated production ownership not run |
| Meal library selection, preparation, upload, analysis, clarification | Bundled sample selected; local upload/mock job; half-bowl correction reached review | Real camera, private R2 upload and OpenAI quality not run |
| Meal manual adjustment, save, history and editing | Browser: blank macro blocks apply/save; cancel restores 34g; 600kcal / 40g adjustment saved; failed-save retry hidden during editing; repeat updates totals/history | Browser delete-confirmation automation did not complete; backend deletion tests are not browser deletion proof. Authenticated production ownership not run |
| Workout plan, checked exercises, load/reps and history | Numeric 47-case smoke; browser draft survives tab return and transport failure; acknowledged partial/full saves reset draft; full save advances next plan and history; submissions/edits guarded while pending | Native/device lifecycle and real network interruption not run; misleading transport-error title remains |
| Equipment catalog, guide, search and return | Manual route with today-plan association and safe YouTube search link | Photo provider disabled locally; real photo/YouTube provider not run |
| Equipment upload/receipt/privacy/quota/concurrency | API regression suite | Real Postgres/R2/provider pending |
| Weight, recovery and progress | Browser: 71.8kg and server-confirmed recovery 3/5/2 retained after reload and other-feature mutations; strict numeric validation | Actual multi-week trend/adaptive guidance not validated |
| Body photo consent, view, delete and safe observation | Retained without bypassing protection | Local auth-disabled gate intentionally blocks body photos; native/authenticated E2E pending |
| Weekly coach and adjustments | Browser partial-only record recognized without completion points; final full session produces completed count 1 and partial count 2; inadequate-data target-adjustment gate retained | FAIL: all-time history presented as weekly. Multi-week/adaptive and semantic quality not proven |
| Privacy, account/session, data deletion | Privacy/back paths and API tests; protection gates retained; inactive equipment panel abort/invalidation statically reviewed | Kakao/Supabase login/callback, token-refresh modal behavior, account deletion and authenticated body-photo flow not run |
| Billing and separate admin | Payment-disabled/back path; admin six smoke checks, typecheck and production build passed; no payment/provider changes | Authenticated admin/data analytics and production E2E not run; billing intentionally disabled |
| Fonts, assets, responsive widths, touch and keyboard | Existing font/theme/assets retained; 320/390/1280 browser checks, no horizontal overflow in sampled equipment screens; 320px last catalog CTA visible; images loaded | Actual device font rendering, keyboard, camera and permission handling not run |

## Final-revision checks

- API: **244 passed, 1 warning** (existing Starlette/httpx TestClient
  deprecation). Used the existing main-worktree Python runtime because this
  feature worktree has no `.venv`; this was not an unmodified `npm run test:api`.
- Mobile smoke: pass, including strict numeric **47 cases**, async/API/session
  and equipment checks. Shared and mobile TypeScript checks: pass.
- Admin: **6 smoke checks**, TypeScript and Vite production build: pass.
  The first typecheck attempt was sandbox-blocked while writing build metadata;
  the rerun completed with exit 0.
- Expo web export: pass. Final local bundle:
  `index-e8198e42e5dfe43b544ca7bfc16d609d.js` (2.66 MB).
- Python compile and `git diff --check`: pass.
- Independent read-only frontend review: no additional actionable source
  findings; dynamic leader checks still found the error-title defect above.
  Backend review: no additional actionable findings; real Postgres/R2 remain
  separate unverified gates. Reviews do not override the unresolved defects.
- Final browser save/recovery checks used the exported bundle and isolated
  SQLite fixture, not production. Provider attempts/cost: **0 / 0**.

Visual evidence (local files, not published):

- `/private/tmp/cal-ai-seven-pass-equipment-390.jpg`
- `/private/tmp/cal-ai-seven-pass-equipment-1280.jpg`

The browser's temporary viewport override was reset. The local browser tab and
local servers remain available for inspection; they are not production builds.

## Required Before Release

- Repair both confirmed defects in a separately authorized new bounded run.
- Verify Kakao/Supabase callback and user ownership without exposing credentials.
- Run private R2 + real Postgres + actual equipment-photo provider E2E and
  independently assess identification/guide quality. Real paid calls need a
  specific bounded approval; this run does not supply one.
- Verify body-photo consent/upload/view/delete with an authenticated account,
  and admin-only login/access with the actual deployed configuration.
- Finish browser deletion confirmation and iPhone/Android camera, album,
  keyboard, permissions, back navigation and upload tests. Local fixtures do
  not replace actual-device proof.
- Only then use the existing feature branch for an authorized commit/push and
  Preview release. Do not merge main or promote production without approval.

## Reusable Workflow

Updated existing `$service-qa-release` to v2 instead of creating a duplicate.
It records the retained-feature matrix, inspect/fix/verify reservations, a hard
seven-pass ceiling, paid-call budget, authenticated evidence boundaries and
separate release authorization. Native `/goal` can support continuation but
does not perform this QA protocol or replace its cap.

Saved and validated in Codex/agents, `Documents/Skills`, and the versioned
`LLM-Wiki` source plus operating bundle/catalog. Agent evidence: five bundles,
20 resource hashes, YAML/reference validation; Wiki index 230 documents and
doctor 0 issues. Existing v1 preserved. No cloud publication was performed.

## Environment and release notes

Public Supabase Auth settings endpoint currently responds HTTP 401 without an
API key: hostname is reachable. This does not prove Kakao login/callback success.
Earlier DNS failure evidence is not a current failure claim.

The feature worktree does not contain `.venv`; use the existing runtime:

```sh
/Users/dd/Documents/cal-ai/services/api/.venv/bin/python -m pytest services/api/tests
```

Main worktree has unrelated uncommitted changes, preserved unchanged. Existing
Preview and production deployments predate these repairs; no new deployment is
claimed by this report.
