# Lark Attendance｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。考勤请求体随 OpenAPI schema 变化，必须由当次 `schema` 生成；示例只展示稳定的 CLI 外层结构。

## 使用说明

- **何时使用：** 查询本人某日/区间打卡、解释空结果或区分打卡事实与考勤结论时读取。
- **准备/输入：** 明确 employee ID/type、profile/identity、IANA 时区、半开日期区间和 schema 对应请求体。
- **执行方式：** 先 schema 与 dry-run，按最小字段调用一次；空结果依次核对身份、边界、权限和服务端限制。
- **验收/边界：** 以服务端原始时间/状态和覆盖区间验收；没有排班规则时不判断迟到，团队数据不在默认范围。

## 正向案例

### 查询本人一个自然月的打卡记录

- **用户请求：** “按上海时区汇总我 2026 年 8 月的打卡记录；没有排班依据的地方不要判迟到。”
- **准备信息/输入：** `work` profile 对应本人；已知合法的本人 employee ID 及 `employee_type=employee_id`；自然日范围是 `2026-08-01T00:00:00+08:00` 至 `2026-09-01T00:00:00+08:00`；请求体保存在 `requests/attendance-aug.json`。
- **处理：**

```bash
lark-cli whoami --profile work
lark-cli schema attendance.user_tasks.query
lark-cli attendance user_tasks query --profile work --as user --employee-type employee_id --data @requests/attendance-aug.json --dry-run --format json
lark-cli attendance user_tasks query --profile work --as user --employee-type employee_id --data @requests/attendance-aug.json --format json
```

按响应字段保留原始时间、打卡类型和服务端状态；只有另有排班/规则证据时才汇总迟到或缺卡。
- **预期输出：** 返回范围内本人的记录，或返回可解释的空结果/权限错误。
- **验收证据：** 输出写明调用身份、employee type、起止边界、IANA 时区、记录数和服务端状态；没有同事记录，也没有凭打卡时间自行推断违规。

## 边界案例

### 团队考勤不是个人查询的自然扩展

- **用户请求：** “顺便把全组人的考勤和手机号也导出来。”
- **边界判断：** 本 Skill 默认只处理已授权用户本人的考勤；团队记录与手机号同时扩大人员范围、权限和敏感字段。
- **处理：** 停止扩张范围；说明组织级考勤、联系方式和人员隐私需要管理员能力、明确业务用途、最小字段和合法授权。保留已授权的本人查询，不切换 bot 或扩大 scope。
- **验收证据：** 没有发出包含其他 employee ID 的请求；交付中只含本人字段，并明确说明团队导出未执行及所缺授权。

## 失败与恢复

### 查询返回空数组

- **场景：** 月度查询成功退出但 `data` 为空。
- **处理与恢复：** 依次核对 profile/identity、employee ID 类型、请求体中的毫秒/秒与自然日边界、scope，以及服务端是否分批限制；必要时把月份按本地自然日切片复查，但不改变身份、不把空结果写成“整月正常”。
- **验收证据：** 若修正边界后出现记录，报告原请求与修正请求差异；仍为空时写明已核对的身份、时间窗、权限和覆盖范围，并把结论限定为“当前查询未返回记录”。
