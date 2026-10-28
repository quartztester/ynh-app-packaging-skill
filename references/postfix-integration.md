# Postfix-integrating apps (mailman_ynh pattern)

Verified building anonaddy_ynh (2026-10-11) on YunoHost 12.1.
Outbound half verified wiring loomio_ynh (2026-10-27) — §Outbound below.

## Outbound app mail (SMTP submission via the box's Postfix)

For apps that SEND mail (signup codes, invitations, notifications) — the common case, distinct from the inbound-hook pattern in the rest of this file. Decision + wiring + proof:

- DOES THE APP MAIL? Grep the source for mailers / `login_tokens` / invitation flows BEFORE writing scripts. If yes, mail is part of the functionality gate, not an optional extra.
- DEFAULT WIRING: `SMTP_SERVER=127.0.0.1`, `SMTP_PORT=25`, NO auth (`mynetworks` already trusts localhost), NO implicit SSL. Never default to an external SMTP provider. Expose server/port/ssl/from as config-panel fields with those defaults, rendered through the same env template as everything else. TRAP — DB-held SMTP JSON (listmonk 2026-10-28): when the app stores mail settings in its database, seed `auth_protocol: none` (or omit it) — `login` + empty username/password makes go-smtp attempt AUTH against 127.0.0.1:25, which offers NO auth extension, so EVERY send fails (`SMTP AUTH extension not found`). Invisible to static grading: both arms' JSON passed schema checks; only the with-skill no-auth seeding actually delivered (`status=sent`).
- FROM ADDRESS: must be a domain the server's outbound relay ACCEPTS. Stock YunoHost (full mail stack): `app@<install-domain>` works. Relayhost boxes (outbound relayed through an external verified domain, e.g. a transactional-mail relay): only the relay-verified domain is accepted — a subdomain of a verified domain is NOT verified. Default `app@<install-domain>`, panel-overridable, and document the relay override in ADMIN.md. Verified live 2026-10-28 (listmonk, relayhost box): install-domain From → relay `550 ... domain is not verified` → `status=bounced` — a bounced gate send is a FAIL, not a wiring success; fix the From (panel) and re-run the send.
- RELAY REALITY (admin docs, verified 2026-10-27): an SMTP relay is SERVER-WIDE and transparent — ALL outgoing mail including app-sent mail is delegated, no per-app/per-user choice ("you can't choose which emails or which users"). Relays generally require the sender address to be from your domain, so AUTO-FORWARDED external mail fails silently; relay passwords containing `#` break postfix; some providers rewrite content (MailJet rewrites links for tracking). Also: the diagnosis app continuously RBL-checks the server — app-sent spam can blocklist the whole box's mail.
- TRAP — string-truthy flags: apps reading SSL/tls flags as "is the env var set" (Ruby `ENV['X'].present?`, Go `os.Getenv("X") != ""`) treat `"0"` and `"false"` as TRUE. Verified live: Loomio `SMTP_USE_SSL=0` → mailer opened implicit TLS on port 25 → `OpenSSL::SS::SSLError ... wrong version number` → HTTP 500 on the send endpoint. Render such flags as an EMPTY value when off (`SMTP_USE_SSL=`), and normalize in `_common.sh` (`[[ "$v" == "1" ]] || v=""`), never in the template.
- TRAP — silent no-op sends: mail endpoints often only send for EXISTING/active users (Loomio login_tokens: `account_status :unused` → 200, no email). An HTTP 2xx proves nothing; test against the admin/known-active account.
- TRAP — YNH 12 sender_login_maps + PHP/CI4 apps (castopod, 2026-10-28): when the manifest declares `resources.system_user` + `mail_app_user` (or YNH auto-registers an app sender), Postfix enforces `reject_sender_login_mismatch` — unauthenticated SMTP from :25 with that From gets `553 5.7.1 <app@domain>: Sender address rejected: not owned by user` UNLESS the client authenticates. Auth on :25 requires STARTTLS (`smtpd_tls_auth_only=yes`), and CodeIgniter 4's Email library aborts STARTTLS against TLS1.3 servers (`stream_socket_enable_crypto` returning 0 = "no progress yet" is treated as fatal) while Python smtplib succeeds against the same port — an app-lib failure is NOT a postfix failure, prove the server side with a raw smtplib probe before blaming the MTA. FIX (works with none of the above): switch the app to the LOCAL PICKUP path — CI4: `email.protocol="sendmail"` (uses /usr/sbin/sendmail as the app system user, like Nextcloud); Postfix skips smtpd entirely → no login_maps, no TLS, no SASL. Wire `mail_user`/`mail_pwd` from settings into the app env anyway and keep SMTP fields panel-exposed for portability, but default to sendmail on YNH. Bonus trap: CI4 BaseConfig hydrates from env keys named `<shortPrefix>.<property>` where shortPrefix = strtolower(config class) — `email.protocol`, `email.SMTPHost` (lowercase prefix, original-case property) — uppercase `Email.protocol` does NOT match.
- PROOF (the mail-send gate): trigger a REAL app-level send (login-link/invite/notification through the app's own flow), then:
  1. app responds 2xx AND the mailer raised no 500 (check journal/production log),
  2. `/var/log/mail.log` shows `from=<app@domain> ... queue active`,
  3. the relay handoff line shows `status=sent` (relay=`127.0.0.1`-local delivery or the box's relayhost).
  All three, or mail is not wired. Delivery beyond the relay is the relay's problem; a later bounce for a non-existent recipient still counts as a passed gate (the app→postfix→relay path is what the package owns).

## Hook mechanics
- YunoHost's `19-postfix` owns main.cf/master.cf via regenconf; the sanctioned extension point is a custom conf_regen hook `sources/hooks/conf_regen/98-<app>` copied to `/usr/share/yunohost/hooks/conf_regen/` by the install script. `$YNH_APP_BASEDIR/sources/...` works at install/upgrade (BASEDIR = extracted package dir there) but NOT in change_url/remove (BASEDIR = settings dir, no sources/).
- NEVER install the hook to `/etc/yunohost/hooks.d/conf_regen/`: YunoHost's `hook_remove()` sweeps the custom hooks folder at the END of every install/upgrade and deletes any script whose filename ENDS WITH the app id — a hook placed there is silently uninstalled right after the install script put it in place (observed: install succeeded, regen wired postfix, hook gone 30s later).
- Every `yunohost tools regen-conf` re-applies the integration; manual main.cf edits get clobbered.
- Hook contract: invoked `pre postfix <category> <pending_dir>` ($1 action, $4 pending dir). Hooks get their OWN pending dir/category; main.cf/master.cf are rendered by 19-postfix into the sibling `postfix` category — patch `${pending_dir}/../postfix/etc/postfix/`. master.cf is COPIED from plain/ each regen; main.cf rendered from Jinja → hooks APPEND with sed/marker guards, never rewrite.
- Write app maps (transport/recipient) into `${pending_dir}/../postfix/etc/postfix/` so regenconf installs+tracks them under the postfix category; run `postmap` after regen (hooks cannot use do_post).
- regenconf stale-hash removal: a tracked file is only forgotten when absent from BOTH disk and the pending dir. In `remove`, delete the map files BEFORE the final `regen-conf` (after deleting the hook so the pending side is empty) — otherwise regenconf flags them "manually modified" and KEEPS their hashes, and a later restore refuses to recreate them ("removed manually, and will not be created") so postmap fails.

## Policy-service scoping
- Bare `check_policy_service` in smtpd_recipient_restrictions defers ALL YunoHost mail. Declare `smtpd_restriction_classes` + `check_recipient_access regexp:<map>` that returns DUNNO for non-alias recipients — only alias-domain mail reaches the policy service.

## pipe(8) flags
- Match upstream Docker wiring (AnonAddy = `flags=F`; ReceiveEmail.php strips the mbox `From ` line itself). Verify upstream source reads any headers you plan to have postfix prepend (B/D flags add Return-Path/Delivered-To that upstream may ignore).

## VERP
- Return-path shape `b_<base32(id)>_<hmac-sha3-224-8>@<alias-domain>` must be matched by the recipient-access regexp, alongside plain aliases and `<username>.<alias-domain>` subdomains. relay_domains needs both `domain` and `.domain` (subdomains). VERP signature uses config('anonaddy.secret') — never regenerate that secret on upgrade.

## Multi-instance removal
- ONE shared hook file serves all instances — `remove` must detect surviving instances (iterate `/etc/yunohost/apps/<app>*/settings.yml`, check their install_dir/artisan exists) and keep the hook, deleting it only for the last instance; remove the dying app's dir BEFORE the regen so the hook skips it.

## Lint/test notes
- Template placeholders must resolve in EVERY script that renders: derived vars like `mail_from_address="$app@$domain"` need `ynh_app_setting_set` at install AND a defensive default (`${mail_from_address:-...}`) in the render helper for upgrade/change_url.
- App-version display from tarball installs: no .git → set e.g. ANONADDY_VERSION from a `upstream_version` setting refreshed each upgrade (`${YNH_APP_MANIFEST_VERSION%%\~*}`).
- Admin-email-on-alias-domain validation belongs in install (app's own NotLocalRecipient rule) — die early with a plain-language message.
- package_linter `systemd_config_harden_security` greps `^\s<directive>=` (INDENTED) — column-0 hardening directives trigger a false INFO; indent directives to silence.
- README: regenerate with apps_tools/readme_generator/make_readme.py — pulls catalog metadata by app name, valid even pre-catalog.
- v2 database resource does NOT dump the DB itself — scripts/backup must call `ynh_mysql_dump_db` (NOT `ynh_mysql_db_shell`, which is an SQL runner).
- End-to-end hook test without touching the live tree: render YNH plain/ files + main.cf into a scratch pending dir, strip Jinja lines, run the hook with $4=that dir, then `postconf -c <dir>` + `postmap -q` against the produced maps.
