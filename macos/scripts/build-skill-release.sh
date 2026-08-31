#!/bin/bash

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
SKILL="$ROOT/skills/codex-bugfire-customizer"
ARCHIVE="${1:-$ROOT/release/codex-bugfire-customizer.skill.zip}"
RELEASE="$(/usr/bin/dirname "$ARCHIVE")"
TMP="$(/usr/bin/mktemp -d /tmp/codex-bugfire-skill.XXXXXX)"
trap '/bin/rm -rf "$TMP"' EXIT

STAGED_SKILL="$TMP/codex-bugfire-customizer"
/bin/mkdir -p "$STAGED_SKILL" "$RELEASE"
/usr/bin/rsync -a --exclude '.DS_Store' "$SKILL/" "$STAGED_SKILL/"
for evidence in LICENSE NOTICE.md PROVENANCE.md SOURCES.md THIRD_PARTY_NOTICES.md ASSET_RIGHTS.csv; do
  /bin/cp "$ROOT/$evidence" "$STAGED_SKILL/$evidence"
done

VALIDATOR="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
if [ -f "$VALIDATOR" ]; then
  /usr/bin/python3 "$VALIDATOR" "$STAGED_SKILL"
else
  /usr/bin/grep -q '^name: codex-bugfire-customizer$' "$STAGED_SKILL/SKILL.md"
  /usr/bin/grep -q '^description: ' "$STAGED_SKILL/SKILL.md"
fi

/bin/chmod 755 "$STAGED_SKILL/scripts/"*.sh
/bin/rm -f "$ARCHIVE"
COPYFILE_DISABLE=1 /usr/bin/ditto -c -k --keepParent --norsrc --noextattr \
  "$STAGED_SKILL" "$ARCHIVE"
SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE" | /usr/bin/awk '{print $1}')"
/usr/bin/printf '%s  %s\n' "$SHA256" "$(/usr/bin/basename "$ARCHIVE")" \
  > "$ARCHIVE.sha256"
/usr/bin/printf 'Created %s\nSHA-256 %s\n' "$ARCHIVE" "$SHA256"
