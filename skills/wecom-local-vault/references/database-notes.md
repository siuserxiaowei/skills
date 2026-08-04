# 企业微信 5.x 本地数据库笔记

## 适用对象

- 平台限定为 macOS 版企业微信 5.x。
- Bundle ID 一般是 `com.tencent.WeWorkMac`。
- 判断一份数据集的依据：`message.db`、`session.db`、`user.db` 三个库同时存在。
- 个人微信（`com.tencent.xinWeChat`）不在覆盖范围内。

## 加密格式细节

企业微信 5.x 用的是 wxSQLite3 式 AES-128-CBC 分页加密，这跟个人微信 4.x 的 SQLCipher AES-256/HMAC 完全是两套格式：

- raw key 长度 16 字节。
- page size 一般为 4096 字节。
- 每页 AES key 的派生方式：对 `raw_key + little_endian(page_number) + b"sAlT"` 做 MD5。
- IV 的派生方式：用页码驱动 wxSQLite3 兼容伪随机序列，再取 MD5。
- 第一页仍保留部分 SQLite header 字段，可用来识别格式并校验 key。
- 不存在个人微信 SQLCipher 那种 80 字节 reserve/HMAC 区。

## 主要数据库与表结构

### `user.db`

- `user_table`：联系人主表。高频字段：`id`、`name`、`real_name`、`account`、`external_corp_name`、`external_job`。
- `external_user_relation_v3`：外部联系人备注。高频字段：`user_id`、`remarks`、`real_remarks`、`corp_remark`。

### `session.db`

- `conversation_table`：会话表。高频字段：`id`、`name`、`roomname_remark`、`last_message_time`、`last_message_id`。
- `conversation_user_table`：群成员昵称表。高频字段：`conversation_id`、`user_id`、`nick_name`。
- conversation ID 前缀的含义：`R:` 表示群聊、`S:` 表示单聊、`M:` 表示微信联系人、`O:` 表示应用、`Y:` 表示系统。

### `message.db`

消息可能分布在这些表里：

- `message_table`
- `message_small_table`
- `kf_message_tableV1`

高频字段：`message_id`、`server_id`、`sequence`、`sender_id`、`conversation_id`、`content_type`、`send_time`、`flag`、`content`、`extra_content`、`local_extra_content`。

任何查询前都先跑 `PRAGMA table_info` 确认字段；版本一变字段就可能变，不要假定字段恒定存在。

## WAL 的处理方式

企业微信运行期间，新消息可能还停在 `*.db-wal` 里。本 Skill 并不产出可挂载的明文 WAL，实际做法是：

1. 先对源 WAL 做一次字节级快照读取。
2. 解析 32 字节 WAL header 与每个 24 字节 frame header。
3. 仅保留最后一个 commit frame 之前的完整事务。
4. 依据 frame 记录的数据库页码逐页解密。
5. 把解密后的页面写进新建的明文数据库快照，并按 commit size 截断。

源数据库全程不被修改，也无需依赖解密后已然失效的 WAL checksum。

## 校验与权限

- key 的通过标准：解密第一页后出现合法 SQLite header，且第 100 字节是合法 B-tree page type。
- 密钥文件权限一律 `0600`，所在目录 `0700`。
- 明文数据库与导出文件权限 `0600`。
- manifest 中既不放 raw key，也不放原始账号目录。
