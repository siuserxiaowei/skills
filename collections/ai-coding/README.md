# AI Coding Knowledge Framework

<!-- SIUSER-REPO-GUIDE:START -->
## 项目介绍 / Project Introduction

### 中文
AI 编程知识框架：把 agentic coding、软件工程纪律和提示词工程整理成系统化学习框架。

### English
AI coding knowledge framework for agentic coding, software engineering discipline, and prompt engineering.

## 使用方式 / Usage

### 中文
1. 优先打开在线入口或本地静态服务查看最终页面。
2. 内容型仓库通常从 `README.md`、`docs/`、`data/` 或 `content/` 开始阅读。
3. 更新资料后，重新生成或刷新静态页面，并检查链接、图片和文字是否正常。

### English
1. Start with the live link or a local static server to view the final page.
2. For content repositories, begin with `README.md`, `docs/`, `data/`, or `content/`.
3. After updating material, regenerate or refresh the static page and check links, images, and copy.

## 入口与元信息 / Entry Points & Metadata

- GitHub 仓库 / Repository: https://github.com/siuserxiaowei/ai-coding-knowledge-framework
- Live / 在线入口：https://siuserxiaowei.github.io/ai-coding-knowledge-framework/
- 默认分支 / Default branch: `main`
- 主要语言 / Primary language: `HTML`
- 可见性 / Visibility: `public`
- 仓库类型 / Repository type: `source`

## 本地运行 / Local Run

```bash
git clone https://github.com/siuserxiaowei/ai-coding-knowledge-framework.git
cd ai-coding-knowledge-framework
python3 -m http.server 8000
```

## 仓库结构 / Repository Map

| 路径 / Path | 中文说明 | English |
| --- | --- | --- |
| `README.md` | 项目入口说明，先读这里。 | Main project entry point and orientation. |
| `index.html` | 静态站首页或页面入口。 | Static-site homepage or entry page. |
| `assets` | 图片、样式、数据等资源。 | Images, styles, data, and other assets. |
| `scripts` | 构建、同步、生成或维护脚本。 | Build, sync, generation, or maintenance scripts. |
| `.nojekyll` | 项目文件或目录。 | Project file or directory. |
| `blueprint.html` | 项目文件或目录。 | Project file or directory. |
| `magazine.html` | 项目文件或目录。 | Project file or directory. |
| `research.html` | 项目文件或目录。 | Project file or directory. |

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

**中文介绍**：AI 编程知识框架页面，把工程纪律、上下文管理、验证、协作和工具链原则整理成可分享的网页版本。

**English**: A shareable AI coding knowledge framework covering engineering discipline, context management, verification, collaboration, and toolchain principles.

**SEO 关键词 / SEO Keywords**: AI coding, agentic coding, software engineering, prompt engineering, AI 编程, 工程纪律

<!-- SIUSER-SEO-INTRO:END -->

Static GitHub Pages version of the AI engineering discipline knowledge framework.

## V2 Pages

- `index.html`: version selector and compact 16-source ledger.
- `research.html`: recommended research archive layout.
- `magazine.html`: editorial long-scroll layout.
- `blueprint.html`: engineering blueprint console layout.
- `assets/v2.css`: shared visual system.
- `scripts/build-v2-pages.mjs`: source-of-truth generator for all four pages.

## Validation

- `npx --yes html-validate index.html research.html magazine.html blueprint.html`
- Each page includes 16 source links with `target="_blank"` and `rel="noopener noreferrer"`.
- The generated pages do not include tracking scripts.

<!-- SIUSER-CONTACT:START -->

## 联系我 / Contact

想交流 AI 工具、内容自动化、SEO、私域增长或项目合作，可以扫码加我微信。

For collaboration on AI tools, content automation, SEO, private-domain growth, or product experiments, scan the WeChat QR code below.

<img src="https://raw.githubusercontent.com/siuserxiaowei/siuserxiaowei/main/assets/contact/wechat-qrcode.jpg" width="180" alt="WeChat QR code / 微信二维码" />

**关键词 / Keywords**: AI coding, agentic coding, software engineering, prompt engineering, AI tools, AI automation, GitHub Pages, SEO

<!-- SIUSER-CONTACT:END -->
