# doc/DESIGN.md template

Ship one per package at `doc/DESIGN.md` after package checks pass — the maintainer's map: what the lifecycle does, every non-obvious choice, what not to break. Fixed slot order across packages so two DESIGN.md files diff by eye; a skimmer reads only Lifecycle + Don't break.

## Skeleton

```markdown
# <app> — packaging design

<Upstream app in one sentence + the one property that shapes this package.>

Anything not mentioned below is standard YunoHost boilerplate identical in most packages.

## Lifecycle
- **Install:** 1–2 lines in execution order: questions → sources → runtime/deps →
  config render → start/health gate → web surface.
- **Upgrade:** 1–2 lines: what changes vs install, what survives untouched.
- **Backup/restore:** 1–2 lines: what's archived, what's regenerated on restore.

## Decisions
One bullet per slot. Keep every slot — write "standard" where the package does the
obvious thing; uniform slots are what makes two packages comparable.
- **Source:** release asset / binary / tarball; sha256 pins; per-arch; in_subdir handling.
- **Runtime:** interpreter or sidecar; how it's obtained; offline deps.
- **Storage:** DB/cache instance (private vs shared); where state lives.
- **Auth:** ldap/sso verdict; permission split; portal regex if any.
- **Path:** root-only or subdir; how it's enforced.
- **Sandboxing:** hardening level; named exceptions with the reason.
- **Backup:** what's in/out; regeneration step on restore.

## Don't break
Gotchas a future maintainer must not "fix" — sandbox relaxations, permission
fixups, CI test exclusions, intentional warnings. Each ≤2 lines with a file#Lx-Ly.
```

## Rules

- Facts + "what breaks otherwise". No glossing of terms, no narration: "we chose X" → state the choice.
- All citations inline `[file Lx-Ly](../path#Lx-Ly)` — relative links work on any branch; grep/sed-verify every range against the file immediately before pushing. Guessed ranges rot silently.
- A fact lives in exactly one section: lifecycle carries order, decisions carry reasons. Duplication between sections is the trim signal.
- Trivially boilerplate app: compress Lifecycle, but never drop Decisions slots — an all-"standard" column is still cross-comparison data.
- Target ~50 lines. Over ~70 means it's re-narrating the code; cite the code instead.
- Example of the finished shape: `quartztester/cap_ynh` and `quartztester/google-maps-scraper_ynh`, `doc/DESIGN.md`.
