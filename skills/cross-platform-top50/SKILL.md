---
name: cross-platform-top50
description: 规划并执行 CSDN、公众号、知乎、小红书、微博、抖音、X、B站、掘金、YouTube、Linux.do、GitHub 等 20+ 公开网络与社交渠道的主题研究，按真实可达性建立可审计候选池、去重验收并生成“本次检索范围内 Top N”，在当前请求明确授权时归档到飞书知识库。用于跨平台调研、全网 Top 50、社交平台搜索、固定研究提示词或搜索后整理飞书；不用于单一事实查询、社交互动写操作、绕过登录/付费墙，或把搜索摘要直接拼成榜单。
---

# 跨平台 Top 50 研究

把一个明确主题编译为可暂停、可恢复、可复核的多平台研究。交付的是限定范围、时间、路由与评分版本的策展榜单，不是“全网绝对排名”。

## 执行合同

- 自主等级：L4。可直接执行公开只读检索、创建本地研究包、运行测试，并把独立分片交给子 Agent；主任务保留策展与最终验收。
- 当前请求明确写“新建/发布到飞书”时，可执行受管空间、空白节点与首次正文写入；仅研究或预览时保持本地模式。
- 必须暂停：主题为空；用户需要完成登录/验证码/飞书授权；付费/私密/访问控制；非托管或歧义飞书目标；删除、覆盖、移动、权限/成员/owner/公开分享；证据或回读与计划不符。
- 修复上限：同一路线最多 3 轮有新证据的定向修复；认证/参数类终止错误不原样重试。到达停止条件时交付真实 Top K、checkpoint 和最小补验方法。
- 不算完成：只有计划、搜索摘要、未审候选、虚构 Agent 数、绿色结构测试、API success 或已创建空库而无回读正文。

## 解析命令

从当前请求与上下文解析以下参数：

- `topic`：必填。`《》`、`《主题》`、`{{TOPIC}}`、空白或无法消歧的对象都是未替换占位符；此时不要开始检索或创建飞书空间，只请求真实主题。
- `purpose`：默认“建立可复用主题知识库”；用途会影响查询和相关性评分。
- `top_n`：默认 50；候选池目标为 `max(150, 3 × top_n)`，但不能为了数量降低门禁。
- `timeframe` / `languages` / `geography`：默认不限、中英文、全球；对版本、价格、政策、职位等易变信息单独冻结核验日期。
- `platforms`：默认计划覆盖 [平台路由](references/platform-routing.md) 的 canonical 28 渠道；用户点名平台为 `required`，明显不适用的平台可带依据标 `not_applicable`。
- `login_mode`：`public-only` 或 `user-assisted`；默认 `public-only`。用户表示可以协助登录时采用 `user-assisted`，但登录完成前仍不得假设会话有效。
- `publish_mode`：`local`、`feishu-new-space` 或 `feishu-existing-space`；默认 `local`。只有当前请求明确要求写入飞书才编译为后两者；其它拼法先规范化为这三个值，不能静默产生第四种语义。

其余缺省项用保守默认值继续，并在 `run_manifest.json` 标为工作假设。用户只要固定提示词而不执行本次研究时，交付 [便携总提示词](assets/master-prompt.md) 的参数化版本。

## 执行阶段

按以下门禁推进，不能把多个状态压成“已验证”：

```text
scope → discovery → fetch → extraction → worker_check
      → curator_acceptance → ranking → synthesis
      → feishu_publish（按需）→ readback_verification（按需）
```

需要字段、状态枚举、研究包结构、去重与评分口径时读取 [研究合同](references/research-contract.md)。

### 1. 冻结范围与查询面

在广泛搜索前保存：研究问题、用途/受众、主题别名与排除词、时间/语言/地域、required/important/adjacent 平台、允许/禁止来源、候选目标、评分版本和停止条件。

查询不能只是把同一句话复制到每个平台。至少覆盖：

- 精确实体、别名、中英文名与旧名；
- 与用途匹配的教程、实战、评测、案例、争议、失败和反例；
- 官方/一手证据、创作者经验、社区讨论、代码/数据、视频/长文等不同视角；
- 时效主题的年份、版本、生效日期和当前状态。

### 2. 体检必须包含真实轻量探针

执行真实网络检索前读取 [平台路由](references/platform-routing.md)。若 `agent-reach` 可用，先运行 `agent-reach doctor --json`；若 OpenCLI 是候选后端，再运行 `opencli doctor`。静态 doctor 只说明组件存在，不能证明浏览器桥接、账号、权限、配额或当前查询可用。

对每种计划后端执行一次最小只读 probe，并分别记录：

```text
tool_readiness | bridge_state | auth_state | quota_state | authorization | probe_result
```

probe 的 401/403、429、验证码、空响应与解析错误都必须进入路由账本。不得在研究中自动升级 CLI、安装扩展、购买配额或切换身份；这些是独立环境变更。

### 3. 并行只用于独立分片

有子 Agent 时按“查询/访问后端/语言或内容类型”划分独立分片，而不是为了凑数一平台一 Agent。使用运行时实际可用的并发槽位并分批复用；不得宣称调用了并未启动的 50 个 Agent，也不得把脚本线程称作独立 Agent。

每个研究 worker 只能把证据推进到 `[_]`。主任务或独立 curator 必须直接查看原始来源支持后，才能写 `[x]` / `reviewer_status=accepted`。主任务负责合并账本、处理转载与冲突、核对所有拟入选条目；Agent 数量本身不构成可信度。

### 4. 登录接力是可恢复 checkpoint

登录型平台被阻塞时：

1. 原子保存 canonical checkpoint：`run_id, topic, platform, stage, exact_probe_or_command, tool_readiness, bridge_state, auth_state, quota_state, authorization, probe_result, error_summary, completed_query_ids, pending_query_ids, candidate_ids, artifact_paths, next_safe_command, created_at, expires_or_unknown`；manifest、查询/来源账本和候选路径由 `artifact_paths` 指向；
2. 继续所有不依赖该登录的独立公开路由；
3. 没有其它有效工作后，一次性告诉用户要打开哪些平台、完成何种登录、完成后回复什么；
4. 恢复时读取同一 `run_id`，先执行 `exact_probe_or_command` 的等价最小只读 probe，再从 `pending_query_ids` 继续；禁止重跑 `completed_query_ids` 或丢掉 `error_summary`。

不得绕过登录墙、付费墙、验证码、robots、限频或私密数据边界。

### 5. 候选不是证据

搜索结果页只负责发现。候选至少保留稳定 ID、平台、标题、原 URL、作者/账号、发布日期或未知标记、访问日期、内容类型、查询与后端、可见互动原值、短摘录/可观察事实和限制。默认只保存元数据、短摘录、分析与链接，不批量复制全文或完整字幕。

入榜条目必须：

- 已读取足够原文、字幕、README/代码或可审计可见内容；
- 引用至少一张由独立 curator 接受的 strong/medium 证据卡；
- 证据卡能通过 `evidence_id` 与来源账本互相解析；
- URL、访问日期、推荐理由、评分输入与审核记录完整；
- 不属于已选代表项的 URL、平台 ID、转载、镜像或同稿簇。

用户若明确限定 `primary-source only` / “只要一手来源”，把它冻结为资格门槛：每张入榜证据卡必须能追到官方、原作者、原始数据/代码或直接可观察的一手对象，并在来源账本标明 `source_type`；普通 `medium` 二手证据不能满足该请求。若一手条目不足，只交付相应 Top K，不用二手材料补满。

自动摘要、标题、热度、多来源表面一致和 worker 自报 `accepted` 都不能单独通过门禁。

### 6. 确定性排名只处理已验收输入

排序前冻结研究包，然后运行：

```bash
python3 scripts/rank_candidates.py \
  --input <run-dir>/candidates.json \
  --manifest <run-dir>/run_manifest.json \
  --queries <run-dir>/queries.tsv \
  --sources <run-dir>/sources.tsv \
  --evidence-cards <run-dir>/evidence_cards.tsv \
  --output-dir <new-nonexistent-output-dir> \
  --top 50
```

脚本必须失败关闭：缺少研究上下文、证据引用不可解析、required 平台仍 pending、非公共 URL、账本不守恒或审核不独立时，不能产生完成通过。评分为相关性 35、来源质量 20、证据 20、平台内可比互动 15、新鲜/适用性 10；未观测互动得 0，不因样本数得到默认奖励。热度不改变证据等级。

合格去重后不足 `top_n` 时交付真实 Top K 与缺口，禁止填充或声称 Top N 完成。平台覆盖与最终入选分布分别报告，不设平台保底名额。

### 7. 先验收本地研究包

最低产物为：

- `run_manifest.json`、`queries.tsv`、`sources.tsv`、`candidates.json`、`evidence_cards.tsv`；
- `ranking.json`、`top.json`、`rejected.json`、`run_summary.json`、`package_validation.json`、`report.md`；
- `source_gap_backlog.md` 与 `platform_coverage.tsv`。

只在结构校验通过且 curator 完成语义验收后，把报告称为最终研究结果。机器绿灯不证明摘录真的支持主张。

创建或大幅修改本 Skill 时，用 [前向验收场景](references/evaluation-scenarios.md) 做独立行为测试；普通运行不需要加载该文件。

### 8. 飞书发布

仅当本地包通过、主题非空、且当前命令明确要求新建/写入飞书时读取并执行 [飞书发布合同](references/feishu-publish.md)。使用 `lark-wiki` 管理空间/节点，使用 `lark-doc` 写正文；显式 `--as user`，逐阶段绑定真实 ID，查重、dry-run、执行、回读。

允许自动执行的只是当前请求中明确指定的可恢复创建。删除、移动、权限/成员、owner 转移、公开分享、覆盖或续写非空既有正文仍需对精确对象单独确认。API 成功而未回读，不能报告发布完成。

## 完成声明

只有以下事实都有当前证据时才说“完成”：

- required 平台均为 `complete|partial|blocked|rejected|not_applicable`，非 complete 状态带原因和最小补验步骤；
- 声称“20+ 平台完成”时至少 20 个平台有已审查终态，且至少 12 个平台实际召回候选；否则说“阶段性覆盖”；
- Top N/K 每条均有可解析、独立 curator 接受的证据与稳定排序输入；
- 路由失败、反证、冲突、单来源、低置信与登录缺口可见；
- 本地包可读、可重放，所有子 Agent 产物已由主任务核查；
- 如发布飞书，真实空间/节点/文档已回读，记录数与关键 URL 和本地快照一致。

交付顺序：实际完成状态 → 3–7 条决定性洞察 → Top 总表/详情 → 平台覆盖、证据、冲突与缺口 → 本地产物 → 已验证的飞书 URL 或真实 ID。
