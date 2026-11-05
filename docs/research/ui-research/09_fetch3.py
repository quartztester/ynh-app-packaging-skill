#!/usr/bin/env python3
"""Round-3: fetch manifests/panels/docs for the 30 selected apps (concurrent)."""
import json, os, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
sel = json.load(open("round3_selection.json"))

FILES = [("manifest.toml", "manifest.toml"), ("config_panel.toml", "config_panel.toml"),
         ("README.md", "README.md"), ("README_fr.md", "README_fr.md"),
         ("doc/ADMIN.md", "doc_ADMIN.md"), ("doc/PRE_INSTALL.md", "doc_PRE_INSTALL.md"),
         ("doc/POST_INSTALL.md", "doc_POST_INSTALL.md"), ("DESCRIPTION.md", "DESCRIPTION.md")]

def rawurl(repo, branch, fname):
    tail = repo.split("github.com/YunoHost-Apps/")[1].rstrip("/")
    return f"https://raw.githubusercontent.com/YunoHost-Apps/{tail}/{branch}/{fname}"

def fetch_one(args):
    app, repo = args
    d = os.path.join(BASE, "data3", app)
    os.makedirs(d, exist_ok=True)
    got, branch_used = [], None
    for branch in ["master", "main"]:
        ok = 0
        for fname, out in FILES:
            try:
                with urllib.request.urlopen(rawurl(repo, branch, fname), timeout=45) as r:
                    open(os.path.join(d, out), "w").write(r.read().decode("utf-8", "replace"))
                got.append(out); ok += 1
            except Exception:
                pass
        if ok:
            branch_used = branch
            break
    return app, branch_used, got

with ThreadPoolExecutor(max_workers=8) as ex:
    for app, branch, got in ex.map(fetch_one, [(a, u) for a, u, _ in sel]):
        status = " ".join(got) if got else "FAILED"
        print(f"{app:16s} {branch or '--'}: {status}")
