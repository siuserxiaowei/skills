# 企微会议与日程

## 先探测授权

每次操作前都运行：

```bash
wecom-cli meeting --help
wecom-cli schedule --help
```

一旦企业侧答复“不支持授权”，立即停下并向用户报告：不建测试会议、不动客户端、不换非官方协议。

## 发起会议预约

确认授权可用后，先跑 `wecom-cli meeting create_meeting --schema` 读取当前 schema，再逐项核对：

- 会议标题；
- 开始时间（格式 `YYYY-MM-DD HH:mm`，时区默认 Asia/Shanghai）；
- 时长，单位为秒；
- 地点、描述、受邀成员按实际需要补充。

标题、开始时间、时长任何一项缺失，都要先向用户问齐。userid 不允许凭空猜测；通讯录接口不可用时，要么创建无邀请人的会议，要么请用户给出明确的人员标识。

```bash
wecom-cli meeting create_meeting '{"title":"周例会","meeting_start_datetime":"2026-08-01 15:00","meeting_duration":3600}'
```

创建成功后，对外只反馈可读标题、时间、时长、会议链接与格式化会议号，meetingid 留作内部使用。

## 查询、调整与取消会议

- 列清单用 `list_user_meetings`，时间窗口仅限当天前后30天；
- 看详情用 `get_meeting_info`；
- 调整受邀人用 `set_invite_meeting_members`，注意它是全量覆盖，先取出现有名单合并后再提交；
- 取消走 `cancel_meeting`，先用列表加详情锁定目标，再请用户确认准确的标题和时间。

仅凭标题模糊命中就直接修改或取消，一律不允许。

## 日程操作

企业授权后可用的工具：

- `get_schedule_list_by_range`、`get_schedule_detail`；
- `create_schedule`、`update_schedule`、`cancel_schedule`；
- `add_schedule_attendees`、`del_schedule_attendees`；
- `check_availability`。

建日程前先和用户敲定标题、起止时间、时区、提醒方式与参与人；取消日程或移除参与人之前，一律先读详情、确认目标。
