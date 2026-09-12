# skills — 自用 Agent Skill 合集

把高频使用的 Agent Skill 收进一个仓库统一管理。共 **57 个 Skill**，覆盖全网调研、微信/企业微信本地数据、飞书全家桶、设计前端和 Agent 效率工具。

说明：

- 仓库中的 **57 个 Skill 当前制品均按功能需求独立设计或独立重建**。这里的“原创”指具体文案、代码组织、示例、模板和随包资产可由仓库证据支持，不表示功能思想、公开 API 或通用术语由本仓库首创。完整定义、证据等级和停止条件见 [`ORIGINALITY_POLICY.md`](ORIGINALITY_POLICY.md)。
- 其中最初收录的第三方 Skill 已完成原创首轮重建：重新研究当前官方资料，保留必要能力，删除上游文字、代码、模板和资产，不把“换措辞”当成重建。
- 57 个 Skill 的入口与正向、边界、失败恢复案例可从 [USAGE_GUIDE.md](USAGE_GUIDE.md) 逐项打开。
- `lark-` 系列不复制官方 CLI 内置 Skill 的静态参数手册，而以运行中 `lark-cli --help` / `schema` 为命令事实，并加入 profile/identity、最小权限、时区、分页、外部内容隔离、高风险确认、未知结果恢复和写后回读合同。
- 合集本体与全部 57 个 Skill 采用顶层 `LICENSE`（MIT）。当前不捆绑第三方文案、代码、模板、字体或媒体素材；外部依赖、研究引用与用户输入不属于原创声明范围。机器可读归属见 [`SKILL_PROVENANCE.json`](SKILL_PROVENANCE.json)，重建证据见 [`ORIGINAL_REBUILD.md`](ORIGINAL_REBUILD.md)，边界说明见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

## 案例与详细说明

每个 Skill 都在入口顶部链接自己的 `references/examples.md`，至少包含一个正向案例、一个边界案例、一个失败恢复场景，以及可观察的验收证据。入口保留共同决策与硬约束，案例按需读取，避免把 57 套细节一次性塞进上下文。

可复跑集合审计：

```bash
python3 skills/skill-vetter/scripts/audit_collection.py . --expected-count 57
python3 skills/skill-vetter/scripts/audit_usage_docs.py . --expected-count 57
python3 skills/skill-vetter/scripts/audit_originality.py . --fail-on unreviewed
```

第一项检查会核对 Skill 数量、归属台账覆盖、案例文件与章节、相对链接、逐 Skill 许可证/声明残留、符号链接和未登记二进制素材。第二项检查每个入口是否包含输入、流程、边界和验收信号，并要求正向、边界、失败恢复案例具有具体准备信息、处理、预期结果和可观察证据。第三项把 `independently_rebuilt` Skill 与固定历史 Git 基线做只读哈希、连续 token 和长行比较，出现实质性重合时阻止发布。自动检查不能替代技术准确性和实际使用效果的人工复核，也不能证明未知的全互联网不存在相似作品。

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
| `web-research` | 按来源可访问性、授权范围和证据要求路由公开网页、已知 URL、私有收藏与媒体研究 |
| `chatgpt-web-research` | 在用户指定且已登录的可见 ChatGPT 网页会话中执行研究，并保存可核验原始证据与编辑稿 |
| `wechat-reading` | 通过微信读书官方只读 Gateway 查询与分析书籍、书架、进度、笔记、划线、点评、推荐和阅读统计，不泄露账号 Key |
| `skill-vetter` | 安装、执行、发布或信任 Agent Skill 前，审计来源、许可证、指令、代码、依赖、权限、隐私与供应链风险 |

### 微信 / 企业微信（5 个）

| Skill | 用途 |
|---|---|
| `wechat-local-vault` | 把用户授权的 macOS 微信数据库只读快照解密到私密 Vault，再按会话和时间窗查询或导出 |
| `wecom-local-vault` | 发现、解密并只读查询用户授权的 macOS 企业微信本地数据库快照，敏感产物留在私密目录 |
| `wecom-operations` | 通过官方 wecom-cli 管理企业微信文档、待办、会议和日程，写操作带明确授权与回读门 |
| `wechat-mp-batch-exporter` | 以预览/执行门批量下载微信公众号文章和授权历史数据，并输出可复核清单、失败项与统计 |
| `mac-wechat-dual-open` | 在 macOS 上预览、构建和核验独立微信副本，不修改原应用或用户容器 |

### 飞书（Lark）系列（27 个）

| Skill | 用途 |
|---|---|
| `lark-approval` | 查询或处理审批定义、实例和任务；校验表单、处理人、决策影响与写后状态 |
| `lark-apps` | 开发和运营妙搭应用；区分本地/dev/online、发布、数据库、密钥、权限和自动化边界 |
| `lark-attendance` | 按明确日期和时区查询个人打卡记录，并限制敏感人事数据披露 |
| `lark-base` | 操作 Base 的表、字段、记录、视图、表单、仪表盘、工作流和权限，保持类型与批量证据 |
| `lark-calendar` | 查询和安排日程、忙闲、参会人、会议室、RSVP 与周期，显式处理时区和冲突 |
| `lark-contact` | 在租户语境中消歧姓名、邮箱与 open_id，为后续动作提供最小必要身份信息 |
| `lark-doc` | 读取和编辑 Docx/Wiki 正文、块、媒体、资源、历史与思维笔记，并做版本回读 |
| `lark-drive` | 管理云盘资源、传输、同步、版本、评论、权限和安全标签，保留恢复路径 |
| `lark-event` | 发现、检查和有界消费实时事件，处理去重、断线、游标及不可信载荷 |
| `lark-im` | 查询与管理聊天、消息、资源、成员、卡片和 Feed；发送前核对真实受众与幂等 |
| `lark-mail` | 查询、整理、起草、回复和发送邮件；默认草稿优先，校验收件人、正文和附件 |
| `lark-markdown` | 读取、比较、patch 或覆盖 Drive 原生 Markdown，处理远端版本与冲突 |
| `lark-minutes` | 搜索和管理妙记、媒体、总结、待办、章节、说话人和逐字稿，保持来源完整性 |
| `lark-note` | 在已知 note_id 时读取纪要详情与 unified transcript，区分关联文档和妙记 |
| `lark-okr` | 管理 OKR 周期、目标、KR、指标、权重、对齐与进展，核对所有者和最终结构 |
| `lark-openapi-explorer` | 现有命令不足时，从当前 schema 与官方文档验证原生 OpenAPI 后再调用 |
| `lark-shared` | 统一处理运行时发现、profile/identity、最小权限、输出、时区、分页、风险和回读 |
| `lark-sheets` | 操作工作簿、单元格、公式、样式、行列和分析对象，保持范围、类型与 revision |
| `lark-skill-maker` | 从当前 help/schema 和官方资料设计窄触发、可验证的原创 lark-cli Skill |
| `lark-slides` | 创建和编辑原生幻灯片，保持元素可编辑，并用 XML 回读与截图验证视觉结果 |
| `lark-task` | 管理任务、清单、负责人、截止时间、附件和智能体，防止重复创建与错误完成 |
| `lark-vc` | 搜索和读取历史/进行中会议、事件、录制与纪要关联，区分不同证据口径 |
| `lark-vc-agent` | 在明确同意后让 bot 加入、读取、发言和离开实时会议，并保证有界运行与清理 |
| `lark-whiteboard` | 查询和编辑画板节点、连线与布局，同时验证 raw graph 和实际预览 |
| `lark-wiki` | 管理知识空间、节点树与成员，区分 node token 和底层对象 token |
| `lark-workflow-meeting-summary` | 在有界时间范围内汇总会议证据，给结论和行动项绑定来源，不默认发布 |
| `lark-workflow-standup-report` | 结合日程与任务生成日期安全、可追溯的站会摘要，不默认改状态或发群 |

### dbs 商业分析与内容创作系列（0 个）

| Skill | 用途 |
|---|---|

### 设计与前端（5 个）

| Skill | 用途 |
|---|---|
| `imagegen-frontend-web` | 为网站生成或编辑最小必要的视觉参考与生产素材，并用响应式、无障碍、来源和实现验收规格完成交接 |
| `vintage-pencil-card` | 把人物、宠物、风景、建筑与静物照片转换为构图保真的复古彩铅卡片 |
| `impeccable` | 依据真实内容、设计系统、交互、无障碍、响应式与性能证据，诊断、设计、实现或精修浏览器界面 |
| `kami` | 把来源材料重组、排版并验证为一页纸、报告、信函、简历、作品集、幻灯片或静态落地页，不虚构事实或格式能力 |
| `beautiful-html-templates` | 用语义 JSON、原创布局语法和系统字体主题生成自包含 HTML 幻灯片，并验证对比度、素材权利、键盘、响应式、离线与打印边界 |

### Agent 效率工具（3 个）

| Skill | 用途 |
|---|---|
| `agent-memory` | 设计、检查、迁移和维护 Markdown-first 私密 Agent 记忆库，区分权威记录与可重建索引 |
| `skill-publisher` | 发布或更新 Agent Skill：先固化仓库、许可证、秘密、提交与远端边界，再验证 GitHub 发布和隔离安装结果 |
| `goal-meta-skill` | 把长期 Codex 请求变成保持完整范围、可用权威证据验收、权限边界真实的持久 Goal |

### PUA 兼容系列（证据优先的执行教练）（12 个）

| Skill | 用途 |
|---|---|
| `pua` | 重复失败、被动交接或完成证据不足时，以观察→假设→实验→验证恢复进展 |
| `pua-ding` | 用户主动要求钉味时，区分用户结果、交付物、证据与汇报口径 |
| `pua-en` | 英文证据优先执行教练；直接但不模拟绩效处分 |
| `pua-ja` | 日本語の証拠重視実行コーチ；叱責ではなく次の検証行動を改善 |
| `pua-loop` | 有明确评价器和预算时运行可停止、可暂停的迭代优化循环 |
| `pua-mama` | 用户主动选择的温和家人式提醒；不使用牺牲叙事和情感勒索 |
| `pua-p10` | 战略兼容模式：比较选项、证据、权衡、可逆性与验证实验 |
| `pua-p7` | 执行兼容模式：方案、影响分析、实现和原路径验证 |
| `pua-p9` | 交付负责人兼容模式：任务规格、依赖、所有权边界、集成和验收 |
| `pua-pro` | 把已验证结果沉淀为有适用边界的经验、测试或可复用控制 |
| `pua-shot` | 用户主动调用的单次紧凑版高能动性执行协议 |
| `pua-yes` | 基于真实行为与结果的鼓励模式，不虚构成就或夸大评价 |

### 发布与分发（1 个）

| Skill | 用途 |
|---|---|
| `x-article-draft-uploader` | 把本地 Markdown 转为经核验的 X Articles 新草稿，保留封面与正文图片位置且不公开发布 |


## 许可说明

- 合集本体与全部 57 个原创 Skill：MIT（见顶层 `LICENSE`）。
- 各 Skill 的依赖（如 `lark-cli`、`wecom-cli`、本地微信数据库、浏览器登录态等）以其 `SKILL.md` 说明为准；涉及本地隐私数据的 Skill 全部在本机运行，不外传数据。

## 安全说明

原创重建与自动扫描不构成“安全”证明。安装、升级或执行任何 Skill 前，仍建议用本合集的 `skill-vetter` 固化制品、检查权限与供应链，并记录未覆盖项和残余风险。
