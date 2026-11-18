# No test-passing theater — fix behavior, not measurement

Green CI must mean the app works, not that the harness was dodged. The harness
measures proxies (stderr line counts, curl returns, log patterns); proxies can
be satisfied without the app working. Rules that keep the two coupled:

## The box test
Before calling any fix legitimate, answer: *would this still break on a real
box, out of CI, in the user's browser?* A fix that only changes what the
harness observes (redirecting a log channel, tweaking a curl expectation,
excluding a test) is only legitimate when the underlying behavior is proven
correct by other means and the proof is written down.

## Allowed (root-cause class)
- Fixing config/scripts so the service actually starts, binds, serves, reloads.
- Excluding a generated test only when the scenario is physically impossible
  for the app, grounded in upstream SOURCE (cite file), not because the test
  was red. State it in doc/DESIGN.md "Don't break" and in the user report.
- Silencing a noisy build/log channel only when the noise provably comes from
  upstream code, output goes to stdout (kept, not dropped), and DESIGN.md
  names the flood and its origin.

## Forbidden
- `|| true`, `set +e`, or exit-code masking around install/upgrade steps.
- `expect_return_code`, `redirect`, or hand-written curl_tests invented to
  accept a response the app gives "because it's fine" — first prove the
  response is correct behavior, then declare it in the report.
- Deleting/narrowing tests.toml suites, preinstall tricks that fake state the
  app should have built itself.
- Reporting a matrix green when any variant was excluded — enumerate included,
  excluded, and why.

## Audit trail (what the user can check without trusting the agent)
- One commit per failure fix, message quoting the exact error line it answers.
- Keep every package_check log; per-test verdict from results_N.json, never
  from the launcher exit code or the global level line.
- Verdict applies only to the tree at launch; any scripts/manifest/conf edit
  after the last green run means rerun before claiming green.

## Day-one green is not the ceiling
CI covers URL-alive + lifecycle. Portal login, a real write path, and the
feature working end-to-end are the user's box test; never mark packaging
"done" or offer catalog transfer before it.
