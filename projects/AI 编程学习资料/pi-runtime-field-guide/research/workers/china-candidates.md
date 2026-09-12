# 中文平台候选发现分片：Pi Agent / Pi Agent Core / Pi Coding Agent

> Worker：`china_discovery`。本文件只推进到候选发现与 worker check，不做最终排名，不把搜索摘要写成已验收证据。冻结主题为 `earendil-works/pi`、`pi-agent-core`、`pi-coding-agent`、Pi Agent harness；显式排除 Raspberry Pi、币圈 Pi、圆周率与强化学习 Policy Iteration 的噪声。用途覆盖入门、源码/架构、扩展实战、踩坑、安全、商业化，以及 Pi 与 DeepSeek Harness（DSH）的比较。

## 真实 probe 与路由账本

访问日期统一为 `2026-08-26`（Asia/Shanghai）。

| route / platform | tool_readiness | bridge_state | auth_state | quota_state | authorization | probe_result | 观察 |
|---|---|---|---|---|---|---|---|
| `agent-reach doctor --json` | available | mixed | mixed | available/unknown | granted_for_current_task | success | GitHub、Bilibili、V2EX、Exa、Web 为 ok；小红书/Reddit 为 warn。 |
| `opencli doctor` | configured | disconnected | unknown | unknown | granted_for_current_task | blocked | daemon 1.8.6 正常；Chrome Extension 未连接，Browser Bridge connectivity failed。未安装/升级扩展。 |
| `bili search 'pi coding agent' --type video -n 20 --yaml` | available | not_required | anonymous | available | granted_for_current_task | success | 平台 API 返回 Pi 主题视频元数据；另以 `bili video BV139bD6gEa8 --yaml` 回读一条详情验证 URL、作者、描述和互动字段。 |
| `opencli v2ex topic 1229821 -f yaml` | available | not_required | anonymous | not_applicable | granted_for_current_task | success | 回读全文、作者、创建时间、回复数和 canonical URL。 |
| `opencli zhihu/weixin/xiaohongshu/linux-do search ...` | configured | disconnected | required/unknown | unknown | granted_for_current_task | blocked | 最小只读 probe 只出现 Node 启动告警后持续等待；结合 doctor 判定为 Browser Bridge 阻塞，已中止，不绕过。 |
| 公共原页 / Web 搜索索引 | available | not_required | anonymous | available | not_required | success | 用于 CSDN、知乎、掘金、Linux.do、InfoQ、SegmentFault、36氪、V2EX、Gitee 的发现与可见原页回读。搜索索引结果本身仅作 discovery。 |
| 百度 discovery | unknown | not_required | anonymous | unknown | not_required | partial | 无已验证百度专用后端；本轮用通用公开索引补中文发现，不能声称“百度直搜完成”。 |

## 平台覆盖终态（本分片）

| platform | status | candidate_count | 说明 / 缺口 |
|---|---:|---:|---|
| Bilibili | complete | 35 | 两类平台查询（核心/对比、扩展/实战）均成功；仅 1 条详情回读，其余是平台元数据候选，最终策展需逐条字幕/视频观察。 |
| CSDN | complete | 12 | 多个公开正文与作者索引可读；个别详情页超时，保留为 discovery-only。 |
| 掘金 | complete | 3 | 公开原文可读，含 Extension Runtime 验收与入门。 |
| 知乎 | complete | 5 | 公开专栏正文可读；未依赖 Browser Bridge。 |
| SegmentFault | complete | 7 | 公开原文可读，含完整指南、选型、Pi vs OMP。 |
| InfoQ | complete | 3 | 公开原文可读，含演讲整理、同模型 Harness 基准与企业讨论。 |
| Linux.do | complete | 8 | 公开索引可读取主题正文/回复；OpenCLI 登录路由阻塞，未读取登录限定内容。 |
| V2EX | complete | 6 | 公开 API/原页回读成功，含 Pi/DSH 一手社区比较、商业实战和扩展。 |
| 36氪 | complete | 5 | 公开报道可读，含商业化、成本、DSH 架构比较和真实工程案例。 |
| Gitee | partial | 2 | 召回一个同步仓库与一个基于 Pi 的项目 release；内容价值有限，不能替代 GitHub 官方源。 |
| 微信公众号 | blocked | 0 | OpenCLI Browser Bridge 未连接；公共搜索未召回可核对的公众号原文。登录接力后最小补验：`opencli weixin search 'Pi Agent earendil-works' --limit 3 -f yaml`。 |
| 小红书 | blocked | 0 | Bridge + 登录缺失；不绕过验证码。登录接力后最小补验：`opencli xiaohongshu search 'Pi Agent' --limit 5 -f yaml`。 |
| 微博 | blocked | 0 | Bridge 未连接，公共索引无稳定候选。最小补验：连接 Bridge 后只读 `opencli weibo search 'Pi Agent' --limit 5 -f yaml`。 |
| 抖音 | blocked | 0 | Bridge/登录不可用；不以搜索摘要编造视频内容。 |
| 快手 | blocked | 0 | 无专用适配器，公开索引未召回稳定主题页。 |
| 微信视频号 | blocked | 0 | 当前无只读搜索/详情适配器；需要用户提供公开视频链接或授权导出。 |
| 今日头条 | partial | 0 | `hot` 不是关键词搜索；公共索引未召回强相关原页。 |
| OSCHINA | partial | 0 | 两类公开索引查询均无严格主题命中。 |

## 去重候选池（86 条）

字段合同：`platform, title, url, author, date/unknown, content_type, why_relevant, excerpt_or_observation, evidence_grade, route, accessed_at`。`M`=已看到足以判断候选价值的公开正文/结构化详情；`D`=discovery-only，只有平台搜索元数据、作者索引或搜索结果可见，最终入榜前必须回源。

| id | platform | title | url | author | date | content_type | why_relevant | excerpt_or_observation | grade | route | accessed_at |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| CN-001 | Bilibili | Pi 大道至简，超越 Codex 和 Claude Code 的极简 Agent，保姆级全攻略 | https://www.bilibili.com/video/BV139bD6gEa8 | 技术爬爬虾 | unknown | video | 入门/架构/竞品对比 | 详情描述明确四个默认工具、短系统提示词和扩展生态；详情回读成功。 | M | `bili search` + `bili video` | 2026-08-26 |
| CN-002 | Bilibili | PI Agent 架构设计，TypeScript 100 行代码实现通用智能体 | https://www.bilibili.com/video/BV1jX8462EFb | 重生之我再干前端 | unknown | video | 从零实现/源码学习 | 平台元数据直接命中 PI-Agent 架构与 TypeScript 实践。 | D | `bili search` | 2026-08-26 |
| CN-003 | Bilibili | Pi Agent：比 Claude Code 和 Codex 更适合普通人的 AI 工具 | https://www.bilibili.com/video/BV15wGR6CEhY | 第四种黑猩猩CHIMP | unknown | video | 入门/选型 | 标题直接比较 Pi、Claude Code、Codex。 | D | `bili search` | 2026-08-26 |
| CN-004 | Bilibili | Pi Agent 从安装到配置保姆级全流程指南 | https://www.bilibili.com/video/BV1qy3E6LEKb | 晴天AI实战 | unknown | video | 入门/安装 | 平台元数据明确覆盖安装与配置。 | D | `bili search` | 2026-08-26 |
| CN-005 | Bilibili | VibeCoding 极简神器 Pi | https://www.bilibili.com/video/BV1LyuB6FEyv | 隔壁的程序员老王 | unknown | video | 入门/生产力 | 以 Vibe Coding 场景介绍 Pi。 | D | `bili search` | 2026-08-26 |
| CN-006 | Bilibili | Pi 为什么能打赢 Claude Code 和 Codex | https://www.bilibili.com/video/BV1akKp6eEVf | 第四种黑猩猩CHIMP | unknown | video | 竞品/性能 | 标题针对 Harness 差异与效果提出解释。 | D | `bili search` | 2026-08-26 |
| CN-007 | Bilibili | 告别玩具 Agent：从 Pi Harness V2 看懂智能体全景架构 | https://www.bilibili.com/video/BV1p68b6YEtE | 为什么叫QQ | unknown | video | 进阶/运行时架构 | 聚焦重启、并发与 Agent Runtime 设计规范。 | D | `bili search` | 2026-08-26 |
| CN-008 | Bilibili | Pi 和 DeepSeek Harness 的核心设计有什么不同 | https://www.bilibili.com/video/BV1CTbf6CEGu | YangAgent | unknown | video | Pi vs DSH | 本轮最直接的 Pi/DeepSeek Harness 设计对比视频。 | D | `bili search` | 2026-08-26 |
| CN-009 | Bilibili | DeepSeek Harness vs Pi Agent，同宗不同路你选谁 | https://www.bilibili.com/video/BV1qS8m6uE3V | 乾学AIAgent | unknown | video | Pi vs DSH | 明确对比两种 Harness 的选型边界。 | D | `bili search` | 2026-08-26 |
| CN-010 | Bilibili | 哦对了，我将 Pi 源码写成了一本书 | https://www.bilibili.com/video/BV12WK666EhM | 费曼学徒冬瓜 | unknown | video | 源码学习/知识产品 | 源码蒸馏成书，兼具进阶学习和潜在内容商业化信号。 | D | `bili search` | 2026-08-26 |
| CN-011 | Bilibili | Pi Agent 扩展实战：pi-hermes-memory | https://www.bilibili.com/video/BV1TUM26vEAC | 程序员暮闲 | unknown | video | 扩展/长期记忆 | 标题说明跨 Session 长期记忆与可复用 Skill。 | D | `bili search` | 2026-08-26 |
| CN-012 | Bilibili | 也许 Pi 是最接近 DeepSeek Harness 的 Harness？缓存命中最重要 | https://www.bilibili.com/video/BV1QwMU6yExQ | 朝霞alpenglow | unknown | video | Pi vs DSH/成本 | 直接把 Pi、DSH 和缓存命中率联系起来。 | D | `bili search` | 2026-08-26 |
| CN-013 | Bilibili | Pi Agent 最佳实践：Harness Agent 定制全流程实战 | https://www.bilibili.com/video/BV1ZnEJ6NEJ6 | 程序员暮闲 | unknown | video | 进阶/实战 | 明确是 Pi 定制全流程与最佳实践。 | D | `bili search` | 2026-08-26 |
| CN-014 | Bilibili | PI：pi-ai 与 pi-agent-core | https://www.bilibili.com/video/BV1wBfvBnEkY | 邓侃AI | unknown | video | 源码/分层 | 精确命中 pi-ai 与 pi-agent-core 两个核心包。 | D | `bili search` | 2026-08-26 |
| CN-015 | Bilibili | PI core Runloop | https://www.bilibili.com/video/BV1gwb96kERJ | AI_Julie | unknown | video | Agent Loop | 精确聚焦 pi-agent-core 的运行循环。 | D | `bili search` | 2026-08-26 |
| CN-016 | Bilibili | 2 分钟下载 Pi Agent 并接入 DeepSeek | https://www.bilibili.com/video/BV1j5NJ6AE6B | 正在进行深度烧烤 | unknown | video | 入门/DeepSeek 接入 | 快速配置 Pi + DeepSeek 的实操候选。 | D | `bili search` | 2026-08-26 |
| CN-017 | Bilibili | Pi Agent Harness：极简的 AI Agent 底座 | https://www.bilibili.com/video/BV12Kh36dEDD | AI璟礼 | unknown | video | 入门/定位 | 标题明确定位为极简 Agent Harness。 | D | `bili search` | 2026-08-26 |
| CN-018 | Bilibili | Pi Subagents：让多个 AI Agent 自动分工协作 | https://www.bilibili.com/video/BV1vL3o6UE5T | 程序员暮闲 | unknown | video | 扩展/多 Agent | 社区扩展的自动分工协作实践。 | D | `bili search` | 2026-08-26 |
| CN-019 | Bilibili | pi-dynamic-workflows：多个 Agent 动态编排、并行协作 | https://www.bilibili.com/video/BV11yM96nE45 | 程序员暮闲 | unknown | video | 扩展/工作流 | 进阶动态编排与并行协作。 | D | `bili search` | 2026-08-26 |
| CN-020 | Bilibili | Pi MCP Adapter 接入 MCP Server | https://www.bilibili.com/video/BV1WHGu6AEFp | 程序员暮闲 | unknown | video | 扩展/MCP | Pi 默认不内置 MCP，此视频展示扩展补齐路径。 | D | `bili search` | 2026-08-26 |
| CN-021 | Bilibili | 推荐一些 Pi Agent 插件 | https://www.bilibili.com/video/BV1k6E167Ext | 夜未央-天将亮 | unknown | video | 插件/技巧 | 插件生态策展候选。 | D | `bili search` | 2026-08-26 |
| CN-022 | Bilibili | pi-clean-tool-render：Pi Agent 插件分享 | https://www.bilibili.com/video/BV15WbB6GEXF | Runminton | unknown | video | 插件/UI | 工具输出渲染扩展。 | D | `bili search` | 2026-08-26 |
| CN-023 | Bilibili | plan-mode：先规划再动手 | https://www.bilibili.com/video/BV1iUbD6CEVY | 一起来亏钱 | unknown | video | 插件/规划 | 展示 Pi 以 Extension 补齐 plan mode。 | D | `bili search` | 2026-08-26 |
| CN-024 | Bilibili | pi-subagents：多 Agent 并行 | https://www.bilibili.com/video/BV1B8by6aER7 | 一起来亏钱 | unknown | video | 插件/多 Agent | 短视频快速展示 subagents 扩展。 | D | `bili search` | 2026-08-26 |
| CN-025 | Bilibili | pi-intercom：会话通信 | https://www.bilibili.com/video/BV1LUbD6CECH | 一起来亏钱 | unknown | video | 插件/会话 | 会话间通信是多 Agent 支撑能力。 | D | `bili search` | 2026-08-26 |
| CN-026 | Bilibili | pi-prompt-template-model：一个命令一个模型 | https://www.bilibili.com/video/BV1i4826KE2K | 一起来亏钱 | unknown | video | 插件/多模型 | 展示 Pi 的模型路由与提示模板组合。 | D | `bili search` | 2026-08-26 |
| CN-027 | Bilibili | pi-permission-system：给 AI 立规矩 | https://www.bilibili.com/video/BV1Ve826hE5t | 一起来亏钱 | unknown | video | 插件/安全 | Pi 无内置权限系统，此扩展是关键安全案例。 | D | `bili search` | 2026-08-26 |
| CN-028 | Bilibili | context-mode：省 98% 上下文 | https://www.bilibili.com/video/BV1HTb16TEGd | 一起来亏钱 | unknown | video | 插件/上下文 | 直接命中上下文压缩/节省主题。 | D | `bili search` | 2026-08-26 |
| CN-029 | Bilibili | 如何为 Pi Agent 配置本地大模型 | https://www.bilibili.com/video/BV1bsuJ6cEq6 | 退役程序员 | unknown | video | 本地模型/隐私 | 本地模型配置实操，适合低成本/私有化路径。 | D | `bili search` | 2026-08-26 |
| CN-030 | Bilibili | pi-deepseek-usage：余额看得见 | https://www.bilibili.com/video/BV1n7826GE2o | 一起来亏钱 | unknown | video | 成本/DeepSeek | 成本可观测的微型扩展。 | D | `bili search` | 2026-08-26 |
| CN-031 | Bilibili | pi-hashline-edit-pro：每行代码都有身份证 | https://www.bilibili.com/video/BV1aq826bEFW | 一起来亏钱 | unknown | video | 编辑工具/可靠性 | 展示替换/增强 edit 工具的工程路径。 | D | `bili search` | 2026-08-26 |
| CN-032 | Bilibili | pi-lens：给 AI 一双代码眼 | https://www.bilibili.com/video/BV1Ye826hETW | 一起来亏钱 | unknown | video | 代码理解/插件 | 针对代码观察能力的扩展候选。 | D | `bili search` | 2026-08-26 |
| CN-033 | Bilibili | pi-memory：AI 记忆扩展 | https://www.bilibili.com/video/BV1RDbD6GEk9 | 一起来亏钱 | unknown | video | 记忆/插件 | 社区长期记忆实现。 | D | `bili search` | 2026-08-26 |
| CN-034 | Bilibili | Pi Agent MCP 的演示使用 | https://www.bilibili.com/video/BV1Eyb86dEX5 | Iammyself001 | unknown | video | MCP/入门 | MCP 扩展的演示型内容。 | D | `bili search` | 2026-08-26 |
| CN-035 | Bilibili | Codex 没额度了，我用 Pi + DeepSeek V4 Flash 接过开发工作 | https://www.bilibili.com/video/BV1ct8T6AEW3 | 五里墩茶社 | unknown | video | 商业/成本/替代 | 以真实额度约束讨论 Pi + DeepSeek 的替代价值。 | D | `bili search` | 2026-08-26 |
| CN-036 | CSDN | Pi Agent Harness 架构解析：一个轻量可扩展的 Agent 开发底座 | https://blog.csdn.net/zzzzz77777aaaaaa/article/details/163392731 | 程序员z7 | 2026-08-19 | article | 架构/入门 | 正文分解 pi-ai、pi-agent-core、pi-tui、pi-coding-agent，涵盖会话树、安全和部署。 | M | public original page | 2026-08-26 |
| CN-037 | CSDN | PI-Agent：像水一样的智能体内核 | https://blog.csdn.net/qq_34167192/article/details/160087942 | AI案例薄 | 2026-08-03 | article | 轻量 SDK/会话 | 正文用 Prompt、Steer、FollowUp 解释核心动作并给出 Session 代码。 | M | public original page | 2026-08-26 |
| CN-038 | CSDN | Pi Agent 生态实战指南：从安全配置到技能开发 | https://blog.csdn.net/weixin_28745525/article/details/160639787 | 血管瘤专家孔强 | 2026-08-19 | article | 扩展/安全/成本 | 正文讨论安全过滤、成本面板、checkpoint 和 awesome-pi-agent。 | M | public original page | 2026-08-26 |
| CN-039 | CSDN | 从 0 到 1 精通 dg-ai-notes：Pi-Agent 框架总览与核心功能解析 | https://blog.csdn.net/gitblog_00801/article/details/155672879 | gitblog_00801 | unknown | article | 中文学习路线 | 精确命中用户提到的 dg-ai-notes 教程与 Pi 源码学习。 | M | public original page | 2026-08-26 |
| CN-040 | CSDN | Pi-Agent 深度硬核解析：极简主义编程智能体，OpenClaw 底层内核源码剖析 | https://kaola.blog.csdn.net/article/details/163912508 | 考拉搞AI | 2026-08-20 | article | 源码/架构/选型 | 作者索引摘要明确定位 Harness，并比较 Claude Code、Codex。详情抓取超时。 | D | public author index; detail timeout | 2026-08-26 |
| CN-041 | CSDN | Pi Agent 编程接口与架构深度解析，将 Pi 集成到自有应用 | https://yychan.blog.csdn.net/article/details/163966176 | 猿与禅 | 2026-08-22 | article | SDK/RPC/会话树 | 作者索引摘要覆盖 SDK、RPC、JSON 事件流、TUI、JSONL 会话树和压缩。详情抓取超时。 | D | public author index; detail timeout | 2026-08-26 |
| CN-042 | CSDN | Pi Agent 自定义扩展与高级技巧：打造专属 AI 编程工作流 | https://yychan.blog.csdn.net/article/details/163935770 | 猿与禅 | 2026-08-21 | article | Extension/Skills | 摘要覆盖工具、命令、事件、Skills、主题、Provider 和热重载。 | D | public author index; detail timeout | 2026-08-26 |
| CN-043 | CSDN | Pi Agent 入门与核心使用指南 | https://yychan.blog.csdn.net/article/details/163904611 | 猿与禅 | 2026-08-20 | article | 入门/会话/压缩 | 摘要覆盖安装、认证、树状会话、上下文压缩和本地模型。 | D | public author index; detail timeout | 2026-08-26 |
| CN-044 | CSDN | pi-agent：循环维护、上下文工程与工具调用管理 | https://lvynote.blog.csdn.net/article/details/163051364 | lvy | 2026-07-20 | article | Agent Loop/可靠性 | 摘要直接命中循环干预、上下文压缩、参数兜底、安全和错误回灌。 | D | public author index; detail timeout | 2026-08-26 |
| CN-045 | CSDN DevPress | OpenCode、Pi 与 Goose：开源 AI Agent 栈的三个层级 | https://devpress.csdn.net/v1/article/detail/162597236 | 一铭 | unknown | article | 选型/生态 | 把 Pi 定位为 agent harness/toolkit，适合解释与成品 Agent 的层级差异。 | M | public original page | 2026-08-26 |
| CN-046 | CSDN DevPress | 收藏！轻松入门 AI Agent：Pi Agent 框架带你玩转大模型 | https://devpress.csdn.net/v1/article/detail/162340648 | 耿直学编程 | unknown | article | 入门 | 公开正文以“核心只做最必要的事、其余交给扩展”解释上手价值。 | M | public original page | 2026-08-26 |
| CN-047 | CSDN / AtomGit | 什么是 Pi？下一代 Agent 架构？ | https://gitcode.csdn.net/69b8fd6e0a2f6a37c5981268.html | 发菜君 | unknown | article | 入门/架构 | 公开正文介绍四工具、树状历史、扩展系统与竞品差异。 | M | public original page | 2026-08-26 |
| CN-048 | 掘金 | Pi Extension 写完不等于可用：从类型检查到真实 Runtime 的证据阶梯 | https://juejin.cn/post/7675622412803358774 | 武子康 | 2026-08-20 | article | Extension/测试/安全 | 正文给出类型检查、Mock、真实 RPC、TUI、模型路径和生产安全六层验收。 | M | public original page | 2026-08-26 |
| CN-049 | 掘金 | Pi Coding Agent：属于你的终端 AI 编码助手 | https://juejin.cn/post/7645239491757621257 | Peppa_ | 2026-05-30 | article | 入门/中文文档 | 正文覆盖安装、运行模式、会话树、上下文工程、扩展，并指向中文文档站。 | M | public original page | 2026-08-26 |
| CN-050 | 掘金 | OpenClaw 架构浅析：pi-ai、pi-agent-core、pi-coding-agent | https://juejin.cn/post/7611732636969287695 | unknown | unknown | article | 架构/生态 | 正文列出 Pi 各包职责、工具执行、事件流和 OpenClaw 依赖关系。 | M | public original page | 2026-08-26 |
| CN-051 | 知乎 | OpenClaw 背后核心框架 Pi：好的 Coding Agent 应该让用户决定需要什么 | https://zhuanlan.zhihu.com/p/2017400881730056207 | Founder Park | 2026-03-18 | article/interview | 设计哲学/一手访谈 | 公开正文整理 Mario 和深度用户访谈，涵盖极简、扩展、会话树、SubAgent、安全与记忆。 | M | public original page | 2026-08-26 |
| CN-052 | 知乎 | OpenClaw 技术解构：从 WhatsApp 聊天机器人到 AI 操作系统 | https://zhuanlan.zhihu.com/p/2014274873778786410 | unknown | unknown | article | pi-agent-core/会话树 | 正文明确 `pi-agent-core` 循环、TypeBox 工具校验、SessionManager JSONL 树与上下文管线。 | M | public original page | 2026-08-26 |
| CN-053 | 知乎 | 关于 OpenClaw：核心架构、Agent 部署、精细化管控和安全风险 | https://zhuanlan.zhihu.com/p/2014351352076183211 | unknown | unknown | article | Pi SDK/生产 | 公开代码片段展示 `createAgentSession`、SessionManager 和 embedded runner 组装。 | M | public original page | 2026-08-26 |
| CN-054 | 知乎 | 详尽从零开始设计实现一个 AI Agent 框架 | https://zhuanlan.zhihu.com/p/2027029874909397801 | 腾讯技术工程 / yabohe | 2026-04-13 | article | 从零实现/停止条件 | 正文展示 MAX_TURNS、无 tool_calls 停止、工具失败回灌，并以 Pi 四工具做参照。 | M | public original page | 2026-08-26 |
| CN-055 | 知乎 | OpenClaw 实践与 AI Agent 发展思考 | https://zhuanlan.zhihu.com/p/2017644431591899897 | unknown | unknown | article | 商业化/生态 | 从 Coding Agent、Skills、Context Engineering 讨论 Pi 作为智能体开发底座的生态位置。 | M | public original page | 2026-08-26 |
| CN-056 | SegmentFault | Pi：不止编程，一套通用 Agent 框架 | https://segmentfault.com/a/1190000048056072 | RobinDevNotes | 2026-07-21 | article | 四包架构/供应链/商业嵌入 | 正文覆盖四包独立组合、供应链安全、权限诚实、SDK 嵌入和 pi-chat/记忆生态。 | M | public original page | 2026-08-26 |
| CN-057 | SegmentFault | 9 款 Coding Agent Harness 选型指南 | https://segmentfault.com/a/1190000048153930 | cc的ai coding实践 | 2026-08 | article | 选型/成本/商业 | Pi 条目含版本、协议、Provider、成本和安全边界。 | M | public original page | 2026-08-26 |
| CN-058 | SegmentFault | OpenClaw 技术解构：Pi Agent Runtime | https://segmentfault.com/a/1190000047640906 | 葡萄城技术团队 | 2026-03 | article | Agent Loop/会话 | 正文解释流事件、工具顺序执行、SessionManager JSONL 与 context transform。 | M | public original page | 2026-08-26 |
| CN-059 | SegmentFault | Pi Agent 完整指南：从安装到 Extension 开发 | https://segmentfault.com/a/1190000048176674 | 七牛云行业应用 | 2026-08-19 | article | 全栈指南/Pi vs DSH | 覆盖安装认证、四模式、会话树、Extension、安全隔离和 Pi/DSH 选型；需复核其中个别营销性断言。 | M | public original page | 2026-08-26 |
| CN-060 | SegmentFault | 2026 年 AI 编程的玩法变了，不是选工具的事了 | https://segmentfault.com/a/1190000047873114 | 知悟之旅 | 2026-06 | article | 竞品/生产力 | 把 Pi 放在 Claude Code、Cursor、Codex 等选型矩阵。 | M | public original page | 2026-08-26 |
| CN-061 | SegmentFault | 终端 AI 编程的两条路：Pi 极简哲学 vs Oh-My-Pi 全能主义 | https://segmentfault.com/a/1190000047814238 | 鸿枫 | 2026-06-03 | article | Pi vs OMP | 适合解释极简 Pi 与全能 fork 的产品策略差异。 | M | public original page | 2026-08-26 |
| CN-062 | SegmentFault | OpenClaw Agent 与 Skill 架构详解 | https://segmentfault.com/a/1190000047691254 | 京东云技术新知 | 2026-04 | article | SDK/生态 | 公开正文列出 `createAgentSession`、SessionManager、AuthStorage、ModelRegistry 等 SDK 组件。 | M | public original page | 2026-08-26 |
| CN-063 | InfoQ | DeepSeek + Pi 跑赢 Claude Code？同模型 8 Harness 对比 | https://www.infoq.cn/article/XpFUaftcEE3iLgGzYGZi | unknown | 2026-08 | report | 基准/成本/商业 | 报道 Composio 的 30 任务对比：Pi 20/30；适合研究同模型下 Harness 影响，但最终需回到原始基准。 | M | public original page | 2026-08-26 |
| CN-064 | InfoQ | 写了 17 年开源代码，我为什么认为 Coding Agents 堆功能是在瞎折腾 | https://www.infoq.cn/article/sLVv23TfVFxoBPjNwcZI | 傅宇琪 / Tina | 2026-04-29 | talk recap | 设计哲学/一手演讲 | Mario 演讲整理，含四包、短提示、Extension、树会话和安全观点。 | M | public original page | 2026-08-26 |
| CN-065 | InfoQ | OpenClaw 走红背后：Agent、AI Coding 与团队协作的新问题 | https://www.infoq.cn/article/D8E3q93kBviq8Z8mu0Ao | unknown | 2026-04 | panel/report | 企业落地/商业化 | 讨论网易等团队直接基于 Pi Agent Core 二开桌面 Agent，以及何时无需重复造轮子。 | M | public original page | 2026-08-26 |
| CN-066 | Linux.do | Pi + DeepSeek V4 Flash，用起来好爽 | https://linux.do/t/topic/2712169 | cxuanAI | 2026-08-06 | forum/article | 配置/实战/成本 | 正文给出 models.json Provider 配置、thinking、会话树命令和真实开发任务。 | M | public indexed original page | 2026-08-26 |
| CN-067 | Linux.do | 现在开发 Agent 应该用 LangGraph 还是 pi-agent-core / DSH | https://linux.do/t/topic/2786114 | buer12138 | 2026-08-21 | forum | 框架选型 | 公开回复直接提出 pi-agent-core 与 DSH 作为新 Harness 底座，与 LangGraph 工作流边界对照。 | M | public indexed original page | 2026-08-26 |
| CN-068 | Linux.do | DeepSeek Harness 和 Codex 用哪个好 | https://linux.do/t/topic/2799206 | Erik123 | 2026-08-24 | forum | Pi/DSH/模型选型 | 回复包含 Pi + DeepSeek V4 Flash、DSH 对 DS 模型特化、Codex 工作流等多方一手体验。 | M | public indexed original page | 2026-08-26 |
| CN-069 | Linux.do | DeepSeek Harness 轻度体验中，佬友们感觉如何 | https://linux.do/t/topic/2752077 | DrPeper | 2026-08-13 | forum | DSH 踩坑/Pi 对照 | 公开讨论插件化、第三方 Provider、缓存、子 Agent 成本，并类比“Pi 套 WebUI”。 | M | public indexed original page | 2026-08-26 |
| CN-070 | Linux.do | 利用 PWA 封装 DeepSeek Harness 桌面 App | https://linux.do/t/topic/2761422 | unknown | 2026-08-16 | forum/tutorial | DSH/Pi GUI | 正文补充 Pi GUI `pi-web` 同样支持 PWA，适合 GUI/产品化旁证。 | M | public indexed original page | 2026-08-26 |
| CN-071 | Linux.do | DeepSeek Harness 发布前后：是否基于 Pi 二次开发 | https://linux.do/t/topic/2748020 | kant 等 | 2026-08-13 | forum | 来源/比较 | 社区讨论 DSH 与 Pi 代码关系；属于传闻与早期观察，须以仓库源码核验。 | M | public indexed original page | 2026-08-26 |
| CN-072 | Linux.do | DeepSeek Harness 到底想解决什么问题 | https://linux.do/t/topic/2756656 | unknown | 2026-08-14 | forum | Pi vs DSH/产品定位 | 公开讨论总结“Pi 扩展 Coding Agent，DSH 解决 DeepSeek 自有 Harness 与产品插件化”。 | M | public indexed original page | 2026-08-26 |
| CN-073 | Linux.do | 同模型在 Pi 与 OpenCode 中表现差异：Harness 提示影响 | https://linux.do/t/topic/2733445?page=4 | lime_ha 等 | 2026-08-10 | forum | Harness 影响/反例 | 回复指出同一 DeepSeek 模型在 Pi/OpenCode 中受 harness prompt 影响且表现不稳定。 | M | public indexed original page | 2026-08-26 |
| CN-074 | V2EX | Pi Coding Agent | https://www.v2ex.com/t/1229821 | Livid | 2026-07-26 | forum/tutorial | Provider 配置/商业 API | V2EX API 全文回读成功，给出自有 AI Persona Provider 与三模型配置，展示 Pi 的模型接入商业化场景。 | M | `opencli v2ex topic` | 2026-08-26 |
| CN-075 | V2EX | Pi 体验如何，大家现在生产主力是什么 | https://www.v2ex.com/t/1235481 | Geon97 | 2026-08-20 | forum | 生产实践/踩坑 | 公开回复包含 Pi 插件冲突、注意力稀释、长程任务、模型分工、运维裸 Pi 等一手体验。 | M | public original page | 2026-08-26 |
| CN-076 | V2EX | 各位 Pi 选手转 DSH 了吗 | https://www.v2ex.com/t/1234716 | DiKaErJi | 2026-08-23 | forum | Pi vs DSH | 51 回复讨论 DSH 极简模式、缓存、插件、模型特化、Pi 多模型中立性与迁移成本。 | M | public original page | 2026-08-26 |
| CN-077 | V2EX | 做了个 Pi Agent 的自动审批扩展 | https://www.v2ex.com/t/1226191 | Reach | 2026-07-09 | forum/project | Extension/审批 | 一手作者说明为 Pi 补齐 Claude Code/Codex 风格自动审批的动机与实现。 | M | public original page | 2026-08-26 |
| CN-078 | V2EX | 开发了自用的 Claw：微信 + Docker + Pi Code Agent + Cron | https://www.v2ex.com/t/1202087 | achangzhou | 2026-03-31 | forum/project | 商业化/产品实战 | 一手项目把微信、Docker、Pi Code Agent 与定时任务组合成个人产品。 | M | public original page | 2026-08-26 |
| CN-079 | V2EX | Wolf RBAC：40 美元 vibe coding，给开源权限系统接了 Pi Agent | https://fast.v2ex.com/t/1218511 | igeeky | 2026-06-07 | forum/case study | 企业嵌入/ROI | 作者说明基于 pi-agent-core + pi-ai 复用 Controller，并给出约 25M tokens 与 40 美元成本。 | M | public original page | 2026-08-26 |
| CN-080 | 36氪 | DeepSeek + Pi 王炸组合跑赢 Claude Code？ | https://36kr.com/p/3936187229142153 | unknown | 2026-08 | report | 基准/商业 | 报道同模型多 Harness 基准，Pi 20/30；需追 Composio 原始测试复核。 | M | public original page | 2026-08-26 |
| CN-081 | 36氪 | DeepSeek Harness 来了，它不想做下一个 Codex | https://www.36kr.com/p/3938529497562503 | unknown | 2026-08 | report | Pi vs DSH/架构 | 核心比较：Pi 让 Coding Agent 任意扩展，DSH 让整个 Agent 产品由插件重组。 | M | public original page | 2026-08-26 |
| CN-082 | 36氪 | 写了 17 年开源代码，我为什么认为 Coding Agents 堆功能是在瞎折腾 | https://www.36kr.com/p/3784634069277961 | 极客邦科技InfoQ | 2026-04-27 | syndicated talk recap | 设计哲学/扩展 | 演讲整理详述四工具、扩展、会话树、容器与可观察性；与 InfoQ 同稿簇，最终去重保留首发。 | M | public original page | 2026-08-26 |
| CN-083 | 36氪 | 2016 款吃灰 Mac 被 AI 救活：用 Pi Agent 做 FreeBSD Wi-Fi 驱动 | https://36kr.com/p/3708436235694210 | unknown | 2026-03 | case study | 真实工程/失败复盘 | 先直接改代码失败，后让 Pi 生成芯片规范并用多模型校验，体现 artifact-first 与独立验证。 | M | public original page | 2026-08-26 |
| CN-084 | 36氪 | 黑鲸之后，OpenAI 开放 Harness，争夺 Agent 运行时 | https://www.36kr.com/p/3952749463895174 | unknown | 2026-08-24 | analysis | 商业竞争/Pi vs DSH | 比较 Pi MIT 运行时与 DSH Cordis 插件化，并记录 DSH 早期预览与规模/历史透明度争议。 | M | public original page | 2026-08-26 |
| CN-085 | Gitee | jianyuan/pi：同步 earendil-works/pi 的 Gitee 镜像 | https://gitee.com/jianyuan/pi | jianyuan | unknown | repository mirror | 国内代码发现 | 项目索引明确“同步 https://github.com/earendil-works/pi”；仅作国内镜像线索，官方 GitHub 仍是真源。 | D | public Gitee index | 2026-08-26 |
| CN-086 | Gitee | Feynman Releases：基于 Pi Runtime 的研究 Agent 产品 | https://gitee.com/yonja/feynman/blob/main/RELEASES.md | Yonja | 2026-06 | release notes | 产品化/扩展/兼容 | Release 记录 Pi 版本升级、扩展加载、subagent、研究工作流、兼容补丁和真实 smoke，展示基于 Pi 商业/产品化的维护成本。 | M | public original page | 2026-08-26 |

## Worker 级去重与风险提示

- 86 条 URL 唯一；同一 Bilibili 视频的多查询重复已按 BV 号合并。
- CN-064 与 CN-082 是 InfoQ/36氪转载簇；最终策展应保留 InfoQ 或演讲原视频为代表，不可双计。
- CN-063 与 CN-080 都报道同一 Composio benchmark；排名前应回到原始实验、任务集与计分记录，不把媒体复述当两份独立证据。
- CSDN/DevPress 存在标题模板化、作者归属不清和事实误写风险；CN-040 至 CN-044 为 discovery-only，必须回读全文并对照固定 Pi tag/源码。
- Bilibili 除 CN-001 外尚未读取字幕或完整视频，只能作为标题/平台元数据候选，不能据此引用具体技术结论。
- Linux.do、V2EX 是社区一手体验，但存在样本偏差；成本、性能、模型“加成”等结论必须与官方代码、基准或可复现实验交叉核对。
- Gitee 镜像不是官方源，不能用于“最新版”或源码归属结论。

## 登录接力最小补验

Browser Bridge 当前未连接；若主任务决定补齐受阻平台，请让用户连接/登录 OpenCLI 使用的 Chrome profile，保持 Chrome 与扩展在线，并回复“已完成登录接力：微信/知乎/小红书/微博/抖音”。恢复后只重跑对应平台最小 probe，不重跑本文件已完成的平台和 query。
