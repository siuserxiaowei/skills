#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ANET_RUNTIME="${ANET_RUNTIME:-$HOME/Workspace/agent-network-runtime}"
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"
ROOT="$(pwd)"
HUB_LOG="/tmp/agent-network-workbench-hub.log"

if [ ! -x "$ANET_RUNTIME/node_modules/.bin/anet" ] || [ ! -x "$ANET_RUNTIME/node_modules/.bin/bunx" ]; then
  echo "Missing agent-network runtime. Run: npm install"
  exit 1
fi

echo "Starting local dashboard on http://127.0.0.1:3000"
if ! curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
  echo "CommHub is not running; starting local Hub on 127.0.0.1:9200 first."
  if ! command -v tmux >/dev/null 2>&1; then
    echo "Missing tmux. Install it with: brew install tmux"
    exit 1
  fi
  tmux kill-session -t agent-network-workbench-hub 2>/dev/null || true
  : >"$HUB_LOG"
  tmux new-session -d -s agent-network-workbench-hub "cd '$ROOT' && export NO_PROXY='${NO_PROXY}' no_proxy='${no_proxy}' && bash scripts/anet.sh hub start >>'$HUB_LOG' 2>&1"

  for _ in $(seq 1 60); do
    if curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if ! curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
    echo "Failed to start CommHub. Log:"
    tail -80 "$HUB_LOG" || true
    exit 1
  fi
fi

bash scripts/anet.sh hub dashboard
