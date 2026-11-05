#!/usr/bin/env python3
"""Round-3: select 30 level-8 apps stratified by category (excluding 19 studied)."""
import urllib.request, tomllib, json

STUDIED = {"nextcloud", "roundcube", "jellyfin", "syncthing", "searxng",
           "rustdesk-server", "stirling-pdf", "forgejo", "joplin",
           "archivebox", "libretranslate", "peertube", "mastodon", "etherpad",
           "freshrss", "paperless-ngx", "homeassistant", "uptime-kuma", "bookstack"}

raw = urllib.request.urlopen("https://raw.githubusercontent.com/YunoHost/apps/master/apps.toml", timeout=60).read().decode()
c = tomllib.loads(raw)
by_cat = {}
for app, d in c.items():
    if d.get("level") == 8 and app not in STUDIED:
        url = d.get("url", "")
        if "github.com/YunoHost-Apps/" in url:  # raw-fetchable
            by_cat.setdefault(d.get("category", "?"), []).append((app, url))

# round-robin across categories (alphabetical), largest pools last
cats = sorted(by_cat, key=lambda k: len(by_cat[k]))
sel, i = [], 0
while len(sel) < 30:
    progressed = False
    for cat in cats:
        pool = by_cat[cat]
        if i < len(pool):
            sel.append((pool[i][0], pool[i][1], cat))
            progressed = True
            if len(sel) >= 30: break
    if not progressed: break
    i += 1

json.dump(sel, open("round3_selection.json", "w"), indent=1)
print(f"selected {len(sel)} apps across {len(set(s[2] for s in sel))} categories:")
for app, url, cat in sel:
    print(f"  {app:26s} {cat}")
