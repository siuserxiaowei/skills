# Goal Contract

Use this reference for final goal wording.

## Required Fields

A Xiaowei goal should include:

- `决策摘要` or `Decision Summary` before the `/goal`
- `默认假设` or `Default Assumptions` before the `/goal`
- `偏好应用` or `Preference Application` before the `/goal`
- `反馈调整` or `Feedback Adjustment` before the `/goal`
- `策略判断` or `Strategy Gate` before the `/goal`
- `优先级判断` or `Business Priority` before the `/goal`
- `输出长度` or `Output Length` before the `/goal`
- `选择理由` or `Choice Rationale` before the `/goal`
- `/goal` line with one clear outcome
- `阶段 1 - 广域调研` when external research is needed
- `阶段 2 - Deep Research` when external research is needed
- `阶段 3 - 业务应用` when external research is needed
- `输出物` when a document or brief is expected
- Agent Reach availability check and fallback route when platform/internet research is needed
- `工具栈` when webpage extraction, crawling, browser automation, or user-supervised Chrome work may matter
- `任务包` when the task matches app, website, SEO, competitor, or growth work
- `领域包` when the task matches AI tool site, Chrome extension, global SaaS, Xiaohongshu/Douyin validation, or GitHub open-source growth; otherwise mark `不适用`
- `质量门槛` when external research is needed
- `验证方式`
- `限制`
- `工作边界`
- `推进规则`
- `停止标准`
- `暂停条件`

For direct execution goals, the three research stage fields and `输出物` may be omitted if not relevant.
For self-evolution goals, also include `自动化边界`, `反馈来源`, `允许修改路径`, `评估方式`, `发布规则`, and `回滚方式`. For daily evolution goals, also include `每日节拍`.

## Three-Stage Research Template

```text
决策摘要：[任务类型、成熟度、外部信息需求、风险等级、输出长度、是否先提问]
默认假设：[不会阻塞执行的安全默认值]
偏好应用：[小闭环、页面/功能/内容/增长/实现目标、工具站/AI 产品/SEO/出海等偏好如何影响本次 goal]
反馈调整：[未提供上次执行反馈则说明不做反馈修正；有反馈则说明如何调整]
策略判断：[问题重构、最小验证、成功指标、反证信号、终止/暂缓条件]
优先级判断：[业务价值、证据强度、执行成本、分发潜力、变现路径、风险、建议]
输出长度：[短版 / 标准版 / 完整版]
选择理由：[为什么选这个深度、任务包和工具栈；为什么没有选择更重或更轻方案]
/goal 围绕[业务任务]执行三阶段研究工作流：先广域联网调研，再进行 Deep Research，最后把所有有效资料应用到当前业务，形成可执行方案和下一阶段实现目标。
任务包：[App MVP 研究包 / 网站/落地页改版包 / SEO 内容集群包 / 竞品分析包 / 增长实验包]；本次必须把研究结论映射到[对应业务产物]。
领域包：[AI 工具站包 / Chrome 插件包 / 出海 SaaS 包 / 小红书/抖音内容验证包 / GitHub 开源项目增长包 / 不适用]；本次必须把研究结论映射到[对应领域产物]。
工具栈：[Agent Reach 平台搜索和来源收集；web reader/browser 读取简单公开网页；Scrapling 做公共网页结构化抽取/爬取；browser-use 做点击、截图、动态 UI、登录授权流程；Claude for Chrome 仅作为用户明确授权的 Chrome 内协作/人工接管选项]。
阶段 1 - 广域调研：[Agent Reach 可用性检查、工具优先级、候选来源数量、来源类型、记录字段、来源池产物、不可用渠道的 fallback]。
阶段 2 - Deep Research：[高价值来源筛选、深读、对比、交叉验证、每条关键结论至少 2 个独立来源或降级为假设、来源强弱、矛盾标注、证据强度]。
阶段 3 - 业务应用：[把去重后相关且可追溯资料映射到产品、页面、文案、SEO、增长、技术实现、验证实验和下一阶段 goal]。
输出物：[研究应用简报、来源池、深度研究证据表、业务应用表、下一阶段目标]。
质量门槛：[2 个独立来源、来源强弱、过期/营销/不可访问来源降权、矛盾信息列出、低证据结论标为低置信度或假设]。
验证方式：[来源可追溯、事实/推断/建议分开、动作可执行]。
限制：[不复制、不编造、不夸大 Agent Reach 覆盖范围、不用抓取/浏览器自动化绕过访问限制、不碰隐私/付费/生产/账号/Cookie]。
工作边界：[研究阶段和实现阶段各自允许写什么]。
推进规则：[先问题和搜索词，再广域调研，再 Deep Research，再业务应用，再生成下一目标]。
停止标准：[三阶段完成、证据完整、业务动作清楚、下一目标清楚]。
暂停条件：[账号、Cookie、Token、付费、绕过限制、合规、版权、生产数据、私域内容、方向决策]。
```

## Direct Execution Template

```text
决策摘要：[任务类型、成熟度、外部信息需求、风险等级、输出长度、是否先提问]
默认假设：[不会阻塞执行的安全默认值]
偏好应用：[小闭环和避免过度研究如何影响本次 goal]
反馈调整：[未提供上次执行反馈则说明不做反馈修正；有反馈则说明如何调整]
策略判断：[问题重构、最小验证、成功指标、反证信号、终止/暂缓条件]
优先级判断：[业务价值、证据强度、执行成本、分发潜力、变现路径、风险、建议]
输出长度：[短版 / 标准版 / 完整版]
选择理由：[为什么直接执行而不是三阶段研究]
/goal 基于当前项目上下文完成[具体结果]，先读取已有文档、脚本和约定，再做最小必要改动。
验证方式：[命令、日志、截图、产物、核心流程]。
限制：[不能改变的行为、接口、数据、配置、凭证、范围]。
工作边界：[允许修改的目录/文件和禁止触碰的部分]。
推进规则：[小步修改、重跑检查、基于证据调整]。
停止标准：[什么证据证明完成]。
暂停条件：[需要人工、账号、付费、生产、破坏性操作、合规或方向选择]。
```

## Self-Evolution Template

```text
决策摘要：[任务类型=docs / mixed；成熟度=已有仓库；外部信息需求=不需要；风险等级；输出长度；是否先提问]
默认假设：[仓库、远程、版本、临时目录、安全默认值]
偏好应用：[小闭环、测试驱动、避免过度拟合单次反馈]
反馈调整：[反馈来源和本次如何调整；无反馈则说明不做反馈修正]
策略判断：[本次行为缺陷、最小能力改动、成功指标、反证信号、终止/暂缓条件]
优先级判断：[业务价值、证据强度、执行成本、分发潜力、变现路径、风险、建议]
输出长度：[短版 / 标准版 / 完整版]
选择理由：[为什么自动进化、为什么不是研究流程、为什么这些护栏足够]
/goal 围绕 xiaowei-goal 仓库执行一次完全自动化自我进化：[收集反馈、定位缺口、修改允许路径、跑校验、提交推送、等 CI、发 release、清理临时目录]。
自动化边界：[用户显式触发后自动执行；不是无人值守后台任务；不跨仓库扩散]
每日节拍：[如果用户要求每天自动进化，使用 GitHub Actions cron 定时审计、artifact 和 issue handoff；运行 check_release_consistency.py 检查 manifest/tag/release；不无人值守改代码或发 release]
反馈来源：[用户反馈、执行结果、examples、validator、README、安装自检、CI、release 差异]
允许修改路径：[SKILL.md、README.md、manifest.json、agents/interface.yaml、.github/workflows/validate.yml、references/、examples/、scripts/、tests/]
评估方式：[evaluate_goal_output.py、正向示例、负向 validator case、不过度拟合]
验证方式：[validate、evaluate、negative tests、installed self-check、JSON、README topics、py_compile、diff check、YAML if changed]
发布规则：[local green -> push -> GitHub Actions green -> semantic release at same commit]
回滚方式：[release 前 fix forward 或只回滚本轮 commit；release 后用修复 release]
限制：[不碰凭证、隐私、生产数据、允许路径外文件、无限制后台自治]
工作边界：[临时目录 clone；只改允许路径；推 GitHub；清理临时目录]
推进规则：[先 failing case 或评估缺口，再最小实现，再完整校验，不跳过失败]
停止标准：[远程、README、manifest、examples、validator、CI、release 一致；临时目录已删除]
暂停条件：[凭证、付费、生产、私域、破坏性、允许路径外、法律隐私、CI 同因连续失败]
```

## Default Choices

Use these defaults unless the user says otherwise:

- New vague app/site: standard three-stage research, no backend/auth/payment in first implementation goal.
- Narrow local code/docs task: direct execution mode with no external research.
- High-risk or high-uncertainty business decision: deep research mode only when the risk or uncertainty justifies it.
- Weak business value or weak evidence: recommend `先小实验验证` or `暂缓`, not immediate full implementation.
- Tool site / AI product / SEO / outbound-global fit: consider the domain pack before finalizing.
- No prior execution feedback: state `未提供上次执行反馈，本次不做反馈修正`.
- Existing repo: inspect local scripts and docs before changes.
- No deployment request: local verification only.
- No source preference: Agent Reach first when available, then web + competitors + user communities + implementation references.
- No language preference from a Chinese user: Chinese recommended goal first.
- No authorization: do not use login-only or paid channels.

## Red Flags

Revise the goal if it contains:

- placeholders such as `[xxx]`, `TODO`, `TBD`, `待定`
- "随便搜", "全网都搜", or "一直试"
- "照抄", "扒下来", or "做一个一样的"
- no source count for research
- no decision summary, default assumptions, or choice rationale
- no preference application, feedback adjustment, business priority, or output length
- no strategy gate with problem reframe, smallest bet, success metric, counter-evidence, and kill criteria
- no reason why the selected output depth fits the task
- no priority recommendation when a business/product/content/growth task is requested
- no domain pack for AI tool site, Chrome extension, global SaaS, social-content validation, or GitHub open-source growth tasks
- no `任务包` for app, website, SEO, competitor, or growth research
- no `质量门槛` for research goals
- no Deep Research stage for business research tasks
- no business application stage after research
- no Agent Reach availability check when platform/internet research is requested
- no tool-stack route when webpage extraction, crawling, browser automation, or Chrome workflow is mentioned
- no tool/channel or access limitation fields in source recording
- no explicit rule against claiming full internet coverage
- no pause condition for scraping, browser automation, credentials, form submission, purchase, account change, private content, or anti-bot bypass
- no verification evidence
- no pause condition
- self-evolution without automation boundary, allowed paths, validation suite, CI gate, release policy, rollback, and pause risks
- daily evolution without cron/schedule, daily audit script, release consistency check, GitHub Actions, issue handoff, and the rule against unattended code rewrites
