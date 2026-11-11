# Owner decisions and release checklist - 2026-11-10

Status: owner review required, not legal attestation or release approval.
This checklist authorizes no external changes, sending, conversion or fees.
An app-registration request does not authorize accepting terms or attesting
compliance on the owner's behalf. No credentials belong in this document.

## Approved public contact

- App: Trust First Nutrition; operator display name: 아르케.
- Per-app public support email: areche.ai.kr@gmail.com (approved spelling).
- Mailbox control/delivery, legal identity and required business details remain
  unverified. The support address is not the Google login. Korean sole-proprietor
  status is owner-reported, not conversion approval.

## Owner actions and latest decisions

Use Leader-opened forms, without repeating setup or exposing values in chat,
docs, source, screenshots or logs. Form state comes from
[FOLLOWUP-2026-11-10.md](FOLLOWUP-2026-11-10.md); Leader reconfirms the exact
account/project at handoff. This checklist did not inspect live forms.

- [x] **1. Server key entered by owner:** privately enter the existing matching Cal AI Supabase
  server secret in Leader's Vercel form: `upglow/cal-ai-api`,
  `SUPABASE_SECRET_KEY`, type Secret, Production only. Supabase project must be
  `nojddnajbrowtcvcjvxv` in org `laeseopkkxsbbhbgobjt`. No rotation, client
  embedding or further production changes are implied; entry is not deletion proof.
  Owner reported completion; fresh Vercel metadata verified the variable is
  sensitive and Production-only. Its value was not read or decrypted. Matching
  provider authorization and actual deletion remain unverified.
- [x] **2. Reviewer credentials:** privately complete the prepared normal-user
  form in that Supabase project for a dedicated non-admin reviewer account with
  synthetic data. Use approved private handling and later Play's private
  sign-in-details form only. Leader verifies deployed, reusable, full-feature
  access without interactive OTP/MFA; creation alone is not access proof.
  Owner selected the support email and created a distinct Email-provider user;
  dashboard readback confirmed it is not the existing admin or Kakao identity.
  Old Preview profile loading hit a web API routing defect. After the same-origin
  correction, fresh owner login, synthetic goal/profile save, reload restoration,
  plan creation and partial workout save succeeded on 2026-11-11. Reviewer data
  remains; no identity was deleted. Effective non-admin authorization is still a
  separate server check, not inferred from normal navigation.
- [x] **3. App creation legal acknowledgment:** the owner declined Organization
  conversion and selected the existing Personal account with closed testing.
  Prepare that draft path without changing this multi-app account. The app form
  had name, Korean, App, Free and available package ID prepared. The owner
  completed the policy/export acknowledgments and app creation; exact app ID
  `4975788258134910868` was read back on the normal dashboard. This does not
  attest that deletion/operational readiness is complete. Play signing terms,
  review submission and public release remain separate gates.
- [x] **4. Private Play reviewer details:** the owner reported Add/Save after
  privately entering the existing Supabase review-user password and reviewing
  the access attestation. Separate app-content overview readback confirms
  login details are addressed. The credential-bearing form was not reread or
  captured. This is not a new credential login test or review submission.
- [x] **5. IARC terms:** the owner reported reviewing the terms and pressing
  Start. The agent completed factual questionnaire answers and saved the result;
  the separate overview confirms IARC complete, submitted 2026-11-11 16:38 KST.
  Korea3+/PEGI3/ESRB Everyone are content ratings, not a change to the approved
  18+ target audience. This did not submit the app for review.

## Legal inputs for action 3 - not approved terms

- **Audience approved 2026-11-11:** initial **18+**, not a Google mandate. New API
  onboarding and mobile validation accept self-reported ages **18-100**; notices
  are aligned in source. Legacy data stays readable; owner-scoped feature-access
  enforcement and preserved privacy/deletion controls pass local regressions.
  They are not yet deployed evidence. This is not verified age or guardian consent.
  Console 18+ target and known-minor discovery/download/purchase restriction
  were saved and confirmed on 2026-11-11. Content rating remains separate and
  is not inferred from the audience setting.
- **Sensitive data:** approve actual legal bases, purposes, required/optional
  processing, disclosure, consent and refusal consequences for health/body
  records, optional photos and AI. Body-AI consent alone is not comprehensive
  sensitive-data consent. Confirm operator, rights contact and effective date.
- **Overseas transfers:** confirm actual recipient entities, processor/third-party
  roles, countries, data items, purposes, timing/method, transfer basis, contracts,
  safeguards and refusal consequences. Provider options, `R2_REGION=auto` and
  `store=False` prove neither geography nor zero retention/training.
- **Retention:** settle records/results, photo bytes/metadata, auth, analytics/audit,
  deletion ledgers/keys, any enabled zero-byte guards, support mail, provider logs
  and backups. Source/example photo TTL is 30 days, not approved terms or proven
  production cleanup. Do not invent statutory periods, deletion deadlines,
  complete erasure or subscription cancellation. Disclose retained state/retries.
- **Play declarations:** align Data safety, deletion URL, health features and
  audience with deployed behavior. Nutrition/fitness is within Google's health
  definition; non-medical wording/community advice is not an account exemption.

## Optional eligibility inquiry - DRAFT, NOT SENT

Exact follow-up draft. Owner must confirm account verification status and product
facts before sending; this text is not itself verified production evidence.

> I operate as a Korean sole proprietor and already have a Personal
> Play developer account with other apps. I am preparing Trust First Nutrition
> (com.trustfirstnutrition.app): non-medical food photo nutrition estimates,
> calorie/protein and weight tracking, workout planning/logging, and optional
> body-photo check-ins. It does not diagnose or treat medical conditions. Does
> Play Console Requirements section 1.2 require converting this existing account
> to Organization before creating/submitting this health-and-fitness app? If so,
> what verification documents and D-U-N-S entity route are accepted for a Korean
> sole proprietor? Please confirm the route before I change this multi-app account.

Official references: [Console requirements](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en),
[health categories](https://support.google.com/googleplay/android-developer/answer/13996367?hl=en),
[account types](https://support.google.com/googleplay/android-developer/answer/13634885?hl=en),
[owner-only conversion procedure](https://support.google.com/googleplay/android-developer/answer/16260648?hl=en).
Published policy points to Organization when creating accounts; transition
applicability to every draft/test step in this existing account remains unresolved.
There is no established closed-test exemption or approval. Owner declined
conversion; proceed with truthful Personal-account draft preparation and use
support only for an actual account-specific blocker, with approval. Do not send
this optional inquiry automatically.

## Leader release verification

- [ ] Verify approved deployment, reviewer login, disposable provider deletion,
  public pages, retention and retries. Recorded production `/ready` HTTP 200,
  source tests or deletion acceptance do not prove these gates/full erasure.
- [ ] Verify Android runtime; keep Play creation, AAB acceptance, test distribution,
  review submission and public release separate. Recorded signed artifacts do
  not prove runtime or Google acceptance. No extra owner setup is requested here.

Evidence: [follow-up](FOLLOWUP-2026-11-10.md),
[source policy facts and unresolved legal/operational details](POLICY-FACTS-2026-11-10.md),
[release gates](RELEASE-GATES.md). These records are not new production checks.
