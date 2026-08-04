# skills — 自用 Agent Skill 合集

把高频使用的 Agent Skill 收进一个仓库统一管理。共 **56 个 Skill**，覆盖全网调研、微信/企业微信本地数据、飞书全家桶、设计前端和 Agent 效率工具。

说明：

- 收录的第三方 Skill 均已做**去个人化处理**：移除原作者的个人路径、账号、联系方式、推广内容，以及自更新/遥测/支付回传代码，保留全部功能；各目录内保留其原始 `LICENSE`，来源见 `THIRD_PARTY_NOTICES.md`。
- `web-research`、`agent-memory`、`wechat-local-vault`、`wecom-local-vault`、`wecom-operations`、`wechat-mp-batch-exporter`、`chatgpt-web-research`、`x-article-draft-uploader`、`mac-wechat-dual-open` 这 9 个 Skill 是**按功能需求重新撰写的原创实现**——文档文字独立撰写，功能灵感来自公开项目，与原作无文字复制关系。
- 合集本体及上述 9 个 Skill 采用顶层 `LICENSE`（MIT）；其余第三方 Skill 以各自目录内 `LICENSE` 为准。

## 安装

把需要的 Skill 目录复制到对应 Agent 的 skills 目录即可：

```bash
git clone https://github.com/siuserxiaowei/skills.git && cd skills

# Claude Code
cp -R skills/<skill-name> ~/.claude/skills/

# Codex
cp -R skills/<skill-name> ~/.codex/skills/

# 通用 Agents（豆包 Mac App / Trae Solo 等）
cp -R skills/<skill-name> ~/.agents/skills/
```

也可以用 `npx skills add siuserxiaowei/skills --skill <skill-name>` 类工具按需安装。

## Skill 一览

### 研究与信息获取（4 个）

| Skill | 用途 |
|---|---|
| `web-research` | 互联网研究总入口 |
| `chatgpt-web-research` | Drive the user's already logged-in ChatGPT 官网 / ChatGPT 网页版 account — … |
| `wechat-reading` | 微信读书助手 — 搜索书籍、管理书架、查看笔记划线、浏览书评、阅读统计、发现推荐好书 |
| `skill-vetter` | Security-first vetting protocol for AI agent skills. Use before instal… |

### 微信 / 企业微信（5 个）

| Skill | 用途 |
|---|---|
| `wechat-local-vault` | 在本机把微信 Mac 4.x 的数据库解密成可长期复用的数字资产库，并提供本地查询分析能力 |
| `wecom-local-vault` | Decrypt and read local WeCom/企业微信 5.x desktop databases on macOS into … |
| `wecom-operations` | 本 Skill 借助官方 wecom-cli 操作企业微信云端资源：把本地 Markdown 发布为普通文档或智能文档（含本地图片时需用户自… |
| `wechat-mp-batch-exporter` | 批量下载微信公众号文章正文、历史文章列表、原创文章筛选、历史计数口径、阅读量、点赞/转发等指标、评论和评论回复 |
| `mac-wechat-dual-open` | Build, check, fix, and refine a second WeChat app on macOS. Duplicate … |

### 飞书（Lark）系列（27 个）

| Skill | 用途 |
|---|---|
| `lark-approval` | 飞书审批：查询和处理审批待办/已办/实例，搜索可发起审批定义、查看定义详情并发起原生审批实例 |
| `lark-apps` | 妙搭（Spark/Miaoda）应用开发与托管：应用创建、本地全栈开发、云端生成迭代、创意设计（UI mockup / 可交互原型 / 线框… |
| `lark-attendance` | 飞书考勤打卡：查询自己的考勤打卡记录 |
| `lark-base` | 飞书多维表格（Base）操作：建表、字段、记录、视图、统计、公式/lookup、表单、仪表盘、workflow、角色权限；遇到 Base/多… |
| `lark-calendar` | 飞书日历：管理日历日程和会议室 |
| `lark-contact` | 飞书 / Lark 通讯录:按姓名 / 邮箱解析成 open_id,或按 open_id 反查姓名 / 部门 / 邮箱 / 联系方式 / 个… |
| `lark-doc` | 飞书云文档（Docx / Wiki 文档）：读取和编辑飞书文档内容 |
| `lark-drive` | 飞书云空间（云盘/云存储）：管理 Drive 文件和文件夹，包含上传/下载、创建文件夹、复制/移动/删除、查看元数据、查询权限设置、评论/权… |
| `lark-event` | Lark/Feishu real-time event listening / subscribing / consuming: strea… |
| `lark-im` | 飞书即时通讯：收发消息和管理群聊 |
| `lark-mail` | 飞书邮箱：Use when user mentions 起草邮件、写邮件、草稿、发送/回复/转发邮件、查阅邮件、看邮件、搜索邮件、邮件文件夹… |
| `lark-markdown` | 飞书 Markdown：查看、创建、上传、编辑和比较 Markdown 文件 |
| `lark-minutes` | 飞书妙记：搜索妙记、查看妙记基础信息、下载/上传音视频、读取或编辑妙记的产物内容、改标题、替换说话人/关键词、申请妙记查看/编辑权限 |
| `lark-note` | 飞书会议纪要（Note）直查：已知 note_id 时查询纪要详情、展示类型、关联文档 token，并读取 unified 原始逐字记录 |
| `lark-okr` | 飞书 OKR：管理目标与关键结果 |
| `lark-openapi-explorer` | 飞书/Lark 原生 OpenAPI 探索：从官方文档库中挖掘未经 CLI 封装的原生 OpenAPI 接口 |
| `lark-shared` | Use for lark-cli setup/auth tasks: auth login/status/logout, user vs b… |
| `lark-sheets` | 飞书电子表格：创建和操作电子表格 |
| `lark-skill-maker` | 创建 lark-cli 的自定义 Skill |
| `lark-slides` | 飞书幻灯片：创建和编辑幻灯片 |
| `lark-task` | 飞书任务：管理任务、清单和任务智能体 |
| `lark-vc` | 飞书视频会议：搜索历史会议记录、查询会议纪要（总结/待办/章节/逐字稿）、查询参会人快照 |
| `lark-vc-agent` | 飞书视频会议会中能力：用于让应用机器人真实加入或离开正在进行的会议，并读取当前身份可见的会中事件、发送会中文本消息或会中表情 |
| `lark-whiteboard` | 飞书画板：查询和编辑飞书云文档中的画板 |
| `lark-wiki` | 飞书知识库：管理知识空间、空间成员和文档节点 |
| `lark-workflow-meeting-summary` | 会议纪要整理工作流：汇总指定时间范围内的会议纪要并生成结构化报告 |
| `lark-workflow-standup-report` | 日程待办摘要：编排 calendar +agenda 和 task +get-my-tasks，生成指定日期的日程与未完成任务摘要 |

### dbs 商业分析与内容创作系列（0 个）

| Skill | 用途 |
|---|---|

### 设计与前端（4 个）

| Skill | 用途 |
|---|---|
| `imagegen-frontend-web` | Elite frontend image-direction skill for generating premium, conversio… |
| `impeccable` | Use when the user wants to design, redesign, shape, critique, audit, p… |
| `kami` | Typeset professional documents and product landing pages: resumes, one… |
| `beautiful-html-templates` | A library of 34 reusable, beautifully designed HTML slide-deck templat… |

### Agent 效率工具（3 个）

| Skill | 用途 |
|---|---|
| `agent-memory` | Install, upgrade, inspect, and maintain the public Agent Memory Vault … |
| `skill-publisher` | 一键发布 agent skill 到 GitHub，自动验证 SKILL.md、生成或检查更吸引人的 README、区分 skill nam… |
| `goal-meta-skill` | Turn vague or complex Codex tasks into strong `/goal` commands with ou… |

### PUA 系列（督促 Agent 干活）（12 个）

| Skill | 用途 |
|---|---|
| `pua` | Use for PUA/try-harder productivity coaching when the user expresses f… |
| `pua-ding` | Use for Ding-style (钉内/钉外) workplace reminders rooted in the 7.5万字 ess… |
| `pua-en` | Performance-coaching mode for repeated failures, passive behavior, com… |
| `pua-ja` | 日本語の生産性コーチングモード |
| `pua-loop` | PUA Loop — guided iterative development with recurring checks, complet… |
| `pua-mama` | 妈妈唠叨模式 — 中国式妈妈提醒风格的生产力 coaching |
| `pua-p10` | P10 CTO mode — define strategic direction, design org topology, manage… |
| `pua-p7` | P7 Senior Engineer mode — solution-driven execution under P8 supervisi… |
| `pua-p9` | P9 Tech Lead mode — write Task Prompts, manage P8 agent teams, never w… |
| `pua-pro` | PUA Pro extensions: self-evolution notes, compaction state continuity,… |
| `pua-shot` | PUA Shot — compact all-in-one PUA reference for explicit injection int… |
| `pua-yes` | SB Leader 夸夸模式 — ENFP 型领导，懂情绪有节奏 |

### 发布与分发（1 个）

| Skill | 用途 |
|---|---|
| `x-article-draft-uploader` | 将 Obsidian 或本地 Markdown 文章上传为 X/Twitter Articles 草稿：自动以第一张图作为封面，正文图片全部… |


## 许可说明

- 合集本体与 9 个重写 Skill：MIT（见顶层 `LICENSE`）。
- 第三方 Skill：`lark-` 系列、`imagegen-frontend-web`、`kami`、`beautiful-html-templates`、`skill-publisher`、`goal-meta-skill` 为 MIT；`impeccable`、`wechat-reading` 为 Apache-2.0（`impeccable` 含 `NOTICE.md`）；`pua` 系列源仓库未附带 LICENSE 文件（其 frontmatter 自述 MIT），使用前请知悉。
- `x-article-draft-uploader` 内保留上游 `wshuyi/x-article-publisher-skill` 的 MIT 归属文件。
- 各 Skill 的依赖（如 `lark-cli`、`wecom-cli`、本地微信数据库、浏览器登录态等）以其 `SKILL.md` 说明为准；涉及本地隐私数据的 Skill 全部在本机运行，不外传数据。

## 安全说明

入库前已做基础安全扫描：无外链数据回传、无凭据窃取、无混淆代码；原项目的遥测/支付/自更新回传代码已移除。安装任何第三方 Skill 前，建议先用本合集的 `skill-vetter` 过一遍。
