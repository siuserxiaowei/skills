# Lark Apps｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证；每次运行先查看当前 `apps --help` 与具体命令帮助。示例不包含真实密钥，`app_id` 和路径必须由本次任务确认。

## 使用说明

- **何时使用：** 需要发布 HTML、核对 release，或区分应用发布与数据库/配置动作时读取。
- **准备/输入：** 确认 app ID/type、local/dev/online 环境、工作区构建目录、当前 release 和敏感文件扫描结果。
- **执行方式：** 先 get 与 dry-run；发布只执行一次，返回 release ID 后仅轮询该 release。
- **验收/边界：** 用真实 URL/release 终态和页面打开结果验收；发布授权不包含数据库迁移、密钥或 access scope 变化。

## 正向案例

### 发布一个已构建的 HTML 应用

- **用户请求：** “把工作区里的 `site/` 发布到‘活动报名页’应用，先检查内容和预览请求，再正式发布。”
- **准备信息/输入：** `work` profile 的 user 身份可见该应用；`site/` 已本地打开验收；目录不含 `.env`、凭证、私钥或未授权素材；应用名称已消歧为一个 `app_id`。
- **处理：**

```bash
lark-cli apps +list --profile work --as user --keyword '活动报名页' --ownership mine --format json
lark-cli apps +get --profile work --as user --app-id <app_id> --format json
lark-cli apps +html-publish --profile work --as user --app-id <app_id> --path site --dry-run --format json
```

核对应用类型、将要上传的目录、敏感文件扫描结果和当前发布状态后，按用户已有的明确发布授权执行一次：

```bash
lark-cli apps +html-publish --profile work --as user --app-id <app_id> --path site --format json
```

若响应返回 `release_id`，只轮询该 release，不重新发布：

```bash
lark-cli apps +release-get --profile work --as user --app-id <app_id> --release-id <release_id> --format json
```

- **预期输出：** HTML 类型返回可访问 URL，需发布类型返回可追踪的 release 及终态。
- **验收证据：** `app_id`、应用类型、构建目录、release/URL 与服务端状态对应；真实页面能打开；Git diff 和输出日志中没有 secret。

## 边界案例

### 发布不授权数据库和生产配置变化

- **用户请求：** “把这个应用上线，顺便把数据库和环境变量配好。”
- **边界判断：** 发布代码、迁移 online 数据库、写环境变量和扩大访问范围属于四个独立控制面，发布授权不能自动覆盖后三项。
- **处理：** 把 HTML/应用发布、online 数据库迁移、环境变量写入、权限开放拆成不同计划；先只读 `+get`、`+db-env-diff`、`+env-list`，分别展示影响。任何 production、密钥、不可逆 migration 都需要单独对象级确认。
- **验收证据：** 用户只确认发布时，release 可以变化，但数据库 schema、环境变量、角色、access scope 和自动化启用状态均保持基线值。

## 失败与恢复

### 发布响应丢失

- **场景：** 上传完成后连接中断，客户端没有拿到明确终态。
- **处理与恢复：** 按已返回的 `release_id` 用 `+release-get` 查询；没有 ID 时用 `+get`/`+release-list --help` 先定位同一时间窗候选，不再次运行 `+html-publish`。
- **验收证据：** 找到 release 时报告其真实状态与日志；无法确定时交付“状态未知”、请求时间、`app_id` 和核查路径，绝不制造第二个发布。
