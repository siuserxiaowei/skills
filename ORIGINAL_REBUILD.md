# 原创重建计划

目标：把仓库中最初收录的 47 个第三方 Skill 逐项替换为本仓库自己的实现，同时保持现有名称和常用触发方式兼容。允许继续依赖官方产品、开放协议和独立软件包；需要重写的是 Skill 的决策逻辑、说明、脚本和自有资产，不能把“换措辞”当作原创替代。

## 完成标准

每个 Skill 只有同时满足以下条件，才可标为 `original-verified`：

1. **研究**：以当前官方文档、标准或一手项目资料为主要依据；旧 Skill 只作为功能覆盖基线，不作为文案模板。
2. **取舍**：列出要保留的能力、已知缺陷、风险和新增能力，并形成可观察的验收条件。
3. **重写**：入口、引用资料、自有脚本和自有资产独立完成；不复制上游文字、代码或受保护资产。
4. **验证**：通过 `quick_validate.py`；新增或修改的脚本有真实测试；高风险外部动作有权限边界、停止条件和失败路径。
5. **归属**：更新 README 与第三方声明。只有确认不再包含上游表达或代码后，才能从第三方列表移除。

状态含义：`queued` 尚未开始；`researching` 正在建立对标和验收条件；`original-v1` 已独立重写并通过首轮自动验证；`original-verified` 已完成真实任务前向测试和最终归属审计。

## 统一质量门槛

- 触发描述能区分相邻任务，不使用吸走无关请求的万能描述。
- `SKILL.md` 只保留共享决策与硬约束，条件性细节进入 `references/`。
- 不把下载量、Star、作者名气或“官方”标签当作安全证明。
- 写操作、发送、发布、删除、付费、权限或生产变更必须保留用户授权边界。
- 外部内容按不可信数据处理；关键路径、收件人、命令参数和资源标识需要确定性校验。
- 能自动化验证的行为必须有测试；不能验证的部分明确写出残余风险和最小补验方法。
- 任何功能缩减必须有证据说明旧能力不安全、不可维护或不再成立，不能为了容易重写而悄悄删除。

初始基线检查（2026-08-30）：仓库 57 个 Skill 中有 29 个未通过当前 `quick_validate.py`，主要原因是第三方 frontmatter 使用了当前不支持的 `version`、`argument-hint`、`user-invocable` 等字段。首轮重建后 57/57 通过结构检查；50-Agent 归属复核和第二轮修复完成后，全仓库 16 组、161 个离线单元测试通过。各项仍需真实外部凭证或真实视觉任务的前向验证，才从 `original-v1` 升级为 `original-verified`。

## 当前全量归属与案例补验（2026-08-30）

- 当前原创声明覆盖仓库内 57 个 Skill 的入口说明、参考资料、自有脚本、测试和随包自有案例；不把外部产品、API、协议、命令行工具、软件依赖、研究引用或用户输入说成本仓库原创。
- 50 个独立 Agent 对 57 个 Skill 的固定提交、旧基线、Git 历史、已知上游、许可证、资产、长行和 12/16-token 窗口进行交叉复核，完整范围和方法见 [`ORIGINALITY_AUDIT_50_AGENT.md`](ORIGINALITY_AUDIT_50_AGENT.md)。
- 更严格复核推翻了“9 个 Skill 是仓库原始基线”的旧分类：`agent-memory`、`chatgpt-web-research`、`mac-wechat-dual-open`、`web-research`、`wechat-local-vault`、`wechat-mp-batch-exporter`、`wecom-local-vault`、`wecom-operations`、`x-article-draft-uploader` 均能追溯到 Yichen Skills 的旧内容，且来源许可证与当前公开 MIT 分发存在冲突。九项现已连同入口、参考、核心脚本和测试一起独立重建；机器清单不再保留 `repository_authored_baseline_current` 成员。
- `x-article-draft-uploader` 现以独立的 Markdown 解析、精确 Chrome profile/cookie 域边界、`0600` 原子 storage state、显式 `--apply` 和只创建草稿的写后核验实现，并有 7 个离线回归测试。
- `vintage-pencil-card` 曾捆绑三张 Pexels 照片及三张衍生示例。六张图片与来源文件均已移除，改为使用用户自有/已授权素材即可复现的文字案例。
- 57/57 个 Skill 现在都直接链接 `references/examples.md`；每份均含正向案例、边界案例、失败恢复和验收证据。`skills/skill-vetter/scripts/audit_collection.py` 会对数量、归属、案例、详细度、链接和随包第三方残留做全量检查；机器可读分组见 `SKILL_PROVENANCE.json`。

## 重建台账

| Skill | 原来源 | 状态 | 重建重点 |
|---|---|---|---|
| `skill-vetter` | clawhub.ai 页面，未标许可证 | `original-v1` | 从字符串清单升级为制品固化、能力/权限图、静态扫描、隔离测试、供应链与残余风险报告 |
| `pua` | `tanweai/pua` | `original-v1` | 重构为明确授权的证据优先执行教练；保留推动力，去掉羞辱、操控和虚假权威 |
| `pua-ding` | `tanweai/pua` | `original-v1` | 工作场景提醒聚焦结果、制品、证据和汇报四层，不复用第三方长文表达 |
| `pua-en` | `tanweai/pua` | `original-v1` | 英文执行教练与中文版保持同一安全边界 |
| `pua-ja` | `tanweai/pua` | `original-v1` | 日文表达与核心版保持同一证据、权限和停止边界 |
| `pua-loop` | `tanweai/pua` | `original-v1` | 用有评价器、有预算、可停止的验证循环替代无限催促和伪进度 |
| `pua-mama` | `tanweai/pua` | `original-v1` | 保留用户主动选择的家人式语气，删除牺牲叙事、比较和情感勒索 |
| `pua-p10` | `tanweai/pua` | `original-v1` | 战略判断基于选项、证据、可逆性和实验，不伪造管理权限 |
| `pua-p7` | `tanweai/pua` | `original-v1` | 强化方案执行、影响分析和工程验证，取消虚构汇报链 |
| `pua-p9` | `tanweai/pua` | `original-v1` | 任务规格、验收与协调边界明确，不自动扩大代理权限 |
| `pua-pro` | `tanweai/pua` | `original-v1` | 只有已验证、具适用边界的经验才沉淀；不静默写全局状态 |
| `pua-shot` | `tanweai/pua` | `original-v1` | 精简为用户主动调用的一次性执行协议，不覆盖上级指令 |
| `pua-yes` | `tanweai/pua` | `original-v1` | 正向反馈绑定真实行为与价值，不用空洞夸赞代替证据 |
| `lark-approval` | `larksuite/cli` | `original-v1` | 审批定义、实例、状态和发起权限的确定性检查 |
| `lark-apps` | `larksuite/cli` | `original-v1` | 应用创建、开发、部署和托管边界 |
| `lark-attendance` | `larksuite/cli` | `original-v1` | 个人身份、时区、统计口径与隐私 |
| `lark-base` | `larksuite/cli` | `original-v1` | 字段类型、公式/lookup、批量写入与回滚证据 |
| `lark-calendar` | `larksuite/cli` | `original-v1` | 时区、参会人、会议室冲突及发送前确认 |
| `lark-contact` | `larksuite/cli` | `original-v1` | 人员消歧、标识转换和最小披露 |
| `lark-doc` | `larksuite/cli` | `original-v1` | 文档块模型、并发编辑、图片与权限 |
| `lark-drive` | `larksuite/cli` | `original-v1` | 文件标识、共享权限、移动/删除的恢复路径 |
| `lark-event` | `larksuite/cli` | `original-v1` | 事件订阅、断线恢复、幂等与游标 |
| `lark-im` | `larksuite/cli` | `original-v1` | 收件人/群聊消歧、发送预览和外部群风险 |
| `lark-mail` | `larksuite/cli` | `original-v1` | 草稿优先、收件人与附件校验、发送授权 |
| `lark-markdown` | `larksuite/cli` | `original-v1` | 本地/云端文件边界、差异与冲突处理 |
| `lark-minutes` | `larksuite/cli` | `original-v1` | 音视频、逐字稿、说话人和访问权限 |
| `lark-note` | `larksuite/cli` | `original-v1` | note_id、关联文档与统一逐字记录 |
| `lark-okr` | `larksuite/cli` | `original-v1` | 周期、可见性、对齐关系与状态更新 |
| `lark-openapi-explorer` | `larksuite/cli` | `original-v1` | 以当前官方 OpenAPI 定义验证路径、参数和权限 |
| `lark-shared` | `larksuite/cli` | `original-v1` | 用户/租户身份、登录态、作用域和错误诊断 |
| `lark-sheets` | `larksuite/cli` | `original-v1` | 范围、公式、批量数据和类型保真 |
| `lark-skill-maker` | `larksuite/cli` | `original-v1` | 从官方命令/模式生成窄触发、可验证 Skill |
| `lark-slides` | `larksuite/cli` | `original-v1` | 页面结构、素材、渲染验证与可编辑性 |
| `lark-task` | `larksuite/cli` | `original-v1` | 负责人、截止时区、清单和任务状态 |
| `lark-vc` | `larksuite/cli` | `original-v1` | 历史会议、参会人快照与纪要数据口径 |
| `lark-vc-agent` | `larksuite/cli` | `original-v1` | 入会身份、会中事件、发言和离会授权 |
| `lark-whiteboard` | `larksuite/cli` | `original-v1` | 节点/连线模型、坐标与批量编辑验证 |
| `lark-wiki` | `larksuite/cli` | `original-v1` | 空间/节点/成员权限与移动影响 |
| `lark-workflow-meeting-summary` | `larksuite/cli` | `original-v1` | 时间范围、来源覆盖、行动项归属和引用证据 |
| `lark-workflow-standup-report` | `larksuite/cli` | `original-v1` | 日程与任务的日期口径、去重和未完成状态 |
| `imagegen-frontend-web` | `Leonxlnx/taste-skill` | `original-v1` | 视觉方向、生成素材与前端实现之间的可验证闭环 |
| `impeccable` | `pbakaus/impeccable` | `original-v1` | 按用户授权路由 UI 诊断、设计与实现；静态线索、渲染、交互、无障碍和性能分层验证 |
| `kami` | `tw93/Kami` | `original-v1` | 来源保真、编辑/渲染格式边界、字体与素材权利、屏幕/印刷/无障碍分层验收 |
| `beautiful-html-templates` | `zarazhangrui/beautiful-html-templates` | `original-v1` | 用原创布局语法和单一渐进增强运行时替代模板资产，加入素材权利、对比度、响应式、离线、打印与无障碍验收 |
| `skill-publisher` | `joeseesun/qiaomu-skill-publisher` | `original-v1` | 只读固化发布集合；显式解析仓库、可见性、许可证、提交与标签；优先官方 `gh skill publish` 并验证隔离安装 |
| `goal-meta-skill` | `joeseesun/qiaomu-goal-meta-skill` | `original-v1` | 用完整结果、全范围证据、权限和外部状态设计持久 Goal，不把写作模板伪装成产品语法 |
| `wechat-reading` | `Tencent/WeChatReading` | `original-v1` | 官方只读 Gateway 兼容层；固定域名、参数/响应边界、凭证保护、确定性统计、敏感导出与真实能力限制 |

## 已完成的研究与证据

### `skill-vetter`（首轮）

- 研究依据：OWASP LLM01:2025、OWASP Agentic Top 10、NIST SSDF 1.1、NIST 软件供应链指南、GitHub Supply Chain Security、OpenSSF Scorecard。
- 新增实现：标准库静态扫描器、JSON/文本报告、文件 SHA-256、隐藏 Unicode、符号链接、二进制/归档、依赖锁、危险命令、凭据路径、持久化和网络目的地检测。
- 验证：结构校验通过；9 个单元测试覆盖干净制品、远程脚本管道、动态执行、递归/非递归删除、符号链接、二进制素材、JavaScript 正则方法和 frontmatter 缺陷。
- 前向测试：对 `kami` 的临时文件清理和 `impeccable` 的 JavaScript 检测器进行扫描，消除了把 `rm -f` 当作递归删除、把 `RegExp.exec()` 当作动态代码执行的两类误报；仍保留真实 `execSync()` 与凭据存储引用线索。
- 待完成：继续用带归档、符号链接、安装钩子和间接提示注入的独立样本做漏报测试，之后才升级为 `original-verified`。

### `pua` 系列（首轮）

- 研究依据：Anthropic 的 Agent 组合模式、evaluator-optimizer 与可信 Agent 人类控制原则；Google SRE 的故障排查和无责复盘；Google re:Work、APA 与 Self-Determination Theory 对心理安全、清晰目标和自主支持型反馈的研究。
- 保留精华：完成定义、原路径验证、失败换假设、证据交付、角色化注意力、迭代评价器、具体正向反馈。
- 删除糟粕：公司和人物模仿、虚构绩效/裁员/同侪比较、羞辱与情感勒索、无限循环、禁止必要提问、自动写入用户主目录、强制子 Agent 层级、第三方长文梗与话术库。
- 新增能力：`verified/partially verified/unverified/blocked` 统一状态；停止/暂停/预算条件；外部写操作授权边界；P7/P9/P10 仅作为任务形态而非权力层级；中文、英文、日文共享同一证据标准。
- 验证：12 个 Skill 全部通过 `quick_validate.py`；`skill-vetter` 扫描结果均为 0 critical、0 high、0 skipped；17 个文件的相对 Markdown 链接无断链；旧危险机制和旧 reference 调用零残留。
- 规模变化：从 6,138 行第三方内容重写为 592 行原创入口与按需参考，减少自动加载和重复规则。
- 待完成：用真实对话任务分别前向测试重复报错、无证完成、用户主动夸夸、跨模块协调、战略决策和预算耗尽六类场景，之后才升级为 `original-verified`。

### `goal-meta-skill`（首轮）

- 研究依据：OpenAI Goal mode 发布说明、OpenAI *Codex-maxxing for long-running work*，以及当前本地 Codex Goal 工具接口。
- 保留精华：把目标写成结果而非活动，补足成功证据、约束、边界、迭代与终止条件。
- 删除糟粕：固定七字段被误当成产品语法、中文默认强制双语、所有模糊任务默认本地 MVP、默认三轮迭代、低风险问题也强制多选访谈。
- 新增能力：完整范围审计、证据范围匹配、外部状态与授权边界、只有用户明确要求才设置 token budget、活动 Goal 不被静默替换。
- 验证：通过结构校验；7 个单元测试覆盖中英文强目标、占位符、高风险授权、无限重试、模糊目标与 JSON 输出；用本次 47 个 Skill 重建目标做真实草案检查并通过 strict 模式；`skill-vetter` 扫描 0 critical/high/medium/low、0 skipped。
- 待完成：在至少一个模糊低风险目标、一个跨系统高风险目标和一个已有活动 Goal 冲突场景中做独立前向使用后，才升级为 `original-verified`。

### `skill-publisher`（首轮）

- 研究依据：Agent Skills 当前规范与参考仓库、GitHub CLI `gh skill publish`、GitHub Agent Skills 文档、`gh repo create`、Secret Scanning/Push Protection、GitHub 许可证指南与 SPDX。
- 保留精华：结构检查、GitHub 仓库发布、公开文档准备和真实安装验证。
- 删除糟粕：自动补 MIT、默认公开、`git add -A` 全量提交、忽略 push 失败后继续报成功、默认覆盖 `~/.agents/skills`、把徽章/截图/双语/Star History 当成所有项目的硬门槛。
- 新增能力：完全只读的标准库预检器；Skill 与文件 SHA-256 清单；秘密文件/密钥内容、符号链接、归档、名称/目录、许可证、README、Git 边界、origin/target 与 `gh skill` 能力探测；发布动作分成创建、提交、推送、Release 和隔离安装验证。
- 验证：通过结构校验；9 个单元测试覆盖干净私有 Skill、非法名称、目录不匹配、公共许可证未决、秘密文件、私钥、符号链接、归档与 JSON 哈希清单；对两个新 Skill 自检均为 0 blocker；`skill-vetter` 扫描 0 critical/high/medium/low、0 skipped。
- 环境证据：本机 `gh 2.87.0` 尚无 `gh skill`；官方文档要求 2.90.0+ 且功能仍为 preview，因此当前只验证了能力探测和安全降级，未伪造 live 发布结果。
- 待完成：在用户明确授权的临时私有测试仓库中前向验证 create/push/release/preview/install 全链路，之后才升级为 `original-verified`。

### `wechat-reading`（首轮）

- 研究依据：Tencent `WeChatReading` 当前仓库与 `v1.0.4` commit `315698a8da1810fab0bbf24a52b38a6960e54cdc`、官方 API Key 页面、仓库全部公开 Issue、RFC 9110、OWASP Secrets Management 与 NIST Privacy Framework；社区实现只用于交叉发现失败场景。
- 保留精华：官方 Gateway、17 个当前只读/元数据端点、搜索/详情/章节/书架/进度/笔记/统计/点评/推荐能力，及分页、条件字段和统计口径。
- 删除糟粕：把只读同步称为可写管理、把 `upgrade_info.message` 当执行指令、大量手写带凭证 `curl`、缺失字段当零、文章收藏含混算成“书”、隐私缺省值强行算公开、默认暴露原始账号数据、静默回退 Cookie/抓取/逆向接口。
- 新增能力：标准库官方域名客户端；Key 不进入 argv/日志；拒绝带凭证重定向；端点白名单、扁平参数与类型校验；响应大小限制、最多两次显式重试；升级消息数据化；书架/笔记/阅读时间确定性汇总；个人数据分类、最小披露与导出完成证据。
- 验证：14 个单元测试覆盖 17 端点只读目录、扁平参数、`/book/similar` 必填字段、本地模拟网关、Authorization 发送、307 重定向拒绝、响应上限、恶意升级消息、Key 脱敏、书架组件/未知隐私、笔记核对、缺失计数和秒数转换；结构校验通过；发布预检 0 blocker。
- 安全扫描：测试攻击字符串改为运行时构造后，制品无真实 critical/high；对 Cookie/浏览器会话的引用只出现在明确禁止回退的说明中，保留为人工审计线索。
- 已知限制：未使用用户真实 `WEREAD_API_KEY` 调用生产 Gateway；官方开放 Issue 显示写书架/上传/书架分组仍不可用，`wordCount` 和图片内容可能缺失。
- 待完成：经用户授权，用最小权限账号对 `/_list`、公开搜索和一个个人只读端点做真实前向测试，并验证分页/429/升级响应后，才升级为 `original-verified`。

### `lark-*` 系列 27 个（首轮）

- 研究依据：官方 `larksuite/cli` 仓库与 v1.0.92（2026-08-28，commit `6646386e0996b1ff5df640bccff834a20bcb203b`）、npm 当前发布元数据、飞书/Lark Open Platform 文档、CLI 风险门禁与结构化错误实现、OAuth 2.0 Device Authorization Grant（RFC 8628）、RFC 3339 与 IANA Time Zone Database；旧 Skill 只用于核对能力覆盖和失败场景。本机实际版本为 1.0.71，官方最新版本为 1.0.92，二者间 1.0.84–1.0.92 已出现身份扩展、会议指南合并、事件管线、下载安全和多个业务域新增能力。
- 保留精华：27 个既有触发名称和业务边界、shortcut 优先、类型化资源与 `schema` 自省、user/bot 身份、最小 scope、结构化输出、分页、异步任务、high-risk-write 门禁，以及审批、Base、日历、文档、云盘、IM、邮件、妙记、Sheets、Slides、任务、会议、画板、Wiki 等领域的关键语义。
- 删除糟粕：485 个上游文件中的静态参数手册和复制参考、每个目录的上游 LICENSE、第三方 32×32 探测图、强制每次认证生成二维码、默认申请全部 scope、把空结果直接解释为资源不存在、把 exit 10 当普通错误、静默更新 CLI、把消息/事件内容当控制指令，以及依赖版本特定长文而没有运行时发现的做法。
- 新增共同能力：先用运行中 `--version` / `skills list` / `--help` / `schema` 建立命令事实；命令级固定 profile 与 identity；外部内容隔离；敏感值不进 argv/日志；IANA 时区与带偏移时间；全量/有界分页声明；cwd 相对文件路径；未知结果先查询不盲重试；异步终态；高风险精确确认；写后独立业务回读；v1.0.89 起 `lark-meeting` 合并与旧 `vc/minutes/note/vc-agent` 入口的双版本路由。
- 领域强化：审批加入定义/字段/任务状态核对；Apps 区分本地/dev/online、数据库事务、密钥与发布；Base/Sheets 保持 schema、类型、revision、原子/部分失败语义；Calendar/Attendance/Task 明确时区；IM/Mail 采用真实受众预览、草稿/幂等和外部发送授权；Docs/Markdown 处理选择器、版本与冲突；Drive/Wiki 处理 canonical token、权限继承和恢复；Event/VC Agent 强制有界运行并隔离 prompt injection；Slides/Whiteboard 同时做结构与视觉验收；两个 workflow 不再默认发布、发群或修改任务。
- 新增实现：`lark-shared` 的标准库 `check_plan.py` 静态检查 argv、profile、identity、risk、目标、授权、dry-run、确认 flag、读回、时区、分页、重复控制、恢复、秘密参数、raw API path 与不可信输入；`audit_family.py` 检查 27 个目录、frontmatter、Agent metadata、相对链接、运行时发现、许可残留和重复入口；二者都不调用飞书、不读取凭证。
- 验证：27/27 通过 `quick_validate.py`；23 个新增单元测试覆盖干净家族、缺目录、许可残留、错误名称、断链、Agent prompt、运行时发现，以及读/写/高风险计划、profile/identity 与 argv 一致性、未确认 `--yes`、dry-run 能力声明、外部发送、日期型/瞬时时区、分页、不可信输入、幂等、秘密参数、安全路径与 raw API query；文档中的 86 个唯一发现命令在本机 1.0.71 全部返回成功；隔离假凭证下 IM 发送、日历创建、Drive 删除三个 dry-run 通过，Drive 未确认删除正确返回 exit 10 / `confirmation_required`；27 个 Skill 经 `skill-vetter` 扫描为 0 critical/high/medium/low、0 skipped；全仓库公开发布预检 0 blocker；全仓库 57/57 结构通过、114 个测试通过。
- 规模与归属：从 485 个第三方文件、121,084 行、5,020,565 bytes（约 4.79 MiB）重建为 65 个原创文件、2,939 行、162,916 bytes（约 159 KiB）；新实现与旧目标及官方 v1.0.92 Skill 的 40 字符以上非标题/表格/命令实质行精确重合均为 0。删除上游文案、代码、许可和资产后，27 个目录改由顶层 MIT 覆盖；`lark-cli` 仅作为外部官方依赖和研究依据。
- 待完成：当前没有使用用户真实飞书凭证进行 API 读写，也没有执行真实消息/邮件发送、审批决策、生产发布、权限、删除或会中入会。后续应在隔离测试租户按域完成只读 → 可恢复写 → 高风险拒绝/确认 → 业务回读 → 清理的前向矩阵，并对 Slides/Whiteboard 做真实视觉检查，之后才升级为 `original-verified`。

### `imagegen-frontend-web`（首轮）

- 研究依据：OpenAI 当前图像生成与 GPT Image 提示指南、W3C WCAG 2.2、web.dev 响应式图片与 CLS 指南；上游 `Leonxlnx/taste-skill` 仅用于核对原功能边界与许可证，不作为文字模板。
- 保留精华：图片主导的网页艺术指导、层级/排版/留白/裁切/材质/品牌一致性、反模板化审查，以及把参考图交给前端实现的基本用途。
- 删除糟粕：每个 section 强制一张横图、模糊网站默认生成 6–8 张、先宣布任意图片数、固定 1–10 风格旋钮和庞大模式清单、把所有网站默认当转化漏斗或图片型 Hero、用像素截图冒充语义/响应式/性能证据。
- 新增能力：按未决设计问题选择最小参考集；区分单概念、响应式集合、参考包、生产素材和探索；保留/修改/禁止引入的编辑协议；live/placeholder/essential raster/no-text 文本策略；来源与权利、裁切焦点、替代文本、响应式与浏览器验收边界。
- 新增实现：标准库 `validate_reference_pack.py`，验证 JSON brief、设计系统、viewport 覆盖、安全相对路径、符号链接、PNG/JPEG/WebP 尺寸、宽高比漂移、文本/alt 策略、实现说明、生产素材权利声明与 SHA-256 清单。
- 验证：通过 `quick_validate.py`；10 个单元测试覆盖干净参考包、PNG/JPEG/WebP 尺寸、缺失文件、目录穿越、符号链接、缺失 alt、生产权利、栅格文字、响应式覆盖和宽高比警告；`skill-vetter` 为 0 critical/high/medium/low、0 skipped；发布预检 0 blocker。
- 规模变化：从 987 行强约束单文件和单独上游许可证重建为原创入口、按需参考、校验脚本与测试；删除上游代码/文案后改由顶层 MIT 许可覆盖。
- 待完成：在真实的“生成参考图 → 响应式实现 → 浏览器视觉/无障碍/性能检查”任务中前向验证一次，并对实际图片生成结果完成文字、裁切和跨帧一致性审查后，才升级为 `original-verified`。

### `impeccable`（首轮）

- 研究依据：W3C WCAG 2.2、WAI-ARIA Authoring Practices、W3C Internationalization Quick Tips、Design Tokens Community Group 2025.10 稳定报告，以及 web.dev 的 Core Web Vitals、响应式图片和 CLS 指南；上游 `pbakaus/impeccable` 仅用于核对能力范围、风险与许可证。
- 保留精华：界面 critique、技术审计、需求 shaping、构建/重设计、精修和设计系统提取；覆盖真实内容、状态、国际化、响应式、无障碍、性能、动效、排版、布局、色彩与浏览器验证。
- 删除糟粕：23 个命令别名和万能路由、把审美偏好伪装成普遍禁令、项目 hooks、用户目录缓存、后台服务、浏览器会话改源码、完整环境变量转发、凭证建议、外部 Agent 调用、绕过 sandbox/permission 的启动参数及压缩浏览器代码。
- 新增能力：先区分只读诊断与获授权修改；用 surface contract 和 preserve/extend/replace 决策约束改动；原生 HTML 优先；静态、渲染、交互、无障碍、性能和回归证据分层；明确实验室指标不能冒充真实用户现场数据。
- 新增实现：完全只读、标准库 `audit_frontend.py`，不执行项目代码、不跟随符号链接；输出带 severity、confidence、位置、证据和人工补验方法的 JSON/文本线索，检查文档元数据、重复 ID、图片、控件名称、表单标签、键盘语义、焦点、动效、固定宽度、溢出、层级和颜色 token 漂移。
- 验证：12 个单元测试覆盖干净页面、HTML 元数据/图片/控件、JSX 键盘线索、可访问名称、动态文字不误报、CSS 焦点/动效/响应式/字号/层级、reduced motion、重复 ID、隐藏可聚焦控件、颜色漂移、符号链接/大文件、失败阈值和 CLI JSON；前向扫描上游 216 个前端文件时发现并修复动态链接名误报；结构校验和安全扫描通过，集合级公开发布预检 0 blocker。
- 规模与归属：从上游快照的 148 个 Skill 文件、56,115 行、约 3.07 MB 重建为 8 个原创文件、790 行；新旧 40 字符以上实质行精确重合为 0；删除上游 LICENSE/NOTICE 和复制实现后改由顶层 MIT 覆盖。
- 待完成：在一个真实界面上分别完成只读 critique 与获授权修复，并用浏览器检查键盘路径、可访问树、响应式状态、视觉回归和适用性能证据后，才升级为 `original-verified`。

### `kami`（首轮）

- 研究依据：W3C WCAG 2.2 与 PDF 技术、WAI 页面结构和复杂图片教程、W3C 国际化语言/UTF-8 指南、CSS Paged Media 与 Fragmentation、ISO 14289-2:2024（PDF/UA-2）、web.dev 字体加载指南及 SIL OFL 当前授权指南；上游 `tw93/Kami` 仅用于核对能力、失败边界与许可证。
- 保留精华：一页纸、报告、信函、简历、作品集、幻灯片与静态落地页路由；先核来源与素材、原子事实不丢失、缺口显式化、印刷/屏幕双通道、编辑源与渲染物分开、字体和逐页/逐视口验收。
- 删除糟粕：固定羊皮纸/墨蓝/衬线审美、默认读取用户主目录品牌画像、49 套上游模板/图表、字体二进制与不完整归属、向用户字体目录写入、可变分支 CDN 下载且只按体积校验、`--break-system-packages` 安装建议、后台 MCP/渲染服务及允许受信 HTML 携带本地/HTTP 资源权限的执行面。
- 新增能力：按读者任务选择结构；事实、推断、用户陈述和缺口分层；中性设计 token 起稿器；自定义字体的来源/权利/许可证/哈希/离线回退合同；内容、结构、渲染、交互、格式与无障碍六层证据；明确“可打开 PDF”“带标签 PDF”和 PDF/UA-2 不是同一结论。
- 新增实现：标准库只读 `validate_delivery.py`，验证 `delivery.json` 状态、制品类型与语言、安全本地路径、符号链接、格式后缀与文件签名、来源日期、素材和字体权利、HTML 语言/UTF-8/title/main/h1/图片、未替换标记、逐页 PDF 截图、落地页窄/宽视口、无障碍状态、缺口与 SHA-256 清单；不联网、不渲染、不执行项目代码。
- 验证：16 个单元测试覆盖已验证报告、填充后的中性起稿器、非法清单、目录穿越/缺失文件/符号链接、重复输出与格式错配、伪 PDF、HTML 结构和未替换内容、落地页双视口、PDF 全页证据、字体权利、已验证缺口、草稿降级、外部来源日期和 CLI 阈值；起稿器经 `impeccable` 静态审计为 0 high/medium/low；结构校验、安全扫描通过，集合级公开发布预检 0 blocker。
- 规模与归属：从 103 个第三方 Skill 文件、33,228 行、约 1.49 MB 重建为 9 个原创文件、约 1,100 行；删除上游 MIT 文件、模板和字体后，新旧 40 字符以上实质行精确重合为 0，改由顶层 MIT 覆盖。
- 待完成：在真实素材上分别完成一个可编辑文档或幻灯片和一个 HTML→PDF/静态页面任务，打开目标格式并逐页/逐视口检查，同时用专用工具核对实际 PDF 标签或明确不作 PDF/UA 声明，之后才升级为 `original-verified`。

### `beautiful-html-templates`（首轮）

- 研究依据：W3C WCAG 2.2、WAI 无障碍演示与活动指南、WAI-ARIA APG Carousel 模式、WAI Carousel 教程、SC 2.2.2 Pause/Stop/Hide、页面结构与复杂图片教程、W3C 国际化语言声明及 MDN `prefers-reduced-motion`；上游只用于核对工作流、能力与许可证。
- 保留精华：场合与语气影响方向、用真实标题做低成本方向预览、同一视觉系统内扩展布局而非随意拼贴、最终 HTML 必须实际打开检查、键盘和自包含交付是浏览器演示的基本能力。
- 删除糟粕：任何任务都强制问场合/情绪并固定预览三套、把 34 个复制构图当成设计答案、要求永不调整字体/色板/网格/装饰、模板特定运行时重复、85 个 Google Fonts 引用和共 159 个外部 URL、固定视口 `overflow:hidden` 掩盖长文/翻译/窄屏问题，以及“打开文件”即算验收。
- 新增能力：按受众结果建立故事合同；从对比、密度、几何、字体角色、图像和动效轴推导原创方向；`cover/section/bullets/two-column/metrics/quote/image/closing` 小型布局语法；系统字体主题、WCAG 对比预检、RTL、当前来源日期、图片格式/体积/路径/权利/描述、用户内容转义、无 JavaScript 阅读顺序、深链接、讲者备注、全屏、窄屏和逐页打印。
- 新增实现：标准库 `build_deck.py` 读取语义 JSON，在 `--check` 中只读验证，生成时原子写入单一 HTML；默认无外部字体、脚本、样式或运行网络依赖，本地 PNG/JPEG/WebP 通过安全路径和格式检查后嵌入 data URL，已有输出需显式 `--force`。
- 验证：14 个单元测试覆盖随附示例、用户内容转义与无远程运行时、无障碍控件/渐进增强、非法语言/布局、主题对比与未知 token、内容密度、长文警告、图片路径/符号链接/alt/权利/描述、图片嵌入与哈希、当前来源日期、RTL、覆盖保护及 CLI JSON；示例 5 页 deck 构建通过，生成 HTML 经 `impeccable` 静态审计为 0 high/medium/low；结构校验、安全扫描通过，集合级公开发布预检 0 blocker。
- 规模与归属：从 120 个第三方文件、74,212 行、约 3.68 MB 重建为 8 个原创文件、约 1,060 行；删除上游 MIT、34 套模板和运行时后，新旧 40 字符以上实质行精确重合为 0，改由顶层 MIT 覆盖。
- 待完成：用真实主题在浏览器中逐页检查目标投影尺寸、375px/1280px、键盘/焦点/哈希/备注/全屏、reduced motion、断网、禁用 JavaScript和打印/PDF，再依据实际反馈完成一次方向迭代，之后才升级为 `original-verified`。
