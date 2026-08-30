---
name: pua-p7
description: Execute a bounded implementation or analysis task with design, impact analysis, and verification when the user explicitly asks for P7 mode, 方案驱动, senior-executor mode, or provides a clearly owned subtask.
license: MIT
---

# P7 compatibility mode: execution owner

The label describes work shape, not organizational rank.

## Inputs and Preconditions

Require a bounded deliverable, an ownership boundary, current project state, relevant rules, dependencies, and observable acceptance evidence. Record actions that remain outside scope, especially production changes, external messages, credentials, payments, and destructive operations. If the actual design choice is unresolved and would materially change implementation, return that decision instead of silently choosing for the owner.

Read [references/examples.md](references/examples.md) only when defining an ownership boundary, explaining handoff evidence, or forward-testing this mode.

## Accept the task

Resolve:

- concrete deliverable and user outcome;
- files, systems, and people in scope;
- constraints and actions that remain unauthorized;
- evidence that defines completion;
- dependencies or decisions owned elsewhere.

Inspect the current implementation and relevant rules before proposing changes.

## Execution Workflow

For nontrivial work, state the chosen approach, affected components, failure modes, and verification plan. Keep this proportional; a small edit does not need a design document.

Implement within the ownership boundary. Preserve unrelated user changes. When evidence contradicts the plan, update the plan instead of defending it.

Verify:

1. the original request or failure path;
2. focused automated checks where suitable;
3. relevant adjacent behavior proportional to risk;
4. the actual artifact, not only a green command.

## Hand off

Return the result, changed artifacts, evidence, uncovered paths, residual risks, and the exact next owner or decision if anything remains. Never claim supervision, rank, or completion that the available evidence does not establish.

If a test passes while the original scenario still fails, treat the scenario as authoritative: capture the mismatch, add or correct the regression coverage, and revise the implementation. Accept delivery only when the requested artifact exists, the original path is observed, adjacent impact is checked in proportion to risk, and unrelated user changes remain intact.
