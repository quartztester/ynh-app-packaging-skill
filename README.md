# ynh-app-packaging

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)

Rules for packaging a native [YunoHost](https://yunohost.org) 12 app, short
enough for a human to read and precise enough for an agent to follow.

Every rule comes from a live install, upgrade, backup, restore or CI run that
broke without it — not from reading the docs.

## The loop

The skill is five steps. Everything else is the reasoning behind one of them.

1. **Bootstrap** — clone [`YunoHost/example_ynh`](https://github.com/YunoHost/example_ynh)
   fresh, every time. No vendored template, so the skill cannot go stale.
2. **Package** — edit the clone in place; keep the template's files, names and
   v2.1 helper idioms.
3. **Verify locally** — [`package_check`](https://github.com/YunoHost/package_check), the same harness the official CI runs. Pull it to latest (or clone it) before every run: a stale clone silently tests an older scenario matrix.
4. **Run the official CI** — open the PR, comment `!testme`, read the per-test
   summary.
5. **Fix and repeat** — one failing test at a time, in the repo, until the
   whole matrix is green.

## Install

This is a plain [Agent Skills](https://agentskills.io) skill: one `SKILL.md`,
no runtime dependency. Clone it as `ynh-app-packaging` (the directory name must
match the `name` field) into your agent's skills directory:

```bash
git clone https://github.com/quartztester/ynh-app-packaging-skill \
  ~/.claude/skills/ynh-app-packaging
```

Claude Code, OpenCode, Codex CLI, Cursor and Goose discover it from the
frontmatter automatically; Hermes installs it under `devops/`.

You need a YunoHost 12.x box with helpers 2.1, git and network access. Apps are
packaged natively — never Docker, LXC or a VM as the app's runtime.

## What's in here

| path | what it is |
|---|---|
| `SKILL.md` | the workflow, the rules that break a package, and a symptom → file map |
| `references/` | 16 files loaded on demand: lifecycle and CI mechanics, trap catalogs, SSO/auth, UX doctrine, repo hygiene, official-docs index |
| `scripts/` | conformance audit, comment budget, comment-only-diff prover, PII sweep, skill self-check |
| `CONTRIBUTION.md` · [`_fr`](CONTRIBUTION_fr.md) | the human contributor guide, with the reviewer bar |
| `PHILOSOPHY.md` · `STRATEGY.md` | why this exists and where it is going |

## AI transparency

> If you still decide to use AI, we highly recommend you to be transparent and
> responsible about it, and "own" it: you must be able to understand and
> explain every piece of your code as if you wrote it yourself.
> — https://doc.yunohost.org/en/dev/packaging/

Nothing here is done until it survives real lifecycle cycles, and you are
expected to be able to defend every line it helped you produce.

## Contributing

Live-gate failures are the most valuable issue you can open: each one is a rule
the skill is missing. See `CONTRIBUTION.md`.

## License

GPLv3 — see [LICENSE](LICENSE).
