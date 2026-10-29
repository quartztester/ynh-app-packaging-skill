# ynh-app-packaging

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lean, gate-enforced rule set that walks an AI agent — or a human — through packaging a native YunoHost 12 app, from `manifest.toml` to catalog submission, with every rule learned from live install/upgrade/backup/restore cycles rather than documentation alone.

## Why this exists

AI-generated YunoHost packages get rejected at catalog review for the same recurring defects: verbose speculative scripts, calls to helpers that don't exist, broken backup/restore, miswired SSO, install forms that ask for everything, tuning walls in config panels. This skill encodes the bar the catalog actually enforces, as machine-checkable rules an agent can follow.

It grew out of ~30 real packaging cycles (anubis, remark42, forgejo, gitea, umami, listmonk, and more), each one benchmarked with-skill vs without and each live-gate failure folded back in as a trap entry.

## What you get

- Golden rules and a Definition of done with hard gates: real install, browser functionality check, anonymous/protected endpoint matrix, config-panel round-trip, backup → remove → restore with a data canary, upgrade ×2, change_url move, package_linter clean
- A UX doctrine for install questions, config panels, and admin docs, calibrated against 99 catalog level-8 apps
- A trap catalog covering helpers v2.1 renames, env quoting, panel getter poisoning, ssowat regex anchoring, build-stack version pins, upgrade durability, Postfix mail wiring
- An SSO-first auth decision tree (LDAP / OIDC / SAML / trusted-header / local)
- Scripts: conformance audit (detects hallucinated helper calls), static grader, skill self-check
- A snapshot of `example_ynh` to bootstrap every package from the official template

## Using it

Copy this repo into your agent's skills directory (for example `~/.hermes/skills/devops/ynh-app-packaging`, or your agent's equivalent) and have the agent load `SKILL.md` before any packaging work. It pairs with two optional companion skills — caveman and ponytail — whose public URLs are in `SKILL.md`.

Requires a YunoHost 12.x box with helpers 2.1; the skill refuses to run against anything else (Golden rule 0), because every trap in it is validated against that core.

## AI transparency

The official YunoHost packaging docs say it best:

> If you still decide to use AI, we highly recommend you to be transparent and responsible about it, and "own" it: you must be able to understand and explain every piece of your code as if you wrote it yourself, you must be able to explain what it does and why you chose to implement it this way. You can't just throw something you don't even understand yourself at other people, and expect them to maintain it for you.
>
> — https://doc.yunohost.org/en/dev/packaging/

This skill's gates exist to make that bar reachable: nothing is called done until it survives real lifecycle cycles, and you are expected to be able to defend every line it helps you produce.

## Repository layout

- `SKILL.md` — the rule set; start here
- `references/` — 18 topical files: traps, gates, UX doctrine, per-app recipes, official-docs index
- `scripts/` — `verify_conformance.py`, `grade_static.py`, `verify_skill_integrity.py`
- `templates/` — `example_ynh-snapshot.tar.gz` bootstrap skeleton

## Contributing

Issues and corrections welcome — especially live-gate failures you hit that the trap catalog doesn't cover yet; each one is a missing rule.

## License

MIT — see [LICENSE](LICENSE).
