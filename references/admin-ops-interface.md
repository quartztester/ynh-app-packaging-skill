# Admin-side behavior your package must survive (ynh-app-packaging)

From the ADMIN docs (doc.yunohost.org/admin, all 75 pages audited 2026-10-27; every fact quote-verified in the fetched text). These are things admins DO to apps that dev docs never mention — the package must keep working under them. Read when designing backup/restore, permissions, file layout, or mail.

## Backup/restore from the admin's side
- The model is "reinstall + reincorporate data": only useful files are archived; restore scripts reinstall dependencies. So venvs/node_modules/apt deps must NOT be in the backup — but everything needed to rebuild (configs, DB dumps, sources refs) must be.
- Restore preconditions: the app must NOT already be installed (restoring an old version requires uninstall first), and its domain must already exist on the box. App IDs collide on server merges (nextcloud vs nextcloud__2).
- Admins (and the core itself during upgrades of data-heavy apps) run CORE-ONLY backups: `BACKUP_CORE_ONLY=1` env or permanent setting `do_not_backup_data=1` skips large data dirs. The backup script must cleanly separate "core" from bulk data or core-only restores break the app.
- No general file-exclusion mechanism exists; the only user-side lever is an empty `.nobackup` file which excludes a FIRST-LEVEL subfolder of /home (and admins drop one in SFTP homes to avoid double-backing bind-mounted app dirs).
- Custom backup methods are hooks in /etc/yunohost/hooks.d/backup_method receiving work_dir/name/repo/size/description with need_mount/backup subcommands; custom data joins system backups via backup/restore hooks in /etc/yunohost/hooks.d/backup.
- Each archive is a .tar + .json sidecar PAIR — anything that moves archives must keep both (docs tell admins to download both files).
- Hand-added apps/databases/configs outside YunoHost tracking are NOT backed up at all.

## Filesystem reality (paths are not always plain dirs)
- Admins relocate /var/www/$app, /home/yunohost.app (canonical heavy-data dir: nextcloud, matrix…), /opt, /var/lib/mysql, /var/lib/postgresql onto other disks — via bind mounts (docs-preferred) or symlinks, both documented as able to break apps and the backup system. Never assume an app path is a real directory on the root filesystem; put heavy data in data_dir (/home/yunohost.app/__APP__ default).
- NodeJS app versions pile up in /opt and admins clean unused ones — never rely on a previously installed node/ruby version persisting; the resource must own the toolchain.
- SFTP-on-apps: users are chrooted in $HOME; app access is granted by bind-mounting /var/www/$app into /home/USER/apps/$app + fstab entry, then setgid dirs (g+s) + POSIX ACLs (app system user rwX, config files r-- for the app user). File layouts must keep working under ACL/setgid permissions.
- Only admins-group users have SSH/SFTP by default; non-admins need the ssh/sftp permissions.

## Permissions, groups, portal
- is_public gates the whole app behind the SSO at install; later changed via groups/permissions (`yunohost user permission …`). Permissions can target sub-URLs (e.g. wordpress.admin); some are "protected" (visitors can't be added); each permission can have its own portal tile (`--show_tile`).
- Default groups: all_users, visitors, admins. Groups carry mail aliases (admins gets root@, webmaster@, postmaster@, abuse@…; the FIRST user created also gets root@ and admin@ on the main domain) — mail to those reaches all group members.
- The SSO/portal is reachable ONLY via the real domain name, never the server IP (unlike the webadmin) — testing via IP will false-fail SSO flows.
- LDAP/SSO autologin is per-app optional and the app README is expected to STATE whether it works. Multi-instance apps get suffixed IDs (nextcloud__2) — never assume the bare app name is unique.

## Mail from the admin's side
- An SMTP relay (relayhost) is SERVER-WIDE and transparent: ALL outgoing mail, including app-sent mail via local postfix, is delegated — no per-app or per-user choice. Relays generally require the sender address to be from your domain, so auto-forwarded external mail silently fails.
- Relay quirks seen in the wild: passwords containing `#` break postfix; some providers rewrite content (MailJet rewrites links for tracking).
- Plus-suffix addressing delivers user+folder@domain into that mailbox folder — mail-handling apps must cope. Mail credentials are the BARE username (no @domain); IMAP 993 SSL/TLS, SMTP 587 STARTTLS.
- Diagnosis continuously RBL-checks the server — app-sent spam can blocklist the whole server's mail. Reverse DNS is set at the ISP/VPS or outgoing mail is marked spam.
- When the server is down, senders' servers keep retrying ~5 days — bounces for app mail can arrive much later.

## Certificates and TLS
- Let's Encrypt certs auto-renew ~every 3 months, and cert operations REGENERATE the SSOwat configuration.
- Custom certs live at /etc/yunohost/certs/DOMAIN/{crt,key}.pem, root:ssl-cert 0640 (ssl-cert group; metronome no longer used), with a -history/stamp dir of past configs. Admins are told to avoid custom certs — packages must work with default self-signed/LE flow.
- The global nginx TLS policy is switchable via yunohost settings (Mozilla intermediate default vs modern) and app vhosts inherit it — never hand-roll TLS directives or cert paths in app nginx confs.
- .onion domains are added as normal domains; SSOwat can be disabled per-domain by commenting the access_by_lua line in that domain's nginx conf.

## fail2ban / security / cleanup
- Fail2ban bans after 5 failed SSH logins for ~10 min (recidive escalates); bans are IPv4-only — and can be triggered by an APP client with a stale password (e.g. Nextcloud desktop) hammering auth. App jails/whitelists must live in /etc/fail2ban/jail.d/*.conf (jail.conf is overwritten on fail2ban updates).
- `yunohost tools basic-space-cleanup` reclaims apt/journal/log space — app logs under /var/log are fair game.
- Hand-editing a regen-conf-managed file FREEZES regen-conf updates for that file (kept as manually-modified) — apply changes through settings/hooks, never by editing managed files. `yunohost tools regen-conf --with-diff --dry-run` previews pending diffs.
- YunoHost auto-redacts secrets from operation logs and yunopaste — secrets printed to stdout may not stay visible in logs.
- Apps are expected to run as a dedicated system user with restricted capabilities (further constraining planned for packaging v3).

## Admin CLI surface (what admins run against your package)
- `yunohost app shell <app>` (v11.1.21.4+): bash as the app's system user, cd'd to the app dir, service env preloaded, php overridden to the app's PHP version — the canonical admin debugging entry. Config panels read/written via CLI with dotted key paths. Apps relabel (`app change-label`) and move (`app change-url -d -p`) — change-url support is user-visible.
- Broken-at-latest-version apps are repaired by users re-running `yunohost app upgrade <app> -F` (force) — same-version forced upgrades are a documented USER repair path, another reason upgrade must be idempotent.
- Post-install instructions/credentials are expected in the admin user's MAILBOX — deliver install info there (or state where it is).
- Quality is scored 0-8 by automated CI; apps at level ≤4 are hidden from the catalog and their UPGRADES PUT ON HOLD for all users — broken gates freeze every installed instance, not just new installs.

## Debian migrations (what users' boxes do to your package)
- Post-migration pending migrations rebuild Python apps' venvs (driven by a marker file next to the venv: `*.requirements_backup_for_bullseye_upgrade.txt`, admins may delete it to opt out) and jump PostgreSQL 13→15. Python apps stay down until the venv rebuild; borg/borgserver additionally need `app upgrade -F`.
- After the Bookworm migration nginx itself may need a restart (Error 500 everywhere); dead phpX-fpm after Bullseye is the documented symptom telling users to force-upgrade PHP apps. Restoring an old-version backup onto a newer YunoHost is a supported repair path (fixed with `yunohost tools regenconf nginx --force`).

## Domains/DNS constraints users hit
- One free nohost.me/noho.st/ynh.fr domain per instance (unlimited subdomains); IDN domains must be passed as punycode on the CLI; .local domains (mDNS) cannot have subdomains — an app can never sit at sub.domain.local.
- Installing an app at a SUBDOMAIN ROOT path=/ locks that subdomain to that one app (no other app installable there).
- Moving an app to another domain/path only works if the app supports URL change; the documented fallback is backup → uninstall → reinstall → restore.
- The recommended DNS zone ships wildcard A/AAAA (any app subdomain resolves), MX, SPF `v=spf1 a mx -all`, DKIM mail._domainkey, DMARC — app mail features depend on these. A broken IPv6 with an AAAA record breaks Let's Encrypt: don't assume AAAA presence means working IPv6.

## Blast radius / ecosystem
- A broken app install or removal can take nginx down for the WHOLE server (all apps + webadmin) — bad nginx conf in one package is box-wide. 502s on apps = backend service failing: register app services with `yunohost service add` so `yunohost service status` surfaces them.
- The Redirect app is the blessed way to expose manually-installed/Docker apps (reverse-proxy to 127.0.0.1:PORT + nginx/SSOwat conf + tile); My Webapp is the empty-shell app for user-dropped sites — don't duplicate either role in a package.
- YunoHost deliberately does NOT use Docker/hard containerization for apps (native services only — matches the skill's native-packaging rule).
- Theming customizes ONLY the user portal (logo, colors, custom CSS, tile display modes) per top-level domain — there is no documented injection of portal theming into app pages, so app UIs are safe; the portal can also show a public-apps page to anonymous visitors and lists apps from all domains by default.
