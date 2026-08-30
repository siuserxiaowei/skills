# Global broad gap audit (2026-08-30)

Run: `pi-platform10-20260826`
Scope: append-only public discovery/readback; no shared ledger or accepted
`candidates.json` mutation.

## De-duplication baseline

Before probing, I loaded the current `review_queue.json` (493 unique worker
objects) and `candidates.json`. The new canonical URL
`https://dishantsharma.hashnode.dev/oh-my-pi-hype-hashline` and post object
`6a1b45e5213ae773f47f6d0e` were absent from both sets. Existing Hashnode URLs
and the already accepted `oh-my-pi` items on other platforms were not
re-submitted; translated/secondary routes were not counted.

## Query and readback

The public Hashnode native search route was opened in ordinary Chrome with
`pi-coding-agent`, which exposed the `oh-my-pi-coding-agent` tag feed. The feed
contained one Pi-fork article not present in the frozen queue:

- **The oh-my-pi Hype: Hashline, Reactions, and What Everyone Missed**
  — Dishant Sharma (`@dishant0406`), Hashnode canonical URL above.

The canonical article was then opened and read end-to-end anonymously. The
page showed “Updated May 30, 2026” and “7 min read”; the rendered article text
was 8,028 characters with SHA-256
`dad902b18c5abf97e5221e662034d43a978cd7cd0af58ef7783ba8c7d56dd6e4`.
The body explicitly names oh-my-pi as a fork of Mario Zechner’s Pi and covers
Hashline content-hash edits, Bun/Rust architecture, provider/tool counts,
persistent Python/Bun workers, LSP/DAP operations, startup context overhead,
Claude Code versus pure Pi tradeoffs, upgrade failures, and maintenance risk.

## Decision

One new `hashnode` candidate is appended as `curator_review_ready` in
`gap-global-broad-20260830-candidates.jsonl`, with a matching independent
readback record in `gap-global-broad-20260830-readbacks.jsonl`. It is a
community analysis of a Pi fork, not an upstream official specification; the
author-reported benchmark and cited Reddit/HN reactions remain explicitly
limited and were not treated as independent measurements. No login, vote,
comment, download, crawler/sitemap scrape, or bypass was used.

## Search negatives / boundaries

- `site:hashnode.dev "pi-mono" -gary-parker` returned zero results in the
  ordinary browser; known Gary Parker same-name pages remain rejected as
  unrelated generic testing content.
- `site:hackernoon.com "pi-coding-agent" -ssh -subagent` returned zero results;
  no new HackerNoon canonical object was identified beyond existing rows.
- Product Hunt’s May 25 daily leaderboard only repeated the existing
  `Pi Coding Agent` product object; its `/reviews` route is a sub-route and was
  not counted as a new content object.
- Stack Exchange API exact aliases (`pi-coding-agent`, `pi-agent-core`,
  `earendil-works/pi`, `badlogic/pi-mono`, title/body probes) remained HTTP 200
  with `items: []`; the separate public **Stack Overflow for Agents** TIL pages
  were not counted because they are a different beta property and not
  Stack Overflow question/answer objects under the frozen API rule.

Files in this audit are append-only worker artifacts. Promotion, queue
rebuild, and ledger updates are intentionally left to the primary curator.
