#!/usr/bin/env python3
"""comment cleanup check (rule 7b) — flag comment-heavy or narration-heavy files.

Usage: comment_cleanup.py [--baseline DIR] <repo> [<repo>...]
Exit 1 if any file is flagged. Two layers, one blocking + one advisory
(maintainer call: prose blocks are accepted style, so only real walls
block; standalone why-one-liners, however many in a row, never do):

DELTA MODE (--baseline, the default invocation for skill-built packages):
  point --baseline at a fresh example_ynh clone; the gate measures only
  comment lines the package ADDED or CHANGED vs that template. Fleet
  ground truth (454 level-8 repos, 2026-11): example_ynh itself carries
  ~50 comment lines per script (banners, template FIXME prose) and 64%
  of level-8 packages fail an absolute-15% budget — the template is the
  house style, not a violation. Without --baseline the absolute budget
  applies (joining/auditing an existing repo: keep its style).

BLOCKING budget (per measured set):
  - comment density > 15% of file lines (min 10 comment lines), or
  - a consecutive WRAPPED-PROSE run >= 6 lines (continuation lines
    lowercase or lines ending mid-sentence — a wall of narration)

ADVISORY gauntlet (reported, never exit 1; adapted from
https://gist.github.com/bavanws/123e0343f8a79cec825d9141124a0a83 —
comment earns its place only by carrying WHY):
  - prose run >= 3 lines (multi-line blocks almost never survive intact)
  - change narration ("fixed X", "updated to Y", "added per Z") — commit-msg
    content, not file content
  - moving-target pointers ("spec section 7", "see the design doc") —
    encode the substance instead; issue IDs and stable doc paths are fine

Keep categories (never flagged, per the gist): cross-file sync pointers
("keep in sync with X"), data-literal semantics, format contracts,
structural banners (#=== title ===), TODO/FIXME markers. Advisory
findings (prose runs 3-5, narration, moving targets) are signals for
the next touch of the file, not push blockers.

Comment syntax per file type: # (sh/toml/conf/env), -- (lua),
// (mjs/js/jsx), <!-- --> (html). Files whose syntax the scanner does
not know are skipped, never guessed.

Vendored upstream files are exempt (rule 7b: never trim them).
"""
import fnmatch, os, re, sys
from collections import Counter

CEILING = 0.15
MIN_LINES = 10
MAX_RUN = 6
PROSE_RUN = 3

# ponytail: name-based list kept minimal; generic dirs cover upstream code
VENDORED = ["sources/*", "sources/**", "scripts/contrib/*"]

SCAN_DIRS = ("conf", "scripts")
SCAN_FILES = ("manifest.toml", "tests.toml", "config_panel.toml")

# syntaxes: (line-comment regex, applies-to suffixes); html handled separately
SYNTAXES = [
    (re.compile(r"^\s*#(?!#!)"), ("", "sh", "toml", "conf", "env", "service", "ini", "py", "yml", "yaml", "nginx")),
    (re.compile(r"^\s*--(?!-)"), ("lua",)),
    (re.compile(r"^\s*//"), ("js", "mjs", "jsx", "ts")),
]
HTML = ("html", "htm")

# standard YunoHost template furniture (banner rule, repo-hygiene.md)
BANNER_RULE = re.compile(r"^\s*[#=+]+\s*$")
ALL_CAPS_TITLE = re.compile(r"^\s*#\s*[A-Z0-9][A-Z0-9 \-/&.]{2,70}\s*$")

# keep categories (gist): the link/convention itself is the why
KEEP = re.compile(
    r"keep in sync|same logic as|mirrors? the|must not clash|"
    r"matches the API default|units?|TODO|FIXME|"
    r"Keep this path for calling|this script is only run if actual change|"
    r"new location is available via")
# change narration addressed to a diff reviewer, not a file reader
CHANGE_NARRATION = re.compile(
    r"^(fixed|updated to|removed the|added per|as requested|"
    r"per feedback|changed to use|now uses)\b", re.I)
# moving-target references (issue IDs and stable paths are fine)
MOVING_TARGET = re.compile(
    r"(spec|requirements? doc|design doc)\s*(§|section)?\s*\d|\bsection \d+\.\d+\b", re.I)

def syntax_for(path):
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    for rx, exts in SYNTAXES:
        if ext in exts:
            return rx
    return None


def baseline_filter(baseline_lines, text):
    """Comment lines identical to a baseline (example_ynh) comment line are
    house style, not the package's own: return text minus one occurrence of
    each baseline comment line (multiset — position-independent, so a
    template comment that moved in a rearranged file still drops)."""
    if not baseline_lines:
        return text
    pool = Counter(l.strip() for l in baseline_lines
                   if l.strip().startswith("#"))
    kept = []
    for l in text:
        s = l.strip()
        if s.startswith("#") and pool.get(s):
            pool[s] -= 1
            continue
        kept.append(l)
    return kept


def scan(path, baseline=None):
    """Return (reasons, comment_count, total_lines)."""
    rx = syntax_for(path)
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if rx is None and ext not in HTML:
        return [], [], 0, 0  # unknown syntax: skip, never guess
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return [], [], 0, 0
    if baseline is not None:
        # delta mode: template furniture is exempt; total lines stay real
        lines = baseline_filter(baseline, lines)
    total = len(lines)
    comments, prose = 0, 0
    wrapped_runs, run, cur = [], 0, []
    def flush():
        if run >= PROSE_RUN:
            # wrapped-paragraph signature: a continuation line starting
            # lowercase, or a line ending mid-sentence (comma/hyphen)
            body = [l.strip().lstrip("#-/< !").strip() for l in cur]
            wrapped = any(b[:1].islower() for b in body[1:]) or \
                      any(b.rstrip().endswith((",", "-", ";")) for b in body[:-1])
            if wrapped:
                wrapped_runs.append(run)
    for l in lines:
        is_banner = BANNER_RULE.match(l) or ALL_CAPS_TITLE.match(l)
        if is_banner:
            continue            # banner furniture: not prose, run-neutral
        if l.strip() == "":
            continue            # blank keeps blocks together, run-neutral
        if (ext in HTML and ("<!--" in l or "-->" in l or l.strip().startswith("<"))) or (rx and rx.match(l)):
            comments += 1; run += 1; cur.append(l)
            if not KEEP.search(l):
                prose += 1
        else:
            flush(); run = 0; cur = []
    flush()
    # second pass: semantic flags on non-keep comment lines
    sem = []
    cl = [l for l in lines if (rx and rx.match(l) and not BANNER_RULE.match(l) and not ALL_CAPS_TITLE.match(l))]
    if ext in HTML:
        cl = [l.strip() for l in lines if l.strip().startswith("<!--")]
    for l in cl:
        if KEEP.search(l):
            continue
        if CHANGE_NARRATION.match(l.strip().lstrip("#-/< !")):
            sem.append("change narration"); break
    for l in cl:
        if KEEP.search(l):
            continue
        if MOVING_TARGET.search(l):
            sem.append("moving-target pointer"); break

    hard, advisory = [], []
    dens = prose / max(total, 1)
    if prose >= MIN_LINES and dens > CEILING:
        hard.append(f"density {dens:.0%} > {CEILING:.0%}")
    if wrapped_runs and max(wrapped_runs) >= MAX_RUN:
        hard.append(f"longest run {max(wrapped_runs)} >= {MAX_RUN}")
    elif wrapped_runs:
        # maintainer-accepted style: prose blocks are advisory, never blocking
        advisory.append(f"prose run {max(wrapped_runs)} >= {PROSE_RUN}")
    advisory += sem
    return hard, advisory, comments, total

def check_repo(repo, baseline=None):
    repo = repo.rstrip("/")
    targets = [os.path.join(repo, f) for f in SCAN_FILES if os.path.exists(os.path.join(repo, f))]
    for d in SCAN_DIRS:
        base = os.path.join(repo, d)
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            targets += [os.path.join(root, f) for f in files]
    flagged = []
    for p in sorted(targets):
        rel = os.path.relpath(p, repo)
        if any(fnmatch.fnmatch(rel, v) or fnmatch.fnmatch(os.path.basename(rel), v) for v in VENDORED):
            continue
        if os.path.islink(p) or not os.path.isfile(p):
            continue
        bl = baseline.get(rel) if baseline is not None else None
        hard, advisory, c, n = scan(p, bl)
        if hard or advisory:
            flagged.append((rel, "; ".join(dict.fromkeys(hard)),
                            "; ".join(dict.fromkeys(advisory)), c, n))
    return flagged

def load_baseline(root):
    """{relative path: [comment lines]} for files the scanner knows."""
    out = {}
    for d, _, files in os.walk(root):
        if ".git" in d.split(os.sep):
            continue
        for f in files:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            if syntax_for(p) is None and f.rsplit(".", 1)[-1].lower() not in HTML:
                continue
            try:
                out[rel] = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                pass
    return out

def main():
    args = sys.argv[1:]
    baseline = None
    if args and args[0] == "--baseline":
        if len(args) < 3:
            sys.exit("usage: comment_cleanup.py [--baseline example_ynh-dir] <repo>...")
        baseline = load_baseline(args[1])
        args = args[2:]
    if not args:
        sys.exit("usage: comment_cleanup.py [--baseline example_ynh-dir] <repo>...")
    blocked = 0
    for repo in args:
        flagged = check_repo(repo, baseline)
        name = os.path.basename(repo.rstrip("/"))
        hard_n = sum(1 for f in flagged if f[1])
        if flagged:
            mode = "delta" if baseline else "absolute"
            print(f"{name}: {hard_n} blocking, {len(flagged) - hard_n} advisory ({mode})")
            for rel, why, adv, c, n in flagged:
                tag = "BLOCK" if why else "advise"
                bits = " | ".join(b for b in (why, adv) if b)
                print(f"  [{tag}] {rel:44s} {c:3d}/{n:3d} comment lines — {bits}")
            blocked += hard_n
        else:
            print(f"{name}: clean")
    if blocked:
        print(f"COMMENT CLEANUP: {blocked} file(s) over budget (why-only one-liners, rule 7b)")
        sys.exit(1)
    print("COMMENT CLEANUP: all repos within budget (advisory notes above, if any)")

if __name__ == "__main__":
    main()
