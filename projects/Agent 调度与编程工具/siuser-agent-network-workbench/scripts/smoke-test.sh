#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/workbench.py doctor
python3 scripts/workbench.py init
python3 scripts/workbench.py create-task daily_digest --notes "Smoke task created by workbench."
python3 scripts/workbench.py pilot daily_digest
python3 scripts/workbench.py pilot article_pipeline --source ../wechat-articles/ai-security-scan-skill-tanstack-2026-05-14.md
python3 scripts/workbench.py pilot skill_maintenance --source ../.agents/skills/security-scan

echo "Smoke test completed."
