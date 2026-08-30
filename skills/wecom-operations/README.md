# wecom-operations

通过用户已配置的官方 `wecom-cli` 查询或管理企业微信文档、待办、会议和日程。这个 Skill 不发送消息、不控制企业微信桌面端，也不读取本地聊天数据库。

## 先检查运行环境

```bash
python3 scripts/doctor.py
python3 scripts/doctor.py --category doc
```

诊断器只检查 CLI、配置文件元数据和 category 帮助。它不会解密 `~/.config/wecom/` 的内容。已经存在配置时不要重复执行 `wecom-cli init`。

所有实际调用都应以本机版本的 `--help` / `--schema` 为准。租户没有开放某一 category 时，就停止该分支，不改用客户端自动化或非官方协议。

## Markdown 智能文档

默认命令只生成计划：

```bash
python3 scripts/create_smartpage.py \
  --source "/absolute/path/report.md" \
  --title "报告标题"
```

用户明确要求创建且计划无误后再加 `--apply`：

```bash
python3 scripts/create_smartpage.py \
  --source "/absolute/path/report.md" \
  --title "报告标题" \
  --apply
```

本地图片需要用户另行提供支持 `doc +doc_upload_image` 的 helper，并通过 `WECOM_UPLOAD_HELPER` 指定。仓库不附带该扩展；缺少 helper 时不要生成图片残缺的文档。

## 安全边界

- 创建和修改必须对应用户当前请求；删除、取消和整篇覆盖需要针对精确对象再次确认。
- 成员、文档、会议、日程和待办 ID 只用于本机调用，不出现在共享日志或版本库。
- 全量替换语义的字段要先读取现值并合并。
- 远端响应成功后仍应回读；创建成功但无读取权限时，要把这两个事实分开报告。
- 私密操作回执使用 owner-only 权限保存；不自动删除用户数据或失败后已创建的云端对象。

详细决策规则见 [SKILL.md](SKILL.md)，对象级说明在 `references/` 下。本目录的自有文件适用仓库顶层 MIT License；外部 `@wecom/cli` 仍按其自身许可与服务条款运行。
