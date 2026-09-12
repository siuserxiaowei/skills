# earendil\-works/pi Agent 运行时与 DeepSeek Harness：本次检索范围内 Top 50

- 目标条数：50
- 合格且证据关联通过：50
- 未入选/重复：0

## 排名

### 1. [Pi Agent Harness:主仓库与版本入口](https://github.com/earendil-works/pi)

- 平台：github | 总分：84.6 | 证据：strong
- 作者：Earendil Works | 内容类型：official\_repository
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：Pi 是 Agent Harness monorepo,不只是 coding CLI;学习入口是 pi\-ai、pi\-agent\-core、pi\-coding\-agent 与 pi\-tui。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 35.0, "source_quality": 19.6}`

### 2. [Pi 根 README:身份、包边界与安全声明](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/README.md)

- 平台：github | 总分：84.6 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：官方包地图同时明确:Pi 没有内建 permission system,运行权限等于启动用户/进程权限。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 35.0, "source_quality": 19.6}`

### 3. [pi\-agent\-core README:消息、事件、工具与停止钩子](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/README.md)

- 平台：github | 总分：84.6 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：把 AgentMessage 到 LLM Message 的边界、事件时序、工具执行和 shouldStopAfterTurn 放在一条可读链路中。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 35.0, "source_quality": 19.6}`

### 4. [AgentHarness 规格:从内存 Loop 到 durable runtime](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/docs/harness.md)

- 平台：github | 总分：84.6 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：当前 core 已增加 immutable entries、registers、usage ledger、原子事务与 tool replay safety;旧 v0.80.2 教程未覆盖。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 35.0, "source_quality": 19.6}`

### 5. [agent\-loop.ts:双层循环的真实停止语义](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts)

- 平台：github | 总分：84.6 | 证据：strong
- 作者：Pi maintainers | 内容类型：source\_code
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：内层处理工具与 steering,外层排空 follow\-up;error/aborted、tool terminate 和确定性 stop hook 共同决定结束。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 35.0, "source_quality": 19.6}`

### 6. [AgentHarness 导出面与会话类型](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/index.ts)

- 平台：github | 总分：84.25 | 证据：strong
- 作者：Pi maintainers | 内容类型：source\_code
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：AgentHarness 已从 pi\-agent\-core 正式导出,但源码仍保留 NotImplemented 错误,不能把规格文档等同于全部路径均完工。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.65, "source_quality": 19.6}`

### 7. [pi\-ai:统一多供应商模型边界](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/ai/README.md)

- 平台：github | 总分：84.25 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：统一流式、工具消息和 provider 配置;DeepSeek Harness 的通用多模型适配器也复用这一层。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.65, "source_quality": 19.6}`

### 8. [Provider retry:哪些错误能透明重试](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/ai/src/utils/retry.ts)

- 平台：github | 总分：84.25 | 证据：strong
- 作者：Pi maintainers | 内容类型：source\_code
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：网络、限流与短暂服务错误走有界退避;quota/billing 与 context overflow 不能混进同一重试策略。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.65, "source_quality": 19.6}`

### 9. [pi\-coding\-agent:把 primitives 组装成产品](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/README.md)

- 平台：github | 总分：83.9 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：四个默认工具、四种运行模式、会话、资源和扩展共同构成可直接使用的终端产品。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.3, "source_quality": 19.6}`

### 10. [Extensions:把工具、命令、事件和 UI 放在用户空间](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/extensions.md)

- 平台：github | 总分：83.9 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：扩展可热加载并拥有完整进程权限;可塑性与供应链风险来自同一个设计选择。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.3, "source_quality": 19.6}`

### 11. [官方 Quickstart:最短可运行闭环](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/quickstart.md)

- 平台：github | 总分：83.9 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：先跑通认证、模型、目录和基础会话,再进入源码与扩展,避免一开始被生态配置淹没。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 34.3, "source_quality": 19.6}`

### 12. [Compaction:不是删旧消息,而是重建可见上下文](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/compaction.md)

- 平台：github | 总分：83.55 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：阈值为 contextWindow\-reserveTokens;保留 recent tail、摘要旧内容,并保证 tool call/result 不被错误拆开。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.95, "source_quality": 19.6}`

### 13. [Session format:可回放数据契约](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/session-format.md)

- 平台：github | 总分：83.55 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：消息、compaction、branch summary 等 entry 明确版本与父指针,是迁移、审计和 GUI 的底层契约。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.95, "source_quality": 19.6}`

### 14. [Sessions:一份 JSONL 如何长成树](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/sessions.md)

- 平台：github | 总分：83.55 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：id/parentId 形成树,active path 决定模型上下文;回退、分叉和分支摘要是数据结构上的自然操作。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.95, "source_quality": 19.6}`

### 15. [RPC:非 Node 客户端与 GUI 的边界](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/rpc.md)

- 平台：github | 总分：83.2 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：JSON/RPC 让 Python、桌面 GUI 或远端控制面复用真实 Pi runtime,而不是模拟聊天。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.6, "source_quality": 19.6}`

### 16. [SDK:把 Pi 嵌进自己的应用](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/sdk.md)

- 平台：github | 总分：83.2 | 证据：strong
- 作者：Pi maintainers | 内容类型：official\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：SDK 提供 session runtime 重建、切换、fork/import 等产品化接缝,适合桌面端、服务端和垂直应用。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.6, "source_quality": 19.6}`

### 17. [Pi Coding Agent 官方站](https://pi.dev/)

- 平台：google\_search | 总分：83.2 | 证据：strong
- 作者：Earendil Works | 内容类型：official\_web
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：官方定位、运行模式、会话树和扩展能力的产品入口。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.6, "source_quality": 19.6}`

### 18. [Pi v0.84.3 release:当前稳定基线](https://github.com/earendil-works/pi/releases/tag/v0.84.3)

- 平台：github | 总分：82.85 | 证据：strong
- 作者：Earendil Works | 内容类型：official\_release
- 发布：2026\-08\-24 | 访问：2026\-08\-26
- 摘要：知识库把 v0.80.2 中文教程与 v0.84.3 当前稳定版分开标记,避免把旧结论误当现状。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 33.25, "source_quality": 19.6}`

### 19. [DeepSeek Harness 官方产品页](https://deepseek.com/harness/en)

- 平台：google\_search | 总分：82.5 | 证据：strong
- 作者：DeepSeek | 内容类型：official\_web
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：Cordis kernel 把模型、工具、skills、sessions、sandbox、storage、loop、调度和 UI 全部做成插件。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.9, "source_quality": 19.6}`

### 20. [DeepSeek Harness:Everything is a Plugin](https://github.com/deepseek-ai/deepseek-harness)

- 平台：github | 总分：82.5 | 证据：strong
- 作者：DeepSeek | 内容类型：official\_repository
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：DSH 是 developer preview / RC;star 快照不能替代成熟度与运行验证。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.9, "source_quality": 19.6}`

### 21. [DSH architecture:没有特权核心的插件微内核](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md)

- 平台：github | 总分：82.5 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：profile/bundle 组合 service、event、effect;替换深度高于 Pi,但依赖图与排障成本也更高。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.9, "source_quality": 19.6}`

### 22. [DSH agent lifecycle:turn / step / request 三层](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/agent-lifecycle.md)

- 平台：github | 总分：82.15 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：与 Pi 的 steering 内环 / follow\-up 外环不是同构命名;应比较队列与 durable boundary,而非只数循环层数。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.55, "source_quality": 19.6}`

### 23. [Cordis primer:四种事件派发语义](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/cordis-primer.md)

- 平台：github | 总分：82.15 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：broadcast、bail、serial、waterfall 让 policy、prompt 与结果变换可由多个插件顺序组合。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.55, "source_quality": 19.6}`

### 24. [DSH tool execution pipeline:治理接缝更重](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/tool-execution-pipeline.md)

- 平台：github | 总分：82.15 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：durable call 后依次经过 guard、permission、sandbox、approval、wrapper、execute、post/finalize,再落 durable result。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.55, "source_quality": 19.6}`

### 25. [Mario:我从极简 Coding Agent 学到什么](https://mariozechner.at/posts/2025-11-30-pi-coding-agent)

- 平台：google\_search | 总分：81.85 | 证据：strong
- 作者：Mario Zechner | 内容类型：creator\_retrospective
- 发布：2025\-11\-30 | 访问：2026\-08\-26
- 摘要：一手解释 provider 差异、partial abort、结构化工具结果、最小 prompt/toolset 和默认高权限的代价。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 9.0, "relevance": 33.25, "source_quality": 19.6}`

### 26. [Pi 迁移到 Earendil:旧仓库与新包名的关系](https://pi.dev/news/2026/5/7/pi-has-a-new-home)

- 平台：google\_search | 总分：81.85 | 证据：strong
- 作者：Earendil Works | 内容类型：official\_web
- 发布：2026\-05\-07 | 访问：2026\-08\-26
- 摘要：v0.74.0 后 badlogic/pi\-mono 与旧 npm scope 迁移到 earendil\-works;旧教程链接需要做版本映射。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 9.0, "relevance": 33.25, "source_quality": 19.6}`

### 27. [DSH compaction:可替换 capability seam](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/compaction.md)

- 平台：github | 总分：81.8 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：start/summary/end 事件包围压缩,锁可识别 orphaned operation,surface replacement 改变模型可见上下文。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.2, "source_quality": 19.6}`

### 28. [DSH session:线性事件日志与跨 session 谱系](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/session.md)

- 平台：github | 总分：81.8 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：单 session 是 append\-only log;fork 复制 prefix 到 child session。它和 Pi 单 JSONL 内父指针树并不相同。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.2, "source_quality": 19.6}`

### 29. [DSH 直接复用 pi\-ai 的通用模型适配器](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-pi-ai/README.md)

- 平台：github | 总分：81.8 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_document
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：Pi 与 DSH 不是纯替代:DSH 的通用 provider adapter 建在 @earendil\-works/pi\-ai 上。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 32.2, "source_quality": 19.6}`

### 30. [dg\-ai\-notes:Pi 源码中文教程基线](https://github.com/buchidonggua/dg-ai-notes/tree/main/pi-agent)

- 平台：github | 总分：81.45 | 证据：strong
- 作者：冬瓜 | 内容类型：open\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：高质量中文导读与源码深潜,基于 v0.80.2;文档 CC\-BY\-SA\-4.0,适合参考但必须标版本和署名。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 31.85, "source_quality": 19.6}`

### 31. [DSH Python SDK:嵌入式路线与危险权限提示](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/user/guide/python-sdk.md)

- 平台：github | 总分：81.45 | 证据：strong
- 作者：DeepSeek maintainers | 内容类型：official\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：SDK 可复用 durable session 与 persistent shell,但示例也明确 danger\-full\-access 风险。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 31.85, "source_quality": 19.6}`

### 32. [PI Agent 学习指南:先问后读的站点化实验](https://github.com/zhoujianbin/pi-agent-guide)

- 平台：github | 总分：81.45 | 证据：strong
- 作者：zhoujianbin | 内容类型：open\_tutorial
- 发布：2026\-08\-26 | 访问：2026\-08\-26
- 摘要：每章三个无答案问题能对抗“看完以为懂了”;同样基于 v0.80.2,内容 CC\-BY\-SA\-4.0。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 10.0, "relevance": 31.85, "source_quality": 19.6}`

### 33. [Distributing Security Controls Through Harness Engineering](https://arxiv.org/html/2607.25890v1)

- 平台：google\_search | 总分：78.35 | 证据：strong
- 作者：SHarD authors | 内容类型：research\_paper
- 发布：2026\-07\-28 | 访问：2026\-08\-26
- 摘要：以 Pi 为实验底座研究 sandbox、skill scanning 与 tool restriction;论文结果需按威胁模型和非确定性限制解读。
- 分项：`{"engagement": 0.0, "evidence": 20.0, "freshness": 9.0, "relevance": 29.75, "source_quality": 19.6}`

### 34. [Pi 大道至简:保姆级全攻略](https://bilibili.com/video/BV139bD6gEa8)

- 平台：bilibili | 总分：72.55 | 证据：medium
- 作者：技术爬爬虾 | 内容类型：tutorial\_video
- 发布：2026\-08\-16 | 访问：2026\-08\-26
- 摘要：中文高热度入门,详情页可核验四工具、短系统提示与扩展生态;具体技术结论仍以源码为准。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 31.15, "source_quality": 16.4}`

### 35. [同一 Qwen 模型,Pi 与 OpenCode 结果为何不同](https://youtube.com/watch?v=fvIVGmwgk4w)

- 平台：youtube | 总分：72.55 | 证据：medium
- 作者：Cloud Codes | 内容类型：comparison\_video
- 发布：2026\-08\-24 | 访问：2026\-08\-26
- 摘要：固定模型、替换 harness 是更合理的比较思路,但单次视频实验不能外推为普遍优胜。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 31.15, "source_quality": 16.4}`

### 36. [Pi Extension 写完不等于可用:证据阶梯](https://juejin.cn/post/7675622412803358774)

- 平台：juejin | 总分：72.2 | 证据：medium
- 作者：武子康 | 内容类型：practice\_article
- 发布：2026\-08\-20 | 访问：2026\-08\-26
- 摘要：从类型检查、Mock、真实 RPC、TUI、模型路径到生产安全,提供六层扩展验收法。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 30.8, "source_quality": 16.4}`

### 37. [Pi 完整指南:从安装到 Extension 开发](https://segmentfault.com/a/1190000048176674)

- 平台：segmentfault | 总分：72.2 | 证据：medium
- 作者：七牛云行业应用 | 内容类型：tutorial\_article
- 发布：2026\-08\-19 | 访问：2026\-08\-26
- 摘要：中文全栈路线覆盖安装、模式、会话树、扩展、安全隔离与 Pi/DSH 选型;营销断言需回源。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 30.8, "source_quality": 16.4}`

### 38. [Pi Agent Crash Course](https://youtube.com/watch?v=N30XGyPrr6I)

- 平台：youtube | 总分：71.9 | 证据：medium
- 作者：Alejandro AO | 内容类型：tutorial\_video
- 发布：2026\-05\-06 | 访问：2026\-08\-26
- 摘要：25 分钟覆盖安装、模型、prompts、skills、extensions 与 tree history,适合作为上手前导。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 31.5, "source_quality": 16.4}`

### 39. [Building Pi in a World of Slop — Mario Zechner](https://youtube.com/watch?v=RjfbvDXpFls)

- 平台：youtube | 总分：71.9 | 证据：medium
- 作者：AI Engineer / Mario Zechner | 内容类型：creator\_talk
- 发布：2026\-04\-16 | 访问：2026\-08\-26
- 摘要：维护者演讲是设计哲学的一手口述;视频指标只作热度,不当成熟度证据。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 31.5, "source_quality": 16.4}`

### 40. [PI Architecture EXPLAINED](https://youtube.com/watch?v=gTeujlv8qK0)

- 平台：youtube | 总分：71.9 | 证据：medium
- 作者：Alejandro AO | 内容类型：tutorial\_video
- 发布：2026\-06\-05 | 访问：2026\-08\-26
- 摘要：用 Agent Loop、tools、TUI 串起架构;技术断言仍需回到固定 commit 源码。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 31.5, "source_quality": 16.4}`

### 41. [Pi \+ DeepSeek V4 Flash 配置与真实开发体验](https://linux.do/t/topic/2712169)

- 平台：linuxdo | 总分：71.85 | 证据：medium
- 作者：cxuanAI | 内容类型：forum\_practice
- 发布：2026\-08\-06 | 访问：2026\-08\-26
- 摘要：给出 models.json、thinking、会话树命令和任务体验;成本与效果属于单用户样本。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 30.45, "source_quality": 16.4}`

### 42. [Pi 生产主力体验:插件冲突与长程任务](https://v2ex.com/t/1235481)

- 平台：v2ex | 总分：71.85 | 证据：medium
- 作者：Geon97 等 | 内容类型：community\_discussion
- 发布：2026\-08\-20 | 访问：2026\-08\-26
- 摘要：一手反馈说明扩展越多不一定越强,插件冲突、注意力稀释和模型分工需要单独治理。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 30.45, "source_quality": 16.4}`

### 43. [Pi to Pi:双向 Agent 编排](https://youtube.com/watch?v=PIdETjcXNIk)

- 平台：youtube | 总分：71.55 | 证据：medium
- 作者：IndyDevDan | 内容类型：practice\_video
- 发布：2026\-05\-18 | 访问：2026\-08\-26
- 摘要：把 Pi 当可编排执行器,而非只在终端里单 Agent 使用。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 31.15, "source_quality": 16.4}`

### 44. [OpenClaw 背后的 Pi:让用户决定需要什么](https://zhuanlan.zhihu.com/p/2017400881730056207)

- 平台：zhihu | 总分：71.2 | 证据：medium
- 作者：Founder Park | 内容类型：interview\_article
- 发布：2026\-03\-18 | 访问：2026\-08\-26
- 摘要：整理 Mario 与深度用户访谈,适合补设计动机、扩展、会话树、SubAgent 与安全语境。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 30.8, "source_quality": 16.4}`

### 45. [How Compaction Works in Pi:社区质询与反例](https://news.ycombinator.com/item?id=49289654)

- 平台：hacker\_news | 总分：71.15 | 证据：medium
- 作者：HN community | 内容类型：community\_discussion
- 发布：2026\-08\-15 | 访问：2026\-08\-26
- 摘要：高密度讨论帮助发现压缩边界、隐藏假设和体验风险;事实结论仍回到官方 compaction 文档。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 10.0, "relevance": 29.75, "source_quality": 16.4}`

### 46. [为什么 Coding Agents 堆功能是在瞎折腾](https://infoq.cn/article/sLVv23TfVFxoBPjNwcZI)

- 平台：infoq | 总分：70.85 | 证据：medium
- 作者：傅宇琪 / Tina | 内容类型：talk\_recap
- 发布：2026\-04\-29 | 访问：2026\-08\-26
- 摘要：Mario 演讲中文整理;与 36氪转载去重后保留较完整版本。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 30.45, "source_quality": 16.4}`

### 47. [The Coding Agent I Could Shape Around My Workflow](https://dev.to/zangetsu101/the-coding-agent-i-could-shape-around-my-workflow-3c38)

- 平台：medium | 总分：70.5 | 证据：medium
- 作者：zangetsu101 | 内容类型：practice\_article
- 发布：2026\-07\-25 | 访问：2026\-08\-26
- 摘要：真实案例暴露 agent\_settled 不等于派生异步工作全部完成,并用并发回归测试修正完成语义。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 30.1, "source_quality": 16.4}`

### 48. [Wolf RBAC:用 pi\-agent\-core 嵌入权限产品](https://fast.v2ex.com/t/1218511)

- 平台：v2ex | 总分：70.5 | 证据：medium
- 作者：igeeky | 内容类型：commercial\_case
- 发布：2026\-06\-07 | 访问：2026\-08\-26
- 摘要：作者披露约 25M tokens 与 40 美元成本;可证明产品化路径,不足以证明通用 ROI。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 30.1, "source_quality": 16.4}`

### 49. [Pi\-Agent vs Claude Code:固定模型的 Code Review 对照](https://georgeracu.substack.com/p/pi-agent-vs-claude-code-in-custom)

- 平台：linkedin | 总分：70.5 | 证据：medium
- 作者：George Racu | 内容类型：controlled\_case
- 发布：2026\-07\-13 | 访问：2026\-08\-26
- 摘要：单 MR、五个 seeded defects 的小样本实验;方法比结果更值得学,必须保留作者的局限声明。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 30.1, "source_quality": 16.4}`

### 50. [pi\-web\-browse:Web 工具的 SSRF 防线](https://scaileagency.substack.com/p/introducing-pi-web-browse-give-your)

- 平台：linkedin | 总分：70.15 | 证据：medium
- 作者：Scaile Agency | 内容类型：security\_walkthrough
- 发布：2026\-04\-14 | 访问：2026\-08\-26
- 摘要：展示协议 allowlist、私网 IP 阻断、超时、body cap 与 redirect cap,说明工具安全不应只写进 prompt。
- 分项：`{"engagement": 0.0, "evidence": 15.0, "freshness": 9.0, "relevance": 29.75, "source_quality": 16.4}`

## 缺口与未入选

- 无。
