---
name: wecom-operations
description: 通过用户已配置的官方 wecom-cli 管理企业微信文档、智能文档、待办、会议和日程。适合创建或查询这些云端对象、把本地 Markdown 转为智能文档，以及在明确确认后更新或取消对象；不发送消息、不控制桌面客户端。
---

# 企业微信云端操作

本 Skill 是官方 `wecom-cli` 的审慎操作层。它不读取本地聊天数据库；本地历史检索属于 `wecom-local-vault`。

先查看 [references/examples.md](references/examples.md)，只再加载与当前对象类型对应的参考页。

## 不可跨越的边界

- 不启动或驱动企业微信桌面端，也不调用任何消息发送能力。
- 查询、帮助和 schema 检查可以直接进行；创建或修改必须来自用户当前请求。
- 删除待办、取消会议或日程、整篇替换文档前，先只读取得对象当前状态，再让用户针对准确对象确认。
- 不读取 `~/.config/wecom/` 中的密文内容；已存在配置时不得重新 `init`。
- 内部 ID、secret、授权参数、成员标识和原始 API 回执不进入对话、共享记录或版本库。
- category 不可用时停止该分支。不得换用客户端自动化、逆向协议或个人账号绕过企业授权。

## 先做只读诊断

```bash
OPS_ROOT="${WECOM_OPERATIONS_SKILL_ROOT:-$HOME/.agents/skills/wecom-operations}"
python3 "$OPS_ROOT/scripts/doctor.py"
python3 "$OPS_ROOT/scripts/doctor.py" --category doc
```

诊断只检查命令存在性、版本、配置文件元数据和 category 帮助，不解密凭据。将 `doc` 换成当前任务需要的 `todo`、`meeting` 或 `schedule`。

任何远端调用前，再读取本机 CLI 的当前 `--help` / `--schema`；不要假定仓库文档等同于运行时接口。

## 文档快捷流程

本地 Markdown 转智能文档时，先做零写入计划：

```bash
python3 "$OPS_ROOT/scripts/create_smartpage.py" \
  --source "/absolute/path/report.md" \
  --title "报告标题"
```

计划中要核对源文件、标题、本地图片、外部 helper、回执目录和将创建的对象。只有用户确实要求创建时才执行：

```bash
python3 "$OPS_ROOT/scripts/create_smartpage.py" \
  --source "/absolute/path/report.md" \
  --title "报告标题" \
  --apply
```

含本地图片时，需要用户自行提供支持 `doc +doc_upload_image` 的可执行文件，并设置 `WECOM_UPLOAD_HELPER`。该 helper 不是本仓库的一部分；缺失时不要创建一个图片残缺的文档。

细节见 [文档操作](references/documents.md)。

## 待办、会议与日程

- 待办的参与人、截止时间、提醒和删除门见 [待办操作](references/todos.md)。
- 会议和日程的时间、成员、更新及取消门见 [会议与日程](references/meetings.md)。

成员标识只能来自用户给定值或获准的通讯录查询。全量替换型字段必须先读取现值并合并，不能凭局部输入覆盖。

## 结果判断与交付

接口业务成功以响应中的成功码为准，不以进程退出码或“已发送请求”代替。出现可展示的官方帮助说明时，完整保留含义并避免夹带敏感字段。自动重试最多一次，且只用于明确的瞬时失败。

用户可见交付只包含对象名称、时间、状态和必要访问链接。脚本生成的含 ID 回执留在本机私密目录，权限应为 `0600`。创建成功但无回读权限时，必须分别陈述“创建结果”和“内容未能回读验证”。

## 依据与许可

运行依赖是外部的 [`@wecom/cli`](https://github.com/WecomTeam/wecom-cli)，其版本和许可由上游维护；本仓库不分发 CLI 源码或二进制。本目录的原创说明、测试与辅助脚本适用仓库顶层 MIT License。
