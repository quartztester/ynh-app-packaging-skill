# Auth backend integration — decision tree + research workflow

STANDING USER POLICY: YunoHost users must be able to SSO into every packaged app as the portal user they're already logged in as, whenever the app makes that possible. Local-password bootstrap is a documented LAST RESORT, never a default. Decision tree below runs BEFORE any script is written; if it lands on local-only, the README must say why an SSO path was impossible.

"How do I make the app give YunoHost users an account on login, like forgejo/nextcloud?" Two distinct layers (official doc, packaging/advanced/sso_ldap_integration):
- **LDAP integration** — app accounts map to YunoHost users (app authenticates against slapd).
- **SSO integration** — a portal session auto-logs into the app (SSOwat header injection, or LDAP bind reused by the app). Exact header names on YunoHost ≥ 12 (live docs, verified 2026-10-27): `YNH_USER` (HTTP `Ynh-User`), `YNH_USER_EMAIL` (`Ynh-User-Email`), `YNH_USER_FULLNAME` (`Ynh-User-Fullname`) — all spoof-protected by SSOwat on protected perms. The `Authorization: Basic` header is NOT spoof-protected: a client-sent Basic header IS passed through to the app, so the app must verify those credentials itself before trusting them.

LDAP without SSO is common and fine; SSO without LDAP is weird. Header-auth is the SSO-only shortcut for apps that can't do LDAP.

## Decision tree — pick the FIRST path the app VERIFIABLY supports
0. **Catalog first**: if the app is already packaged (YunoHost-Apps org, api.github.com/repos/YunoHost-Apps/<app>_ynh), its scripts/conf ARE the reference implementation — read before designing. (No keycloak_ynh / authentik_ynh / authelia_ynh exist in the org — 404s verified 2026-10-27.)
1. **LDAP auth backend** → canonical wiring below. JIT on first login if the app supports it; else sync function.
2. **Trusted-header / proxy auth** → SSOwat injects YNH_USER/YNH_USER_EMAIL/YNH_USER_FULLNAME on protected perms; app creates/mints its session from the header. Traps + recipes: references/ssowat-integration.md.
3. **OIDC/OAuth only** → YunoHost ships NO first-party OIDC IdP (a "walnut OIDC provider" is a memory fabrication — searches + repo GETs come back empty; ALWAYS verify an IdP claim against the GitHub API before designing around it). Real options: YunoHost-Apps/dex_ynh (Dex with LDAP connector serving OIDC — community pattern), or an admin-run external IdP. App side = render issuer/client-id/secret into its env/config; document that the package cannot auto-provision the IdP.
4. **SAML only** (loomio case) → no YunoHost SAML IdP either. Before settling for local accounts, consider a CUSTOM TRUSTED-HEADER PATCH (path 4.5): a small middleware/initializer in patches/main that mints the app session from the portal's injected YNH_USER/YNH_USER_EMAIL headers, with the app permission portal-protected so no public route exists (spoof-safety: only trust the headers where SSOwat strips client-sent copies — a public route plus header trust = anyone can be anyone). Works for any cookie-session app (Rails/Node/Python); costs: custom security-sensitive auth code, patch drift on upstream bumps, app loses anonymous access. This is the sanctioned "makeshift glue" path when the user wants portal-SSO and upstream offers nothing.
5. **Local-only auth** → bootstrap the ADMIN at install from the YunoHost admin (email via `ynh_user_get_info --username=$admin --key=mail`, password install arg). Regular users: CHECK the registration service for email-gating before promising self-signup — apps that prove email control with a mailed code/link (e.g. Loomio's RegistrationService → :send_code) dead-end without SMTP; then either wire the panel's SMTP settings to the box's Postfix relay or document admin-creates-users via the app CLI. Say so in README — never fake SSO.

LOOMIO OUTCOME (live-verified): no LDAP gem, no omniauth, no header auth; sessions controller accepts only login-link/code/local-password (+ SAML gated on SAML_APP_KEY with an external IdP). Package bootstrapped a local admin; user pushback ("password should be my yunohost one") → path 4.5 offered and DECLINED — local accounts accepted as this app's ceiling; second-user onboarding = wire panel SMTP (email-gated signup) or admin-create via CLI.

## Research workflow for a new app (do this BEFORE writing scripts; ~15 min)
1. Upstream docs/readme: grep for `LDAP | OIDC | SAML | proxy auth | trusted header | REMOTE_USER | auth providers | SSO`.
2. Source greps by stack (in the extracted source tree):
   - Rails: Gemfile — `devise-ldap-authenticatable`, `omniauth-*`, `ruby-saml`, `openid_connect`; config/initializers/devise.rb; routes gated by ENV (loomio mounts SAML routes only when `ENV['SAML_APP_KEY']` is set); `bin/rails routes | grep -iE 'session|sign_in'` + the sessions controller — SPA apps expose login as a JSON API route (e.g. POST /api/v1/sessions), not the Devise form path.
   - Node: package.json — `passport-*`, `openid-client`, `next-auth`, `@auth/*`; env like `AUTH_TRUST_HEADER`, `HEADER_AUTH`.
   - Python: settings `AUTH_LDAP_*` (django-auth-ldap), `authlib`/flask-oidc config classes.
   - PHP: config arrays with `ldap`/`oauth`/`saml` keys.
   - Go: config.yaml `auth: ldap|oauth2` blocks.
3. Admin CLI: backends configurable via CLI are the cleanest to wire idempotently — forgejo `forgejo admin auth add-ldap`, nextcloud `occ ldap:*`.
4. **JIT check**: does the FIRST successful external login auto-create the local profile? Nextcloud: yes. Forgejo: yes on login, plus on-demand full sync (`POST /api/v1/admin/cron/sync_external_users` with an admin API token stored in app settings — forgejo_ynh `synchronize_users()`). Loomio SAML: `IdentityService.link_or_create` = JIT. If NO JIT: pre-provision admin at install + idempotent sync function in _common.sh called from install AND upgrade AND restore.
5. Nothing found → path 5, document honestly.

## Canonical LDAP wiring (verified in YunoHost-Apps/nextcloud_ynh conf/config.json + forgejo_ynh)
- host `localhost`, port `389`, tls `0`, **anonymous bind** (no agent DN — slapd allows anonymous read of the user tree; Nextcloud ships no ldap_dn/agent keys).
- Base DN `dc=yunohost,dc=org`; users `ou=users,dc=yunohost,dc=org`; groups `ou=groups,dc=yunohost,dc=org`.
- **Permission-aware login filter** (only users holding the app's `main` permission can authenticate):
  `(&(|(objectclass=posixAccount))(|(uid=%uid)(mail=%uid))(permission=cn=__APP__.main,ou=permission,dc=yunohost,dc=org))`
- Attributes: uid / displayname / cn / mail; groups: posixGroup, `memberUid` assoc, cn display, userquota quota.
- Forgejo CLI equivalent (forgejo_ynh): `forgejo admin auth add-ldap --name "YunoHost LDAP" --host localhost --port 389 --security-protocol Unencrypted --user-search-base 'ou=users,dc=yunohost,dc=org' --user-filter '()' --email-attribute mail` — note the EMPTY filter (all ynh users can bind; ssowat permission still gates the HTTP surface). Prefer the permission-aware filter when the app accepts a login filter.
- Gate the wiring at install: nextcloud runs `occ ldap:test-config` and `ynh_die`s on failure — do the same with the app's own test command if it has one.
- The filter references `cn=<appid>.main` — re-render it in change_url? No (app id never changes), but it DOES embed the permission name: if you rename/split permissions later, re-render the app's LDAP config too.

## Rules regardless of path
- ALWAYS bootstrap the admin from the YunoHost admin at install — the admin should never self-register (loomio_ynh: `bin/rails runner bootstrap_admin.rb` with LOOMIO_BOOTSTRAP_EMAIL from `ynh_user_get_info`).
- Credential resets via an app CLI (rails runner, occ, manage.py): pipe the secret with `printf '%s' "$PW" | sudo -u $app …` — a `<<<` heredoc appends a newline that becomes part of the stored value, and login then fails with the exact wrong-password symptom you were fixing. After ANY reset, re-exercise the real login endpoint before reporting success.
- Portal-gate (`main` protected) when the app lacks real SSO: access control from the portal, app login separate — that's the honest ceiling; say it in README. Public `main` only for apps with their own solid auth or genuine anon surfaces.
- Logout asymmetry (official doc): app logout ≠ portal logout; only patch the app's logout to `https://<domain>/yunohost/sso/?action=logout` when trivial (Nextcloud can't).
- Declare integration honesty in the manifest: `integration.ldap` / `integration.sso` take bool OR "not_relevant" ("not_relevant" only when the app has no notion of user account at all); README states whether portal auto-login works (catalog convention).
- `protect_against_basic_auth_spoofing=false` ONLY for CalDAV/CardDAV/WebDAV/webmail-style apps that validate Basic credentials themselves (Nextcloud/SOGo pattern): `ynh_app_setting_set --key=protect_against_basic_auth_spoofing --value=false` then `yunohost app ssowatconf` + reload nginx.
- Sub-permissions can be initialized at install via an `init_admin_permission` question (mirrors init_main_permission) — use it to gate an admin UI behind admins from day one.
- Config-panel settings for auth backends must re-render the app's config from settings (upgrade-durability rules apply).
