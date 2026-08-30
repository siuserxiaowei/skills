# China broad gap audit — 2026-08-30

Scope: append-only public discovery/readback for 36Kr, InfoQ, OSCHINA, Toutiao and Gitee. Existing candidate IDs and canonical URLs were loaded from `review_queue.json` and all worker `*-candidates*.jsonl` shards before discovery. No existing candidate, core ledger, `candidates.json`, `review_queue.json`, `sources.tsv`, or `evidence_cards.tsv` was modified.

## New candidate

One previously unseen Gitee root was found and read end-to-end:

- `gitee-itpk-codeg-pi-workspace-20260830` — `https://gitee.com/itpk/codeg`
  - Public root title: “codeg: Codeg（Code Generation）是一个面向多 Agent 的企业级代码生成工作台。”
  - Visible owner `xggz`, main branch, 2355 commits, Apache-2.0.
  - Rendered README explicitly lists Pi among the fifteen supported coding agents and explains unified session import/search/resume, `@` delegation, parallel worktrees, Skills/MCP, permission prompts and local-first storage.
  - Full README readback hash: `c818454052751361721c4f6b90acc77d3c9953c8bf86cee693868153d81b0122` (21,779 Unicode chars; 22,083 UTF-8 bytes).
  - Decision at worker stage: `curator_review_ready`; strict curator must still decide whether the README’s “Pi” support declaration is sufficiently explicit for the frozen Pi identity gate because the root does not spell out the npm package name.

## Exact-site discovery outcomes / no-new-result records

- 36Kr: bounded public queries for `site:36kr.com/p "Pi Agent"`, `site:36kr.com/p "pi-coding-agent"`, and `site:36kr.com/p "earendil-works/pi"` returned only already-known URLs or false positives. The surfaced `36kr.com/p/3667435997717385` is a Claude swarm article where “PI Server Agent” is a generic sub-agent label; direct HTML readback contains no `earendil-works/pi`, `pi-coding-agent`, or Pi runtime discussion, so it was rejected as a same-name false positive. No new 36Kr object was added.
- InfoQ: bounded public queries for `site:xie.infoq.cn/article "Pi Agent"`, `site:xie.infoq.cn/article "Pi Coding Agent"`, and `site:xie.infoq.cn/article "earendil-works/pi"` produced no new canonical result beyond existing accepted/held URLs. No new InfoQ object was added.
- OSCHINA: bounded query `site:my.oschina.net "pi-coding-agent"` surfaced old unrelated posts without the specified Pi identity; no new canonical object was added. Existing 19741369, 19743475 and Huiyu-Pi remain the only independently read objects in this shard.
- Toutiao: bounded query `site:toutiao.com/article "pi-coding-agent"` produced no new canonical result. The newly inspected `7673696349073818147` is a Hubwiz cross-post (see `toutiao-hubwiz-pi-sdk-crosspost-audit-20260830.md`) and was not added.
- Gitee: Brave exact-site search also surfaced `bin-mian/PyAgent`, `baidu/ipipe-agent`, `henry_host/PI` and similar false positives. Their public READMEs concern generic operations agents, CI task agents or an unrelated C/C++ PI library; none names `earendil-works/pi`, `pi-coding-agent`, `pi-mono`, or Pi AgentHarness. They were rejected and not added. `itpk/codeg` is the only new root whose rendered README explicitly lists Pi as a supported coding agent.

## Boundaries

All reads were public, anonymous and read-only. No login, CAPTCHA, paywall, download, star/follow, issue/comment, push or account mutation was attempted. Gitee security/challenge routes and disallowed API/raw/blob automation were not used as final evidence. The new line is append-only and awaits main-thread curator promotion; it must not be counted as accepted until `candidates.json` is explicitly updated by the curator.
