# OSChina bounded follow-up 3 audit — 2026-08-30

Run: `pi-platform10-20260826`
Scope: one final bounded public-only OSChina search pass requested by the
primary curator. No root candidate, queue, ledger, or library file was edited.

## Baseline and duplicate control

Before probing, all current OSChina rows in `candidates.json`,
`review_queue.json`, and `workers/*-candidates*.jsonl` were normalized by URL,
platform object ID, candidate ID, title, author, and date. The snapshot had
seven unique OSChina canonical URLs (six blog/detail objects plus Huiyu-Pi)
and no unrecorded candidate IDs for the URLs below. No guessed article URL was
opened.

## Bounded queries

Only two distinct ordinary search queries were used:

1. Google `site:oschina.net/blog "earendil-works/pi"` — the visible result page
   returned **0 results**. This is an exact official-alias probe and yielded no
   canonical object.
2. Bing `site:my.oschina.net/u "Pi Agent" 技巧` — the visible page stopped at
   a “请解决以下难题以继续” challenge before any result list rendered.
   No CAPTCHA/challenge was solved and no alternate automated route was used.

The exact request URLs, timestamps, status, result state, and response hashes
are in `oschina-followup3-20260830-probes.jsonl`.

## Result

**0 new OSChina candidates.** The first query is a reproducible strict zero;
the second is a normal search-access blocker. Existing OSChina objects remain
the only accepted/queued material. No login, interaction, download, robots or
challenge bypass, or external write occurred. The worker shard remains
append-only evidence and does not alter the root accounting.
