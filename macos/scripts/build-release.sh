#!/bin/bash

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
VERSION="$(/usr/bin/tr -d '[:space:]' < "$ROOT/VERSION")"
RELEASE_DIR="$ROOT/release"
ARCHIVE="$RELEASE_DIR/codex-bugfire-skin-v$VERSION.zip"
TMP="$(/usr/bin/mktemp -d /tmp/codex-dream-skin-release.XXXXXX)"
trap '/bin/rm -rf "$TMP"' EXIT

if [ "${1:-}" != "--skip-tests" ]; then "$ROOT/tests/run-tests.sh"; fi

/bin/mkdir -p "$TMP/codex-dream-skin-studio" "$RELEASE_DIR"
/usr/bin/rsync -a \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude 'release/' \
  "$ROOT/" "$TMP/codex-dream-skin-studio/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/skills/codex-bugfire-customizer"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$ROOT/../skills/codex-bugfire-customizer/" \
  "$TMP/codex-dream-skin-studio/skills/codex-bugfire-customizer/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/docs"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$ROOT/../docs/" \
  "$TMP/codex-dream-skin-studio/docs/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/contest/bugfire"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$ROOT/../contest/bugfire/" \
  "$TMP/codex-dream-skin-studio/contest/bugfire/"
for evidence in PROVENANCE.md SOURCES.md THIRD_PARTY_NOTICES.md ASSET_RIGHTS.csv; do
  /bin/cp "$ROOT/../$evidence" "$TMP/codex-dream-skin-studio/$evidence"
done
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/*.command
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/scripts/*.sh "$TMP/codex-dream-skin-studio"/tests/*.sh
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/skills/codex-bugfire-customizer/scripts/*.sh
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/contest/bugfire/*.sh
/bin/rm -f "$ARCHIVE"
/usr/bin/ditto -c -k --keepParent "$TMP/codex-dream-skin-studio" "$ARCHIVE"
SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE" | /usr/bin/awk '{print $1}')"
/usr/bin/printf '%s  %s\n' "$SHA256" "$(basename "$ARCHIVE")" > "$RELEASE_DIR/SHA256SUMS.txt"
/usr/bin/printf 'Created %s\nSHA-256 %s\n' "$ARCHIVE" "$SHA256"
