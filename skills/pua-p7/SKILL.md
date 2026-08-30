---
name: pua-p7
description: Execute a bounded implementation or analysis task with design, impact analysis, and verification when the user explicitly asks for P7 mode, 方案驱动, senior-executor mode, or provides a clearly owned subtask.
license: MIT
---

# P7 compatibility mode: execution owner

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

The label describes work shape, not organizational rank.

## Accept the task

Resolve:

- concrete deliverable and user outcome;
- files, systems, and people in scope;
- constraints and actions that remain unauthorized;
- evidence that defines completion;
- dependencies or decisions owned elsewhere.

Inspect the current implementation and relevant rules before proposing changes.

## Execute

For nontrivial work, state the chosen approach, affected components, failure modes, and verification plan. Keep this proportional; a small edit does not need a design document.

Implement within the ownership boundary. Preserve unrelated user changes. When evidence contradicts the plan, update the plan instead of defending it.

Verify:

1. the original request or failure path;
2. focused automated checks where suitable;
3. relevant adjacent behavior proportional to risk;
4. the actual artifact, not only a green command.

## Hand off

Return the result, changed artifacts, evidence, uncovered paths, residual risks, and the exact next owner or decision if anything remains. Never claim supervision, rank, or completion that the available evidence does not establish.
