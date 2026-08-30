# China scarce-platform follow-up audit — 2026-08-30

Scope: one bounded public Google query per scarce platform (36Kr, OSChina,
Toutiao), plus one Bing retry and one Google pagination check. Existing
`candidates.json` and `review_queue.json` URL/ID sets were checked before
opening any result. No candidate shard or shared ledger was modified because
no result satisfied the independent Pi-original gate.

## Decisions

- 36Kr `3848341689685254` was fully read but is the 36Kr authorized copy of the
  accepted InfoQ RCA transcript. It is not a second original object.
- OSChina `19471470` was fully read as an IMClaw/ACP gateway article with Pi as
  one of many Agent targets; the repository already records this IMClaw
  syndication as excluded. `19675310` returned the native not-found page.
- Toutiao `7672638408224670242` was fully read, but its distinctive
  99.93%/0.028 DeepSeek-Composio benchmark narrative is the same cache/
  benchmark cluster represented by the accepted 36Kr object; it was excluded
  conservatively. `7673706027698635316` is DeepSeek-Harness-primary and says
  the product did not adopt Pi architecture, so Pi is not the article's
  primary object. Other visible hits were roundup/list pages, known objects,
  or a native 404.
- Bing pagination reached a verification interstitial and Google pagination
  reached an abnormal-traffic interstitial. Both routes were stopped without
  solving a challenge or changing identity.

Machine-readable probe details are in
`china-scarce-followup2-20260830-probes.jsonl`. `agent-reach` was not installed
or upgraded; the executable was unavailable in this shell, so the repository
acceptance protocol and ordinary browser routes were used.
