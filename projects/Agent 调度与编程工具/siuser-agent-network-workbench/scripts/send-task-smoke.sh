#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
export no_proxy="${no_proxy:-localhost,127.0.0.1,::1}"

if ! command -v jq >/dev/null 2>&1; then
  echo "Missing jq. Install it first: brew install jq"
  exit 1
fi

role_label() {
  case "$1" in
    inbox-agent) echo "收件箱 Agent / Inbox Agent" ;;
    digest-agent) echo "摘要 Agent / Digest Agent" ;;
    writer-agent) echo "写作 Agent / Writer Agent" ;;
    review-agent) echo "审校 Agent / Review Agent" ;;
    skill-agent) echo "Skill 维护 Agent / Skill Agent" ;;
    qa-agent) echo "验收 Agent / QA Agent" ;;
    *) echo "$1" ;;
  esac
}

from="${1:-inbox-agent}"
to="${2:-digest-agent}"
task="${3:-烟测任务 / Smoke task: $(role_label "$from") 请求 / asks $(role_label "$to") 确认本地工作台投递链路正常 / to acknowledge local workbench wiring.}"

from_config=".anet/nodes/$from/config.json"
if [ ! -f "$from_config" ]; then
  echo "Missing node config: $from_config"
  echo "Run: npm run nodes:create"
  exit 1
fi

token="$(jq -r '.token // empty' "$from_config")"
if [ -z "$token" ]; then
  echo "Missing node token in: $from_config"
  exit 1
fi

started_hub=0
if ! curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1; then
  npm run -s hub >/tmp/agent-network-send-task-smoke-hub.log 2>&1 &
  hub_pid=$!
  started_hub=1
  for _ in $(seq 1 60); do
    curl --noproxy '*' -fsS http://127.0.0.1:9200/health >/dev/null 2>&1 && break
    sleep 1
  done
fi

cleanup() {
  if [ "$started_hub" -eq 1 ]; then
    [ -n "${hub_pid:-}" ] && kill "$hub_pid" 2>/dev/null || true
    [ -n "${hub_pid:-}" ] && wait "$hub_pid" 2>/dev/null || true
    lsof -tiTCP:9200 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
  fi
}
trap cleanup EXIT

payload="$(jq -nc \
  --arg to "$to" \
  --arg task "$task" \
  --arg from "$from" \
  '{jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"send_task",arguments:{alias:$to,task:$task,priority:"normal",from_session:$from}}}')"

response="$(curl --noproxy '*' -fsS http://127.0.0.1:9200/mcp \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d "$payload")"

echo "Hub 返回 / Hub response:"
echo "$response"
echo
COMMHUB_TOKEN="$token" npm run -s anet -- tasks || true
