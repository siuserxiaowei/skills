---
name: wechat-local-vault
description: 在 macOS 本机建立并查询私有微信数据快照。适用于盘点数据库、离线校验已有密钥候选、创建全量或增量明文快照、查会话与联系人、按时间检索消息、导出指定聊天、查看朋友圈或收藏，以及准备群聊摘要素材。所有查询只读，默认隐藏内部账号标识，不操控微信界面，也不发送任何内容。
---

# 微信本地私有快照

这套工具把“原始微信库”和“可查询快照”隔开。查询命令只打开解密后的 SQLite 文件；解密命令只读取原库，并把结果写到本机私有目录。任何时候都不能借本 Skill 发消息、点开微信窗口、处理第二个容器，或把明文数据库放进仓库及同步盘。

需要范例时阅读 [references/examples.md](references/examples.md)。

## 开始前准备

- 确认用户有权检查这份本机微信数据，并选择只读查询、离线 key 校验、生成快照、导出还是摘要素材；
- 指定原始数据目录或已验证明文快照、准确会话/联系人和日期边界；涉及自然语言日期时先声明时区；
- 为任何新快照、报告或素材包准备不在仓库/同步盘内的私有目标，输出文件不得已存在；
- 只有生成明文快照才需要已验证 key；只读查询不应接触微信进程。当前版本不执行实时注入、客户端控制或媒体解密。

## 先判断动作等级

1. 仅检查现状、联系人、会话、消息、收藏或朋友圈：直接使用 `vault_cli.py`，不需要进程权限。
2. 已经有候选 key 或捕获日志：用 `extract_keys.py --match-only` 做离线校验。
3. 要生成明文快照：确认来源目录、目标私有目录及源库 WAL 状态，再运行解密命令。
4. 要接触进程或制作已签名应用副本：本版本不执行。说明限制，由用户选择独立且有授权的本机工具；不要偷偷换路线。

## 不可越过的边界

- 默认输出不包含 wxid、userName、salt 或 key；用户确实需要账号标识时，查询入口必须显式加 `--show-identifiers`。
- `--show-sensitive` 仅用于用户主动要求的本地故障排查，结果不得转贴到对话或日志。
- 所有 SQLite 查询使用只读连接。遇到缺表、歧义联系人或损坏文件就停止，不猜测结果。
- 明文快照、游标、manifest 与素材包使用私有权限；显式输出文件若已存在会报错，绝不覆盖。
- 原始库旁存在非空 WAL 时停止解密。先退出微信并取得一致副本，不能生成“看起来成功”的残缺快照。
- `--clean` 会把旧快照改名保留，不直接删除。
- 摘要素材不会更新 `history.json`；只有成稿确认后的独立流程才可推进摘要游标。
- 图片、语音和附件只显示类型提示。本 Skill 不解密媒体，也不凭上下文编造其中内容。

## 查询入口

先把目录保存到配置，或在命令前传 `--decrypted-dir <PRIVATE_SNAPSHOT>`。常用调用如下：

```bash
python3 {{SKILL_DIR}}/scripts/vault_cli.py status --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py sessions --limit 20 --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py unread --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py new-messages --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py contacts --query "项目群" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py members "项目群" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py history "客户甲" --start-time "2026-08-01" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py search "交付" --chat "项目群" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py stats "项目群" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py favorites --type article --query "研究" --format text
python3 {{SKILL_DIR}}/scripts/vault_cli.py moments --name "联系人甲" --start "2026-08-01" --format text
```

消息筛选接受 `text`、`image`、`voice`、`video`、`sticker`、`location`、`link`、`file`、`call` 与 `system`。

名称可能命中多人时，命令会拒绝继续。先缩小 `contacts --query` 的关键词；只有用户明确需要时，再用 `--show-identifiers` 找到精确 ID。

## 导出和摘要素材

导出单个会话：

```bash
python3 {{SKILL_DIR}}/scripts/vault_cli.py export "客户甲" --start-time "2026-08-01" --format markdown --output <PRIVATE_REPORT.md>
```

旧入口仍保留。`export_chat.py --mode incremental` 必须同时给 `--since`，这是为了避免未经核验的隐式游标漏掉消息。

生成群聊素材包：

```bash
python3 {{SKILL_DIR}}/scripts/vault_cli.py digest-source "项目群" --start "2026-08-20" --end "2026-08-29" --data-root <PRIVATE_DIGEST_ROOT> --format text
```

素材包包含一份 JSON 和一份 Markdown。它们含聊天原文，必须留在用户指定的私有位置。没有图片说明文件时，后续摘要只能写“图片内容不可见”。

## 密钥候选和快照

列出数据库时默认隐藏 salt 与账号目录：

```bash
python3 {{SKILL_DIR}}/scripts/extract_keys.py --list-dbs --db-base <WECHAT_DB_STORAGE>
```

对已有本地捕获日志进行匹配，不启动或附加进程：

```bash
python3 {{SKILL_DIR}}/scripts/extract_keys.py --match-only --targets all --db-base <WECHAT_DB_STORAGE>
```

创建快照：

```bash
python3 {{SKILL_DIR}}/scripts/decrypt_all_dbs.py --mode full
python3 {{SKILL_DIR}}/scripts/decrypt_all_dbs.py --mode incremental
```

密钥文件沿用 `~/.config/wechat-keys.json`，主配置沿用 `~/.config/wechat-local-vault.json`。测试或隔离运行可用 `WECHAT_VAULT_KEYS`、`WECHAT_VAULT_CONFIG` 与 `WECHAT_VAULT_HOME` 覆盖位置。

## 交付检查

向用户汇报：执行了哪类只读或写入动作、快照或报告保存位置、命中条数、是否存在失败库、是否因 WAL 或歧义而停止。不要在回复中粘贴 key、内部账号标识或大段私聊原文。

实现限制必须直说：当前原创版本支持离线候选匹配，但不提供实时 Frida 注入；媒体内容解密也不在范围内。

## 失败与恢复

失败恢复以“源库不变、未知状态不重放”为准：WAL 不一致、缺表、歧义联系人、损坏页或已有输出都会停止相应分支；按 manifest 报告成功/失败库和恢复条件，不因部分成功宣称全量完成。
