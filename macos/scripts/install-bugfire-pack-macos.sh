#!/bin/bash

set -euo pipefail
. "$(cd "$(dirname "$0")" && pwd -P)/common-macos.sh"

PACK_DIR=""
APPLY_NOW="true"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --pack) PACK_DIR="${2:-}"; shift 2 ;;
    --no-apply) APPLY_NOW="false"; shift ;;
    *) fail "Unknown Bugfire Pack argument: $1" ;;
  esac
done

[ -n "$PACK_DIR" ] || fail "Usage: install-bugfire-pack-macos.sh --pack <folder> [--no-apply]"
[ -d "$PACK_DIR" ] || fail "Bugfire Pack folder not found: $PACK_DIR"

discover_codex_app
require_macos_runtime
ensure_state_root

THEMES_ROOT="$STATE_ROOT/themes"
REPORT_JSON="$("$NODE" "$SCRIPT_DIR/bugfire-pack.mjs" validate "$PACK_DIR")"
PACK_ID="$("$NODE" -e 'const value=JSON.parse(process.argv[1]);process.stdout.write(value.packId)' "$REPORT_JSON")"
PACK_NAME="$("$NODE" -e 'const value=JSON.parse(process.argv[1]);process.stdout.write(value.packName)' "$REPORT_JSON")"
LIBRARY_DIR="$THEMES_ROOT/$PACK_ID"

/bin/mkdir -p "$THEMES_ROOT"
"$NODE" "$SCRIPT_DIR/bugfire-pack.mjs" build "$PACK_DIR" "$LIBRARY_DIR" --replace >/dev/null

if [ "$APPLY_NOW" = "true" ]; then
  /bin/bash "$SCRIPT_DIR/switch-theme-macos.sh" --id "$PACK_ID"
fi

if [ "$APPLY_NOW" = "true" ]; then
  printf 'Installed and activated Bugfire Pack “%s” (%s) from %s\n' "$PACK_NAME" "$PACK_ID" "$PACK_DIR"
else
  printf 'Installed Bugfire Pack “%s” (%s) in the local library; active theme and progress are unchanged.\n' "$PACK_NAME" "$PACK_ID"
fi
