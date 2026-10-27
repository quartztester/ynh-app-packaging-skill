#!/usr/bin/env python3
"""example_ynh structural conformance verifier for *_ynh package repos.

Checks per repo: script file set + git modes; banner bytes (# + 49 '=');
banner title casing (ALL-CAPS ASCII); canonical heads (IMPORT GENERIC HELPERS
first banner; 'source _common.sh'; '../settings/scripts/_common.sh' + its
Keep-comment in backup/restore; config sources helpers only); END OF SCRIPT
trailer in the six lifecycle scripts; bash -n on every script; required
template files; every ynh_* helper called in scripts/ exists in the local
/usr/share/yunohost/helpers.v2.1.d (skipped with INFO on non-YunoHost hosts).

NOT covered — do manually: PNG/logo validity, PII sweep, package_linter.

Usage: verify_conformance.py <repo-dir> [<repo-dir> ...]
       An argument dir with no scripts/ or manifest.toml is scanned as a
       parent directory of repos.
Exit:  0 = all clean, 1 = issues found (printed per repo).
Ground truth = a fresh example_ynh clone; if upstream changes, update the
constants below from it, not from memory.
"""
import re
import subprocess
import sys
from pathlib import Path

BANNER = "#" + "=" * 49
KEEP = ("# Keep this path for calling _common.sh inside the execution's context "
        "of backup and restore scripts")
HELPERS_SRC = "source /usr/share/yunohost/helpers"
COMMON_SRC = "source _common.sh"
COMMON_BR_SRC = "source ../settings/scripts/_common.sh"
LIFECYCLE = ("install", "remove", "upgrade", "backup", "restore")
SIX = LIFECYCLE + ("change_url",)
TITLE_OK = re.compile(r"^#[ ]?[A-Z0-9][A-Z0-9 ,&'()/+.:\"~_-]*$")
INLINE_BANNER = re.compile(r"^#\s*=+ .+ =+\s*$")

REQUIRED_FILES = ("README.md", "README_fr.md", "LICENSE", "tests.toml",
                  "manifest.toml", ".gitignore",
                  "doc/DESCRIPTION.md", "doc/DESCRIPTION_fr.md")
INFO_FILES = ("doc/ADMIN.md", "doc/ADMIN_fr.md", "conf", ".github/ISSUE_TEMPLATE.md")


def is_banner(line):
    return line.startswith("#") and line != "#" and set(line[1:]) == {"="}


def parse(path):
    """-> (lines, titles, bad_banner_lines, inline_banners)."""
    lines = path.read_text(errors="replace").splitlines()
    bad_len, inline = [], []
    for n, ln in enumerate(lines, 1):
        if is_banner(ln):
            if len(ln) != 50:
                bad_len.append((n, len(ln)))
        elif INLINE_BANNER.match(ln):
            inline.append(n)
    titles = []
    i = 0
    while i < len(lines):
        # banner triples: open / title / close
        if is_banner(lines[i]) and i + 2 < len(lines) and is_banner(lines[i + 2]):
            titles.append((i + 2, lines[i + 1].strip()))
            i += 3
            continue
        i += 1
    return lines, titles, bad_len, inline


def available_helpers():
    """-> set of helper names defined in the local helpers.v2.1.d, or None."""
    hdir = Path("/usr/share/yunohost/helpers.v2.1.d")
    if not hdir.is_dir():
        return None
    names = set()
    for f in sorted(hdir.iterdir()):
        if f.is_file():
            names |= set(re.findall(r"^((?:_)?ynh_[a-z0-9_]+)\(\)",
                                    f.read_text(errors="replace"), re.M))
    return names


def audit(repo, helpers=None):
    issues, infos = [], []
    sdir = repo / "scripts"

    for name in LIFECYCLE + ("_common.sh",):
        if not (sdir / name).is_file():
            issues.append(f"scripts/{name} missing")
    for name in ("change_url", "config"):
        if not (sdir / name).is_file():
            infos.append(f"scripts/{name} absent (optional upstream)")
    for rel in REQUIRED_FILES:
        if not (repo / rel).exists():
            issues.append(f"{rel} missing")
    for rel in INFO_FILES:
        if not (repo / rel).exists():
            infos.append(f"{rel} absent")

    # script modes: git index when available, stat otherwise
    modes = {}
    if (repo / ".git").exists():
        out = subprocess.run(["git", "-C", str(repo), "ls-files", "-s", "scripts"],
                             capture_output=True, text=True).stdout
        for row in out.splitlines():
            meta, path = row.split("\t", 1)
            modes[path] = int(meta.split()[0], 8)

    def executable(rel):
        if rel in modes:
            return bool(modes[rel] & 0o111)
        return bool((repo / rel).stat().st_mode & 0o111)

    for name in LIFECYCLE:
        rel = f"scripts/{name}"
        if (repo / rel).is_file() and not executable(rel):
            issues.append(f"{rel} not executable (want 755)")
    for name in ("_common.sh", "change_url", "config"):
        rel = f"scripts/{name}"
        if (repo / rel).is_file() and executable(rel):
            issues.append(f"{rel} executable (want 644)")

    # functions defined inside this repo's own scripts are not hallucinations
    repo_defined = set()
    for script in sorted(sdir.glob("*")):
        if script.is_file() and not script.name.startswith("."):
            repo_defined |= set(re.findall(r"^((?:_)?ynh_[a-z0-9_]+)\(\)",
                                           script.read_text(errors="replace"), re.M))

    for script in sorted(sdir.glob("*")):
        if not script.is_file() or script.name.startswith("."):
            continue
        name = script.name
        lines, titles, bad_len, inline = parse(script)
        tvals = [t for _, t in titles]
        for n, ln in bad_len:
            issues.append(f"scripts/{name}:{n} banner length {ln} (want 50)")
        for n in inline:
            issues.append(f"scripts/{name}:{n} one-line '# ==== X ====' banner")
        for n, t in titles:
            if not TITLE_OK.match(t):
                issues.append(f"scripts/{name}:{n} title not ALL-CAPS ASCII: {t!r}")
        if lines and not lines[0].startswith("#!"):
            issues.append(f"scripts/{name} no shebang on line 1")

        head = "\n".join(lines[:15])
        if name in SIX:
            if not tvals or tvals[0] != "# IMPORT GENERIC HELPERS":
                issues.append(f"scripts/{name} first banner "
                              f"{tvals[0] if tvals else '(none)'!r},"
                              f" want IMPORT GENERIC HELPERS")
            if "# END OF SCRIPT" not in tvals:
                issues.append(f"scripts/{name} no END OF SCRIPT trailer")
        if name in ("install", "remove", "upgrade", "change_url"):
            if COMMON_SRC not in head:
                issues.append(f"scripts/{name} no 'source _common.sh' in head")
        if name in ("backup", "restore"):
            if COMMON_BR_SRC not in head:
                issues.append(f"scripts/{name} no '../settings/scripts/_common.sh' source")
            for i, ln in enumerate(lines):
                if ln.strip() == COMMON_BR_SRC:
                    if i == 0 or lines[i - 1].strip() != KEEP:
                        issues.append(f"scripts/{name}:{i + 1} "
                                      f"source lacks Keep-comment above")
                    break
        if name == "config":
            if HELPERS_SRC not in head:
                issues.append(f"scripts/{name} no helpers source in head")
            # source _common.sh in config is sanctioned when the apply path
            # needs shared logic (official catalog precedent: grav, nextcloud,
            # my_webapp all do it); only the ../settings/ path is wrong there.
            if COMMON_BR_SRC in head:
                issues.append(f"scripts/{name} must NOT source ../settings/_common.sh")
        elif name != "_common.sh" and HELPERS_SRC not in head:
            issues.append(f"scripts/{name} no helpers source in head")

        rc = subprocess.run(["bash", "-n", str(script)],
                            capture_output=True, text=True)
        if rc.returncode:
            err = rc.stderr.strip().splitlines()
            issues.append(f"scripts/{name} bash -n: {err[-1] if err else 'syntax error'}")

        if helpers is not None:
            called = set(re.findall(r"(?<![\w/.@=\"-])(ynh_[a-z0-9_]+)(?![\w.])",
                                    "\n".join(lines)))
            for h in sorted(called - helpers - repo_defined):
                issues.append(f"scripts/{name} calls unknown helper {h}()")
    return issues, infos


def main():
    roots = [Path(a) for a in sys.argv[1:]] or [Path.cwd()]
    repos = []
    for root in roots:
        if (root / "scripts").is_dir() or (root / "manifest.toml").is_file():
            repos.append(root)
        elif root.is_dir():
            repos += [c for c in sorted(root.iterdir())
                      if c.is_dir() and (c / "scripts").is_dir()]
        else:
            print(f"skip {root}: not a dir", file=sys.stderr)
    bad = 0
    helpers = available_helpers()
    for repo in repos:
        issues, infos = audit(repo, helpers)
        for msg in infos:
            print(f"INFO  {repo.name}: {msg}")
        if issues:
            bad += 1
            print(f"FAIL  {repo.name} ({len(issues)} issues)")
            for msg in issues:
                print(f"  - {msg}")
        else:
            print(f"OK    {repo.name}")
    print(f"\n{len(repos) - bad}/{len(repos)} repos conformant")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
