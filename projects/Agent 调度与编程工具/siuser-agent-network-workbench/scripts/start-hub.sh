#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ANET_RUNTIME="${ANET_RUNTIME:-$HOME/Workspace/agent-network-runtime}"

if [ ! -x "$ANET_RUNTIME/node_modules/.bin/anet" ] || [ ! -x "$ANET_RUNTIME/node_modules/.bin/bunx" ]; then
  echo "Missing agent-network runtime. Run: npm install"
  exit 1
fi

echo "Starting local-only agent-network Hub on 127.0.0.1:9200"
echo "Do not expose this port publicly."
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"
npm run -s anet -- hub start
