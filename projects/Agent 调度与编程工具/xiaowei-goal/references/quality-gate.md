# Quality Gate

Use this reference for research goals that produce market, competitor, product,
SEO, growth, or implementation judgments.

## Required Quality Gate

Every research goal should include a `质量门槛` field with these rules:

- every key conclusion should have at least 2 independent supporting sources
- if a conclusion has fewer than 2 sources, mark it as `低置信度` or `假设`
- source strength must be labeled as `强`, `中`, or `弱`
- outdated, promotional, inaccessible, anonymous, or non-primary sources must be downgraded
- contradictions must be listed instead of smoothed over
- claims that affect pricing, legal/compliance, health, finance, minors, privacy, or production data need explicit human confirmation

## Source Strength

| Strength | Source type | Use |
|---|---|---|
| 强 | official docs, pricing pages, product pages, public repository/code, app store listing, primary data, first-party announcement | Can support factual claims when current and directly visible |
| 中 | user reviews, forum discussions, public social posts, interviews, comparison pages, technical blogs | Useful for patterns, pain points, objections, and hypotheses |
| 弱 | promotional posts, SEO listicles, unattributed summaries, inaccessible pages, stale screenshots, single anecdotes | Only use as weak signal or discard |

## Downgrade Rules

Downgrade a source when it is:

- outdated for the decision, especially pricing, product capability, laws, or APIs
- clearly promotional or affiliate-driven
- inaccessible, partially visible, login-only, paywalled, or based on snippets only
- a duplicate of another source
- not directly relevant to the user's business, geography, platform, audience, or use case

## Required Tables

Add these columns to research evidence when possible:

```text
关键结论 | 支撑来源数量 | 独立来源 | 来源强弱 | 反例/矛盾 | 置信度 | 是否需要人工确认
```

Use this decision rule:

- `高置信度`: at least 2 strong or medium independent sources, no serious contradiction
- `中置信度`: 2 sources but mixed strength, partial contradiction, or limited context
- `低置信度`: 1 source, weak sources, inaccessible evidence, or unresolved contradiction

## Stop And Pause

Do not finish a research brief while key conclusions lack evidence labels. Before finalizing, either add sources, downgrade the conclusion, or mark the decision as requiring human confirmation.
