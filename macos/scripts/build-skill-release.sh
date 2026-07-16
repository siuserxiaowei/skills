#!/bin/bash

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
SKILL="$ROOT/skills/codex-bugfire-customizer"
RELEASE="$ROOT/release"
ARCHIVE="$RELEASE/codex-bugfire-customizer.skill.zip"
TMP="$(/usr/bin/mktemp -d /tmp/codex-bugfire-skill.XXXXXX)"
trap '/bin/rm -rf "$TMP"' EXIT

VALIDATOR="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
if [ -f "$VALIDATOR" ]; then
  /usr/bin/python3 "$VALIDATOR" "$SKILL"
else
  /usr/bin/grep -q '^name: codex-bugfire-customizer$' "$SKILL/SKILL.md"
  /usr/bin/grep -q '^description: ' "$SKILL/SKILL.md"
fi

/bin/mkdir -p "$TMP/codex-bugfire-customizer" "$RELEASE"
/usr/bin/rsync -a --exclude '.DS_Store' "$SKILL/" "$TMP/codex-bugfire-customizer/"
/bin/chmod 755 "$TMP/codex-bugfire-customizer/scripts/"*.sh
/bin/rm -f "$ARCHIVE"
COPYFILE_DISABLE=1 /usr/bin/ditto -c -k --keepParent --norsrc --noextattr \
  "$TMP/codex-bugfire-customizer" "$ARCHIVE"
SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE" | /usr/bin/awk '{print $1}')"
/usr/bin/printf '%s  %s\n' "$SHA256" "$(/usr/bin/basename "$ARCHIVE")" \
  > "$RELEASE/codex-bugfire-customizer.skill.zip.sha256"
/usr/bin/printf 'Created %s\nSHA-256 %s\n' "$ARCHIVE" "$SHA256"
