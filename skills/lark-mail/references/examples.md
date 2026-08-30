# Lark Mail｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。示例邮件地址、message ID 和附件均为占位值；附件必须是当前工作区内的相对路径。

## 使用说明

- **何时使用：** 需要起草/发送邮件、核对附件，或恢复未知发送状态时读取。
- **准备/输入：** 确认 mailbox/from、To/CC/BCC、subject、最终正文、附件相对路径和 reply/thread 语境。
- **执行方式：** 默认 dry-run/草稿；只有用户确认最终版本后才用 `--confirm-send`，随后按 message/thread ID 回读。
- **验收/边界：** 用 sent/draft 状态、受众、正文和附件元数据验收；“写邮件”不等于发送，reply-all 与外部域需重新核对。

## 正向案例

### 预览后发送带附件的客户邮件

- **用户请求：** “给客户 `buyer@example.com` 发 Q3 报价邮件，附件是 `quotes/Q3.pdf`；先给我看最终版本再发。”
- **准备信息/输入：** profile 为 `work`，user 身份可访问 `sales@example.com` mailbox；To、CC/BCC、主题、HTML 正文已确定；附件存在、MIME/大小和使用权已核对。
- **处理：** 先 dry-run，展示发件人、所有受众、主题、正文和附件清单；不要先创建一个随后难以对账的重复草稿：

```bash
lark-cli mail +send --profile work --as user --mailbox sales@example.com --from sales@example.com --to buyer@example.com --subject 'Q3 报价方案' --body-file mails/q3-quote.html --attach quotes/Q3.pdf --dry-run --format json
```

用户确认精确版本后执行一次发送并按返回 ID 回读：

```bash
lark-cli mail +send --profile work --as user --mailbox sales@example.com --from sales@example.com --to buyer@example.com --subject 'Q3 报价方案' --body-file mails/q3-quote.html --attach quotes/Q3.pdf --confirm-send --format json
lark-cli mail +message --profile work --as user --mailbox sales@example.com --message-id <message_id> --format json
```

- **预期输出：** 返回服务端 message/thread ID，邮件进入真实发送状态；只有一个发送尝试。
- **验收证据：** 回读的 From/To/CC/BCC、subject、正文摘要、附件名称/大小、message ID 和 sent 状态与确认稿一致；没有把 BCC 暴露给其他收件人。

## 边界案例

### 只要求“写邮件”不等于立即发送

- **用户请求：** “帮我写一封催款邮件。”
- **边界判断：** 用户授权内容创作，但没有提供确定收件人，也没有要求发送；群发、外部域、reply-all 和敏感附件会进一步扩大影响。
- **处理：** 先在对话中交付草稿或在收件人完整时创建服务端 draft（调用 `+send` 但不加 `--confirm-send`）；明确列出待补 To/CC/BCC 和附件，不发送。
- **验收证据：** 最多产生 draft ID，服务端没有 sent 状态/发送时间；所有收件人字段都保持待确认，不存在自动 reply-all。

## 失败与恢复

### 发送或附件上传状态未知

- **场景：** 上传附件后连接中断，或 send 返回超时而没有明确终态。
- **处理与恢复：** 保留 mailbox、受众、主题、附件 hash、请求时间及已返回的 draft/message/thread ID；优先按 ID 回读，或使用当前 `+triage --help` 提供的 sent 时间窗查询。未知时不再调用 `+send --confirm-send`；若附件明确失败，则保留草稿并标出缺失附件。
- **验收证据：** 找到消息时以同一 message/thread ID 的 sent/draft 状态为准；找不到时报告检索 mailbox、时间窗和主题，状态维持未知，不产生第二封同主题邮件。
