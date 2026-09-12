# Security Notes

这个工作台按本地优先设计，用来调度个人项目，不用于公网服务或客户生产环境。

## 必做

1. Hub 只监听 `127.0.0.1`。
2. 首次启动后立即运行 `npm run passwd`，修改默认管理员密码。
3. Agent 工作目录使用项目子目录，不使用 `$HOME`、Obsidian vault 根目录或微信数据目录。
4. 只把需要处理的 Markdown、仓库状态和检查结果交给 Agent。
5. 发布、push、删除、覆盖主笔记、修改微信客户端等动作都需要人工确认。

## 禁止

- 不上传微信聊天数据库、导出的 Markdown、图片、Obsidian vault 或 secrets。
- 不把 Hub、Dashboard、Agent Node 暴露到公网。
- 不把默认账号密码写入脚本、笔记或仓库。
- 不提交 `.anet/`，里面可能包含本机节点 token。
- 不让 Agent 自动执行 `rm -rf`、`git push`、发布网页、发布公众号。

## 推荐

- 用 `90_Agent/test/` 做新工作流的第一轮验证。
- 每条流水线先生成检查报告，再由人决定是否进入实际修改。
- 对外发布前，用 `review-agent` 做隐私、事实和引用检查，用 `qa-agent` 做文件与脚本检查。
