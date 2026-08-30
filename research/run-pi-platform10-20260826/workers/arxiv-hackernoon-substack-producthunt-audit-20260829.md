# arXiv / HackerNoon / Substack / Product Hunt bounded gap audit

Run: `pi-platform10-20260826`
Checked: `2026-08-29` (Asia/Shanghai)
Scope: append-only discovery audit; no candidate is promoted by this file.

## Current queue baseline

The shared review queue was read before probing. It contains three distinct
arXiv/OpenReview URLs, two HackerNoon URLs, five Substack URLs, and two Product
Hunt routes (the product page plus its reviews sub-route). The corresponding
accepted counts at the start of this audit were 3, 2, 5, and 1. Existing
candidate IDs and normalized canonical URLs were not re-submitted.

## Bounded probes and reproducible outcomes

### arXiv / OpenReview

Official arXiv Atom API was queried with these exact, bounded intents (20 or
fewer results requested per query):

```text
all:"pi-coding-agent"       -> HTTP 200, totalResults 0
all:"pi coding agent"       -> HTTP 200, totalResults 0
all:"earendil-works"        -> HTTP 200, totalResults 0
all:"badlogic/pi-mono"      -> HTTP 200, totalResults 0
all:"pi-mono"               -> HTTP 200, totalResults 0
all:"Pi harness"            -> HTTP 200, one result: arXiv 2605.24220v1
all:"Pi Agent" AND all:harness -> HTTP 200, one result: arXiv 2607.25890v1
all:"pi.dev"                -> HTTP 200, totalResults 0
all:"pi coding" AND all:agent -> HTTP 200, totalResults 0
```

The two returned papers are already present in the queue, as is the SHarD
paper 2607.25890v1. Their canonical HTML readbacks are retained in
`public-api-research-supplemental-readbacks.jsonl`; no new independent paper
was found. OpenReview remains at its previously recorded HTTP 403 boundary;
no alternate identity, proxy, or bypass was attempted.

### HackerNoon

`https://hackernoon.com/robots.txt` was read with the bounded retrieval
identity used for this run and returned HTTP 200. Its current policy has a
default `User-agent: * Disallow: /`, while explicitly allowing named search or
user-triggered retrieval agents; the run's generic crawler is not an allowed
route. The sitemap request with the same unlisted identity returned HTTP 403.
The two known canonical English stories already in the queue were not fetched
again, and translated paths were treated as the same content cluster. No new
HackerNoon object can be accepted without an ordinary user-visible canonical
story read or an explicitly allowed retrieval route.

### Substack

The queue already contains five distinct canonical public posts (five
publication domains/URLs, including the independently read Andrew Dotooo,
George Racu, Scaile Agency, Owain Lewis, and ZazenCodes objects). Existing
canonical IDs and URL/content clusters were checked locally; no new object was
added. Substack terms/API terms remain the controlling boundary: publication
HTML must not be crawled or bulk-collected, and paywalls/login gates cannot be
bypassed. The ZazenCodes row remains worker-only until a fresh full public-body
readback is available; it is not counted as a newly accepted object here.

### Product Hunt

The official GraphQL endpoint was probed without credentials using one
read-only exact-alias query. It returned the Product Hunt not-found/Cloudflare
challenge response (`HTTP 404`), so no API data was collected. The public
canonical product page is already represented by
`sparse-producthunt-pi-launch`; `/reviews` is a sub-route of the same product
object and remains metadata-only, not an independent content item. No token was
created, and no vote, comment, follow, launch, or other interaction occurred.

## Decision

This bounded pass adds **zero** new curator-ready candidates for all four
platforms. Existing shortage states remain honest (`arxiv_openreview 3/10`,
`hackernoon 2/10`, `substack 5/10`, `product_hunt 1/10`). Resume only through
the platform-specific permitted routes recorded in `platform_rules.tsv`; do not
use search snippets, translations, Product Hunt sub-routes, paywalled posts,
metadata-only rows, or generic crawlers to pad quotas.

No shared ledger, handoff file, or publication artifact was modified by this
audit.
