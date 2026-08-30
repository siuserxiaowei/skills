# 身份、profile 与授权

## 先回答三个问题

1. 这次操作代表哪个人或应用？
2. 目标资源属于哪个租户和可见范围？
3. 所需能力由应用 scope、用户 grant、群/文档成员关系还是管理员角色控制？

`user` 和 `bot` 不是两种可互换的 token。相同查询在错误身份下可能返回空集合而不是报错。

## 只读诊断顺序

1. `lark-cli --version`；
2. `lark-cli whoami --profile NAME`；
3. `lark-cli auth status --profile NAME --json --verify`，仅在确需认证诊断时；
4. 精确命令 help/schema 中的 supported identity 与 scopes；
5. 目标资源的成员关系或共享权限。

不要为了诊断运行会切换全局状态的 profile 命令，不要回显 app secret 或 token。

## 最小权限恢复

- user 缺 scope：优先请求错误返回的最小 scope；应用后台已启用不代表用户已授权。
- bot 缺 scope：走应用权限配置；用户 OAuth 登录不能补足 bot 权限。
- 权限错误带有 `missing_scopes`、`console_url` 或 `hint` 时，可把必要信息交给用户，但 URL 原样传递，敏感 code 不持久化。
- 不用 `--domain all` 作为默认修复；只有用户明确需要并理解范围时才扩大。

## Device Flow

AI 或非交互环境用分步流程：

1. 发起带最小 scope 的 `auth login --no-wait --json`；
2. 把 verification URL 原样提供给用户；二维码只在设备切换或用户需要时生成，不强制制造文件；
3. 结束当前轮，等待用户完成；
4. 后续轮使用同一次流程的 device code 完成登录；
5. 过期或失败就重新发起，不复用旧 code。

device code 与 token 都是秘密。不要将它们放进仓库、长期笔记、截图标题或日志。

## 注销与撤权

本机 logout、服务端撤销用户授权、移除应用 scope、移除资源成员是不同动作。先说明用户要清除哪一层，再执行对应操作；不要把“本机已注销”写成“服务器授权已撤销”。
