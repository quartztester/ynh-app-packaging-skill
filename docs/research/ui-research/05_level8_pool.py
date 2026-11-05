#!/usr/bin/env python3
"""List all catalog level-8 apps, excluding the already-studied 9."""
import urllib.request, tomllib

STUDIED = {"nextcloud", "roundcube", "jellyfin", "syncthing", "searxng",
           "rustdesk-server", "stirling-pdf", "forgejo", "joplin"}

raw = urllib.request.urlopen("https://raw.githubusercontent.com/YunoHost/apps/master/apps.toml", timeout=60).read().decode()
c = tomllib.loads(raw)
rows = []
for app, d in c.items():
    if d.get("level") == 8 and app not in STUDIED:
        rows.append((app, d.get("category", "?"), ",".join(d.get("subtags", [])[:3])))
rows.sort()
print(f"total level-8 not yet studied: {len(rows)}")
for a, cat, sub in rows:
    print(f"{a:28s} {cat:22s} {sub}")
