# Gitee voice2024/how-pi-agent-works follow-up audit (2026-08-30)

Before discovery I loaded the current `candidates.json`, `review_queue.json`, and all worker candidate shards and checked both candidate IDs and normalized canonical URLs. `gitee-voice2024-how-pi-agent-works-20260830` and `https://gitee.com/voice2024/how-pi-agent-works` were absent. A bounded native Gitee search for `Pi Agent` exposed this public root; no internal API, blob/raw route, crawler or account action was used.

The anonymous Chrome root page was read end to end. It visibly identifies the `voice` owner, 29 commits, MIT license, and the title “Pi Agent 原理与实现：从零到一实现一个 AI Agent”. The rendered README explicitly links `earendil-works/pi` and `pi.dev`, explains Agent Loop, messages/stream events, tool calls, session trees, context compaction, and the `pi-ai`/`pi-agent-core`/`pi-coding-agent` layers. It also describes four progressive TypeScript demos, a React+Node teaching agent, docs build and teaching-agent test/typecheck/build commands, and an environment-variable-only API-key warning. The rendered body text was 3,065 characters with SHA-256 `84296a2aced1832766e677d6de948d909410dc32cd37d4bc88a737b776ee2fb7`.

This is an independent tutorial/teaching implementation, not an upstream mirror: it has a distinct owner, repository object, VitePress/docs structure and original explanatory/demo content. No same-author or same-content cluster was found in the frozen local snapshot. The row is appended as `curator_review_ready`; primary curator promotion remains required. No existing global ledger was modified.

All access was anonymous, ordinary-browser, read-only. No login, CAPTCHA, download, install, build, star, issue, comment, fork or other mutation was attempted.
