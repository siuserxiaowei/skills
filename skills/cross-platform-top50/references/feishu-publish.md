# 飞书知识库发布合同

本合同只负责把已经通过研究门禁的本地快照发布到飞书，不在飞书端补研究数据。发布是外部写入：只有用户当前命令明确要求“新建/发布/写入飞书知识库”时，才允许创建空间、节点和空白文档正文；研究、预览或生成报告只做到本地制品、只读解析和 dry-run。

## 1. 运行时真源与安全边界

`lark-cli` 的参数和返回结构会随版本变化。每次发布会话开始时必须记录 `lark-cli --version`，并用下面的**运行时真源**读规则；不得只读本机 `.agents/skills`、凭记忆选 flag，或从本文件复制旧参数直接写入：

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-wiki
lark-cli skills read lark-doc
lark-cli skills read lark-doc references/lark-doc-fetch.md
lark-cli skills read lark-doc references/lark-doc-md.md
lark-cli skills read lark-doc references/lark-doc-update.md
lark-cli skills read lark-doc references/style/lark-doc-style.md
lark-cli skills read lark-doc references/style/lark-doc-update-workflow.md
lark-cli skills read lark-wiki references/lark-wiki-space-list.md
lark-cli skills read lark-wiki references/lark-wiki-space-create.md
lark-cli skills read lark-wiki references/lark-wiki-node-list.md
lark-cli skills read lark-wiki references/lark-wiki-node-get.md
lark-cli skills read lark-wiki references/lark-wiki-node-create.md
lark-cli skills read lark-wiki references/lark-wiki-member-list.md
```

同时对本次实际使用的每个 shortcut 执行 `--help`；原生 API 则先执行 `lark-cli schema <service.resource.method> --format json`。如果内嵌 Skill、help、schema 与本合同示例冲突，停止写入并以当前 CLI 真源修订计划；安全边界仍取更严格者。

- 全程显式 `--as user`；不在失败后静默切换 bot。使用 `auth status --json --verify` 建立身份锁：该命令成功形态不保证有 `ok` 字段，必须要求进程退出码 0、顶层 `verified=true`、`identities.user.status="ready"`、`identities.user.available=true`、`identities.user.verified=true`、`identities.user.tokenStatus="valid"`，并取得非空 `identities.user.openId`。在每个 apply 前和最终验证后重查，openId 或 user 状态变化即停止。
- 缺 scope 时按 `lark-shared` 的 split-flow 申请最小权限并暂停；原样展示授权 URL 与二维码。不得缓存旧 URL/device code，不输出 app secret、token、Cookie。
- 所有命令必须用结构化 argv 数组调用（例如 `execve` / `exec.Command`），每个动态值只占一个 argv 元素。禁止 `sh -c`、`eval`、把标题或 URL 拼进命令字符串，也禁止用未经引用的 shell 变量、command substitution 或 heredoc 承载研究内容。
- 多行正文用 cwd 内相对 `@file`（或安全 stdin）；不得把不可信标题、Markdown、URL直接作为 shell 语法。当前 CLI 的文件参数不接受绝对路径。
- 删除、移动、owner 转移、成员/权限变更、公开分享、覆盖已有正文都不在本合同自动授权范围。exit 10 / `confirmation_required` 必须展示原 action、risk、精确 argv，得到用户对该动作的单独确认后才能在原 argv 末尾追加 `--yes`。

## 2. 对象模型、稳定空间身份与快照身份

### 2.1 空间是稳定容器

一个规范化主题默认对应一个受管空间：

- `space_key = "cross-platform-top50/space/v1:" + sha256(utf8(NFKC(topic).trim().replace(/\s+/gu, " ")))`。
- `managed_by = "cross-platform-top50/v1"`，它是工作流所有权标记，不随研究快照变化。
- 建议空间名：`跨平台 Top 50｜<安全主题>`；描述必须含两条独立的机器行：`managed_by: <managed_by>`、`space_key: <space_key>`。

空间描述**不得**放 `publish_id`：空间代表主题容器，`publish_id` 代表一次快照。空间名称可以变化，`space_key` 才是稳定身份；不得因标题改写或新的资料截止日重复创建空间。

### 2.2 节点是不可变研究快照

每个快照对应一个根目录 `origin/docx` 节点，建议标题 `<安全主题>｜Top <ACTUAL_COUNT>｜<research_as_of>`。正文第一块的第一个非空行必须是 `TOP50_PUBLISH_METADATA_V1 <BASE64URL>`：`BASE64URL` 是下面对象经第 2.3 节 RFC 8785 序列化后的 UTF-8 字节再做无 padding base64url。解析时拒绝未知 key、重复 key、错误类型或非 canonical 重新编码；这避免不可信 topic 逃逸 Markdown 结构。

```json
{
  "managed_by": "cross-platform-top50/v1",
  "space_key": "<SPACE_KEY>",
  "publish_id": "<PUBLISH_ID>",
  "semantic_digest": "sha256:<HEX>",
  "digest_spec": "top50-semantic-v1",
  "topic": "<JSON_STRING>",
  "research_as_of": "<YYYY-MM-DD>",
  "generated_at": "<RFC3339>",
  "record_count": "<ACTUAL_COUNT>",
  "requested_top_n": "<REQUESTED_TOP_N>",
  "schema_version": "<RUN_MANIFEST_SCHEMA_VERSION>",
  "chunk_count": "<CHUNK_COUNT>"
}
```

`record_count`、`requested_top_n` 和 `chunk_count` 在真实元数据中都是 JSON integer，不是字符串；上面的尖括号仅表示模板位。它们必须分别严格取 `run_summary.json.actual_count`、`run_summary.json.requested_top_n` 和已冻结发布计划的实际分块数，不能使用固定 50/10。`schema_version` 严格取 `run_manifest.json.schema_version`。

`publish_id = "cross-platform-top50/snapshot/v1:" + <semantic_digest hex>`。同一语义快照重跑得到相同值；`generated_at`、远端 ID、分块方式和渲染空白不参与快照身份。

### 2.3 canonical semantic digest

不能把“规范化正文”留给实现自行理解。`top50-semantic-v1` 明确定义为：

1. 从冻结的 `run_manifest.json`、`run_summary.json`、`top.json` 和其引用的 accepted 证据卡构造一个 JSON value；字段名使用[研究合同](research-contract.md)的真名，不另造平行 schema。只保留会改变研究语义的字段：`topic`、`research_as_of`、`requested_top_n`、`actual_count`、`ranking_version`、`schema_version`（严格取冻结的 `run_manifest.json.schema_version`）、`scope`（timeframe/languages/geography/platforms）、每条记录的 `candidate_id/rank/platform_id/title/canonical_url/creator_name/published_at/accessed_at/relevance_score/source_quality_score/evidence_score/engagement_score/freshness_score/total_score/evidence_ids/counter_evidence/caveats`，以及由 `evidence_ids` 解析出的 accepted 卡的 `evidence_id/claim/claim_value/source_id/source_url/excerpt_or_observation/evidence_grade/supports/counter_evidence` 和报告级 `limitations/conflicts`。
2. 所有字符串做 Unicode NFKC；保留字符串内部字节，不做自然语言改写。URL 使用研究阶段已冻结的 `canonical_url`。缺失值编码为 JSON `null`，不得在 `null`、空串、缺字段间漂移。
3. 对象 key 严格按 RFC 8785 的 UTF-16 code-unit 顺序；数组保留语义顺序（records 按 rank，再以 `candidate_id` 打破同分；accepted 证据卡按 `evidence_id`；platforms/limitations/conflicts 等集合型数组先去重再按 Unicode code point 排序）。数字必须是有限 JSON number，以 RFC 8785/JCS 的十进制表示序列化，禁止 NaN/Infinity、`-0` 写为 `0`，不得因展示四舍五入改变冻结值。
4. 按 RFC 8785 JSON Canonicalization Scheme 序列化为 UTF-8、无 BOM、无尾随换行，对这些字节计算 SHA-256，小写十六进制即 `semantic_digest`。

渲染后的本地 Markdown 另算 `rendered_sha256`，用于锁定 dry-run/apply 的输入文件，但不生成 `publish_id`。飞书 fetch 可能规范化 Markdown，不能把导出字节与本地文件的 raw hash 强行比较；远端改用 revision 锁、机器元数据、chunk semantic marker、记录字段和链接目标验收。正文模板、`generated_at`、`chunk_index`、chunk marker、revision ID、飞书 token/URL 均不进入 semantic digest。

## 3. 不可信研究内容的安全序列化

研究标题、作者、摘录和来源 URL 一律视为不可信数据，即使来自已验收来源。正文生成器必须做结构化 Markdown 序列化，不能用字符串拼出 Markdown/HTML：

- 纯文本字段按当前 `lark-doc-md` 规则转义 `\`、反引号、`*`、`_`、`[`、`]`、`$`、`~`、`<`；位于行首或表格 cell 时再转义 `# + - > |`。不可信文本不得直接占据 Markdown 结构行首：单值换行折叠，长摘录逐行放在固定、已转义的容器中，并防止 `1. ` 等序号触发新结构。去除/替换 NUL、C0/C1 控制字符（仅保留必要 LF），把 CRLF/CR 统一成 LF。
- 标题只允许单行：换行折叠为空格，去除双向文本控制字符。未从当前 schema/help 得到更小限制时，空间名最多 80、节点标题最多 120 个 Unicode code point；若截断，追加 `-<space_key/publish_id 最后 12 个 hex>` 防碰撞。截断只影响远端展示名，不改变快照 digest，正文保留完整安全化标题。
- URL 必须用标准 URL parser 解析后再输出，只允许 `http`/`https`，拒绝凭据段、控制字符、空白、反斜杠和危险 scheme；规范化 URL 来自冻结清单，Markdown link destination 对空格、括号等结构字符做 percent-encoding，不接受研究内容提供的任意 raw Markdown link。展示文字与目标 URL 分别序列化。
- 不允许 raw HTML/XML、图片语法、自动资源块、`@file`、mention 或飞书 token 从研究字段穿透到模板；代码围栏长度必须大于内容中最长连续反引号，或改用缩进代码块。
- 先生成文件，再以当前 `lark-doc-md` 规则解析/往返检查标题层级、链接数量/目标、记录 marker 和字面字符；任何异常都在远端写入前失败。

发布目录必须固定在 cwd 下，状态/正文文件使用随机临时名写完后以原子 rename 落位。不要把密钥写进正文、日志、计划或状态。

## 4. 本地制品与状态合同

远端写入前必须确认：实际记录数与 `run_summary.json` 一致；accepted 记录满足必填字段和证据门禁；URL/平台 ID 去重；排名、资料截止日、事实/推断状态已冻结；报告与机器清单来自同一 semantic digest；引用和署名符合授权范围。少于请求 Top N 时按实际 N 发布并在标题、元数据和局限中明确缺口，不补低可信条目。

发布状态至少包含：

```text
managed_by, space_key, publish_id, semantic_digest, rendered_sha256,
identity_open_id, cli_version, space_mode, expected_space_type,
expected_visibility, space_id, node_token, obj_token,
chunk_count, next_chunk_index, last_revision_id, state,
created_space_by_run, created_node_by_run, last_verified_at
```

每次成功远端写后立即原子更新状态。状态查找顺序：显式 state 路径（仅当真实调用入口支持；不得臆造 `--state` flag）→ 当前 run artifact 目录 → cwd 向上寻找本 Skill 的 manifest 根 → 以 `(managed_by, space_key, publish_id)` 扫描本 Skill 本地 state 索引。只能接受 schema 合法、digest 一致、ID 格式合法的唯一结果；0 个转远端递归查找，多个冲突则暂停。不得盲猜固定 `./state.json` 或依赖 shell 历史。

## 5. 解析空间：新空间与现有空间

在计划中显式选择一种模式：

- `new-managed-space`（默认的新建知识库请求）：完整列出可见空间，对名称精确匹配只用于发现；只有 0 个 `space_key` 命中且不存在同名非托管空间时才可计划创建私有 team/person 空间。
- `existing-managed-space`：用户给真实 `space_id`/URL，或远端描述中 `managed_by + space_key` 唯一匹配。验证后复用；不因快照变化新建空间。
- `existing-unmanaged-space`：用户明确指定的既有空间但缺少本工作流标记。默认**只读且不写**；即使名称相同也不能创建节点、修改描述或“收编”。若用户确实要发布到它，须先得到对精确 `space_id` 的单独授权并定义不覆盖的子树位置；这属于合同外的显式接管流程。
- `my_library`：只有用户明确选择个人文档库时使用；用 `wiki spaces get --space-id my_library --as user` 解析，不要期待 `+space-list` 返回它。默认新建独立知识空间时不降级到此模式。

解析步骤：

1. `wiki +space-list --as user --page-all --page-limit 0`，并确认最终 `has_more=false`。兼容读取 `data.spaces`、原生 `data.items`、顶层 `spaces/items`，但最终每项必须能提取 `space_id/name/description/space_type/visibility/open_sharing`；未知响应形态停止，不把空集合当真实结果。
2. 对每个候选用 `wiki spaces get --space-id <ID> --as user` 回查，兼容 `data.space`、顶层 `space`、shortcut 的扁平 `data` 或 raw 顶层对象，并验证：ID 与目标一致；`space_type` 等于计划类型；默认 `visibility=private` 且 `open_sharing=closed`。任一字段缺失都不能假设安全。
3. 空间管理权通过 `auth status` 的 user openId 加 `wiki +member-list --space-id <ID> --as user --page-all --page-limit 0` 验证：当前用户必须以 `admin`（或当前 CLI 明示的 owner/admin 等价角色）出现。`spaces.get` 没有 owner 字段，因此这里只能证明当前用户管理权，不能把它误报为“API 已验证的 owner”；若任务要求精确空间 owner 而运行时无该字段，就暂停。成员列表响应形态同样需兼容 `data.members`/原生 `data.items`/raw 顶层数组，并要求分页完成。
4. 只有描述中 `managed_by` 与 `space_key` 均精确匹配才是受管空间。相同名称但缺/错标记是非托管空间：默认不写，也不得通过改描述自动接管。多个 key 命中或同名歧义必须暂停并列出真实 ID、类型、visibility、description。

## 6. 递归解析节点与正文所有权

先用本地 state 的 `node_token/obj_token` 做 `wiki +node-get` 验证；无状态或失效时，从空间根开始递归调用 `wiki +node-list`。对每个 `has_child=true` 的节点继续传其 `node_token`，每一层均 `--page-all --page-limit 0` 且必须 `has_more=false`。维护 visited token 集和最大节点数/深度，检测环或超限即暂停。只查根目录会漏掉历史快照，不合格。

兼容读取 shortcut `data.nodes`、原生 `data.items`、顶层 `nodes/items`；`node-get` 兼容扁平 `data`、`data.node`、顶层 `node`。最终都必须验证：`space_id`、精确父 token、`node_type=origin`、`obj_type=docx`、标题、`node_token`、`obj_token`、`owner`。owner 必须等于当前 user openId；字段缺失或不符则不写。

对同标题候选调用 `docs +fetch` 读取元数据：

- `managed_by + space_key + publish_id` 全部匹配才是同一受管快照。
- 标记缺失/不符、obj type 错误、owner 不符或解析不唯一，视为非托管/歧义对象，默认不写，也不得再无条件创建第三个同名节点。
- semantic digest 相同且完整回读验证通过：no-op。
- **既有非空正文默认不自动续写**，即使 `publish_id` 匹配；这避免把人工修改或前次未知部分写入误判成可恢复状态。只有第 8 节的严格 chunk 恢复门禁全部成立才允许续写。

## 7. 逐阶段 bind ID → dry-run → apply

本 Skill 不提供额外的虚构入口命令或 `--apply` flag。发布器在本地保存不可变 step record；每个 step 的 `step_digest` 是该 step 的 CLI version、identity openId、semantic digest、动作、完整 argv（密钥除外）、输入文件 SHA-256、已绑定上游 ID 的 RFC 8785 canonical JSON SHA-256。只有同一个 step record 的 dry-run 成功后才能 apply；任何字段变化都必须重新 dry-run。

严格串行执行：

1. **bind-space**：只读解析后绑定“复用的真实 space_id”或“待创建空间的确切 name/description/期望 type/visibility”。当前 `+space-create` shortcut 只接收 name/description，不能假装请求里设置了 type/visibility；对真实 argv dry-run、检查预览后再执行同一 argv 去掉 `--dry-run`。若 CLI 把该动作标为 high-risk/exit 10，按 `lark-shared` 单独确认，不能因为总体发布授权自动加 `--yes`。从 apply 响应解析真实 `space_id`，立即回读验证管理权/type/visibility/标记；若服务端默认值不符，停止在该空间，不创建节点，并报告遗留真实 ID。
2. **bind-node**：把上一步验证后的真实 `space_id` 写入新的 step record。递归查重后，对确切 `node-create` argv dry-run，再 apply；解析并保存真实 `node_token/obj_token`，立即 `node-get` 回读验证 owner/type/parent/title。
3. **bind-content**：把验证后的 `obj_token`、远端基线 `revision_id`、chunk 文件摘要绑定到各 chunk step。每个 chunk 都先对确切 argv dry-run，再用同一 argv apply。chunk `i+1` 只有在 chunk `i` apply、状态落盘和远端 marker 回读成功后才能生成 dry-run。

dry-run 只验证请求形态，不授权 apply，也不证明权限。总体“新建并发布”授权只覆盖计划中可恢复的新建与首次空文档写入；计划目标、identity、标题、parent、digest、argv 或输入文件任一变化都使对应 dry-run 失效。

推荐 argv 形态（模板中的动态值必须先安全序列化；示例不授权真实写入）：

```text
["lark-cli","wiki","+space-create","--name",SPACE_NAME,"--description",SPACE_DESCRIPTION,"--as","user","--dry-run","--format","json"]
["lark-cli","wiki","+node-create","--space-id",SPACE_ID,"--node-type","origin","--obj-type","docx","--title",NODE_TITLE,"--as","user","--dry-run","--format","json"]
["lark-cli","docs","+update","--doc",OBJ_TOKEN,"--command","append","--doc-format","markdown","--content","@artifacts/feishu/chunk-0001.md","--revision-id",REVISION_ID,"--as","user","--dry-run","--format","json"]
```

复用已解析对象时跳过 create，但仍要把真实 ID 和完整只读验证结果绑定到后续 step。

## 8. 长文分块、revision 与安全恢复

长报告按完整记录边界分块，不能切断 Markdown link、表格行、代码围栏或一条 Top 记录。第 1 块含机器元数据和总览；每块结尾含唯一的可回读纯文本 marker（不用可能被 Markdown/XML 解析器吞掉的 HTML comment）：

```text
TOP50_CHUNK_MARKER managed_by=cross-platform-top50/v1 publish_id=<ID> index=<I> count=<N> chunk_semantic_sha256=<HEX> payload_sha256=<HEX>
```

marker 的字段来自本地计划，不接受研究文本覆盖。`chunk_semantic_sha256` 是 `{publish_id,index,count,record_ids,records,evidence}` 按第 2.3 节规则序列化后的 SHA-256；records/evidence 是本块引用的 canonical semantic object 子集。`payload_sha256` 只计算该块 marker 前的本地 Markdown：统一 LF、UTF-8、无 BOM、恰好一个尾随 LF；不把 marker 自身放进 hash，避免自引用。完整 chunk 文件（payload + marker + 尾随 LF）再另算 `file_sha256`。计划同时记录 index/count/semantic hash/payload hash/file hash、预期记录 ID 范围与前一 revision。远端 Markdown 可能被规范化，因此 raw payload hash 只锁定上传文件；回读以 semantic marker + 逐字段/链接核对 + revision 不变为准。

首次写前执行 `docs +fetch --doc <OBJ_TOKEN> --doc-format markdown --detail simple --as user --format json`：只能对本次创建且正文在语义上为空（允许平台自动生成的空标题壳）的节点首次 append。读取 `data.document.revision_id`；每次 `docs +update` 都传这个基线 `--revision-id`，成功后要求新的 revision ID 严格递增，并把它绑定到下一块，防止并发人工编辑。

按当前 `lark-doc-update` Skill 的返回合同，update 业务数据含 `result=success|partial_success|failed`、`warnings`、`updated_blocks_count` 和 `document.revision_id`。每个 update 响应必须满足：进程 0；若有标准 envelope 则 `ok=true` 且 `identity=user`；业务 payload 的 `result == "success"`、`warnings` 为空、`updated_blocks_count` 是有限非负整数、`document.revision_id` 存在且递增；apply 前后身份锁仍为同一 user openId。`partial_success`、`failed`、warnings 非空、revision 缺失/不增都不是成功；立即停止，不发送下一块，并将状态记为 `content_unknown` 后回读。若当前运行时 Skill/help 不再声明这些字段，先按第 1 节重新核对 schema/响应合同并更新计划，不能臆造成功形态或把缺字段当成功。

### 唯一允许的自动续写路径

既有非空文档只有同时满足下列条件才可 append 下一块：

1. 本地唯一 state 表明 `created_node_by_run=true`，CLI version/identity/space/node/obj/publish/semantic digest/chunk_count 全匹配；
2. 远端元数据标记匹配，正文中 marker 恰为连续前缀 `1..k`，每个 `chunk_semantic_sha256/payload_sha256` 与本地 step record 相同，marker 对应的记录字段/链接核对通过，没有重复/未知 marker，`k < chunk_count`；
3. 远端当前 revision ID 等于 state 的 `last_revision_id`，已写记录 ID 与计划前缀完全一致，正文除这些 chunk 外没有其他非空 block、媒体、画板或人工内容；
4. 下一块仍重新执行 bind-content → dry-run → apply，并用当前 revision ID。

任一条件不满足就暂停，保留现场；不 overwrite、不重复 append、不尝试“修掉”远端差异。无本地 state 但远端似乎部分写入也不能自动恢复。

## 9. 响应解析、回读与验收

CLI shortcut 可能返回 envelope 内扁平数据，原生 API 常返回嵌套对象。解析器应先验证 envelope，再从已知形态提取；不得对任意 JSON 深度搜索第一个同名 token：

| 对象 | 允许的已知形态 |
|---|---|
| space list | `data.spaces`、`data.items`、顶层 `spaces/items` |
| space create/get | 扁平 `data`、`data.space`、顶层 `space`、含 `space_id` 的 raw 顶层对象 |
| node list | `data.nodes`、`data.items`、顶层 `nodes/items` |
| node create/get | 扁平 `data`、`data.node`、顶层 `node`、含 `node_token/obj_token` 的 raw 顶层对象 |
| docs fetch/update | 标准 envelope 常为 `data.document`；当前 update 合同另有 `data.result/warnings/updated_blocks_count`；若 shortcut 返回 raw payload，则相同字段可在顶层 |

未知形态、字段类型不对或相互矛盾时保存脱敏响应并停止。`_notice` 不决定业务成功。成功判定分三类，不能强制读取不存在的字段：

1. `auth status` 使用第 1 节的 exit 0 + verified/user ready/valid/openId 合同，不要求 `ok`。
2. 返回标准 envelope（存在 `ok`）时，要求 exit 0、`ok=true`；若存在 `identity` 还必须为 `user`，缺失 identity 时由同一 argv 的显式 `--as user` 与 apply 前后不变的身份锁补证。
3. shortcut raw payload（没有 `ok/identity`）时，要求 exit 0、apply argv 显式 `--as user`、apply 前后 auth 身份锁 openId 不变，并严格校验当前运行时 Skill/help/schema 声明的所有业务字段与写后回读。raw payload 不能只凭退出码判成功。

最终回读必须证明：

1. 空间的真实 ID、name、`managed_by/space_key`、owner/admin、计划的 `space_type/visibility/open_sharing` 一致；
2. 节点的真实 `space_id/node_token/obj_token`、owner、parent、title、`origin/docx` 一致；
3. fetch 的 revision 与最后 update 一致，元数据、publish/semantic digest、实际记录数、资料截止日一致；所有 `1..chunk_count` marker 唯一、hash 正确，稳定记录 ID 和来源 URL 数量/目标与本地计划一致；
4. 同一 `(managed_by, space_key, publish_id)` 经本地 state + 远端递归解析唯一落到同一对象；再次计划为 no-op。

只有上述证据成立，状态才能从 `verifying` 改为 `complete`。交付只返回 API 明示的 URL；当前 create/get 没返回 URL 时，返回真实 `space_id`、`node_token`、`obj_token`，明确“API 未返回规范 URL”，禁止自行拼接飞书域名。

## 10. 失败恢复

采用前向恢复，不因后续失败自动删除空间或节点：

| 失败位置 | 状态 | 下一步 |
|---|---|---|
| 创建前/参数或权限失败 | 无对象或未知 | 修 scope/参数，重新只读 bind 和 dry-run；相同错误不循环重试 |
| 空间创建响应不明 | `space_unknown` | 完整 space-list + get，以 `space_key` 查重；未解析前禁止再次 create |
| 空间已建、节点失败 | `space_created` | 保存并验证 `space_id`，重新递归查重、bind-node |
| 节点创建响应不明 | `node_unknown` | 递归 node-list + node-get，以所有权标记/本地时间窗谨慎解析；未唯一确定前禁止再次 create |
| 正文部分或响应不明 | `content_unknown` | fetch revision、全部 marker 和正文；只有第 8 节严格恢复门禁允许续写 |
| 验证失败 | `verification_failed` | 停止写入，报告差异和真实 ID；不 overwrite、不自动删除 |
| rate limit/暂时网络错误 | 状态未知 | 指数退避后先读后写；未收到响应不等于写失败 |

`permission_denied`、`invalid_parameters`、`not_found` 对当前参数是终止性错误，按 hint 修复后从 bind 重新开始。最终失败报告必须列出当前 state、已创建对象的真实 ID、最后已验证 revision/chunk、可安全重试步骤、需用户决定的高风险项和未验证内容，不得用“已回滚”掩盖远端遗留对象。
