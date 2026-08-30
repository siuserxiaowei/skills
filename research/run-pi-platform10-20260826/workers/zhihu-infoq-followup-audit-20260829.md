# Zhihu / InfoQ follow-up readback audit (2026-08-29)

本轮只新增 append-only candidate/readback 证据，不直接修改
`candidates.json`、`review_queue.json` 或 accepted/coverage 账本。访问使用普通匿名
Chrome 公开页面；没有登录、互动、下载、验证码或 robots 绕过。

## Zhihu: one new Pi-primary article

- Canonical URL: `https://zhuanlan.zhihu.com/p/2071363866802574677`
- Candidate ID: `china-followup-zhihu-2071363866802574677-pi-deep-dive`
- Title: **Pi Agent 深度剖析：一个“什么都不要”的编码智能体，凭什么一年 8.9 万星？—— 与 Codex、OpenCode 的实现对比**
- Creator / column: **Arthur**, `Agent工程`
- Visible publication line: **2026-08-14 21:27・江苏**
- Full visible article text: **21,851 characters**, SHA-256
  `0ca84e20016befcd7ee64a29135d769a5a8dd408c599d293cecb57a5827b58c3`.

The canonical article is Pi-primary rather than a passing OpenClaw mention. The
readback covered the explicit `earendil-works/pi` / `pi-mono` identity, Mario
Zechner attribution, five-package layout, two-level `runLoop`, four core tools,
JSONL session tree and branching, `reserveTokens`/`keepRecentTokens` compaction,
`pi-ai` provider abstraction, Extensions/Skills/Prompt Templates/Themes/Packages,
and the deliberate omission of MCP, subagents, Plan/todo and permission dialogs.
The closing sections also discuss project trust and Gondolin/Docker/OpenShell
isolation. A focused exact-title Google check returned this same canonical result;
no matching URL or candidate ID exists in the current local queue/ledger.

## InfoQ Writing Community: one new Pi-primary article

- Canonical URL: `https://xie.infoq.cn/article/5283abadb925d54053bf986b9`
- Candidate ID: `china-followup-infoq-5283abadb925d54053bf986b9-pi-guide`
- Title: **Pi Coding Agent：一款极简主义 AI 编程助手的深度解析与实践**
- Creator: **AIWeker**
- Visible publication line: **2026-08-06** (page also shows “本文字数：2351 字”).
- Visible `.article-detaile` body: **3,613 characters**, SHA-256
  `365d64319d22e059e71da8f6c93dd272e79104ce3a4ab535c856f3c4876336d3`.

The public InfoQ Writing page rendered the complete body, not a card or search
snippet. It introduces Pi as a minimal, user-controlled factory, names Mario
Zechner, `pi-ai`, `pi-agent-core`, `pi-tui`, and `pi-coding-agent`, and provides
installation/authentication and a Flask example. Its comparison table covers
the four default tools, multi-provider support, extensions/Skills, transparency,
permission model and MIT license; later sections explain context efficiency,
when to choose Pi, and building a scheduler around extensions. The page's native
metadata and canonical link match the supplied URL. The body is materially
shorter than the Zhihu deep dive and should remain a separate, introductory
InfoQ object; no matching URL or ID appears in the current local queue/ledger.

## Promotion boundary

Both append-only candidate rows are `curator_review_ready`, not `accepted`.
Before any promotion, the primary curator must run the explicit-ID promotion
helper, compare title/author/date/body clusters against the global ledger, and
keep the InfoQ and Zhihu objects separate only if that comparison remains clean.

## Additional InfoQ discovery and cluster check

The public InfoQ result `https://www.infoq.cn/article/KyLqAEKpkvrH3tJwMgiw`
was then read in full. It is a 2026-04-01 Tina article titled **Claude Code
已经过度设计？OpenClaw 背后的 Pi 给出了一个极简答案**, with a visible
18,501-word marker, 49:28 podcast metadata, and approximately 21,892 visible
characters in the `.content-main` body (SHA-256
`30c2ba71d3979472547a046718a4faa3867054f0967f3ffa237cb39912399b3c`). The
body is a long Syntax interview transcript/analysis centering Mario Zechner and
Armin Ronacher. It covers Pi's while-loop/four-tool core, short prompt,
Extensions/Skills/session handling, YOLO/containerization, observability and a
concrete prompt-injection example.

The existing accepted InfoQ `seed-infoq-42-coding-agents` (`sLVv23...`) is a
different April 29 Tessel talk recap, and overlap with that one article is low.
However, a later global check found that this InfoQ page is effectively the same
editorial transcript as accepted 36Kr/Baidu `named-baidu-36kr-interview-digest`
(`https://36kr.com/p/3743397385044224`). Normalized 8/12/16/20/30/50-character
shingle overlap is approximately 98.6/98.4/98.2/98.0/97.6/96.7% in the InfoQ
direction and 95.2/95.0/94.8/94.7/94.2/93.4% in the 36Kr direction. The opening,
Syntax interview, Mario/Armin quotations, four-tool and prompt-injection
sections, and closing sequence are the same body. The append-only decision file
therefore marks `china-followup-infoq-KyLqAEKpkvrH3tJwMgiw-pi-podcast` as
`reject_duplicate_content_cluster`; it must not be promoted. The audio player
was not downloaded or played.

## Additional 36Kr discovery and source-chain caution

The exact-title public search also exposed
`https://www.36kr.com/p/3934404658642055`, **缓存命中率99.93%，DeepSeek最适合的Harness来了，GitHub狂揽8.6万Star** (量子位, 2026-08-11 09:02). The anonymous canonical article body was read in full (3,461 characters; SHA-256
`c3285df011322161b840403ac516a97060ec8be6261247b88dc16307a171f0ac`). It
explicitly covers Pi/DeepSeek V4 Flash cache hit rate, the Composio eight-harness
30-task report, Pi's four tools and extension/Skills model, provider adaptation,
and third-party cache projects; the footer says it is a Qbit WeChat article
authorized for 36Kr.

The article is clearly Pi-primary and a stable 36Kr object, but source-chain
review is important: it discusses the same underlying Composio/Evan facts as
accepted InfoQ `worker-cn-063` and worker `worker-cn-080`. A body-level normalized
20-shingle comparison against the current InfoQ benchmark readback found no
matching 20-shingles (different rewrite and ordering), while the factual source
line and benchmark subject overlap. The row is retained as
`curator_review_ready` with an explicit media-rewrite limitation; primary curator
should decide whether cross-platform source-chain policy permits counting it.
