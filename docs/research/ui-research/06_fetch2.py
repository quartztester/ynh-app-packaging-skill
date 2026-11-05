#!/usr/bin/env python3
"""Fetch round-2 corpus (10 diverse level-8 apps incl. user's own examples)."""
import urllib.request, os

APPS = ["archivebox", "libretranslate", "peertube", "mastodon", "etherpad",
        "freshrss", "paperless-ngx", "homeassistant", "uptime-kuma", "bookstack"]

BASE = os.path.dirname(os.path.abspath(__file__))

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None

FILES = [("manifest.toml", "manifest.toml"), ("config_panel.toml", "config_panel.toml"),
         ("README.md", "README.md"), ("README_fr.md", "README_fr.md"),
         ("README_ADMIN.md", "README_ADMIN.md"), ("doc/ADMIN.md", "doc_ADMIN.md"),
         ("doc/PRE_INSTALL.md", "doc_PRE_INSTALL.md"), ("doc/POST_INSTALL.md", "doc_POST_INSTALL.md")]

for app in APPS:
    d = os.path.join(BASE, "data2", app)
    os.makedirs(d, exist_ok=True)
    got = []
    for branch in ["master", "main"]:
        root = f"https://raw.githubusercontent.com/YunoHost-Apps/{app}_ynh/{branch}"
        for fname, out in FILES:
            txt = fetch(f"{root}/{fname}")
            if txt is not None:
                open(os.path.join(d, out), "w").write(txt)
                got.append(out)
        if got:
            print(f"{app:14s} <- {branch}: {' '.join(got)}")
            break
    if not got:
        print(f"{app:14s} FAILED")
