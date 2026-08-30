# Lark Approval｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证；执行时仍须先运行相应 `--help`/`schema`，以当前版本为准。示例中的 profile、ID 和请求文件都是占位值，不可原样提交。

## 使用说明

- **何时使用：** 需要发起审批、处理待办或判断提交结果未知时，参考相应案例；普通只读查询不必逐段加载。
- **准备/输入：** 固定 profile/identity，准备唯一 definition/instance/task 标识、按 schema 构造的请求体和本轮授权范围。
- **执行方式：** 先 search/get 与 dry-run，再对高风险动作取得对象级确认；一次提交后用 instance/task 读命令回查。
- **验收/边界：** 以实例/任务 ID、表单字段和服务端终态为准；发起不等于通过，批量待办不等于逐项授权。

## 正向案例

### 发起一份确定的请假审批

- **用户请求：** “给我发起 2026-09-03 09:00 到 2026-09-04 18:00 的年假审批，原因写家庭安排；提交前让我确认。”
- **准备信息/输入：** `work` profile 已登录；调用者使用 `user` 身份；时区为 `Asia/Shanghai`；`requests/approval-search.json` 和 `requests/leave.json` 均在当前工作区内，后者由实际定义 schema 的字段 ID 与类型生成。
- **处理：**

```bash
lark-cli whoami --profile work
lark-cli schema approval.approvals.search
lark-cli approval approvals search --profile work --as user --data @requests/approval-search.json --format json
lark-cli schema approval.instances.create
lark-cli approval instances create --profile work --as user --data @requests/leave.json --dry-run --format json
```

预览中展示唯一 `definition_code`、申请人、起止时间、时区、请假类型和原因。只有用户确认这一版后，才执行一次：

```bash
lark-cli approval instances create --profile work --as user --data @requests/leave.json --yes --format json
lark-cli approval instances get --profile work --as user --instance-code <instance_code> --format json
```

- **预期输出：** 创建响应返回唯一 `instance_code`，实例进入服务端初始状态。
- **验收证据：** 回读的定义、申请人、字段值和时间段与预览一致；保存实例 code 和当前状态；没有把“发起成功”写成“审批通过”。

## 边界案例

### 拒绝“把待办都通过”的模糊授权

- **用户请求：** “把我的审批待办全通过。”
- **边界判断：** 请求覆盖多个会影响他人的高风险决策，却未给出具体任务、实例、申请人和影响说明；“全部”不是对象级授权。
- **处理：** 只读列出有限页待办，禁止追加 `--yes`：

```bash
lark-cli approval tasks query --profile work --as user --topic 1 --page-all --page-limit 10 --format json
```

按实例标题、申请人、task ID、金额/日期等关键影响生成候选清单，请用户逐项选择；未经对象级确认不调用 `tasks approve`。
- **验收证据：** 只产生待办清单和待确认项，服务端任务状态不变；日志中没有 approve/reject/transfer/rollback 写请求。

## 失败与恢复

### 提交超时或字段校验失败

- **场景：** create 返回字段类型错误，或请求超时导致结果未知。
- **处理与恢复：** 字段错误时重新读取 `approval.instances.create` schema 和审批定义，不根据错误文本猜字段；超时时先查询已发起列表，再按候选 `instance_code` 回读，不能直接重提：

```bash
lark-cli schema approval.instances.create
lark-cli approval instances initiated --profile work --as user --definition-code <definition_code> --page-all --page-limit 10 --format json
lark-cli approval instances get --profile work --as user --instance-code <candidate_instance_code> --format json
```

- **验收证据：** 若已创建，交付唯一实例及回读状态；若能证明未创建，修正请求后重新预览；无法判断时明确标为“状态未知”，保留错误、时间窗和查询范围。
