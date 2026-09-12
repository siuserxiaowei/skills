# Feishu-Claude-Code-Bridge

<!-- SIUSER-REPO-GUIDE:START -->
## 项目介绍 / Project Introduction

### 中文
飞书 Claude Code 桥接：连接飞书协作和 AI 编程工作流的团队自动化工具。

### English
Feishu Claude Code bridge for connecting team collaboration with AI coding workflows.

## 使用方式 / Usage

### 中文
1. 先克隆仓库并安装 Node 依赖。
2. 根据 `package.json` 中的 scripts 启动开发、构建或测试命令。
3. 如果有在线入口，先对照线上页面理解最终效果，再回到源码修改。

### English
1. Clone the repository and install the Node dependencies.
2. Use the scripts in `package.json` for development, build, or tests.
3. If a live link exists, review the deployed page first, then make source changes.

## 入口与元信息 / Entry Points & Metadata

- GitHub 仓库 / Repository: https://github.com/siuserxiaowei/feishu-claude-code-bridge
- 默认分支 / Default branch: `main`
- 主要语言 / Primary language: `JavaScript`
- 可见性 / Visibility: `public`
- 仓库类型 / Repository type: `source`

## 本地运行 / Local Run

```bash
git clone https://github.com/siuserxiaowei/feishu-claude-code-bridge.git
cd feishu-claude-code-bridge
npm install
npm run dev
npm run start
```

## 仓库结构 / Repository Map

| 路径 / Path | 中文说明 | English |
| --- | --- | --- |
| `README.md` | 项目入口说明，先读这里。 | Main project entry point and orientation. |
| `package.json` | Node/前端项目配置、依赖和脚本。 | Node/frontend dependencies and scripts. |
| `.gitignore` | 项目文件或目录。 | Project file or directory. |
| `bridge.mjs` | 项目文件或目录。 | Project file or directory. |
| `package-lock.json` | npm 依赖锁定文件。 | npm dependency lockfile. |
| `飞书接入ClaudeCode全过程.md` | 项目文件或目录。 | Project file or directory. |

## 维护备注 / Maintenance Notes

- 中文：当项目目标、在线入口、运行命令或目录结构变化时，同步更新本说明。
- English: Keep this guide updated when the project purpose, live link, run commands, or structure changes.
- 中文：修改代码、数据或生成页面后，优先运行相关构建、测试或校验命令。
- English: After changing code, data, or generated pages, run the relevant build, test, or validation command.

## 安全与隐私 / Safety & Privacy

- 中文：不要提交 API key、token、密码、cookie、私有链接或内部账号资料。
- English: Do not commit API keys, tokens, passwords, cookies, private URLs, or internal account data.
- 中文：公开 GitHub Pages 前，确认资料已脱敏并允许公开。
- English: Before publishing GitHub Pages output, confirm the material is redacted and cleared for public release.
<!-- SIUSER-REPO-GUIDE:END -->



<!-- SIUSER-SEO-INTRO:START -->

## 项目介绍 / Project Introduction

**中文介绍**：飞书与 Claude Code 的协作桥接项目，把团队消息、文档和 AI 编程工作流连接起来。

**English**: A Feishu and Claude Code bridge that connects team messages, documents, and AI coding workflows.

**SEO 关键词 / SEO Keywords**: Feishu, Claude Code, AI coding, team workflow, 飞书自动化

<!-- SIUSER-SEO-INTRO:END -->

在手机飞书上远程操控你电脑上的 Claude Code。不是简单的 AI 对话，是完整的 Claude Code 体验——能读写文件、跑命令、改代码。

```
手机飞书 → 飞书云端 ←WebSocket→ bridge.mjs (你的电脑) → Claude Agent SDK → Claude Code
```

## 为什么做这个

起因是 [Claude-to-IM-skill](https://github.com/op7418/Claude-to-IM-skill)（1800+ Star），一个支持 5 个 IM 平台桥接 Claude Code 的项目。但实际使用时发现它的核心依赖库 `claude-to-im`（含 `src/lib/bridge/`）未发布到 npm，`npm run build` 会报错，无法直接运行。

于是我从零写了这个轻量版，**只用两个 SDK、一个文件**就实现了完整的飞书桥接。

## 和 Claude-to-IM-skill 的对比

| | Claude-to-IM-skill | 本项目 |
|---|---|---|
| 支持平台 | Telegram/Discord/飞书/QQ/微信 | 飞书 |
| 核心文件 | 10+ 个 TypeScript 模块 | 1 个 bridge.mjs（200行） |
| 构建步骤 | 需要 `npm run build`（esbuild 编译） | 无需构建，直接 `node bridge.mjs` |
| 依赖 | claude-to-im 核心库（未发布，build 会失败） | 仅 2 个 npm 包 |
| AI 后端 | Claude Agent SDK / Codex SDK | Claude Agent SDK |
| 消息连接 | WebSocket 长连接 | WebSocket 长连接（相同） |
| 会话管理 | 持久化到文件 | 内存 Map（重启清空） |
| daemon 管理 | launchd/setsid/WinSW | 手动启动 |

简单说：Claude-to-IM-skill 是一个功能完整的多平台框架，但目前有构建依赖问题。本项目是一个专注飞书的轻量方案，开箱即用。

## 快速开始

### 1. 创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app) → 创建自建应用 → 添加「机器人」能力
2. 权限管理 → 添加权限：
   - `im:message`
   - `im:message.group_at_msg`
   - `im:message.p2p_msg`
3. 事件与回调 → 添加事件：`im.message.receive_v1`
4. 订阅方式选「使用长连接接收事件」
5. 版本管理 → 创建版本 → 申请发布 → 管理员审批

### 2. 安装 & 启动

```bash
git clone https://github.com/siuserxiaowei/feishu-claude-code-bridge.git
cd feishu-claude-code-bridge
npm install

FEISHU_APP_ID=你的AppID \
FEISHU_APP_SECRET=你的AppSecret \
AUTO_APPROVE=true \
node bridge.mjs
```

看到这个输出就说明成功了：

```
🚀 Feishu-Claude Bridge
   App ID:       cli_xxxxx
   Work Dir:     /your/project/path
   Auto Approve: true
✅ WebSocket connected, listening...
```

然后去飞书私聊你的机器人，发条消息试试。

### 3. 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `FEISHU_APP_ID` | 是 | — | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 是 | — | 飞书应用 App Secret |
| `WORKDIR` | 否 | 当前目录 | Claude Code 工作目录 |
| `AUTO_APPROVE` | 否 | `false` | 设为 `true` 跳过所有权限确认 |

## 实现原理

### 飞书侧：WebSocket 长连接

使用飞书官方 `@larksuiteoapi/node-sdk` 的 WSClient，通过出站 WebSocket 连接飞书云端。**不需要公网 IP、不需要域名、不需要 ngrok**。你的电脑能上网就行。

```js
const wsClient = new lark.WSClient({ appId, appSecret });
await wsClient.start({ eventDispatcher });
```

> 注意：新版 SDK 的 `start()` 需要传 `{ eventDispatcher }` 参数，旧版是在构造函数传。

### Claude 侧：Agent SDK

使用 `@anthropic-ai/claude-agent-sdk` 的 `query()` 函数。这不是简单的 API 调用——它会启动一个完整的 Claude Code 子进程，拥有和你终端里一样的能力：

- 读写文件（Read/Write/Edit）
- 执行命令（Bash）
- 搜索代码（Grep/Glob）
- 多轮对话上下文

```js
const q = query({
  prompt: userText,
  options: {
    cwd: WORKDIR,
    permissionMode: 'bypassPermissions',
    thinking: { type: 'adaptive' },
  }
});

for await (const msg of q) {
  if (msg.type === 'result' && msg.subtype === 'success') {
    // msg.result 就是 Claude Code 的最终回复
  }
}
```

### 消息流程

```
1. 用户在飞书发消息
2. 飞书云端通过 WebSocket 推送到 bridge.mjs
3. bridge.mjs 提取文本，过滤重复消息
4. 如果是群聊，检查是否 @了机器人
5. 调用 Claude Agent SDK 启动 Claude Code 会话
6. 等待 Claude Code 返回结果
7. 将结果通过飞书 API 回复给用户
```

### 额外功能

- **消息去重**：60 秒窗口内同一消息 ID 只处理一次
- **并发控制**：同一个聊天同时只处理一条消息，避免冲突
- **思考提示**：超过 2 秒未回复自动发送「💭 思考中...」
- **长消息分片**：超过 3800 字符自动按换行符拆分发送
- **群聊过滤**：仅在 @机器人、问号结尾、包含请求动词时回复

## 踩坑记录

1. **Claude-to-IM-skill build 失败**：`package.json` 里 `"claude-to-im": "file:../Claude-to-IM"` 指向的核心库缺少 `src/lib/bridge/` 目录，esbuild 编译报 5 个 resolve 错误。`npx skills add` 安装也一样。
2. **飞书 WSClient API 变更**：`eventDispatcher` 从构造函数参数改到了 `start()` 方法参数，报 `Cannot destructure property 'eventDispatcher' of 'params' as it is undefined`。
3. **飞书权限两阶段审批**：添加权限后必须创建新版本并审批通过才生效。

## 致谢

- [Claude-to-IM-skill](https://github.com/op7418/Claude-to-IM-skill) — 架构思路来源，支持 5 个 IM 平台的完整方案
- [khazix-skills](https://github.com/KKKKhazix/khazix-skills) — 卡兹克老师的写作 skill
- [alive-writer-skill](https://github.com/siuserxiaowei/alive-writer-skill) — 活人感写作 skill

## License

MIT

<!-- SIUSER-CONTACT:START -->

## 联系我 / Contact

想交流 AI 工具、内容自动化、SEO、私域增长或项目合作，可以扫码加我微信。

For collaboration on AI tools, content automation, SEO, private-domain growth, or product experiments, scan the WeChat QR code below.

<img src="https://raw.githubusercontent.com/siuserxiaowei/siuserxiaowei/main/assets/contact/wechat-qrcode.jpg" width="180" alt="WeChat QR code / 微信二维码" />

**关键词 / Keywords**: Feishu, Claude Code, AI coding, team workflow, AI tools, AI automation, GitHub Pages, SEO

<!-- SIUSER-CONTACT:END -->
