#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

ROOT="$(pwd)"
HUB_SESSION="agent-network-workbench-hub"
DASHBOARD_SESSION="agent-network-workbench-dashboard"
HUB_LOG="/tmp/agent-network-workbench-hub.log"
DASHBOARD_LOG="/tmp/agent-network-workbench-dashboard.log"

start_tmux_service() {
  local session="$1"
  local log="$2"
  local command="$3"

  if ! command -v tmux >/dev/null 2>&1; then
    echo "Missing tmux. Install it with: brew install tmux"
    exit 1
  fi

  if tmux has-session -t "$session" 2>/dev/null; then
    tmux kill-session -t "$session" 2>/dev/null || true
  fi

  : >"$log"
  tmux new-session -d -s "$session" "cd '$ROOT' && export NO_PROXY='${NO_PROXY}' no_proxy='${no_proxy}' && $command >>'$log' 2>&1"
}

if ! curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
  echo "Starting CommHub on http://127.0.0.1:9200"
  start_tmux_service "$HUB_SESSION" "$HUB_LOG" "bash scripts/anet.sh hub start"
fi

for _ in $(seq 1 60); do
  curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1 && break
  sleep 1
done

if ! curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
  echo "Failed to start CommHub. Log:"
  tail -80 "$HUB_LOG" || true
  exit 1
fi

if ! curl --noproxy '*' -fsS http://127.0.0.1:3000/login >/dev/null 2>&1; then
  echo "Starting Dashboard on http://127.0.0.1:3000"
  start_tmux_service "$DASHBOARD_SESSION" "$DASHBOARD_LOG" "bash scripts/anet.sh hub dashboard"
fi

for _ in $(seq 1 60); do
  curl --noproxy '*' -fsS http://127.0.0.1:3000/login >/dev/null 2>&1 && break
  sleep 1
done

if ! curl --noproxy '*' -fsS http://127.0.0.1:3000/login >/dev/null 2>&1; then
  echo "Failed to start Dashboard. Log:"
  tail -80 "$DASHBOARD_LOG" || true
  exit 1
fi

echo "OK: CommHub  http://127.0.0.1:9200"
echo "OK: Dashboard http://127.0.0.1:3000"
echo "Logs: $HUB_LOG and $DASHBOARD_LOG"
echo "Stop: npm run stop:local"
