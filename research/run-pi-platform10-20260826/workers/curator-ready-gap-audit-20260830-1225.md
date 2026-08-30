# Curator-ready gap audit — 2026-08-30 12:25 (Asia/Shanghai)

This append-only audit re-scans the current review queue and all worker
candidate/readback shards. It does not modify `candidates.json`,
`review_queue.json`, ledgers, or the public library.

## Method and de-duplication

The scan compared candidate IDs and normalized canonical URLs against the
accepted candidate set, then matched worker rows to every available
`*-readback*.jsonl`, `*-decision*.jsonl`, and `*-decisions*.jsonl` record. The
current snapshot contains 441 physical candidates, 523 queue rows, and 133
queue IDs not present in the accepted ledger. Existing rows were not fetched
again. Existing accepted URL/platform-object identities were treated as
authoritative, including Product Hunt product subroutes and 36Kr syndication
clusters.

## Findings

### Safe-to-promote candidates (primary curator decision still required)

No queue row is recommended for promotion in this pass (`promotable=0`). The
only unaccepted 36Kr row with a complete independent readback is
`china-followup-36kr-3925157852493960-penguin-harness-20260830`; its own
curator decision records reject it because Pi appears only as a thin secondary
comparison while the article is centered on PenguinHarness. The two remaining
unaccepted 36Kr rows are already rejected as same-content clusters:

- `worker-cn-080` — duplicate content cluster of accepted InfoQ `worker-cn-063`.
- `worker-cn-082` — syndicated copy of accepted InfoQ `worker-cn-064`.

### Existing readbacks that must remain rejected/withheld

- Hashnode `web-hashnode-channels`, `web-hashnode-gary-components`,
  `web-hashnode-gary-tools`, and `web-hashnode-symphony`: full page readbacks
  exist, but decisions classify them as Pi-secondary, same-name false
  positives, or incidental mentions; none passes the Pi-primary/identity gate.
- Product Hunt `web-producthunt-reviews`: the public reviews subroute is part
  of the already accepted `Pi Coding Agent` product object and cannot be split
  into a second quota item.
- Official-web worker rows 016/017/018/020: exact canonical or redirect
  duplicates of accepted rows.
- SegmentFault `worker-cn-059`: exact URL duplicate and same-author/date
  cluster with the accepted SegmentFault/OSChina guide.
- Hacker News workers 063–069: platform discovery metadata only, with no
  curator body readback; no promotion.
- YouTube workers 047/048/053/058: metadata-only rows; no accepted transcript
  or complete-watch evidence in the ledger. (A separate local subtitle probe
  does not alter those worker rows or count as curator evidence.)

OSChina has no unaccepted queue row in this snapshot. Product Hunt's Tyndale
Built-with adoption page is already accepted as a single independent secondary
object; other Built-with routes were not opened or promoted.

## Result

`promotable=0`. No candidate/readback row was appended by this audit and no
shared accounting changed. The next safe actions are primary-curator decisions
on existing accepted-ready rows or a user-assisted read-only Product Hunt/
Hashnode session; do not infer quota completion from metadata, snippets,
subroutes, translations, or secondary mentions.
