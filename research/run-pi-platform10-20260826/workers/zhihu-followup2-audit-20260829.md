# Zhihu follow-up 2 audit (2026-08-29)

本轮仅写 append-only candidate/readback 证据，不修改主账本。访问使用
agent-reach 规定的普通匿名 Chrome canonical 页面路线（本机
`agent-reach doctor --json` 已尝试但命令不存在）；Google focused exact-title
查询只用于发现，未使用站内自动搜索、登录绕过、互动或下载。

## Newly read canonical articles

1. `china-followup2-zhihu-2004665077618458930-agent-core` — 王鹏LLM，**下一代Agent架构——Pi Agent Core 设计逻辑深度解析**，编辑于 2026-02-10；7,879 chars，SHA-256 `88a766c7e996aa65f779b4cc440ff65481356adfa1555cf97aaec716b42d2dba`。聚焦 types/loop/agent facade、双层循环、steering/follow-up、错误恢复和事件流。
2. `china-followup2-zhihu-2041790459144561263-sdk` — 军舰，**Pi Agent SDK 参考文档**，发布于 2026-05-24；24,703 chars，SHA-256 `46c2bb37e464d1ab39930b00758945a07dca4a715997d11804289aa4c5caf33f`。提供 createAgentSession、runtime、prompt 队列、认证、工具、扩展/Skills、会话与 RPC/打印模式索引。
3. `china-followup2-zhihu-2043046237939749518-three-months` — 玩客笔记，**我用了三个月 Pi，终于可以告诉你它凭什么比 Claude Code 更省更聪明**，发布于 2026-05-27；6,395 chars，SHA-256 `8ef36a05d5464a9c35b41cac5b2227e0c729e01d4103e568307d45865fa3a1dd`。是三个月个人使用的对照评测，含成本/扩展/安全/门槛的作者自述。
4. `china-followup2-zhihu-2059648027586045590-scalpel` — 是13啦，**Pi Agent：一把你完全掌控的手术刀**，编辑于 2026-07-12（首发日期不可见，candidate `published_at=unknown`）；6,744 chars，SHA-256 `cabeaf68062fa43547c8ee283a892fbb3e52afb0dcd2ce9697771a6085193585`。记录跨项目 handoff、Pi-to-Pi、只读模式和 Hashline 等具体实践。

四个 URL/ID 均在写入前对当前 queue、candidates 和 worker shards 做过去重检查，未发现冲突；四位作者与内容主题彼此独立。均保持 `curator_review_ready`，不得直接计入 accepted quota，需主代理显式 promotion。
