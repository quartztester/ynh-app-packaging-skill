#!/usr/bin/env python3
"""Polarity self-check for the skill's gates — run before every push.

Every gate must pass its own ground truth and fail a known deviant.
3.5.0 shipped a VENDORED regression that green runs missed because the
polarity fixtures lived only in /tmp; this file persists them.

Usage: python3 scripts/test_gates.py [example_ynh-dir]
Without example_ynh: comment_cleanup delta/absolute/vendored polarities.
With it: also verify_conformance MUST/STYLE polarities on live copies.
Exit 0 = all gates discriminate correctly."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent

TEMPLATE_INSTALL = "\n".join([
    "#!/bin/bash",
    "#=================================================",
    "# IMPORT GENERIC HELPERS",
    "#=================================================",
    "source _common.sh",
    "source /usr/share/yunohost/helpers",
    "",
    "# FIXME: template prose explaining the next block in detail",
    "# continues here because the template ships it",
    'ynh_script_progression "Installing..."',
    "",
    "#=================================================",
    "# END OF SCRIPT",
    "#=================================================",
    "",
])

WHYS = "\n".join([
    "# upstream hardcodes PORT so we template it",
    "# avoid chgrp: helper sets it",
    "# v2.1 has no final_path",
    "# sqlite needs the dir writable",
])

WALL = "\n".join("# " + l for l in [
    "This section handles the installation of the application on the",
    "target system. We start by provisioning the database because the",
    "app requires it to be present before the config files are rendered,",
    "and this is a common source of confusion for new packagers who",
    "expect the core to do it automatically, which it does not do here,",
    "so we do it ourselves instead of relying on any other mechanism",
    "that might exist in the platform, because that would be fragile",
    "and hard to debug in production environments later on.",
])

failures = []


def run(script, args):
    return subprocess.run([sys.executable, str(HERE / script)] + args,
                          capture_output=True, text=True)


def case(name, script, args, want):
    r = run(script, args)
    if r.returncode != want:
        failures.append(f"FAIL {name}: exit {r.returncode}, want {want}\n{r.stdout}")


def comment_polarities(td):
    tmpl = td / "tmpl"
    ok = td / "ok"
    wall = td / "wall"
    for d in (tmpl, ok, wall):
        (d / "scripts").mkdir(parents=True)
        (d / "scripts" / "install").write_text(TEMPLATE_INSTALL)
    (tmpl / "tests.toml").write_text("# template comment\n")
    (ok / "scripts" / "install").write_text(TEMPLATE_INSTALL + WHYS + "\n")
    (wall / "scripts" / "install").write_text(TEMPLATE_INSTALL + WALL + "\n")
    # 12 comment lines / 1 code: blocks on density if the VENDORED entry
    # is lost — proves the upstream-vendored conf exemption
    (ok / "conf").mkdir()
    (ok / "conf" / "redis.conf").write_text(
        "".join(f"# upstream line {i}\n" for i in range(12)) + "bind 127.0.0.1\n")

    case("template alone, delta clean", "comment_cleanup.py",
         ["--baseline", str(tmpl), str(tmpl)], 0)
    case("template + why-one-liners, delta clean", "comment_cleanup.py",
         ["--baseline", str(tmpl), str(ok)], 0)
    case("vendored conf exempt (12/13 comments)", "comment_cleanup.py",
         ["--baseline", str(tmpl), str(ok)], 0)
    case("prose wall added, delta blocks", "comment_cleanup.py",
         ["--baseline", str(tmpl), str(wall)], 1)
    case("prose wall, absolute blocks", "comment_cleanup.py",
         [str(wall)], 1)


def conformance_polarities(td, example_ynh):
    pristine = td / "ynh_pristine"
    styled = td / "ynh_styled"
    broken = td / "ynh_broken"
    for dest in (pristine, styled, broken):
        shutil.copytree(example_ynh, dest,
                        ignore=shutil.ignore_patterns(".git"))
    # cosmetic-only deviation: lowercase banner title (STYLE) + first-banner
    # mismatch — must stay advisory
    s = (styled / "scripts" / "install").read_text()
    (styled / "scripts" / "install").write_text(
        s.replace("# IMPORT GENERIC HELPERS", "# import generic helpers", 1))
    # MUST deviation: required file missing
    (broken / "README_fr.md").unlink()

    case("example_ynh conforms", "verify_conformance.py", [str(pristine)], 0)
    case("STYLE-only deviant still passes", "verify_conformance.py", [str(styled)], 0)
    case("MUST deviant (missing README_fr) fails", "verify_conformance.py",
         [str(broken)], 1)


def main():
    example_ynh = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        comment_polarities(td)
        if example_ynh:
            conformance_polarities(td, example_ynh)
        else:
            print("SKIP verify_conformance polarities (no example_ynh dir given)")
    if failures:
        print("\n".join(failures))
        print(f"POLARITY: {len(failures)} case(s) broken")
        return 1
    print("POLARITY: all cases discriminate correctly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
