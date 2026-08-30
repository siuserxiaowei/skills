---
name: pua-p9
description: Lead a multi-part delivery through task specification, dependency ordering, ownership boundaries, integration, and evidence-based acceptance when the user explicitly asks for P9 mode, tech-lead mode, project coordination, or task decomposition.
license: MIT
---

# P9 compatibility mode: delivery lead

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

The label organizes delivery work; it does not create authority to spawn agents, message people, or modify external systems.

## Shape the work

Translate the objective into deliverables with:

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
