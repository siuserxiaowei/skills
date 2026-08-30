# Delivery reality review

Use this when status language, dashboards, meetings, or progress reports may be getting confused with the real outcome.

## Separate the layers

1. **Requested outcome:** what changed for the user or system?
2. **Artifact:** what file, deployment, decision, message, or dataset now exists?
3. **Evidence:** what test, trace, screenshot, query, or primary source demonstrates the outcome?
4. **Reporting:** how is the result summarized for stakeholders?

Reporting cannot substitute for the first three layers. A metric is useful only when its definition, denominator, time window, environment, and relationship to the outcome are clear.

## Status vocabulary

- `planned`: work is scoped but not started.
- `in-progress`: an identified action is currently underway.
- `candidate`: an artifact exists but has not passed the agreed evidence gate.
- `verified`: the evidence gate passes for the stated scope.
- `partially-verified`: explicitly named paths remain unchecked.
- `blocked`: a named external condition prevents the next material action.

Never change a metric definition or success criterion solely to make the status look better. Preserve the old definition, explain the mismatch, and propose a separate metric when the old one no longer serves the decision.

## Output

For a disputed delivery, report: outcome, artifact, evidence, status, uncovered scope, and next decision. Quote stakeholder feedback accurately but treat it as an input to investigate, not proof of either success or failure.
