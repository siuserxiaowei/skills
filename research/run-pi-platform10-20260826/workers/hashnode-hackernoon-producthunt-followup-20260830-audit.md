# Hashnode / HackerNoon / Product Hunt bounded follow-up audit — 2026-08-30

Run: `pi-platform10-20260826`
Scope: append-only public discovery and duplicate-control evidence. This pass
does not promote candidates and does not modify `candidates.json`,
`review_queue.json`, `platform_coverage.tsv`, `evidence_cards.tsv`, or the
public library.

## Baseline and duplicate control

Before recording the probes, the current `candidates.json`,
`review_queue.json`, and every `workers/*-candidates*.jsonl` shard were scanned
for normalized canonical URL, candidate ID, platform object ID, product ID,
title, author, and date. The scan covered 57 files, 504 normalized URLs, 840
known IDs, and 1,487 parseable row occurrences. The known HackerNoon and
Product Hunt URLs were present only where already recorded; the newly rejected
Hashnode discovery URLs (AIMOWAY provider overview, Huiyu Pi, and Omnigent)
were absent as candidate objects and remain absent because they fail the Pi
identity/content-cluster gate. No duplicate candidate row was created.

## Hashnode

Four bounded native-search intents were checked in an ordinary anonymous
browser: `pi coding agent`, `pi-mono codebase`, `pi.dev`, and `pi agent`. The
results exposed the two already captured sparse-follow-up canonical posts, the
two already captured Think Throo Pi-mono analyses, generic AI-agent/provider
guides, Huiyu Pi product-cluster content, the Omnigent meta-harness comparison,
and tag/feed pages. The provider overview mentions Pi only incidentally in
generic lists; Omnigent is centered on Liel/Databricks; Huiyu is the same
product/content cluster represented on other platforms; tags are not content
objects. These were therefore rejected or withheld rather than counted as new
Hashnode items.

## HackerNoon

Ordinary public search queries `site:hackernoon.com "pi-coding-agent"` and
`site:hackernoon.com "Pi Agent" -Raspberry` returned only already known
canonical stories, the Anson June 23/June 25 same-author subagent cluster,
translation paths, and list/tag routes. The June 23 story overlaps the retained
June 25 story by approximately 79% bidirectional six-word shingles and is not
an independent quota object. HackerNoon robots/terms restrict generic
crawling, so no sitemap, HTML crawler, or unauthorized route was used.

## Product Hunt

Anonymous public search pages 1 and 2 for `pi coding agent` were read. Page 1
returned only the existing Pi Coding Agent product (`1232648`, canonical
`https://www.producthunt.com/products/pi-coding-agent-3`); page 2 returned
unrelated products. Reviews, alternatives, comments, and other subroutes are
views of that same product object and were not split into candidates. Product
Hunt API access would require an authorized token; no token was created and no
HTML crawler was used.

## Result and safety boundary

The attached `*-probes.jsonl` records exact request URLs, intents, timestamps,
readback status, and rejection reasons. **Result: 0 new candidates.** This is a
bounded no-new probe, not a claim that any quota is complete. All access was
public, read-only, and anonymous: no login, vote, comment, follow, download,
CAPTCHA or paywall bypass, robots bypass, API-token creation, or external write
was attempted. `agent-reach` was checked as required by the internet-research
skill but is unavailable on this machine; the documented ordinary-browser
fallback was used.
