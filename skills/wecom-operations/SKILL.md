---
name: wecom-operations
description: 本 Skill 借助官方 wecom-cli 操作企业微信云端资源：把本地 Markdown 发布为普通文档或智能文档（含本地图片时需用户自备上传 helper），读取或覆写企微文档，创建与管理待办，并在企业权限开放后预约、查询、更新或取消会议和日程。当用户提到“企微文档”“智能文档”“上传 Markdown”“预定会议”“企微会议”“企微日程”“企微待办”时触发；不负责消息发送，也不操控企业微信客户端。
---

# 企业微信操作

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

本 Skill 通过本机安装的官方 `wecom-cli` 调用企微云端接口。只读本地数据库的需求交给 `$wecom-local-vault`，两者分开使用，不要混用。

## 硬性红线

1. 不碰企业微信客户端：不启动、不点击、不退出、不控制，也不调用 `wecom-cli msg` 或任何形式的消息发送。
2. 读类操作（查询、`--help`、schema 查看）随时可执行；写类操作（创建、覆写、更新、邀请、取消、删除）必须在用户当轮明确指示后才进行。
3. 凡是取消会议／日程、删除待办、整体覆写既有文档，先以只读方式核实确切对象与当前状态，再由用户针对该具体对象确认后方可动手。
4. `~/.config/wecom/` 内的加密凭证一律不读不输出；Bot ID、Secret、内部 userid、docid、meetingid、todo_id 以及带授权参数的 URL 均不得写入回复、日志、报告或记忆。
5. 只要 `~/.config/wecom/{.encryption_key,bot.enc,mcp_config.enc}` 已经存在，就禁止再次运行 `wecom-cli init`，以免覆盖既有配置。
6. 动手前先跑目标 category 的 `--help`。若接口答复“当前企业暂不支持授权”，该 category 立即停止，不允许改用客户端自动化或非官方协议绕行。
7. 远端业务成功与否以 `errcode == 0` 判定；失败时最多低频重试一次。响应中带 `help_instruction` 时，按其要求将 `help_message` 原样逐字展示。
8. 不擅自清理本地上传副本、回执，或失败后已经建出的企微资源；确实需要删除时，先向用户说明并征得明确同意。

## 运行前自检

```bash
SKILL_ROOT="${WECOM_OPERATIONS_SKILL_ROOT:-$HOME/.agents/skills/wecom-operations}"
python3 "$SKILL_ROOT/scripts/doctor.py"
python3 "$SKILL_ROOT/scripts/doctor.py" --category doc
```

`doctor.py` 是纯只读检查：核对 CLI 版本、加密配置文件权限与 category 可用性，不会触碰凭证内容本身。

## 按需取阅

- 涉及本地 Markdown、普通文档、智能文档或图片证据：打开 [references/documents.md](references/documents.md)。
- 涉及会议预约／查询／取消，或企微日程：打开 [references/meetings.md](references/meetings.md)。
- 涉及待办的创建、查询、更新或删除：打开 [references/todos.md](references/todos.md)。

与任务无关的参考文件不要提前全部读取。

## 智能文档快速用法

不带 `--execute` 时只做预检，对企微不产生任何写入：

```bash
SKILL_ROOT="${WECOM_OPERATIONS_SKILL_ROOT:-$HOME/.agents/skills/wecom-operations}"
python3 "$SKILL_ROOT/scripts/create_smartpage.py" \
  --source "/absolute/path/report.md" \
  --title "报告标题"
```

仅当用户当轮明确要求创建时才附加 `--execute`：

```bash
SKILL_ROOT="${WECOM_OPERATIONS_SKILL_ROOT:-$HOME/.agents/skills/wecom-operations}"
python3 "$SKILL_ROOT/scripts/create_smartpage.py" \
  --source "/absolute/path/report.md" \
  --title "报告标题" \
  --execute
```

Markdown 不含本地图片时，直接产出最终智能文档；含本地图片时，会先另建一个命名清晰的“图片资源”普通文档，把图片传上去换取企微 CDN 链接，之后才生成最终智能文档。两类产物都要在结果里向用户交代。

## 能力边界与依赖

- 运行基础是企业微信官方 [`@wecom/cli`](https://github.com/WecomTeam/wecom-cli)；安装完成后由用户自行执行 `wecom-cli init` 配置自己的机器人。
- 文档、待办、会议、日程与通讯录各类目能否使用，由企业侧与机器人配置共同决定，只能靠 `doctor.py` 加目标 category 的 `--help` 现场探测。
- 官方 CLI 原生处理文本与已托管的远程图片；本地图片上传必须借助用户另行提供、具备 `doc +doc_upload_image` 能力的 helper，并通过 `WECOM_UPLOAD_HELPER` 指向其可执行文件。本仓库不附带该本地扩展。
- 智能文档的回读可能因权限返回 `851008`；“创建成功”不等于“回读验证成功”，两者不可混为一谈。

## 结果交付

对用户只展示可读名称、时间、状态与最终访问链接。内部 ID 只落盘到权限为 `0600` 的本机回执，不在对话中展开。
