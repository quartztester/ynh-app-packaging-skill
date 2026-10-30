#!/bin/sh
# PII gate wrapper: feeds regex patterns from an EXTERNAL file (never stored
# in this repo — see verify_skill_integrity.py's docstring) to the skill
# integrity check. Run this before EVERY push of the skill repo.
#
# Pattern file: $PII_PATTERNS_FILE or /root/.pii_patterns (one regex per
# line; blank lines and #-comments skipped; file kept mode 600).
set -eu
DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PATTERNS_FILE=${PII_PATTERNS_FILE:-/root/.pii_patterns}
if [ ! -r "$PATTERNS_FILE" ]; then
    echo "pii_gate: pattern file $PATTERNS_FILE missing or unreadable" >&2
    exit 2
fi
set --
while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in '#'*) continue ;; esac
    set -- "$@" --pii "$p"
done < "$PATTERNS_FILE"
if [ "$#" -eq 0 ]; then
    echo "pii_gate: pattern file has no patterns" >&2
    exit 2
fi
exec python3 "$DIR/scripts/verify_skill_integrity.py" "$DIR" "$@"
