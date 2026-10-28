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
DEFAULT_PII = [r"\b10\.", r"\b192\.168\.", r"\b172\.(1[6-9]|2[0-9]|3[01])\."]
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

    # 4. id valid
    app_id = manifest.get("id", "")
    checks.append(check("app-id-valid", bool(re.fullmatch(r"[a-z0-9_]+", app_id or "")), f"id={app_id!r}"))

    # 5. version format (+ expected upstream release if given)
    ver = str(manifest.get("version", ""))
    checks.append(check("version-ynh-format", bool(re.fullmatch(r"[\w.+-]+~ynh\d+", ver)), f"version={ver!r}"))
    if EXPECT_VER:
        checks.append(check("version-matches-expected-upstream", ver.startswith(EXPECT_VER),
                            f"version={ver!r} expected prefix {EXPECT_VER}"))

    # 6. bash -n every script
    sdir = os.path.join(pkg, "scripts")
    scripts = sorted(os.listdir(sdir)) if os.path.isdir(sdir) else []
    bad = []
    for s in scripts:
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
    used, halluc = set(), set()
    for s in scripts:
        txt = open(os.path.join(sdir, s), encoding="utf-8", errors="ignore").read()
        for call in re.findall(r"\b(ynh_[a-z0-9_]+)\b", txt):
            used.add(call)
            if defined and call not in defined:
                halluc.add(call)
    checks.append(check("no-hallucinated-helpers", not halluc,
                        f"hallucinated={sorted(halluc)}" if halluc
                        else f"all {len(used)} distinct ynh_* calls defined in {HELPERS_DIR}"))

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
                tomllib.load(f)
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
            if f.lower().endswith(".png") and re.search(r"logo|icon", f, re.I):
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
        for f in files:
            if "screenshot" in f.lower():
                shots.append(os.path.relpath(os.path.join(root, f), pkg))
    checks.append(check("screenshots-present", bool(shots), f"{shots}", informational=True))

    # 15. source sha256 verified by download
    sha_ok, sha_ev = False, "no source"
    try:
        src = get(manifest, "resources.sources.main") or {}
        url, declared = src.get("url"), str(src.get("sha256", ""))
        if url and declared:
            if NO_NET:
                sha_ok, sha_ev = None, "skipped (no-network)"
            else:
                with tempfile.NamedTemporaryFile(delete=True) as tf:
                    urllib.request.urlretrieve(url, tf.name)
                    actual = hashlib.sha256(open(tf.name, "rb").read()).hexdigest()
                sha_ok = actual == declared
                sha_ev = f"declared={declared[:12]} actual={actual[:12]}"
    except Exception as e:
        sha_ev = f"error: {e}"
    checks.append(check("source-sha256-correct", sha_ok, sha_ev))

    # 16. apt deps with php (v2: packages is a comma STRING — split before iterating)
    apt_raw = get(manifest, "resources.apt.packages") or []
    if isinstance(apt_raw, str):
        apt = [p.strip() for p in apt_raw.split(",") if p.strip()]
    else:
        apt = list(apt_raw)
    php = any("php" in str(p) for p in apt)
    checks.append(check("apt-deps-with-php", bool(apt) and php, f"apt={apt}"))

    # 17. PII scan (generic defaults; operator patterns via --pii)
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
            for pat in PII_PATTERNS:
                if re.search(pat, txt, re.I):
                    pii_hits.append(f"{os.path.relpath(p, pkg)}: {pat}")
    checks.append(check("pii-clean", not pii_hits, f"hits={pii_hits}" if pii_hits else "no personal-info matches"))

    # 18. informational: no git remotes (benchmark runs are local-only)
    r = sh(["git", "remote", "-v"], cwd=pkg)
    checks.append(check("no-git-remotes", r.stdout.strip() == "", r.stdout.strip() or "no remotes",
                        informational=True))

    # 19. multi-instance declaration (v2: integration.multi_instance)
    mi = get(manifest, "integration.multi_instance")
    checks.append(check("multi-instance-declared", mi is True, f"integration.multi_instance={mi}"))

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
    checks.append(check("nginx-conf-references-php", bool(re.search(r"fastcgi|php", ng, re.I)),
                        f"nginx conf found={bool(ng)}; php ref={bool(re.search('fastcgi|php', ng, re.I))}"))

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
