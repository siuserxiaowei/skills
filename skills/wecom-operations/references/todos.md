# 企微待办

## 能力探测

先跑 `wecom-cli todo --help` 现场确认。目前企业返回的工具包括：

- `search_todo_userid`；
- `create_todo`、`update_todo`、`delete_todo`；
- `get_todo_list`、`get_todo_detail`；
- `change_todo_user_status`。

可操作的仅限本机器人自己创建的待办。

## 新建待办

创建前与用户核对内容、参与人、截止时间和提醒设置。`follower_list` 为必填项；userid 一律通过 `search_todo_userid` 查得，不猜测，也不向用户展示。

```bash
wecom-cli todo create_todo '{"content":"提交报告","follower_list":{"followers":[{"follower_id":"USERID","follower_status":1}]},"end_time":"2026-08-01 18:00:00","remind_type_list":[3]}'
```

提醒类型取值：`0` 不提醒、`1` 到期时、`3` 提前15分钟、`5` 提前1小时、`6` 提前2小时、`7` 提前1天、`8` 提前2天、`9` 提前1周。凡要设置真实提醒，截止时间必须一并提供。

## 查询和更新

- 可查的时间范围一般是当天前后30天；
- `update_todo` 提交参与人时是整表替换，先读详情把现有名单合并进来；
- 接受、拒绝或完成这类参与状态变更走 `change_todo_user_status`；
- todo_id 仅供内部传参，回复里不出现。

## 删除待办

删除前先读详情，把待办内容、截止时间与当前状态复述给用户，取得针对该条待办的明确同意后再删。批量盲删、自动清理都不允许。
