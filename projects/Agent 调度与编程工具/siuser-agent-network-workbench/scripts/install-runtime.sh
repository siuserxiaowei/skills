#!/usr/bin/env bash
set -euo pipefail

ANET_RUNTIME="${ANET_RUNTIME:-$HOME/Workspace/agent-network-runtime}"
mkdir -p "$ANET_RUNTIME"

if [ ! -f "$ANET_RUNTIME/package.json" ]; then
  (
    cd "$ANET_RUNTIME"
    npm init -y >/dev/null
  )
fi

(
  cd "$ANET_RUNTIME"
  npm install @sleep2agi/agent-network@2.1.9 bun@^1.3.4
)

echo "agent-network runtime is ready at: $ANET_RUNTIME"
