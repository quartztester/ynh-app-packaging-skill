# ynh-app-packaging

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)

A short, workflow-first rule set that walks an AI agent — or a human — through packaging a native YunoHost 12 app, from `manifest.toml` to catalog submission, with every rule learned from live install/upgrade/backup/restore cycles rather than documentation alone.

## Why this exists

AI-generated YunoHost packages get rejected at catalog review for the same recurring defects: verbose speculative scripts, calls to helpers that don't exist, broken backup/restore, miswired SSO, install forms that ask for everything, tuning walls in config panels. This skill encodes the bar the catalog actually enforces, as machine-checkable rules an agent can follow.

It grew out of ~30 real packaging cycles (anubis, remark42, forgejo, gitea, umami, listmonk, and more), each one benchmarked with-skill vs without and each live-gate failure folded back in as a trap entry.

## What you get

- A five-step workflow with the official CI as the feedback loop: bootstrap from a fresh `example_ynh` clone, package, verify locally with the same harness the CI runs (`package_check`), push and read the CI's per-test summary, fix what fails, repeat
- The rules that actually break a package (helpers 2.1 pin, native-only runtime, SSO wiring, upgrade durability, secrets, comments, PII, publishing)
- The checks CI cannot make: browser functionality, anonymous/protected endpoint matrix, config-panel round-trip, backup → remove → restore canary, change_url move, mail send
- A UX doctrine for install questions, config panels, admin docs and shipped admin GUIs, calibrated against 199 catalog level-8 apps
- A trap catalog covering helpers v2.1 renames, env quoting, panel getter poisoning, ssowat regex anchoring, build-stack version pins, upgrade durability, Postfix mail wiring
- A two-layer comment gate (blocking density budget + advisory semantic gauntlet, adapted from [this gist](https://gist.github.com/bavanws/123e0343f8a79cec825d9141124a0a83)) with syntax-aware scanning (`#`, `--`, `//`, `<!-- -->`) so lua/js/html files can't pass blind
- An SSO-first auth decision tree (LDAP / OIDC / SAML / trusted-header / local)
- Scripts: conformance audit (detects hallucinated helper calls), the comment gate, a comment-only-diff prover, the PII sweep, a static grader, skill self-check
- No vendored template: every package starts from a fresh `git clone` of [YunoHost/example_ynh](https://github.com/YunoHost/example_ynh), so the skill cannot go stale

## Using it

This skill follows the open [Agent Skills](https://agentskills.io) standard — one `SKILL.md` read by Claude Code, OpenCode, Codex CLI, Gemini CLI, Cursor, Goose, Hermes, and 20+ other agents. Clone the repo into your agent's skills directory; the folder name must be `ynh-app-packaging`, matching the skill's `name` field:

| Agent | Path |
|-------|------|
| Claude Code | `~/.claude/skills/ynh-app-packaging` (or `.claude/skills/` inside a project) |
| OpenCode | `~/.config/opencode/skills/ynh-app-packaging` or `.opencode/skills/` — or reuse the Claude path, OpenCode reads `.claude/skills/` too |
| Codex CLI | `~/.codex/skills/ynh-app-packaging`, or `$skill-installer` |
| Hermes | `~/.hermes/skills/devops/ynh-app-packaging` |

```bash
git clone https://github.com/quartztester/ynh-app-packaging-skill ~/.claude/skills/ynh-app-packaging
```

Agents discover it from `name` + `description` and load the full `SKILL.md` when a task matches (Codex: `/skills`; Claude Code / OpenCode: automatic). It pairs with two optional companion skills — caveman and ponytail — whose public URLs are in `SKILL.md`.

The skill body is agent-neutral by design: per-agent syntax appears only as parenthetical examples, never as the instruction itself, and every script runs on system `python3` with no agent runtime imported.

Requires a YunoHost 12.x box with helpers 2.1; the skill refuses to run against anything else (Golden rule 0), because every trap in it is validated against that core only. Personal environment defaults (GitHub account, PAT path, workspace root, commit identity) are defined as overridable conventions at the top of SKILL.md.

## AI transparency

The official YunoHost packaging docs say it best:

> If you still decide to use AI, we highly recommend you to be transparent and responsible about it, and "own" it: you must be able to understand and explain every piece of your code as if you wrote it yourself, you must be able to explain what it does and why you chose to implement it this way. You can't just throw something you don't even understand yourself at other people, and expect them to maintain it for you.
>
> — https://doc.yunohost.org/en/dev/packaging/

This skill's gates exist to make that bar reachable: nothing is called done until it survives real lifecycle cycles, and you are expected to be able to defend every line it helps you produce.

## Repository layout

- `SKILL.md` — the workflow and the rules; start here
- `references/` — 16 topical files, loaded on demand: `workflow.md` (lifecycle + CI mechanics), trap catalogs by symptom, UX doctrine, repo hygiene, official-docs index, per-app recipes
- `scripts/` — `verify_conformance.py`, `comment_cleanup.py`, `comment_gate.py`, `pii_gate.sh`, `grade_static.py`, `verify_skill_integrity.py`
- `docs/research/` — provenance for the UX doctrine (level-8 calibration corpus, reusable scripts): human reference, not part of the agent's load path
- `CONTRIBUTION.md` / `CONTRIBUTION_fr.md` — the human contributor guide

## Contributing

Issues and corrections welcome — especially live-gate failures you hit that the trap catalog doesn't cover yet; each one is a missing rule.

## License

GPLv3 — see [LICENSE](LICENSE).
