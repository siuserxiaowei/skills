---
name: agent-task-spec
description: >
  Turn vague requests, rough ideas, or existing prompts into explicit, executable
  task specifications for AI agents. Use when the user wants to brief Codex,
  Claude Code, ChatGPT agents, subagents, or another AI worker; asks to write,
  expand, refine, audit, or rewrite an agent prompt/spec/task brief/handoff;
  says "帮我把需求跟 agent 说清楚", "派任务", "扩写需求", "优化 prompt", "审查这段需求",
  "写成 spec", "托管执行", "接管", "直接帮我操作", "派子智能体", "主 Agent",
  "自主执行等级", or "autonomy level";
  or gives a broad request that needs clearer goals, context, boundaries, output
  format, false-completion warnings, verification, delegation policy, and safe
  execution boundaries before an agent should act.
---

# Agent Task Spec

Convert fuzzy intentions into task briefs that an AI agent can execute independently. Do not merely make the prompt longer; make the work observable, bounded, and verifiable.

## Choose A Mode

Pick the lightest mode that fits the user request.

- **Expand mode**: Use when the user gives a rough one-liner or vague idea. Produce a complete, copy-ready task spec. Make reasonable assumptions and label them.
- **Interview mode**: Use when missing information would change the direction, risk, or deliverable. Ask 1-3 high-leverage questions before writing the final spec.
- **Review mode**: Use when the user provides an existing prompt, task brief, PRD, or handoff. Diagnose gaps first, then provide a revised version.
- **Managed Execution mode**: Use when the user wants an agent to take over more work, operate tools, run commands, edit files, research, validate, or coordinate subagents after the task is clarified. Produce a task spec plus an execution contract the current or next agent can follow directly.

When unsure, default to Expand mode with a short "Assumptions" section. Do not ask questions just to fill every template field.

## Core Workflow

1. Identify the real job behind the request.
   - Name the audience, user, stakeholder, or system affected by the work.
   - State the problem, blockage, decision, or desired state.
   - Convert adjectives such as "高级", "有深度", "完整", "优化", "better", or "polished" into concrete outcomes.

2. Gather only useful context.
   - Include files, links, data, prior decisions, rejected options, examples, and stale assumptions when relevant.
   - Separate facts from assumptions.
   - Mark anything that must be verified before being treated as true.

3. Draw the action boundary.
   - State what the agent may do directly.
   - State what the agent must not do.
   - State what requires user confirmation first.
   - Add a "stop if" condition when the agent could otherwise continue in a risky direction.

4. Define real completion.
   - Describe what must be true at the end.
   - Add false-completion warnings specific to the task type.
   - Require evidence: tests, command output, screenshots, citations, reviewed rows, examples, diffs, or manual acceptance checks.

5. Produce the final brief in the user's language unless they ask otherwise.
   - If the user wants to hand it to another agent, output a copy-ready prompt.
   - If the user wants this agent to execute the work now, do not stop after producing the spec. Use the brief as the working contract and begin execution immediately unless a pause rule is triggered.
   - If using Managed Execution mode, make the autonomy level, risky-action pause rules, delegation policy, verification evidence, and stop conditions explicit before acting.

## Managed Execution Mode

Use this mode for broad tasks where the user wants the agent to do more than write advice. The goal is controlled autonomy: the agent should keep moving, but not cross risky boundaries silently.

Default operating contract:

- First convert the user's request into a concrete outcome, constraints, write boundaries, and verification checks.
- Act directly when the action is low risk: read files, inspect docs, search public sources, run local commands, edit scoped files, start local dev servers, create local artifacts, and rerun checks.
- Ask first before account creation, paid services, production changes, deleting user data, irreversible operations, credentials, private data export, legal/medical/financial decisions, or broad repo/system rewrites.
- Prefer doing the immediate blocking work locally. Delegate only sidecar work that can run independently while the main agent continues useful progress.
- Use subagents only when the task naturally splits into independent domains. Assign each subagent a concrete scope, expected output, and disjoint write ownership. Do not spawn subagents merely to appear thorough.
- The main agent owns final judgment: review subagent output, integrate or reject it, run verification, and report what is proven, uncertain, or still blocked.
- After failures, inspect logs or evidence before retrying. Make at most 3 focused repair rounds unless new evidence justifies continuing.

Autonomy levels:

- **L1 Spec only**: Clarify the request and produce a task spec. Do not execute.
- **L2 Read and research**: Read local files, inspect docs, search public sources, and propose the execution plan. Do not edit files.
- **L3 Local execution**: Run local commands, edit scoped local files, create local artifacts, and verify results.
- **L4 Delegated execution**: Do L3 work and coordinate subagents for independent sidecar tasks with disjoint write scopes.
- **L5 Pause required**: Stop and ask before credentials, accounts, payments, production systems, destructive actions, public publishing, private data export, legal/medical/financial judgment, or broad unrelated rewrites.

If the user does not specify a level, choose the safest level that still matches their wording. Phrases like "直接帮我操作", "接管", "托管执行", or "按 spec 执行" usually imply L3. Mention L4 only when independent subagent work is truly useful.

Subagent dispatch template:

```markdown
Subagent task:
- Objective:
- Scope:
- Files/modules owned:
- Must not touch:
- Inputs to inspect:
- Expected output:
- Verification to run:
- Return format:
```

Each subagent brief must be self-contained. Give subagents one narrow domain, name the files or modules they own when editing, and tell them not to revert or overwrite work outside their scope. The main agent must review their output before treating it as true.

Managed Execution output should include:

```markdown
## Execution Contract
Autonomy level: L1/L2/L3/L4/L5 and what the agent may do without asking.
Delegation policy: when to use subagents, how to split ownership, and when not to delegate.
Pause rules: actions that require user confirmation.
Verification evidence: commands, screenshots, citations, diffs, or manual checks required before completion.
Completion rule: what must be proven before the agent can say it is done.
```

## Scenario Presets

Use these presets to add task-specific boundaries and verification. Combine presets when a task crosses domains.

### Coding Or Automation

Emphasize:
- Target files/modules and areas that are out of scope.
- Whether new dependencies, migrations, broad refactors, generated files, or formatting churn are allowed.
- Required commands, test scope, fixtures, and manual checks.
- Compatibility, rollback, and data-loss concerns.

False completion:
- Tests pass but do not cover the changed behavior.
- The happy path works but edge cases, errors, loading states, or empty states are untested.
- The patch solves the example while breaking an existing contract.
- The agent claims verification without command output or concrete checked behavior.
- The agent produces a plan but does not execute even though the user asked for execution.
- Subagent output is accepted without main-agent review and verification.

### Content Or Copywriting

Emphasize:
- Target reader, reader pain, desired belief change, and distribution channel.
- Core argument, must-include points, forbidden angles, and voice.
- Source of examples: real user context, provided notes, public sources, or clearly labeled hypotheticals.

False completion:
- The structure is complete but the piece has no judgment.
- The writing is fluent but generic.
- The agent invents experience, data, quotes, or audience insight.
- The ending summarizes but does not land the intended takeaway.

### Research Or Competitive Analysis

Emphasize:
- Research question, decision the research should support, freshness requirements, and source hierarchy.
- Required citations, date ranges, competitors, comparison dimensions, and uncertainty labels.
- Whether recommendations are expected or only findings.

False completion:
- Many facts are listed but no synthesis or decision support is provided.
- Claims lack source links or dates.
- Unverified information is written as fact.
- The comparison dimensions do not match the user's decision.

### Product, Growth, Or Ops

Emphasize:
- Target user segment, current journey, desired behavior, business metric, and constraints.
- Required states: normal path, edge cases, empty states, permissions, errors, analytics, and ownership.
- Tradeoffs, priority, rollout, and measurement plan.

False completion:
- The plan names features but not user behavior or success metrics.
- It ignores attribution, instrumentation, or review cadence.
- It covers the intended path but not failure states.
- It gives a backlog without priority or rationale.

### Design Or Frontend Experience

Emphasize:
- User job, information hierarchy, density, interaction states, accessibility, and responsive behavior.
- Existing design system, visual references, brand constraints, and content that must fit.
- Required screenshots or viewport checks when implementation is involved.

False completion:
- The UI looks polished but key controls do not work.
- Desktop works but mobile, overflow, long text, hover/focus, or empty states fail.
- Visual style is changed without respecting the product context.
- The agent describes the design instead of delivering the experience.

## Spec Template

Use this structure by default. Omit sections only when they are truly irrelevant.

```markdown
# Agent Task Spec

## Mode
Expand / Interview / Review / Managed Execution

## Background
Why this work matters now, what has already happened, and what the agent should know before acting.

## Goal
The concrete outcome to produce, including whose problem it solves and what state should be true afterward.

## Assumptions
- Assumption 1
- Assumption 2

## Success Criteria
- Observable result 1
- Observable result 2
- Observable result 3

## Context And Sources
- Files, docs, links, data, previous discussions, or examples to inspect
- Known rejected approaches or stale assumptions
- Information that must be verified before being treated as fact

## Available Tools And Actions
- What the agent may read, search, run, edit, create, or call
- Any preferred local commands, APIs, frameworks, or workflows

## Execution Contract
- Autonomy level:
- Delegation policy:
- Pause rules:
- Retry policy:

## Boundaries
- Can do:
- Do not do:
- Ask first before:
- Stop if:

## False Completion Warnings
- Task-specific case 1
- Task-specific case 2
- Task-specific case 3

## Output Format
The exact deliverable: patch, doc, table, checklist, analysis, code, message draft, dashboard, etc.

## Verification
How the user or agent should check the result, including tests, review steps, citations, screenshots, or acceptance checks.
```

## Compact Version

For small tasks, use:

```markdown
Task:
Context:
Assumptions:
Must include:
Must avoid:
Allowed actions:
Autonomy level:
Delegation:
Ask first before:
Done means:
Not done if:
Output:
Verification:
```

## Review Mode Output

When reviewing an existing prompt or spec, use this shape:

```markdown
## Gaps
- Missing or vague goal:
- Missing context:
- Missing boundary:
- Missing success criterion:
- Missing verification:

## Risk
What the agent might do wrong if this prompt is used as-is.

## Revised Agent Task Spec
[Provide the improved copy-ready version.]
```

## Examples

### Example 1: Coding

Input:
```text
帮我优化一下 dashboard 新手引导。
```

Better task direction:
```markdown
Goal: Improve dashboard onboarding so new users can reach first API key creation and first successful call with less confusion.
Boundaries: Inspect the dashboard onboarding flow and analytics events. Do not change billing, auth, database schema, or install dependencies without confirmation.
False completion: A prettier onboarding panel is not enough if key actions, empty states, event attribution, and verification are not addressed.
Verification: Name the changed files, run relevant tests or type checks, and list the onboarding paths manually checked.
```

### Example 2: Content

Input:
```text
帮我写一篇有深度的 AI 产品文章。
```

Better task direction:
```markdown
Goal: Write for product/growth people who already use AI but struggle to turn vague ideas into executable agent work.
Must include: 2-3 concrete points, each grounded in a work scenario.
Must avoid: Prompt-tip listicles, generic AI news commentary, invented personal stories, and motivational filler.
False completion: A polished structure without a sharp argument does not count.
Verification: The final piece should make the reader change one behavior before assigning work to an agent.
```

### Example 3: Research

Input:
```text
帮我做一个完整的竞品分析。
```

Better task direction:
```markdown
Goal: Compare the competitors only on dimensions that support the user's decision.
Context needed: Product category, target customer, competitor list, buying/use-case decision, and freshness requirements.
Boundaries: Use cited public sources. Do not invent pricing, customer counts, roadmap claims, or private metrics.
False completion: A large comparison table without synthesis, confidence levels, and recommendation does not count.
Verification: Every factual claim that could change the conclusion needs a source and access date.
```

### Example 4: Managed Execution

Input:
```text
以后这种任务你直接接管，能拆就拆，能操作就操作，不要每步都问我。
```

Better task direction:
```markdown
Mode: Managed Execution
Goal: Complete the requested outcome end to end, not merely propose a plan.
Allowed actions: Inspect relevant files and docs, run local commands, edit scoped files, start local services, search public sources, and verify results with concrete evidence.
Delegation policy: Split into subagents only when there are independent modules or research questions. Give each subagent a narrow scope and disjoint write ownership. The main agent keeps the critical path, reviews outputs, and performs final verification.
Ask first before: Credentials, paid services, production data, destructive operations, public publishing, privacy-sensitive data, or broad unrelated rewrites.
False completion: A plan, partial implementation, unreviewed subagent output, or unverified "looks done" summary does not count.
Verification: Report changed files, command outputs, runtime checks, source links, screenshots, or acceptance checks that prove the result.
```

### Example 5: Subagent Brief

Input:
```text
这个任务可以拆给几个子智能体并行做，但不要让他们互相改同一批文件。
```

Better task direction:
```markdown
Delegation policy: Use subagents only for independent modules. Keep the critical path in the main agent. Assign disjoint ownership before dispatch.

Subagent task:
- Objective: Audit README examples for clarity and missing setup steps.
- Scope: README.md only.
- Files/modules owned: README.md.
- Must not touch: SKILL.md, agents/openai.yaml, repo settings, git history.
- Inputs to inspect: Current README.md and any local usage examples named in the task.
- Expected output: A concise list of proposed README edits plus any direct patch if asked.
- Verification to run: Markdown renders without broken fenced blocks; examples match current skill modes.
- Return format: Changed files, summary, verification, remaining risks.
```

## Quality Check

Before handing off the spec, confirm:

- A capable agent would know why the task matters, not only what to produce.
- The spec says what matters more than what is merely nice to have.
- Scope boundaries are explicit enough to prevent unwanted edits, claims, or tool use.
- The autonomy level is explicit enough that the agent can keep moving without asking about every safe action.
- Delegation is justified by independent work, not by a desire to use more agents.
- Any subagent brief has objective, scope, owned files, forbidden files, expected output, and verification.
- Completion cannot be faked by a polished but shallow answer.
- Verification is independent enough that the user is not relying only on the agent's self-assessment.
- The final brief is short enough to use and specific enough to constrain action.

## Source Note

This skill is distilled from the workflow ideas in the WeChat article "AI 时代，如何把需求跟 Agent 说清楚" by 李乐意AI实战, adapted into a reusable agent-briefing procedure.
