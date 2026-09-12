#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd -P)"
BOARD_ROOT="$PROJECT_ROOT/contest/bugfire/boards"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || { printf 'Google Chrome is required for deterministic local board rendering.\n' >&2; exit 1; }

render_tmp="$(/usr/bin/mktemp -d /tmp/bugfire-board-render.XXXXXX)"
demo_output="$render_tmp/demo"

"$PROJECT_ROOT/contest/bugfire/run-demo.sh" --output "$demo_output" >/dev/null

capture() {
  local source="$1"
  local output="$2"
  local profile="$render_tmp/chrome-$(basename "$output" .png)"
  local chrome_pid=""
  local attempt=0
  /bin/rm -f "$output"
  "$CHROME" \
    --headless=new \
    --disable-gpu \
    --disable-background-networking \
    --disable-default-apps \
    --disable-sync \
    --hide-scrollbars \
    --no-first-run \
    --allow-file-access-from-files \
    --force-device-scale-factor=1 \
    --window-size=1920,1080 \
    --user-data-dir="$profile" \
    --screenshot="$output" \
    "file://$source" >/dev/null 2>&1 &
  chrome_pid="$!"
  while [ "$attempt" -lt 300 ] && [ ! -s "$output" ]; do
    /bin/sleep 0.1
    attempt=$((attempt + 1))
  done
  if [ ! -s "$output" ]; then
    /bin/kill "$chrome_pid" 2>/dev/null || true
    wait "$chrome_pid" 2>/dev/null || true
    printf 'Chrome did not render %s within 30 seconds.\n' "$source" >&2
    exit 1
  fi
  /bin/sleep 0.3
  /bin/kill "$chrome_pid" 2>/dev/null || true
  wait "$chrome_pid" 2>/dev/null || true
}

capture "$BOARD_ROOT/source/01-ai-draft.html" "$BOARD_ROOT/01-ai-draft.png"
capture "$BOARD_ROOT/source/02-human-rejection.html" "$BOARD_ROOT/02-human-rejection.png"
capture "$demo_output/preview.html" "$BOARD_ROOT/03-pack-preview.png"

/bin/cp "$BOARD_ROOT/01-ai-draft.png" "$PROJECT_ROOT/docs/images/bugfire-director-ai-draft.png"
/bin/cp "$BOARD_ROOT/02-human-rejection.png" "$PROJECT_ROOT/docs/images/bugfire-director-human-rejection.png"
/bin/cp "$BOARD_ROOT/03-pack-preview.png" "$PROJECT_ROOT/docs/images/bugfire-director-pack-preview.png"

/usr/bin/sips -g pixelWidth -g pixelHeight \
  "$BOARD_ROOT/01-ai-draft.png" \
  "$BOARD_ROOT/02-human-rejection.png" \
  "$BOARD_ROOT/03-pack-preview.png"

printf 'Rendered three offline 1920x1080 BUGFIRE boards under %s\n' "$BOARD_ROOT"
printf 'Copied the same verified boards into docs/images for GitHub Pages.\n'
