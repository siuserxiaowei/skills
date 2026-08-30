# Lark Calendar｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。示例时间都带偏移；人员 ID 必须先经通讯录消歧，不能把显示名直接填入写命令。

## 使用说明

- **何时使用：** 需要查询忙闲、创建/更新日程或处理周期与未知创建结果时读取。
- **准备/输入：** 确认 calendar/event ID、带偏移起止时间、IANA 时区、参会人/会议室稳定 ID 与实例/系列范围。
- **执行方式：** 先查忙闲和现有事件，dry-run 展示受众与通知影响，写一次后按 event ID 回读。
- **验收/边界：** 用 organizer、时间、attendee/room RSVP 和 recurrence 验收；忙闲不代表愿意参会，周期范围不得猜测。

## 正向案例

### 查忙闲后创建一次性日程

- **用户请求：** “2026-09-01 15:00（上海）约张三和李四开 45 分钟项目复盘，确认他们有空后创建。”
- **准备信息/输入：** profile 为 `work`，调用身份为 user；张三、李四已解析为 `ou_zhang`、`ou_li`；起止时间为 `2026-09-01T15:00:00+08:00` 和 `2026-09-01T15:45:00+08:00`；目标是调用者的 primary calendar。
- **处理：**

```bash
lark-cli calendar +freebusy --profile work --as user --user-id ou_zhang --start '2026-09-01T15:00:00+08:00' --end '2026-09-01T15:45:00+08:00' --format json
lark-cli calendar +freebusy --profile work --as user --user-id ou_li --start '2026-09-01T15:00:00+08:00' --end '2026-09-01T15:45:00+08:00' --format json
lark-cli calendar +create --profile work --as user --calendar-id primary --summary '项目复盘' --start '2026-09-01T15:00:00+08:00' --end '2026-09-01T15:45:00+08:00' --attendee-ids 'ou_zhang,ou_li' --dry-run --format json
```

把最终标题、时区、受众和通知影响展示给用户；其请求已明确要求创建且预览无误后执行一次并回读：

```bash
lark-cli calendar +create --profile work --as user --calendar-id primary --summary '项目复盘' --start '2026-09-01T15:00:00+08:00' --end '2026-09-01T15:45:00+08:00' --attendee-ids 'ou_zhang,ou_li' --format json
lark-cli calendar +get --profile work --as user --calendar-id primary --event-id <event_id> --format json
```

- **预期输出：** 创建一个非周期事件并向两个已确认用户发送邀请。
- **验收证据：** 回读的 event ID、organizer、起止时间/偏移、标题、attendee ID 和 RSVP 状态一致；忙闲只作为冲突证据，不写成参会承诺。

## 边界案例

### 修改周期范围必须先选“本次”还是“系列”

- **用户请求：** “把周会改到四点。”
- **边界判断：** “周会”可能是周期系列或单次实例；修改范围不同会通知不同日程和参会人，不能依据标题猜范围。
- **处理：** 先查唯一事件和 recurrence 信息；若是周期实例，要求明确是本次、后续还是整个系列。未选择前不调用 update，也不通知参会人。
- **验收证据：** 服务端 event/revision 保持不变；交付候选事件、当前时间、时区和三种修改范围，而不是自行选择整个系列。

## 失败与恢复

### 创建响应超时

- **场景：** 写请求已发出但没有收到 event ID。
- **处理与恢复：** 用相同 calendar、精确时间窗、标题和 organizer 查询 agenda，检查是否已有唯一匹配；不重复 create：

```bash
lark-cli calendar +agenda --profile work --as user --calendar-id primary --start '2026-09-01T14:55:00+08:00' --end '2026-09-01T15:50:00+08:00' --format json
```

- **验收证据：** 唯一匹配则回读并交付；无匹配且能证明未创建时才重新预览；多匹配或权限不足则报告状态未知，避免重复邀请。
