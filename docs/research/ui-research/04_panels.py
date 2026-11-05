#!/usr/bin/env python3
"""Fixed panel parse (options under [main.<section>]) + verbatim samples."""
import os, tomllib, itertools

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

for app in ["forgejo", "nextcloud"]:
    t = tomllib.load(open(os.path.join(BASE, app, "config_panel.toml"), "rb"))
    print(f"== panel {app} ==")
    for sec_name, sec in t.items():
        if sec_name in ("version",): continue
        for sub_name, sub in (sec or {}).items():
            if not isinstance(sub, dict): continue
            opts = {k: v for k, v in sub.items() if isinstance(v, dict) and "type" in v}
            if not opts: continue
            types = [v["type"] for v in opts.values()]
            binds = sum(1 for v in opts.values() if "bind" in v)
            btns = [k for k, v in opts.items() if v["type"] == "button"]
            vis = sum(1 for v in opts.values() if "visible" in v)
            helped = sum(1 for v in opts.values() if "help" in v)
            askless = sum(1 for v in opts.values() if not v.get("ask"))
            print(f"  [main.{sub_name}] opts={len(opts)} types={types} bind={binds} buttons={len(btns)} visible={vis} help={helped} no-ask={askless}")

print("\n== verbatim: forgejo init_admin_permission + nextcloud user_home + rustdesk full install ==")
m = tomllib.load(open(os.path.join(BASE, "forgejo", "manifest.toml"), "rb"))
print("forgejo init_admin_permission:", m["install"]["init_admin_permission"])
m = tomllib.load(open(os.path.join(BASE, "nextcloud", "manifest.toml"), "rb"))
print("nextcloud user_home:", m["install"]["user_home"])
m = tomllib.load(open(os.path.join(BASE, "rustdesk-server", "manifest.toml"), "rb"))
print("rustdesk install:", m["install"])

print("\n== forgejo panel: one full section verbatim (first 30 lines) ==")
txt = open(os.path.join(BASE, "forgejo", "config_panel.toml")).read()
print(txt[:1800])
