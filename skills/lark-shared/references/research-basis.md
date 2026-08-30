# 研究依据

核对日期：2026-08-30。

## 一手资料

- [larksuite/cli 官方仓库](https://github.com/larksuite/cli)
- [v1.0.92 发布记录](https://github.com/larksuite/cli/releases/tag/v1.0.92)
- [CLI 中文 README](https://github.com/larksuite/cli/blob/v1.0.92/README.zh.md)
- [命令风险门禁实现](https://github.com/larksuite/cli/blob/v1.0.92/cmd/service/service.go)
- [嵌入 Agent 的官方说明](https://open.larksuite.com/document/mcp_open_tools/feishu-cli/embed-feishu-cli-in-agent)
- [飞书开放平台文档入口](https://open.feishu.cn/document/home/index)
- [OAuth 2.0 Device Authorization Grant，RFC 8628](https://www.rfc-editor.org/rfc/rfc8628)
- [RFC 3339 日期与时间格式](https://www.rfc-editor.org/rfc/rfc3339)
- [IANA Time Zone Database](https://www.iana.org/time-zones)

## 现场证据

- 本机 `lark-cli --version`：1.0.71。
- npm registry 于核对日返回 latest 1.0.92，modified 2026-08-28。
- 官方 v1.0.92 tag commit：`6646386e0996b1ff5df640bccff834a20bcb203b`。
- 本机 help 明示 read/write/high-risk-write、`--dry-run`、`--yes`、`--profile`、`--as`、`--jq` 与 schema 自省。
- `schema im.messages.delete` 明示 user/bot、scope、Open Platform doc URL 和 high-risk-write。
- v1.0.84 至 v1.0.92 的变更包含身份支持、事件管线、下载安全、会议指南合并、Docs/Drive/Base/Sheets/Slides 能力扩充，证明复制静态参数说明会快速失效。

## 本实现的取舍

保留：领域路由、shortcut 优先、schema 自省、user/bot 身份、最小 scope、结构化输出、高风险门禁、分页和异步任务。

删除：强制生成二维码、默认申请全部 scope、静默更新 CLI、把空结果当成资源不存在、把 exit 10 当普通错误、复制数百页易过期参数文档，以及依赖外部内容指挥 Agent 的做法。

新增：操作计划静态检查、profile 固定、外部内容隔离、时间与分页合同、未知结果恢复、写后业务回读、家族结构审计和版本差异说明。
