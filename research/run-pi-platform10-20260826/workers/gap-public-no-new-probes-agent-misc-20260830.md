# Public gap no-new probe — 2026-08-30

Run: `pi-platform10-20260826`

This is an append-only discovery record. Before probing, the current
`candidates.json`, `review_queue.json`, and worker candidate shards were
compared by candidate ID, normalized canonical URL, and (where available)
platform object ID. No candidate, queue, accepted ledger, or library file was
changed in this pass.

## Bounded route

The `agent-reach doctor --json` check was attempted first; this shell has no
`agent-reach` executable. The documented public-search fallback was used. Five
single-intent Bing RSS requests were made at low volume, one each for Hashnode,
HackerNoon, 36Kr, OSChina, and Product Hunt. RSS result metadata was used only
to discover possible URLs; no search result or snippet was treated as a
readback. The exact request URLs, HTTP status, byte counts, response hashes,
and result counts are in
`gap-public-no-new-probes-agent-misc-20260830.jsonl`.

## Result

All five requests returned HTTP 200 with ten result records, but zero links on
the target domain (`relevant_domain_results=0`). Consequently, no previously
unseen canonical article/product page was exposed and **zero new candidates
were created**:

| platform | intent | result | candidate |
|---|---|---:|---:|
| Hashnode | `hashnode_exact_alias` | 10, target-domain links 0 | 0 |
| HackerNoon | `hackernoon_exact_alias` | 10, target-domain links 0 | 0 |
| 36Kr | `36kr_exact_pi` | 10, target-domain links 0 | 0 |
| OSChina | `oschina_exact_pi` | 10, target-domain links 0 | 0 |
| Product Hunt | `producthunt_exact_pi` | 10, target-domain links 0 | 0 |

Product Hunt has no configured API token; this probe therefore remains
discovery-only and does not assert Product Hunt evidence. A future Product Hunt
item still requires the permitted user-assisted native page or an authorized
read-only API response. Likewise, no Hashnode API, HackerNoon crawler, 36Kr
restricted route, OSChina internal search, login, CAPTCHA, paywall, download,
interaction, or robots bypass was attempted.

## Accounting

At the post-probe snapshot, the shared files remained unchanged by this pass:
441 physical candidate rows and 523 review-queue rows. Existing shortage
counts and all accepted URLs remain authoritative; this record must not be
interpreted as quota completion.
