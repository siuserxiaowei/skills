#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_CANDIDATE="$(cd "$SKILL_ROOT/../.." 2>/dev/null && pwd -P || true)"

for candidate in "${CODEX_BUGFIRE_ROOT:-}" "$REPO_CANDIDATE" "$HOME/.codex/codex-dream-skin-studio"; do
  [ -n "$candidate" ] || continue
  if [ -f "$candidate/macos/scripts/bugfire-pack.mjs" ] \
    || [ -f "$candidate/scripts/bugfire-pack.mjs" ]; then
    printf '%s\n' "$candidate"
    exit 0
  fi
done

printf 'Codex BUGFIRE engine not found. Set CODEX_BUGFIRE_ROOT to the repository root.\n' >&2
exit 1
