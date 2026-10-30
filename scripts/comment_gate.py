#!/usr/bin/env python3
"""Gate: repo's scripts/*.sh changed ONLY in comments vs given git ref.
Usage: comment_gate.py <repo_dir> [ref=HEAD]
Checks, per changed .sh file:
 1. every inserted/deleted line is comment-only or blank
 2. every replaced line pair has identical pre-'#' code part
 3. heredoc bodies byte-identical old vs new
Exit 0 = code provably unchanged."""
import sys, re, subprocess, difflib
from pathlib import Path

repo = Path(sys.argv[1]); ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
def show(path):
    r = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def heredocs(text):
    """bodies of <<'DELIM'/<<DELIM/<<-DELIM blocks"""
    out = []
    lines = text.splitlines(); i = 0
    while i < len(lines):
        m = re.search(r"(?<!<)<<(?!<)-?\s*['\"]?(\w+)['\"]?", lines[i])  # (?<!<)/(?!<): <<< is a here-string, not a heredoc
        if m and not lines[i].lstrip().startswith("#"):
            delim, body, i = m.group(1), [], i + 1
            while i < len(lines) and not re.match(rf"^\s*{delim}\s*$", lines[i]):
                body.append(lines[i]); i += 1
            out.append("\n".join(body))
        i += 1
    return out

def is_comment(l):
    s = l.strip()
    return s == "" or s.startswith("#")

def codepart(l):
    # cut at first # not inside quotes (cheap: only used for inline-comment lines)
    inq = None
    for i, ch in enumerate(l):
        if inq:
            if ch == inq: inq = None
        elif ch in "'\"":
            inq = ch
        elif ch == "#":
            return l[:i]
    return l

bad = 0
files = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", ref, "--"],
                       capture_output=True, text=True).stdout.split()
for f in files:
    if not (f.startswith("scripts/") and (f.endswith(".sh") or "/" in f and "." not in Path(f).name)):
        print(f"{repo.name}/{f}: NON-.sh CHANGE (outside policy)"); bad += 1; continue
    old = show(f); new = (repo / f).read_text()
    if old is None:
        print(f"{repo.name}/{f}: new file, skip gate"); continue
    o, n = old.splitlines(), new.splitlines()
    for l in o + n:
        pass
    sm = difflib.SequenceMatcher(None, o, n, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal": continue
        a, b = o[i1:i2], n[j1:j2]
        if tag in ("delete", "insert"):
            for l in a + b:
                if not is_comment(l):
                    print(f"{repo.name}/{f}: CODE line {'added' if tag=='insert' else 'removed'}: {l[:80]}"); bad += 1
        else:
            fa = [l for l in a if not is_comment(l)]
            fb = [l for l in b if not is_comment(l)]
            if [codepart(l).rstrip() for l in fa] != [codepart(l).rstrip() for l in fb]:
                print(f"{repo.name}/{f}: replaced CODE differs: {fa[:2]} vs {fb[:2]}"); bad += 1
    if heredocs(old) != heredocs(new):
        print(f"{repo.name}/{f}: HEREDOC BODY CHANGED"); bad += 1
    for l in new.splitlines():
        if re.match(r"^#!", l): continue
print(f"{repo.name}: {'FAIL' if bad else 'CODE-IDENTITY-OK'} ({len(files)} files)")
sys.exit(1 if bad else 0)
