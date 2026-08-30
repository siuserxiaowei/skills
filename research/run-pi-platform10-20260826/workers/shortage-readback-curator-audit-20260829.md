# Shortage-platform readback audit

Run: `pi-platform10-20260826`
Checked: `2026-08-29` (Asia/Shanghai)
Scope: read-only audit of existing `workers/*readbacks*.jsonl`, joined to the
current `review_queue.json` and `candidates.json`. This artifact does **not**
promote rows or modify the shared candidate/ledger files.

## Method and evidence boundary

I enumerated all 43 existing `*readbacks*.jsonl` files and joined records by
`candidate_id`, then resolved platform and canonical URL from the queue/accepted
ledger when a readback overlay omitted those fields. The shortage-platform
scope was: `zhihu`, `weibo`, `toutiao`, `36kr`, `infoq`, `oschina`, `gitee`,
`product_hunt`, `arxiv_openreview`, `hackernoon`, `hashnode`, and `substack`.

The scan found 60 readback records representing 44 unique candidate IDs. There
were no malformed JSON lines and no missing platform identities. Most accepted
rows have multiple independent readback overlays; repeated overlays were
counted once by candidate ID. URL identity was checked after lower-casing host,
removing trailing slashes and dropping fragments. Content-cluster decisions use
the explicit prior audit records where available; no new page fetch was done.

Current snapshot at audit time: 468 queue items, 371 accepted items. Shortage
platform accepted counts were: 36Kr 4, arXiv/OpenReview 7, Gitee 2,
HackerNoon 3, Hashnode 1, InfoQ 3, OSCHINA 5, Product Hunt 1, Substack 9,
Toutiao 4, Weibo 3, Zhihu 2.

## Safe promotion candidates from existing readbacks

No unaccepted object in this scan is safe to promote without changing an
existing, explicit cluster/duplicate decision. In particular, the seemingly
strong rows below are already represented by accepted objects or are explicitly
excluded:

- `worker-cn-064` (InfoQ) has a complete anonymous canonical-body readback and
  is technically Pi-primary, but its URL is exactly the accepted
  `seed-infoq-42-coding-agents` object. The readback audit marks it as a
  duplicate/cluster representative; **do not promote**.
- `web-substack-nader-agent-stack` has a complete 47,766-character public body
  and is Pi-primary, but the article says it was originally posted on X and is
  already clustered with accepted `social-gap-x-dabit-agent-stack`;
  **do not promote**.
- `worker-global-078` (George Racu) and `worker-global-079` (Scaile Agency)
  each have complete public Substack API/HTML bodies, but their canonical URLs
  are already accepted as `seed-substack-47-pi-agent-vs-claude-code-code-review`
  and `seed-substack-48-pi-web-browse-web-ssrf`, respectively; **do not
  promote**.
- `web-hackernoon-subagents-built` is a complete Pi-primary HackerNoon article,
  but its same-author June 23/June 25 pair has approximately 79% bidirectional
  six-word-shingle overlap. The accepted `web-hackernoon-subagent-primitive-race`
  (June 25) is the retained series representative; **do not promote** the June
  23 row as a second quota item.

The exact machine-readable decisions are in
`shortage-readback-curator-decisions-20260829.jsonl`.

## Accepted rows confirmed as already accounted for

The following readback families are accepted and must not be re-promoted:

- **36Kr:** `worker-cn-081`, `worker-cn-083`, `worker-cn-084`, and
  `china-followup-36kr-3884083529658374-harness-pi` (all canonical bodies
  already accepted).
- **arXiv/OpenReview:** six accepted canonical papers, including the two
  supplemental papers and the exact-ID prompt-waste paper; `worker-global-083`
  is the exact SHarD URL already accepted and remains a duplicate.
- **Gitee:** `code-hosts-gitee-002` (Feynman root) and `worker-cn-086`
  (Feynman `RELEASES.md`) are accepted; the latter is a distinct release-note
  object under the same project, while `code-hosts-gitee-001` is an explicit
  upstream mirror and must remain rejected.
- **HackerNoon:** the SSH-extension, VT-theme, and June 25 subagent primitive
  stories are accepted; translated paths and the June 23 same-author story do
  not add independent objects.
- **Hashnode:** `web-hashnode-sohan-pi-internals` is the only accepted
  Pi-primary Hashnode object. The channels and Symphony pages are Pi-secondary;
  the two Gary Parker `pi-mono` titles are same-name false positives.
- **OSCHINA/Toutiao/Weibo/Zhihu:** all scanned rows are already accepted and
  therefore cannot be promoted again. Existing notes record cross-platform
  clusters (e.g. Toutiao/Linux.do, OSCHINA/DEV, and OSCHINA/SegmentFault).
- **Product Hunt:** `sparse-producthunt-pi-launch` is accepted; the `/reviews`
  sub-route is metadata-only and part of the same product object.
- **Substack:** all nine accepted rows have canonical readbacks. The only
  unaccepted rows are the three duplicate/cluster cases listed above.

## Exclusion and access decisions

The following queue/readback objects are explicitly non-promotable:

| Candidate | Decision | Evidence basis |
|---|---|---|
| `code-hosts-gitee-001` | reject upstream mirror | Gitee README says it synchronizes `github.com/earendil-works/pi`; not an independent original object. |
| `worker-global-083` | reject exact duplicate | arXiv `2607.25890v1` is the accepted SHarD URL/content cluster. |
| `web-hashnode-channels` | reject Pi-secondary | Full article is OpenClaw-focused; Pi Coding Agent is one comparison section. |
| `web-hashnode-symphony` | reject Pi-incidental | Symphony is the article subject; Pi appears as Kata CLI implementation context. |
| `web-hashnode-gary-tools` | reject same-name false positive | Body discusses generic LangChain/Playwright/Zod/Jest tooling, not the specified Pi runtime. |
| `web-hashnode-gary-components` | reject same-name false positive | Invented generic `@pi-mono`-style commands do not match earendil-works/pi. |
| `web-producthunt-reviews` | reject sub-route/metadata | Reviews are mutable user claims under the accepted Product Hunt launch object and lack an independent publication date/body object. |
| `web-substack-nader-agent-stack` | reject cross-platform cluster | Complete body is explicitly an X-origin tutorial already represented by accepted X object. |
| `worker-global-078` | reject exact URL duplicate | Canonical URL already accepted as `seed-substack-47-pi-agent-vs-claude-code-code-review`. |
| `worker-global-079` | reject exact URL duplicate | Canonical URL already accepted as `seed-substack-48-pi-web-browse-web-ssrf`. |
| `web-hackernoon-subagents-built` | reject same-author content cluster | ~79% bidirectional shingle overlap with accepted June 25 Anson article. |

No metadata-only, search-snippet-only, translated, mirror, sub-route, or
peripheral Pi mention was counted. No login, CAPTCHA, paywall, robots, or rate
limit was bypassed by this scan.

## Outcome

**Safe promotion IDs: none.** Existing complete readbacks remain useful evidence
for future explicit curator decisions, but every unaccepted shortage-platform
row either duplicates an accepted URL/object, belongs to a documented content
cluster, or is a non-Pi-primary/false-positive object. The shortage state must
remain honest until genuinely new canonical objects are found and independently
read.
