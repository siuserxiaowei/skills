# 运行时发现与版本漂移

## 事实层级

从高到低使用：

1. 当前可执行文件对精确命令给出的 `--help` 与 `schema`；
2. 当前可执行文件的结构化错误、risk、identity 和 scope 元数据；
3. 与该版本配套的内置 Skill；
4. 官方仓库对应 tag 的源码、测试和 release notes；
5. 当前飞书/Lark Open Platform 文档；
6. 本仓库静态示例。

静态示例只能说明意图，不能证明某个 flag 在用户机器上存在。

## 三层命令面

- **Shortcut**：`lark-cli DOMAIN +ACTION`。适合常见多步业务工作流，应优先。
- **类型化资源**：`lark-cli DOMAIN RESOURCE METHOD`。执行前用 schema 获取请求与响应结构。
- **原始 API**：`lark-cli api METHOD /open-apis/...`。仅在前两层缺能力且官方文档已确认时使用。

不要把 URL 查询串塞进 raw API path；参数应进入 CLI 暴露的 params/data 参数。不要从旧 Skill 复制一段 JSON 后直接发送。

## 版本矩阵

2026-08-30 的研究快照：

| 项目 | 版本或状态 | 用途 |
|---|---|---|
| 本机 `lark-cli` | 1.0.71 | 本地 help/schema 和无凭证测试的运行时事实 |
| npm latest | 1.0.92，发布于 2026-08-28 | 当前发布边界 |
| 官方源码 tag | v1.0.92，commit `6646386e…` | 变更、测试和风险实现依据 |
| 会议指南 | v1.0.89 起合并为 `lark-meeting` | 老版本的 vc/minutes/note/vc-agent 入口需兼容路由 |

本仓库不要求静默升级。遇到命令缺失时先查 `lark-cli skills list`、`--help` 和 release notes；把升级作为用户可选方案，不为业务任务自行修改全局 CLI。

## 兼容降级

- shortcut 缺失：查当前域的类型化资源和 schema。
- 域被合并：保留原业务意图，按 `skills list` 指出的新入口取证。
- 参数改名：重新生成 argv，不把未知 flag 透传。
- 输出字段变化：以 `ok`、`data`、`error` 与命令 output schema 为准，不依赖未声明的深层字段。
- API 尚未注册：只有在官方文档给出方法、路径、身份、scope 和数据结构时才用 raw API。
