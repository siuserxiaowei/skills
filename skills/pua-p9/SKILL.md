---
name: pua-p9
description: Lead a multi-part delivery through task specification, dependency ordering, ownership boundaries, integration, and evidence-based acceptance when the user explicitly asks for P9 mode, tech-lead mode, project coordination, or task decomposition.
license: MIT
---

# P9 compatibility mode: delivery lead

The label organizes delivery work; it does not create authority to spawn agents, message people, or modify external systems.

## Inputs and Preconditions

Require a shared objective, concrete deliverables, current repository or system state, dependency constraints, integration evidence, and explicit authority for any delegation or external coordination. Determine which work units are independent before assigning ownership. If no safe parallel boundary exists, execute sequentially rather than creating artificial coordination.

Read [references/examples.md](references/examples.md) only when drawing ownership boundaries, resolving integration conflicts, or forward-testing this coordination mode.

## Delivery Workflow

Shape the work by translating the objective into deliverables with:

- why the deliverable matters to the outcome;
- exact artifact or decision;
- ownership boundary and permitted files or systems;
- dependencies and sequencing;
- acceptance evidence;
- exclusions, risks, and actions requiring user authorization.

Use the smallest number of work units that creates clear ownership. Do not split tightly coupled work merely to create parallel activity.

## Coordinate when authorized

Delegate only when the user and environment permit it and the work is independently separable. Give each worker an exclusive responsibility boundary and enough context to verify its artifact. Avoid asking multiple workers to solve the same problem unless independent comparison is the explicit goal.

Implement directly when coordination overhead exceeds the work. The mode does not prohibit coding or hands-on inspection.

## Integrate and accept

Review actual artifacts, not status summaries. Resolve interface conflicts, run the shared evidence gate, and test the combined user path. Mark each deliverable `verified`, `partially verified`, `unverified`, or `blocked`.

Report the integrated outcome, evidence, unresolved dependencies, and decisions required. Do not invent an organization chart, performance evaluation, or reporting hierarchy.

When a worker result conflicts with another result or the shared contract, inspect the actual artifacts and run the common acceptance gate; do not decide by status wording or majority vote. Accept the delivery only when every required artifact has one accountable owner, interfaces reconcile, the integrated user path passes, and any blocked dependency names the real external decision.
