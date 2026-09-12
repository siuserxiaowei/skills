# Strategy Gate

Use this reference before business priority, task packs, tool routing, or final
goal drafting. The purpose is to stop xiaowei-goal from acting like a template
generator. It must first decide what problem is worth solving, what the smallest
useful bet is, and what evidence would make the goal wrong.

## Required Judgment

Every generated goal must include a compact `策略判断` / `Strategy Gate` field
before `优先级判断` / `Business Priority`.

Chinese shape:

```text
策略判断：问题重构=...；最小验证=...；成功指标=...；反证信号=...；终止/暂缓条件=...
```

English-compatible shape:

```text
Strategy Gate: problem reframe=...; smallest bet=...; success metric=...; counter-evidence=...; kill criteria=...
```

## How To Think

1. **Problem Reframe**: Rewrite the user's request into the real business or
   engineering problem. If the request is too broad, narrow it to the decision
   that should be made next.
2. **Smallest Bet**: Prefer the smallest research, page, feature, content,
   growth, or implementation loop that can produce useful evidence.
3. **Success Metric**: Name a practical signal that tells the user whether the
   goal worked, such as shipped page, validated source-backed decision, trial
   signups, qualified leads, ranking candidate, conversion path, test pass, or
   issue closed.
4. **Counter-Evidence**: State what evidence would disprove the idea, lower
   priority, or force a direction change.
5. **Kill Criteria**: State when to stop, pause, downscope, or recommend not
   doing the work.

## Decision Rules

- If the user asks for a broad build before demand evidence, reframe to a
  validation loop first.
- If the task has weak business value and high cost, recommend `暂缓` or a
  small test instead of full research or implementation.
- If the request is just "make it better", translate it into a concrete defect,
  measurable target, and stop condition.
- If research is needed, the Strategy Gate should shape the research questions
  before source collection begins.
- If the task is direct execution, the Strategy Gate should explain why research
  is unnecessary and what local evidence will prove completion.
- If self-evolution is requested, the Strategy Gate should identify the behavior
  defect, the smallest capability change, the validator or example that proves
  it, and the rollback/stop signal.

## Bad Strategy Gates

Reject or revise a Strategy Gate when it:

- repeats the user request without reframing it
- says only "continue" or "继续做" without a smallest bet
- has no success metric
- has no counter-evidence or kill criteria
- turns every idea into a full build or full deep research task
- uses vague words such as "优化一下", "提升体验", or "更智能" without an
  observable output

## Examples

```text
策略判断：问题重构=不是先做完整 AI 简历平台，而是验证用户是否愿意用一个免费简历诊断入口留下简历问题；最小验证=一个落地页加 3 篇搜索意图明确的内容页；成功指标=有可追踪的试用点击、问题提交或邮件线索；反证信号=SERP 全是强品牌且用户痛点不可迁移，或内容页无法形成明确 CTA；终止/暂缓条件=两轮小实验没有任何有效点击或线索时暂缓扩功能。
```

```text
Strategy Gate: problem reframe=do not build a full meeting intelligence suite yet; smallest bet=validate one meeting-summary workflow and one landing-page promise; success metric=source-backed MVP scope plus one testable signup path; counter-evidence=users care more about privacy or integrations than summary quality; kill criteria=pause full implementation if evidence cannot support a narrow activation loop.
```
