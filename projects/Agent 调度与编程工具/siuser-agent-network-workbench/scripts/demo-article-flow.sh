#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

source_path="../wechat-articles/ai-security-scan-skill-tanstack-2026-05-14.md"
tasks_dir="$HOME/Documents/Obsidian Vault/90_Agent/tasks"
drafts_dir="$HOME/Documents/Obsidian Vault/03.公众号/_agent_drafts"

echo "== Agent Network Workbench: 公众号生产演示 / Article demo =="
echo
echo "这条命令会做什么 / What this does:"
echo "1. 启动本地 Hub 和 Dashboard / Starts the local Hub and Dashboard."
echo "2. 创建 article_pipeline 任务 JSON / Creates an article_pipeline task JSON."
echo "3. 生成本地 Obsidian 公众号草稿 / Generates a local Obsidian article draft."
echo "4. 投递一条中英文任务到 Dashboard > Tasks / Sends a bilingual task to Dashboard > Tasks."
echo

if [ ! -f "$source_path" ]; then
  echo "缺少演示素材 / Missing demo source: $source_path"
  echo "请修改 scripts/demo-article-flow.sh，把 source_path 指向一篇 Markdown 文章。"
  exit 1
fi

npm run start:local

echo
echo "== 创建任务 / Create task =="
npm run task:article

echo
echo "== 生成草稿 / Generate draft =="
npm run pilot:article

echo
echo "== 投递 Dashboard 可见任务 / Send visible Dashboard task =="
npm run smoke:send-task

latest_task="$(ls -t "$tasks_dir"/article_pipeline_*.json 2>/dev/null | head -n 1 || true)"
latest_draft="$(ls -t "$drafts_dir"/article_pipeline_*.md 2>/dev/null | head -n 1 || true)"

echo
echo "== 演示结果 / Demo result =="
echo "Dashboard: http://127.0.0.1:3000"
echo "任务 JSON / Task JSON: ${latest_task:-not found}"
echo "草稿 MD / Draft MD:  ${latest_draft:-not found}"
echo
echo "怎么看 Dashboard / How to read the Dashboard:"
echo "- Tasks / 任务：看刚刚那条 delivered，意思是任务已投递。"
echo "- Mesh / 节点：看 6 个本地 Agent 角色配置。"
echo "- Messages / 消息：看角色之间的消息记录。"
