# 跨平台 Top 50 研究总提示词

把下面代码块粘贴到 Codex 对话中作为便携提示词使用。它不是 shell 命令，假定 `cross-platform-top50` Skill 包已经存在于本地；在 Codex 中唯一入口是 `$cross-platform-top50`。不能仅凭提示词假定本机已有 OpenCLI、agent-reach、飞书 CLI、登录态、额度或 50 个可用子 Agent。

```text
使用本地已安装的 $cross-platform-top50 完成下面任务，并严格遵守该 Skill 的 research contract、platform routing 与 Feishu publish contract。

[输入]
- 主题：《{{TOPIC}}》
- 用途：{{PURPOSE | 默认：建立可复用的主题知识库}}
- Top N：{{TOP_N | 默认：50}}
- 时间范围：{{TIMEFRAME | 默认：不限；时效性主张优先近 24 个月}}
- 语言/地域：{{LANGUAGES_AND_GEOGRAPHY | 默认：中英文、全球}}
- 平台范围：{{PLATFORMS | 默认：Skill 定义的 canonical 28}}
- 飞书发布模式：{{PUBLISH_MODE | local / feishu-new-space / feishu-existing-space}}
- 飞书目标：{{FEISHU_TARGET | feishu-new-space 时默认“<主题>｜跨平台 Top <N> 研究”}}
- 本地执行引擎：{{ENGINE_MODE | auto / python / go / rust / hybrid；默认 auto}}
- 双引擎复核：{{DUAL_RUN | false / true；默认 false}}

[输入门禁]
1. 《》、空白、`{{TOPIC}}`、`<主题>` 或其他未替换占位符都表示主题为空。不要开始检索，也不要自动猜题；只请求用户补一个真实主题。
2. 便携提示词默认使用本地 Skill 包。若 `$cross-platform-top50` 不存在或不可读，明确报告缺失，不能假装已经执行其合同。
3. 把用户点名平台设为 required；其余保留 Skill 的 required / important / adjacent 优先级，并独立判断是否 not_applicable。主题明显不适用的平台可记 not_applicable，但必须说明依据，不能用它掩盖 blocked。

[执行]
1. 先生成 run manifest：主题、用途、范围、canonical 平台层级、候选池目标 `max(3N,150)`、停止条件、外部写入边界和工作假设。
2. 真实检索前运行只读体检，并对计划使用的每个后端做最小真实 probe。按 Skill 合同分开记录 `tool_readiness`、`bridge_state`、`auth_state`、`quota_state`、当前任务 `authorization` 和 `probe_result`；工具安装不等于登录成功，doctor 通过也不等于本次查询有结果。
3. 先运行 Skill 的 Python engine router，对 Python、Go、Rust 三个本地后端做真实合同 probe 并保存 plan。三套结构长期保留、互补使用，不是从 Python 迁移到 Go/Rust，也不表示每次三跑。`auto` 按阶段选择：Python 负责平台 CLI/Browser、URL 发现、抓取后提取、证据策展、排名和飞书；Go 只批量抓已经授权、已经发现且由 manifest SHA-256/job-set digest 冻结的公共 URL；Rust 只做本地规范化、指纹和去重。Go 的 `transport_success` 只表示透明 UA、robots、2xx 和响应工件通过；Python extraction 必须把登录墙、验证码、挑战页、付费墙、空白或不完整页标成非 content，禁止产生候选。完整 hybrid 通常按 Python discovery→Go fetch→Python extraction→Rust process→Python curate/rank/publish；每个 handoff 必须绑定真实文件 SHA、合同、run/stage/producer/result digest 与 ID-set，Rust 输入由已验证 extraction 原子生成。rank 前冻结六文件 `rank-input-manifest.json`，curator 和 ranker 必须绑定同一候选、证据和来源集合；缺少提取产物、accepted curator 产物或 lineage 时失败关闭且不创建输出目录。选择后端看实现/返工、测试、依赖/部署、安全维护、平台适配、故障定位、运行资源、验证与 Token 的总成本。源码或二进制存在不等于 ready；用户强制后端而能力不满足时失败关闭。高风险或 `dual_run=true` 才双跑比较，不无条件把任务重复三遍。
4. 优先使用 Skill 路由中真实存在且 probe 通过的 OpenCLI 专用适配器；Browser 型 OpenCLI 适配器需要 Browser Bridge，登录型平台还需要当前浏览器会话。`ego-browser`/ego-lite 只是默认禁用的候选 Python browser_session 后端；供应链、CLI 数据流、二进制许可与会话隔离门禁关闭后，仍需用户对当前任务显式 opt-in、已安装且真实 probe 通过，并使用低敏感独立 profile。不得自动安装、移除 quarantine、迁移 Chrome 全量资料或更新。不要自动执行 pipx/brew/pip/cargo/go install 或升级，也不要假定未 probe 的 MCP、包或二进制存在。
5. 每个平台做精确/别名查询与高价值意图查询；易变主题再加日期/版本词。查询账本记录计划后端、实际后端、时间、结果数、错误、重试和降级。搜索摘要只用于发现，不能当 accepted evidence。
6. Exa 遇到 429/额度错误时记录 `quota_state=rate_limited|exhausted`，最多一次有界退避重试，然后切到已 probe 通过的 Google/Brave/DuckDuckGo 或平台专用适配器；不得用并发或换账号规避限流。
7. 登录/验证码需要用户时，先完成其他独立只读工作，原子保存 canonical checkpoint：`run_id, topic, platform, stage, exact_probe_or_command, tool_readiness, bridge_state, auth_state, quota_state, authorization, probe_result, error_summary, completed_query_ids, pending_query_ids, candidate_ids, artifact_paths, next_safe_command, created_at, expires_or_unknown`。一次性请求用户登录；用户回复后读取同一 `run_id`、再次 probe，只续跑 `pending_query_ids`，不要重跑 `completed_query_ids`，也不要索取密码/Cookie/token。
8. 对原页提取稳定 ID、平台、标题、URL、作者、日期、访问日期、内容类型、语言、可见互动、窄摘录/观察、相关性和限制。不批量复制受保护全文。
9. 先规范 URL，再用标题+摘录/正文指纹处理转载与一稿多发。只有 curator 接受、strong/medium 证据且 URL/访问日期/可审计摘录齐全的条目进入可发布榜单。
   - 若本次请求明确限定 `primary-source only` / “只要一手来源”，再加一手来源硬门槛：官方、原作者、原始数据/代码或直接可观察对象；`medium` 二手证据不能补满 N。
10. 按 Skill 的 deterministic 评分和稳定同分规则排名。互动是热度信号，不是正确性。合格去重后不足 N 时只交付实际 Top K 和缺口；始终称“本次检索范围内 Top K/N”，不声称全网绝对排名。
11. 不得虚报平台覆盖、引擎可用性、并发量、子 Agent 数、候选数、原页读取、登录状态或飞书写入。只报告真实工具输出和已审阅产物；可用并发由当前环境决定，不能承诺“调用 50 个 Agent”。
12. 先完成本地研究包与门禁验证，再处理飞书。`local` 不执行任何外部写入；`feishu-new-space` / `feishu-existing-space` 只有在用户当前请求明确要求发布时才是发布授权。
13. 飞书发布必须读取 Skill 的发布合同，显式 user 身份，先认证、全量查重和 dry-run，再按串行顺序创建/复用空间、创建/复用 docx 节点、写正文，并回读核验真实空间/节点 ID、标题、记录数、来源 URL、publish_id 和摘要。不得覆盖、删除、改权限或虚构链接。

[HTTP 身份门禁]
- 默认请求返回空白或明显不完整时，可尝试平台专用只读适配器、Jina/reader、真实浏览器渲染，以及受控 `Accept`/`Accept-Language` 内容协商，并记录差异；不得把 `OAI-SearchBot`、`ChatGPT-User`、`Claude-User`、`Claude-SearchBot`、`Bytespider` 等第三方官方爬虫 UA 当作解锁身份。
- Go collector 与 Python 直接 HTTP 路由使用固定透明自有 UA，身份合同覆盖成功、失败和策略阻断记录；平台适配器、reader 与浏览器会话使用真实 backend/probe 身份，不接受调用方指定 UA。Go 执行 robots；robots disallow、401/403、验证码、登录墙或访问控制必须停止和入账，不得通过换 UA、换账号或并发规避。
- Go 只自动跟随同源重定向；跨源目标必须回到 discovery/授权并作为新 job 冻结，不能由重定向自动扩大已授权 URL 集。

[完成门禁]
- required 平台无 pending；important 平台已处理或有明确缺口；blocked/not_applicable/rejected 都有依据和最小下一步。
- 称“20+ 平台完成”前，至少 20 个 canonical 渠道有已处理状态且至少 12 个平台真实召回候选。发现引擎结果必须回源。
- 可发布榜单每条都有原链接、访问日期、可审计摘录、accepted reviewer 状态和 strong/medium evidence；重复与总分均可重放检查。
- 本地包存在且可读；使用 engine router 时，probe/plan/execution 可重放且降级原因完整。若请求飞书发布，只有回读通过才可声称已新建/写入；认证、权限或登录需用户动作时，交付 checkpoint 和 resume 指令，不虚报完成。

[交付]
先给实际完成状态（Top N 或合格 Top K），再给决定性洞察、榜单与详情、平台覆盖/证据/冲突/缺口、六字段能力状态和 checkpoint、本地产物路径；飞书已真实发布且回读通过时，最后附 API 返回的真实链接或 ID。
```

## Codex 极简入口（粘贴到对话，不在终端执行）

```text
$cross-platform-top50 研究《真实主题》，用于《决策/用途》；覆盖 canonical 28，交付本次检索范围内 Top 50 和可审计本地研究包。验收后，按当前明确授权新建飞书知识库《知识库名》并回读验证。登录型平台需要时保存 checkpoint，请我完成一次登录接力后 resume；不得绕过访问控制，也不得虚报覆盖或并发。
```

只要本地报告时，将最后两句替换为：

```text
只生成并验证本地研究包，不执行任何飞书或其他外部写入。
```
