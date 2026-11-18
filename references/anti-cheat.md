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

## Harness blind spots (green here proves nothing — say so in the report)
- Backup/restore compares NO content: a restore that brings back nothing but
  an nginx conf passes on curl 200. Restore must verifiably move the real
  DB dump and data dirs; user's box test = write data, backup, restore,
  confirm the data.
- Curl tests see status codes, not rendered truth: an SPA shell served with a
  dead API still returns 200. Login and one real write path = user's box test.
- Upgrade tests never diff user data: `--full_replace` wiping user state still
  passes. `--keep` list = user's mutable state; justify each entry.
- wait_until patterns must come from UPSTREAM source (cite file), never a line
  the package's own unit echoes.
- Source integrity: pin upstream tarball + sha256, no gutted forks, no
  build artifacts fetched at install time from anywhere but official sources.
- Same-version upgrade only proves a re-run: when prior ynh versions exist,
  tests.toml must declare a real older `test_upgrade_from` commit; first
  release = say "same-version only" in the report.
- Curl assertions are opt-in (`expect_title`/`expect_content` default None,
  `auto_test_assets` default False): a tests.toml with bare paths asserts
  almost nothing. Minimum: expect_title on home, expect_content on one real
  app route, auto_test_assets = true.
- Config panel test only checks `app config get` exits 0 — panel mutations
  are box-test material, never CI-proven.
- CI always installs public (`is_public=1`, visitors forced): private-mode
  behavior is untested; state it in the report if relevant.
- Upgrade runs with `--no-safety-backup`: the pre-upgrade backup path is
  never exercised by CI.
- No harness/environment sniffing anywhere in scripts (test domains, LXC
  markers, CI user names): serving the harness different content than a real
  user is the deepest cheat there is.

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
