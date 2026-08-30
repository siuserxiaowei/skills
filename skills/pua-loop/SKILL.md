---
name: pua-loop
description: Run a bounded evaluator-optimizer loop with explicit evidence, budgets, pause conditions, and human-control boundaries only when the user explicitly asks for loop, repeated iteration, or automated refinement mode.
license: MIT
---

# Bounded evidence loop

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Use iteration only when the outcome has a meaningful evaluator and repeated refinement can improve it. A loop is not a substitute for missing product intent or authorization.

## Define the loop contract

Before starting, record:

- the task and immutable completion criterion;
- the evaluator: command, test, rubric, or observable state;
- the working boundary and permitted side effects;
- an iteration, elapsed-time, cost, and risk budget appropriate to the task;
- pause, cancellation, and escalation conditions.

If the user supplies a verification command, preserve it exactly unless the user changes it. Resolve its working directory and prerequisites before relying on it. Do not infer a command that creates external side effects.

## Iterate

For each iteration:

1. Read the current artifact and the previous evaluator result.
2. State one hypothesis about the largest remaining gap.
3. Make the smallest change that tests or improves that gap.
4. Run the evaluator and capture exit status plus material output.
5. Keep the change only when evidence improves or it yields useful new information.
6. Record the result so the next iteration does not repeat the same failed assumption.

After the same failure signature appears twice, stop parameter variations and reframe the hypothesis. Do not restart a confirmed live process merely because observation timed out.

## Stop or pause

Stop when the evaluator passes and a proportionate regression check succeeds. Pause or return control when:

- the agreed budget is exhausted;
- the user pauses or cancels;
- the next action needs new credentials, authority, payment, publication, deletion, or a material product decision;
- the evaluator is invalid, unstable, or can be gamed by changing the artifact away from the user's goal;
- further iterations no longer produce new evidence.

Never default to an infinite loop. Do not suppress a necessary user question or continue consequential external actions solely because “loop mode” is active.

## State and reporting

Store state only inside the user-approved workspace and only when persistence is useful. Record iteration, hypothesis, change, evaluator result, remaining budget, artifact revision, and next action. Do not write to a home-directory profile or global hook configuration without explicit authorization.

On exit, report the final artifact, evaluator evidence, iterations used, remaining uncertainty, and whether the result is `verified`, `partially verified`, `unverified`, or `blocked`.
