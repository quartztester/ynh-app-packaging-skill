# Per-app packaging recipes — verified builds (ynh-app-packaging)

Moved verbatim from SKILL.md on 2026-10-26. App-specific war stories; load only when packaging the named app or its family.

## YNH 12.1 packaging details verified building anubis_ynh (nginx lua gate + Flask webui + sudo helper, 2026-10-10)
- **WSGI servers drop underscore headers.** waitress silently discards
  `YNH_USER` (only RFC token chars). Re-forward in the app's nginx fragment:
  `proxy_set_header Ynh-User $http_ynh_user;` and read
  `request.environ["HTTP_YNH_USER"]` in Flask — dashed and underscored names
  both map to that WSGI key.
- **`ngx.location.capture` fails inside HTTP/2** ("http2 requests not
  supported yet" — YunoHost vhosts speak HTTP/2). A pcall-wrapped capture
  error silently fails gates open. For rewrite-phase gates calling a local
  service, use `ngx.socket.tcp` cosockets with a hand-rolled minimal HTTP/1.1
  request; strip CR/LF from header values before sending.
- **systemd: any seccomp-backed sandbox option implicitly raises
  NoNewPrivileges** (deb12/systemd-252) — including `PrivateDevices`,
  `LockPersonality`, `ProtectKernelTunables`, `CapabilityBoundingSet`,
  `SystemCallFilter`. A service that must sudo a helper cannot use ANY of
  them (`systemctl show -p NoNewPrivileges` lies — check
  `/proc/<MainPID>/status`). Safe for sudo-callers: `PrivateTmp`,
  `DevicePolicy`, `ProtectProc`, `ProtectControlGroups`. `ProtectSystem=full`
  ro-mounts /etc → breaks helpers writing /etc/nginx/conf.d or settings.yml.
- **`ynh_config_remove_systemd` takes the service as POSITIONAL arg**
  (`ynh_config_remove_systemd "$app"`), unlike add which uses `--service=`.
  Passing `--service=` silently skips removal (garbage unit names).
- **Anubis specifics**: check API (`/.within.website/x/cmd/anubis/api/check`,
  requires `X-Real-IP`) answers DENY with HTTP 200 unless the policy sets
  `status_codes: {CHALLENGE: 401, DENY: 403}` explicitly — ship policy.yaml
  (mapping form `bots:` + `status_codes:`; the built-in default-config.yaml
  is a bare list, indent under `bots:`). Gate: 401→307 to
  `/.within.website/?redir=`, 403→block, else pass (fail-open).
- Health-probe the check endpoint with `curl -s -o /dev/null -w %{http_code}` and accept ANY code 100–599 as "serving": DENY/CHALLENGE answers are non-2xx BY DESIGN, so `curl -sf` false-fails a healthy server and rolls back good installs.
- Local gate tests from the box itself originate at 127.0.0.1, which the shipped private-addresses ALLOW rule passes straight to SSO (302) — to exercise the gate, spoof a public client with `-H "CF-Connecting-IP: 8.8.8.8"` (the package's client-ip map honors it): browser UA → 307 to `/.within.website/`, denied bot UA → 403, unprotected domains unaffected. Testing from the box without the spoof proves nothing about the gate. A protected domain with no app installed still gets gated, then falls through to YunoHost's default vhost / SSO redirect — expected, not a gate bug (the GUI marks such domains 'no vhost yet').
- GUI policy editing: transcribe validator key lists from upstream's Go config structs (lib/config/config.go, checker.go) so the editor accepts exactly what the binary accepts — including nameless `import:` rule entries and matcher keys like geoip/asns/headers that a naive bots-schema misses.

## YNH 12.1 packaging details verified building remark42_ynh (native Go binary, 2026-10-10)
- Per-arch sources: NOT `platform.map.*` — schema wants `[resources.sources.main.amd64] url/sha256` tables (flat `url=` fallback used when present); autoupdate asset map is a `[resources.sources.main.autoupdate.asset]` table with arch keys.
- Mail sender wiring is a TWO-PATH decision keyed on `allow_email` (both paths live-verified): `[resources.system_user] allow_email = true` provisions SASL creds (login=$app / password=$mail_pwd setting) AND registers the sender in postfix sender_login_maps — unauthenticated localhost:25 sends with that From are then 553-rejected (`not owned by user`) and the app MUST authenticate (dovecot STARTTLS on :25) or switch to the sendmail pickup path (see postfix-integration.md §Outbound). WITHOUT `allow_email`, the sender stays unregistered and plain unauthenticated localhost:25 submission is ACCEPTED — simplest wiring for notify-only apps. Verify the chosen path with a real app-level send + mail.log queue handoff either way. Go SMTP to this box needs SMTP_INSECURE_SKIP_VERIFY=true.
- Optional install questions need `optional = true` — an empty-string default is NOT enough ("Value is required" blocks omitting them).
- go-flags boolean env vars accept only true/false — map yes/no manifest choices before template render.
- `yunohost app config set <app> -a "k=v&k=v"` serialized form; a JSON payload is silently parsed as 'nothing changed'.
- Config-panel `bind = "settings"` stores the setting only — override `ynh_app_config_apply` to also re-render env/config files; core then restarts services listed in the panel.

## YNH 12.1 packaging details verified building gmaps_ynh (native Go binary + Playwright Chromium, 2026-10-14)
- `ynh_systemctl --action=daemon_reload` is INVALID — systemd replies "Unknown command verb daemon_reload" and the helper fails the script. Use bare `systemctl daemon-reload`.
- `StandardOutput=append:/var/log/$app/$app.log` requires the log dir to EXIST and be app-owned BEFORE first start, else the unit crashloops `status=209/STDOUT` (fails before ExecStart spawns — the binary log never appears; journal has the real error). mkdir -p + chown in install AND upgrade AND restore.
- Apps with NO own login (protected wholly by SSO perm): `ldap = "not_relevant"`, `sso = "not_relevant"` in [integration]; don't fake "partial".
- Playwright-go apps (gosom/scrapemate family): upstream binary honors `PLAYWRIGHT_INSTALL_ONLY=1` (installs driver+chromium and exits, run as app user) and `PLAYWRIGHT_BROWSERS_PATH`. Point browsers into `$data_dir/browsers`, exclude from backup (~650MB, re-installable), and re-run the installer idempotently in restore/upgrade. The playwright driver itself extracts to the app user's ~/.cache/ms-playwright-go — it lives under $install_dir/.cache when HOME=$install_dir, so backup of install_dir covers it.
- ynh_restore default-permission chmod-400 hit a restored SUBDIR of data_dir (`$data_dir/webdata`) too — the end-of-script `chown -R` + `chmod 0750` fix must run AFTER all ynh_restore calls, not between them. Symptom: sqlite `unable to open database file: out of memory (14)` in the app log.
- Upstream web UIs that hardcode absolute URLs (`/jobs`, `/static/`) force root-path installs: document it, pin `path = "/"` in tests.toml args, and exclude `multi_instance_and_domain_not_constrained`.
- New `yunohost domain add` gets a SELF-SIGNED cert (LE issuance needs the domain registered long enough / --no-checks may still work: `yunohost domain cert install <d> --no-checks` issued instantly once DNS (Cloudflare wildcard) resolved). Browser shows privacy error until then — check `yunohost domain cert status` before debugging the app.
- nginx hairpin hang returned after repeated reloads during lifecycle tests (known nchan symptom on this box, other vhosts hang too): `systemctl stop nginx; pkill -9 nginx; systemctl start nginx` restores all vhosts.
- tests.toml v1 schema is minimal: `test_format = 1` + `[default]` suite keys only (`exclude`, `only`, `args`, `preinstall`, `curl_tests`...). The old per-test inline form (`test1 = { title=..., urls=[...] }`) and an `install_args` table both fail schema validation — default install args go in `[default.args]`.
- Do NOT re-add the old `ynh_app_setting_set --key=final_path` line from 2.0-era packages/tutorials: v2.1 has no `$final_path` variable and `set -u` kills the install with `final_path: unbound variable` at the very END of the script (everything above it succeeded — the failure looks unrelated to its cause).
- remark42 specifics: binary inside tarball is `remark42.linux-<arch>` (mv needed); frontend hardcodes `/api/v1` so root-path-only; email user id = `email_<sha1(email)>` (go-pkgz/auth v2); magic-link confirm URL is `/auth/email/login?token=<jwt>` (NOT /confirm); comment POST body uses `locator:{site,url}` + `?site=` query and refuses posting to remark42's own domain; SSE stream location needs proxy_buffering off + long read timeout.
- remark42 SITE/REMARK_URL MUST be settings-backed (incident 2026-10-26): a same-origin blog placement (blog proxies `/comments` to the app; nginx confs outside the app) carried `SITE=<blog-domain>` + `REMARK_URL=https://<blog-domain>/comments` as LIVE-ONLY env edits. The next `app upgrade` re-rendered `/etc/remark42/env` from the template — SITE vanished → remark42 fell back to the default `remark` site DB (user comments invisible; the site DB itself stayed intact on disk). Fix: `SITE=__SITE__` / `REMARK_URL=__REMARK_URL__` in conf/env, `ensure_placement_settings()` (ynh_app_setting_set_default site=$domain, remark_url=https://$domain$path) called from render_env_file, box overrides via `yunohost app setting remark42 site -v ...`. Lesson generalizes: ANY env var the running service depends on that isn't derivable from standard settings needs its own setting + template placeholder — `ynh_config_add` overwrites managed files on every pass (YunoHost keeps the manual copy as `.backup` in /var/cache/yunohost/appconfbackup — restore-from-there is the recovery when it already bit).

## YNH 12.1 packaging details verified building sveltia-cms-auth_ynh (unmodified Cloudflare Worker on a Node shim, 2026-10-15)
- `ynh_config_add`/`_ynh_replace_vars` substitutes ONLY uppercase `__FOO__` tags (from lowercase `$foo`). Lowercase placeholders pass through SILENTLY (no ynh_die) — rendered config keeps literal `__site_hosts__` and the app misbehaves confusingly far from the cause.
- `config_panel.toml` must sit at the PACKAGE ROOT (archived to /etc/yunohost/apps/<app>/config_panel.toml), NOT under conf/ — wrong location = 'No config panel found'.
- scripts/config TRAP: panel answers arrive as shell variables named by the TOML short keys. Never re-fetch those same names from settings at script top — that clobbers the NEW answers with OLD values, the core diff says 'Nothing has changed', settings never update, yet the CLI still prints 'Config updated as expected'. Use `${key:-$(ynh_app_setting_get --key=key)}` fallbacks INSIDE the apply override only.
- Manifest `version` upstream part must be dpkg-parseable — a bare git sha ('33674be~ynh1') passes install but every later `app upgrade` dies 'Failed to parse app version'. Recovery needs BOTH the archived /etc/yunohost/apps/<app>/manifest.toml sed'd AND `rm -rf /var/cache/yunohost/app_tmp_work_dirs/app_<hash>`.
- Install answers ARE committed to settings BEFORE scripts/install runs but were NOT autoloaded as shell variables in it — fetch custom keys explicitly with ynh_app_setting_get (resource settings like $port DO autoload). Docs claim answers are also auto-exported as bash vars in scripts/install — see the contradiction register in references/official-docs.md; keep the defensive fetch.
- Stateless Worker→Node port pattern: vendor upstream index.js unmodified as worker.js; ~45-line node:http shim (reconstruct Request URL from X-Forwarded-Proto/Host; Node<19 needs `globalThis.crypto ??= webcrypto`; skip hop-by-hop headers) + `{"type":"module"}` package.json; env via EnvironmentFile 600; [resources.nodejs] uses the shared /opt/node_n install (version="24" → zero download).
- **GitHub OAuth client secret is NOT replaceable by a PAT** — the token-exchange POST rejects it. Validate a client_id/secret pair WITHOUT completing the OAuth flow: POST `https://github.com/login/oauth/access_token` (Accept: application/json) with client_id + candidate secret + a fake `code` — `incorrect_client_credentials` = bad pair, `bad_verification_code` = pair accepted (secret is real). Never wire a general-purpose high-scope PAT into an app env file when a purpose-specific credential is required; test empirically and refuse politely.
- Secret-typed settings: use `type = "password"` in BOTH the manifest install question and config_panel.toml — masks entry and makes `yunohost app config get` print the value as `**************` (plain `string` type echoes secrets into every config view).
- sveltia-cms-auth ALLOWED_DOMAINS ground truth: the worker embeds the allowlist as `trustedPatterns` regexes in the HTML served by `/auth` (the domain check is client-side, so 200-for-any-Origin is correct behavior) — curl `/auth?provider=github` and grep the served body for the compiled patterns to prove an allowlist change took effect; the worker trims spaces and supports `*` wildcards in the comma-separated list.
- No `yunohost app config check` subcommand on YNH 12.1 (only get/set). To validate an edited config_panel.toml without reinstalling: copy it over the archived `/etc/yunohost/apps/<app>/config_panel.toml` and run `yunohost app config get <app>` — it parses the panel and prints (masked) values.

## Reference package built with this workflow
plausible_ynh (https://github.com/quartztester/plausible_ynh): native Elixir/OTP release + ClickHouse, SSO walk-in, config panel, full lifecycle verified, catalog-ready assets.
i2pd_ynh (https://github.com/quartztester/i2pd_ynh): upstream-deb wrapping — pinned per-arch deb + sha256, config-before-deb ordering, native AppArmor paths, coexistence ports with the java_i2p app.

Learned building plausible_ynh (native Elixir/OTP + ClickHouse) 2026-10-10; verified by full install/backup/remove/restore/upgrade cycles. Re-verified applying ~ynh5 on the live server 2026-10-26.

## RPC-on-live-node steps in upgrade scripts (~ynh5 finding, 2026-10-26)
- `plausible rpc` provisioning (`Plausible.Release.YunohostSetup.provision_user`) executes on the LIVE node only. The upgrade script runs it BEFORE the service restart → every upgrade logs `WARNING --rpc-eval : RPC failed with reason :noconnection` + 'Could not re-provision the SSO account (non-fatal)' and skips it. REPO FIX PENDING: move the provisioning block AFTER the restart step (+ wait_for_url). Until then, re-run manually post-upgrade: `sudo -u plausible bash -c "set -a; source /var/www/plausible/env; set +a; cd /home/yunohost.app/plausible; /var/www/plausible/app/bin/plausible rpc 'Plausible.Release.YunohostSetup.provision_user(\"<email>\", \"<name>\")'"`.
- Landed-state check: `sudo -u postgres psql plausible -t -A -c 'SELECT email,name FROM users;'` — SSO match key is users.email == SSOwat-injected YNH_USER_EMAIL. (Install-time RPC works because the service is already up; only upgrade ordering is broken.)

## Secrets consistency across reinstall/upgrade (the 516 cascade)
- ALL generated secrets (db_pwd, ch_password, secret_key_base, totp keys) live in app settings as the single source of truth; scripts re-render env/users.d from settings. NEVER regenerate a secret in upgrade/restore — a reinstall that rotates a password while ClickHouse keeps the old one in memory → every event flush fails CH 516.
- upgrade must re-sync dependency config files (e.g. users.d XML) AND restart the dependency service, even when 'nothing changed' — idempotent no-op when unchanged.
- ClickHouse DICTIONARIES bake the password at migration time (SOURCE(CLICKHOUSE ... PASSWORD) in CREATE DICTIONARY, LIFETIME(MIN 0 MAX 0) = cached forever). After ANY ch_password change: re-run the data migration that creates them (e.g. Plausible.DataMigration.AcquisitionChannel.run(quiet: true) inside the live node via `bin/plausible remote`) or every INSERT touching dictGet/dictHas fails 516 even though direct queries succeed.
- Symptom fingerprint: app's own queries work (IngestRepo.query → OK) but WriteBuffer flushes fail 516 mentioning dictGet/dictHas functions = stale dictionary credentials, not connection credentials.

## BEAM/Erlang releases under YunoHost
- Never run `bin/<app> eval/version` from YunoHost's script CWD (`/var/cache/yunohost/app_tmp_work_dirs/app_*`, root 700): the VM crashes at boot with `Kernel pid terminated (logger)` / badarg persistent_term code_server. Always `cd '$data_dir'` inside the exec-as-app subshell first.
- `systemctl start` returns before the BEAM finishes booting (~20s cache warmers). Probe a public HTTP route in a curl loop (e.g. `/js/script.js`), not /health (may redirect pre-first-launch) and not systemctl state.

## ClickHouse
- `https://packages.clickhouse.com/deb/archive.key` is DEAD (404). Key `8919F6BD2B48D754` from `hkp://keyserver.ubuntu.com:80`; `gpg --export` includes signing subkey `3E4AD4719DDE9A38` which signs InRelease. Mirror the armored export to a stable HTTPS URL (GitHub release asset) for manifest `apt.extras.key`.
- users.d password changes need `systemctl restart clickhouse-server` (in-memory auth) — restart after writing the XML in install AND restore.
- CH never logs 'Ready for connections' to the journal; Type=notify means systemctl start blocks until ready — don't use --wait_until.
- Dump tables per-table `FORMAT Native`, excluding MaterializedView/View engines; skip empty dump files on restore (NO_DATA_TO_INSERT).

## Forgejo Actions / forgejo_runner (verified 2026-10-13)
- DON'T package what exists: YunoHost-Apps/forgejo_runner_ynh is official (salamandar) — install it instead. For a local forgejo on a SUBPATH: local_forge=0 + forge_url=https://domain/forgejo + manual token (`sudo -u forgejo /var/www/forgejo/forgejo actions generate-runner-token`); the local_forge=1 path builds URL from domain setting only, ignoring path.
- YNH forgejo package ships `[actions] ENABLED = false` — runner register then 404-pings `/api/actions/ping.v1.PingService/Ping` and RETRIES FOREVER (looks like a network hang; it is not). Fix: `yunohost app config set forgejo main.actions.actions_enabled -v true`. Verify ping answers 200 before blaming nginx/DNS.
- Diagnosis pattern that works: run register manually as the app user with a timeout, tcpdump loopback to capture the real POST path, check 404 vs 405 (405 = route exists, wrong method).

## Castopod (CodeIgniter 4 podcast server, verified 2026-10-28)
- Source: GitHub `castopod/castopod` release zips 404 — upstream ships release tarballs from `code.castopod.org` (ad-aures GitLab) with a PREBUILT `vendor/` (no composer step). Pin url+sha256 to that tarball.
- Install routes are registered via `app/Config/Routing.php` (`$routeFiles`), NOT `Routes.php` includes — and `InstallController::index()` HARD-404s once `.env` is complete AND an `is_owner` user exists. So the web wizard is single-shot: after `spark install:init-database` + CLI superadmin creation, /cp-install is gone by design. Bootstrap the superadmin with `spark user:create <email>` + SQL `is_owner=1` (shield group `superadmin`) — never rely on the wizard from a package.
- Admin/auth gateways are env-configurable (`admin.gateway=cp-admin`, `auth.gateway=cp-auth`) — permission regexes must match the RENDERED values, and the SSO wall goes on the admin gateway only (public podcast pages + RSS + `/media/` stay visitors).
- `location /media/` must alias the DATA dir (podcast covers/audio land there via the app) — nginx serves them directly; missing alias = broken covers after first upload.
- Media derivatives (thumbnails etc.) are generated by `cp-scheduled-tasks` — a systemd TIMER. v2.1 `ynh_config_add_systemd` only knows `*.service`: write the `.timer` pair manually + bare `systemctl daemon-reload` (`ynh_systemctl --action=daemon_reload` is invalid — helper passes the verb verbatim AND appends the unit name).
- Podcast create form validates hard: `handle` regex, `owner_email` + `location_name` REQUIRED (silent plain-redisplay on missing), cover must be a real PNG ≥ minimum dims. Gate with a multipart curl POST, then `UPDATE cp_podcasts SET published_at=NOW()` (DB default is NULL = unpublished).
- Mail: see postfix-integration.md §Outbound — CI4 STARTTLS is broken vs TLS1.3; default `email.protocol="sendmail"` (env keys are `email.<Property>` — lowercase prefix).

## Gitea (Go git forge, verified 2026-10-28)
- Source: single Go binary per-arch from GitHub releases (`gitea-<ver>-linux-amd64`, `-arm64`, `-arm-6`); declare one `[resources.sources.main.<arch>]` per arch with url+sha256, `in_a_subdir = false`. No build toolchain. Ship `git` (+ `git-lfs` if wanted) in apt.
- DB: postgres resource works cleanly (`ynh_psql_db_shell` for login-source seed SQL and backup/restore dumps). Official gitea_ynh uses MariaDB; postgres is equally supported upstream (`app.ini [database] DB_TYPE=postgres`).
- Auth: LDAP login source seeded by SQL into `login_source` (cfg JSON: Host 127.0.0.1, port 389, BindDN `uid=<app>,ou=apps,dc=yunohost,dc=org` + bind password from `yunohost app setting`, UserDN `ou=users,dc=yunohost,dc=org`, Filter `(&(uid=%s)(objectClass=posixAccount)(permission=cn=<app>.main,ou=permission,dc=yunohost,dc=org))`, AdminFilter `cn=<app>.admin,...` style; `Attributes` map username/mail/name). Web login auto-provisions user rows (`login_source=1`, empty passwd). Admin = YNH `admins` group via AdminFilter.
- **`protect_against_basic_auth_spoofing=false` app setting + forced portal regen is MANDATORY** (traps-helpers-and-panels §SSOwat) — git-over-HTTP, the REST API, and the OCI registry all authenticate with client basic auth that ssowat otherwise strips.
- app.ini: `[server] DOMAIN/ROOT_URL/SSH_DOMAIN`, `HTTP_ADDR=127.0.0.1`, `HTTP_PORT=$port`; `[session] PROVIDER=db` (memory sessions die on restart mid-upgrade); `[log] MODE=file` to `/var/log/$app/`; `[mailer] SMTP 127.0.0.1:25 no-auth (postfix-integration §Outbound); `[security] INTERNAL_TOKEN` random; INSTALL_LOCK=true. Render with ynh_config_add and re-assert on upgrade (gitea rewrites app.ini itself on start — template only needs to be correct at provision time).
- nginx: root location proxies `127.0.0.1:$port` with `client_max_body_size 100m` (git pushes); separate `/v2/` permission (container_registry, visitors, auth_header=false) if the registry is exposed.
- Backup/restore: `ynh_backup "$install_dir"` + data_dir + `pg_dump`-equivalent via `ynh_psql_db_shell` into `$data_dir`/backup staging; restore re-imports SQL, re-seeds `login_source` from a STAGED file — resolve package-relative files with `$(dirname "$0")/<file>` (restore CWD is the archive staging dir, traps-lifecycle).
- Gates: web login 303→/explore, `curl -u` API 200 (NO cookie jar!), repo create (settle 3-5s after login), git clone/push over https with LDAP creds, anon clone of a public repo, admin permission separation (regular user 403 on /-/admin, admin 200).
