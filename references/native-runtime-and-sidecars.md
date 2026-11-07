# Native runtimes and private sidecar services (no Docker)

Pattern proven packaging a Bun/Elysia server (cap) that upstream only ships as a Docker image: native runtime binary + private per-app redis, both under YunoHost resources.

## Pinned runtime binary via resources.sources
- Official runtime releases (oven-sh/bun, nodejs) publish per-arch zips → per-arch source entries:
  ```toml
  [resources.sources.bun]
  format = "zip"
  amd64.url = ".../bun-linux-x64.zip"   # sha256 each
  arm64.url = ".../bun-linux-aarch64.zip"
  ```
  Zip has one `bun-linux-<arch>/` level → default `in_subdir = true` lands `bin/bun` clean. `chmod 755` after extract.
- Monorepo tarball for a subdir app (e.g. `standalone/`): DO NOT use `in_subdir = 2`. `ynh_setup_source` implements it as `tar --strip-components=2`, which flattens EVERY second-level dir into dest_dir — in the cap monorepo `docs/package.json` clobbered `standalone/package.json` and bun installed a bogus 19-pkg dev tree (app: `Cannot find module '@elysiajs/cors'`, install fails at the health probe). Correct pattern: `in_subdir = 1` extracting into a staging dir (`$install_dir/.repo`), then a `_common.sh` helper that `mv`s the wanted subdir's files over the previous ones (rm -rf src/ public/ + tarball-supplied files first; preserve node_modules, cache dir, bin/, env). No helper does strip-components for zip; single-level (in_subdir=true) is safe there.
- Keep runtime version + app version both recorded as app settings (`bun_version`, ...) so upgrade scripts can compare.
- **pnpm/npm monorepo module paths (umami iteration-7): resolve build-time deps by BARE require with cwd = build root, never a hardcoded `<subdir>/node_modules/<pkg>` path.** pnpm installs a package's deps where THAT package declares them: umami v3's `bcryptjs` sits in the ROOT `package.json`, so it materializes at `build/node_modules/bcryptjs` while `build/src/node_modules/bcryptjs` does not exist — a hardcoded src-relative require dies at install with `Cannot find module` even though a scratch smoke "proved" it (scratch layouts differ from the real build tree). `node -e` resolves bare specifiers from the process cwd, so inside the build pushd: `ynh_exec_as_app node -e 'console.log(require("bcryptjs").hashSync(process.argv[1], 10))' "$pw"`. Before hardcoding ANY module path, verify where the dep is declared: `grep '"<pkg>"' <build>/{package.json,*/package.json}` — declare-where-installs-where is the rule.

## Offline lockfile install as the app user
```bash
ynh_exec_as_app env HOME="$install_dir" \
  bash -c "cd '$install_dir' && '$install_dir/bin/bun' install --production --frozen-lockfile --cache-dir '$install_dir/.bun-cache'"
```
- The system user has NO writable home (`/var/www/$app` exists but set HOME explicitly — bun/node caches want `$HOME`).
- `--frozen-lockfile` = exact versions from bun.lock/package-lock; offline after first resolution when versions are already in the lockfile cache dir. Keep the cache dir in-tree (`.bun-cache`) and pass it via `--keep` on upgrade's `ynh_setup_source` so upgrades resolve from cache.
- `ynh_setup_source` without `--keep` wipes the dest dir (incl. node_modules) — always reinstall deps after setup_source in upgrade, and list runtime artifacts (`bin/`, dot-cache dirs) in `--keep`.

## Private per-app redis instance (recommended over shared DB numbers)
YunoHost's `ynh_redis_get_free_db` shares the system redis (flushdb risk, config drift, no per-app auth). For apps whose state is critical (keys, sessions), run a PRIVATE instance like upstream's compose does with a dedicated valkey container:
- Book a SECOND port: `[resources.ports] redis.default = <port>` → setting `$port_redis` (named ports expose as `port_<name>`; `main` → plain `$port`). Loopback-bound; never firewall-allowed.
- Own `redis.conf` template rendered into `$install_dir`: `port __REDIS_PORT__`, `bind 127.0.0.1 -::1`, `requirepass __REDIS_PASSWORD__` (generated, stored in settings, never printed), `dir $data_dir/redis`, `save 60 1`, `maxmemory 128mb`, `maxmemory-policy noeviction` (noeviction matters: eviction of `noeviction`-flagged auth/session keys silently breaks the app; upstream compose pins the same).
- Second systemd unit via `ynh_config_add_systemd --service="${app}-redis" --template=redis.service` (`Type=notify` is valid for Debian redis-server with `--supervised systemd`; `ReadWritePaths=$data_dir/redis` for the dump dir under ProtectSystem=full). Register both with `yunohost service add`.
- The app unit gets `After=`/`Requires=` on `${app}-redis.service`; stop/start order: app first down, redis second; start reverse.
- Backup: `redis-cli -h 127.0.0.1 -p $port_redis -a $redis_password --no-auth-warning bgsave` in the backup script, then the RDB rides along inside the already-declared `$data_dir` backup. Auth via env or `-a --no-auth-warning` only — the password must never hit logs.
- apt `redis-server` is then just the binary provider; remove scripts leave the package installed (shared system redis may use it).

## Pinned standalone CPython for modern Django/Python apps (linkding_ynh, 2026-10-26)
When the app needs a Python newer than Debian's (Django 6 wants ≥3.13; Debian 12 ships 3.11), pin [astral-sh/python-build-standalone](https://github.com/astral-sh/python-build-standalone) per-arch tar.gz as a `resources.sources` entry extracted to `$install_dir/python`, and pin `astral-sh/uv` the same way (`$install_dir/.uv-bin`) to sync deps from the app's committed lockfile (`uv sync --frozen --no-dev`) as the app user.
- **CC trap**: the standalone build's sysconfig hardcodes `CC = clang` (rarely installed) — export `CC=gcc` plus `LDFLAGS="-L$install_dir/python/lib -Wl,-rpath,$install_dir/python/lib"` for any C extension build (uwsgi), or uv dies with "you need a C compiler".
- **Relocated interpreter under uwsgi**: `--virtualenv` mangles PYTHONHOME for a relocated standalone interpreter. Instead set unit env `PYTHONHOME=$install_dir/python` + `PYTHONPATH=$install_dir/.venv/lib/python3.N/site-packages` and drop the flag.
- **uv cwd trap**: YunoHost runs scripts from a root-owned tmp dir; uv's config discovery walks UP from cwd and dies on EACCES. Always `cd '$install_dir'` (inside the `ynh_exec_as_app bash -c`) before invoking uv. Keep `.cache` in the setup_source `--keep` list so re-syncs stay fast.
- **Env-var FORMAT verification**: before templating any `LD_*`/`*_PATH` var, read the upstream settings module for how it composes URLs from it — linkding builds routes as `"/" + LD_CONTEXT_PATH + "route"`, so the correct value is `path/` (NO leading slash). A wrong format produces app-level 404s on every route that masquerade as nginx/permission bugs. Same discipline for Python-bool vars (`True`/`False` literal casing).
- Subpath apps: uwsgi static maps need the context prefix too (`static-map = /<context>static=static`); nginx `client_max_body_size 100m` if the app imports HTML files.
- SQLite apps: run `manage.py enable_wal` once (install) — concurrent web+worker access without WAL corrupts/collides; tasks DB (`migrate_tasks`) is separate.


## Redis URL forms worth knowing (Bun RedisClient, ioredis)
- `redis://:pass@host:port` and trailing `/N` DB selection both honored — but a private instance beats DB-index isolation on a shared server.
- Apps that `PING` at boot and crash on failure: install scripts must start the private redis BEFORE the app unit and health-loop on the app's combined `/health` (not just `/health/live`).

## Admin-key apps (no user system, single master key)
- Manifest `[install.admin_key] type = "password"` question; store in app settings so config panel/restore can re-render env. Help text must tell the user how to read it back (`yunohost app setting <app> admin_key`).
- Double-lock model: portal gates the key-management API prefixes; the app's own key guards its dashboard. Tell the user in install output + README which prefix is portal-gated.
- Rate-limit/IP awareness: behind nginx always set `proxy_set_header X-Forwarded-For $remote_addr` (overwrite, not append) for apps that trust XFF — client-forged chains get stripped; CF-fronted domains additionally get CF-Connecting-IP which most apps read first anyway.

## GUI-app containers (webtop/selkies family): probe before declaring infeasible
- For `linuxserver/docker-<app>`-style desktop images, read the Dockerfile via raw.githubusercontent and the file list via `api.github.com/repos/<repo>/git/trees/<branch>?recursive=1` FIRST: these repos often ship only the upstream AppImage/deb extracted to /opt plus launcher scripts — the real machinery lives in the base image (compositor + WebRTC/VNC browser streaming + s6), not in app-specific code.
- Consequence: the app is NOT docker-only — pin the upstream binary via `ynh_setup_source` (AppImage → `--appimage-extract` into `$install_dir`), apt-install the Electron GUI deps (`libgtk-3-0 libnss3 libatk-bridge2.0`). The packaging work is the streaming layer, not the app.
- Minimal native streaming stack, all stock Debian: xvfb + x11vnc + noVNC/websockify, nginx with websocket upgrade, ssowat in front (VNC password in app settings). Latency worse than WebRTC but fine for text apps; chasing GPU-parity WebRTC stacks (Selkies/KasmVNC) natively is not worth the fragility.
- Flag BEFORE investing: these containers expose ONE shared desktop session — YunoHost multi-user collapses into a single shared app instance/vault.

## Python apps upstream ships as Docker+Chrome images (flaresolverr_ynh)
- Upstream's release tarball can be a pyinstaller bundle with an amd64 Chrome baked in — read the Dockerfile first: if it's just `pip install` + apt chromium, package THAT natively (source archive + `python3 -m venv` + apt `chromium chromium-driver xvfb`) and get `architectures = "all"` for free where the binary bundle gives amd64-only.
- Docker-isms hardcoded in app code (`/app/chromedriver` detection) → `sed -i` the one literal to `$install_dir/...` in install AND upgrade (source re-extracts every upgrade). Never populate system `/app` — collides across multi-instance.
- Chromium-driven Python caches (undetected_chromedriver's patched binary) write under `$HOME`: set `Environment=HOME=__DATA_DIR__` in the unit, else it writes to root's home when run by systemd.
- app's pinned deps vs Debian python: check `requires_python` on PyPI for the pinned versions before committing to bookworm python (websockets 17 needs >=3.11 = bookworm exactly OK).
- Functionality test payload for FlareSolverr v3.5+: `{"cmd":"request.get","url":"...","method":"get"}` — flat, no `params` wrapper, cmd is dotted (`request`, or nested `params`, both return a parse-ish error that looks like a broken service).

- v2.1 has NO `ynh_exec_warn_less` (v1 helper, dies 'command not found' mid-upgrade): plain command + `-qq` flags, or `ynh_exec_and_print_stderr_only_if_error` / `ynh_hide_warnings` from helpers.v2.1.d/logging.
