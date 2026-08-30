# Lark OKR｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。当前 `+patch --score` 接受 0–1 且最多一位小数，示例把 60% 写成 `0.6`，不直接传 `60`。

## 使用说明

- **何时使用：** 需要定位周期/层级、更新进度，或区分 score 与对齐/负责人组织语义时读取。
- **准备/输入：** 确认 owner ID、cycle/objective/KR ID、当前值、新值、事实依据和 profile/identity。
- **执行方式：** 先 cycle list/detail 消歧，dry-run 单个 target patch，写后回读整个层级并比较非目标字段。
- **验收/边界：** 用 target ID、score、路径、时间与其他 KR/权重/alignment 基线验收；进度授权不包含关系与可见性变化。

## 正向案例

### 更新一个唯一 KR 的进度分数

- **用户请求：** “把我本季度‘灰度发布’KR 从 40% 更新到 60%；其他 KR、权重和对齐都别动。”
- **准备信息/输入：** profile/identity 为 `work`/user；本人 open ID 已验证；时间范围定位到唯一 cycle；cycle detail 中该 KR 唯一命中 `<kr_id>`，当前 score 为 0.4；用户已明确授权改为 0.6。
- **处理：**

```bash
lark-cli okr +cycle-list --profile work --as user --user-id <owner_open_id> --user-id-type open_id --time-range '2026-07--2026-09' --format json
lark-cli okr +cycle-detail --profile work --as user --cycle-id <cycle_id> --style simple --format json
lark-cli okr +patch --profile work --as user --level key-result --target-id <kr_id> --score 0.6 --dry-run --format json
```

展示 cycle、Objective 路径、KR ID、0.4→0.6 差异后执行一次，再回读整个周期结构：

```bash
lark-cli okr +patch --profile work --as user --level key-result --target-id <kr_id> --score 0.6 --format json
lark-cli okr +cycle-detail --profile work --as user --cycle-id <cycle_id> --style simple --format json
```

- **预期输出：** 同一 KR 的 score 变为 0.6，cycle/objective/KR ID 不变。
- **验收证据：** 回读目标 KR 的 score、更新时间和路径；对比同级 KR、Objective 内容、权重和 alignment，证明它们与基线一致。

## 边界案例

### 进度更新不授权对齐或负责人变化

- **用户请求：** “更新到 60%，顺便对齐老板的目标并把同事设成负责人。”
- **边界判断：** score 是事实进展字段；alignment 和 owner 改变组织关系与可见/编辑语义，不能由进度更新自动授权。
- **处理：** 先只执行已明确的 score 更新；另行读取候选上级目标、当前 alignment 和 owner，展示组织影响并请求独立确认。
- **验收证据：** 回读显示目标 score 为 0.6，同时 alignment ID、owner ID、权重及可见性保持基线；未确认的关系变更列为未执行。

## 失败与恢复

### 周期或 KR 不唯一

- **场景：** 当前与历史周期都存在“灰度发布”KR，或同一周期有两个同名 KR。
- **处理与恢复：** 停止 patch；用 `+cycle-list`/`+cycle-detail` 展示 cycle 时间、Objective 路径、KR ID 和当前 score，请用户选定。若写响应超时，先回读同一 KR score，不能再次 patch 猜测未生效。
- **验收证据：** 消歧前没有 KR score 变化；消歧或超时恢复后，以唯一 target ID 的 0.4/0.6 服务端值为依据，未知时明确标记而不更改其他 KR。
