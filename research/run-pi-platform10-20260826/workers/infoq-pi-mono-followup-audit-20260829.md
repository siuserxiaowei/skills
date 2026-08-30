# InfoQ Pi-Mono follow-up audit (2026-08-29)

本轮获主线程授权，只新增 append-only worker candidate/readback 证据；没有修改
`candidates.json`、`review_queue.json`、`queries.tsv`、`sources.tsv`、
`evidence_cards.tsv` 或 `platform_coverage.tsv`。

## 原页回读

- Canonical URL: `https://xie.infoq.cn/article/e42849033fd5c48ea132059a4`
- Candidate ID: `china-followup-infoq-e42849033fd5c48ea132059a4-pi-mono`
- Title: **从底层看懂 Pi-Mono：Agent 与 AI 核心机制揭秘**
- Creator: **鼎道智联**
- Visible publication line: **2026-05-29**；页面同时显示“本文字数：4357 字”
- Visible `.article-detaile` body: **约 6,984 字符**
- Body SHA-256: `def3660dcf4bc38c46da3feb24deec452d6cf79de88486627f52d087443c7546`

正文在普通匿名 Chrome 页面中完整渲染，不是搜索卡片或摘要。逐段读取了
`packages/agent` 与 `packages/ai` 的职责边界、Agent 状态和
`runAgentLoop`/`runAgentLoopContinue`、`prompt`/`continue`/`abort`/
`steer`/`followUp`、`AgentTool` 参数与执行事件、`stream`/`streamSimple`、
Provider 注册/模型查询、统一消息和流式事件，以及 coding-agent、mom、Web UI
对底层包的复用。文章明确把 `pi-mono` 作为主体，并非只在 OpenClaw 或其他
产品文章中顺带提及 Pi。

## 去重检查

写入前以 candidate ID、规范化 canonical URL、标题/作者/日期扫描了当前
`review_queue.json`、`candidates.json` 和全部 `*-candidates*.jsonl` worker
shards；未发现 `e42849033fd5c48ea132059a4` 或该 candidate ID。现有 InfoQ
对象（`5283abad...` 入门文、`sLVv23...` 演讲整理及其他队列项）标题、作者、
日期、正文主题和文章结构均不同；本页不是已接受 36Kr/Baidu 访谈稿或 Composio
benchmark 的转载。它仍需主策展人完成全局正文指纹/来源链复核，当前状态仅为
`curator_review_ready`，不得直接计入 accepted。

## 访问边界

发现使用有界 Google exact-site 查询；回读使用普通匿名 InfoQ Writing 原页。
没有登录、互动、下载、验证码/robots 绕过或 API 逆向。搜索摘要只用于发现，
正文字段与哈希来自原页可见内容。
