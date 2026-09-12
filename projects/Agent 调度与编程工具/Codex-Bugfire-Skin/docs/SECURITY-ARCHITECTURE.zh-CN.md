# BUGFIRE 安全架构：为什么不修改 Codex.app？

**BUGFIRE 是运行在官方 Codex Desktop 外部的本地桌宠扩展。** 它先验证官方应用及其内置 Node.js 的签名，再通过仅绑定 `127.0.0.1` 的 CDP 向已确认的 Codex renderer 注入 CSS 和桌宠 DOM；它不改 `.app`、`app.asar`、代码签名、模型配置或 API Key。

> 适用版本：`1.3.0-bugfire.1` · 2026-08-31 · 非 OpenAI 官方产品

## 数据流是什么？

```text
官方 Codex Desktop（签名保持有效）
        │
        │ 仅本机 127.0.0.1 CDP；验证进程归属与 renderer URL
        ▼
BUGFIRE injector
        ├── 幂等注入 CSS、背景和桌宠 DOM
        ├── 保留原生侧栏、项目选择器、任务区与输入框
        └── 一个 Runtime binding，只接收受限的桌宠事件
                         │
                         ▼
Application Support 本地存档
schema 校验 · lockf 内核锁 · 原子写入 · 0600 权限
```

Renderer 只发送 `reset` 或模拟 Build 的 `failed` / `repair-success` 事件。Injector 会限制事件类型、ID、长度和奖励规则，再在跨进程内核锁中重新读取、结算并保存进度。同一事件 ID 只结算一次。

## 会读取哪些数据？

存档只包含宠物与赛季 ID、XP、失败/成功/修复次数、已解锁技能、成长卡、已结算事件 ID 和更新时间。

BUGFIRE 不读取或保存：

- 任务正文、提示词或对话
- 项目源码、文件名、分支、语言或依赖
- API Key、Base URL、认证文件或模型供应商配置
- 真实 Shell 命令、Build 日志或退出码

首版的 `BUILD · 演示` 只驱动本地状态机，不会运行 `npm`、`make`、`xcodebuild` 或其他项目命令。

### 可选 AI 角色导演的网络边界

桌宠运行时与 pack validator 仍然离线。只有用户主动执行 `bugfire-director.mjs draft-live` 时，CLI 才会把用户提供的角色 brief 发给配置的 OpenAI-compatible endpoint。Key 只从环境变量读取，不接受命令行 secret；解析后的响应和最终 plan 在写盘前都会递归扫描 Key 的精确值，恶意端点即使把凭据回显进合法字段也会失败且不生成文件。endpoint-controlled envelope/content 解析失败只返回固定错误文案，不拼接可能带有 Key 的 parser response excerpt。响应声明的 `Content-Length` 若超过 1 MiB 会在读取 body 前拒绝；随后无论是否有该 header，body reader 都逐 chunk 累计，并在首个越界 chunk 主动取消。这个边界限制的是应用层累计，HTTP/运行时仍可能在交付单个 chunk 前自行缓冲。live `manifestProposal.rights` 一律从已校验的人工 brief 派生；recorded fixture、review 和 materialize 都强制重新提供由操作员控制的 brief，并分别核对摘要和 rights 完全一致，因此不能靠跳过 fixture 校验从 plan 单独持久化伪造 rights。产物只记录 endpoint origin、model ID、时间和摘要。远程 endpoint 必须是 HTTPS，HTTP 只允许本机 loopback 模型或测试服务。

这份 brief 是调用者自行选择和保管的信任根。上述机制验证的是 plan 与该文件的一致性，不认证作者身份、不证明法律权利；普通 SHA-256 是完整性摘要，不是数字签名。

仓库内的 recorded fixture 不联网，并明确标注它不是实时调用。AI draft 无法直接 materialize；人工替换后会先重建 canonical draft 并严格核对 `draftSha256`，再通过原 pack validator。materialize 会在建目录前后拒绝调用方可控路径段中的 symlink；受限于 Node 缺少可移植的 directory-fd `openat` 链，同一用户恶意进程在检查与写入之间抢占替换祖先路径仍属于残余竞态，建议只在私有输出目录运行。

## CDP 如何被限制？

- 调试地址固定为 `127.0.0.1`，不会绑定 `0.0.0.0` 或局域网地址。
- 端口必须归属于官方 Codex 主进程或其合法子进程。
- 只接受预期的 `app://` renderer，不向任意网页注入。
- Watcher 停止前会核对 PID、启动时间和完整命令行；PID 被复用或进程在 TERM 后变身时不会继续 KILL。
- 进度同步复用已经验证的 CDP 会话，不新增 HTTP 服务或监听端口。

CDP 即使只在回环地址也拥有较高权限。主题运行期间不要执行来路不明的本机程序；不用时应暂停或 Restore。

## 自定义宠物包为什么不能带脚本？

`Bugfire Pack v1` 只接受声明式 JSON 和本地 PNG/JPEG/WebP。编译器拒绝远程素材、任意 JavaScript/CSS、路径穿越、素材符号链接、越出包目录的父级链接、扩展名伪装、APNG、动画 WebP、超限字节和超限像素。

图片通过 `O_NOFOLLOW` 同一文件句柄读取，并在前后核对 inode、大小和时间戳；Build 写入已经验证的字节，不在校验后重新打开源文件。同一宠物图被多个状态复用时只编码一次。主题切换先在同一文件系统内完整暂存、设置权限并再次验证，再用原子重命名替换活动目录；失败时恢复旧主题。

素材包必须声明使用权。校验降低的是执行与路径风险，不代替版权、肖像权或商标审查。

## 如何完整恢复？

```bash
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh \
  --restore-base-theme --restart-codex
```

Restore 会停止身份匹配的 watcher，移除注入 DOM、样式、监听器和 Runtime binding，并恢复安装前备份的基础外观设置。官方应用包从始至终不被修改。

## 如何自行核验？

```bash
cd macos
./tests/run-tests.sh

~/.codex/codex-dream-skin-studio/scripts/doctor-macos.sh --require-live
~/.codex/codex-dream-skin-studio/scripts/verify-dream-skin-macos.sh --reload
/usr/bin/codesign --verify --deep --strict /Applications/ChatGPT.app
```

`doctor --require-live` 与 `verify --reload` 只有在当前 Codex 由已验证的回环 CDP 会话启动时才应返回 `pass: true`。不要把历史截图或静态测试描述成当前实时验证。

本版本的实际测试与 release build 结果在发布前重新记录；不要沿用旧版 87/87 的数字冒充当前验收。详细证据见 [QA inventory](../macos/references/qa-inventory.md)、[隐私说明](PRIVACY.md) 与根目录 [安全策略](../SECURITY.md)。
