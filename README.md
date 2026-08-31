# Goal Compiler｜需求编译器

[![Validate Xiaowei Goal](https://github.com/siuserxiaowei/xiaowei-goal/actions/workflows/validate.yml/badge.svg)](https://github.com/siuserxiaowei/xiaowei-goal/actions/workflows/validate.yml)
![Version](https://img.shields.io/badge/version-0.12.0-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<!-- SIUSER-REPO-GUIDE:START -->
## 项目介绍 / Project Introduction

### 中文
Research-first Agent Skill 与可执行需求编译器：把模糊任务收束成机器可读、人工审核、有反证和终止门槛的 /goal。

### English
Agent Skill and executable compiler for turning vague intent into measurable, evidence-gated, human-reviewed goals with a first safe output.

## 使用方式 / Usage

### 中文
1. 先阅读 `SKILL.md`，确认触发场景、输入要求和执行步骤。
2. 按仓库 README 的安装方式复制或安装 Skill。
3. 在真实任务中调用前，先用示例或测试脚本做一次小范围验证。

### English
1. Read `SKILL.md` first to understand triggers, inputs, and workflow steps.
2. Install or copy the skill according to this README.
3. Before using it on real work, run a small example or validation script.

## 入口与元信息 / Entry Points & Metadata

- GitHub 仓库 / Repository: https://github.com/siuserxiaowei/xiaowei-goal
- Live / 在线入口：https://siuserxiaowei.github.io/xiaowei-goal/
- 默认分支 / Default branch: `main`
- 主要语言 / Primary language: `Python`
- 可见性 / Visibility: `public`
- 仓库类型 / Repository type: `source`
- Topics: `agent-reach`, `agent-research`, `agent-skill`, `codex`, `goal`, `goal-compiler`, `human-in-the-loop`, `browser-use`, `claude-for-chrome`, `competitor-analysis`, `deep-research`, `growth`, `prompt-engineering`, `research-agent`, `requirements-engineering`, `scrapling`, `seo`, `web-research`

## 本地运行 / Local Run

```bash
git clone https://github.com/siuserxiaowei/xiaowei-goal.git
cd xiaowei-goal
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
open /tmp/goal-compiler-demo/walkthrough.html
```

## 仓库结构 / Repository Map

| 路径 / Path | 中文说明 | English |
| --- | --- | --- |
| `README.md` | 项目入口说明，先读这里。 | Main project entry point and orientation. |
| `SKILL.md` | Skill 的核心说明、触发条件和执行步骤。 | Core skill instructions, trigger rules, and workflow. |
| `docs` | 文档或 GitHub Pages 输出目录。 | Documentation or GitHub Pages output. |
| `scripts` | 构建、同步、生成或维护脚本。 | Build, sync, generation, or maintenance scripts. |
| `examples` | 示例输入、用法或 fixture。 | Examples, usage samples, or fixtures. |
| `tests` | 测试用例与验证脚本。 | Tests and validation scripts. |
| `.github` | GitHub Actions 和协作自动化配置。 | GitHub Actions and collaboration automation. |
| `LICENSE` | 许可证文件。 | License file. |
| `agents` | Agent 配置或平台适配文件。 | Agent configuration or platform adapters. |
| `references` | 参考资料、规范或补充说明。 | References, specifications, or supporting notes. |
| `.gitignore` | 项目文件或目录。 | Project file or directory. |
| `manifest.json` | 项目文件或目录。 | Project file or directory. |

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



`Goal Compiler｜需求编译器` 是 `xiaowei-goal` v0.12.0 的可执行产品形态：一个面向 App、网站、落地页、SaaS、SEO、增长和竞品分析的 Agent Skill，加上确定性 CLI 门禁。

它的核心目标不是让 agent 立刻动手写代码，也不是把 Prompt 润色得更长，而是把模糊需求编译为：

- Smart Router：任务类型、成熟度、风险、外部信息需求。
- Strategy Gate：问题重构、最小验证、可测量成功指标、反证、终止条件。
- Tool / Evidence Gate：什么证据允许什么结论，什么操作必须暂停。
- Human Sign-off：人工把“好看”这类主观词改成可验收门槛后，CLI 才允许执行。
- First Real Output：不停在方案，真正生成第一个 HTML 产物和检查报告。

一句话：

> 先把想要的结果编译成会失败、能反证、知道何时停止的契约，再动手。

## 70 秒可复现 Demo

一条命令生成固定证据链：Router JSON、主观指标 `FAIL`、人工 metric patch、严格 `PASS`、真实静态页和 execution report。

```bash
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
open /tmp/goal-compiler-demo/walkthrough.html
```

固定输入：

```text
给我做个 AI 网站，越快越好
```

证据链：

```text
模糊需求
  → Smart Router + Strategy Gate JSON
  → 成功指标“好看”被 validator 拒绝
  → 人工改为 60 分钟 / 1 页 / 1 CTA / 假设标记
  → 严格校验 PASS
  → first-output/index.html + execution-report.json
```

已冻结的比赛 Demo 位于 `contest/demo-output/`；在线演示页位于 [GitHub Pages](https://siuserxiaowei.github.io/xiaowei-goal/)。

### 四个 CLI 状态

```bash
python3 scripts/goal_compiler.py compile --request-file contest/demo-fixtures/request.txt --output /tmp/goal-draft
python3 scripts/goal_compiler.py apply-review /tmp/goal-draft/goal-contract.json --review contest/demo-fixtures/human-review.json --output /tmp/goal-reviewed.json
python3 scripts/goal_compiler.py validate /tmp/goal-reviewed.json
python3 scripts/goal_compiler.py execute /tmp/goal-reviewed.json --output /tmp/goal-first-output
```

`execute` 对未审批契约直接返回非零退出码，且不会创建输出目录。

如果当前环境安装了 [Agent Reach](https://github.com/Panniantong/Agent-Reach)，`xiaowei-goal` 会把它作为广域调研的首选能力层，用来路由 X、Reddit、YouTube、GitHub、小红书、抖音、B站、微信公众号、V2EX、RSS、Exa 搜索等公开或用户授权来源。

当前版本还会把研究型任务强制补上判断层和质量约束：

- `Smart Router`：先判断任务类型、成熟度、外部信息需求、风险和输出长度，再决定要不要三阶段研究。
- `Goal Compiler`：生成前先暴露默认假设、选择理由和工具取舍，避免死板套模板。
- `Executable Contract`：把路由、策略、指标、反证、终止条件、工具/证据门槛和第一步固化为 JSON。
- `Human Review Gate`：未完成人工指标修订与签字时，不允许执行。
- `First-step Executor`：严格校验通过后才生成第一个安全产物和机器检查报告。
- `Strategy Gate`：先重构真实问题，定义最小验证、成功指标、反证信号和终止/暂缓条件，避免把每个想法都写成大工程。
- `小伟偏好`：默认把研究落到页面、功能、内容、增长和实现目标，优先小闭环、工具站、AI 产品、SEO 和出海方向。
- `商业优先级`：如果价值低、证据弱或成本高，会建议先小实验、暂缓或不建议做。
- `输出压缩`：按短版、标准版、完整版控制输出长度，不默认长篇模板。
- `领域包`：支持 AI 工具站、Chrome 插件、出海 SaaS、小红书/抖音内容验证、GitHub 开源项目增长。
- `自我进化`：用户显式触发后，可自动收集反馈、修改允许路径、运行校验、推送、等 CI、发 release。
- `每日进化`：GitHub Actions 每天 09:00 Asia/Shanghai 自动跑审计，必要时创建 issue 交接给 agent。
- `Release 一致性`：每日审计检查 `manifest.json` 版本、git tag 和 GitHub release 是否对齐。
- `目标评估`：用 `scripts/evaluate_goal_output.py` 给示例和生成目标做完整性、比例和业务应用检查。
- `工具栈`：按任务选择 Agent Reach、普通网页读取、Scrapling、browser-use、Claude for Chrome。
- `任务包`：把 App、网站/落地页、SEO、竞品分析、增长实验映射到具体产物。
- `质量门槛`：每条关键结论至少 2 个独立来源支撑；标明来源强弱；过期、营销软文、不可访问来源降权；矛盾信息必须列出。

## 先确认本地是新版

如果你之前安装过这个 skill，GitHub 仓库更新后，本地已安装副本不一定会自动刷新。遇到当前 agent 不提 `工具栈`、`任务包`、`质量门槛` 或 `agent-reach doctor` 时，先更新本地 skill：

```bash
npx skills add siuserxiaowei/xiaowei-goal
```

安装后自检：

```bash
python3 ~/.agents/skills/xiaowei-goal/scripts/check_installed_skill.py
```

## 适合什么场景

适合：

- 我要做一个 App，先研究竞品和用户评价
- 我要做一个网站或落地页，先看同行页面、文案和转化路径
- 我要做 SaaS、Chrome 插件、工具站，先找产品机会和技术参考
- 我要做 SEO、增长、内容选题，先研究搜索结果和用户语言
- 我要让 agent 用 Agent Reach 或其他联网工具搜资料，再应用到我的业务
- 我要把一句模糊需求改成可执行、可验证、知道什么时候停止的 `/goal`
- 我要让这个 skill 根据反馈自动进化、自动测试、自动发布新版
- 我要让它每天自动检查一次是否需要进化

不适合：

- 一句话翻译
- 简单改写
- 不需要联网、不需要持续执行的小任务
- 已经有清晰步骤、只需要马上跑一个命令的任务

## 安装

从 GitHub 安装或更新：

```bash
npx skills add siuserxiaowei/xiaowei-goal
```

GitHub 仓库更新后，本地已经安装过的 skill 不一定会自动同步。只要怀疑当前 agent 读到的是旧版，就重新运行上面的安装命令，然后开启新会话或重启当前 agent 环境。

只查看仓库里有哪些 skill：

```bash
npx skills add siuserxiaowei/xiaowei-goal --list
```

安装后可以检查：

```bash
test -f ~/.agents/skills/xiaowei-goal/SKILL.md
```

也可以检查当前本地安装版是否包含新版能力：

```bash
python3 ~/.agents/skills/xiaowei-goal/scripts/check_installed_skill.py
```

如果你只是临时排查，也可以用文本搜索确认：

```bash
rg -n "Tool Stack Routing|Quality Gate|Task Packs" ~/.agents/skills/xiaowei-goal
```

如果你的运行环境使用其他 skills 路径，请以对应客户端的安装位置为准。

## 怎么使用

直接对 agent 说：

```text
用 xiaowei-goal 帮我写一个 goal：
我要做一个 AI 英语口语练习 App，先联网研究竞品、用户评价、小红书/B站/YouTube/公众号内容，再把结论应用到 MVP 功能和官网页面。
```

或者：

```text
用 xiaowei-goal：
我要改一个 AI 工具官网，先研究同行首页、定价页、SEO 内容和用户痛点，再给我一个可以执行的改版 goal。
```

它会优先输出一段可以复制的三阶段 `/goal`，例如：

```text
决策摘要：任务类型=app；成熟度=模糊想法；外部信息需求=标准；风险等级=中；输出长度=标准版；是否先提问=否
默认假设：目标用户是想提升英语口语的中文用户，当前还没有明确竞品池和 MVP 范围；先用公开资料建立方向，不使用账号、Cookie 或付费数据。
偏好应用：优先把调研落到页面、功能、内容、增长和下一阶段实现目标；保持小闭环，不做大而全教育市场战略。
反馈调整：未提供上次执行反馈，本次不做反馈修正；如果执行后发现范围过大，下次应收紧渠道和输出长度。
策略判断：问题重构=不是先做完整 AI 口语教育平台，而是验证用户是否愿意完成一个低摩擦口语练习闭环；最小验证=竞品/用户痛点研究后落到一个免费练习入口、一个核心练习流程和一个官网首屏承诺；成功指标=能得到来源支撑的 MVP 范围、明确首访 CTA 和下一阶段可实现 goal；反证信号=用户痛点主要集中在真人反馈、课程体系或考试结果承诺，当前 AI 小工具难以提供可信差异；终止/暂缓条件=如果 2 个以上强来源无法支撑核心练习闭环或信任路径，暂缓完整 App 实现。
优先级判断：业务价值=中高；证据强度=中；执行成本=中；分发潜力=中高；变现路径=订阅、会员或练习包；风险=口语效果和教育承诺难验证；建议=继续做标准研究，但先形成可验证 MVP 小闭环。
输出长度：标准版；给出可直接执行的完整 goal，但不展开成长报告。
选择理由：这是新 App 方向，真实用户评价和竞品结构会显著影响 MVP，所以选择标准三阶段研究；不选深度模式是因为当前目标仍是形成可执行起点，不是做融资级市场判断。
/goal 围绕 AI 英语口语练习 App 执行三阶段研究工作流：先广域联网调研，再进行 Deep Research，最后把所有有效资料应用到当前业务，形成 MVP 功能、官网页面、增长动作和下一阶段实现目标。
任务包：App MVP 研究包；本次必须把研究结论映射到目标用户、首访体验、核心工作流、激活时刻、留存循环、MVP 功能、定价假设、信任风险和下一阶段实现 `/goal`。
领域包：AI 工具站包；把研究优先落到低成本首访体验、免费练习入口、核心功能闭环、内容获客和可验证留存指标。
工具栈：优先 Agent Reach 做平台搜索和来源收集；普通公开网页先用 web reader/browser；需要结构化抽取或公共网页爬取时使用 Scrapling；需要点击、截图、登录授权流程或动态 UI 验证时使用 browser-use；Claude for Chrome 仅作为用户明确授权的 Chrome 内协作/人工接管选项。
阶段 1 - 广域调研：优先使用 Agent Reach；开始前运行 `agent-reach doctor` 或确认可用渠道，若不可用则使用当前环境可用的搜索、浏览、GitHub、RSS 或平台读取工具；检索 15-25 个候选来源，覆盖直接竞品、官方资料、App 用户评价或社区讨论、小红书/B站/YouTube/公众号等内容平台、技术或实现参考；记录标题、URL、来源类型、工具/渠道、检索日期、访问限制和初步价值判断。
阶段 2 - Deep Research：从第一阶段来源池中筛选高价值来源进行深读、对比和交叉验证；提取关键事实、用户痛点、竞品策略、页面/产品结构、增长路径、技术做法、风险和证据强度；每条关键结论至少用 2 个独立来源支撑，否则标成低置信度或假设；把矛盾信息标成不确定。
阶段 3 - 业务应用：把本轮收集到、去重后、与 AI 英语口语练习 App 相关且可追溯来源的资料，映射到 MVP 功能、官网页面、文案方向、SEO 主题、增长动作、技术实现、验证实验和下一阶段 `/goal`。
输出物：产出一份研究应用简报，包含来源池、深度研究证据表、业务应用表、可迁移动作、不能复制的内容、风险和下一阶段 `/goal`。
质量门槛：每条关键结论至少需要 2 个独立来源支撑；标明来源强弱；过期、营销软文、不可访问或片段来源必须降权；矛盾信息必须列出；不足 2 个来源的结论只能标为低置信度或假设。
验证方式：每条关键结论必须能追溯到来源；事实、推断、建议分开写；最终动作要能对应到产品、页面、文案、SEO、增长、技术实现或验证实验。
限制：不复制竞品品牌、文案、图片、视频、代码、课程、版权素材或未经证实的市场结论；不把单一来源当成事实；不把 Agent Reach 描述成无限制全网访问；不使用登录账号、Cookie、Token、付费平台、生产数据、私域内容或隐私数据，除非用户明确授权。
工作边界：三阶段研究期间只创建研究应用文档和下一阶段执行目标；实现阶段只改与 AI 英语口语练习 App、官网页面或直接相关测试有关的文件。
推进规则：先列研究问题和搜索词，再做广域检索，再筛选来源做 Deep Research，最后统一映射到业务动作；每个阶段结束前先补齐证据缺口，再进入下一阶段。
停止标准：研究应用简报覆盖三阶段，包含可追溯来源、深度研究证据、业务启发、可执行动作、风险和下一阶段目标。
暂停条件：需要 Cookie、Token、付费数据库、登录账号、绕过平台限制、法律或教育合规判断、版权授权、生产数据、私域内容或重大业务定位选择时暂停。
```

## 三档输出模式

当前版本会先做一次智能路由，再决定输出多长：

- `轻量模式`：明确的本地代码、文档、校验、维护任务，不做外部研究。
- `标准研究模式`：App、网站、SEO、增长、竞品等需要外部证据的常规任务。
- `深度研究模式`：高不确定性、高风险、重大业务决策、拥挤市场或用户明确要求深度研究的任务。

每个 goal 都应该先出现：

```text
决策摘要：任务类型=...；成熟度=...；外部信息需求=...；风险等级=...；输出长度=...；是否先提问=...
默认假设：...
偏好应用：...
反馈调整：...
策略判断：问题重构=...；最小验证=...；成功指标=...；反证信号=...；终止/暂缓条件=...
优先级判断：业务价值=...；证据强度=...；执行成本=...；分发潜力=...；变现路径=...；风险=...；建议=...
输出长度：短版 / 标准版 / 完整版
选择理由：...
```

### 1. 三阶段研究模式

这是默认的业务模式。适合 App、网站、SaaS、落地页、SEO、增长、竞品和产品方向。

它会要求 agent：

- 阶段 1：先做广域调研，建立来源池
- 阶段 2：再做 Deep Research，深读、对比、交叉验证高价值来源
- 阶段 3：最后做业务应用，把资料映射到产品、页面、文案、SEO、增长、技术实现和下一阶段 `/goal`
- 全程记录标题、URL、来源类型、工具/渠道、检索日期和访问限制
- 全程区分事实、推断、建议
- 不允许从搜索结果直接跳到建议，中间必须经过 Deep Research

默认广域调研来源数量：

- 轻量：6-8 个来源
- 标准：15-25 个来源
- 深度：40+ 个来源

Deep Research 不是多搜几个链接，而是从来源池里筛出高价值资料，做深读、对比、交叉验证和业务判断。

### 工具栈

研究型 goal 会按任务选择最小工具层：

- `Agent Reach`：平台搜索、社交/视频/社区/GitHub/RSS/播客/Exa 来源收集。
- `普通网页读取`：简单公开网页，优先使用 web reader、browser 或 Agent Reach 网页读取。
- `Scrapling`：公开网页结构化抽取、重复爬取、动态公开页面、抗页面结构变化的抽取逻辑。
- `browser-use`：点击、输入、筛选器、截图、页面状态、动态 UI 验证、用户明确授权的登录流程。
- `Claude for Chrome`：仅作为用户明确授权的 Chrome 内协作/人工接管选项，不作为默认后台爬虫。

如果这些工具涉及凭证、私域内容、验证码、付费、账号修改、表单提交、消息发送、购买或绕过平台限制，goal 必须暂停并要求用户确认。

### 任务包

研究型 goal 会选择一个主要任务包，让结果更接近可执行业务产物：

- `App MVP 研究包`：目标用户、首访体验、核心工作流、激活时刻、留存循环、MVP 功能、定价假设、信任风险。
- `网站/落地页改版包`：首屏表达、导航、页面模块顺序、CTA 路径、信任证明、异议处理、SEO 入口、转化实验。
- `SEO 内容集群包`：搜索意图、关键词/主题集群、SERP 竞品、页面类型、内链结构、优先页面 brief、转化路径。
- `竞品分析包`：竞品列表、定位、受众、定价、功能流程、获客渠道、用户抱怨、可借鉴结构、不可复制内容。
- `增长实验包`：目标人群、渠道、触发点、实验假设、hook、漏斗步骤、成功指标、护栏指标、优先级。

### 质量门槛

研究型 goal 会要求：

- 每条关键结论至少 2 个独立来源支撑。
- 不足 2 个来源时，只能标为 `低置信度` 或 `假设`。
- 来源强弱标成 `强`、`中`、`弱`。
- 过期、营销软文、不可访问、片段来源、重复来源必须降权或丢弃。
- 矛盾信息必须列出来，不允许被总结掉。

### 2. 直接执行模式

适合不需要外部信息的小范围任务，例如：

- 修一个明确 bug
- 给已有项目加一个小功能
- 改一段文档
- 跑一个本地检查

它会强调：

- 先读项目脚本和约定
- 只改相关文件
- 用命令、日志、截图或产物证明完成
- 遇到凭证、付费、生产数据、破坏性操作时暂停

### 3. 自我进化模式

当你说“让 xiaowei-goal 自己进化”或“完全自动化进化”时，它会生成或执行一个自我进化 `/goal`。

这个模式会自动做：

- 收集反馈来源：用户反馈、执行结果、示例、validator、README、安装自检、CI、release 差异。
- 定位问题：无效、太重、缺失、错误假设、需要下次调整的地方。
- 修改允许路径：`SKILL.md`、`README.md`、`manifest.json`、`agents/interface.yaml`、`.github/workflows/validate.yml`、`references/`、`examples/`、`scripts/`、`tests/`。
- 跑完整校验：validator、目标评估、负向测试、安装自检、JSON、README topics、Python 编译、diff 检查和 YAML 检查。
- 本地通过后提交推送；GitHub Actions 通过后创建语义化版本 release。
- 完成后删除临时目录，不在用户 home 目录保留临时 clone。

它必须写清这些护栏：

```text
自动化边界：
反馈来源：
允许修改路径：
评估方式：
发布规则：
回滚方式：
暂停条件：
```

它不会在无人触发时后台运行，也不会跨仓库、碰凭证、生产数据、私域内容或允许路径外文件。

### 4. 每日进化模式

`v0.12.0` 保留并继续验证定时审计入口：

```text
.github/workflows/daily-evolution.yml
```

默认每天 `09:00 Asia/Shanghai` 运行一次，也可以手动触发 `workflow_dispatch`。

每日 workflow 会自动：

- 运行 `scripts/daily_evolution_audit.py`
- 执行 validator、目标评估、负向测试、安装自检、manifest、README topics、Python 编译和 diff 检查
- 检查 self-evolution、daily workflow、示例、版本 badge 等结构漂移
- 检查 `manifest.json` 版本、`vX.Y.Z` git tag 和 GitHub release 是否一致
- 上传审计报告 artifact
- 只有发现需要处理的问题时，创建或更新 GitHub issue

它不会做：

- 无人值守改 `SKILL.md`
- 每天无意义 bump 版本
- CI 里自动发 release
- 跨仓库或碰凭证、生产数据、私域内容

如果 daily issue 出现，下一步让 agent 执行：

```text
用 xiaowei-goal 执行一次完全自动化自我进化
```

这是目前最稳的“每天进化一次”形态：每天自动体检和交接，真正代码进化在 agent session 中完成。

## Agent Reach 怎么配合

`xiaowei-goal` 本身不直接联网。它负责生成一个更好的 `/goal`，告诉后续 agent 应该如何使用联网能力。

如果当前环境安装了 Agent Reach，生成的 goal 会优先要求使用 Agent Reach，并在研究开始前确认可用渠道，例如运行 `agent-reach doctor`。

优先路由：

- 海外社交和内容：X/Twitter、Reddit、YouTube、GitHub、LinkedIn、Instagram
- 国内社交和内容：B 站、小红书、抖音、微博、微信公众号、V2EX
- 通用发现：RSS、Exa 网页搜索、播客转录、普通网页读取

如果没有 Agent Reach，也可以使用当前环境可用的：

- web search
- browser
- GitHub CLI
- 官方文档
- 搜索 API
- RSS
- 平台公开接口

如果某个渠道需要 Cookie、Token、登录、付费、代理、私域内容或绕过平台限制，goal 会要求 agent 暂停并让用户决定。Agent Reach 扩大可访问来源面，但不能被写成无限制全网访问。

## 输出会长什么样

三阶段研究任务通常包含：

```text
决策摘要：...
默认假设：...
偏好应用：...
反馈调整：...
策略判断：...
优先级判断：...
输出长度：...
选择理由：...
推荐执行版（中文，可直接复制）
/goal ...
阶段 1 - 广域调研：...
阶段 2 - Deep Research：...
阶段 3 - 业务应用：...
输出物：...
验证方式：...
限制：...
工作边界：...
推进规则：...
停止标准：...
暂停条件：...

默认选择理由：...
可选调整：...
```

最终研究应用简报通常要求包含：

```text
来源池：标题 | URL | 来源类型 | 工具/渠道 | 检索日期 | 访问限制 | 初步价值 | 是否进入 Deep Research
深度研究证据表：主题 | 关键事实 | 支撑来源 | 独立来源数量 | 来源强弱 | 反例/矛盾 | 推断 | 证据强度 | 对本业务的意义
质量门槛：关键结论 | 支撑来源数量 | 独立来源 | 来源强弱 | 降权原因 | 反例/矛盾 | 置信度 | 是否需要人工确认
业务应用表：业务模块 | 可用资料/证据 | 业务判断 | 具体动作 | 优先级 | 验证方式 | 是否需要人工确认
```

基础证据表仍然可以使用：

```text
来源标题 | URL | 来源类型 | 工具/渠道 | 日期/检索日期 | 事实 | 推断 | 可执行动作 | 置信度 | 需要人工确认？
```

这个表是整个 Skill 的重点：搜索不是为了堆资料，而是为了把外部信息转成业务动作。

## 示例

仓库内置了多个示例：

- `examples/app-research-goal.zh.txt`
- `examples/website-research-goal.zh.txt`
- `examples/practice-run-ai-website-goal.zh.txt`
- `examples/seo-content-cluster-goal.zh.txt`
- `examples/competitor-analysis-goal.zh.txt`
- `examples/growth-experiment-goal.zh.txt`
- `examples/direct-execution-goal.zh.txt`
- `examples/tool-boundary-goal.zh.txt`
- `examples/app-research-goal.en.txt`

你可以用本地校验脚本检查示例：

```bash
python3 scripts/validate_xiaowei_goal.py examples/*.txt
```

校验 validator 的坏例子：

```bash
python3 scripts/test_validator_negative_cases.py
```

检查本地已安装 skill 是否是新版：

```bash
python3 scripts/check_installed_skill.py ~/.agents/skills/xiaowei-goal
```

校验脚本会检查研究型 goal 是否包含：

- `agent-reach doctor` 或渠道可用性检查
- 明确来源数量
- `工具/渠道` 和 `访问限制`
- `任务包`
- `质量门槛`
- `工具栈`
- 禁止夸大 Agent Reach 或全网覆盖范围
- Deep Research 和业务应用阶段

通过时会输出：

```text
Xiaowei goal validation passed.
```

目标质量评估：

```bash
python3 scripts/evaluate_goal_output.py examples/*.txt
```

通过时会输出每个文件的分数，并以：

```text
Xiaowei goal output evaluation passed.
```

每日进化审计：

```bash
python3 scripts/daily_evolution_audit.py --report /tmp/daily-evolution-report.md
```

Release 一致性检查：

```bash
python3 scripts/check_release_consistency.py
```

Goal Compiler 行为测试与完整 Demo：

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
python3 scripts/validate_xiaowei_goal.py /tmp/goal-compiler-demo/02-reviewed-contract/goal.md
python3 scripts/evaluate_goal_output.py /tmp/goal-compiler-demo/02-reviewed-contract/goal.md
```

## 目录结构

```text
xiaowei-goal/
├── SKILL.md
├── README.md
├── manifest.json
├── agents/
│   ├── interface.yaml
│   └── openai.yaml
├── contest/
│   ├── demo-fixtures/
│   └── demo-output/
├── examples/
│   ├── app-research-goal.en.txt
│   ├── app-research-goal.zh.txt
│   ├── competitor-analysis-goal.zh.txt
│   ├── daily-self-evolution-goal.zh.txt
│   ├── direct-execution-goal.zh.txt
│   ├── growth-experiment-goal.zh.txt
│   ├── practice-run-ai-website-goal.zh.txt
│   ├── seo-content-cluster-goal.zh.txt
│   ├── self-evolution-goal.zh.txt
│   ├── tool-boundary-goal.zh.txt
│   └── website-research-goal.zh.txt
├── docs/
│   └── README.md
├── references/
│   ├── business-priority.md
│   ├── domain-packs.md
│   ├── feedback-loop.md
│   ├── compiler-runtime.md
│   ├── goal-compiler.md
│   ├── goal-contract.md
│   ├── output-compression.md
│   ├── quality-gate.md
│   ├── research-workflow.md
│   ├── self-evolution.md
│   ├── smart-router.md
│   ├── source-map.md
│   ├── task-packs.md
│   ├── tool-stack.md
│   └── xiaowei-preferences.md
├── scripts/
│   ├── check_installed_skill.py
│   ├── check_release_consistency.py
│   ├── check_readme_topics.py
│   ├── daily_evolution_audit.py
│   ├── evaluate_goal_output.py
│   ├── goal_compiler.py
│   ├── test_validator_negative_cases.py
│   └── validate_xiaowei_goal.py
└── tests/
    ├── invalid-goals/
    └── test_goal_compiler.py
```

## 分发说明

Skill 的核心分发内容是 `SKILL.md`、`references/`、`examples/`、`agents/`、`manifest.json` 和 `scripts/`。`contest/` 是可复现投稿证据，`docs/` 是 GitHub Pages 和历史报告展示；它们不替代 Skill 行为规范。

## 设计原则

`xiaowei-goal` 的风格是：

- 业务优先，不为了形式写提示词
- 证据优先，不把猜测写成结论
- 小闭环优先，不一上来做大而全
- 边界优先，不让 agent 随便碰生产、隐私、账号、付费和版权
- 动作优先，研究必须落到产品、页面、文案、SEO、增长或实现任务

## 和乔木老师案例的关系

这个 Skill 参考了乔木老师公开的 [qiaomu-goal-meta-skill](https://github.com/joeseesun/qiaomu-goal-meta-skill) 案例：它启发了“把模糊需求改写成可执行 `/goal`”这个方向。

但 `xiaowei-goal` 不是对原 Skill 的改名或换皮。它重新围绕我的使用场景设计：

- 更强调 App、网站、SaaS、SEO、增长和竞品研究
- 更强调 Agent Reach 或其他联网能力
- 更强调“事实 -> 推断 -> 可执行动作”
- 更强调广域调研、Deep Research、业务应用和下一阶段执行目标
- 新增机器可读契约、反证/终止门槛、人工 metric patch、严格 validator 和 first-step executor
- 重新编写了 `SKILL.md`、reference、示例和校验脚本

保留致谢，是为了尊重启发来源；具体来源、时间线、自己的实现边界和不主张的“全球/类别首创”见 `PROVENANCE.md`。

## License

MIT

Copyright (c) 2026 Xiaowei
