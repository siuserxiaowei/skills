# 横纵研究模式合同

横纵研究模式是 `cross-platform-top50` 的可选深度综合门禁。它不替代平台发现、抓取、证据策展或确定性排名；它把已经取得的材料组织成一份带明确日期、范围和反证的决策简报，并在独立策展者验收前禁止声称 `verified`。

本实现为独立原创合同设计，只借鉴通用研究方法；未复制限制性许可证项目的代码、提示词或文字。

## 1. 何时启用

当用户要求行业判断、机会地图、趋势推演、复杂决策或根因诊断时，可在常规 Top 50 策展之后启用。普通榜单、链接收集或单篇摘要无需承担这套额外成本。

模式包含四个版本化合同：

- `top50-hengzong-request/v1`：目标、日期、地区、语言和查询预算。
- `top50-hengzong-plan/v1`：完整规范 workstream 拓扑与有界查询组。
- `top50-hengzong-brief/v1`：来源、主张、时间链、情景、机会与未解决缺口。
- `top50-hengzong-curator-acceptance/v1`：独立策展者对精确 brief 文件的验收。

JSON Schema 位于 `assets/engine-contracts/hengzong-*.schema.json`，运行时语义验证器位于 `scripts/hengzong_contract.py`。Schema 提供结构边界；运行时验证器负责跨字段集合、时间、哈希和独立性约束。两者缺一不可。

## 2. 请求与计划

请求必须给出：

- `brief_date` 和带时区的 `as_of`；两者按 UTC 日期一致。
- `goal.type`：`opportunity`、`decision`、`landscape` 或 `diagnosis`。
- 明确的 `objective`、`audience` 和待支持的 `decision`。
- `scope.start_date/end_date`、地区列表和语言列表。
- `max_geo_language_cells`、`max_queries_per_group`、`max_total_queries`。
- 实际研究 worker ID；后续 curator 不得与其重合。

计划固定包含三条横向和三条纵向 workstream：

1. 横向：边界与基准。
2. 横向：当前信号与反证。
3. 横向：采用与利益相关方。
4. 纵向：过去事件到当前效果的机制。
5. 纵向：三情景及失效条件。
6. 纵向：根据目标类型生成机会、决策反转、结构转移或干预否证路径。

`canonical_workstreams` 不是调用方可自由删减的清单。验证器会依据已声明目标重新生成规范拓扑并逐项比较，所以删掉 workstream、修改关联查询、更新计数，再重算 `plan_id` 与摘要，仍会失败。

每个 `geography × language` 单元都有查询组，默认最多三种互补意图：

- `landscape`：定义、参与者、采用和数据。
- `primary_and_counterevidence`：一手材料、实测、争议和反例。
- `timeline_and_future`：事件、影响、情景、机会和风险。

默认模板只是检索任务合同；执行层仍应按平台、授权和来源类型选择具体搜索路由。硬上限为 24 个地区—语言单元、每组 8 条、总计 192 条，避免笛卡尔积无界膨胀。

## 3. 时间与证据账本

Brief 的每个来源保存：

```text
source_id, url, title, publisher, independence_group,
published_at, as_of, pre_scope_context
```

每条主张保存：

```text
claim_id, text, temporal_role, event_date, as_of,
pre_scope_context, scope, evidence_links
```

每个 `evidence_link` 都必须有 `source_id`、`support/refute`、可复查的 `locator`、`evidence_date` 和证据适用 `scope`。搜索摘要只能用于发现；没有原文定位符就不能进入该账本。

`independence_group` 表示共同所有权、同一原始数据、转载链或同一研究团队。多个 URL 若属于同组，只算一个独立证据组。已发生的 `past_event` 和可观察的 `present_effect` 至少需要两个独立组；整份账本至少保留一条 `refute` 关系。`implication` 是条件性判断，不伪装成已经发生的事实。

时间字段有不同语义：

- `event_date`：主张所述事件实际发生日；未来含义可为 `null`。
- `published_at`：来源公开时间。
- `as_of`：本次简报的证据截止时刻。
- `pre_scope_context`：事件或来源早于研究窗口，只能作为背景上下文；该布尔值由日期关系校验，不能自报。

## 4. 纵向解释与未来判断

至少建立一条：

```text
past_event → present_effect → implication
```

链条必须引用三种正确角色的不同 claim，并说明 `mechanism` 与 `caveat`。这表达“有证据约束的解释”，不把相关性冒充成唯一因果。

未来部分固定输出三个互斥方向：

- `constrained`：受限情景。
- `continuity`：延续情景。
- `acceleration`：加速情景。

每个情景至少有一项可观察 trigger 和一项 invalidator，包含检查日期和对应 claim。没有失效条件的预测不得通过。

`goal.type=opportunity` 时至少输出一个未来行业机会项，包含行业、时距、未满足需求、促成变化、可交付方案、受益者、约束、领先指标及主张引用；至少引用一条 `implication`。

## 5. 两路补搜与保留缺口

未知不是失败，但不能用“尚无资料”一句话跳过。一个 gap 只有在至少两次补搜后才允许标记为 `retained`，且每次尝试的以下三个维度都必须彼此不同：

- `query`：查询文本不同。
- `query_path`：例如平台原生、监管文件、论文索引、代码仓库或作者资料页。
- `route`：例如授权平台搜索、公开 Web 索引、官方 API 或用户提供材料。

若只是把同一句查询交给同一个路由重跑两次，不构成独立补搜。每次还要记录执行时刻和限定结果：无结果、无合格证据、独立性不足、授权阻塞、或证据冲突。

## 6. 策展验收与失败关闭

研究 worker 只能产生 `ready_for_curator` 或 `blocking` brief，禁止自报 `verified`。独立 curator acceptance 必须：

- curator ID 不在 brief 的 `producer.worker_ids` 中。
- 绑定 brief 原始文件 SHA-256 和 brief 内嵌内容摘要。
- 覆盖完整规范 workstream 集合。
- 接受完整 claim 集合；部分接受要先退回修订 brief，不能伪装成整份验收。

最终 `validate_brief` 成功后才返回 `status=verified`。缺少独立 acceptance 返回非零退出码 3；结构、摘要或绑定错误返回非零退出码 2。

Brief 自身状态为 `blocking` 时必须提供机器可读的 `blocking_reasons[{code,message}]`。CLI 把第一项原样返回：

```json
{"status":"blocking","code":"source_access_blocked","message":"关键来源需要用户授权后才能继续。"}
```

不得在阻塞状态下返回零退出，也不得把阻塞 brief 写成完成或已验证。

## 7. CLI 示例

建立并验证计划：

```bash
python3 scripts/hengzong_contract.py build-plan \
  --request run/hengzong-request.json \
  --output run/hengzong-plan.json

python3 scripts/hengzong_contract.py validate-plan \
  --plan run/hengzong-plan.json
```

策展者在读取精确 brief 后建立验收；每个规范 workstream 和 claim ID 均需显式列出：

```bash
python3 scripts/hengzong_contract.py build-acceptance \
  --brief run/hengzong-brief.json \
  --curator-id curator-independent-01 \
  --workstream-id H1-boundary-and-baseline \
  --workstream-id H2-current-signals-and-counterevidence \
  --workstream-id H3-adoption-and-stakeholders \
  --workstream-id V1-past-to-present-mechanisms \
  --workstream-id V2-scenarios-and-invalidators \
  --workstream-id V3-future-value-paths \
  --claim-id claim-past \
  --claim-id claim-present \
  --claim-id claim-future \
  --output run/hengzong-curator-acceptance.json
```

最终验证：

```bash
python3 scripts/hengzong_contract.py validate-brief \
  --brief run/hengzong-brief.json \
  --plan run/hengzong-plan.json \
  --acceptance run/hengzong-curator-acceptance.json
```

成功输出 `status=verified`；任何不完整拓扑、时间漂移、来源定位缺失、错误因果角色、情景缺失、伪独立 curator、brief 文件替换或不充分补搜均失败关闭。
