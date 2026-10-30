#!/usr/bin/env python3
"""Static rubric grader for YunoHost packages (benchmark/eval use).

Usage: python3 grade_static.py <package_dir> [--expect-version 2.0.6] [--no-network] [--pii REGEX]...

Emits JSON: per-check pass/fail + evidence, scored vs informational totals.
Calibrated against a level-8 official catalog repo, which scores ~19/21 —
it fails only catalog-presentation checks (description bullet format, in-repo
logo) that are intentional discriminators (this skill's rule 10 exceeds
common official practice). See references/benchmarking.md for the procedure
and the v2-manifest false-fail traps encoded below. PII patterns are passed
as --pii args — nothing personal is baked into this public-bound script.
"""
import json, os, re, subprocess, sys, glob, urllib.request, hashlib, tempfile

PKG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
ARGS = sys.argv[1:]
NO_NET = "--no-network" in ARGS
EXPECT_VER = (ARGS[ARGS.index("--expect-version") + 1]
               if "--expect-version" in ARGS else None)
EXTRA_PII = [ARGS[i + 1] for i, a in enumerate(ARGS) if a == "--pii" and i + 1 < len(ARGS)]
DEFAULT_PII = [r"\b10\.\d+\.", r"\b192\.168\.\d+", r"\b172\.(1[6-9]|2[0-9]|3[01])\.\d+"]
PII_PATTERNS = DEFAULT_PII + EXTRA_PII
BANNED_FILLER = ["self-hosted", "selfhosted", "simple", "lightweight", "light-weight",
                 "easy to use", "easy-to-use", "beautiful", "modern", "powerful"]

def helpers_dir():
    cands = sorted(glob.glob("/usr/share/yunohost/helpers.v2*.d"))
    for c in cands:
        if "2.1" in c:
            return c
    return cands[-1] if cands else None

HELPERS_DIR = helpers_dir()

def sh(cmd, cwd=None):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, cwd=cwd)

def check(name, passed, evidence="", informational=False):
    return {"name": name, "passed": bool(passed), "evidence": str(evidence)[:300],
            "informational": informational}

def png_dims(path):
    try:
        with open(path, "rb") as f:
            d = f.read(26)
        if d[:8] == b"\x89PNG\r\n\x1a\n" and d[12:16] == b"IHDR":
            return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")
    except Exception:
        pass
    return None, None

def get(d, dotted):
    for part in dotted.split("."):
        if isinstance(d, dict) and part in d:
            d = d[part]
        else:
            return None
    return d

def grade(pkg):
    checks = []
    def exists(rel):
        return os.path.exists(os.path.join(pkg, rel))

    # 1. manifest parses
    manifest = None
    try:
        import tomllib
        with open(os.path.join(pkg, "manifest.toml"), "rb") as f:
            manifest = tomllib.load(f)
        checks.append(check("manifest-parses-toml", True, "tomllib OK"))
    except Exception as e:
        checks.append(check("manifest-parses-toml", False, f"{e}"))
        return checks, None

    # 2. packaging format + helpers
    pf = manifest.get("packaging_format")
    hv = get(manifest, "integration.helpers_version")
    checks.append(check("packaging-format-2", str(pf) == "2", f"packaging_format={pf}"))
    checks.append(check("helpers-version-2.1", str(hv) == "2.1", f"helpers_version={hv}"))

    # 3. required keys (v2 schema: license in [upstream], integration block — NOT root)
    req = ["id", "version", "name", "description.en", "description.fr",
           "upstream.license", "upstream.code",
           "integration.yunohost", "integration.helpers_version",
           "integration.architectures", "integration.sso", "integration.ldap"]
    missing = [k for k in req if get(manifest, k) is None]
    checks.append(check("manifest-required-keys", not missing, f"missing={missing}"))

    # 3b. question schema vs the BOX's own parser (umami iteration-7: baseline
    # put v1-era `full_domain = true` inside [install.domain] — tomllib parses,
    # static checks pass, but YNH 12's pydantic OptionsModel rejects the
    # manifest at install time with "extra fields not permitted" = dead
    # package. tomllib-only "parses" is NOT a schema validation.)
    try:
        sys.path.insert(0, "/usr/lib/python3/dist-packages")
        import moulinette
        from moulinette.core import Translator
        # group-type options translate choice labels during validation; bare
        # imports have no translator -> fake 'translator' attr failures
        moulinette.Moulinette18n.translator = Translator("/usr/share/moulinette/locales", "en")
        from yunohost.utils.form import OptionsModel
        bad_q = []
        for qname, qdef in (manifest.get("install") or {}).items():
            if not isinstance(qdef, dict):
                continue
            try:
                OptionsModel(**{qname: qdef})
            except Exception as e:
                bad_q.append(f"{qname}: {str(e).splitlines()[1].strip() if len(str(e).splitlines())>1 else e}")
        checks.append(check("manifest-question-schema", not bad_q, "; ".join(bad_q) or "box OptionsModel accepts all install questions"))
    except ImportError:
        checks.append(check("manifest-question-schema", True, "yunohost core not importable here — informational", informational=True))

    # 4. id valid
    app_id = manifest.get("id", "")
    checks.append(check("app-id-valid", bool(re.fullmatch(r"[a-z0-9_]+", app_id or "")), f"id={app_id!r}"))

    # 5. version format (+ expected upstream release if given)
    ver = str(manifest.get("version", ""))
    checks.append(check("version-ynh-format", bool(re.fullmatch(r"[\w.+-]+~ynh\d+", ver)), f"version={ver!r}"))
    if EXPECT_VER:
        checks.append(check("version-matches-expected-upstream", ver.startswith(EXPECT_VER),
                            f"version={ver!r} expected prefix {EXPECT_VER}"))

    # 6. bash -n every SHELL script (skip .sql/.py/.conf assets that live in scripts/)
    sdir = os.path.join(pkg, "scripts")
    scripts = sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []
    bad = []
    for s in scripts:
        root, ext = os.path.splitext(s)
        if ext and ext != ".sh":
            continue  # non-shell asset (sql fixtures, python helpers) — not bash syntax
        r = sh(["bash", "-n", os.path.join(sdir, s)])
        if r.returncode != 0:
            bad.append(f"{s}: {r.stderr.strip()[:120]}")
    checks.append(check("scripts-bash-n-clean", not bad and len(scripts) >= 4,
                        f"bad={bad}" if bad else f"{len(scripts)} scripts: {scripts}"))

    # 7. no hallucinated helpers (against on-box helpers dir for the pinned version)
    defined = set()
    if HELPERS_DIR and os.path.isdir(HELPERS_DIR):
        for f in os.listdir(HELPERS_DIR):
            try:
                txt = open(os.path.join(HELPERS_DIR, f), encoding="utf-8", errors="ignore").read()
                defined |= set(re.findall(r"^(_?[a-z0-9_]+)\s*\(\)", txt, re.M))
            except Exception:
                pass
    # package-local definitions count too: a ynh_-prefixed function
    # defined in the package's own scripts/_common.sh is callable, not
    # hallucinated (e.g. i2pd's ynh_check_tcp_port_free)
    for s in scripts:
        lext = os.path.splitext(s)[1]
        if lext and lext != ".sh":
            continue
        try:
            ltxt = open(os.path.join(sdir, s), encoding="utf-8", errors="ignore").read()
            defined |= set(re.findall(r"^(_?[a-z0-9_]+)\s*\(\)", ltxt, re.M))
        except Exception:
            pass
    used, halluc = set(), set()
    for s in scripts:
        txt = open(os.path.join(sdir, s), encoding="utf-8", errors="ignore").read()
        # strip full-line comments: helper NAMES mentioned in prose comments
        # (e.g. explaining behavior) are not calls and must not be flagged
        code_lines = [l for l in txt.splitlines() if not l.lstrip().startswith("#")]
        code = "\n".join(code_lines)
        for call in re.findall(r"\b(ynh_[a-z0-9_]+)\b", code):
            used.add(call)
            if defined and call not in defined:
                halluc.add(call)
    checks.append(check("no-hallucinated-helpers", not halluc,
                        f"hallucinated={sorted(halluc)}" if halluc
                        else f"all {len(used)} distinct ynh_* calls defined ({HELPERS_DIR} + package scripts)"))

    # 8. core file set (README_fr / _common.sh / change_url are optional even in level-8 repos)
    core = ["manifest.toml", "LICENSE", "README.md",
            "doc/DESCRIPTION.md", "doc/DESCRIPTION_fr.md", "tests.toml"]
    missing_files = [c for c in core if not exists(c)]
    checks.append(check("core-file-set", not missing_files, f"missing={missing_files}"))

    # 9. lifecycle scripts
    need_scripts = ["install", "upgrade", "remove", "backup", "restore"]
    miss_s = [s for s in need_scripts if not exists(f"scripts/{s}")]
    extras = [s for s in ("change_url", "_common.sh") if exists(f"scripts/{s}")]
    checks.append(check("lifecycle-scripts-present", not miss_s,
                        f"missing={miss_s}; extras={extras}"))

    # 10. LICENSE = real license text, not placeholder (repo license may legitimately
    # differ from the upstream app's license — never grade "matches upstream")
    lic = ""
    try:
        lic = open(os.path.join(pkg, "LICENSE"), encoding="utf-8", errors="ignore").read()
    except Exception:
        pass
    placeholder = bool(re.search(r"fill me|example_ynh|TODO", lic[:500], re.I))
    real = len(lic) > 1000 and not placeholder and bool(
        re.search(r"copyright|GNU|MIT|BSD|Apache|zlib|Mozilla|licence|license", lic, re.I))
    checks.append(check("license-real-text", real, f"len={len(lic)}; placeholder={placeholder}"))

    # 11. tests.toml parses
    terr = None
    try:
        import tomllib
        with open(os.path.join(pkg, "tests.toml"), "rb") as f:
            tomllib.load(f)
    except Exception as e:
        terr = str(e)
    checks.append(check("tests-toml-parses", terr is None, terr or "tomllib OK"))

    # 12. config panel (ecosystem usability)
    panel = "present"
    cp = os.path.join(pkg, "config_panel.toml")
    if os.path.exists(cp):
        try:
            import tomllib
            with open(cp, "rb") as f:
                panel_doc = tomllib.load(f)
            # vocabulary check: YNH pydantic closed enums the CLI hides
            ALLOWED_TYPES = {"display_text","markdown","alert","button","string","text",
                             "password","color","number","range","boolean","date","time",
                             "email","path","url","file","select","tags","domain","app",
                             "user","group"}
            bad_types, bad_patterns = [], []
            def walk_opts(node, path=""):
                if not isinstance(node, dict):
                    return
                t = node.get("type")
                if isinstance(t, str) and t not in ALLOWED_TYPES:
                    bad_types.append(f"{path}: type={t}")
                p = node.get("pattern")
                if isinstance(p, str):
                    bad_patterns.append(f"{path}: pattern must be a table (regexp/error)")
                for k, v in node.items():
                    if isinstance(v, dict) and k not in ("pattern",):
                        walk_opts(v, f"{path}.{k}" if path else k)
            walk_opts(panel_doc)
            if bad_types:
                panel = "vocab-error: " + "; ".join(bad_types[:3])
            elif bad_patterns:
                panel = "vocab-error: " + "; ".join(bad_patterns[:3])
        except Exception as e:
            panel = f"parse-error: {e}"
    else:
        panel = "absent"
    checks.append(check("config-panel", panel == "present", f"config_panel.toml: {panel}"))

    # 13. description quality (catalog-presentation rules)
    desc_en = get(manifest, "description.en") or ""
    filler = [w for w in BANNED_FILLER if w in desc_en.lower()]
    desc_ok = len(desc_en) >= 30 and not filler
    dmd = ""
    try:
        dmd = open(os.path.join(pkg, "doc/DESCRIPTION.md"), encoding="utf-8", errors="ignore").read()
    except Exception:
        pass
    bullets = len([l for l in dmd.splitlines() if l.strip().startswith(("-", "*"))])
    checks.append(check("description-quality-catalog", desc_ok and bullets >= 2,
                        f"desc_en_len={len(desc_en)}; filler={filler}; DESCRIPTION.md bullets={bullets}"))

    # 14. logo: square PNG >=128px in-repo (discriminator — official repos often lack one)
    logos = []
    for root, _, files in os.walk(pkg):
        if ".git" in root:
            continue
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), pkg)
            if rel.lower().endswith(".png") and re.search(r"logo|icon", rel, re.I):
                logos.append(os.path.join(root, f))
    logo_ok = False
    logo_ev = f"logo candidates={len(logos)}"
    for lp in logos:
        w, h = png_dims(lp)
        if w and w >= 128 and abs(w - h) <= max(2, w // 16):
            logo_ok = True
            logo_ev = f"{os.path.relpath(lp, pkg)} {w}x{h}"
            break
    checks.append(check("logo-square-128", logo_ok, logo_ev))

    # 14b. informational: screenshots
    shots = []
    for root, _, files in os.walk(pkg):
        if ".git" in root:
            continue
        # YNH convention: screenshots live in a doc/screenshots/ DIRECTORY with
        # arbitrary filenames (homepage.png, profile.png) — match path, not just name
        if "screenshot" in root.lower():
            shots.extend(os.path.relpath(os.path.join(root, f), pkg) for f in files)
            continue
        for f in files:
            if "screenshot" in f.lower():
                shots.append(os.path.relpath(os.path.join(root, f), pkg))
    checks.append(check("screenshots-present", bool(shots), f"{shots}", informational=True))

    # 15. source sha256 verified by download (flat url or arch-mapped sources)
    sha_ok, sha_ev = False, "no source"
    try:
        src = get(manifest, "resources.sources.main") or {}
        # arch-mapped: sources.main.amd64.url/.sha256 (gitea-style binary releases)
        entry = src
        if not src.get("url"):
            for arch in ("amd64", "arm64", "armhf", "i386", "x86_64"):
                cand = src.get(arch) or {}
                if isinstance(cand, dict) and cand.get("url") and cand.get("sha256"):
                    entry = cand
                    break
        url, declared = entry.get("url"), str(entry.get("sha256", ""))
        if url and declared:
            if NO_NET:
                sha_ok, sha_ev = None, "skipped (no-network)"
            else:
                with tempfile.NamedTemporaryFile(delete=True) as tf:
                    urllib.request.urlretrieve(url, tf.name)
                    actual = hashlib.sha256(open(tf.name, "rb").read()).hexdigest()
                sha_ok = actual == declared
                sha_ev = f"declared={declared[:12]} actual={actual[:12]} (arch-mapped)" if entry is not src else f"declared={declared[:12]} actual={actual[:12]}"
    except Exception as e:
        sha_ev = f"error: {e}"
    checks.append(check("source-sha256-correct", sha_ok, sha_ev))

    # 15b. wheel rename must stay PEP 427 (name-version-py3-none-any.whl) —
    # the provisioner validates wheel filenames and dies exit-1 with an
    # empty operation log otherwise (archivebox 2026-10-28)
    try:
        src = get(manifest, "resources.sources.main") or {}
        if str(src.get("url", "")).endswith(".whl"):
            ren = str(src.get("rename") or src.get("url", "").rsplit("/", 1)[-1])
            # distribution-version(-build)?-python-abi-platform => >=5 dash parts
            parts = ren[:-4].split("-") if ren.endswith(".whl") else []
            wheel_ok = len(parts) >= 5 and all(p for p in parts)
            wheel_ev = f"rename={ren}"
            checks.append(check("wheel-rename-pep427", wheel_ok, wheel_ev))
    except Exception as e:
        pass  # non-wheel packages: check does not apply

    # 16. apt deps with php (v2: packages is a comma STRING — split before iterating)
    apt_raw = get(manifest, "resources.apt.packages") or []
    if isinstance(apt_raw, str):
        apt = [p.strip() for p in apt_raw.split(",") if p.strip()]
    else:
        apt = list(apt_raw)
    php = any("php" in str(p) for p in apt)
    # class-aware + core-verified (YNH 12.1 utils/resources.py): the database
    # resource provisions db/user ONLY — it never installs the DB server.
    # mariadb-server is a yunohost core dependency (every box has it; apt pin
    # redundant-but-tolerated), but postgresql is NOT — a postgres app that
    # doesn't apt-pin the server dies at provision on a stock box (works only
    # where another app already installed PG; gitea iteration-6 slipped through
    # exactly that way on a PG-carrying box).
    db_res = get(manifest, "resources.database")
    db_type = str(get(db_res, "type") or "") if db_res else ""
    pg_in_apt = any(re.fullmatch(r"postgresql(-\d+)?", str(p)) for p in apt)
    if php:
        apt_ok, apt_ev = bool(apt), f"php app; apt={apt}"
    elif db_res and "postgresql" in db_type:
        apt_ok = pg_in_apt
        apt_ev = (f"postgres app; server apt-pinned={pg_in_apt}" if pg_in_apt
                  else f"postgres db resource but server NOT in apt ({apt}) — resource provisions db/user only; install dies on a PG-less box")
    else:
        apt_ok, apt_ev = True, f"non-php class; apt={apt}"
    checks.append(check("apt-deps-appropriate", apt_ok, apt_ev))

    # 17. PII scan (generic defaults; operator patterns via --pii)
    # IP patterns are exempted inside i18n doc strings (help.*/ask.*/comment
    # lines of TOML): RFC1918 EXAMPLE addresses in user-facing help text
    # (e.g. an IGNORE_IP format example) are documentation, not leaked box
    # state. Real PII is IPs/domains/emails in scripts, conf, manifest keys.
    pii_hits = []
    for root, dirs, files in os.walk(pkg):
        if ".git" in root:
            continue
        for f in files:
            p = os.path.join(root, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            if p.endswith((".toml",)):
                # drop help./ask. i18n value lines and # comments before matching
                txt = "\n".join(
                    ln for ln in txt.splitlines()
                    if not re.match(r"\s*(help|ask)\.[a-z]{2,3}\s*=", ln)
                    and not ln.lstrip().startswith("#")
                )
            for pat in PII_PATTERNS:
                if re.search(pat, txt, re.I):
                    pii_hits.append(f"{os.path.relpath(p, pkg)}: {pat}")
    checks.append(check("pii-clean", not pii_hits, f"hits={pii_hits}" if pii_hits else "no personal-info matches"))

    # 18. informational: no git remotes (benchmark runs are local-only)
    r = sh(["git", "remote", "-v"], cwd=pkg)
    checks.append(check("no-git-remotes", r.stdout.strip() == "", r.stdout.strip() or "no remotes",
                        informational=True))

    # 19. multi-instance declaration (v2: integration.multi_instance)
    # true passes; false passes ONLY with a stated reason (comment on the
    # manifest key, or a single/multi-instance note in doc/ADMIN.md or README)
    # — decision rule: references/quality-gates.md §Multi-instance
    mi = get(manifest, "integration.multi_instance")
    if mi is True:
        checks.append(check("multi-instance-declared", True, "integration.multi_instance=true"))
    else:
        reason = False
        try:
            with open(os.path.join(pkg, "manifest.toml")) as f:
                mlines = f.read().splitlines()
            for i, ln in enumerate(mlines):
                if "multi_instance" in ln:
                    if "#" in ln or (i and "#" in mlines[i - 1]):
                        reason = True
        except OSError:
            pass
        for doc in ("doc/ADMIN.md", "README.md"):
            try:
                with open(os.path.join(pkg, doc)) as f:
                    if re.search(r"(single|multi)[- ]instance", f.read(), re.I):
                        reason = True
            except OSError:
                pass
        if mi is False:
            checks.append(check("multi-instance-declared", reason,
                                "false WITH stated reason" if reason else
                                "multi_instance=false WITHOUT stated reason — add a comment on the manifest key or a single-instance note in doc/ADMIN.md (quality-gates.md §Multi-instance)"))
        else:
            checks.append(check("multi-instance-declared", False,
                                f"integration.multi_instance={mi} — must be true, or false with a stated reason"))

    # 20. nginx conf wires PHP-FPM
    ng = ""
    for root, _, files in os.walk(pkg):
        if ".git" in root:
            continue
        for f in files:
            if "nginx" in f.lower():
                try:
                    ng += open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
                except Exception:
                    pass
    # class-aware wiring: php apps fastcgi; proxy/daemon apps (go/node/python
    # sockets) need proxy_pass — the landing-style php regex 404s an entire
    # class of correct packages
    has_fastcgi = bool(re.search(r"fastcgi", ng, re.I))
    has_proxy = bool(re.search(r"proxy_pass", ng))
    if has_fastcgi or re.search(r"php", ng, re.I):
        wired = has_fastcgi or has_proxy
        ev = f"php-style; fastcgi={has_fastcgi} proxy={has_proxy}"
    else:
        wired = has_proxy
        ev = f"proxy-style; proxy_pass={has_proxy}"
    checks.append(check("nginx-conf-wires-app", bool(ng) and wired,
                        f"nginx conf found={bool(ng)}; {ev}"))

    return checks, manifest

if __name__ == "__main__":
    if not PKG or not os.path.isdir(PKG):
        sys.exit("usage: grade_static.py <package_dir> [--expect-version X] [--no-network] [--pii REGEX]")
    checks, manifest = grade(PKG)
    scored = [c for c in checks if not c["informational"]]
    passed = sum(1 for c in scored if c["passed"])
    out = {
        "package_dir": PKG,
        "manifest_id": (manifest or {}).get("id"),
        "manifest_version": (manifest or {}).get("version"),
        "checks_passed": passed,
        "checks_total": len(scored),
        "checks": checks,
    }
    print(json.dumps(out, indent=2))
