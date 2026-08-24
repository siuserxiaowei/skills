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
- `engine_mode`：`auto`、`python`、`go`、`rust` 或 `hybrid`；默认 `auto`。这决定本地执行后端，不改变平台授权、证据门禁或发布边界。用户强制的后端若探针/能力不满足必须失败关闭，不能静默改成另一种语言。
- `dual_run`：默认 `false`。只有用户明确要求，或当前阶段属于高风险规范化/去重且有两个独立可用实现时才启用；双跑用于比较，不把同一请求无条件执行三遍。
- `research_mode`：`standard` 或 `hengzong`；默认 `standard`。行业判断、机会地图、趋势推演、复杂决策或根因诊断可选 `hengzong`；普通榜单不承担该模式的额外查询与策展成本。
- `recent_social_mode`：默认 `auto`。QueryPlan 编译器机械映射为 fusion 时间策略：`auto → advisory`、`strict → strict`、`off → unbounded`；未知值失败关闭。主题明确要求“最近 30 天/近期舆情/社区反馈”时使用 `strict` 并冻结真实日期区间；日期未知或仅推断的候选隔离，不能混入窗口榜单。
- `wigolo_mode`：`disabled` 或 `external`；默认 `disabled`。它只是预留外部 Adapter：除用户显式启用、非 CJK 公开 Web、能力白名单与真实 probe 外，还必须先通过“兼容当前主机的原生单文件可执行镜像 + 源码冻结的已审计发行 SHA-256”门禁。JavaScript、Node/npm CLI、任何 shebang/解释型脚本（包括无后缀包装器）一律在 probe 前失败关闭；调用方不能注入摘要。当前摘要白名单为空，审计基线的标准 npm `wigolo@0.2.1` 没有生产执行路线；不是第四核心引擎。

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

把冻结范围编译为版本化 QueryPlan 时，运行 `scripts/research_planner.py`：每条记录分开保存平台专用 `search_query` 与跨平台可比的 `ranking_query`，并保存 query ID、意图、时间窗、CJK tokenizer 的实际实现和摘要。中文默认用零依赖 CJK bigram；只有明确可用时才使用可选 jieba，且回退必须入账。任何未知平台、未知意图、占位主题、无界查询数或摘要漂移都失败关闭。

多后端召回需要融合时，用 `scripts/fuse_candidates.py` 执行 weighted RRF。融合只生成 `discovery_only` 候选和完整 rank provenance，可施加作者上限、第一方作者的有界例外及显式 discovery breadth floor；互动量不参与 RRF，也不能创建 curator acceptance。输入候选 ID 的 URL、标题、作者、日期或来源语义冲突时失败关闭。

### 2. 体检必须包含真实轻量探针

执行真实网络检索前读取 [平台路由](references/platform-routing.md)。若 `agent-reach` 可用，先运行 `agent-reach doctor --json`；若 OpenCLI 是候选后端，再运行 `opencli doctor`。静态 doctor 只说明组件存在，不能证明浏览器桥接、账号、权限、配额或当前查询可用。

对每种计划后端执行一次最小只读 probe，并分别记录：

```text
tool_readiness | bridge_state | auth_state | quota_state | authorization | probe_result
```

probe 的 401/403、429、验证码、空响应与解析错误都必须进入路由账本。不得在研究中自动升级 CLI、安装扩展、购买配额或切换身份；这些是独立环境变更。

用 `scripts/source_contract.py` 规范化每条路线 outcome：保留 adapter/backend/probe、访问方式、采集方式、可见内容层级、原始日期依据、错误、重试与 breaker。429/瞬时故障最多按冻结预算重试；认证、挑战、robots 或未授权是终止状态。搜索摘要始终 `discovered_only`，未知/推断日期不得冒充严格时间窗命中。登录接力通过同一脚本创建带 TTL、幂等键、错误历史和原子写入的 checkpoint；恢复必须重新做等价最小 probe，只返回 pending query IDs。

### 3. 三套执行后端长期保留、按阶段路由

需要执行本地采集、批处理或排名时读取 [三引擎路由](references/engine-routing.md)。当一个研究范围同时含平台 CLI、浏览器、已发现公共 URL 或已完成 extraction 的本地批次时，先按 [多来源请求编译](references/route-bundle-compilation.md) 生成独立 shard，再对可执行 shard 运行 Python 路由器的真实 probe/plan：

- **Python 控制面**：始终保留，负责平台 CLI/Browser 登录编排、能力与授权账本、证据门禁、`deterministic-v2` 排名和飞书发布；小规模或登录型任务可全程走 Python。
- **Go collector**：只处理已经授权、已发现且由 manifest SHA-256/job-set digest 冻结的公共 HTTP(S) URL 批量抓取，负责透明自有 UA、robots 门禁、有界并发、按 host 限速、重试、响应上限和 checkpoint。它不是搜索引擎，不能绕过登录/验证码，也不能接收 Cookie/Authorization、任意请求 Header 或调用方自定义 UA；`transport_success` 只证明传输与工件落盘，不证明内容可用。
- **Rust processor**：只处理本地候选批次，负责 URL 规范化、安全预检、内容指纹、精确聚类和近重复待审标记。它不联网，不把离线 DNS 判断冒充 fetch-time SSRF 防护，也不代替 curator 或 Python 排名器。
- **Hybrid**：完整流程通常按 `Python discovery → Go fetch → Python extraction → Rust process → Python curate/rank/publish` 串行交接。Python extraction 必须把抓取工件转换为带稳定 ID、来源字段和可审计摘录的候选；没有完整提取产物时 Rust 不得启动。平台原生 CLI、OpenCLI 或浏览器获得的内容仍由 Python 控制面编排，再按需送 Rust 批处理。

不得仅凭源码目录或可执行文件存在就称引擎可用。probe 必须核对 engine ID、版本、合同版本、能力和退出状态；计划保存候选引擎、实际选择、阶段顺序、fallback、reason code 与 probe 证据。后端失败不能从账本消失。

语言选择看总成本，不只看 Token：同时评估实现与返工时间、测试矩阵、依赖/部署、安全维护、平台变化适配、故障定位、运行资源和结果验证成本。三套结构长期保留不表示每次三跑；只让某个后端承担它能明显降低总成本或不确定性的阶段。

`ego-browser` / ego-lite 只保留为 Python `browser_session` 的默认禁用候选，不是第四引擎。供应链、CLI 数据流、二进制许可和会话隔离门禁未关闭时，它不得进入 `auto` / `hybrid` 候选集；不得自动安装、移除 quarantine 或迁移日常 Chrome 数据。

Wigolo 同样只是 Python 的默认禁用外部 Adapter。启用前读取 [Wigolo 外部适配合同](references/wigolo-adapter.md)，先验证兼容当前主机的原生单文件镜像及源码冻结的已审计发行 SHA-256，再执行其真实 probe，并保存版本、能力、入口 SHA-256、HMAC 认证执行计划和原始结果；跨进程 plan/execute 必须共享 owner-only key file，密钥不进入工件、argv 或子进程环境。当前发行摘要白名单为空；标准 npm `wigolo@0.2.1` 是 Node/npm CLI，会在 probe 前被拒绝，不得以自制 fixture、重命名解释器或 dispatch 绿灯冒充可执行。discovery/fetch/cache 都是只读，watch 仅允许 `list`。禁止 watch mutation、challenge/stealth/CAPTCHA solver/hosted egress/任意 shell/自定义身份等路径；CJK 必须显式 experimental，且结果仍经过本 Skill 的来源、提取和 curator 门禁。

不得把 `OAI-SearchBot`、`ChatGPT-User`、`Claude-User`、`Claude-SearchBot`、`Bytespider` 或其它第三方官方爬虫 UA 当作失败重试身份；UA 表示请求软件/服务身份，不是内容解锁开关。公开页可使用透明自有 UA 与受控 `Accept` / `Accept-Language` 内容协商，但 robots disallow、401/403、验证码、登录墙或访问控制必须停止并入账。

### 4. 并行只用于独立分片

有子 Agent 时按“查询/访问后端/语言或内容类型”划分独立分片，而不是为了凑数一平台一 Agent。使用运行时实际可用的并发槽位并分批复用；不得宣称调用了并未启动的 50 个 Agent，也不得把脚本线程称作独立 Agent。

每个研究 worker 只能把证据推进到 `[_]`。主任务或独立 curator 必须直接查看原始来源支持后，才能写 `[x]` / `reviewer_status=accepted`。主任务负责合并账本、处理转载与冲突、核对所有拟入选条目；Agent 数量本身不构成可信度。

### 5. 登录接力是可恢复 checkpoint

登录型平台被阻塞时：

1. 原子保存 canonical checkpoint：`run_id, topic, platform, stage, exact_probe_or_command, tool_readiness, bridge_state, auth_state, quota_state, authorization, probe_result, error_summary, completed_query_ids, pending_query_ids, candidate_ids, artifact_paths, next_safe_command, created_at, expires_or_unknown`；manifest、查询/来源账本和候选路径由 `artifact_paths` 指向；
2. 继续所有不依赖该登录的独立公开路由；
3. 没有其它有效工作后，一次性告诉用户要打开哪些平台、完成何种登录、完成后回复什么；
4. 恢复时读取同一 `run_id`，先执行 `exact_probe_or_command` 的等价最小只读 probe，再从 `pending_query_ids` 继续；禁止重跑 `completed_query_ids` 或丢掉 `error_summary`。

不得绕过登录墙、付费墙、验证码、robots、限频或私密数据边界。

### 6. 候选不是证据

搜索结果页只负责发现。候选至少保留稳定 ID、平台、标题、原 URL、作者/账号、发布日期或未知标记、访问日期、内容类型、查询与后端、可见互动原值、短摘录/可观察事实和限制。默认只保存元数据、短摘录、分析与链接，不批量复制全文或完整字幕。

入榜条目必须：

- 已读取足够原文、字幕、README/代码或可审计可见内容；
- 引用至少一张由独立 curator 接受的 strong/medium 证据卡；
- 证据卡能通过 `evidence_id` 与来源账本互相解析；
- URL、访问日期、推荐理由、评分输入与审核记录完整；
- 不属于已选代表项的 URL、平台 ID、转载、镜像或同稿簇。

用户若明确限定 `primary-source only` / “只要一手来源”，把它冻结为资格门槛：每张入榜证据卡必须能追到官方、原作者、原始数据/代码或直接可观察的一手对象，并在来源账本标明 `source_type`；普通 `medium` 二手证据不能满足该请求。若一手条目不足，只交付相应 Top K，不用二手材料补满。

自动摘要、标题、热度、多来源表面一致和 worker 自报 `accepted` 都不能单独通过门禁。

### 7. 确定性排名只处理已验收输入

排序前冻结研究包，然后运行：

```bash
python3 scripts/rank_candidates.py \
  --input <run-dir>/candidates.json \
  --manifest <run-dir>/run_manifest.json \
  --queries <run-dir>/queries.tsv \
  --sources <run-dir>/sources.tsv \
  --source-outcomes <run-dir>/source_outcomes.jsonl \
  --evidence-cards <run-dir>/evidence_cards.tsv \
  --platform-coverage <run-dir>/platform_coverage.tsv \
  --lineage-manifest <run-dir>/rank-input-manifest.json \
  --curator-acceptance <run-dir>/curate-result.json \
  --output-dir <new-nonexistent-output-dir> \
  --top 50
```

脚本必须失败关闭：缺少研究上下文、证据引用不可解析、required 平台仍 pending、非公共 URL、账本不守恒或审核不独立时，不能产生完成通过。评分为相关性 35、来源质量 20、证据 20、平台内可比互动 15、新鲜/适用性 10；未观测互动得 0，不因样本数得到默认奖励。热度不改变证据等级。

`rank-input-manifest.json` 必须在 curator 决策前冻结 ranker 实际读取的全部必需输入（包括 `source_outcomes.jsonl`）及其原始 SHA-256、记录数与 ID-set 摘要；curator 工件再绑定该 manifest。router 和 standalone ranker 都要在创建输出目录前核对同一组文件、候选/证据/来源/outcome 集合，禁止 curator 验收集合 A 而 ranker 读取集合 B。

冻结命令：

```bash
python3 scripts/lineage_contract.py freeze-rank-inputs \
  --run-dir <run-dir> \
  --run-id <run-id>
```

合格去重后不足 `top_n` 时交付真实 Top K 与缺口，禁止填充或声称 Top N 完成。平台覆盖与最终入选分布分别报告，不设平台保底名额。

### 7.1 可选横纵研究模式

`research_mode=hengzong` 时，在常规候选、来源与证据账本建立后读取 [横纵研究模式](references/hengzong-research.md)，运行 `scripts/hengzong_contract.py`。该模式固定完整横向/纵向 workstream 拓扑、有界地域×语言矩阵、明确 `event_date/published_at/as_of/start_date`，并要求 claim-source ledger、independence group、反证、`past_event → present_effect → implication`、三个带 trigger/invalidator 的情景和目标匹配的机会/决策路径。缺口只有经过 query/query_path/route 均不同的至少两路补搜后才可 retained；最终 brief 必须由非 worker 的 curator 对精确文件和完整 claim/workstream 集合验收。

### 8. 先验收本地研究包

最低产物为：

- `run_manifest.json`、`queries.tsv`、`sources.tsv`、`candidates.json`、`evidence_cards.tsv`；
- `query_plan.json`、`source_outcomes.jsonl` 与 `research_checkpoint.json`（发生暂停时）；多路召回融合时另有 `fusion_result.json`。
- `ranking.json`、`top.json`、`rejected.json`、`run_summary.json`、`package_validation.json`、`report.md`；
- `source_gap_backlog.md` 与 `platform_coverage.tsv`。
- `engine_probe.json`、`engine_plan.json` 与 `engine_execution.json`（执行过三引擎路由时）；其中必须能解释为何选择/跳过/降级每个后端。
- `hengzong_plan.json`、`hengzong_brief.json` 与 `hengzong_curator_acceptance.json`（启用横纵模式时）。
- `wigolo_probe.json`、`wigolo_plan.json` 与 `wigolo_result.json`（显式启用 Wigolo 且实际执行时）。

只在结构校验通过且 curator 完成语义验收后，把报告称为最终研究结果。机器绿灯不证明摘录真的支持主张。

创建或大幅修改本 Skill 时，用 [前向验收场景](references/evaluation-scenarios.md) 做独立行为测试；普通运行不需要加载该文件。

### 9. 飞书发布

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
