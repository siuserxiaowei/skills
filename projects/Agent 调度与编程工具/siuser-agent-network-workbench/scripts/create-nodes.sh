#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Creating local agent profiles."
echo "This requires the Hub to be running and login to be completed."
echo "If a node already exists, the command may report that it exists; that is safe."

for name in inbox-agent digest-agent writer-agent review-agent skill-agent qa-agent; do
  npm run -s anet -- node create "$name" --runtime codex-sdk || true
done

bash scripts/harden-nodes.sh

echo "Done. Start individual nodes with:"
echo "  npm run -s anet -- node start inbox-agent"
