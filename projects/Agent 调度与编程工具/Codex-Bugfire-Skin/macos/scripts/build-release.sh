#!/bin/bash

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
. "$SCRIPT_DIR/release-layout.sh"
ROOT="$BUGFIRE_ENGINE_ROOT"
PROJECT_ROOT="$BUGFIRE_PROJECT_ROOT"
VERSION="$(/usr/bin/tr -d '[:space:]' < "$ROOT/VERSION")"
SKIP_TESTS="false"
if [ "${1:-}" = "--skip-tests" ]; then SKIP_TESTS="true"; shift; fi
if [ "$#" -gt 1 ]; then
  /usr/bin/printf 'Usage: %s [--skip-tests] [output.zip]\n' "$0" >&2
  exit 1
fi
ARCHIVE="${1:-$ROOT/release/codex-bugfire-skin-v$VERSION.zip}"
RELEASE_DIR="$(/usr/bin/dirname "$ARCHIVE")"
TMP="$(/usr/bin/mktemp -d /tmp/codex-dream-skin-release.XXXXXX)"
trap '/bin/rm -rf "$TMP"' EXIT

if [ "$SKIP_TESTS" != "true" ]; then "$ROOT/tests/run-tests.sh"; fi

/bin/mkdir -p "$TMP/codex-dream-skin-studio" "$RELEASE_DIR"
/usr/bin/rsync -a \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude 'release/' \
  "$ROOT/" "$TMP/codex-dream-skin-studio/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/skills/codex-bugfire-customizer"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/skills/codex-bugfire-customizer/" \
  "$TMP/codex-dream-skin-studio/skills/codex-bugfire-customizer/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/docs"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/docs/" \
  "$TMP/codex-dream-skin-studio/docs/"
/bin/mkdir -p "$TMP/codex-dream-skin-studio/contest/bugfire"
/usr/bin/rsync -a \
  --exclude '.DS_Store' \
  "$PROJECT_ROOT/contest/bugfire/" \
  "$TMP/codex-dream-skin-studio/contest/bugfire/"
"$ROOT/scripts/prepare-package-layout.sh" "$TMP/codex-dream-skin-studio"
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/*.command
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/scripts/*.sh "$TMP/codex-dream-skin-studio"/tests/*.sh
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/skills/codex-bugfire-customizer/scripts/*.sh
/bin/chmod 755 "$TMP/codex-dream-skin-studio"/contest/bugfire/*.sh
/bin/rm -f "$ARCHIVE"
/usr/bin/ditto -c -k --keepParent "$TMP/codex-dream-skin-studio" "$ARCHIVE"
SHA256="$(/usr/bin/shasum -a 256 "$ARCHIVE" | /usr/bin/awk '{print $1}')"
/usr/bin/printf '%s  %s\n' "$SHA256" "$(basename "$ARCHIVE")" > "$RELEASE_DIR/SHA256SUMS.txt"
/usr/bin/printf 'Created %s\nSHA-256 %s\n' "$ARCHIVE" "$SHA256"
