# Triage: why a `_ynh` repo lags upstream / is its auto-update bot dead?

Answer "why is <app>_ynh still on version X? are the bots broken?" from repo evidence, never recall. All steps are read-only `gh api` (PAT `$GH_TOKEN_FILE` via GH_TOKEN env).

## Recipe (each step settles one question)
```bash
export GH_TOKEN=$(cat "$GH_TOKEN_FILE")
R=YunoHost-Apps/<app>_ynh
gh api repos/$R/commits --jq '.[0:5][] | .sha[0:8]+" "+.commit.committer.date+" "+(.commit.message|split("\n")[0])'   # repo alive? when last touched?
gh api repos/$R/contents/manifest.toml --jq .content | base64 -d | grep -E '^version|\[resources.apt\]|packages'       # pinned version + apt deps
gh api repos/$R/contents/.github/workflows --jq '.[].name'                                                        # which bot infra exists
gh api repos/$R/contents/.github --jq '.[].name'                                                                  # autoupdate.toml? (new central bot)
gh api "repos/$R/actions/runs?per_page=10" --jq '.total_count'                                                    # 0 = bot never ran
gh api repos/$R/contents/scripts --jq '.[].name'                                                                  # sources.sh present?
gh api repos/<upstream>/releases/latest --jq .tag_name                                                             # what upstream actually is
```

## Decision table
- **No `scripts/sources.sh` + `[resources.apt] packages = "<pkg>"`** → the app installs the *Debian* package; there is nothing for any bot to update. The manifest version just mirrors what apt resolves to on the running Debian. The pin is Debian's, not the maintainer's. Upgrade path = OS migration (YunoHost major = Debian major), which bumps apt automatically with zero repo changes.
- **`updater.sh` is the only workflow file** → it's the stock template helper whose script body starts with `exit 1` ("Remove this exit command when you are ready"). If the stub is intact and `actions/runs` total_count = 0, the bot was never enabled. There is also no per-repo `auto_version.yml` and the modern mechanism is the central YunoHost/apps CI driven by `.github/autoupdate.*` — absent means no central bot either.
- **sources.sh present with pinned url+sha256** → a real autoupdatable app; no bot config or dead bot is then the actual cause of staleness.
- **Why Debian can't just ship the newer major**: check the new major's library requirement vs bookworm's lib version (e.g. qBittorrent 5.x needs libtorrent-rasterbar ≥ 2.1; bookworm ships 2.0.x → not rebuildable into old stable). State this as the mechanism, not a maintainer failing.

## Debian-version-per-suite lookup (verified)
- Local box: `apt-cache show <pkg> | grep ^Version` (what YOUR installs get).
- All suites: `curl -s https://sources.debian.org/api/src/<pkg>/` → JSON list of version→suites (bookworm/trixie/sid/backports). Use this to say exactly which YunoHost/Debian release unlocks the newer version.

## Framing for the user
Report the verified chain: manifest pin == apt version == Debian suite version; bot status separately (stub + 0 runs); repo maintenance status separately (recent merged PRs ≠ version control — the maintainer may be active yet version-locked). Check YunoHost release status (forum/roadmap) before promising the OS-migration path is production-safe.

## Fleet audit: every `$GH_ACCOUNT` _ynh repo at once

For "audit all my packages / does anything need updating". Read-only; PAT from `$GH_TOKEN_FILE`, never printed. Parallelize per-repo calls (8 workers) and dump the results JSON to the workspace so the report is re-derivable.

### Procedure
1. Enumerate: `api.github.com/users/$GH_ACCOUNT/repos?per_page=100` (token header), keep names ending in `_ynh`. Exclude unsuffixed repos — those are upstream apps the account owns (e.g. sveltia-cms-auth), not packages.
2. Per repo collect: default_branch; manifest.toml (default branch, fallback master/main) parsed for version, upstream.code, [resources.sources], [resources.apt]; root listing (conformance flags: tests.toml/LICENSE/README/logos/doc/conf); `.github/` listing + `actions/runs?per_page=1` total_count; upstream latest release else newest tag (from upstream.code or any source URL).
3. Classify the sourcing shape (table below), then compare pinned vs upstream and count the gap.
4. Catalog membership: fetch YunoHost/apps `apps.toml` once and grep `$GH_ACCOUNT` — expect NONE (submission-PR-only policy). Consequence: zero bot CI anywhere, actions/runs = 0 on every repo, and autoupdate strategies in manifests are inert metadata. Report staleness as fully manual, not as broken bots.
5. Cross-check the box: `unset PYTHONPATH; yunohost app list --output-as json` — report installed apps lagging their own repo HEAD (~ynhN behind) separately from upstream lag; both are actionable.
6. Report as one table grouped by verdict (behind / up-to-date / nothing-to-track) with gap counts, then housekeeping flags (docker-based package violating the native-only rule, conformance gaps). End with a bump-order proposal; pushes stay approval-gated.

### Manifest-parse gotchas
- Multi-arch sources live in `[resources.sources.main.amd64]`-style sub-tables — `sources.main.url` being empty does NOT mean "no sources"; descend into arch sub-tables before classifying, or pinned repos get misreported as sourceless.
- Normalize versions before comparing: strip `~ynh<N>`, leading `v`, prefixes like `i2p-`; compare numeric tuples, never raw strings.
- When counting release gaps from `/releases`, verify the pinned tag actually appears in the listed page. If it does not, the upstream mingles build artifacts/nightlies in releases — count via `/tags` filtered to a stable-tag regex instead (one router showed "100 newer releases" that was really one minor behind).
- Commit-pinned tarballs (`/archive/<sha>.tar.gz`): distance = index of the sha in `/commits?per_page=100`; sha absent from the page means >100 commits behind.
- Non-GitHub upstreams have metadata APIs — query them instead of reporting "unknown": maven `<release>` in the component's `maven-metadata.xml`, `meta.fabricmc.net/v2/versions/game|loader`, etc.

### Sourcing shapes (his repos — superset of the catalog decision table above)
- `[resources.sources]` + autoupdate strategy → bot-dependent in catalog repos; inert in personal repos (no CI).
- `[resources.sources]` pinned, no autoupdate → manual bump: new url + sha256 per arch, bump `~ynh<N>`.
- `[resources.apt] packages` → Debian pin; nothing repo-side to bump (see decision table above).
- deb URL + per-arch sha256 pinned as vars in `scripts/_common.sh` → manual bump in _common.sh.
- `ynh_apt_install_dependencies_from_extra_repository` in install → version comes from the upstream deb repo; bump the pin there.
- docker-compose + `:latest` image in conf/ → upgrades are image pulls, manifest version is self-assigned; flag against the native-only rule.
- No sources, no apt → config-only package; nothing upstream to track.
