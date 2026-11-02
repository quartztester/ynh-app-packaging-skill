# Contributing to YunoHost app packaging

A human-facing guide for contributing `_ynh` packages — to the
[YunoHost-Apps](https://github.com/YunoHost-Apps) organization, to a personal
package, or to an existing one. It restates in plain prose what the
machine-readable packaging doctrine enforces, and adds best practices mined
from a full re-audit (November 2026) of the **712 `_ynh` repos listed in the
[YunoHost/apps catalog](https://github.com/YunoHost/apps)** (`apps.toml`,
727 entries). Percentages below are measured on that corpus.

## 1. You are the contributor of record

An AI assistant can write, review and refactor packaging code, but it does not
change the process: the human who opens the commit or pull request owns
everything in it — correctness, security, licensing, tests, docs, and every
follow-up review comment. The official packaging docs put it plainly:

> If you still decide to use AI, we highly recommend you to be transparent and
> responsible about it, and "own" it: you must be able to understand and
> explain every piece of your code as if you wrote it yourself.
> — https://doc.yunohost.org/en/dev/packaging/

Reviewers reject "generated" packages on sight when they deviate from the
template: verbose scripts, hallucinated helpers, off-standard layouts. Do not
submit code you have not personally read.

**Disclosure rule for this fleet of packages (mandatory):** every commit whose
content an AI tool generated or substantially transformed must carry a trailer:

```
Assisted-by: <agent-name>:<model-version>
```

Example: `Assisted-by: Hermes Agent:qwen-next`. List only AI tools and
specialized analyzers that materially contributed — not git, editors, or
compilers. Omitting the trailer on AI-assisted work blocks acceptance here.

## 2. The normal process comes first

1. Non-trivial change? Open (or comment on) a GitHub issue with your plan and
   wait for feedback before writing significant code.
2. Start from [`example_ynh`](https://github.com/YunoHost/example_ynh) — clone,
   copy the files, edit in place. Never hand-write a manifest or copy the
   layout of an old package: the template and helper conventions evolve.
3. Work in a branch. A catalog-listed repo's `main` is auto-published to the
   store within hours; merge only what passed the gates.
4. Test the real lifecycle on a real box (or the docs' sanctioned disposable
   LXC/Incus VM): install → **config panel round-trip** → backup → remove →
   restore → upgrade → the **same upgrade again** → **change_url move** →
   reinstall. A script that was never executed is an untested script.
5. Run the linter and CI: `package_linter` locally; for catalog repos, a PR
   comment `!testme` triggers the dev CI. Read the output, don't assume green.
6. Open a PR, expect to revise during review.

## 3. Anatomy of a package (what the corpus actually ships)

Every package: `manifest.toml` (100%), `LICENSE` (100%), `README.md` (100%),
`scripts/` (flat v2.1 layout: `install remove upgrade backup restore
change_url config _common.sh`), `conf/` (100%), `tests.toml` (100%),
`doc/` (100%). Script file modes: 755 for lifecycle scripts, 644 for
`_common.sh`/`change_url`/`config`.

Docs quality is what separates a reviewable package from a rejected one:

- `doc/DESCRIPTION.md` (100%) + `DESCRIPTION_fr.md` (81%) — the catalog
  renders these, not your README. 96% of manifests pair the English
  description with a French one; match that (multi-line feature list, no
  "self-hosted web app" filler).
- `doc/screenshots/*.png` (92%) and embedded in the README (82% of READMEs
  embed them) — official upstream assets first, live captures second.
- `doc/ADMIN.md` (44%, median **9 lines**) — only what an admin can trip on:
  first-login steps, risky options, what doesn't survive reinstall. Short and
  real beats long and generic.
- Version-gated migration notes go in `doc/PRE_UPGRADE.d/<version>.md` (16%)
  — run by the upgrade only when crossing that version; the right home for
  breaking-upstream-changes warnings.

## 4. Manifest best practices

- `[upstream]` block: 100% ship it — `license` (100%), `code` (98%),
  `website` (77%), `admindoc` (65%), `demo` (49%), `fund` (18%) if you care
  about donations.
- `version = "1.2.3~ynh1"` (100%): the `~ynh` suffix is yours — bump it on every
  package-side change, even with no upstream bump.
- `helpers_version = "2.1"` in `[integration]` (95% do; the rest silently
  load the dead 2.0 helpers). Always set it. Helpers 2.1 is current on both
  YunoHost 12 and 13 (the 13 core still ships `helpers.v2.1.d`).
- Install questions stay lean (median 3): `domain`, `path` when subpath
  works, `init_main_permission` (88% ship it) — and think about the default:
  "visitors" for public-facing apps, admins for private tools. Ask only what
  the install cannot decide; 53% of questions carry a default.
- `[resources.sources]`: pin `url` + `sha256` (per-arch `amd64.url`/
  `amd64.sha256` sub-tables), and add `autoupdate` — **87% of repos with
  pinned sources declare an update strategy** (`latest_github_release`/
  `latest_github_tag`, per-arch `asset` regex). It keeps the catalog bot
  opening version-bump PRs. Constrain it to stable tags (`version_regex`) so
  a beta is never auto-shipped.
- `integration.multi_instance`: true by default (72% of the catalog). False is
  legitimate only for machine-global state (fixed protocol ports, system
  hooks) — say why in a comment, and self-guard the install against a second
  copy (the platform does not enforce the flag).

## 5. Script best practices (v2.1 idioms, corpus frequency)

- Render config with `ynh_config_add` (+`_fail2ban`, `_logrotate`, `_systemd`)
  from templates in `conf/` — 95% use it; config files in `conf/`, not
  heredocs in scripts (only 4% have any heredoc left).
- `ynh_systemctl` to manage services (94%) — no raw `systemctl` in scripts.
- Secrets: create once with `ynh_app_setting_set_default --key=x
  --value=$(ynh_string_random)` (27%) and re-render config from settings;
  never regenerate a secret on upgrade/restore.
- Run as the app user with `ynh_exec_as_app` (39%).
- Clean up with `ynh_safe_rm` (45%).
- Databases: dump in `backup` with `ynh_mysql_dump_db` / `ynh_psql_dump_db`,
  restore with the matching helper; also archive the settings/scripts dir
  (backup copies `scripts/` via the `../settings/scripts/_common.sh`
  Keep-comment pattern).
- **Do not copy these from older repos** — dead v2.0 helpers still present in
  the corpus: `ynh_add_config` (35 repos), `ynh_secure_remove` (30),
  `ynh_use_logrotate` (14), `ynh_permission_update` (4). Verify every `ynh_*`
  call against `/usr/share/yunohost/helpers.v2.1.d/` on a real box.
- Comments: lean. One-line capability labels and why-traps with a link; no
  tutorial prose. A reviewer must follow each script top-to-bottom in one read.
- Nothing personal ever: no names, private domains, or usernames in any file,
  example, or screenshot — including git history.

## 6. tests.toml

100% ship it. Good practice from the corpus: keep the `#:schema` line (73%);
add `test_upgrade_from.<commit>` entries from your own repo's history at every
release (61% have them, and they are what proves upgrades for the store);
set `[default.args]` for required questions with no default (63%) so CI can
install headless; `exclude` scenarios your app legitimately can't serve (19%);
`curl_tests` (36 repos, growing) let CI assert pages and login behavior.

## 7. Submitting to the catalog

A PR to [YunoHost/apps](https://github.com/YunoHost/apps) adds your app to
`apps.toml` (+ the logo under `logos/`): state `working`, a category from
`categories.toml`. Quality levels 0–8 are bot-assigned from CI each Friday;
level ≤4 hides the app and freezes upgrades for every user, so the test
scenarios in `tests.toml` are not optional. Read the submission thread
thoroughly — reviewers care most about §3–§5 of this document.

## 8. Pre-PR checklist

- [ ] I read every line of the diff and can explain it as my own.
- [ ] `bash -n` clean; every `ynh_*` helper exists in helpers 2.1.
- [ ] Installed, backed up, removed, restored, upgraded twice, change_url moved,
      reinstalled — on a real box, not just CI.
- [ ] Config panel get → set → get round-trip verified on the rendered file.
- [ ] Real login test in a real browser for the primary user path.
- [ ] `README_fr.md`/`DESCRIPTION_fr.md` and the real upstream `LICENSE` text shipped.
- [ ] `helpers_version = "2.1"`, `[upstream]` block, `autoupdate` strategy present.
- [ ] `~ynh` suffix bumped; release tag `v<version>-ynh<N>` exists on the remote.
- [ ] No PII anywhere, including history and screenshots.
- [ ] `Assisted-by:` trailer on every AI-assisted commit.

*The machine-readable version of these rules, with trap catalogs and gate
mechanics, lives in the `ynh-app-packaging` skill.*
