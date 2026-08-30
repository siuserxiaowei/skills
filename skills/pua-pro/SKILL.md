---
name: pua-pro
description: Turn verified task outcomes into reusable execution lessons, baselines, and anti-regression controls when the user explicitly asks for PUA Pro, self-improvement, retrospective learning, or continuity across work sessions.
license: MIT
---

# Verified learning and continuity

Convert evidence from real work into reusable guidance. Do not claim autonomous self-improvement from conversation alone.

## Inputs and Preconditions

Require a completed or materially informative work episode, direct evidence of what changed the outcome, an intended reuse scope, and an authorized destination if anything will be persisted. Separate repository facts from transient environment details and secrets. A conversation summary or a single successful guess is not enough to establish a reusable rule.

Read [references/examples.md](references/examples.md) only when deciding whether a lesson is mature enough to persist, handling a contradicted lesson, or forward-testing this mode.

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

If later evidence contradicts a stored lesson, mark it superseded or narrow its scope with a reason and date; do not silently rewrite provenance. Accept a reusable lesson only when its evidence is traceable, its counterexample is stated, sensitive data is excluded, its storage was authorized, and the associated control can be observed or tested.
