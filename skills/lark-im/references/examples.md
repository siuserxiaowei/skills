# Lark IM｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。所有群名和人名都先解析成稳定 ID；示例幂等键必须替换为本次操作唯一且可追踪的值。

## 使用说明

- **何时使用：** 需要发送/回复消息、处理同名受众、附件或未知发送结果时读取。
- **准备/输入：** 确认 chat/user/message/thread ID、profile/identity、最终正文/附件、外部受众、线程位置和幂等键。
- **执行方式：** 先 search 与 dry-run 展示目标/内容；确认后发送一次，再按 message ID 回读，超时沿用同一幂等键查证。
- **验收/边界：** 用 message ID、chat ID、sender、正文与时间验收；单一受众不自动扩成批量、@ 全员、加急或群成员变化。

## 正向案例

### 预览后向唯一项目群发送通知

- **用户请求：** “给‘支付重构项目群’发停机维护通知：今晚 23:00 到 23:30 暂停服务；先让我看预览。”
- **准备信息/输入：** profile/identity 为 `work`/user；已确认群是否含外部成员；正文、时间与时区明确；无附件；本次幂等键为 `maint-20260831-pay-v1`。
- **处理：**

```bash
lark-cli im +chat-search --profile work --as user --query '支付重构项目群' --page-size 20 --format json
lark-cli im +messages-send --profile work --as user --chat-id <chat_id> --text '维护通知：2026-08-31 23:00–23:30（Asia/Shanghai）暂停服务。' --idempotency-key maint-20260831-pay-v1 --dry-run --format json
```

展示群名、chat ID 后缀、群类型/外部成员、发送者和最终正文。用户确认后执行一次并按 message ID 回读：

```bash
lark-cli im +messages-send --profile work --as user --chat-id <chat_id> --text '维护通知：2026-08-31 23:00–23:30（Asia/Shanghai）暂停服务。' --idempotency-key maint-20260831-pay-v1 --format json
lark-cli im +messages-mget --profile work --as user --message-ids <message_id> --format json
```

- **预期输出：** 目标群中产生一条文本消息，不额外私聊或 @ 全员。
- **验收证据：** 回读 message ID、chat ID、sender、正文和时间一致；幂等键与本次操作绑定；未命中任何同名群。

## 边界案例

### 姓名、外部群和全员提及需要另行消歧

- **用户请求：** “发给张总，再在所有客户群里 @ 全员。”
- **边界判断：** “张总”不是稳定用户 ID，“所有客户群”和 @ 全员又把单一受众扩成批量外部通知，不能从一句话中安全确定对象与影响。
- **处理：** “张总”不是稳定身份，“所有客户群”和 @ 全员扩大受众；先用 contact/chat search 列出候选并分别确认，不从单条通知授权推导批量发送。
- **验收证据：** 未确认前没有 send/reply/urgent 写请求；候选清单明确内部/外部、群数量和预计通知影响。

## 失败与恢复

### 发送响应超时

- **场景：** send 请求已提交但客户端未收到 message ID。
- **处理与恢复：** 保留 chat ID、幂等键、正文 hash 和时间；先按当前 help 提供的消息搜索/聊天消息列表在窄时间窗查询。若重试，必须沿用同一幂等键，绝不能换键制造第二条消息。
- **验收证据：** 找到唯一匹配则回读并交付；仍未知时明确状态未知并停止；任何结果都不以“再发一次看看”恢复。核查记录必须显示原 chat ID、原幂等键和命中的 message ID。
