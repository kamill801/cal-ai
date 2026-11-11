# Play policy and account-type check

Observed 2026-11-09. This is release preparation, not legal approval or a
Google eligibility determination. No policy declarations were accepted.

## Evidence and interpretation

- Console home for developer `7707482448795132061` visibly identifies ARCHE
  Labs as a personal account. The list contains the unrelated Ilsang draft
  and existing UPGLOW closed-test app, not Trust First Nutrition. No change
  was made to either app or the developer account.
- The owner reports being a sole proprietor. No business number or identity
  documents were collected by the agent. That report has not been independently
  verified and does not automatically authorize an organization conversion.
- [Play Console Requirements](https://support.google.com/googleplay/android-developer/answer/10788890?hl=en)
  was read directly in the browser after search-tool retrieval timed out.
  Its full policy lists health apps, with medical/research examples, under
  services requiring organization registration. Its summary cannot override
  the full policy.
- [Account-type guidance](https://support.google.com/googleplay/android-developer/answer/13634885?hl=en)
  was also read directly. It distinguishes personal from business use and
  repeats the health-app wording; organization verification includes D-U-N-S.
- [Health categories](https://support.google.com/googleplay/android-developer/answer/13996367?hl=en)
  explicitly includes fitness/nutrition tracking within health and fitness.
  This app's planned nutrition, weight and workout functionality belongs in
  the health declaration; describing it as not medical does not remove the
  need for that declaration.
- Counterevidence: a [Google-hosted community answer](https://support.google.com/googleplay/android-developer/thread/474044993)
  surfaced in search says non-medical fitness may use personal accounts.
  This is community guidance, not an explicit exemption in the full policy;
  it does not settle this app's eligibility or authorize account conversion.

Conclusion: account-type applicability is an unresolved release decision,
not a confirmed order to convert every fitness developer. Before creating or
submitting this app, reconcile the actual business/operator setup with current
Google guidance or obtain an official support determination. Do not create a
new paid account, alter legal identity, or convert the existing multi-app
account without owner involvement. Continue independent source preparation.

## Other verified requirement

[Target API policy](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en)
currently requires API 36 or later for new phone apps. The published extension
date was November 1, 2026, already past on this check date. SDK 54 source and
JavaScript export are not proof of a signed AAB's final target, permissions,
16 KB native alignment or Android runtime behavior; inspect the real artifact.

## Immediate owner-dependent steps

1. Completed: owner signed in to existing Kakao app 1561523. Saved only the
   approved icon, then verified it after reload. Name, company, category,
   domain, grants and keys were not changed by the icon operation.
2. Completed by the owner: business setup. Verified the Biz App badge on the
   same app's consent page without reading or recording registration numbers.
   With explicit action-time approval, saved email as optional for member
   identification/login/account management and reopened the persisted value.
   Missing-email forced collection remains off. Actual production Kakao login
   and session restoration now work. No repeated owner Kakao setup is needed.
3. Sign in to the existing Expo/EAS CLI account when build preparation reaches
   the project-linking gate. No account identifier, project UUID or signing key
   is to be invented, replaced or created implicitly.
4. Review legal/operator/policy text and applicable Play declarations only after
   the product's real lifecycle and account-type gates are resolved. App creation
   is not a release, accepted upload, installed test or public listing.

The Play creation form is prepared with app/free/Korean/name/package fields and
the package-availability result read back. Policy and US export declarations
remain unchecked; Create was not clicked. This is not a reservation or app record.
