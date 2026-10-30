# Platform traps — ROUTER (ynh-app-packaging)

Split into four topical files 2026-10-27 so a small-context agent loads only the domain it's debugging (was one 39k file). Content moved verbatim. Pick by symptom:

| Symptom / task | File |
|---|---|
| Helper name renames, `__FOO__` templating, env/dotenv quoting, config-panel.toml, systemd helper signatures, ynh_restore permission fixups | references/traps-helpers-and-panels.md |
| What survives upgrade/restore, patches/<source_id>/, backup→remove→restore mechanics, canary discipline, remove cleanliness, half-registered apps | references/traps-lifecycle.md |
| SSO symptoms: 401s despite valid creds, Authorization headers rewritten/injected (basic-auth clients, Bearer/JWT SPAs), permissions that look configured but don't gate, public endpoints 302ing to the portal, regex permission URIs, portal-login scripting | references/ssowat-integration.md |
| npm/bundler build failures, engine pins, patch generation, SPA/API auth endpoints, demo modes, login throttles, app-CLI env, mail flags, Laravel/Eloquent, root-helper apps, deb wrapping | references/traps-build-and-appcode.md |
| Driving yunohost ops (background jobs, PTY prompts, global lock, op-log forensics), portal/SSO testing, this box's nginx/DNS/lock quirks, bash sed traps | references/traps-box-and-ops.md |

Adjacent homes (not traps): mail-stack conf_regen hooks + outbound SMTP recipe → references/postfix-integration.md; Docker-only upstreams packed natively → references/native-runtime-and-sidecars.md; official-docs facts (resources details, autoupdate, hooks copying, manifest limits) → references/official-docs.md; admin-side behaviors your package must survive (backups, moves, SFTP, relays, certs, migrations) → references/admin-ops-interface.md; settling a claim from core code (on-disk paths, repo layout, citation convention) → references/core-internals-map.md.
