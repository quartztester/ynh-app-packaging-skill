#!/usr/bin/env python3
"""comment cleanup check (rule 7b) — flag comment-heavy or narration-heavy files.

Usage: comment_cleanup.py <repo> [<repo>...]
Exit 1 if any file is flagged. Two layers, one blocking + one advisory (maintainer call: prose blocks
are accepted style, so only real walls block):

BLOCKING budget:
  - comment density > 15% of file lines (min 10 comment lines), or
  - any consecutive run >= 6 lines

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

CEILING = 0.15
MIN_LINES = 10
MAX_RUN = 6
PROSE_RUN = 3

VENDORED = ["conf/nova3/*", "conf/nova3/**", "*nova2dl.py", "*novaprinter.py",
            "conf/webui/templates/*", "conf/redis.conf",
            "conf/i2pd.conf", "conf/tunnels.conf", "scripts/contrib/*"]

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
    r"matches the API default|pence|units?|portrait|TODO|FIXME|FIXME|"
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

def scan(path):
    """Return (reasons, comment_count, total_lines)."""
    rx = syntax_for(path)
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if rx is None and ext not in HTML:
        return [], [], 0, 0  # unknown syntax: skip, never guess
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return [], [], 0, 0
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

def check_repo(repo):
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
        hard, advisory, c, n = scan(p)
        if hard or advisory:
            flagged.append((rel, "; ".join(dict.fromkeys(hard)),
                            "; ".join(dict.fromkeys(advisory)), c, n))
    return flagged

def main():
    blocked = 0
    for repo in sys.argv[1:]:
        flagged = check_repo(repo)
        name = os.path.basename(repo.rstrip("/"))
        hard_n = sum(1 for f in flagged if f[1])
        if flagged:
            print(f"{name}: {hard_n} blocking, {len(flagged) - hard_n} advisory")
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
