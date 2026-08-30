---
name: goal-meta-skill
description: Turn a long-running Codex request into one durable, evidence-verifiable goal. Use when the user asks to create, refine, review, or troubleshoot a Codex Goal or `/goal` instruction; do not use for ordinary one-turn prompts.
---

# Goal Meta Skill

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Design the smallest durable contract that still preserves the user's full intended outcome.

## Establish the Goal

1. Recover the real end state from the request and available project evidence. Write what must become true, not a list of activities.
2. Identify the evidence that would prove the whole result. Match the evidence scope to the outcome scope; a narrow check cannot prove a broad claim.
3. Preserve explicit requirements, named deliverables, constraints, permissions, and external-state dependencies. Do not silently turn a large goal into an easier milestone.
4. Ask only when a missing choice materially changes product direction, external impact, cost, ownership, or risk. Otherwise state a conservative assumption in the goal.
5. Produce one paste-ready `/goal` instruction in the user's language unless the user asks for analysis, alternatives, or another format.

Use [references/goal-design.md](references/goal-design.md) when the request is vague, risky, multi-system, or difficult to verify.

## Write an Executable Contract

The instruction should normally make these ideas clear in natural language:

- **Outcome:** the observable state to achieve.
- **Evidence:** tests, artifacts, runtime behavior, external records, or review criteria that prove it.
- **Invariants:** behavior, data, interfaces, attribution, or user work that must remain intact.
- **Authority:** what may be changed and which external, destructive, paid, public, or permission-changing actions still require authorization.
- **Persistence:** how to use new evidence after failure without retrying the same assumption indefinitely.
- **Terminal states:** what proves completion, and what constitutes a genuine human or external blocker.

These are design dimensions, not mandatory Codex field names. Do not claim that a fixed label set, bilingual mirror, numbered questionnaire, or exact prose template is required by the product.

## Product Semantics

- A Goal is for persistent work that benefits from repeated execution and verification. Keep simple answers and obvious one-step tasks as ordinary prompts.
- Set a token budget only when the user explicitly requests one. Never invent a budget as a productivity tactic.
- Do not replace an unfinished goal merely to rephrase it. If a goal is already active, refine it only through the product's supported flow or explain the conflict.
- Do not encode new authorization inside the goal. A request to keep working does not authorize publication, deletion, payment, credential use, production changes, or other unrelated high-impact actions.
- Treat schedules, indexing, approvals, third-party responses, and other external state as real dependencies. Never turn elapsed effort or repeated polling into evidence of success.

Read [references/research-basis.md](references/research-basis.md) when checking product assumptions or updating this Skill for a new Codex release.

## Check the Draft

For a saved draft, run:

```bash
python3 scripts/check_goal.py path/to/goal.txt
```

Use `--format json` for automation and `--strict` when warnings should fail CI. The checker detects structural omissions and risky contradictions; it cannot decide whether the proposed outcome is the right business decision.

Before returning the draft, confirm that:

- every explicit deliverable remains in scope;
- evidence proves the requested end state rather than a convenient subset;
- placeholders and vague completion claims are gone;
- risky actions retain their real authorization boundary;
- completion and blocking are both grounded in authoritative state.
