# Siuser Agent Network Workbench

<!-- SIUSER-REPO-GUIDE:START -->
## 项目介绍 / Project Introduction

### 中文
Agent 网络工作台：实验多 Agent 协作、知识系统和自动化工作流。

### English
Agent network workbench for experimenting with multi-agent collaboration, knowledge systems, and automation workflows.

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

- GitHub 仓库 / Repository: https://github.com/siuserxiaowei/siuser-agent-network-workbench
- Live / 在线入口：https://siuserxiaowei.github.io/siuser-agent-network-workbench/
- 默认分支 / Default branch: `main`
- 主要语言 / Primary language: `Python`
- 可见性 / Visibility: `public`
- 仓库类型 / Repository type: `source`

## 本地运行 / Local Run

```bash
git clone https://github.com/siuserxiaowei/siuser-agent-network-workbench.git
cd siuser-agent-network-workbench
npm install
```

## 仓库结构 / Repository Map

| 路径 / Path | 中文说明 | English |
| --- | --- | --- |
| `README.md` | 项目入口说明，先读这里。 | Main project entry point and orientation. |
| `package.json` | Node/前端项目配置、依赖和脚本。 | Node/frontend dependencies and scripts. |
| `docs` | 文档或 GitHub Pages 输出目录。 | Documentation or GitHub Pages output. |
| `scripts` | 构建、同步、生成或维护脚本。 | Build, sync, generation, or maintenance scripts. |
| `config` | 项目文件或目录。 | Project file or directory. |
| `.env.example` | 项目文件或目录。 | Project file or directory. |
| `.gitignore` | 项目文件或目录。 | Project file or directory. |
| `CHANGELOG.md` | 项目文件或目录。 | Project file or directory. |
| `package-lock.json` | npm 依赖锁定文件。 | npm dependency lockfile. |
| `SECURITY.md` | 项目文件或目录。 | Project file or directory. |

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

**中文介绍**：Agent 网络工作台实验，探索多 Agent 协作、知识组织、任务编排和个人 AI 工作流。

**English**: An agent-network workbench for experimenting with multi-agent collaboration, knowledge organization, task orchestration, and personal AI workflows.

**SEO 关键词 / SEO Keywords**: AI agents, multi-agent, agent workflow, knowledge system, 任务编排

<!-- SIUSER-SEO-INTRO:END -->

> Version: `0.2.2`

一句话：这是一个只跑在你本机的多 Agent 调度台，用来把“素材收集、日报生成、公众号写作、Skill 维护、发布前检查”拆成可派活、可追踪、可复盘的任务流。

它不是 Obsidian 插件，也不是公开 SaaS。你可以把它理解成一个本地项目经理：

1. 把任务写成统一格式。
2. 交给不同角色的 Agent。
3. 把产物落到指定 Obsidian 目录。
4. 关键动作仍然由你人工确认。

这是给个人本地工作流准备的 `agent-network` 调度台。第一期只做内部提效：Obsidian 日报、公众号生产、Skill 工厂。

## 它具体能做什么

| 场景 | 输入 | 参与角色 | 输出 |
| --- | --- | --- | --- |
| Obsidian 日报 | 微信/Obsidian Markdown、本地日报管线 | `inbox-agent`、`digest-agent`、`review-agent`、`qa-agent` | 本地日报草稿、公开前检查 |
| 公众号生产 | 文章素材、项目更新、参考资料 | `inbox-agent`、`writer-agent`、`review-agent`、`qa-agent` | 标题、结构、初稿、配图提示词、发布清单 |
| Skill 工厂 | `.agents/skills/`、安全扫描 Skill、视觉 Skill | `skill-agent`、`qa-agent`、`writer-agent`、`review-agent` | README/SKILL 检查、风险提示、维护报告 |

Dashboard 里看到的 `Tasks / Mesh / Messages` 分别对应：

- `Tasks`：任务有没有派出去、谁处理、状态如何。
- `Mesh`：本机有哪些 Agent 节点。
- `Messages`：Agent 之间的任务消息。

## Dashboard 中英文对照

agent-network 自带 Dashboard 的菜单还是英文，但工作台生成的任务内容会尽量使用中英文对照。常见词先这样看：

| 英文 | 中文 | 你应该怎么理解 |
| --- | --- | --- |
| `Tasks` | 任务 | 看任务有没有投递出去，以及现在是什么状态 |
| `Mesh` | 节点网络 | 看本机有哪些 Agent 角色节点 |
| `Messages` | 消息 | 看 Agent 之间传了什么任务消息 |
| `queued` | 排队中 | 任务已创建，还没处理 |
| `running` | 运行中 | 任务正在处理 |
| `review_needed` | 需要人工审阅 | 产物已经生成，但要你看一眼 |
| `delivered` | 已投递 | 消息已经送到目标 Agent |
| `expired` | 已过期 | 任务消息太久没人处理，过期了 |
| `from` | 来源 Agent | 谁发起了任务 |
| `to` | 目标 Agent | 任务派给谁 |

真正有用的不是页面炫，而是它把你平时散落在 Codex、Obsidian、GitHub、微信素材里的工作，整理成一条条可交接的本地流水线。

## 在线说明页

GitHub Pages 页面：

```text
https://siuserxiaowei.github.io/siuser-agent-network-workbench/
```

## 边界

- Hub 只允许绑定 `127.0.0.1`，不要暴露到公网。
- 不把工作目录设成 `$HOME`。
- 不自动删除、不自动 push、不自动发布。
- Obsidian 写入只允许这几个目录：
  - `~/Documents/Obsidian Vault/90_Agent/`
  - `~/Documents/Obsidian Vault/微信渠道/_daily/`
  - `~/Documents/Obsidian Vault/03.公众号/`
- 默认只生成草稿、检查报告和任务记录；主 vault 笔记、发布仓库和 Skill 实际代码改动都需要单独确认。

## 安装

```bash
cd "agent-network-workbench"
npm install
npm run doctor
npm run init
```

`npm run init` 会在 Obsidian vault 的 `90_Agent/` 下创建任务、草稿、检查报告和测试目录，并写入一篇烟测笔记。

注意：当前 `agent-network` CLI 在带空格路径下会把路径编码成 `New%20project%203`，所以安装脚本会把实际 CLI 运行时放在无空格路径：

```text
~/Workspace/agent-network-runtime
```

工作台配置、脚本和文档仍保留在当前项目目录。

## 启动本地服务

如果你第一次打开 Dashboard 完全不知道怎么用，先跑这个一键演示。它会启动本地服务、创建一条公众号任务、生成一份 Obsidian 草稿，并向 Dashboard 投递一条可见任务：

```bash
cd "agent-network-workbench"
npm run demo:article
```

跑完后看三个地方：

- Dashboard：`http://127.0.0.1:3000`，看 `Tasks / 任务` 里最新的 `delivered / 已投递` 任务。
- 任务 JSON：`~/Documents/Obsidian Vault/90_Agent/tasks/`
- 生成草稿：`~/Documents/Obsidian Vault/03.公众号/_agent_drafts/`

推荐用这个命令。它会在后台同时启动 Hub 和 Dashboard，并在启动后返回终端：

```bash
cd "agent-network-workbench"
npm run start:local
```

停止：

```bash
cd "agent-network-workbench"
npm run stop:local
```

地址：

```text
Hub:       http://127.0.0.1:9200
Dashboard: http://127.0.0.1:3000
```

## 手动启动 Hub

```bash
cd "agent-network-workbench"
npm run hub
```

首次启动后，另开一个终端立刻修改默认密码：

```bash
cd "agent-network-workbench"
npm run passwd
```

然后登录并创建固定角色节点：

```bash
cd "agent-network-workbench"
npm run login
npm run nodes:create
```

节点配置会落在 `.anet/nodes/`，里面有本机 node token，已被 `.gitignore` 排除。`nodes:create` 会自动运行 `nodes:harden`，把 `dangerouslySkipPermissions` 改成 `false`。

Dashboard：

```bash
cd "agent-network-workbench"
npm run dashboard
```

`npm run dashboard` 会占住当前终端；日常使用更推荐 `npm run start:local`。

## 固定角色

- `inbox-agent`：收件箱 Agent / Inbox Agent。收集 Obsidian、微信日报、文章素材、GitHub 项目状态。
- `digest-agent`：摘要 Agent / Digest Agent。生成每日学习卡片、群日报摘要、专题沉淀。
- `writer-agent`：写作 Agent / Writer Agent。把素材转公众号、X 长文、小红书草稿。
- `review-agent`：审校 Agent / Review Agent。事实核查、去 AI 味、标题优化、发布前检查。
- `skill-agent`：Skill 维护 Agent / Skill Agent。维护安全扫描、视觉审美实验室、微信文章读取等 Skill。
- `qa-agent`：验收 Agent / QA Agent。跑本地脚本、README 检查、安全扫描、发布前验收。

角色定义在 `config/roles.json`，流水线定义在 `config/pipelines.json`。

## 本地试点命令

这些命令不需要 Hub，适合先验证本地目录和任务格式。

```bash
npm run task:daily
npm run pilot:daily

npm run task:article
npm run pilot:article

npm run task:skill
npm run pilot:skill
```

一次性烟测：

```bash
npm run smoke
```

验证 `send_task` 任务投递链路：

```bash
npm run smoke:send-task
```

这个烟测使用 `inbox-agent` 的 node token 给 `digest-agent` 投递一条任务，并通过 `anet tasks` 确认状态。它不启动真实 Codex Agent，不调用模型。完整“Agent 收到任务并回复”的验收，需要先确认 `npm run passwd` 已改默认密码，再运行 `anet upgrade` 安装 `agent-node`，然后手动启动对应节点。

## 产物位置

- 任务 JSON：`~/Documents/Obsidian Vault/90_Agent/tasks/`
- 日报草稿：`~/Documents/Obsidian Vault/微信渠道/_daily/`
- 公众号草稿/检查：`~/Documents/Obsidian Vault/03.公众号/_agent_drafts/`
- Skill 检查：`~/Documents/Obsidian Vault/90_Agent/skill-reports/`
- QA 报告：`~/Documents/Obsidian Vault/90_Agent/qa/`

<!-- SIUSER-CONTACT:START -->

## 联系我 / Contact

想交流 AI 工具、内容自动化、SEO、私域增长或项目合作，可以扫码加我微信。

For collaboration on AI tools, content automation, SEO, private-domain growth, or product experiments, scan the WeChat QR code below.

<img src="https://raw.githubusercontent.com/siuserxiaowei/siuserxiaowei/main/assets/contact/wechat-qrcode.jpg" width="180" alt="WeChat QR code / 微信二维码" />

**关键词 / Keywords**: AI agents, multi-agent, agent workflow, knowledge system, AI tools, AI automation, GitHub Pages, SEO

<!-- SIUSER-CONTACT:END -->
