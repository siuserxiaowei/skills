#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v jq >/dev/null 2>&1; then
  echo "Missing jq. Install it first: brew install jq"
  exit 1
fi

shopt -s nullglob
configs=(.anet/nodes/*/config.json)
if [ "${#configs[@]}" -eq 0 ]; then
  echo "No node configs found under .anet/nodes."
  exit 0
fi

for f in "${configs[@]}"; do
  tmp="$f.tmp"
  jq '.flags.dangerouslySkipPermissions = false | del(.flags.teammateMode)' "$f" > "$tmp"
  mv "$tmp" "$f"
done

echo "Hardened ${#configs[@]} node config(s): dangerouslySkipPermissions=false."
