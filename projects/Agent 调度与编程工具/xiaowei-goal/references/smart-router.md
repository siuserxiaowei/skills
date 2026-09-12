# Smart Router

Use this reference before writing any final `/goal`. The router decides how
heavy the generated goal should be and whether the agent should ask questions
before drafting.

## Routing Dimensions

Classify the task with these dimensions:

```text
任务类型：app / website / SEO / growth / competitor / coding / docs / skill-evolution / mixed
任务成熟度：模糊想法 / 已有方向 / 已有仓库 / 已有数据 / 已有执行清单
外部信息需求：不需要 / 轻量 / 标准 / 深度
风险等级：低 / 中 / 高
是否需要先问问题：是 / 否
输出长度：短版 / 标准版 / 完整版
商业建议：立即做 / 先小实验验证 / 暂缓 / 不建议做
策略建议：直接执行 / 先验证需求 / 先重构问题 / 暂缓
领域包：AI 工具站包 / Chrome 插件包 / 出海 SaaS 包 / 小红书/抖音内容验证包 / GitHub 开源项目增长包 / 不适用
```

For English-compatible output:

```text
Task type: app / website / SEO / growth / competitor / coding / docs / skill-evolution / mixed
Task maturity: vague idea / chosen direction / existing repo / existing data / execution checklist
External information need: none / light / standard / deep
Risk level: low / medium / high
Ask clarifying questions first: yes / no
Output length: short / standard / full
Business recommendation: do now / validate with a small experiment / pause / do not recommend
Strategy recommendation: direct execution / validate demand first / reframe the problem first / pause
Domain pack: AI tool site / Chrome extension / global SaaS / Xiaohongshu-Douyin validation / GitHub open-source growth / not applicable
```

## Question Gate

Ask at most 3 clarifying questions before producing the `/goal` when missing
information would materially change scope, cost, risk, or direction.

Ask first when any of these are unknown:

- target user, market, geography, or language
- existing repo/product state
- business objective or success metric
- deadline, budget, or implementation tolerance
- whether external research, cookies, paid tools, accounts, or private data are authorized
- production impact, privacy, compliance, medical, legal, financial, or minors-related risk

Do not ask questions when the missing information can be handled with safe
defaults. In that case, state the defaults in `默认假设`.

## Depth Selection

Use the smallest sufficient output:

| Depth | Use when | Output |
|---|---|---|
| 轻量 / light | narrow docs, local code, small implementation, no external research | direct execution goal |
| 标准 / standard | app/site/SEO/growth/competitor work with normal research needs | three-stage research goal with 15-25 sources |
| 深度 / deep | high uncertainty, high risk, major business decision, crowded market, or broad strategy | three-stage research goal with 40+ sources and stronger evidence tables |

Do not default to deep mode just because the request sounds important. Deep mode
should have a reason: high uncertainty, high stakes, broad market scope, or
explicit user request.

## Preference Routing

Apply `references/xiaowei-preferences.md` before final routing:

- If the task can become a small loop, prefer a small validation or implementation loop over a large plan.
- If research is needed, require it to map into page, feature, content, growth, or implementation outputs.
- If the task matches tool site, AI product, SEO, or outbound/global SaaS, consider the matching domain pack.
- If the value is weak or the task is too broad, route to `先小实验验证` or `暂缓` instead of full implementation.

## Strategy Gate Routing

Before finalizing the route, apply `references/strategy-gate.md`:

- Broad build request with weak demand evidence: route to `先验证需求`.
- Vague "optimize/improve/make smarter" request: route to `先重构问题`, then define one observable behavior defect.
- Low-value, high-cost task: route to `暂缓` or a small validation loop.
- Existing local code/docs task with clear outcome: route to `直接执行`, but still name success evidence and stop conditions.
- Research task: use the Strategy Gate to decide the research questions before choosing source count or tools.

## Tool Weight

Choose the smallest reliable tool layer:

- no external tools for local docs/code edits
- normal web reader/browser for public pages that do not need structure or state
- Agent Reach for platform discovery and source collection
- Scrapling for repeatable public extraction or structured crawling
- browser-use for interactive state, clicking, screenshots, or authorized login flows
- Claude for Chrome only as a user-supervised browser extension path

If a heavier tool is not needed, explicitly avoid it in the choice rationale.

## Self-Evolution Routing

When the user asks for xiaowei-goal to evolve itself, automatically improve
itself, learn from previous outputs, update its own GitHub repository, or run
daily evolution:

- task type: `skill-evolution`
- external information need: usually `不需要` unless external tool research is part of the requested improvement
- output length: `标准版` by default
- read `references/self-evolution.md`
- require automation boundary, allowed paths, validation suite, CI gate, release policy, rollback, and pause conditions
- for daily evolution, require cron/schedule, daily audit script, release consistency guard, GitHub Actions, issue handoff, and an explicit no-unattended-code-rewrite rule
- do not ask clarifying questions unless the change needs credentials, production data, destructive actions, or an out-of-scope repository

## Required Decision Summary

Every generated goal should include a compact decision summary before the
`/goal` line:

```text
决策摘要：任务类型=...；成熟度=...；外部信息需求=...；风险等级=...；输出长度=...；是否先提问=...
默认假设：...
偏好应用：...
反馈调整：...
策略判断：...
优先级判断：...
输出长度：...
选择理由：...
```

If the answer should ask questions first, do not draft the final `/goal` yet.
Ask the smallest set of questions and explain which decision each answer will
change.
