# 多来源请求编译

`scripts/compile_route_bundle.py` 把已经完成主题解析和平台访问分类的结构化范围，编译成可重放的多 shard 路由 bundle。它不解析任意自然语言，不执行 probe、登录、网络请求、引擎计划或外部写入。

## 输入门禁

输入使用 `top50-route-scope/v1`，合同见 [route-bundle-request.schema.json](../assets/engine-contracts/route-bundle-request.schema.json)。调用方先完成以下工作，再运行编译器：

- 先用 `scripts/research_planner.py` 生成并落盘 `top50-research-query-plan/v1`；route scope 的 `query_plan_path` 必须指向这个不可变工件。编译器读取同一份原始字节快照，冻结规范化绝对路径、原始 SHA-256、计划自身 `plan_digest_sha256`、查询数与 query-ID set digest。
- 每个 discovery shard 的 router request 必须携带与 bundle 根完全相同的 `query_plan_binding`；fetch/process/rank 不得携带。router 在计划时再次读取该路径并核对五项描述符，discovery 完成工件再绑定同一 QueryPlan。旧 `top50-scope-query-plan/v1`、重签后的替换包、文件漂移、集合漂移或没有绑定的旁路都失败关闭。

- 把真实主题写入 `topic`；占位符、空白或纯标点失败关闭。
- 为已 probe 和分类的平台显式给出 `platform_id`、`access_kind=platform_cli|browser_session` 和 `required`。不要为未检查的平台猜访问方式。
- `platform_scope_mode=required_plus_default` 表示保留 canonical 28 覆盖目标；未显式分类的默认渠道只进入 `pending_classification`，不产生可执行 shard。只有用户明确表达“只/仅/include_only”时使用 `include_only`。
- 只有已经发现且当前任务已授权的公共 URL，才同时填写正数 `public_url_count` 和 `public_urls_authorized=true`。此时还必须提供 `public_http_binding={manifest_path,manifest_artifact_sha256,job_set_sha256,job_count}`，且 `job_count == public_url_count`；两个 digest 均为 64 位小写 SHA-256。编译器只冻结并透传绑定，不读取 manifest；router plan/execute 再核对实际工件。
- 只有 canonical extraction 已完成，才同时填写正数 `local_candidate_count` 和 `extraction_complete=true`。
- `risk` 省略时编译为 `low`，并进入 `assumptions`；工作量固定为 `<50=small`、`50–149=medium`、`>=150=large`。

示例：

```json
{
  "schema": "top50-route-scope/v1",
  "run_id": "agent-search-001",
  "topic": "Agent 跨平台检索",
  "top_n": 50,
  "engine_mode": "auto",
  "dual_run": false,
  "login_mode": "user-assisted",
  "query_plan_path": "research-runs/agent-search-001/query_plan.json",
  "platform_scope_mode": "required_plus_default",
  "platform_routes": [
    {"platform_id": "github", "access_kind": "platform_cli", "required": true},
    {"platform_id": "xiaohongshu", "access_kind": "browser_session", "required": true}
  ],
  "public_url_count": 75,
  "public_urls_authorized": true,
  "public_http_binding": {
    "manifest_path": "route-inputs/agent-search-001/public-http-manifest.json",
    "manifest_artifact_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "job_set_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "job_count": 75
  },
  "local_candidate_count": 150,
  "extraction_complete": true
}
```

## 编译与计划

```bash
python3 scripts/compile_route_bundle.py \
  --input <run-dir>/route-scope.json \
  --output <run-dir>/route-bundle.json
```

输出使用 `top50-route-bundle/v1`，合同见 [route-bundle.schema.json](../assets/engine-contracts/route-bundle.schema.json)。同一规范化输入产生相同 shard 顺序、路径、计划文件名和 `bundle_digest_sha256`。编译器在输出前还会运行纯内存 `validate_route_bundle()`，核对 shard ID 唯一性、`depends_on` 引用与 DAG、计划文件映射、交接路径链和 digest 真值；这个校验不读写文件也不执行引擎。

- `platform_cli` 按 access kind 聚合为 Python discovery/fetch 两个 shard，不按平台复制计划。
- `browser_session` 在 `public-only` 下生成 `blocked` 记录且 `login_requested=false`；在 `user-assisted` 下生成共享 `pending_checkpoint`，通过真实认证 probe 前没有 `router_request`。
- bundle 中的 `top50-login-checkpoint/v1` 只是尚未执行的 checkpoint locator/创建意图：它冻结目标路径、平台集合和下一门禁，不含认证状态、查询进度或错误历史。真正暂停时，控制面必须用 `scripts/source_contract.py` 在该路径生成完整 `top50-research-checkpoint/v1`，再以其 TTL、摘要、幂等键和 pending IDs 恢复；不得把 locator 当成可恢复运行态或已完成登录。
- 已授权公共 URL 生成 `public_http/fetch`，并把 `public_http_binding` 原样写入其 `router_request`，避免只凭数量把计划换绑到另一批 URL；已完成 extraction 的本地候选生成 `local_bundle/process` 与 `local_bundle/rank`。
- `ready_to_plan` shard 的 `router_request` 可以直接作为 `engine_router.py plan --input` 的输入；`run_dir`、`plan_filename` 和 merge contract 已冻结。`blocked` / `pending_checkpoint` shard 不得送入 router。
- `shared_handoffs` 固定保存 shard merge、独立 curator acceptance 和 rank 的失败关闭交接；它是后续主编排器的合同，不代表这些阶段已经完成。`shards-to-merge.input_shard_ids` 按 bundle 顺序精确列出 `status=ready_to_plan && stage!=rank` 的 shard；`blocked` / `pending_checkpoint` 只保留在 shard 与 coverage 状态中，不成为必须 `complete` 的 merge 输入。该集合可以为空，调用方不得自行补入待登录 shard。merge 输入工件使用严格的 [`top50-route-shard-result-manifest/v1`](../assets/engine-contracts/route-shard-result-manifest.schema.json)，其中每个单项结果仍使用 `top50-route-shard-result/v1`；manifest 只有在顶层 `status=complete` 且所有记录均 complete 时才能满足 handoff。`local-bundle-rank` 明确排除：rank 只能在 `merge-to-curate` 产出独立验收结果且 `curate-to-rank.required_status=accepted` 后执行。

逐个生成计划时，由调用方读取 bundle 中 `status=ready_to_plan` 的对象，把 `router_request` 原子写到该 shard 的请求文件，再使用其 `plan_filename`：

```bash
python3 scripts/engine_router.py plan \
  --input <shard-router-request.json> \
  --output <plan_filename>
```

编译器不会创建 `route-runs/`；CLI 只写显式 `--output`。研究运行目录由 `.gitignore` 排除，不能进入 Skill 安装包。
