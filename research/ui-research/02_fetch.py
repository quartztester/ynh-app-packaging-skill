#!/usr/bin/env python3
"""Fetch manifest.toml / config_panel.toml / README+doc inventory for level-8 corpus."""
import urllib.request, os, sys

APPS = ["nextcloud", "roundcube", "jellyfin", "syncthing", "searxng",
        "rustdesk-server", "stirling-pdf", "forgejo", "joplin"]

BASE = os.path.dirname(os.path.abspath(__file__))

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return None

for app in APPS:
    d = os.path.join(BASE, "data", app)
    os.makedirs(d, exist_ok=True)
    for repo_try in [f"{app}_ynh"]:
        for branch in ["master", "main"]:
            root = f"https://raw.githubusercontent.com/YunoHost-Apps/{repo_try}/{branch}"
            ok = False
            for fname, out in [("manifest.toml", "manifest.toml"),
                                ("config_panel.toml", "config_panel.toml"),
                                ("README.md", "README.md"),
                                ("README_ADMIN.md", "README_ADMIN.md"),
                                ("doc/ADMIN.md", "doc_ADMIN.md")]:
                txt = fetch(f"{root}/{fname}")
                if txt is not None:
                    open(os.path.join(d, out), "w").write(txt)
                    ok = True
            if ok:
                print(f"{app:14s} <- {repo_try}@{branch}")
                break
        else:
            continue
        break
    else:
        print(f"{app:14s} FAILED")
