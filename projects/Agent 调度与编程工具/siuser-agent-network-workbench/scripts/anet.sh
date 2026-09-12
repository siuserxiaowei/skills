#!/usr/bin/env bash
set -euo pipefail

ANET_RUNTIME="${ANET_RUNTIME:-$HOME/Workspace/agent-network-runtime}"
ANET_BIN="$ANET_RUNTIME/node_modules/.bin/anet"

if [ ! -x "$ANET_BIN" ]; then
  echo "Missing agent-network runtime."
  echo "Run: bash scripts/install-runtime.sh"
  exit 1
fi

export PATH="$ANET_RUNTIME/node_modules/.bin:$PATH"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"
exec "$ANET_BIN" "$@"
