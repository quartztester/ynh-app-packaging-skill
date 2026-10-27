#!/usr/bin/env python3
"""Skill self-check: reference integrity + optional PII scan.

1. Every references/<file>.md mentioned in any .md of the skill resolves on disk,
   both directions (mentioned-but-missing and on-disk-but-never-mentioned).
2. PII scan: regex patterns passed as --pii args, NEVER hardcoded — the skill
   files must not themselves contain the identifiers they guard against.

Usage:
  verify_skill_integrity.py <skill_dir> [--pii 'pattern1' --pii 'pattern2']
Exit code 1 on any finding; 0 + OK line when clean.
"""
import argparse
import glob
import os
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("skill_dir", help="root of the skill (dir containing SKILL.md)")
    ap.add_argument("--pii", action="append", default=[],
                    help="regex to flag; repeatable, e.g. --pii 'somename' --pii 'bad\\.domain'")
    args = ap.parse_args()

    problems = []
    files = sorted(glob.glob(os.path.join(args.skill_dir, "**", "*.md"), recursive=True))
    if not files:
        sys.exit(f"no .md files under {args.skill_dir}")

    mentioned = set()
    on_disk = {os.path.basename(p)
               for p in glob.glob(os.path.join(args.skill_dir, "references", "*.md"))}
    pii = re.compile("|".join(args.pii), re.I) if args.pii else None

    for f in files:
        rel = os.path.relpath(f, args.skill_dir)
        with open(f, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in re.finditer(r"references/([A-Za-z0-9_.-]+\.md)", text):
            mentioned.add(m.group(1))
        if pii:
            for i, line in enumerate(text.splitlines(), 1):
                if pii.search(line):
                    problems.append(f"PII {rel}:{i}: {line.strip()[:90]}")

    for name in sorted(mentioned - on_disk):
        problems.append(f"MISSING reference mentioned but not on disk: {name}")
    for name in sorted(on_disk - mentioned):
        problems.append(f"ORPHAN reference on disk but never mentioned: {name}")

    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"OK: {len(mentioned)} references resolve both ways, "
          f"{len(files)} md files scanned, {len(args.pii)} PII patterns clean")


if __name__ == "__main__":
    main()
