#!/usr/bin/env python3
from collections import Counter
"""Round-4 aggregate over 50 apps (corpus -> 99) + scale probes."""
import os, tomllib, statistics, json, re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data4")
sel = json.load(open("round4_selection.json"))
APPS = [a for a, _, _ in sel]

STANDARD = {"domain", "path", "user", "group", "admin", "admin_pass", "password",
            "init_main_permission", "init_admin_permission", "is_public", "language"}

qc, ids, types_seen = [], {}, set()
std_ask_nonempty, custom_total, custom_no_default, custom_no_fr, optional_any = 0, 0, 0, 0, 0
path_omitted, is_public_legacy, ask_pw, ask_admin = 0, [], 0, 0
fmt = {}
sso_flags = {"sso_true": 0, "sso_false": 0}
pw_vs_sso = {"pw_and_sso_possible": 0, "pw_and_sso_impossible": 0}
parsed = []
for app in APPS:
    try:
        m = tomllib.load(open(os.path.join(BASE, app, "manifest.toml"), "rb"))
    except Exception as e:
        print(f"!! {app} parse fail: {e}"); continue
    parsed.append(app)
    fmt[m.get("packaging_format")] = fmt.get(m.get("packaging_format"), 0) + 1
    integ = m.get("integration", {})
    sso = integ.get("sso")
    if sso is True: sso_flags["sso_true"] += 1
    elif sso is False: sso_flags["sso_false"] += 1
    args = m.get("install", {})
    qc.append(len(args))
    if "path" not in args: path_omitted += 1
    has_pw = has_admin = False
    for k, v in args.items():
        ids[k] = ids.get(k, 0) + 1
        t = v.get("type", "string")
        types_seen.add(t)
        if t == "password" or k in ("password", "admin_pass"): has_pw = True
        if k == "admin" or k == "init_admin_permission": has_admin = True
        ask = v.get("ask", {})
        en = ask.get("en", "") if isinstance(ask, dict) else ""
        if k in {"domain", "path", "init_main_permission", "init_admin_permission", "admin", "is_public"} and en:
            std_ask_nonempty += 1
        if k not in STANDARD:
            custom_total += 1
            if "default" not in v and not v.get("optional"): custom_no_default += 1
            if isinstance(ask, dict) and "en" in ask and "fr" not in ask: custom_no_fr += 1
        if v.get("optional"): optional_any += 1
        if k == "is_public": is_public_legacy.append(app)
    if has_pw:
        ask_pw += 1
        if sso is True: pw_vs_sso["pw_and_sso_possible"] += 1
        else: pw_vs_sso["pw_and_sso_impossible"] += 1
    if has_admin: ask_admin += 1

print(f"parsed={len(parsed)}/50 | questions: median={statistics.median(qc)} mean={statistics.mean(qc):.1f} range={min(qc)}-{max(qc)}")
print("histogram:", dict(sorted(Counter(qc).items())))
print("most:", sorted(zip(qc, APPS), reverse=True)[:4])
print(f"path omitted: {path_omitted}/50 | is_public: {is_public_legacy or 'NONE'} | ask admin: {ask_admin} | ask password: {ask_pw}")
print(f"sso flags: {sso_flags} | pw-asking apps where sso=true: {pw_vs_sso['pw_and_sso_possible']}, sso!=true: {pw_vs_sso['pw_and_sso_impossible']}")
print(f"std ask non-empty: {std_ask_nonempty} | customs: {custom_total} no-default: {custom_no_default} no-fr: {custom_no_fr} | optional: {optional_any}")
print(f"packaging_format: {fmt}")
print("ids:", sorted(ids.items(), key=lambda x: -x[1])[:14])
print("types:", sorted(types_seen))
print()
print("== panels:")
panel_apps = [a for a in APPS if os.path.exists(os.path.join(BASE, a, "config_panel.toml"))]
print(f"present: {len(panel_apps)}/50")
for app in panel_apps:
    t = tomllib.load(open(os.path.join(BASE, app, "config_panel.toml"), "rb"))
    nopts = nbind = nbtn = nvis = 0; secs = []
    for sec_name, sec in t.items():
        if not isinstance(sec, dict): continue
        for sub_name, sub in sec.items():
            if not isinstance(sub, dict): continue
            opts = {k: v for k, v in sub.items() if isinstance(v, dict) and "type" in v}
            if not opts: continue
            secs.append(sub_name); nopts += len(opts)
            nbind += sum(1 for v in opts.values() if "bind" in v)
            nbtn += sum(1 for v in opts.values() if v["type"] == "button")
            nvis += sum(1 for v in opts.values() if "visible" in v)
    print(f"  {app:20s} secs={secs} opts={nopts} bind={nbind} btn={nbtn} vis={nvis}")
print()
adminlens = []
for app in APPS:
    p = os.path.join(BASE, app, "doc_ADMIN.md")
    if os.path.exists(p):
        adminlens.append((sum(1 for _ in open(p)), app))
adminlens.sort()
if adminlens:
    vals = [l for l, _ in adminlens]
    print(f"ADMIN.md present: {len(adminlens)}/50 | lines min={vals[0]} p25={statistics.quantiles(vals, n=4)[0]} median={statistics.median(vals)} p75={statistics.quantiles(vals, n=4)[2]} max={vals[-1]}")
    print("longest:", adminlens[-4:])
pre = sum(1 for a in APPS if os.path.exists(os.path.join(BASE, a, "doc_PRE_INSTALL.md")))
post = sum(1 for a in APPS if os.path.exists(os.path.join(BASE, a, "doc_POST_INSTALL.md")))
rdfr = sum(1 for a in APPS if os.path.exists(os.path.join(BASE, a, "README_fr.md")))
desc = sum(1 for a in APPS if os.path.exists(os.path.join(BASE, a, "DESCRIPTION.md")))
print(f"PRE_INSTALL: {pre}/50 | POST_INSTALL: {post}/50 | README_fr: {rdfr}/50 | DESCRIPTION.md: {desc}/50")
