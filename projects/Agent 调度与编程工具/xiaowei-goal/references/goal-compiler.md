# Goal Compiler

Use this reference after Smart Router and before the final answer. The compiler
turns a task into a goal through explicit judgment rather than template filling.

## Compiler Passes

Run these passes before output:

1. **Intent Pass**: restate the real business or engineering outcome.
2. **Knowns Pass**: list what is already known from the user request.
3. **Gap Pass**: identify missing information that changes scope, risk, or direction.
4. **Assumption Pass**: choose safe defaults for non-blocking gaps.
5. **Preference Pass**: apply `xiaowei-preferences.md` without inventing private memory.
6. **Feedback Pass**: if prior execution feedback exists, convert it into concrete adjustments.
7. **Strategy Gate Pass**: apply `strategy-gate.md`; reframe the real problem, choose the smallest useful bet, name a success metric, state counter-evidence, and define kill criteria.
8. **Priority Pass**: score value, evidence, cost, distribution, monetization, and risk.
9. **Routing Pass**: choose direct execution, light research, standard research, or deep research.
10. **Compression Pass**: choose short, standard, or full output length.
11. **Tool Pass**: choose the smallest sufficient tool stack and name tools to avoid.
12. **Task Pack Pass**: choose the primary task pack and mention secondary packs only if useful.
13. **Domain Pack Pass**: choose one domain pack when AI tool site, Chrome extension, global SaaS, Xiaohongshu/Douyin validation, or GitHub open-source growth applies.
14. **Evolution Pass**: when self-evolution is requested, apply `self-evolution.md` and require automation boundary, allowed paths, validation suite, CI gate, release policy, rollback, and pause conditions. When daily evolution is requested, require schedule, daily audit script, release consistency guard, GitHub Actions, issue handoff, and no unattended code rewrite.
15. **Risk Pass**: add pause conditions for credentials, paid access, production data, private content, compliance, copyright, or destructive actions.
16. **Self-Critique Pass**: remove template bloat, unnecessary tools, vague verbs, and unsupported claims.
17. **Finalization Pass**: produce the copy-ready `/goal`.

## Self-Critique Checklist

Before finalizing, check:

- Is the goal heavier than the task needs?
- Is a three-stage research workflow actually required?
- Did Xiaowei preferences change the depth, domain pack, or stop standard?
- Did prior feedback change the next goal, or is there no feedback to apply?
- Did the Strategy Gate reframe the problem instead of repeating the request?
- Did it name a smallest bet, success metric, counter-evidence, and kill criteria?
- Is the business priority strong enough for this level of effort?
- Is the output length proportional to the task?
- Are any tools listed only because they are fashionable?
- Does the task pack match the real outcome?
- Does the domain pack match the actual distribution/product context?
- If this is self-evolution, are the allowed paths, validation suite, CI gate, release policy, rollback, and temporary-directory cleanup explicit?
- If this is daily evolution, are schedule, daily audit, release consistency, issue handoff, and no-unattended-code-rewrite boundaries explicit?
- Did the goal name concrete output and stop criteria?
- Are facts, assumptions, and actions separated?
- Are Agent Reach and browser automation boundaries clear?
- Does the goal avoid copying competitors or overclaiming internet coverage?
- Is the next step obvious after the goal runs?

## Output Contract

For Chinese users, include these fields before the goal:

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
```

For English-compatible output:

```text
Decision Summary: ...
Default Assumptions: ...
Preference Application: ...
Feedback Adjustment: ...
Strategy Gate: ...
Business Priority: ...
Output Length: ...
Choice Rationale: ...
Recommended execution version (English-compatible)
/goal ...
```

Keep this section compact. It exists to expose judgment, not to create another
long report.
