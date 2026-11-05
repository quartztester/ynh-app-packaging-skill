#!/usr/bin/env python3
"""Fetch YunoHost apps.json catalog, report level+repo for the study list."""
import json, urllib.request, sys

APPS = ["nextcloud", "vaultwarden", "my_webapp", "roundcube", "jellyfin", "syncthing",
        "wireguard_server", "searxng", "rustdesk-server", "immich", "stirling-pdf",
        "forgejo", "joplin", "loomio"]

url = "https://raw.githubusercontent.com/YunoHost/apps/master/apps.toml"
with urllib.request.urlopen(url, timeout=60) as r:
    raw = r.read().decode()
try:
    import tomllib
    catalog = tomllib.loads(raw)
except ImportError:
    import toml
    catalog = toml.loads(raw)

for a in APPS:
    d = catalog.get(a)
    if not d:
        print(f"{a:16s} NOT-IN-CATALOG"); continue
    lvl = d.get("level")
    repo = d.get("git", {}).get("https_url", d.get("git", "")).replace("https://github.com/", "")
    branch = d.get("git", {}).get("branch", "master")
    print(f"{a:16s} level={lvl} branch={branch} repo={repo}")
