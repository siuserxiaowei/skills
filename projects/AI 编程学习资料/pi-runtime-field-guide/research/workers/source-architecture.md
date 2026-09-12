# Pi 与 DeepSeek Harness：官方源码架构核验

> 【事实】研究分片：官方源码、官方文档与两套中文教程的版本核验。冻结时间：2026-08-26 08:10:46（Asia/Shanghai）。本文只把读过的仓库文件、官方网页与 GitHub API 作为证据；搜索摘要不作为证据。

## 0. 结论先行

- 【事实】当前 `earendil-works/pi` 的官方定位是 **Pi Agent Harness**。它同时提供终端 coding agent、统一模型层 `pi-ai`、低层运行时 `pi-agent-core`、TUI 等包，并不是只有一个“Agent Loop demo”。证据：[官方 README，身份与包列表](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/README.md#L13-L35)。
- 【事实】当前 Pi 的学习对象至少要拆成两层：一是 `Agent` / `agentLoop` 这套易读、状态式低层运行时；二是已经由 `pi-agent-core` 导出的持久化 `AgentHarness`，后者增加 entry tree、facts、lanes、usage ledger、原子事务和崩溃恢复语义。证据：[core 导出面](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/index.ts#L43-L80)、[AgentHarness 规格](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/docs/harness.md#L80-L137)。
- 【事实】`badlogic/pi-mono` 不是另一个需要并列研究的当前项目；GitHub API 现已把它重定向到 `earendil-works/pi`。当前教程中出现 `pi-mono`，应理解为仓库旧名/旧入口，而不是平行实现。证据：[旧入口 API 的当前 canonical `full_name`](https://api.github.com/repos/badlogic/pi-mono)、[当前仓库](https://github.com/earendil-works/pi)。
- 【事实】DeepSeek Harness（下文简称 DSH）的官方定位是 developer preview；模型、工具、session、sandbox、storage、loop、调度和 UI 都通过 Cordis 插件组合，甚至 agent loop 也不是“特权核心”。证据：[官方 README](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/README.md#L5-L11)、[架构说明](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md#L9-L14)。
- 【事实】Pi 与 DSH 不是纯粹的“二选一”竞争关系：DSH 的通用多供应商适配器直接建立在 `@earendil-works/pi-ai` 上。证据：[DSH `llm-pi-ai` 说明](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-pi-ai/README.md#L1-L11)。
- 【事实】`dg-ai-notes` 与 `pi-agent-guide` 的 Pi 源码教程都明确以 v0.80.2 为基线，而当前 Pi release 是 v0.84.3；直接翻修旧十章会漏掉 durable `AgentHarness`、session backend、lane 等当前结构。证据：[dg 教程版本声明](https://github.com/buchidonggua/dg-ai-notes/blob/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf/pi-agent/pi_source_dive/typescript/%E7%AC%AC1%E7%AB%A0-%E5%BC%80%E7%AF%87-Pi-Agent%E6%A1%86%E6%9E%B6%E6%80%BB%E8%A7%88.md#L426-L428)、[guide 版本声明](https://github.com/zhoujianbin/pi-agent-guide/blob/f838dd4a166d0130d8f5fa96db689a557ae6b5ff/content/chapters/ch01.md#L236-L243)、[Pi v0.84.3 release](https://github.com/earendil-works/pi/releases/tag/v0.84.3)。
- 【推断】新知识库最有辨识度的切口不是复刻“十章导读”，而是做成 **v0.80.2 教程基线 → v0.84.3 当前源码差分 → DSH 架构对照 → 可运行实验**。这能把已有中文内容的版本缺口转成明确产品价值。

## 1. 冻结版本与项目身份

| 项目 | 冻结版本 / commit | 2026-08-26 快照 | 许可证与成熟度信号 |
|---|---|---|---|
| 事实｜Pi | `main` = [`8fa7eeb`](https://github.com/earendil-works/pi/commit/8fa7eebd235355522c8104166b4f1f959b4e2f10)；最新稳定 release [`v0.84.3`](https://github.com/earendil-works/pi/releases/tag/v0.84.3) | 97,227 stars；12,016 forks；139 open issues | MIT；稳定 release；仓库创建于 2025-08-09。元数据：[GitHub API](https://api.github.com/repos/earendil-works/pi)，许可证：[LICENSE](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/LICENSE#L1-L20)。 |
| 事实｜DeepSeek Harness | `master` = [`b150a55`](https://github.com/deepseek-ai/deepseek-harness/commit/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e)；release `dsh-v0.1.1-rc.2` | 195,224 stars；22,054 forks；GitHub Issues 功能被关闭，不能把 API 的 `open_issues=0` 解读为零缺陷 | MIT；RC / developer preview；仓库创建于 2026-08-13。元数据：[GitHub API](https://api.github.com/repos/deepseek-ai/deepseek-harness)，许可证：[LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/LICENSE#L1-L20)。 |
| 事实｜dg-ai-notes | [`5f4abd3`](https://github.com/buchidonggua/dg-ai-notes/commit/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf) | 2,312 stars；176 forks；4 open issues | 教程代码 MIT、文档 CC-BY-SA-4.0。证据：[教程 README](https://github.com/buchidonggua/dg-ai-notes/blob/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf/pi-agent/README.md#L77-L80)、[API](https://api.github.com/repos/buchidonggua/dg-ai-notes)。 |
| 事实｜pi-agent-guide | [`f838dd4`](https://github.com/zhoujianbin/pi-agent-guide/commit/f838dd4a166d0130d8f5fa96db689a557ae6b5ff) | 66 stars；2 forks；1 open issue | 章节内容 CC-BY-SA-4.0，工程代码由 README 声明为 MIT，运营二维码图片不在开源许可内。证据：[README](https://github.com/zhoujianbin/pi-agent-guide/blob/f838dd4a166d0130d8f5fa96db689a557ae6b5ff/README.md#L67-L78)、[API](https://api.github.com/repos/zhoujianbin/pi-agent-guide)。 |

- 【事实】以上 stars 是同一时间点的易变快照，只能描述该时刻的 GitHub 计数，不能证明质量、成熟度或“全网排名”。
- 【事实】Pi 根工作区通过 `packages/*` 等 workspaces 组织；核心公开包包括 `@earendil-works/pi-ai`、`pi-agent-core`、`pi-coding-agent` 和 `pi-tui`。证据：[根 package.json](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/package.json#L1-L17)、[README 包列表](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/README.md#L26-L35)。
- 【事实】DSH 根包版本为 `0.1.1-rc.2`，使用 pnpm workspace，覆盖 `vendor/*`、`packages/*/*`、`apps/*`，Node 要求为 `^22.19.0 || >=24.0.0`。证据：[DSH package.json](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/package.json#L1-L18)。
- 【推断】Pi 的稳定 release、较长公开历史与较小核心面，使其目前更适合作为入门源码和较低变动风险的嵌入式底座；DSH 的 developer-preview/RC 标签意味着近期 API 和配置破坏性变化风险更高。这个判断来自发布状态，不来自 star 数。

## 2. Pi：两层运行时，而不是一条链

### 2.1 低层 `Agent` / `agentLoop`

- 【事实】Pi 的低层 loop 是显式双层结构：内层在 assistant 产生 tool calls 或收到 steering 消息时继续；外层在一次 turn chain 结束后继续排空 follow-up 消息。assistant 返回 `error` 或 `aborted` 会退出。证据：[双层循环与退出分支](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L155-L275)。
- 【事实】停止并不只靠模型输出：tool result 可以给出 `terminate`，运行时还可调用 `shouldStopAfterTurn` 在读取队列或再次请求模型前做确定性拦截。证据：[Agent README 的 hooks/termination 说明](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/README.md#L122-L146)、[配置类型](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/types.ts#L212-L290)。
- 【事实】Pi 要求 `StreamFn` 不用 throw 表示模型请求、运行时或流错误，而在最终 `AssistantMessage` 中以 `stopReason=error|aborted` 表达；这让 loop 能用统一消息状态做退出判断。证据：[StreamFn 合约](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/types.ts#L18-L32)。
- 【事实】应用侧消息可以是富类型 `AgentMessage`；真正送入模型前先经过 `transformContext`，再经 `convertToLlm` 收敛为严格 LLM 消息。证据：[消息边界说明](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/README.md#L45-L64)。
- 【事实】Pi 在 `message_end` 后才进入工具预检/执行阶段；事件顺序被当作时序屏障，而不仅是 UI 通知。证据：[事件序列与工具执行顺序](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/README.md#L65-L120)。
- 【推断】教学时应把“为什么双层”落到两个不同队列语义：steering 是当前链路内纠偏，follow-up 是当前链路结束后的新工作；合成单层 while 会让优先级、停止点和事件顺序变得含糊。

### 2.2 工具管道、失败与重试边界

- 【事实】一次 Pi 工具调用实际经历 lookup → 参数准备/校验 → `beforeToolCall` → execute/update → `afterToolCall` → result；找不到工具、校验失败、hook 拦截和执行 throw 都会被标准化成 `isError` 的 tool result，而不是直接炸穿 loop。证据：[预检与拦截](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L600-L668)、[执行与流式更新](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L670-L711)、[后处理](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L713-L758)。
- 【事实】provider 因长度截断、但响应里仍含 tool calls 时，Pi 拒绝执行这些可能残缺的参数，并把错误结果交回模型。证据：[截断保护](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L374-L405)。
- 【事实】并发工具会先按源码顺序预检，再并行执行，并维持结果顺序；sequential 工具则形成执行屏障。证据：[调度入口](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L408-L425)、[并发预检和执行](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L489-L553)。
- 【事实】低层工具管道没有对 tool body 的内建自动重试；失败成为模型可见的 tool result，模型可以决定是否改参重试。模型供应商请求重试是另一条机制，按 transient error 分类执行指数退避。证据：[工具异常归一化](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/agent-loop.ts#L670-L711)、[provider retry](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/ai/src/utils/retry.ts#L92-L104)、[重试与溢出分类](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/ai/src/utils/retry.ts#L145-L227)。
- 【推断】“要不要重试”必须分成两题：网络/限流等同一请求可由 provider policy 透明重试；有副作用的工具若自动重试可能重复扣费、发消息或写数据，默认把错误交给模型/上层 policy 更安全。需要自动 tool retry 时，必须增加幂等键、重放策略和副作用分类。

### 2.3 Context、自动压缩与会话树

- 【事实】coding-agent 的自动压缩阈值为 `contextTokens > contextWindow - reserveTokens`；默认保留 16,384 tokens 余量，寻找切点后保留约 20k 最近内容，对较早内容做摘要，并用 compaction entry 重建上下文。证据：[压缩算法](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/compaction.md#L27-L45)。
- 【事实】切点不会落在 tool result 上；跨越单个 user turn 时会保留 turn prefix，避免产生没有对应调用的孤立 tool result。证据：[切点规则](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/compaction.md#L81-L117)。
- 【事实】context overflow 不走普通 provider retry；session controller 会触发压缩并最多重试一次，失败/截断 assistant 从活动上下文移除，但保留在历史中。证据：[溢出恢复](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/src/core/agent-session.ts#L2131-L2175)、[retry 分流](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/src/core/agent-session.ts#L2821-L2829)。
- 【事实】普通 transient provider error 使用可配置指数退避；等待可取消，错误消息仍写在 session history 中，但从下一次模型活动上下文移除。证据：[coding-agent retry 控制器](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/src/core/agent-session.ts#L2862-L2915)。
- 【事实】coding-agent 的 JSONL entry 带 `id` / `parentId`；同一个 session 文件因此形成树。`/tree` 切换 active leaf，模型上下文沿根到当前叶的路径构建，不需要删改旧分支。证据：[entry 和 compaction 结构](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/session-format.md#L203-L260)、[树和 active path](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/session-format.md#L306-L342)。
- 【事实】从树中离开旧分支时，Pi 会找共同祖先、收集旧分支、生成 branch summary，再把摘要追加到新路径。证据：[branch summarization](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/compaction.md#L148-L160)。
- 【推断】Pi 的树并不是“为了 UI 分叉而额外打补丁”，而是持久层的父指针模型；回退、平行分支、分支摘要都能围绕 active path 统一解释。这是知识库里最值得配图做交互实验的数据结构主题。

### 2.4 当前的 durable `AgentHarness`

- 【事实】当前 `pi-agent-core` 已导出 `AgentHarness` 及 harness session/compaction/tool 类型；它不是只存在于未引用的设计文档。证据：[导出面](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/index.ts#L43-L80)。
- 【事实】其规格把持久状态拆为 immutable entry store、mutable register store 与 append-only usage ledger；原子 transaction 让 durable program counter 与 effect state 一起落盘。证据：[三类存储与原子事务](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/docs/harness.md#L115-L137)。
- 【事实】entry 类型含 message、model change、thinking、active tools、compaction、branch summary 和 custom，并继续用 `parentId` 构造树；compaction entry 记录 retained tail。证据：[harness session types](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/harness/session/types.ts#L14-L74)。
- 【事实】工具重放策略区分 `never` 与 `safe`：崩溃恢复时，`never` 不会重放副作用工具，而是生成 synthetic error；`safe` 才允许重新执行。证据：[工具 replay safety](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/docs/harness.md#L180-L205)。
- 【事实】规格明确不承诺 exactly-once、partial stream resume、多写者并发、复制与删除；流片段是进程内状态，只有 settled response 才进入 durable model。证据：[非目标](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/docs/harness.md#L207-L214)。
- 【事实】实现中仍定义 `HarnessNotImplemented` 错误类型，因此不能仅凭导出面推断所有文档操作都已经完整实现。证据：[实现错误类型](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/agent/src/harness/agent-harness.ts#L74-L80)。
- 【推断】知识库应把 `AgentHarness` 单列为“当前进阶轨”，并用源码测试确认每项能力的真实完成度；若继续只讲 coding-agent JSONL，会把旧教程的产品层 session model 错当成当前 core 的全部能力。

### 2.5 Extensions 与安全边界

- 【事实】Pi extension 可注册工具、命令、事件、UI、消息渲染和持久状态；TypeScript extension 由运行时加载并支持 `/reload`。证据：[extension 能力与加载](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/extensions.md#L1-L29)、[异步工厂和加载器](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/extensions.md#L154-L181)。
- 【事实】Pi 官方明确写明没有内建 permission system，coding agent 继承启动进程/用户的权限；extension 也能执行任意代码、拥有完整系统权限，官方建议用容器或其他 sandbox 隔离不受信环境。证据：[根 README 安全声明](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/README.md#L38-L46)、[extension 安全提示](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/packages/coding-agent/docs/extensions.md#L109-L150)。
- 【推断】“模型不许乱做”不应只写 prompt。Pi 低层已提供 hook 和工具管道，但企业交付还需要独立的 permission/policy、sandbox、审计和 secret broker 层；这是服务和产品机会，也是必须醒目标出的安全缺口。

## 3. DeepSeek Harness：Cordis 微内核与事件溯源

### 3.1 组合哲学和包结构

- 【事实】DSH 的 Cordis 插件可以贡献 service、typed event 与 reversible effect；模型 adapter、tool registry、session log、agent loop 都由插件提供，架构声明“没有 privileged core”。证据：[架构总览](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md#L9-L14)、[Cordis 五个概念](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/cordis-primer.md#L5-L13)。
- 【事实】Cordis 事件分成广播、bail、serial 和 waterfall；waterfall 让多个插件按顺序变换同一值，是 policy、prompt、tool result 和错误恢复的主要组合点。证据：[事件派发模式](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/cordis-primer.md#L15-L35)。
- 【事实】profile 和 bundle 负责声明插件集合与有序配置层；base bundle 已组合 provider adapters、tools、persistence、policy、settings/credentials、telemetry、spawn/fork 等能力。证据：[profile/bundle 配置](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md#L15-L37)、[base bundle](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/bundle/base/README.md#L1-L7)。
- 【事实】DSH 区分 durable session events、live agent coordination events 与 capability seam events，避免把所有信号都当成同一条日志。证据：[事件分层](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md#L53-L61)。
- 【推断】DSH 更接近“可替换子系统的 agent 操作系统/微内核”，Pi 更接近“可读的 runtime primitives + 可直接使用的 coding product”。DSH 的收益是替换深度，代价是服务注入、事件派发、profile/config layering 带来的认知和排障成本。

### 3.2 Turn / Step / Request 三层循环

- 【事实】DSH driver 反复调用 `turn()`；每个 turn 可含多个 step，每个 step 内又有 provider request retry 的 `while(true)`。这不是 Pi 那种“steering 内环 + follow-up 外环”的同构命名。证据：[driver](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/src/agent.ts#L210-L223)、[turn/step](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/src/agent.ts#L245-L330)、[request retry loop](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/src/agent.ts#L332-L419)。
- 【事实】成功 provider 调用的流片段、assistant message、工具调用与结果都进入 durable session log；compaction 可在 pre-step 或 request-error seam 介入。证据：[生命周期说明](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/agent-lifecycle.md#L19-L80)。
- 【事实】DSH 的 `llm-retry` 是插件：默认 normal policy 对 empty response、rate limit、server、timeout 和 transport 错误最多重试五次，500ms 起步、10s 封顶并带 10% jitter；重试事件本身可持久化，模型不直接看到中间失败。证据：[retry policy](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-retry/README.md#L1-L13)、[可见性与限制](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/llm/llm-retry/README.md#L31-L52)。
- 【推断】DSH 把“重试策略”提升为可替换插件并记入 durable trace，更适合统一治理不同 agent；Pi coding-agent 的内置控制器更直接、更易读，但若多产品共享策略，需要另加抽象层。

### 3.3 更重的工具执行管道

- 【事实】DSH 在真正调用工具前先持久化 `tool/call`，随后经过 pre waterfalls、权限/sandbox/guard、approval、execute wrappers、tool body、post/finalize，冻结标准化结果后再持久化 `tool/result`。guard 采用单调语义：后续插件不能把已经拒绝的调用改回允许。证据：[完整工具管道](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/tool-execution-pipeline.md#L4-L60)。
- 【事实】工具调度支持 exclusive barrier 与有界 rolling pool；pre 阶段有序、tool body 可并发、post 和结果重新按原调用顺序提交。abort 时会排空并为未执行项生成 synthetic result。证据：[调度语义](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/src/tool-calls.ts#L1-L11)、[rolling pool](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/agent-loop/src/tool-calls.ts#L112-L245)。
- 【事实】DSH base tool semantics 同样不是“失败自动重跑”；如果要 retry，可由插件围绕 `tools/execute` 包装，并需自行处理副作用和取消合约。证据：[tool API 与 execution mode](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/tools/README.md#L18-L35)、[extension points](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/tools/README.md#L41-L59)。
- 【推断】DSH 的默认工具面比 Pi 丰富，适合 permission、sandbox、approval、metrics 和 retry 都由不同团队/插件负责的场景；单人学习时应先画出 waterfall 和 durable event 时序，否则容易“每个文件都懂、整条调用链仍不懂”。

### 3.4 Durable event log、压缩与分叉

- 【事实】DSH session 是 append-only typed `SessionEvent` log，是重建模型 history 的 source of truth；事件包含 turn/step、user、assistant chunk/message、tool call/result、request header/context 等。证据：[session 定义与事件词汇](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/session.md#L1-L128)。
- 【事实】事件有单调递增 `seq`，重建遇到未知 required event type 会失败关闭；模型可见 surface 是由日志派生，而不是原地改写日志。证据：[SessionEvent 合约](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/session.md#L198-L249)、[surface 模型](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/session.md#L255-L315)。
- 【事实】DSH compaction 是可选 capability seam，而不是硬编码 loop spine；start/summary/end 三类 log-only 事件包围一次压缩，lock 使崩溃后的 orphaned operation 可检测，summary 通过 surface replacement 改变模型可见上下文。证据：[compaction event transaction](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/compaction.md#L1-L23)。
- 【事实】压力触发压缩发生在 pre-step；context-overflow recovery 只有在生成出新的 surface 时才重试，还可以选择性剪枝旧 tool result，同时保持 tool call/result 配对边界。证据：[触发、失败与边界](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/compaction.md#L25-L88)。
- 【事实】DSH 的单个 session 本身仍是线性 append-only log。fork 会把源 session 的某个 turn 间边界之前的 prefix 复制到新的 child session，并写 `parentSession` / `seedLength` 元数据；会话谱系在多个 session 之间形成树。证据：[fork 语义](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/session.md#L527-L542)、[fork 实现](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/packages/core/session/src/index.ts#L1073-L1094)。
- 【推断】Pi coding-agent 是“单文件内的 entry tree”；DSH 是“每个 session 线性、跨 session 谱系成树”。两者都支持分叉，但恢复、复制成本、分享边界与 UI 语义不同，不能笼统写成“都采用会话树”。

### 3.5 插件边界

- 【事实】DSH dynamic extension 可以定义版本化 Cordis package，并由 host/browser 两侧 runner 加载；runner 具有 define、run 和 approval 生命周期。证据：[extension 模型](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/extensions.md#L1-L13)、[runner/approval](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/subsystems/extensions.md#L67-L119)。
- 【事实】policy、context construction、storage、provider、tool、UI 和 durable state 都是官方列出的扩展 seam；这比只增加一个工具或 command 更接近替换子系统。证据：[capability seams](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/docs/architecture.md#L92-L130)。
- 【推断】DSH 适合已有平台团队把权限、存储、模型路由、前端和审计分别产品化；若目标只是理解 agent loop 或快速嵌入一个 agent，Pi 的源码路径更短，学习投资回报更快。

## 4. Pi 与 DSH 对照矩阵

| 维度 | Pi | DeepSeek Harness | 判断 |
|---|---|---|---|
| 产品边界 | 事实｜terminal coding agent + `pi-ai` + low-level agent core + current durable AgentHarness | 事实｜local-first Web/headless harness，所有主要能力以 Cordis plugin/profile/bundle 组合 | 推断｜Pi 是“清晰 primitives + 成品 coding agent”；DSH 是“可组装平台内核”。 |
| Loop | 事实｜steering/tool 内环 + follow-up 外环；`terminate` / `shouldStopAfterTurn` | 事实｜driver → turn → step → request retry；`agent/turn-stopping` 等 waterfall | 推断｜不能只比“都有双层循环”，应比较各层队列和 durable boundary。 |
| Provider | 事实｜`pi-ai` 统一多供应商 | 事实｜既有 DeepSeek adapter，也直接用 `pi-ai` 的通用 adapter | 推断｜DSH 可以位于 Pi provider 层之上，二者可组合。 |
| Tool | 事实｜校验、before、execute/update、after、result；错误归一化 | 事实｜durable call、guard/permission/sandbox/approval、execute wrappers、post/finalize、durable result | 推断｜DSH 治理 seam 更完整；Pi 更适合源码教学和轻量定制。 |
| Tool retry | 事实｜core 不透明自动重试；失败交给模型/上层 | 事实｜base 也不自动重试；可用 wrapper plugin 扩展 | 推断｜两者都要求显式解决幂等和副作用，不应宣传“自动兜底”。 |
| 消息/事件 | 事实｜富应用消息经 transform/convert 送模型；事件流承担时序屏障 | 事实｜typed append-only durable event log 派生模型 surface，另有 live/capability events | 推断｜DSH 的回放/审计更原生；Pi 的消息模型更容易读懂和嵌入。 |
| 流恢复 | 事实｜当前 AgentHarness 只持久化 settled response，不恢复 partial stream | 事实｜assistant raw chunks 可进入 session log | 推断｜DSH 对 UI/replay 细节更忠实；是否能恢复同一 provider stream 仍不能仅由“记录 chunks”推出。 |
| Context | 事实｜coding-agent 摘要旧内容并保留 recent tail；overflow 压缩后最多重试一次 | 事实｜compaction capability 以 durable start/summary/end 和 surface replacement 工作 | 推断｜两者都超越“截断数组”，DSH 更 event-sourced，Pi 算法更容易教学。 |
| 分叉 | 事实｜同一 JSONL 内 entry parent tree 与 active path | 事实｜每个 session 线性，fork 复制 prefix 到 child session | 推断｜Pi 的原地导航更自然；DSH 的 session 隔离和分享边界更清楚。 |
| Extension | 事实｜热加载 TS extensions、skills、prompts、themes；extension 有进程完整权限 | 事实｜Cordis plugin 可替换 loop/session/provider/storage；base 有 policy/sandbox/approval | 推断｜DSH 深度更高但复杂；Pi 需要外置安全层才能用于高风险环境。 |
| 成熟度 | 事实｜v0.84.3 stable，公开仓库约一年 | 事实｜v0.1.1 RC，developer preview，公开仓库约 13 天 | 推断｜当前交付优先 Pi；DSH 更适合架构研究、试点和插件卡位，需预算 API churn。 |

## 5. 中文教程的可用部分、版本债与许可

- 【事实】`dg-ai-notes/pi-agent` 有两条路线：7 章实战与 10 章源码深潜；源码路线覆盖架构、Agent Loop、模型、工具、消息、事件、context、compaction 和 session。证据：[课程结构](https://github.com/buchidonggua/dg-ai-notes/blob/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf/pi-agent/README.md#L1-L48)。
- 【事实】`pi-agent-guide` 明确声明改编自 dg 教程，并采用“章节开头三个问题”、源码行号、进度等站点化设计。证据：[guide README](https://github.com/zhoujianbin/pi-agent-guide/blob/f838dd4a166d0130d8f5fa96db689a557ae6b5ff/README.md#L1-L30)。
- 【事实】两套内容都以 Pi v0.80.2 为源码基线；Pi 当前 stable 为 v0.84.3。因此旧教程的架构结论只能标为“对 v0.80.2 成立”，不能直接当作当前 main 的完整说明。证据：[dg 版本声明](https://github.com/buchidonggua/dg-ai-notes/blob/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf/pi-agent/pi_source_dive/typescript/%E7%AC%AC1%E7%AB%A0-%E5%BC%80%E7%AF%87-Pi-Agent%E6%A1%86%E6%9E%B6%E6%80%BB%E8%A7%88.md#L426-L428)、[guide 版本声明](https://github.com/zhoujianbin/pi-agent-guide/blob/f838dd4a166d0130d8f5fa96db689a557ae6b5ff/content/chapters/ch01.md#L236-L243)。
- 【事实】Pi 与 DSH 的代码均为 MIT；dg 教程文档和 guide 章节为 CC-BY-SA-4.0。若改编其表达、章节正文或图解，必须保留署名和相同方式共享；仅参考事实并独立研究、独立表达，也仍应给出清晰来源，但不要把第三方教程许可错误套到整站工程代码。证据：[Pi LICENSE](https://github.com/earendil-works/pi/blob/8fa7eebd235355522c8104166b4f1f959b4e2f10/LICENSE#L1-L20)、[DSH LICENSE](https://github.com/deepseek-ai/deepseek-harness/blob/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e/LICENSE#L1-L20)、[dg 许可](https://github.com/buchidonggua/dg-ai-notes/blob/5f4abd34d3d4d756e016b78bfbfe90d97cd9c7cf/pi-agent/README.md#L77-L80)、[guide 许可拆分](https://github.com/zhoujianbin/pi-agent-guide/blob/f838dd4a166d0130d8f5fa96db689a557ae6b5ff/README.md#L67-L78)。
- 【推断】站点页脚应拆分许可：自研前端代码、原创研究内容、改编内容、第三方源码引用和不纳入许可的运营素材分别声明；“MIT 项目”不意味着可以把 CC-BY-SA 教程正文换皮闭源。

## 6. 建议的学习知识库骨架

- 【推断】第 1 轨“看懂 primitives”：项目身份、`pi-ai` provider abstraction、消息转换、低层 Agent Loop、工具管道、event barrier；每章开头保留三个无答案问题。
- 【推断】第 2 轨“做成长对话”：coding-agent 的 overflow 分类、compaction cut point、retained tail、JSONL parent tree、branch summary，并提供可视化 session tree playground。
- 【推断】第 3 轨“追上当前源码”：专讲 v0.84.3 `AgentHarness` 的三类 store、facts、lanes、usage ledger、durable program counter、tool replay safety 和非目标；每一节附 v0.80.2 → v0.84.3 差分卡。
- 【推断】第 4 轨“生产边界”：permission、sandbox、secrets、provider retry、tool idempotency、telemetry、crash recovery 和测试；明确区分“Pi 已提供”“extension 可实现”“必须由外部基础设施承担”。
- 【推断】第 5 轨“DSH 对照”：Cordis service/event/effect、profile/bundle、turn-step-request、durable event log、surface replacement、跨 session fork；用同一个任务分别画 Pi 与 DSH 时序图。
- 【推断】推荐 14 章而非照搬旧十章：①仓库演化与许可；②pi-ai；③低层 Agent；④双层 loop；⑤tool pipeline；⑥消息与事件；⑦context/retry；⑧compaction；⑨session tree；⑩extensions/security；⑪current AgentHarness；⑫DSH Cordis；⑬同题对照实验；⑭部署、商业化与生产检查表。
- 【推断】每条源码结论都应链接到固定 commit，而不是 `main`；页面额外显示“验证版本、当前 latest release、最后复核日期”，发现版本漂移时自动标“待复核”，避免再次积累 v0.80.2 式隐性版本债。

## 7. 商业化机会与风险

- 【推断】机会 A：**Pi v0.84.3 中文源码学院 / 版本差分订阅**。免费层解释 primitives；付费层提供可运行 lab、版本 diff、测试题、架构评审和升级笔记。证据基础是现有中文教程停在 v0.80.2，而当前源码已增加 durable harness。
- 【推断】机会 B：**Pi 企业安全与治理套件**。围绕 policy、approval、sandbox、secret broker、audit、tool idempotency 和 deployment recipe 提供开源基础版 + 企业支持；卖点必须表述为“补齐官方明确未内建的安全边界”，不能暗示 Pi 官方背书。
- 【推断】机会 C：**vertical agent starter kits**。基于 Pi extensions、skills、prompts 和 `pi-ai` 做可审计的行业模板、培训和定制集成；商业价值来自领域工具/流程与维护，不是换皮 CLI。
- 【推断】机会 D：**DSH plugin/profile 工程与企业试点**。可优先布局企业 storage、policy、telemetry、provider routing、sandbox 与合规 profile；但报价和承诺要包含 RC/developer-preview 的迁移预算，暂不适合承诺稳定公共 API。
- 【推断】机会 E：**跨 harness 教学**。先用 Pi 建立 loop/tool/context/session 的直觉，再用 DSH 讲微内核、event sourcing 和 capability seam；这种递进比直接从 200+ package 的 DSH 开始更适合大多数学习者。
- 【事实】MIT 允许商业使用、修改和再分发，但仍需保留许可与版权声明；CC-BY-SA 改编内容还需署名与相同方式共享。商标、域名、官方合作关系和第三方服务条款是独立问题，不能由代码许可自动推出。证据见第 5 节许可证链接。

## 8. 证据边界与后续补验

- 【事实】本分片只做源码/官方文档静态核验，没有运行 Pi/DSH、没有执行崩溃注入或兼容性测试。因此“代码路径存在”不等于每种 provider、storage backend 和 recovery case 均已通过实测。
- 【事实】Pi 主分支提交 `8fa7eeb` 晚于 v0.84.3 release tag 的提交；本文关于当前导出面以该固定 main commit 为准，关于稳定版本状态以 v0.84.3 release 为准，两者没有混写成同一工件。
- 【事实】DSH `has_issues=false`；其 GitHub API 的 `open_issues=0` 不能用于成熟度比较。
- 【推断】上线知识库前的最小补验应包括：Pi 低层 loop 事件快照测试、parallel/sequential tool order、context overflow 自动压缩、session branch/reload、AgentHarness crash/replay；DSH 则应测试 durable chunk log、tool guard monotonicity、retry event、compaction orphan recovery 和 fork lineage。
- 【推断】涉及“生产可用”的页面文案应以这些运行验证和明确威胁模型为门槛；官方 README/源码能证明设计与实现入口，不能单独证明任意业务环境下的生产可靠性。
