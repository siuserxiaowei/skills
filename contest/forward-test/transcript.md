# Recorded Skill Forward Test

Status: `agent_result + human_pending`

Date: 2026-08-31

Agent context: Codex subagent `/root/build_goal_compiler`

Skill read: repository `SKILL.md` and `references/compiler-runtime.md`

Browsing: not attempted

Execution: not attempted

Human approval: not supplied

## User prompt

> Use $xiaowei-goal from this repository to compile the following request. Do
> not merely polish the wording. Run Smart Router and Strategy Gate, expose
> default assumptions, define a measurable success metric, at least two
> disconfirming signals, at least two kill criteria, a tool/evidence gate, and
> one safe first step. Return both a concise human-readable /goal and a JSON
> object suitable for comparison with the deterministic contract. Do not
> execute, browse, or claim live market evidence. Clearly mark which decisions
> came from your semantic judgment and which still need human approval.
>
> Request: 给我做个 AI 网站，越快越好

## Agent response

`agent_result`

决策摘要：任务类型=website；成熟度=模糊想法；外部信息需求=标准；风险等级=中；输出长度=标准版；是否先提问=否。

默认假设：目标用户、高频问题和付费意愿均未验证；首轮不做后端、登录、支付、数据采集或生产部署；页面文案只是待验证假设。

策略判断：真正问题不是“快速建完一个 AI 网站”，而是验证一个具体人群、一个问题和一个可点击承诺是否值得继续。最小验证是来源证据通过后，交付一个无外部依赖的本地假设页。成功指标候选是：生成 1 个本地 HTML，包含 1 个主标题、1 个主 CTA 和假设标记；测量方法是 HTML 结构检查。该指标仍需真人确认。

反证：

- 5 名目标用户中少于 2 名能复述页面所解决的问题；响应是停止加功能，重写人群和问题假设。
- 5 次测试中 CTA 意图数为 0；响应是将方向降级为低置信度假设。

Kill criteria：

- 连续 2 轮调整人群与承诺后，每轮 5 次测试仍无 CTA 意图，暂停完整建站。
- 首个产物需要 1 个未授权账号、付费数据或对外变更，停止并请求授权。

Tool / Evidence Gate：允许读取公开页面与本地文件；登录、Cookie/Token、付费数据、表单提交和生产变更需另行授权；“用户痛点或需求”至少需要 2 个独立来源。

`/goal` 先补齐两个独立的需求来源，保留矛盾与访问限制；再由真人确认精确成功指标、证据和执行范围；批准后仅写入一个本地 HTML 假设页并生成结构检查报告。缺来源、缺人工批准、需要外部授权或任一门禁失败时暂停。

JSON comparison record: [`semantic-result.json`](semantic-result.json).

## Boundary note

This is a preserved Agent forward-test record. It does not claim browsing,
market evidence, human approval, CLI validation PASS, or execution. The exact
metric and action remain `human_pending`.
