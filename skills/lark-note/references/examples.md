# Lark Note｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。note ID、minute token、meeting ID 与 doc token 互不替代；输出路径必须位于当前工作区。

## 使用说明

- **何时使用：** 已知可信 note ID，需要详情、关联文档 token 或 unified transcript，以及处理部分权限失败时读取。
- **准备/输入：** 准备 note ID、profile/user、locale/格式、工作区输出路径、覆盖选择与完整性检查方法。
- **执行方式：** 先 detail，再 transcript；关联正文只把返回的 doc token 路由 lark-doc，下载中断先核对文件。
- **验收/边界：** 用同一 note ID、display type、doc token、文件字节数和时间覆盖验收；未知 ID 不按标题猜，摘要不补写逐字稿。

## 正向案例

### 读取已知 note 的详情与 unified transcript

- **用户请求：** “note_id 是 `note_abc`，读取它的关联文档信息和中文 unified 原始逐字记录。”
- **准备信息/输入：** `note_abc` 来自可信会议元数据；profile 为 `work`、user 身份有访问权；输出格式为 Markdown、locale 为 `zh_cn`，目标文件 `evidence/notes/note_abc.md` 当前不存在。
- **处理：**

```bash
lark-cli note +detail --profile work --as user --note-id note_abc --format json
lark-cli note +transcript --profile work --as user --note-id note_abc --locale zh_cn --transcript-format markdown --output evidence/notes/note_abc.md --format json
```

关联文档需要正文时，仅把详情返回的 doc token 转给 lark-doc；不把 note ID 传给 docs 命令。
- **预期输出：** 返回 note 的 display type、关联资源 token，并在指定相对路径保存统一逐字稿。
- **验收证据：** detail 与 transcript 响应使用同一 note ID；输出文件存在、可读、非半文件，并记录格式、locale、字节数和时间覆盖；关联文档未被自动修改。

## 边界案例

### 未知 note_id 时不能按标题猜

- **用户请求：** “把昨天那个项目会的 note 找出来并下载。”
- **边界判断：** note 域需要可信 `note_id`，标题和日期不足以构造该 ID；会议、妙记和统一纪要是不同资源。
- **处理：** 路由到 lark-vc/lark-minutes 以标题、时间和参与人定位，并从服务端元数据取得 note ID；没有唯一 ID 前不调用 `note +transcript`。
- **验收证据：** 交付候选会议/minute 的稳定 ID 与消歧信息；没有创建以猜测 note ID 命名的逐字稿文件。

## 失败与恢复

### 详情可见但逐字稿无权限

- **场景：** `+detail` 成功返回 doc token，`+transcript` 返回无权限或处理中。
- **处理与恢复：** 分别记录 detail 与 transcript 状态；无权限时走合法申请路径，处理中做有界复查。不得读取关联文档摘要来补写 unified transcript，也不得加 `--overwrite` 反复下载。
- **验收证据：** detail 字段仍可交付，但 transcript 标为不可用/处理中；目标路径不存在或被识别为不完整而不作为全文交付，错误与 note ID 对得上。
