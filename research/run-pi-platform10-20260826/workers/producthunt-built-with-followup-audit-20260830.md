# Product Hunt Built-with follow-up audit — 2026-08-30

## New candidate

The canonical `https://www.producthunt.com/products/bb/built-with` page was
read anonymously over a transparent public HTTP route. Its main **Products
used by bb** section (not the similar-products sidebar) contains the
`Pi Coding Agent` product object and the exact adoption note **“A huge
inspiration for the extendability of Pi.”** The parent page identifies `bb` as
an agentic orchestrator GUI that works with multiple providers and can extend
itself through prompts. Canonical/og URLs match, the parent JSON-LD identifies
the product and authors, and the response was HTTP 200.

The row is recorded as
`producthunt-bb-built-with-pi-20260830` in the candidate/readback shards. It is
an independent Product Hunt product subroute and a Pi-secondary adoption
snapshot, not a Pi-primary tutorial or benchmark. It remains
`curator_review_ready` until the explicit primary-curator promotion step.

## Negative controls

The previously discovered `maestri`, `scritty`,
`shepherd-terminal-designed-for-agent`, and `agent-manager` Built-with pages
were also fetched once for route verification. Their visible Pi mentions were
only in similar-product/alternative sidebars; their main Products used by
sections did not contain a Pi adoption review. They were not converted into
candidates. `shelly-3` did not expose a Pi card at all. This prevents sidebar
recommendations from being mistaken for product adoption.

## Boundary

Public read-only only. No Product Hunt API token, login, vote, comment, follow,
launch, download, HTML crawler, CAPTCHA bypass, or robots bypass was used.
