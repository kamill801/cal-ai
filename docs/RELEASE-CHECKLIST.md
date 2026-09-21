# Private Beta Release Gate

## 2026-09-07 Local Implementation Pass

Implemented authenticated `/v1/profiles/me` discovery, cross-device profile restoration, retry/signout on discovery failure, same-tab web Kakao PKCE redirect, and web-only callback session detection. Native OAuth retains its existing browser-session code exchange.

Admin reads now have a 20-second timeout, cancellation on selection/session change, no-store requests, explicit HTML-fallback errors, and removal of previously displayed data on authorization failure. First-visit and recent-five-minute activity labels do not claim exact Auth signup or socket presence. Empty funnels no longer report 100% abandonment.

Fresh evidence after explicit resume: API suite 194 passed (one existing TestClient deprecation warning); mobile/shared/admin typechecks and mobile smoke passed; six fixture-only admin API smoke checks passed. The suite includes SQL owner filtering before deserialization and one-query admin user aggregation regression tests. Admin build and final single-worker Expo web export passed before the pause; interrupted earlier exports are not passes.

Browser verification after resume: local sample meal photo selection, mock analysis, one-bowl clarification, review, save and page-reload restoration all passed. The saved 675 kcal meal updated remaining calories to 2085 and protein to 114 g for the synthetic test profile. No browser errors were returned by the bounded error-log check. The earlier photo connection error did not reproduce; no CORS or security policy was loosened. Local presign and preflight checks returned 200. This does not verify real R2, OpenAI or authenticated production flows.

Independent re-review found no actionable remaining findings. Focused component coverage for transient profile restore failure followed by successful retry, and provider sign-out failure rendering, remains a test gap; the existing mobile smoke suite is not a substitute for real OAuth E2E.

Local API is explicitly isolated: `127.0.0.1:8015`, temporary SQLite, mock food/body AI, local storage, no production credentials and admin disabled. This is a functional mock test environment, not authenticated production verification.

The in-app browser currently redirects the Cal AI Supabase Users page to sign-in. Owner Auth user/allowlist configuration remains unverified. Sign in to the existing Cal AI project; do not create another project. Production publication approval was requested separately. No production changes in this pass yet.

Still gated: owner Auth user/password and allowlist, deployment, two-user real login/ownership E2E, approved real-food analysis, legal policy sign-off, and device tests. Exact provider signup timestamps need a trusted Auth sync; current admin reports first app visit. Groble checkout/webhooks remain disabled until the merchant contract and configuration are supplied. Body-photo AI remains mock and must not be marketed as live visual coaching.

## 2026-09-05 Status

Release is blocked pending owner account setup, deployment, and real authenticated E2E. Local tests are not provider or device E2E.

Local evidence: full API suite 187 passed (one existing TestClient deprecation warning); after the final unknown-alias throttle fix, 13 login tests passed again. Shared/mobile/admin typechecks, mobile smoke, admin build and `git diff --check` passed. Local admin form renders username/password fields with password masking and no horizontal overflow. A pattern scan of 50 modified/untracked files found no matching private-key credentials; this is not a guarantee against all possible secrets.

Web export remains unverified: the first invocation rejected an out-of-project output path; subsequent in-project and offline CLI attempts stalled without output and were stopped. Real provider login, hosted PostgreSQL concurrency and Android device E2E were not run. No production deployment or credential changes were performed in this pass.

Read-only production observations:

- Main web renders the Kakao login screen.
- `/ready` reports Supabase auth, R2 and food OpenAI configured; body analysis remains mock.
- Unauthenticated `/v1/dashboard/today` returns 401.
- `/internal/admin/overview` currently serves HTML fallback, not the new admin API.
- `https://cal-ai-admin.vercel.app` returns Vercel `DEPLOYMENT_NOT_FOUND`.
- Current browser Supabase account redirects away from the Cal AI project to another organization's project list. Owner must switch accounts.

## Owner Setup

1. Open the existing Cal AI Supabase project, Authentication > Users > Add user > Create new user.
2. Enter an owned email and a new unique password directly in the provider dashboard. Never use a password shared in chat; never put a password in source, documentation or env vars.
3. Configure API-only values: `ADMIN_LOGIN_USERNAME`, `ADMIN_LOGIN_EMAIL`, `ADMIN_SUPABASE_PUBLISHABLE_KEY`, `ADMIN_USER_IDS` (created user's UUID). Keep `ADMIN_DASHBOARD_ENABLED=false` until this identity is confirmed.
4. Verify `ADMIN_SUPABASE_URL` and the admin frontend `VITE_SUPABASE_URL` identify the same project; configure matching asymmetric JWT algorithm.
5. Enable the owner-only dashboard, deploy the main API and the separate `apps/admin` Vercel project. No admin links belong in the consumer app. URL separation is not an authorization boundary; API checks enforce owner access.

## Authenticated Release Checks

- Owner can log in by chosen ID; incorrect credentials return a generic error, rate limiting returns 429, a valid non-owner token returns 403 for admin data.
- Two distinct Kakao accounts complete login and onboarding. A's profile, meals, photos and workouts are inaccessible to B, including switching accounts while requests are in flight.
- Food photo selection, compression, private direct upload, real analysis, clarification, save, refresh and history succeed. Paid analysis requires an approved small call budget.
- Logout/login restores the same account's saved profile. Server-owned cross-device discovery is implemented locally; verify it with two devices after deployment. Legacy anonymous profiles are not claimed by a signed-in user automatically.
- Deleting app data removes profile-linked media and identifiable analytics; verify R2 deletion and Neon persistence remotely with disposable owner-approved records.
- New auth/consent policies and legal links must be finalized by the owner before inviting users; explain mock body analysis honestly.
- Verify real Android camera/gallery/permissions and upload on a tester's device before Android release. Web rendering does not prove Android behavior.

Do not send a public test invitation until these checks pass. Commit only intended paths after tests and secret scans. Never capture auth request or response bodies in monitoring.
