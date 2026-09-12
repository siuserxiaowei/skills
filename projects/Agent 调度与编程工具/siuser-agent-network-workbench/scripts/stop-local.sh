#!/usr/bin/env bash
set -euo pipefail

for session in agent-network-workbench-dashboard agent-network-workbench-hub; do
  if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$session" 2>/dev/null; then
    tmux kill-session -t "$session" 2>/dev/null || true
  fi
done

lsof -tiTCP:3000 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
lsof -tiTCP:9200 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true

for pidfile in /tmp/agent-network-workbench-dashboard.pid /tmp/agent-network-workbench-hub.pid; do
  if [ -f "$pidfile" ]; then
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [ -n "$pid" ]; then
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  fi
done

echo "Stopped local agent-network services."
