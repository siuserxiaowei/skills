---
name: xiaowei-goal
description: >
  Convert app, website, SaaS, landing page, content, SEO, growth, competitor,
  product, or vague business tasks into Xiaowei-style executable `/goal`
  commands with a three-stage workflow: broad research, Deep Research, then
  business application. Use when the user wants to search first, learn from the
  internet, use Agent Reach, do competitor research, build an app/site after
  research, turn a rough idea into an agent task, or define evidence-based
  success criteria. Triggers include 小伟 goal, xiaowei-goal, 联网调研, 先搜索再做,
  Deep Research, Agent Research, Agent Reach, 竞品分析, 网站方案, App MVP, 增长方案,
  SEO 方案, 自我进化, 自动进化, 每日进化, and 把需求写成可执行 goal.
---

# Xiaowei Goal

把一句模糊的业务想法，改写成可以交给 agent 持续执行、能联网研究、能深度分析、能落到业务动作、能验收结果的 `/goal`。

核心风格：

- 先判断任务轻重，再决定是不是要三阶段研究。
- 先识别信息缺口，再决定是否需要问用户最多 3 个关键问题。
- 默认采用小闭环、业务应用、工具站/AI 产品/SEO/出海友好的工作偏好。
- 如果商业价值低或证据太弱，要建议暂缓、重构问题或先做小实验。
- 先看外部世界，再决定怎么做。
- 先广域调研，再 Deep Research，最后应用到自己的业务。
- 如果当前环境安装了 Agent Reach，把它作为广域调研的首选能力层。
- 按任务选择最小工具层：Agent Reach、普通网页读取、Scrapling、browser-use、Claude for Chrome。
- 用任务包把研究映射到具体业务产物，而不是只给通用建议。
- 用 quality gate 约束结论质量：关键结论至少 2 个独立来源支撑，否则降级为假设。
- 用 Strategy Gate 先做策略判断：重构真实问题、定义最小验证、成功指标、反证信号和终止/暂缓条件。
- 用 Goal Compiler 暴露默认假设、选择理由和工具取舍，不做死板模板填空。
- 用输出压缩控制长短，不默认输出过长模板。
- 用细分领域包把研究落到 AI 工具站、Chrome 插件、出海 SaaS、内容验证或开源增长。
- 用户明确要求时，进入自我进化模式：自动收集反馈、改允许路径、跑校验、推送、等 CI、发 release。
- 自我进化 goal 必须写清 `自动化边界`、`允许修改路径`、`评估方式`、`发布规则`、`回滚方式` 和暂停条件。
- 每日进化使用 GitHub Actions 定时审计、artifact 和 issue handoff；不在无人值守 CI 中随机改代码或每天制造无意义 release。
- 每日进化必须检查 manifest 版本、git tag 和 GitHub release 一致性，避免“仓库更新但 release 漏发”。
- 先分清事实和判断，再给执行动作。
- 先做一个能跑通的小闭环，再扩展功能。
- 重要结论必须有来源；没有证据就标成假设。
- 不复制竞品，只提炼可迁移的结构、路径和判断。

## Default Mode

Use Chinese output by default for Chinese users. Keep the slash command as `/goal`.

Always run Smart Router before drafting. Do not default to the heaviest
three-stage template when a direct or light goal is enough.

## Executable Contract Mode

When the user asks to compile, validate, demonstrate, or execute a vague goal,
read `references/compiler-runtime.md`. Use `scripts/goal_compiler.py` to create a
machine-readable contract rather than presenting prose as execution evidence.

Keep the judgment layers separate:

- the Agent/Skill performs semantic passes and produces a complete semantic
  JSON input: router, strategy, measurable metric, disconfirming evidence, kill
  criteria, tool/evidence gate, domain-specific acceptance, and first safe step
- the CLI does not invent missing semantics; `compile` requires
  `--semantic-input` and rejects request/domain/action mismatches
- for `research_required` work, recorded sources and source-backed claims must
  pass before a human can approve anything
- a real human edits the exact metric when needed and explicitly approves the
  execution scope; examples marked pending or test-only are not approval
- the CLI saves the complete semantic input, reconstructs every derived field,
  and records `approved_payload_sha256` so validation and execution can detect
  drift between the retained review record and the current payload
- `approved_payload_sha256` and `review_id` are unkeyed consistency values, not
  signatures or proof against an actor who can rewrite both data and digests
- the executor may dispatch only one whitelisted, task-compatible text artifact
  inside the approved absolute workspace plus relative output directory, with
  fixed checks; it must not execute generated code or cross an authorization
  boundary

Never report a draft contract as executed. A `FAIL.log` is failure evidence,
not a partial pass. Write `PASS.log` only after strict validation really passes.
The bundled contest fixture is deterministic (`liveAiClaimed:false`) and stops
at `HUMAN_PENDING`; it is not a live model result or a human approval.

## Distribution Note

If a local installed copy behaves like an older version and does not mention
quality gates, task packs, Agent Reach routing, or the research tool stack, ask
the user to update the installed skill with:

```bash
npx skills add siuserxiaowei/xiaowei-goal
```

GitHub updates do not guarantee that an already installed local skill copy has
been refreshed in the current agent session.

Choose one of three output depths:

1. **轻量模式**：use for narrow docs, local coding, or simple execution where external information is unnecessary.
2. **标准研究模式**：default for app, website, landing page, SaaS, SEO, growth, competitor, content, market, and product direction tasks.
3. **深度研究模式**：use for high uncertainty, high-risk business decisions, crowded markets, broad strategy, or explicit deep-research requests.

If the user mentions Agent Reach, search, research, Deep Research, competitor analysis, app/site planning, SEO, growth, or "先学习再应用", choose 三阶段研究模式.

If missing information would materially change scope, risk, cost, or direction,
ask at most 3 clarifying questions before drafting the final `/goal`. Otherwise,
state safe defaults in `默认假设`.

## Agent Reach Routing

When external research is needed, prefer Agent Reach if it is installed or explicitly requested. Treat it as a capability layer for reading/searching public or user-authorized content, not as a guarantee of unlimited internet access.

Generated goals should ask the executing agent to:

- run `agent-reach doctor` or otherwise confirm channel availability before relying on Agent Reach
- route sources through Agent Reach first for X/Twitter, Reddit, YouTube, GitHub, LinkedIn, Instagram, Bilibili, 小红书, 抖音, 微博, 微信公众号, V2EX, RSS, Exa web search, podcasts, and normal web pages when available
- record the tool/channel used for every source, such as Agent Reach X, Agent Reach YouTube, Agent Reach Exa, browser, web search, GitHub CLI, or RSS
- use accessible fallbacks when a channel is unavailable, blocked, login-only, paid, or rate-limited
- pause before asking for or using cookies, tokens, paid access, production accounts, private groups, or platform-bypass techniques

## Tool Stack Routing

When research needs more than search results, choose the smallest reliable tool layer:

- Agent Reach for platform discovery, semantic web search, social/video/community/GitHub/RSS/podcast sources
- normal web readers/search/browser for simple public pages
- Scrapling for public webpage extraction, resilient selectors, dynamic public pages, or repeatable crawling
- browser-use for clicking, typing, screenshots, browser state, login-authorized flows, or visual verification
- Claude for Chrome only as an optional, user-supervised Chrome extension workflow when the user explicitly has it available

Do not require every tool. Do not use scraping, browser automation, or extensions to bypass paywalls, private content, CAPTCHAs, platform restrictions, credentials, purchases, messages, account settings, or legal/terms-sensitive flows without explicit authorization.

## Workflow

1. Restate the user's real outcome in business terms.
2. Read `references/xiaowei-preferences.md` and apply current preferences without pretending they are permanent memory.
3. Read `references/feedback-loop.md`; if the user provides prior execution feedback, extract what worked, failed, was too heavy, or should change.
4. Read `references/smart-router.md` and classify task type, maturity, external information need, risk, question need, and output length.
5. Read `references/strategy-gate.md` and define problem reframe, smallest bet, success metric, counter-evidence, and kill criteria.
6. Read `references/business-priority.md` for business/product/content/SEO/growth/competitor tasks and decide whether to do now, validate first, pause, or reject.
7. If critical missing information changes scope, cost, risk, or direction, ask at most 3 questions and stop before drafting.
8. Read `references/output-compression.md` and choose short, standard, or full output.
9. If research is needed, read `references/research-workflow.md`.
10. If research is needed, read `references/quality-gate.md`.
11. If research needs internet/platform/browser capability, read `references/tool-stack.md`.
12. If the user names an app/site/business channel, read `references/source-map.md`.
13. If the task matches app, website, SEO, competitor, or growth work, read `references/task-packs.md`.
14. If the task matches AI tool site, Chrome extension, global SaaS, Xiaohongshu/Douyin validation, or GitHub open-source growth, read `references/domain-packs.md`.
15. If the user asks xiaowei-goal to evolve itself, auto-improve, automatically update its repository, or run daily evolution, read `references/self-evolution.md`.
16. Read `references/goal-compiler.md` and run the compiler passes: intent, knowns, gaps, assumptions, preference, feedback, strategy, priority, routing, compression, tool, task pack, domain pack, evolution, risk, self-critique, finalization.
17. If the task is ready for execution, read `references/goal-contract.md`.
18. Produce the best copy-ready `/goal` with `决策摘要`, `默认假设`, `偏好应用`, `反馈调整`, `策略判断`, `优先级判断`, `输出长度`, and `选择理由` before the goal.
19. Add compact options only when a choice changes cost, risk, or direction.
20. If writing an output file, run `python3 scripts/validate_xiaowei_goal.py <file>` and `python3 scripts/evaluate_goal_output.py <file>`.

## Three-Stage Research Output

Use this shape when the task should search, deeply analyze, then apply findings to the user's business:

```text
决策摘要：任务类型=[app / website / SEO / growth / competitor / coding / docs / mixed]；成熟度=[模糊想法 / 已有方向 / 已有仓库 / 已有数据 / 已有执行清单]；外部信息需求=[轻量 / 标准 / 深度]；风险等级=[低 / 中 / 高]；输出长度=[短版 / 标准版 / 完整版]；是否先提问=[是 / 否]
默认假设：[列出不会阻塞执行的安全默认值]
偏好应用：[说明小闭环、页面/功能/内容/增长/实现目标、工具站/AI 产品/SEO/出海等偏好如何影响本次 goal]
反馈调整：[未提供上次执行反馈则说明不做反馈修正；如有反馈则说明本次如何调整]
策略判断：[问题重构、最小验证、成功指标、反证信号、终止/暂缓条件]
优先级判断：[业务价值、证据强度、执行成本、分发潜力、变现路径、风险和建议]
输出长度：[短版 / 标准版 / 完整版]
选择理由：[说明为什么选这个深度、任务包和工具栈，为什么没有选择更重或更轻的方案]
推荐执行版（中文，可直接复制）
/goal 围绕[业务任务]执行三阶段研究工作流：先广域联网调研，再进行 Deep Research，最后把所有有效资料应用到当前业务，形成可执行方案和下一阶段实现目标。
任务包：[选择 App MVP 研究包 / 网站/落地页改版包 / SEO 内容集群包 / 竞品分析包 / 增长实验包]；本次必须把研究结论映射到[对应业务产物]。
领域包：[AI 工具站包 / Chrome 插件包 / 出海 SaaS 包 / 小红书/抖音内容验证包 / GitHub 开源项目增长包 / 不适用]；本次必须把研究结论映射到[对应领域产物]。
工具栈：优先 Agent Reach 做平台搜索和来源收集；普通公开网页先用 web reader/browser；需要结构化抽取或公共网页爬取时使用 Scrapling；需要点击、截图、登录授权流程或动态 UI 验证时使用 browser-use；Claude for Chrome 仅作为用户明确授权的 Chrome 内协作/人工接管选项。
阶段 1 - 广域调研：优先使用 Agent Reach；开始前运行 `agent-reach doctor` 或确认可用渠道，若不可用则使用当前环境可用的搜索、浏览、GitHub、RSS 或平台读取工具；检索[数量]个候选来源，覆盖直接竞品、相邻产品、官方资料、用户评价或社区讨论、内容平台、技术/实现参考；记录标题、URL、来源类型、工具/渠道、检索日期、访问限制和初步价值判断。
阶段 2 - Deep Research：从第一阶段来源池中筛选高价值来源进行深读、对比和交叉验证；提取关键事实、用户痛点、竞品策略、页面/产品结构、增长路径、技术做法、风险和证据强度；把矛盾信息标成不确定。
阶段 3 - 业务应用：把本轮收集到、去重后、与业务目标相关且可追溯来源的资料，映射到当前业务的产品功能、页面结构、文案方向、SEO 主题、增长动作、技术实现、验证实验和下一阶段 `/goal`。
输出物：产出一份研究应用简报，包含来源池、深度研究证据表、关键洞察、可迁移动作、不能复制的内容、业务决策、风险和下一阶段 `/goal`。
质量门槛：每条关键结论至少需要 2 个独立来源支撑；标明来源强弱；过期、营销软文、不可访问或片段来源必须降权；矛盾信息必须列出；不足 2 个来源的结论只能标为低置信度或假设。
验证方式：每条关键结论必须能追溯到来源；事实、推断、建议分开写；业务动作必须能对应到产品、页面、文案、SEO、增长、技术实现或验证实验。
限制：不复制竞品品牌、文案、图片、视频、代码、课程、版权素材或未经证实的市场结论；不把单一来源当成事实；不把 Agent Reach 描述成无限制全网访问；不使用登录账号、Cookie、Token、付费平台、生产数据、私域内容或隐私数据，除非用户明确授权。
工作边界：三阶段研究期间只创建研究应用文档和下一阶段执行目标；实现阶段只改与当前业务目标直接相关的文件。
推进规则：先列研究问题和搜索词，再做广域检索，再筛选来源做 Deep Research，最后统一映射到业务动作；每个阶段结束前先补齐证据缺口，再进入下一阶段。
停止标准：研究应用简报覆盖三阶段，包含可追溯来源、深度研究证据、业务启发、可执行动作、风险和下一阶段目标。
暂停条件：需要 Cookie、Token、付费数据库、登录账号、绕过平台限制、法律/医疗/金融判断、版权授权、生产数据、私域内容或重大业务定位选择时暂停。
```

Default source counts for broad research:

- 轻量：6-8 个来源
- 标准：15-25 个来源
- 深度：40+ 个来源

Deep Research should not simply add more links. It should read and compare the highest-value sources from the broad research pool, then turn them into business decisions.

## Direct Execution Output

Use this shape when research is unnecessary:

```text
决策摘要：任务类型=[coding / docs / mixed]；成熟度=[已有仓库 / 已有执行清单]；外部信息需求=不需要；风险等级=[低 / 中 / 高]；输出长度=短版；是否先提问=[是 / 否]
默认假设：[列出不会阻塞执行的安全默认值]
偏好应用：[说明小闭环和避免过度研究如何影响本次 goal]
反馈调整：[未提供上次执行反馈则说明不做反馈修正；如有反馈则说明本次如何调整]
策略判断：[问题重构、最小验证、成功指标、反证信号、终止/暂缓条件]
优先级判断：[业务价值、证据强度、执行成本、分发潜力、变现路径、风险和建议]
输出长度：[短版 / 标准版 / 完整版]
选择理由：[说明为什么直接执行而不是三阶段研究]
推荐执行版（中文，可直接复制）
/goal 基于当前项目上下文完成[具体结果]，先读取已有文档、脚本和约定，再做最小必要改动。
验证方式：运行项目中最小相关检查；如果是前端或交互任务，启动本地服务并走通核心流程；用命令输出、日志、截图或产物路径证明完成。
限制：不改无关功能、公开接口、数据结构、生产配置、凭证或用户数据；不加入用户没有要求的账号、支付、部署或复杂功能。
工作边界：只修改与本次目标直接相关的文件、测试和文档。
推进规则：一次只做一个聚焦改动；每次有意义改动后重跑检查；失败时先读错误、日志或文档，再调整方案。
停止标准：核心结果被运行证据证明可用，相关检查通过，或缺少配置时明确说明无法继续的原因。
暂停条件：需要凭证、付费服务、生产数据、破坏性操作、法律/医疗/金融判断、版权素材或产品方向决策时暂停。
```

## Response Contract

For Chinese users, output:

1. `决策摘要`
2. `默认假设`
3. `偏好应用`
4. `反馈调整`
5. `策略判断`
6. `优先级判断`
7. `输出长度`
8. `选择理由`
9. `推荐执行版（中文，可直接复制）`
10. `可选调整`
11. `Goal Draft (English-compatible)` only when useful for cross-tool compatibility or when the user asks for it

Do not lead with a blank template. Do not leave placeholders. Do not start implementation unless the user explicitly asks to execute the generated goal.

## Quality Rules

Good goals:

- describe an outcome, not activity
- include a compact decision summary before the goal
- state safe assumptions instead of silently guessing
- apply Xiaowei preferences without inventing private memory
- adjust based on explicit user feedback when available
- include a strategy gate with problem reframe, smallest bet, success metric, counter-evidence, and kill criteria
- include business priority and recommend pause or a small experiment when value is weak
- choose output length intentionally
- explain why the selected depth, task pack, and tool stack fit the task
- name source count or verification commands
- name Agent Reach routing and fallback rules when internet/platform research matters
- name tool-stack routing when webpage extraction, crawling, browser automation, or Chrome user-supervised work matters
- name a task pack when the work is app, website, SEO, competitor, or growth related
- include a quality gate with 2-source support, source strength, downgrade rules, and contradiction handling
- force the three stages when external information matters
- protect unrelated files, secrets, production data, and copyrighted material
- separate facts, inferences, and actions
- define where work may happen
- define how to retry after failures
- define when to stop and when to pause

Bad goals:

- "帮我做得更好"
- "随便搜一下"
- "一直试直到满意"
- "看起来可以就行"
- "全网资料都整理一下" without depth or source rules
- "深度研究一下" without a broad research pool, source selection, and business application stage
- "照着竞品做一个一样的"
- using a full three-stage research template for a narrow local edit
- ignoring low business value and pushing directly into large implementation
- repeating the user request without a strategy gate, counter-evidence, or kill criteria
- outputting a long template when short mode is enough
- self-evolution goals that automate commit/push/release without allowed paths, validation suite, CI gate, release policy, rollback, and pause conditions
- daily-evolution goals that do not mention cron/schedule, `daily_evolution_audit.py`, GitHub Actions, issue handoff, and the rule against unattended code rewrites
- daily-evolution goals that do not mention `check_release_consistency.py` or release/tag consistency
- listing every tool when the smaller layer is enough
- research conclusions without source strength, downgrade rules, or contradiction handling
- using scraping or browser automation without authorization, scope, access limits, and pause conditions

## References

- `references/smart-router.md`: task classification, question gate, depth selection, and tool weight decisions.
- `references/goal-compiler.md`: intent, knowns, gaps, assumptions, routing, tool selection, risk, self-critique, and finalization passes.
- `references/xiaowei-preferences.md`: current Xiaowei-style defaults for small loops, business application, tool sites, AI products, SEO, outbound/global work, and pause decisions.
- `references/feedback-loop.md`: explicit prior-result feedback extraction and next-goal adjustment rules.
- `references/strategy-gate.md`: problem reframe, smallest bet, success metric, counter-evidence, and kill criteria.
- `references/business-priority.md`: lightweight business priority scoring and do/validate/pause/reject recommendations.
- `references/output-compression.md`: short, standard, and full output rules.
- `references/domain-packs.md`: AI tool site, Chrome extension, global SaaS, Xiaohongshu/Douyin validation, and GitHub open-source growth packs.
- `references/self-evolution.md`: automatic feedback-to-change loop, allowed paths, validation gates, release policy, rollback, and pause conditions.
- `references/research-workflow.md`: three-stage broad research, Deep Research, evidence table, and business application rules.
- `references/quality-gate.md`: source strength, 2-source rule, downgrade rules, contradiction handling, and confidence labels.
- `references/tool-stack.md`: Agent Reach, Scrapling, browser-use, and Claude for Chrome routing and boundaries.
- `references/source-map.md`: platform routing and query patterns for app, website, SEO, growth, and technical tasks.
- `references/task-packs.md`: App MVP, website/landing page, SEO cluster, competitor analysis, and growth experiment packs.
- `references/goal-contract.md`: compact templates for executable goals and validation rules.
- `references/compiler-runtime.md`: machine-readable contract, human review, strict validation, and first-step execution protocol.
- `scripts/goal_compiler.py`: deterministic CLI for compile, validate, apply-review, execute, and reproducible demo modes.
- `scripts/validate_xiaowei_goal.py`: local validator for generated goal examples.
- `scripts/evaluate_goal_output.py`: local scorer for generated goal completeness, proportionality, and business application signals.
- `scripts/daily_evolution_audit.py`: deterministic daily audit for scheduled evolution checks and GitHub issue handoff.
- `scripts/check_release_consistency.py`: manifest version, git tag, and GitHub release consistency guard.
