# Goal Design Guide

Use this guide only when a durable goal needs more than a straightforward outcome and success check.

## 1. Recover the Contract

Build a private design table before drafting:

| Dimension | Question | Weak substitute to avoid |
|---|---|---|
| Outcome | What observable state should exist at the end? | “work on”, “research”, “improve” |
| Coverage | Which named requirements and deliverables must remain? | one easy milestone |
| Evidence | What authoritative state proves each requirement? | confidence, effort, or a narrow smoke test |
| Invariants | What must remain compatible or untouched? | “be careful” |
| Authority | Which actions are already authorized? | assuming persistence expands permission |
| Dependencies | Which facts depend on people, time, services, or credentials? | pretending local work controls external state |
| Stop | What evidence proves there is no required work left? | “looks good” |
| Block | Which specific unavailable input or external state prevents meaningful progress? | difficulty or uncertainty |

Do not expose the table unless it helps the user review the goal.

## 2. Choose Evidence by Deliverable

- **Code or configuration:** relevant tests, build/type checks, runtime behavior, diff review, and migration or rollback evidence when applicable.
- **User interface:** functional checks plus representative viewport screenshots or interaction evidence. A screenshot alone does not prove behavior.
- **Research:** a defined question set, source coverage, dates, primary-source preference, conflict handling, and a usable synthesis artifact.
- **Data:** source identity, row/count reconciliation, schema and type checks, transformations, exceptions, and output integrity.
- **Documents or media:** required sections, factual checks, render/open verification, and format-specific review.
- **External publication or mutation:** exact target, visibility/audience, authorization, remote confirmation, and a post-action readback.
- **Monitoring:** a live handle or authoritative remote state, a polling cadence, an event condition, and a bounded reporting policy.

When the repository exposes commands, name them only after inspection. Otherwise instruct Codex to discover project-provided checks before inventing new ones.

## 3. Control Ambiguity

Choose a default when the uncertainty is reversible, local, low-cost, and unlikely to change the product direction. State it as an assumption that evidence may overturn.

Ask before drafting when the choice changes any of these:

- the external target, audience, account, or visibility;
- payment, budget, legal obligations, ownership, or licensing;
- destructive or hard-to-reverse changes;
- production data, credentials, permissions, or privacy exposure;
- the central deliverable or intended user.

Do not force a questionnaire merely because the request is short. One precise question is better than a generic form.

## 4. Define Persistence Without Infinite Retry

A useful goal tells the agent to:

1. inspect authoritative state;
2. form a testable hypothesis or focused work item;
3. make one bounded attempt;
4. gather new evidence;
5. update the next action;
6. stop only when the full completion contract is proved.

Repeated failure is not itself a blocker. Require a different evidence source or strategy before repeating the same action. A real blocker names the unavailable decision, permission, credential, dependency, or external state and explains why no safe in-scope alternative remains.

## 5. Draft Naturally

A strong goal can be one cohesive paragraph. Labels may improve readability, but they are not the product API.

Example:

```text
/goal Fix the checkout coupon defect so percentage coupons apply exactly once while fixed-value coupons and gift-card credit retain their documented behavior. Preserve the public coupon API and stored order schema. Prove the fix with a regression test that fails on the current behavior, the smallest relevant checkout suite, and the repository's existing lint/type checks; inspect the final diff for unrelated changes. Work only in checkout pricing logic, its tests, and directly required fixtures. Use new test or runtime evidence after a failed attempt instead of repeating the same hypothesis. Finish only when every named behavior is proved and no required check is missing; pause if the correct stacking rule requires a product decision, production data, payment credentials, or a schema migration.
```

The example illustrates coverage and evidence. Adapt the contract to the actual request instead of copying its wording.
