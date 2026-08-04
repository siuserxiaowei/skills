---
name: wecom-local-vault
description: Decrypt and read local WeCom/企业微信 5.x desktop databases on macOS into a private read-only vault, then query, search, and export from that vault. Use when the user asks about parsing 企业微信本地数据、企微聊天记录、WeCom/WXWork contacts, sessions, groups, customers, message history, local database backup, structured export, or any Mac enterprise-WeChat data analysis workflow.
---

# wecom-local-vault：Mac 企业微信本地数据私密 Vault

本 Skill 面向 macOS 上的企业微信 5.x：从本地加密数据库产出一份全新的私密明文快照，之后对联系人、会话和消息的一切查询都针对快照进行。它与个人微信的 `wechat-local-vault` 相互独立，两边在容器路径、加密方式和表结构上都不通用，切勿混用。

## 不可逾越的边界

- 原始 `/Applications/企业微信.app` 一律不动：不点击、不退出、不重启、不重签，也绝不代发任何企业微信消息。
- 仅当用户当轮明确说出“修改边界 / 用重签副本抓企微 key / 继续完整解密”时，才把企业微信复制进私密 Vault，对这份副本做 ad-hoc 重签，并用 Frida 拉起副本来捕获 key。
- 重签副本的用途仅限本机 owner 授权的数据解析：默认不复用旧副本、不覆盖已有副本，也不写进项目目录或云盘。
- 默认不 attach 企业微信进程。只有在用户明确说“抓企微 key / 捕获密钥 / 继续解密”时，才允许执行带 `--confirm-attach` 的捕获命令；系统拒绝 attach 时，优先切换到签名副本方案。
- 对源数据库和 WAL 只读，绝不写回企业微信容器。
- 任何文件都不删除、不覆盖：解密总是新建带时间戳的快照，导出总是新建文件。
- 回复与日志中一律不出现 raw key、完整账号目录、联系人内部 ID 或整段私聊原文。
- 明文快照、密钥文件、导出结果都是敏感数据，禁止放进项目、桌面、云盘或 Git。

## 从这里开始

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/wecom-local-vault"
python3 "$SKILL_DIR/scripts/vault_cli.py" status
```

依赖情况：发现与查询阶段只要 Python 3；`decrypt` 需要 `pycryptodome`；在 Mac 上被动捕获 key 还需要 `frida`。缺什么先如实报告，不要替用户自动安装。

## 工作流如何自动选择

1. 初次使用、或用户问“能不能解析”：执行 `status`，仅做数据库检查，不碰任何进程。
2. 私密 key 文件已存在：执行 `decrypt` 生成新快照，默认把已提交的 WAL 帧一并合并。
3. 还没有 key：先向用户说明捕获必须明确授权；可以先试只读 attach，若 macOS 拒绝 `task_for_pid`，再走重签副本捕获。
4. 快照已存在：直接用 `sessions`、`contacts`、`history`、`search`、`export`，避免重复解密。
5. 用户给出具体会话或时间段：只查该范围；消息量大时先落成 Markdown/JSON 文件再看。

## 数据库发现与状态检查

```bash
python3 "$SKILL_DIR/scripts/vault_cli.py" discover
python3 "$SKILL_DIR/scripts/vault_cli.py" status
python3 "$SKILL_DIR/scripts/vault_cli.py" status --show-paths
python3 "$SKILL_DIR/scripts/capture_key_macos.py" list
python3 "$SKILL_DIR/scripts/capture_key_macos.py" doctor
python3 "$SKILL_DIR/scripts/scan_dbkey_manager_macos.py" scan
```

`--show-paths` 只在用户确实要看真实路径时才加。机器上有多个账号时，用 `--data-dir` 指明包含 `message.db`、`session.db`、`user.db` 的那一份数据集。

## 捕获 Mac 企业微信 key

这一步只对已在运行的进程做被动附加，不会启动或操纵客户端，且必须拿到用户当轮的明确授权：

```bash
python3 "$SKILL_DIR/scripts/capture_key_macos.py" capture \
  --confirm-attach \
  --duration 60
```

捕获器会监听 CommonCrypto 的 AES/MD5 调用，把每个候选 16 字节 key 与本地加密数据库第一页逐个比对验证；验证通过后才以 `0600` 权限写进私密 Vault，终端全程不显示 key。一旦超时，就如实报告“未捕获”——不要引导用户去客户端里点击，也不要自行重签应用。

`doctor` 以只读方式检查 Python、Frida、Developer Tools、SIP 和数据库格式。遇到 macOS 拒绝 `task_for_pid` 的情况，应停止捕获并向用户说明权限边界，而不是自动关闭 SIP、放宽系统 `taskport` 或重签企业微信。可参考 [Frida macOS 官方说明](https://frida.re/docs/examples/macos/)与[官方故障排查](https://frida.re/docs/troubleshooting/)。

### 走重签副本捕获

若原始企业微信的 attach 被 macOS 拒绝，而用户又明确同意修改边界，此时允许复制一份企业微信并做 ad-hoc 重签。脚本随后通过 Frida 启动该副本并静候 key 出现；副本若要求登录，只提示用户自己手动登录——脚本不点 UI、不发消息、也不关闭原始企业微信。如果原始企业微信还在运行，副本可能被单实例机制拉起后立即退出，这时必须请用户自行退出原始客户端再重试。

```bash
python3 "$SKILL_DIR/scripts/capture_key_macos.py" capture \
  --mode spawn-signed-copy \
  --confirm-signed-copy \
  --duration 240
```

副本的默认落盘位置：

```text
~/Library/Application Support/wecom-local-vault/apps/WeComSigned-<timestamp>.app
```

这条路线除常规 hook 外，还会 hook `DbKeyManager::UpdateKey`、`GetAllLocalEncryptKey` 回调以及 wxSQLite3 内部页加解密函数。以当前 5.0.x macOS 客户端为例，内部页加解密函数会复制 `args[3][0..15]`，再拼接页码与 `sAlT` 派生出每页 AES key；捕获器把这份 16 字节 raw key 候选与当前本地数据库第一页逐一验证，验证成功才保存。

如果 Frida 被系统拦截，可以退到只读 Mach VM 扫描 DbKeyManager 的方案：不注入代码、不重启或重签客户端、不碰 UI，代价是需要用户在本机终端输入管理员密码：

```bash
python3 "$SKILL_DIR/scripts/scan_dbkey_manager_macos.py" scan --confirm-sudo
```

扫描器利用进程当前 load address 定位 `DbKeyManager` vtable，仅读取 `this+0x68` 处 Apple libc++ `std::string` 里的候选 key；候选须通过数据库第一页验证才会写入私密 Vault，raw key 同样不会出现在终端。

## 生成明文快照

```bash
python3 "$SKILL_DIR/scripts/vault_cli.py" decrypt
python3 "$SKILL_DIR/scripts/vault_cli.py" decrypt --key-file "/private/path/keys-时间戳.json"
```

快照的默认落盘位置：

```text
~/Library/Application Support/wecom-local-vault/snapshots/<timestamp>-<dataset_id>/
```

每个快照目录都带 `manifest.json`，其中标记 `contains_plaintext_wecom_data: true`。解密时，脚本仅处理 WAL 中 header salt 匹配、且位于最后一次已提交事务之前的页面，把它们解密合并进新快照，源 WAL 保持原样。

## 查询与导出

```bash
python3 "$SKILL_DIR/scripts/vault_cli.py" sessions --limit 50
python3 "$SKILL_DIR/scripts/vault_cli.py" contacts --query "关键词"
python3 "$SKILL_DIR/scripts/vault_cli.py" history "群名或conversation_id" \
  --start "2026-07-01" --end "2026-07-13" --limit 500
python3 "$SKILL_DIR/scripts/vault_cli.py" search "关键词" \
  --chat "群名" --start "2026-07-01" --limit 200
python3 "$SKILL_DIR/scripts/vault_cli.py" export "群名" \
  --start "2026-07-01" --format markdown
```

不加参数时读取最新快照；若要锁定某个证据版本，传 `--snapshot`。导出结果默认落在私密 Vault 的 `exports/` 下，权限 `0600`，目标文件已存在时一律拒绝覆盖。

## 目前的已知限制

- 在 Mac 上抓 key 的前提是捕获期间企业微信确实在打开或读写加密数据库；若这段时间没有触发任何 wxSQLite3 页加解密调用，就可能一无所获。
- 消息二进制体走通用的 UTF-8/Protobuf 文本提取；图片、语音、文件的正文暂以类型占位输出，不做媒体解密。
- 判断会话方向需要可靠的本人内部 ID；确认之前，不要想当然地把某个发送者标注成“我”。
- 企业微信每次升级都可能改动密钥调用位置或表结构；处理真实数据前，先跑离线测试和 `status`。

数据库格式、表结构与 WAL 的更多细节见 [references/database-notes.md](references/database-notes.md)。

## 自检

```bash
cd "$SKILL_DIR/scripts"
python3 test_wecom_local_vault.py
python3 -m py_compile *.py
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" "$SKILL_DIR"
```
