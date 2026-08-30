# Lark Base｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。示例 ID 均为占位值；字段值形状必须服从当前表的实际 schema。

## 使用说明

- **何时使用：** 需要把 Base URL 解析为坐标、按 schema 读写记录，或恢复批次部分失败时读取。
- **准备/输入：** 准备 base/table/field/record ID、字段类型与选项、唯一记录键、写入差异和恢复基线。
- **执行方式：** 先 url-resolve/field-list/record read，确认可写字段后 dry-run 小批次，并逐 record 回读。
- **验收/边界：** 用 record ID、逐项状态和字段回读验收；同一 batch patch 不适合逐行异值，结构删除另行评估依赖。

## 正向案例

### 按已确认记录批量更新同一状态

- **用户请求：** “把订单 `SO-1042`、`SO-1043` 的状态改成 `Done`，公式和 lookup 不要动。”
- **准备信息/输入：** 已给出 Base URL；解析后为 `<base_token>`/`<table_id>`；订单号唯一命中 `rec_a`、`rec_b`；`Status` 是可写单选字段且存在 `Done` 选项。
- **处理：**

```bash
lark-cli base +url-resolve --profile work --as user --url '<base_url>' --format json
lark-cli base +field-list --profile work --as user --base-token <base_token> --table-id <table_id> --format json
lark-cli base +record-list --profile work --as user --base-token <base_token> --table-id <table_id> --field-id 'Order ID' --field-id Status --filter-json '{"logic":"or","conditions":[["Order ID","==","SO-1042"],["Order ID","==","SO-1043"]]}' --limit 20 --format json
lark-cli base +record-batch-update --profile work --as user --base-token <base_token> --table-id <table_id> --json '{"record_id_list":["rec_a","rec_b"],"patch":{"Status":"Done"}}' --dry-run --format json
```

确认 dry-run 仅包含两个 record ID 和一个可写字段后执行一次，并按 ID 回读：

```bash
lark-cli base +record-batch-update --profile work --as user --base-token <base_token> --table-id <table_id> --json '{"record_id_list":["rec_a","rec_b"],"patch":{"Status":"Done"}}' --format json
lark-cli base +record-get --profile work --as user --base-token <base_token> --table-id <table_id> --record-id rec_a --record-id rec_b --field-id 'Order ID' --field-id Status --format json
```

- **预期输出：** 两条目标记录的 Status 为 Done，其他字段未在 patch 中出现。
- **验收证据：** 输入订单号、record ID、逐项成功/失败、回读值和数量对得上；公式/lookup 字段没有写请求。

## 边界案例

### 每行不同的值不能冒充同一批 patch

- **用户请求：** “这 200 行分别写不同负责人和日期，顺便把旧公式列删掉。”
- **边界判断：** `+record-batch-update` 只适合所有记录共享同一 patch；逐行异值必须换路由，而删除公式字段是会破坏依赖的结构变更。
- **处理：** 不使用 `+record-batch-update` 把同一 patch 错套到所有行；把逐行 upsert 与删除字段拆开。删除字段先读取公式、lookup、视图、自动化依赖并取得高影响确认。
- **验收证据：** 未确认结构变更前 schema 不变；逐行计划中每个输入都有唯一 record/键和值，且不存在静默字符串化或计算字段覆盖。

## 失败与恢复

### 批次部分成功

- **场景：** `rec_a` 成功、`rec_b` 因选项或权限失败。
- **处理与恢复：** 保存 per-record ledger，先用 `+record-get` 回读两条真实状态；只对可证明未应用的 `rec_b` 修正并重新 dry-run，禁止重放整批。
- **验收证据：** ledger 明确 `updated/failed/retried`；`rec_a` 只更新一次，`rec_b` 的服务端错误与最终回读可追溯，未知项不计入成功。
