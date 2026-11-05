# Contributing a YunoHost app package

The human guide. The agent-facing version — gates, trap catalogs, CI mechanics —
is [`SKILL.md`](SKILL.md) and `references/`. Numbers below come from an audit of
the 712 `_ynh` repos listed in the [YunoHost/apps](https://github.com/YunoHost/apps)
catalog (November 2026).

## 1. You are the contributor of record

An assistant can write and review packaging code; it does not change who owns
it. Whoever opens the commit or the pull request owns correctness, security,
licensing, tests, docs and every review comment that follows. The official docs:

> If you still decide to use AI, we highly recommend you to be transparent and
> responsible about it, and "own" it: you must be able to understand and
> explain every piece of your code as if you wrote it yourself.
> — https://doc.yunohost.org/en/dev/packaging/

Reviewers reject generated packages that deviate from the template: verbose
scripts, helpers that do not exist, non-standard layouts. Do not submit code you
have not read.

**Disclosure trailer (mandatory):** every commit whose content an AI tool
generated or substantially transformed ends with

```
Assisted-by: <agent-name>:<model-version>
```

Name only AI tools and analyzers that materially contributed — not git, editors
or compilers. Missing trailers block acceptance.

## 2. The process

1. Non-trivial change? Open an issue with the plan first.
2. Start from [`example_ynh`](https://github.com/YunoHost/example_ynh): clone,
   copy, edit in place. Never hand-write a manifest or copy an old layout — the
   template and helper conventions move.
3. Work in a branch. A catalog-listed repo's `main` is auto-published within
   hours; merge only what passed the gates.
4. Exercise the real lifecycle on a box or a disposable VM: install → config
   panel round-trip → backup → remove → restore → upgrade → the same upgrade
   again → change_url move → reinstall. A script nobody executed is untested.
5. Run `package_linter` and the CI (`!testme` on the PR). Read the output; never
   assume green.
6. Open the PR and expect revisions.

## 3. What a package ships

`manifest.toml`, `LICENSE`, `README.md`, flat v2.1 `scripts/` (`install remove
upgrade backup restore change_url config _common.sh`), `conf/`, `tests.toml`,
`doc/`. Modes: 755 lifecycle, 644 `_common.sh`/`change_url`/`config`.

Documentation is what separates a reviewable package from a rejected one:

- `doc/DESCRIPTION.md` + `DESCRIPTION_fr.md` — the catalog renders these, not
  your README. A multi-line feature list, no "self-hosted web app" filler, and
  a French pairing (96% of manifests pair them).
- `doc/screenshots/*.png`, embedded in the README — official upstream assets
  first, clean captures second.
- `doc/ADMIN.md` — median 9 lines. Only what an admin can trip on: first login,
  risky options, what does not survive reinstall.
- `doc/PRE_UPGRADE.d/<version>.md` for version-gated migration notes.

## 4. Manifest

- `[upstream]`: `license`, `code`, plus `website`/`admindoc`/`demo` when real.
  `website` must be the project site, never the code repo.
- `version = "1.2.3~ynh1"`: the `~ynh` suffix is yours — bump it for every
  package-side change.
- `helpers_version = "2.1"` in `[integration]`, always. Without it a
  packaging_format 2 app silently loads the dead 2.0 helpers.
- Install questions stay lean — corpus median 3: `domain`, `path` only when a
  subpath really works, `init_main_permission` (default `visitors` for anything
  public-facing). Ask only what the install cannot decide.
- `[resources.sources]`: pin `url` + `sha256` (per-arch sub-tables when the
  release differs by architecture) and declare `autoupdate` on stable tags —
  87% of pinned sources do, and it is what keeps the catalog bot opening bumps.
- `integration.multi_instance`: true unless the app holds machine-global state
  (fixed protocol ports, system hooks). Say why in a comment, and self-guard the
  install — the platform does not enforce the flag.

## 5. Scripts

- Render config with `ynh_config_add` (+`_fail2ban`, `_logrotate`, `_systemd`)
  from `conf/` templates, never heredocs in scripts.
- `ynh_systemctl` for services; `ynh_exec_as_app` for app-user commands;
  `ynh_safe_rm` for removals.
- Secrets: `ynh_app_setting_set_default --key=x --value=$(ynh_string_random)`,
  then re-render config from settings on every pass. Never regenerate on
  upgrade or restore.
- Databases: dump in `backup` with `ynh_mysql_dump_db`/`ynh_psql_dump_db`,
  restore with the matching helper. A PostgreSQL app must also include
  `postgresql` in `[resources.apt]` — the database resource provisions the db
  and user but never installs the server.
- Check every `ynh_*` call against `/usr/share/yunohost/helpers.v2.1.d/`. Dead
  v2.0 helpers still circulate in older repos: `ynh_add_config`,
  `ynh_secure_remove`, `ynh_use_logrotate`, `ynh_permission_update`.
- Comments: one line of why, or none. A reviewer must be able to follow each
  script top to bottom in one read.
- Nothing personal anywhere — no names, private domains, IPs or usernames in
  files, examples, screenshots or history.

## 6. tests.toml

Keep the `#:schema` line. Add `test_upgrade_from.<commit>` entries from your own
history at every release — they are what proves upgrades for the store. Set
`[default.args]` for required questions with no default so CI can install
headless, `exclude` only scenarios the app genuinely cannot serve (and say why
in the docs), and use `curl_tests` to assert pages and login behavior.

## 7. Submitting

A PR to [YunoHost/apps](https://github.com/YunoHost/apps) adds the entry to
`apps.toml` (state `working`, category from `categories.toml`) and the logo
under `logos/`. Quality levels 0–8 are assigned by the CI bot every Friday;
level ≤4 hides the app and freezes upgrades for everyone who installed it, so
the scenarios in `tests.toml` are not optional.

## 8. Pre-PR checklist

- [ ] I read every line of the diff and can defend it as my own.
- [ ] `bash -n` clean; every `ynh_*` helper exists in helpers 2.1.
- [ ] Installed, backed up, removed, restored, upgraded twice, moved and
      reinstalled on a real box — not just in CI.
- [ ] Config panel get → set → get verified on the rendered file.
- [ ] Real browser login and primary write path works.
- [ ] `README_fr.md`, `DESCRIPTION_fr.md` and the real upstream `LICENSE` shipped.
- [ ] `helpers_version = "2.1"`, `[upstream]` block, `autoupdate` strategy present.
- [ ] `~ynh` suffix bumped; tag `v<version>-ynh<N>` exists on the remote.
- [ ] No PII anywhere, history and screenshots included.
- [ ] `Assisted-by:` trailer on every AI-assisted commit.
