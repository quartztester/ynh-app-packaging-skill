#!/usr/bin/env python3
"""Aggregate install-question + panel + doc patterns across level-8 corpus."""
import os, re, tomllib, statistics

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
APPS = ["nextcloud", "roundcube", "jellyfin", "syncthing", "searxng",
        "rustdesk-server", "stirling-pdf", "forgejo", "joplin"]

qcount, all_ids, qtypes = [], {}, {}
opt_style = []
for app in APPS:
    d = os.path.join(BASE, app)
    m = tomllib.load(open(os.path.join(d, "manifest.toml"), "rb"))
    args = m.get("install", {})
    ids = list(args.keys())
    qcount.append(len(ids))
    for k, v in args.items():
        all_ids[k] = all_ids.get(k, 0) + 1
        qtypes.setdefault(k, v.get("type", "?"))
        opt_style.append((app, k, v.get("type", "?"), bool(v.get("optional", False)),
                          ("default" in v), bool(v.get("help")), len(v.get("ask", {}).get("en", ""))))
print("== questions per app:", dict(zip(APPS, qcount)), "| median", statistics.median(qcount))
print("== ids by frequency:", sorted(all_ids.items(), key=lambda x: -x[1]))
print("== types:", qtypes)
print("== per-question style (app, id, type, optional, has-default, has-help, ask-len):")
for row in opt_style:
    print("  ", row)

print()
for app in ["forgejo", "nextcloud"]:
    p = os.path.join(BASE, app, "config_panel.toml")
    t = tomllib.load(open(p, "rb"))
    print(f"== panel {app}:")
    for sk, sv in t.items():
        if not isinstance(sv, dict): continue
        opts = [k for k in sv if isinstance(sv[k], dict) and "type" in sv[k]]
        types = [sv[k]["type"] for k in opts]
        binds = sum(1 for k in opts if "bind" in sv[k])
        btns = [k for k in opts if sv[k]["type"] == "button"]
        vis = sum(1 for k in opts if "visible" in sv[k])
        helpn = sum(1 for k in opts if "help" in sv[k])
        print(f"   [{sk}] opts={len(opts)} types={types} binds={binds} buttons={len(btns)} visible={vis} helped={helpn}")

print()
print("== docs inventory (doc_ADMIN.md lines / README first line):")
for app in APPS:
    d = os.path.join(BASE, app)
    a = os.path.join(d, "doc_ADMIN.md")
    r = os.path.join(d, "README.md")
    al = sum(1 for _ in open(a)) if os.path.exists(a) else "-"
    r1 = open(r).readline().strip() if os.path.exists(r) else "-"
    print(f"   {app:14s} ADMIN.md lines={al}  README: {r1[:60]}")
