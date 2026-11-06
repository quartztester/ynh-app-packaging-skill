---
name: ynh-app-packaging
description: "Package, repair or audit a YunoHost 12 app package (_ynh): manifest, install/upgrade/backup/restore/change_url scripts, SSO, mail, config panels, catalog submission. Bootstrap every package from a FRESH clone of YunoHost/example_ynh, verify with the official CI, fix whatever fails. Use for any task touching a YunoHost app package. Native packaging only — no Docker/Kubernetes/LXC/VM as the app's runtime mechanism; helpers 2.1."
license: AGPL-3.0
compatibility: "Any agentskills.io-compatible agent. Needs a reachable YunoHost 12.x box (local or ssh), git, python3, and network access to github.com."
metadata:
  version: "3.3.1"
  author: Hermes Agent
  tags: yunohost, packaging, debian, sysadmin
---

# YunoHost app packaging (YNH 12, helpers 2.1)

The workflow below is the skill. Everything else is lookup: open a reference only when the task reaches it. Write terse, lean packages — verbosity is the first thing reviewers reject.

## Environment conventions (defaults are this repo's maintainer; override yours)
| var | meaning | default |
|---|---|---|
| `GH_ACCOUNT` | GitHub account owning `<app>_ynh` repos | `quartztester` |
| `GH_TOKEN_FILE` | classic PAT file, mode 600, wired into git credential.helper and exported as `GH_TOKEN` for `gh` | `/root/.gh_token` |
| `WORKSPACE` | where packages are bootstrapped | `/root/workspace` |
| `COMMIT_AUTHOR` | noreply commit identity | `91350035+quartztester@users.noreply.github.com` |

## Workflow — in order
### 0. Environment guard, before anything
`yunohost --version` major 12 **and** `/usr/share/yunohost/helpers.v2.1.d/` exists. On mismatch stop: every trap in this skill is validated against that core only.

### 1. Bootstrap from a FRESH example_ynh — every time, no exceptions
example_ynh is live upstream, not a snapshot to hoard. Clone it at the start of every packaging task:

```bash
git clone --depth 1 https://github.com/YunoHost/example_ynh "$WORKSPACE/.example_ynh"
mkdir -p "$WORKSPACE/<app>_ynh"
rsync -a --exclude .git "$WORKSPACE/.example_ynh/" "$WORKSPACE/<app>_ynh/"
git -C "$WORKSPACE/<app>_ynh" init -q    # the package gets its own history
```

Never hand-write `manifest.toml` or `scripts/` from memory, never copy an older package's layout. Joining an existing half-done package? Clone the same way and diff: adopt every template file it lacks (`README_fr.md`, `doc/`, `.github/`, `tests.toml`, dotfiles).

### 2. Package
Edit the clone in place. Keep example_ynh's file set, names and v2 idioms (`ynh_config_add*`, `ynh_app_config_apply`, `ynh_systemctl`, `ynh_setup_source`). Every `ynh_*` call must exist in the local `helpers.v2.1.d` — hallucinated helpers are a hard linter failure. `scripts/verify_conformance.py` checks this plus the file set.

### 3. Verify locally
Run [package_check](https://github.com/YunoHost/package_check), the same harness the official CI uses, before spending CI cycles. Keep that clone current — `git -C package_check pull --ff-only`, or clone it if absent, immediately before every run:
`YNHDEV_BACKEND=incus ./package_check.sh <repo-dir>` (in that clone; `-D` dry-run first to compare the matrix with `tests.toml`). Green means the completed run's per-test summary. Full setup and traps: references/workflow.md §Local package_check.

### 4. Run the official CI
Push a branch, open the PR, comment `!testme` as its own comment, then read the bot's per-test summary once the badges settle. Dev CI only fires on YunoHost-Apps org repos; pre-transfer, local package_check is the same matrix. Mechanics: references/workflow.md §Official CI.

### 5. Fix, repeat, then report
One failing test at a time: read the per-test log, fix the cause in the repo (never on the box), re-run step 3, re-push the branch, re-trigger `!testme`. Stop when the whole matrix is green. A run killed by timeout or still in progress has no verdict — never call it green. Report: what passed, what CI could not cover, what is gated on user approval.

### 6. Ship it to the catalog
Green CI is the halfway point. Public repo → human verify → transfer to `YunoHost-Apps` →
`!testme` in the org repo → catalog PR to `YunoHost/apps` → forum + fediverse announcement.
Org CI passes as two green jobs (bookworm, trixie) with exactly one linter warning each, the
pre-catalog `not in YunoHost's application catalog`. PR template, transfer gate, credential
prompts: references/publish-and-catalog.md.

## Rules that break a package if ignored
1. **Native only.** No Docker, Kubernetes, Podman, LXC/Incus or VM as the app's install/runtime mechanism — systemd unit, dedicated user, `ynh_setup_source`, native deps. Container-only upstreams are a packaging constraint, not an exemption: references/native-runtime-and-sidecars.md. (The CI harness itself may use containers.) Deviate only if the user acknowledges it in the current task.
2. **`helpers_version = "2.1"`** in `[integration]`. Without it a packaging_format=2 app silently loads the dead 2.0 helpers.
3. **example_ynh is the architecture.** Same file set, same idioms, no speculative settings, shared logic in `_common.sh`, no comment walls. Catalog level ≤4 hides the app and freezes upgrades for every installed instance; reviews reject deviating AI-generated packages.
4. **SSO by default** for any app with its own login — research its auth backends first (LDAP/OIDC/SAML/trusted-header/local): references/auth-backend-integration.md, wiring in references/ssowat-integration.md. `auth_header` DEFAULTS to true per permission: set it explicitly false on permissions covering Bearer-token API routes, or you ship an infinite login loop.
5. **No live-only fixes.** `ynh_setup_source` re-extracts on every pass and managed config is overwritten every time, so a box-side edit is unprovisioned until it is in the repo AND landed with `yunohost app upgrade <app> -u <clone>`. Durability doctrine: references/traps-lifecycle.md.
6. **Secrets live in app settings**, scripts re-render config from settings. Never regenerate on upgrade/restore: `ynh_app_setting_set_default --key=k --value=$(ynh_string_random)`.
7. **Comments: one line of WHY, or none.** Density under ~15% with no run of 6+ lines; `scripts/comment_cleanup.py <repo>` exits 1 above that. A why that needs a paragraph belongs in `doc/`, not in the script.
8. **Nothing leaks.** No names, emails, domains, usernames, IPs or box inventories in files, images or history — 3-layer audit before every push: references/repo-hygiene.md.
9. **Publish as `$GH_ACCOUNT`:** PAT from `$GH_TOKEN_FILE` (never in a remote URL), author `$COMMIT_AUTHOR`, repo `<upstream-name>_ynh`, tag `v<version>-ynh<N>` verified on the remote, sources as release assets. Stage **explicit paths** — a blanket `git add -A` in a package dir commits package_linter's `.manifest.v2.schema.json`, `.tests.v1.schema.json`, `.config_panel.v1.schema.json` and `.spdx_licenses`, which is why all four are gitignored (references/repo-hygiene.md). Changes to an already published repo: verify on the box, commit, then wait for explicit user approval before pushing.
10. **Ship the catalog set:** real `doc/screenshots/*.png` embedded in README+README_fr, square RGBA logo ≥180px with transparent corners, DESCRIPTION/ADMIN (+fr), canonical AGPL-3.0 LICENSE text, modes 755 for lifecycle scripts and 644 for `_common.sh`/`change_url`/`config`. Sourcing ladder and presentation rules: references/repo-hygiene.md.
11. **Mail goes through the box's Postfix** when the app sends email: `127.0.0.1:25`, plaintext, no auth, never an external provider; From must be a domain the relay accepts (`app@<install-domain>` by default). Prove it with a real send and a `status=sent` in mail.log: references/postfix-integration.md §Outbound.

## Checks CI cannot make (do these on a live box)
| check | pass condition |
|---|---|
| browser functionality | real portal login, primary write path exercised, result survives reload, no login bounce over ~15 s, nginx really serves the built output |
| endpoint matrix | from `/etc/ssowat/conf.json`: every `visitors` URI answers anonymously without a 302, every protected URI does 302/401 |
| config panel round-trip | get → set → get, asserted on the rendered file, not on the CLI exit code |
| backup → remove → restore | canary row + panel change created right before the backup is still there after restore, then the functionality gate again |
| change_url move | relocate once, re-run endpoint matrix + functionality gate, read a pre-move canary |
| mail send | app-level send returns 2xx and mail.log shows relay handoff |

Mechanics for each: references/workflow.md §Manual checks. CI already covers install variants, backup/restore, upgrade, change_url and the linter — don't re-run those by hand unless you are diagnosing a red scenario.

## What survives what
`ynh_setup_source` re-extracts every pass; managed config is rewritten every pass; panel applies re-render from the archived tree; `settings.yml` survives upgrades and is wiped on remove; app data belongs in `$data_dir`, `--keep` is the only sanctioned mutable set inside `$install_dir`. Fix routing: app-code fix → `patches/<source_id>/`, real divergence → fork and pin in `[resources.sources]`, config → `conf/` template. Full doctrine: references/traps-lifecycle.md.

## Repair map — load the file matching the symptom
| symptom | reference |
|---|---|
| helper name unknown, `__FOO__` templating, env quoting, config_panel.toml, systemd helper signatures, restore permissions | references/traps-helpers-and-panels.md |
| what survives upgrade, backup/restore mechanics, canary, half-registered apps, remove cleanliness | references/traps-lifecycle.md |
| npm/bundler/python build failures, engine pins, SPA auth, demo modes, throttles, Laravel, root helpers, deb wrapping | references/traps-build-and-appcode.md |
| driving yunohost ops (locks, PTY prompts, background jobs, op-log forensics), portal test hygiene | references/traps-box-and-ops.md |
| 401s despite valid creds, injected/rewritten Authorization headers, permissions that don't gate, public URIs 302ing, regex URIs | references/ssowat-integration.md |
| how should this app authenticate at all | references/auth-backend-integration.md |
| mail hooks, outbound SMTP, pipe/VERP | references/postfix-integration.md |
| container-only upstream, private sidecars, pinned runtimes | references/native-runtime-and-sidecars.md |
| what admins do to installed apps (backups, moves, SFTP, relays, certs, migrations) | references/admin-ops-interface.md |
| where implementation truth lives (core code, org repos, helpers) | references/core-internals-map.md |

## References — read on demand, not up front
- references/workflow.md — the lifecycle mechanics behind steps 1–5: bootstrap, every local check, package_check setup, official CI, verdict rules, multi-instance decision, reviewer/comment bar, feasibility probe, repo audit.
- references/official-docs.md — index of every official dev-doc page plus documented-but-easily-missed facts (manifest keys, resources, helpers surface, hooks, dev environments, quality levels, doc-vs-box contradictions).
- references/repo-hygiene.md — PII audit, logo/screenshot sourcing, portal tile, conformance sweeps, `tests.toml`, branch discipline, catalog submission and its PR.
- references/ui-questions-panels-docs.md — install questions, config panels, ADMIN.md wording, and the standard for an admin GUI the package ships itself.
- references/upstream-repo-staleness-triage.md — one lagging `_ynh` repo or the whole fleet: why it lags, is the update bot dead.
- references/publish-and-catalog.md — the production path after green CI: public repo, human verification, org transfer (and what to do without membership), the two-job org-CI acceptance rule, the catalog PR template, forum + fediverse announcement, credential prompts.
- references/app-recipes.md — verified builds and their quirks, one block per app class.
- `scripts/` — `verify_conformance.py` (file set + hallucinated helpers), `comment_cleanup.py` (comment budget), `comment_gate.py` (proves a cleanup touched only comments), `pii_gate.sh` (pre-push PII sweep), `verify_skill_integrity.py` (this skill's own reference/link check).

## Maintaining this skill
- Commit every edit: `scripts/verify_skill_integrity.py .` must pass (references resolve both ways, per-file line budget), `scripts/pii_gate.sh` before pushing, then bump `metadata.version`, tag `v<x.y.z>`, `gh release create <tag>`.
- One canonical home per trap: fold a lesson into the existing file and delete the duplicate instead of adding a parallel section. A rule earns a place only if a real live failure proved it or it covers a script every package ships.
- Human docs live in `CONTRIBUTION.md` / `CONTRIBUTION_fr.md`. They are not part of the agent's load path — don't read them to package an app.

## AI-use policy — verbatim from the official packaging docs
> If you still decide to use AI, we highly recommend you to be transparent and responsible about it, and "own" it: you must be able to understand and explain every piece of your code as if you wrote it yourself, you must be able to explain what it does and why you chose to implement it this way. You can't just throw something you don't even understand yourself at other people, and expect them to maintain it for you.
>
> — https://doc.yunohost.org/en/dev/packaging/

In practice: you own every line this skill helps you produce, including the ones you wrote. Nothing is done until it survives real install / upgrade / backup / restore / CI cycles.
