# Research basis

The suite uses the following primary and first-party sources as design constraints, not as text templates.

## Agent execution

- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) recommends simple composable patterns, clear gates, and evaluator-optimizer loops when criteria are explicit and iteration produces measurable value.
- [Anthropic: Trustworthy agents in practice](https://www.anthropic.com/research/trustworthy-agents) describes useful agents as plan-act-observe loops that retain meaningful human control over tools and consequential actions.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) emphasizes evaluating whether an agent avoided damage, followed the request, and produced a good result rather than relying on a single superficial metric.

## Failure learning

- [Google SRE: Effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) uses system state, telemetry, hypotheses, and confirming or disconfirming experiments to identify causes.
- [Google SRE: Postmortem culture](https://sre.google/sre-book/postmortem-culture/) treats failure analysis as a blameless search for contributing system causes and preventive actions, not punishment.

## Feedback and team conditions

- [Google re:Work: Understand team effectiveness](https://rework.withgoogle.com/en/guides/understanding-team-effectiveness) identifies psychological safety, dependability, structure, clarity, meaning, and impact as important team dynamics.
- [APA: Psychological safety in the changing workplace](https://www.apa.org/pubs/reports/work-in-america/2024/psychological-safety) reports associations between psychological safety and opportunities for feedback, decision participation, job satisfaction, and lower burnout.
- [Self-Determination Theory overview](https://selfdeterminationtheory.org/theory/) grounds motivation in autonomy, competence, and relatedness; feedback should support competence without controlling or humiliating the recipient.

These sources support clear goals, observable feedback, bounded iteration, autonomy, and learning from failure. They do not support shame, fabricated performance threats, infinite retries, or removal of human control.
