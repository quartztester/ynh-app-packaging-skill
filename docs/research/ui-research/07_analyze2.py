#!/usr/bin/env python3
"""Round-2 aggregate: same stats as round 1 + bind/optional/exotic/doc probes."""
import os, tomllib, statistics

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data2")
APPS = ["archivebox", "libretranslate", "peertube", "mastodon", "etherpad",
        "freshrss", "paperless-ngx", "homeassistant", "uptime-kuma", "bookstack"]

qcount, all_ids, types_seen = [], {}, set()
opt_no_default = 0
for app in APPS:
    m = tomllib.load(open(os.path.join(BASE, app, "manifest.toml"), "rb"))
    args = m.get("install", {})
    ids = list(args.keys())
    qcount.append(len(ids))
    for k, v in args.items():
        all_ids[k] = all_ids.get(k, 0) + 1
        types_seen.add(v.get("type", "?"))
        if v.get("optional") and "default" not in v:
            opt_no_default += 1
print("questions per app:", dict(zip(APPS, qcount)), "| median", statistics.median(qcount))
print("ids by freq:", sorted(all_ids.items(), key=lambda x: -x[1]))
print("types seen:", sorted(types_seen), "| optional-without-default:", opt_no_default)
print()
for app in ["archivebox", "mastodon", "peertube"]:
    m = tomllib.load(open(os.path.join(BASE, app, "manifest.toml"), "rb"))
    print(f"== {app} install questions detail:")
    for k, v in m["install"].items():
        ask = v.get("ask", {}).get("en", "")
        print(f"   {k}: type={v.get('type')} default={'default' in v} ask_len={len(ask)} optional={v.get('optional', False)}")
print()
for app in ["libretranslate", "paperless-ngx"]:
    t = tomllib.load(open(os.path.join(BASE, app, "config_panel.toml"), "rb"))
    print(f"== panel {app}:")
    nopts = 0
    for sec_name, sec in t.items():
        if sec_name == "version" or not isinstance(sec, dict): continue
        for sub_name, sub in (sec or {}).items():
            if not isinstance(sub, dict): continue
            opts = {k: v for k, v in sub.items() if isinstance(v, dict) and "type" in v}
            if not opts: continue
            nopts += len(opts)
            types = [v["type"] for v in opts.values()]
            binds = sum(1 for v in opts.values() if "bind" in v)
            btns = sum(1 for v in opts.values() if v["type"] == "button")
            vis = sum(1 for v in opts.values() if "visible" in v)
            print(f"   [main.{sub_name}] opts={len(opts)} types={types} bind={binds} btn={btns} visible={vis}")
    print(f"   TOTAL opts={nopts}")
print()
print("== doc_ADMIN.md line counts:")
for app in APPS:
    a = os.path.join(BASE, app, "doc_ADMIN.md")
    print(f"   {app:14s}", sum(1 for _ in open(a)) if os.path.exists(a) else "-")
