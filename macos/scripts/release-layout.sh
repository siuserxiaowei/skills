#!/bin/bash

set -euo pipefail

BUGFIRE_RELEASE_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
BUGFIRE_ENGINE_ROOT="$(cd "$BUGFIRE_RELEASE_SCRIPT_DIR/.." && pwd -P)"

if [ -d "$BUGFIRE_ENGINE_ROOT/skills/codex-bugfire-customizer" ] \
    && [ -d "$BUGFIRE_ENGINE_ROOT/docs" ] \
    && [ -d "$BUGFIRE_ENGINE_ROOT/contest/bugfire" ] \
    && [ -f "$BUGFIRE_ENGINE_ROOT/LICENSE" ]; then
  BUGFIRE_PROJECT_ROOT="$BUGFIRE_ENGINE_ROOT"
elif [ -d "$BUGFIRE_ENGINE_ROOT/../skills/codex-bugfire-customizer" ] \
    && [ -d "$BUGFIRE_ENGINE_ROOT/../docs" ] \
    && [ -d "$BUGFIRE_ENGINE_ROOT/../contest/bugfire" ] \
    && [ -f "$BUGFIRE_ENGINE_ROOT/../LICENSE" ]; then
  BUGFIRE_PROJECT_ROOT="$(cd "$BUGFIRE_ENGINE_ROOT/.." && pwd -P)"
else
  /usr/bin/printf 'Could not resolve BUGFIRE release layout from %s\n' "$BUGFIRE_ENGINE_ROOT" >&2
  return 1 2>/dev/null || exit 1
fi
