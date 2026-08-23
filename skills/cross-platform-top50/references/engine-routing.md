# 三引擎能力路由

三套结构是长期并存的互补后端，不是迁移阶段，也不是性能竞赛：

| 结构 | 稳定职责 | 不声称的能力 |
|---|---|---|
| Python 控制面与 ranker | 平台 CLI、浏览器登录接力、控制与合同校验、最终排名、发布编排 | 不因 ranker 可启动就声称公网抓取 |
| Go collector | 已获授权且已发现的公开 HTTP(S) URL fetch、透明自有 UA、robots、并发、限速、重试、checkpoint、响应工件 | 不负责 URL discovery，不接管浏览器登录、平台账号或最终排名 |
| Rust processor | 大批量 URL 规范化、安全预检、内容指纹、精确簇与近重复复核标记 | 不执行网络 fetch、不替代独立 curator |

## 选择依据

`scripts/engine_router.py` 先真实 probe，再按一个请求的阶段、工作量、来源类型、风险、能力要求与 `engine_mode` 生成计划。文件或源码目录存在不等于 `ready`。研究范围同时包含多种来源时，不要把不同访问边界压成一个 router request；先用 [多来源请求编译](route-bundle-compilation.md) 生成按 access kind / stage 聚合的确定性 shard，再分别 plan。

开发成本不等于 Token 成本。路由与演进决策看总成本：实现和返工时间、测试矩阵、依赖与部署、安全维护、平台变化适配、故障定位、运行资源、结果验证以及 Token 都要计入。优先复用已经验收的实现；只有新后端能降低某一阶段的总成本或不确定性时才让它承担该阶段。三套长期保留不表示同一任务默认执行三遍。

```bash
python3 scripts/compile_route_bundle.py \
  --input <run-dir>/route-scope.json \
  --output <run-dir>/route-bundle.json

python3 scripts/engine_router.py probe --json

python3 scripts/engine_router.py plan \
  --input assets/engine-contracts/example-request.json \
  --output /tmp/top50-router-plan.json

python3 scripts/engine_router.py execute \
  --plan /tmp/top50-router-plan.json \
  --output /tmp/top50-router-result.json
```

`public_http` 的 fetch/full 请求还必须携带 `public_http_binding`：精确绑定 `go-collector-input.json` 路径、原始文件 SHA-256、按 `job_id` 排序的 job-set SHA-256 与 job 数。router 生成 plan 时原样冻结该对象，execute 在启动前重新核对，Go collector 再通过必需的 `--expected-input-sha256` 从同一文件描述符读取、校验并解码；文件或 job 集合被替换时不得发网。

`probe` 默认从 Skill 根解析源码后端：

- Python：执行 `python3 scripts/rank_candidates.py --help`，能力只登记为控制、平台编排、rank 与发布编排；
- Go：执行 `go -C engines/go-collector run . probe --json`；
- Rust：执行 `cargo run --quiet --manifest-path engines/rust-processor/Cargo.toml -- probe --json`。

请求里的 `engine_paths.python|go|rust` 可覆盖为预编译二进制或替代 ranker 路径。缺少 toolchain、启动失败、超时、非零退出、非 JSON、错误 ID/版本/status/contract 或空能力数组都记为 `unavailable`，不能只靠 `Path.exists()` 宣称就绪。

Go 与 Rust 的 canonical probe 必须使用这五个字段；下面是当前 Go 0.2.0 示例，Rust 报告自身版本与 ID：

```json
{
  "contract_version": "top50-engine/v1",
  "engine_id": "go-collector",
  "engine_version": "0.2.0",
  "status": "ready",
  "capabilities": ["public_http_collect"]
}
```

router 不接受外部 probe 用 `contract`、`id`、`version` 等旧别名，也拒绝 canonical 五字段之外的未知字段；计划里的内部 probe 证据会另行保存命令、退出码和有界 stdout/stderr。

## 选择矩阵

| 请求 | 首选 | 回退 |
|---|---|---|
| `platform_cli` / `browser_session` discovery 或 fetch | Python | 无网络引擎替代；需要原平台接力 |
| discovery（包括公开 HTTP URL 发现） | Python | 无；Go 不负责查询面或 URL 发现 |
| `public_http` medium/large fetch | Go | Python 平台/工具编排 |
| large process | Rust | Python 合同校验与既有处理 |
| rank | Python | 无；最终排名合同只有 Python ranker 实现 |
| large + public HTTP + full | Python discovery → Go fetch → Python extraction → Rust process → Python curator → Python rank | 每阶段按自身 fallback chain 降级 |

`engine_mode=python|go|rust` 是强制模式：引擎不存在、probe 失败、不能承担请求阶段或缺少 required capability 时立即失败关闭，绝不静默降级。只有 `engine_mode=auto|hybrid` 可以按计划中的 fallback chain 降级；`hybrid` 明确要求按可用能力组合，`auto` 使用同一矩阵自主选择。强制语言也不能绕过 Python extraction 或 curator gate。`engine_mode` 是唯一公开参数名，机器合同不接受 `preference` 别名。

## 双引擎验证

- `dual_run=true` 必须找到另一套能承担同一阶段的 ready 引擎，否则拒绝生成可执行计划。
- `risk=high` 会优先添加独立验证；如果不存在独立验证者，计划保留 `high_risk_dual_validation_unavailable`，调用方不得把它误读为已双验。
- 只为一个决定性阶段添加一个 validator；不会把同一工作无差别重复给 Python、Go、Rust 三次。
- validator 若由 Python 主研究工作流编排，计划会为它生成独立的 `*-validator-result.json` completion artifact；同一 plan 回放后才能与 primary 比较。
- 执行结果只去掉根级 engine/version/timestamp/digest 等易变 envelope，再按阶段计算完整业务投影：fetch 覆盖全部 results，process 覆盖 candidates、exact clusters、near-duplicate reviews 与 counts，rank 覆盖 summary 与入选集合；候选内部的 status/stage/engine_id 仍参与比较。集合顺序不参与跨实现语义，processor 的 `cluster_id` / `review_id` 只作为引擎本地定位符；成员、代表项、证据、相似度、处置与 counts 必须一致。双跑不一致返回 `validation_mismatch`，不会静默选择方便的答案。

## 执行安全与中间合同

router 只执行 argv 数组，调用 `subprocess.run(..., shell=False)` 的默认语义；字符串命令直接拒绝。每步有超时，stdout/stderr 被捕获并限制长度，非零退出、缺少输出、损坏 JSON 与输出合同漂移都失败关闭。

计划里的 `fallback_chain` 是下一次恢复计划和审计证据，不是失败后立刻重放网络或处理动作的授权。运行时失败会先停止并保留真实错误；主工作流核对幂等性、能力与输入 checkpoint 后，才能重新 plan/execute 兼容后端。显式强制模式始终没有运行时降级。

计划只负责写出确定 argv、输入/输出合同和路径，不凭空制造阶段输入：

- Go 输入 `top50-collector/v1`，输出 `top50-collector-result/v1`；模板见 [go-collector-input.example.json](../assets/engine-contracts/go-collector-input.example.json)。Go 的结果是原始响应工件，不含可供 Rust 直接消费的完整候选元数据。
- Go `collect` 必须同时接收 `--expected-input-sha256 <64 lowercase hex>`。collector 只打开输入一次，从同一文件描述符读取完整原始字节，先核对 exact SHA-256，再从同一 byte slice 解码；缺参、摘要格式错误或不匹配都在启动 collector/fetch 前失败关闭，防止 plan/precheck 与 process 读取不同 manifest。
- Go 只跟随与原作业同 origin 的重定向，并对每个新路径重新执行 robots、公网解析和限速。跨 origin 目标不属于冻结的 job 授权集，返回 `cross_origin_redirect_requires_authorization`；调用方必须把最终 URL 重新送回 discovery/授权并作为新 job 冻结，不能在一次 fetch 内自动扩权。
- Go 与 Python 直接 HTTP 路由都使用固定透明 UA `TopFiftyCollector/0.1 (+https://github.com/siuserxiaowei/skills)`；Go 另以自有 product token `TopFiftyCollector` 与 `*` 执行 RFC 9309 robots。该身份合同适用于成功、失败和策略阻断记录，调用方不能注入或改写 `User-Agent`。平台适配器、reader 与浏览器会话改由 `backend_id` / `provider_id` / probe 证明实际后端，canonical fetch 工件不得夹带调用方选择的 UA。作业 header 只接受大小写不敏感的 `Accept`、`Accept-Language`、`Accept-Encoding` 三项；验证后键统一为 canonical spelling，大小写折叠后重复的键拒绝，未知键拒绝。`Accept-Encoding` 若出现只能是 `identity`，safe HTTP transport 同时禁用自动压缩/解压；请求协商值和响应 `Content-Encoding`、`Vary`、语言必须保留在抓取 provenance。
- JobResult 的 2xx 状态固定为 `transport_success`，只证明 HTTP 响应体按上限完整落盘并取得 digest，不证明正文相关、可用、已登录或通过内容门禁。200 登录样式 HTML、204 空正文和服务端主动返回的 206 都是 `transport_success`；Go 不对 HTML/登录墙做语义分类，Python extraction/控制面必须读取工件后另行判断。robots 不允许、401/403、验证码或其它可见访问控制阻塞仍停止并入账，不改成第三方 AI crawler 身份。
- Python extraction 必须回读 Go 工件并生成 `top50-extraction-result/v1`，至少保留稳定候选 ID、原始工件引用/digest、来源 URL、title、author、published_at 与 excerpt；没有 canonical `status=complete` 工件时 Rust 不会启动。
- Go 的每项 `transport_success` 只表示透明 UA、robots、2xx、响应上限与工件落盘/哈希均通过，不表示正文可用。Python extraction 必须把每个上游项分类为 `content|login_wall|captcha|challenge|consent_wall|paywall|access_denied|empty_or_incomplete|unsupported_media|extraction_error`；只有 `content` 能产生候选。
- Rust 输入 `top50-processor/v1`，输出 `top50-processor-result/v1`；模板见 [rust-processor-input.example.json](../assets/engine-contracts/rust-processor-input.example.json)。生产 `process` CLI 强制接收 `--expected-input-sha256 <64 lowercase hex>`；处理器只打开输入一次，从同一字节快照校验摘要并解析，避免控制面校验后同路径内容被替换。
- Python rank 输入是完整、已验收的研究包，输出适配为 `top50-ranking-summary/v1`。
- Python 的平台 CLI/浏览器 discovery/fetch、extraction 和 curate 步骤标为 `execution_mode=orchestrated`；它们必须由主研究工作流执行，router 不会假装 `rank_candidates.py` 能抓网络或完成语义策展。

每次 `process → curate` handoff 必须同时保留 raw fetch/processor result、来源 URL、工件 digest 和处理诊断，不能只传清洗后的候选。curator 必须回读原始来源并产生 `top50-curator-acceptance/v1`：只有 `status=accepted` 才能解除 rank gate。缺失 artifact、错误 contract、pending/rejected 或任何未 accepted evidence 都暂停，router 不会执行 ranker。

Python orchestrated completion 不是四字段状态空壳。discovery/fetch/extraction/process/curate 工件必须包含 producer、input bindings、守恒 counts、阶段业务集合和可重算 `result_digest_sha256`，并通过 router 的阶段语义 validator；同一 validator 同时用于 completion 恢复和 process/rank gate。伪装 UA、跳过 robots、未绑定 URL、登录/验证码 outcome 产生候选或 curator 账本不守恒都会失败关闭。

`input_bindings` 是固定 DAG，不是自报字符串数组。每个绑定都要从同一文件描述符解析并核对原始文件 SHA-256、contract/run/stage/status、producer、内嵌 result digest、记录数与记录 ID-set 摘要；空数组、额外前驱或替换后的同路径文件都失败。阶段前驱为 scope→discovery、discovery/frozen manifest→fetch、fetch→extraction、extraction→process、process+rank-input manifest→curate。Rust process 的 canonical 输入由已验证 extraction 工件原子生成，候选 ID 必须三方守恒，不能消费预放的陈旧 `rust-processor-input.json`。

rank 前先冻结 `top50-rank-input-manifest/v1`，精确绑定 `candidates.json`、`run_manifest.json`、`queries.tsv`、`sources.tsv`、`evidence_cards.tsv`、`platform_coverage.tsv` 六个文件。curator acceptance 必须绑定同一 manifest；router 与 standalone ranker 都在 subprocess 和输出目录创建前复验文件 SHA、记录 ID、候选 decision/accepted 集合及 evidence→source 引用。任意 A/B 换包都返回失败，不产生部分排名目录。

先生成并核对每一阶段的输入文件，再运行 `execute`。每个 `orchestrated` 步骤在计划中绑定不可变的 `completion_artifact` 路径、contract、status、run_id 和 stage：缺失时返回 `pending_orchestrator`；主研究工作流完成该步并原子落盘后，重放同一 plan 会把它记为 `covered` 并继续。artifact 存在但 contract/status/run_id/stage 任一不符时失败关闭，不能通过手改 plan 或借用其它 run 的结果续跑。

## 合同资产

- [route-bundle-request.schema.json](../assets/engine-contracts/route-bundle-request.schema.json)
- [route-bundle.schema.json](../assets/engine-contracts/route-bundle.schema.json)
- [router-request.schema.json](../assets/engine-contracts/router-request.schema.json)
- [router-plan.schema.json](../assets/engine-contracts/router-plan.schema.json)
- [router-result.schema.json](../assets/engine-contracts/router-result.schema.json)
- [external-probe.schema.json](../assets/engine-contracts/external-probe.schema.json)
- [rank-input-manifest.schema.json](../assets/engine-contracts/rank-input-manifest.schema.json)

JSON Schema 是跨语言交换规范；Python CLI 仍执行同等级的标准库运行时校验，因此部署不依赖第三方 schema 包。

## 可选登录浏览器

`ego-browser` / ego-lite 可以补足动态 DOM、用户登录接力与独立浏览器 Task Space，但它属于 Python 的候选 `browser_session` 访问后端，不是第四套处理引擎，也不替代 OpenCLI 专用适配器。当前默认禁用；先读取并关闭 [ego-lite 适配评估](ego-lite-assessment.md) 的供应链、数据流、许可与会话隔离门禁，再要求用户显式 opt-in、低敏感独立 profile 和真实最小 probe。默认不安装、不迁移 Chrome 数据、不自动升级。原始 CDP、任意 fetch、上传/下载和会话变更默认不在只读研究授权内。

## HTTP 身份依据

第三方官方 crawler token 只描述其官方服务流量，不能由本 Skill 借用。实现和复验以 [OpenAI crawler 说明](https://developers.openai.com/api/docs/bots)、[Anthropic crawler 说明](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)、[RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) 与 [Cloudflare Verified Bots](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) 为当前依据；易变页面在改变策略前重查。
