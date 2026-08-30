# WeCom 本地私有快照｜验收案例

所有操作只适用于用户有权检查的本机企业微信数据。源库只读，明文快照、key、manifest 与导出都必须使用 owner-only 权限。

## 使用说明

- **何时使用：** 被动发现授权的 WeCom 数据、经单独授权捕获/验证 secret、生成快照或导出有限会话。
- **准备/输入：** dataset label/data-dir、已验证 secret 或 snapshot、会话/日期/时区、全新私有输出和动作级授权。
- **执行方式：** 被动检查优先；capture/signed-copy/sudo 分门授权；解密创建新时间戳快照，查询固定 snapshot。
- **验收/边界：** manifest、条数、权限和源库不变可证明；未知页头/schema/布局 fail closed，不控制客户端、不泄露 ID/secret。

## 正向案例

### 导出项目群一周消息

- **用户请求：** “导出项目群 2026-08-24 到 2026-08-30 的消息为 Markdown，不要改源库。”
- **准备信息/输入：** 已有通过首页校验的 16-byte secret 或可用私有快照；用户选择准确 dataset label、时区和不存在的输出文件；不要求媒体内容推断。
- **处理：** 设置 `SKILL_DIR`，依次运行 `python3 "$SKILL_DIR/scripts/vault_cli.py" status` 与 `discover`；若需新快照，执行 `python3 "$SKILL_DIR/scripts/vault_cli.py" decrypt --key-file "/private/location/key.json"`；固定新 snapshot 后先用 `sessions`/`search` 消歧群，再运行当前 `--help` 支持的 `history` 或 `export`，同时给出开始与结束边界。
- **预期输出：** 新建私有 Markdown，只包含目标会话与时间窗；源数据库与 WAL 未变化。
- **验收证据：** dataset label、snapshot/manifest、消息数、输出权限、日期边界、源文件大小/mtime/哈希前后对比。

## 边界案例

### 只做发现但未授权进程接触

- **用户请求：** “看看本机有没有可读的企微数据，先别附加进程。”
- **边界判断：** 用户只授权被动检查；可能存在多个账号数据集。
- **处理：** 仅运行 `status`、`discover` 和 `python3 "$SKILL_DIR/scripts/capture_key_macos.py" doctor`；不执行带 `--confirm-attach`、`--confirm-signed-copy` 或 `--confirm-sudo` 的命令。若返回多个 opaque label，请用户选定或提供准确 `--data-dir`，不得通过联系人内容猜账号。
- **预期输出：** 报告可发现性和缺失条件，不附加、启动、签名或 sudo 读取任何进程。
- **验收证据：** 被动命令列表、候选 dataset 数、路径是否按默认隐藏，以及无 capture/signed-copy/sudo 事件。

## 失败与恢复

### 客户端更新导致格式未知

- **场景：** 加密页头、schema 或已知 5.x `DbKeyManager` 内存布局不匹配。
- **处理与恢复：** fail closed，保留只读诊断并停止；不把未知列解释为联系人或消息，不把超时解释为 key 错误。先用脱敏 fixture 更新兼容逻辑并通过离线测试，之后才能再次处理 live data。
- **预期输出：** 不产生虚假明文或误导导出，源状态不变。
- **验收证据：** 明确 unsupported boundary、无 plaintext claim、fixture 测试要求、失败 manifest/日志和下一次重试版本条件。
