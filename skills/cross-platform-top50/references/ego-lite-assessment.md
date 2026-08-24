# ego-lite 适配评估

仅在 `ego-browser` / ego-lite 被提议为登录浏览器后端时读取。评估冻结于 2026-08-24；仓库证据固定到 commit `689f71a7bad8b78e22664ca8708a41ceaf263e93`，易变事实须在启用前重查。

## 当前决策

`default_disabled`：保留适配位，不安装、不打包、不作为依赖，也不在生产研究中启用；该状态下不得进入 `auto` / `hybrid` 候选集。它能补足动态 DOM、登录接力、snapshot 与独立 Task Space，但当前四个门禁未关闭：

1. **分发完整性**：公开安装脚本从 CDN 下载 DMG，未固定 artifact digest，也未显式执行 `codesign` / `spctl` 验证，并会移除 quarantine；[Issue #292](https://github.com/citrolabs/ego-lite/issues/292) 的签名问题在评估时仍未关闭。
2. **CLI 数据流**：[README](https://github.com/citrolabs/ego-lite/blob/689f71a7bad8b78e22664ca8708a41ceaf263e93/README.md) 声称浏览数据留在设备上，但适用范围更广的[隐私政策](https://lite.ego.app/privacy)说明服务可能收集 URL、页面内容、交互、搜索、任务日志并交给第三方模型处理；两者不能证明 `ego-browser` CLI 路径零外传，必须取得或验证 CLI 专属数据流与保留说明。
3. **会话隔离**：公开问题 [#303](https://github.com/citrolabs/ego-lite/issues/303)、[#213](https://github.com/citrolabs/ego-lite/issues/213)、[#204](https://github.com/citrolabs/ego-lite/issues/204)、[#199](https://github.com/citrolabs/ego-lite/issues/199) 涉及跨 Space Cookie 或 CDP/session 路由。Task Space 只按工作区隔离理解，不能当安全边界。
4. **许可边界**：仓库 helper/Skill 使用 MIT，但 README 将浏览器本体描述为单独下载；线上 [Terms](https://lite.ego.app/terms) 也不是浏览器二进制的开源再分发许可，启用、打包或再分发前必须核实二进制许可。GitHub Release 的 digest 对应 helper Skill 压缩包，不能当作 DMG 的固定摘要。

供应商的速度、Token 节省与 “browsing data stays on device” 均先标 `supplier_claim`，不能替代独立验证。

它始终只是 Python 控制面下的可选 `browser_session` 访问后端，不是第四套采集/处理引擎；Python、Go、Rust 的长期分工不因是否准入 ego-lite 而改变。

## 重新准入条件

只有以下证据都有当前版本记录时，才能把状态改为 `experimental`：

- 版本化下载地址、固定 SHA-256、有效代码签名与 Gatekeeper 验证；不依赖移除 quarantine 才能启动；
- CLI 模式的出站域名、遥测、页面/截图/任务日志、第三方模型、保留与删除路径已明确；
- 浏览器二进制许可已确认；
- 上述会话问题已修复，或试验明确限制为“每个低敏感 profile 同时一个任务”并证明不会跨 Space 影响；
- 用户对当前任务显式 opt-in，使用独立低权限 profile，只登录本次所需平台，不迁移日常 Chrome 全量 Cookie、扩展、历史或密码。

## 实验期允许面

即使进入 `experimental`，第一阶段只允许：创建/恢复指定 Task Space、白名单公网域名导航、`pageInfo`、`snapshotText`、受限截图、只读滚动/搜索表单、用户 handoff，以及完成后关闭空间。默认禁止 raw CDP、`serverFetch`、`browserFetch`、上传、下载、Cookie/cache mutation、账号互动和发布。

最小 probe：`command exists → 版本/来源核验 → 临时 Task Space → 公开测试页 → pageInfo + snapshot → 最终公网 URL 核对 → 关闭空间`。登录型平台仍走 canonical checkpoint；已有登录态不等于当前任务授权。
