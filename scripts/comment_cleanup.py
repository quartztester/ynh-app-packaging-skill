#!/usr/bin/env python3
"""comment cleanup check (rule 7b) — flag comment-heavy package files.

Usage: comment_cleanup.py <repo> [<repo>...]
Exit 1 if any file is flagged. Flags:
  - comment density > 15% of file lines (min 10 comment lines), or
  - any consecutive comment run >= 6 lines
Vendored upstream files are exempt (rule 7b: never trim them) — maintained
as VENDORED globs below; extend per-repo as discovered.
"""
import fnmatch, os, re, sys

CEILING = 0.15
MIN_LINES = 10
MAX_RUN = 6
VENDORED = ["conf/nova3/*", "conf/nova3/**", "*nova2dl.py", "*novaprinter.py",
            "conf/webui/templates/*", "conf/redis.conf"]

SCAN_DIRS = ("conf", "scripts")
SCAN_FILES = ("manifest.toml", "tests.toml", "config_panel.toml")
COMMENT = re.compile(r"^\s*#(?!#!)")
# Standard YunoHost template furniture, mandated by repo-hygiene's banner
# rule — exempt from the density/run budget so the two rules agree:
#   - banner rule lines:  #============...====#
#   - ALL-CAPS section titles inside banner blocks (short, no lowercase)
BANNER_RULE = re.compile(r"^\s*#=+\s*$")
ALL_CAPS_TITLE = re.compile(r"^\s*#\s*[A-Z0-9][A-Z0-9 \-/&.]{2,70}\s*$")

def is_exempt_comment(l):
    return bool(BANNER_RULE.match(l) or ALL_CAPS_TITLE.match(l))

def scan(path, rel):
    lines = open(path, encoding="utf-8", errors="replace").readlines()
    total = run = best = comments = 0
    for l in lines:
        if COMMENT.match(l):
            if is_exempt_comment(l):
                pass  # banner furniture: not prose, not counted, run-neutral
            else:
                comments += 1; run += 1; best = max(best, run)
        elif l.strip() == "":
            pass  # blank keeps a block visually together but not counted
        else:
            run = 0
        total += 1
    dens = comments / max(total, 1)
    reasons = []
    if comments >= MIN_LINES and dens > CEILING:
        reasons.append(f"density {dens:.0%} > {CEILING:.0%}")
    if best >= MAX_RUN:
        reasons.append(f"longest run {best} >= {MAX_RUN}")
    return reasons, comments, total

def check_repo(repo):
    repo = repo.rstrip("/")
    flagged = []
    targets = [os.path.join(repo, f) for f in SCAN_FILES if os.path.exists(os.path.join(repo, f))]
    for d in SCAN_DIRS:
        base = os.path.join(repo, d)
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            targets += [os.path.join(root, f) for f in files]
    for p in sorted(targets):
        rel = os.path.relpath(p, repo)
        if any(fnmatch.fnmatch(rel, v) or fnmatch.fnmatch(os.path.basename(rel), v) for v in VENDORED):
            continue
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        try:
            reasons, c, n = scan(p, rel)
        except (OSError, UnicodeDecodeError):
            continue
        if reasons:
            flagged.append((rel, "; ".join(reasons), c, n))
    return flagged

def main():
    all_flagged = 0
    for repo in sys.argv[1:]:
        flagged = check_repo(repo)
        name = os.path.basename(repo.rstrip("/"))
        if flagged:
            print(f"{name}: {len(flagged)} file(s) over comment budget")
            for rel, why, c, n in flagged:
                print(f"  {rel:44s} {c:3d}/{n:3d} comment lines — {why}")
            all_flagged += len(flagged)
        else:
            print(f"{name}: clean")
    if all_flagged:
        print(f"COMMENT CLEANUP: {all_flagged} file(s) need compression (why-only one-liners, rule 7b)")
        sys.exit(1)
    print("COMMENT CLEANUP: all repos within budget")

if __name__ == "__main__":
    main()
