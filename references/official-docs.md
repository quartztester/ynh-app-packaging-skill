# Official-docs coverage — dev/packaging tree (ynh-app-packaging)

Canonical: https://doc.yunohost.org/en/dev/packaging (LIVE tree; helpers/resources pages auto-generated 2026-09-03 from YunoHost 12.1.41.1 — current). Audited against live page text 2026-10-26 (preview tree) and re-audited 2026-10-27 against the live tree: every fact below quote-verified in the fetched pages. RE-FETCH instead of recalling; standards evolve. TRAP: the scripts/ page's examples still use v2.0/v1 helper names (`ynh_add_nginx_config`, `ynh_install_nodejs`); under a `helpers_version = "2.1"` pin those are DEAD — the helpers_v2.1 page + the installed helpers are ground truth.
Nav notes (live tree): resources is a STANDALONE page (not manifest/resources); git/virtualbox/shell-scope live under misc/; core/forms + core/devenv + translation sit OUTSIDE the packaging subtree but matter (§16–18). Live-doc internal errors — do NOT propagate: hooks page writes 'post_create_user' where its own reference section says post_user_create; config_panels writes the settings path as /etc/yunohost/$app/settings.yml (correct: /etc/yunohost/apps/$app/); forms example uses type="display_text"; ynh_systemctl usage line says --timeout=300 while its arg docs say default 60s.

## Re-audit procedure (how this file stays true)
Run whenever the live docs move (new helpers version, format v3, nav reorg) or before trusting a fact here for a critical decision:
1. FETCH the tree: pull `https://doc.yunohost.org/sitemap.xml`, extract page URLs, save each page's extracted text to scratch as `<area>_<slug>.txt` with a `SOURCE: <url>` first line, one file per page.
2. READ via parallel subagents, one per doc area (dev vs admin), with a fixed extraction contract: facts grouped by TOPIC not by page, every bullet prefixed with the page slug, and a short verbatim quote (≤15 words) for every load-bearing fact.
3. VERIFY BEFORE MERGING — the gate: programmatically grep every cited quote against the fetched text. Expect attribution drift, not fabrication: when a quote misses its cited page, grep the WHOLE tree for the phrase before discarding the fact. Merge only verified facts; re-attribute or drop the rest.
4. Fix contradictions IN PLACE (edit the wrong sentence) and log them in the §15 register — including this file's own prior errors. Never append "UPDATE: actually" prose under a stale claim.
5. Sweep with `scripts/verify_skill_integrity.py` — every mentioned reference resolves both directions, PII patterns supplied as CLI args (never hardcoded: the skill itself must stay clean of what it guards against).

## Page index — where each lands in this skill
| Page (under /en/dev/) | Topic | Carried by |
|---|---|---|
| packaging/ (root) | philosophy, prerequisites, format history | quality-gates.md reviewer bar; history/v3 → §9 |
| packaging/manifest | manifest.toml schema, antifeatures, questions | SKILL.md rules 3/8; app-recipes.md; §1 below |
| packaging/resources | full resource reference | traps-helpers-and-panels.md, native-runtime-and-sidecars.md; §2 below |
| packaging/scripts | lifecycle scripts, variables, templating | SKILL.md, traps-helpers-and-panels.md; §4 below |
| packaging/scripts/helpers_v2.0 | legacy helper names | traps-helpers-and-panels.md rename table; §3 (2.0-pin note) |
| packaging/scripts/helpers_v2.1 | helper reference | SKILL.md rules, traps-helpers-and-panels.md; §3 below |
| packaging/misc/shell_variables_scope | bash scoping | §5 below |
| packaging/structure | canonical repo tree | quality-gates.md 0b, repo-hygiene.md, scripts/verify_conformance.py |
| packaging/test | manual tests, package_linter, package_check, CI | SKILL.md Definition of done, repo-hygiene.md; §12 below |
| packaging/publish | catalog submission PR | repo-hygiene.md; §10 below |
| packaging/policy | catalog inclusion policy | repo-hygiene.md:75; §10 below |
| packaging/doc | DESCRIPTION, screenshots, notes | quality-gates.md:27, repo-hygiene.md:74; §11 below |
| packaging/advanced/packaging_v2 | v2 format, converter | SKILL.md; §9 below |
| packaging/advanced/config_panels | config_panel.toml | traps-helpers-and-panels.md §Config panels, app-recipes.md; §8 below |
| packaging/advanced/hooks | hook reference | traps-lifecycle.md, postfix-integration.md; §6 below |
| packaging/advanced/sso_ldap_integration | SSO headers + LDAP | ssowat-integration.md, auth-backend-integration.md; §7 below |
| packaging/advanced/advanced_packagers | dev infrastructure | §13 below |
| packaging/misc/packaging_apps_git | git/PR workflow | quality-gates.md 0b, repo-hygiene.md; §14 below |
| packaging/misc/packaging_apps_virtualbox | VirtualBox dev env | §13 below |
| core/forms (outside packaging) | forms/option-type reference | §16 below |
| core/devenv (outside packaging) | ynh-dev / Incus dev env | §13 below |
| translation (outside packaging) | app-specific translations | §17 below |

## 1. Manifest keys the recipes never name (packaging/manifest)
- `upstream.license` MUST be a valid SPDX id — and if the license is absent from SPDX's list, start the identifier with `LicenseRef-` + a short name (link the full text via license_url). The real license TEXT gate is separate — this is the id format.
- Optional upstream keys: `demo`, `admindoc`, `userdoc`, `cpe` (NIST CPE; may later drive CVE detection), `maintainers` (array).
- Hard limits: name ≤ 23 chars, description ≤ 150 chars.
- `integration.yunohost = ">= 11.1"` minimum core version; `architectures = ["amd64","i386","armhf","arm64"]` (dpkg nomenclature).
- Estimates: `integration.disk`, `ram.build`, `ram.runtime` — declare what the feasibility probe measured.
- `integration.ldap` and `integration.sso` take bool OR the string "not_relevant" — "not_relevant" only when the app has no notion of user account at all (ldap = app uses YunoHost LDAP as account DB; sso = auto-login from the portal works).
- Version visibility: bumping `version` (the ~ynhX part included) is what EFFECTIVELY TRIGGERS the upgrade being offered to instances — forgetting the bump hides the upgrade from every installed box.
- Antifeatures are a 3-step declaration: id from the catalog's antifeatures.toml → declare the id in YunoHost/apps apps.toml at submission → describe it (with translations) in manifest `[antifeatures]`. Current catalog set (antifeatures.toml fetched 2026-10-27, 14 ids, official en glosses): `tracking` (tracks/reports your activity to upstream or third parties, without permission or by default) · `non-free-network` (promotes/depends entirely on a non-free network service) · `non-free-addons` (promotes other non-free apps/plugins) · `non-free-dependencies` (needs non-free software deps to run) · `non-free-assets` (bundled non-free artwork — images/sounds under commercial license; this is where Google-Fonts-style third-party asset calls land) · `bad-security-reputation` (e.g. deprecated addons) · `deprecated-software` (UPSTREAM unmaintained — expect breakage, unfixed CVEs) · `package-not-maintained` (the YNH PACKAGE is unmaintained/needs adoption — inactive maintainer, NOT the same as broken) · `paid-content` (promotes/depends entirely or partially on a paid service) · `arbitrary-limitations` (limitation clauses — explain in the README) · `replaced-by-another-app` (superseded — point to the successor in the README) · `alpha-software` (early development stage, unstable features, bugs, security vulnerabilities) · `not-totally-free-upstream` (upstream license is overall free but with use-restricting clauses) · `not-totally-free-package` (same, for the package itself). Distinguish upstream-vs-package and maintained-vs-working when picking ids; catalog_linter (apps_tools) validates the apps.toml entry against schemas/*.toml.schema.json. Catalog policy: apps must be free software overall (ethical exceptions case-by-case) — non-free upstreams belong in rejectedlist.toml ("won't package"), dead apps in graveyard.toml, ideas in wishlist.toml (all in YunoHost/apps; wishlist browsable + voteable at https://apps.yunohost.org/wishlist — 514 open requests as of 2026-10-27).
- Install question types: string, text, select, tags, email, url, date, time, color, password, path, boolean, domain, user, group, number, range, alert, markdown, file, app. PASSWORD answers are NOT auto-saved as settings (persist what scripts need). Questions are mandatory unless `optional = true` (an empty default is not enough).
- `upstream.website` must be the project's real site, never the git repo URL (linter checks).

## 2. Resources reference facts (packaging/resources)
- apt: the virtual deps package is named `$app-ynh-deps` (underscores → dashes). Extra repositories: `extras.<name>.repo` / `.key` / `.packages` dicts (e.g. yarn's repo). Conditional deps: `packages_from_raw_bash` — a multi-line bash snippet echoing additional packages (arch/Debian-version/install-question-dependent).
- composer: composer.phar lands in `$install_dir`; `composer_version` setting; run composer via `ynh_composer_exec`.
- go: `go_version` setting; toolchain via goenv; unused versions garbage-collected. ruby: COMPILED on target (gcc, make, libjemalloc-dev, libffi-dev, libyaml-dev, zlib1g-dev; rbenv; `ruby_version` setting; slow install).
- Runtime helpers (helpers page; usually provisioned by the resources instead): `ynh_nodejs_install` (uses 'n'), `ynh_go_install` (goenv), `ynh_ruby_install` (rbenv), `ynh_composer_install` / `ynh_composer_exec` — plus `$path_with_go` / `$path_with_ruby` exported for script use.
- ports: `default` auto-increments to a free port when taken; unset default = random 10000–60000; `fixed = true` only when the app needs the exact value (protocol constraint). `exposed` (false / true=Both / Both / TCP / UDP) controls whether the port is FIREWALL-OPENED and publicly reachable — and makes diagnosis check that something answers on it.
- data_dir: `dir` defaults to /home/yunohost.app/__APP__; properties are `owner`/`group` with EMBEDDED permissions (defaults `__APP__:rwx` / `__APP__:rx`) — there is NO separate `mode` key; `subdirs` list pre-creates dirs.
- install_dir: `owner`/`group` (same embedded-perms shape). On FRESH install the folder is DELETED if it already exists (pre-existing /var/www/$app content does not survive). The core MOVES the dir when the `dir` PROPERTY value changes between package versions — NOT on domain/path changes.
- database: settings `db_name`/`db_user`/`db_pwd`; app name sanitized for db identifiers (strip `-` and `.`); only ONE database per app; NO automagic migration if `type` changes mysql↔postgresql — a type change means manual migration work.
- system_user: `allow_ssh` (ssh.app group), `allow_sftp` (sftp.app group), custom `mail_user`/`mail_domain` settings (pair with allow_email for SMTP creds). `home` defaults to /var/www/__APP__ and PLACEHOLDERS DON'T WORK there (no __INSTALL_DIR__/__DATA_DIR__) "for now".
- sources: `prefetch = true` is the DEFAULT (asset fetched during the provisioning phase = install/upgrade); `prefetch = false` defers the download to inside `ynh_setup_source`; RESTORE never fetches either way. `format = "docker"` + `platform` (e.g. linux/amd64) extracts files from a built image (docker-image-extract); `extract = false` + `rename` for asset repackaging; `in_subdir` can be an integer N (strip N leading dirs).
- permissions: `allowed` (default nobody — initialize via an `init_<perm>_permission` question or manifest `<perm>.allowed`), `auth_header` (default true), `protected`, `additional_urls`, `show_tile` (default true when url is set); legacy `is_public` is deleted; UNDECLARED permissions are deleted on upgrade. Permission `url`s may be REGEXES prefixed `re:` (e.g. `re:/api/[A-Z]*$`).
- autoupdate strategy grammar: `latest_<gitforge>_<release|tag|commit>`; gitforges = github, gitlab, gitea, forgejo. release = the only strategy that puts the changelog link in the PR; pre/draft releases ignored. tag = ignores rc/beta/alpha and non-x.y.z tags; `version_regex` (e.g. `^release-v(.*)$`) handles non-standard tag names — the matched group becomes the version; `upstream` can point at a repo other than upstream.code. Per-arch `asset` regexes under `[resources.sources.<id>.autoupdate.asset]`. Local test: clone YunoHost/apps_tools, venv, `python autoupdate_app_sources/autoupdate_app_sources.py <path-or-appid>` (live text shows the localtest-branch invocation; verify CLI flags before teaching `--commit-and-pr` — see §18).

## 3. Helpers v2.1 surface not carried elsewhere (packaging/scripts/helpers_v2.1)
- `ynh_config_add --jinja` — jinja templates with filters `from_json`/`from_yaml`/`from_toml`/`to_json`/`to_yaml`/`to_toml`. THE sanctioned route for complex config files (this skill bans sed on installed files; this is the replacement).
- `ynh_config_add` checksum-TRACKS destinations: it verifies the checksum and backs up the destination file if an admin hand-edited it, then stores the new checksum (matches the observed `.bak` + warning on re-apply).
- `ynh_read_var_in_file` / `ynh_write_var_in_file` (--file --key --value) — get/set values in heterogeneous files (yaml, json, php, python…).
- nginx templates: `#sub_path_only` / `#root_path_only` lines auto-uncomment depending on `$path` — use instead of hand-branching root vs subpath.
- `ynh_config_add_phpfpm` — PHP-FPM integration; tunables `$php_upload_max_filezise` (upstream's own spelling), `$php_process_management`, `$php_max_children`, extra conf via extra_php-fpm.conf; php deps auto-define the `phpversion` setting (use it in templates). Under `php_process_management = "dynamic"` these have NO defaults and MUST be set: `$php_group`, `$php_memory_limit` (nominal default 128M), `$php_start_servers`, `$php_min_spare_servers`, `$php_max_spare_servers`.
- `ynh_config_add_fail2ban`: if `--logpath` / `--failregex` are provided the helper GENERATES the appropriate conf — no f2b templates needed (template route: conf/f2b_jail.conf + f2b_filter.conf; validate with `fail2ban-regex`). `ynh_config_add_logrotate [/path]` / `ynh_config_remove_logrotate`.
- `ynh_systemctl --wait_until="line to match" --log_path=... --timeout=... --length=...` — wait for a log line (do NOT use with Type=notify services that never log a ready line).
- `ynh_local_curl "page_uri" "key1=value1"` — automatizes app-internal install forms from scripts.
- `ynh_replace --match --replace --file` / `ynh_replace_regex` — sanctioned in-file replacement.
- `ynh_store_file_checksum` / `ynh_backup_if_checksum_is_different` (config-file change tracking); `ynh_restore_everything`.
- `ynh_add_swap --size=` (Mb); `ynh_smart_mktemp --min_size=`; `ynh_validate_ip`; `ynh_in_ci_tests`; `ynh_hide_warnings`.
- `ynh_user_get_info --username --key=`; `ynh_user_list`.
- `ynh_exec_as_app` (v2.1 rename of ynh_exec_as) — sudo as $app with $PATH PRESERVED so nodejs/ruby/go toolchains still resolve.
- `ynh_spawn_app_shell` / admin `yunohost app shell <app>` — bash with the app's env loaded (env files sourced, php aliased to the app's PHP version + phpflags).
- `ynh_app_setting_set_default --key=...` doesn't just define the setting, it ALSO EXPORTS the matching shell variable — the sanctioned way to give php-fpm tunables etc. non-default defaults while staying admin-overridable.
- `ynh_app_upgrading_from_version_before_or_equal_to`; `ynh_string_random --length= --filter=`.
- SQL runs through the db shells now: `ynh_mysql_db_shell` / `ynh_psql_db_shell` (heredoc or file) replace v2.0's `ynh_mysql_connect_as` / `ynh_*_execute_as_root`.
- v2.1 source patches: `patches/${src_id}/*.patch` applied to $dest_dir (v2.0 layout was sources/patches/${src_id}-*.patch + sources/extra_files/); `ynh_setup_source --keep "f1 f2"` preserves files across upgrades, `--full_replace` wipes first.
- apt helpers renamed and demoted ("Deprecated Or Handled By The Core / App Resources Since V2"): `ynh_apt_install_dependencies` / `ynh_apt_remove_dependencies` / `ynh_apt_install_dependencies_from_extra_repository` (replacing v2.0's ynh_install_app_dependencies family).
- `ynh_backup` EXCLUDES $data_dir (and children) and /var/log/$app from the pre-upgrade SAFETY backup and when `do_not_backup_data` is set — they survive failed upgrades and remove (unless --purge).
- `ynh_restore` safeguards existing files: an existing file/dir at the destination is backed up to /var/cache/yunohost/appconfbackup/ when lighter than 500MB, otherwise removed.
- Simple templating is case-sensitive: tags UPPERCASE, variable names lowercase; `__PATH__/` collapses to `/` when $path is /.
- Masked settings keys (exact doc list): pwd, pass, passwd, password, passphrase, `secret\w*`, `\w+key`, token, PASSPHRASE.
- MongoDB: `ynh_mongo_exec` / `ynh_mongo_dump_db` / `ynh_mongo_setup_db` / `ynh_mongo_install` / `ynh_mongo_remove_db`; `YNH_MONGO_PWD`.
- Multimedia (shared /home/yunohost.multimedia): `ynh_multimedia_build_main_dir`, `ynh_multimedia_addfolder`, `ynh_multimedia_addaccess`.
- Permissions (script-side, beyond manifest): `ynh_permission_update --add/--remove <groups>`, `ynh_permission_exists`, `ynh_permission_has_user`.
- v2.0 names remain valid ONLY for apps pinning `helpers_version = "2.0"`; under 2.1 they are dead (rename table: traps-helpers-and-panels.md).

## 4. Script-context facts (packaging/scripts)
- change_url variables: `new_domain`, `new_path`, `old_domain`, `old_path`, plus `change_domain` / `change_path` (1 = changed, 0 = not). change_url should essentially just call `ynh_config_change_url_nginx` (v2.0: ynh_change_url_nginx_config).
- remove runs WITHOUT `set -eu` — failing cleanup lines don't abort it; every other lifecycle script gets set -eu automatically. NUANCE: scripts/config still ships `ynh_abort_if_errors` after sourcing helpers — config scripts are NOT auto set -eu (must end with `ynh_app_config_run $1`).
- conf/app.src is the v1 sources format — v2 packages use `[resources.sources]` exclusively.

## 5. Bash variable scoping (packaging/misc/shell_variables_scope) — why ../settings/scripts/_common.sh
- Functions run in the SAME shell: a variable assigned inside a function is global unless declared `local`.
- Pipelines, `( … )` and `$( … )` run in a SUB shell: assignments there NEVER propagate back to the parent.
- `export` only propagates DOWN to child processes, never back up.
- This is WHY backup/restore must source `../settings/scripts/_common.sh` (the execution context differs from the package dir) — the Keep-comment enforced by verify_conformance.py is load-bearing, not ceremony.

## 6. Hooks (packaging/advanced/hooks)
- App packages ship hooks in a TOP-LEVEL hooks/ dir, script named after the hook type (the page's prose says 'post_create_user' but its own reference section says post_user_create — reference wins). The package-root hooks/ dir is what the core copies to /etc/yunohost/apps/<app>/hooks — don't hand-place scripts into /etc/yunohost/hooks.d from install scripts.
- post_app_install: `YNH_APP_ARG_XXXXXXX` (install answers, uppercased).
- post_app_upgrade: `YNH_APP_UPGRADE_TYPE` (UPGRADE_PACKAGE / UPGRADE_APP / UPGRADE_FULL), `NO_BACKUP_UPGRADE`.
- All post_app_* also get: `YNH_APP_ID`, `YNH_APP_INSTANCE_NAME`, `YNH_APP_INSTANCE_NUMBER` (e.g. nextcloud__2 → 2), `YNH_APP_MANIFEST_VERSION`, `YNH_ARCH`; upgrades add `YNH_APP_CURRENT_VERSION`.
- post_app_remove: `YNH_APP_PURGE`; post_app_change_url: `YNH_APP_OLD_DOMAIN` / `YNH_APP_NEW_DOMAIN` / `YNH_APP_OLD_PATH` / `YNH_APP_NEW_PATH`.
- backup/restore hooks: `YNH_BACKUP_DIR`, `YNH_BACKUP_CSV`, `YNH_CWD`.
- User hooks (post_user_create/update/delete): `YNH_USER_USERNAME`, `YNH_USER_MAIL`, `YNH_USER_PASSWORD`, `YNH_USER_FIRSTNAME`, `YNH_USER_LASTNAME`; post_user_update adds `YNH_USER_MAILS` (mail + aliases), `YNH_USER_MAILFORWARDS`, `YNH_USER_MAILQUOTA`; only CLI-provided arguments become env vars.
- Also: post_domain_add/remove, post_cert_update (restart services after a cert change), custom_dns_rules (return a JSON array), post_iptable_rules, backup_method (custom backup targets: need_mount/backup/mount actions). Custom hook naming: `dd-name` (2-digit priority prefix), owned root:root.

## 7. SSO headers + LDAP (packaging/advanced/sso_ldap_integration)
- LDAP parameters for apps that authenticate against the server: host `localhost` / `127.0.0.1`, port `389`, Base DN `dc=yunohost,dc=org`, User DN `ou=users,dc=yunohost,dc=org`, permission-aware search filter `(&(objectclass=posixAccount)(uid=%uid)(permission=cn=__APP__.main,ou=permission,dc=yunohost,dc=org))`, attributes uid / displayname / mail. Real-life examples in the docs: Nextcloud, Wekan.
- Exact header names on YunoHost ≥ 12: `YNH_USER` (HTTP `Ynh-User` / `$_SERVER["HTTP_YNH_USER"]`), `YNH_USER_EMAIL` (Ynh-User-Email), `YNH_USER_FULLNAME` (Ynh-User-Fullname) — all spoof-protected.
- The `Authorization: Basic` header is NOT spoof-protected: a client can send it and it WILL be passed to the application — the app must verify the credentials itself before trusting them.
- WebDAV/CalDAV/CardDAV apps (Nextcloud, SOGo pattern) must opt OUT of basic-auth spoofing protection: `ynh_app_setting_set --key=protect_against_basic_auth_spoofing --value=false` (or post-install `yunohost app setting <app> protect_against_basic_auth_spoofing -v false`), then `yunohost app ssowatconf` + reload nginx.
- Sub-permissions can be initialized by install questions: `init_admin_permission` mirrors `init_main_permission`.
- App logout should redirect to `https://__DOMAIN__/yunohost/sso/?action=logout` so it logs out of YunoHost too.
- SSO-header patterns, spoofing opt-out traps: references/ssowat-integration.md + auth-backend-integration.md.

## 8. Config panel extras (packaging/advanced/config_panels + core/forms)
- Validations: `pattern.regexp` + `pattern.error` (regexp between SINGLE quotes, not double); number/range take `min`/`max`/`step`; file takes `accept`; boolean takes `yes`/`no`.
- Full override set in scripts/config: `ynh_app_config_get` / `_show` / `_validate` / `_apply` / `_run`.
- `visible`/`enabled` are JS expressions (== != > >= < <= ! && ||, arithmetic, `match(v,'regex')`) evaluated against the section's PREVIOUS answers (converted to python on the fly in CLI). Buttons: `type = "button"` (bind forced null) trigger `run__<id>` functions in scripts/config; buttons are ALSO callable from CLI (`yunohost app action run <action_id>`); `enabled` can gate a button on other inputs.
- Password options: tested as a regular user password (≥ 8 chars); `redact` forced true; `example` forbidden; `default` forced empty.
- `optional` defaults false in install questions but TRUE in config panels. `domain` defaults to the main domain, `user` to the first admin found, `group` to all_users (choices all_users/visitors/admins); `tags` serialize as a comma-separated list.
- Panels/sections declare `services` to reload-or-restart when any option in them changes ("__APP__" = the app instance name) — settable per-section too.
(Bind syntax, getters/setters, forbidden short keys: traps-helpers-and-panels.md §Config panels; answer-clobbering trap: app-recipes.md.)

## 9. v1→v2 migration (packaging/advanced/packaging_v2)
- Official converter: `python3 convert_app_to_packaging_v2.py /path/to/app`.
- Settings the core auto-renames: datadir→data_dir, path_url→path, mysqldbpwd/psqlpwd→db_pwd, NAME_port→port_NAME (plus final_path→install_dir). Format history v0/v1/v2, with a v3 on the horizon (further capability constraining per app planned).

## 10. Catalog policy + publish (packaging/policy + packaging/publish)
- Nature-of-app exclusions: resource-hungry relative to features; super-niche-only use cases; cryptocurrency promotion; AI promoted for purposes deemed futile (ecological/sociological cost); tracking/stalking promotion.
- The free-software rule has case-by-case ethical exception families (e.g. ACSL, HL3, CoopCycle, BSL).
- Escape hatches when a package won't be cataloged: users can `yunohost app install <url-to-git-repo>` directly, or add the repo as a custom catalog source in /etc/yunohost/apps_catalog.yml.
- Submission = PR adding the app to apps.toml in the YunoHost/apps repo. Quality LEVELS are bot-assigned, never manual: the bot opens a PR with official CI results every Friday evening; the real catalog (app.yunohost.org/default/v3/apps.json) rebuilds every 4 hours.
- AI-generated packages are formally REJECTED at review if they don't follow the example_ynh template ("decided to reject generated packages that do not follow the example_ynh template") — packagers must be transparent and able to explain every line (matches SKILL.md rule 7).

## 11. doc/ extras (packaging/doc)
- Screenshots: filenames must not start with a dot; keep each under 512kb; subfolders add pictures WITHOUT showing them on the app info page.
- The pre-upgrade note shown to users is taken from the NEW version's PRE_UPGRADE doc.
- PRE/POST install/upgrade notes surface as a CLI keypress and a webadmin popup + dismissable note.
- Notes localize by filename suffix: `doc/{hook}_{locale}.md` or `doc/{hook}.d/{version}_{locale}.md` (no suffix = English); VERSION-SPECIFIC notes live in doc/PRE_UPGRADE.d/{version}.md (and POST_UPGRADE.d), shown when upgrading to that version or higher.
- Repo READMEs in YunoHost-Apps are BOT-MANAGED: yunohost-bot auto-regenerates README.md from doc/DESCRIPTION.md — never hand-edit them. Description/presentation TEXT quality rules (tiles, detail pages, markdown rendering traps, fr pairing): repo-hygiene.md §Catalog-presentation-quality, sourced from YunoHost/issues#2676.
- Version bump + docs via PR comments: `!bump` (bot adds 1 to ~ynhN), `!changelog <text>`, `!pre_upgrade <text>` / `!preupgrade <text>` (bot creates the corresponding doc file).

## 12. Testing & CI (packaging/test)
- package_check manipulates the package in a clean LXC container; scenario matrix: root domain vs subpath, private vs public, multi-instance, upgrade-from-older-commit; snapshots reused between tests. tests.toml tunes package_check (usually near-empty — much is deduced from the manifest).
- QUALITY LEVELS 0-8 (official definitions): 0 broken; 1 installable in ≥1 scenario; 2 installable in ALL scenarios; 3 upgradable; 4 + backup/restore works; 5 + no linter ERROR; 6 + hosted in the YunoHost-Apps org; 7 + all tests pass AND no linter warning; 8 maintained in good long-term quality. Level ≤ 4 = "bad quality": the app gets HIDDEN from the catalog and its upgrades PUT ON HOLD for all users.
- yunorunner interfaces with package_check as a job-queue CI; official levels from ci-apps (triggered on master/main commits); PR validation via dev CI at ci-apps-dev.yunohost.org (URL CONFIRMED 2026-10-27 via example_ynh's PR template). Dev-CI jobs are triggered from PR comments (`!testme`, `!gogogadgetoci`, or the systemd incantation) and REQUIRE YunoHost-Apps org membership — they do NOT fire on personal-repo PRs (pre-transfer alternatives: developer-CI access request, or local package_check — §13); a .png summary is auto-posted when the job completes.
- `yunohost ... --debug` gives verbose operation logs — use before raw op-log forensics.
- Install answers are preconfigurable: `-a "&domain=sub.domain.tld&path=/my_app&init_main_permission=all_users"` (ampersand-separated). Debug flags: `--no-remove-on-failure` (won't remove the app if install fails — the autopsy flag), `--force` to skip unsafe/low-quality/experimental confirmations and the post-install notification pause.

## 13. Dev environments (packaging/misc/packaging_apps_virtualbox + advanced_packagers + core/devenv)
- The docs' sanctioned test bed is a disposable VM/LXC, NOT a production server: torture it, snapshot freely.
- ynh-dev is now INCUS-based: official images per Debian release and branch (before-install/dev/appci/core-tests); appci is what the CI uses.
- VirtualBox recipe: install virtualbox-qt; fake domain `yunohost.packaging` mapped in /etc/hosts; MULTIPLE SNAPSHOT BRANCHES correspond to apps and test types (removal, upgrade, backup/restore) — NOT git branches; access via SSH/SFTP.
- Advanced packagers run parallel VMs/LXCs with per-test domains, share packages via a common dir / rsync / syncthing, and track parallel packaging on a kanban.
- The live-box procedures across this skill are a production-server workflow — prefer a dev VM when testing would be destructive or when a clean package_check run is needed.
- LOCAL package_check dry-run (pre-transfer CI parity — the SAME harness that computes official levels; README-verified 2026-10-27): deps `lynx jq btrfs-progs` + LXD-or-Incus (`incus admin init --minimal`; LXD additionally needs `lxc remote add yunohost https://repo.yunohost.org/incus --protocol simplestreams --public` and the btrfs storage driver), user in the `lxd`/`incus-admin` group, REBOOT after the group add. Run: `git clone https://github.com/YunoHost/package_check && cd package_check && ./package_check.sh <path-or-url-to-app_ynh>`; tune architecture/DIST/YNH_BRANCH via a `config` file in the package_check folder (`ARCH=amd64` / `DIST=bookworm` / `YNH_BRANCH=stable`); results print to terminal AND land in Test_results.log. Scenario matrix: linter, install/remove/reinstall at root domain / subpath / no-url, private install (is_public=0), multi-instance (if multi_instance=true), upgrade from same + previous versions, backup/restore, change_url. TRAP: Incus/LXD DEFINITELY conflicts with Docker (dnsmasq on port 53, bridge firewalling) and MAY conflict with libvirt/LXC — never set it up on a server that runs Docker (e.g. a YunoHost box hosting Pterodactyl/wings): use a dedicated VM or spare host, or the developer CI instead.

## 14. Org-repo git workflow (packaging/misc/packaging_apps_git)
- Start new packages by CLONING example_ynh, not forking it (copy files except .git).
- In YunoHost-Apps org repos NEVER work directly on master: testing branch, merge to master only when green.
- Moving YOUR repo into YunoHost-Apps: Settings → Transfer ownership; write access requested in the Apps room (chat).
- PRs: never uncheck "Allow edits from maintainers". `git pull` before anything else.

## 15. Contradiction register — doc claim vs verified box behavior (keep BOTH sides, labeled)
1. Install answers as bash vars: docs say install answers are auto-available as bash variables AND auto-saved as settings; verified on YNH 12.1 they are in SETTINGS but NOT autoloaded as vars in scripts/install (resource settings like $port DO autoload). Keep the defensive `ynh_app_setting_get` fetch (app-recipes.md). [Live tree still claims this — register valid.]
2. conf_regen hook location: docs say /etc/yunohost/hooks.d/conf_regen/; the end-of-install `hook_remove()` sweep deletes scripts named after the app id — verified. Install to /usr/share/yunohost/hooks/conf_regen/ instead (mailman_ynh precedent; full mechanics: postfix-integration.md). [Live tree still documents /etc/yunohost/hooks.d — register valid.]
3. `ynh_abort_if_errors`: lifecycle scripts get auto `set -eu` and current example_ynh installs ship NO ynh_abort_if_errors — don't re-add it there; BUT scripts/config DOES still use it (config scripts aren't auto set -eu).
4. scripts/ page staleness: its examples still use v2.0 helper names; under a 2.1 pin those are dead — traps-helpers-and-panels.md's rename table is correct.
5. (Fixed 2026-10-27 — was this audit's own error, not a doc contradiction) prefetch semantics: prefetch=true is the DEFAULT and means "fetch at provision time"; prefetch=false defers to inside ynh_setup_source; restore never fetches. An earlier version of this file inverted the flag.
6. multi_instance=false does NOT refuse a second install on YNH 12.1.41.2 (code-read 2026-10-30; manifest-key semantics imply refusal, code doesn't do it): app_install passes action="upgrade" to _check_manifest_requirements (app.py ~1399) while the multi-instance requirement yields only for action=="install" (app_utils.py:949), and _next_instance_number_for_app (app_utils.py:1286) has no gate — a second install proceeds as app__2 over UNSUFFIXED global state (the "app_already_installed" hard-raise only exists in the catalog/info display path, app.py:1309). Consequence + self-guard rule: quality-gates.md §Multi-instance decision rule. Not re-verified on upstream dev (13.x).

## 16. core/forms (outside the packaging tree — the option-type reference)
- The forms page is the full reference for question/option types shared by manifest questions, config panels and other core forms; key behaviors captured in §8 (optional defaults, password rules, regexp quoting, domain/user/group defaults, tags serialization, services auto-reload, run__ buttons + CLI action run).

## 17. translation (outside the packaging tree)
- App-specific translations are GIT-ONLY (not integrated in Weblate): manifest.toml description/ask, doc/*_{locale}.md, and config_panel.toml inline `name.en`/`ask.en`-style keys.

## 18. Unverified-in-live-text items (kept from the preview audit, use with care)
- ci-apps.yunohost.org/ci URL (unconfirmed in live text). ci-apps-dev.yunohost.org: CONFIRMED 2026-10-27 via example_ynh's PR template ("Automatic tests can be triggered on https://ci-apps-dev.yunohost.org/ after creating the PR") — see §12.
- `--commit-and-pr` flag form for autoupdate_app_sources.py (live text shows the localtest-branch invocation only).
