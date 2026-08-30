---
name: pua-pro
description: Turn verified task outcomes into reusable execution lessons, baselines, and anti-regression controls when the user explicitly asks for PUA Pro, self-improvement, retrospective learning, or continuity across work sessions.
license: MIT
---

# Verified learning and continuity

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Convert evidence from real work into reusable guidance. Do not claim autonomous self-improvement from conversation alone.

## Extract a lesson

After a material success or failure, record:

- context and requested outcome;
- observed failure or opportunity;
- evidence that identified the cause;
- action that changed the result;
- verification evidence;
- scope where the lesson applies;
- counterexample or condition where it should not apply;
- smallest reusable control: test, check, template, script, or decision rule.

Promote a lesson to a default only after it recurs in meaningfully similar tasks or a strong invariant justifies it. Prefer a narrow correction over adding a universal rule for one anecdote.

## Persist deliberately

Read or write memory only when the user requests persistence or the active environment already provides an authorized memory mechanism. Use the user-specified project location; otherwise propose a local project file before writing. Do not silently create or update home-directory profiles, hooks, global configuration, performance scores, or identity files.

When resuming, verify saved state against the current repository, process, branch, or external tool. A note that says work was running is not proof that it remains live.

## Report

Return the learned rule, supporting evidence, applicability boundary, control added, and remaining uncertainty. Distinguish a proposed lesson from a verified reusable pattern.
