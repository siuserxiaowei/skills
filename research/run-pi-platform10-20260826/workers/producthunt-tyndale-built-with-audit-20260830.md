# Product Hunt Built-with adoption follow-up — 2026-08-30

Run: `pi-platform10-20260826`
Scope: one ordinary public-page readback plus bounded discovery. This append-only
worker audit does not promote the row in `candidates.json`.

## Duplicate and route control

Before appending, the current candidate ledger, review queue, and worker shards
were checked by candidate ID and normalized canonical URL. The Tyndale Built
with URL was absent; the existing Pi product URL and its `/reviews` subroute
were not reused. Product Hunt API/token access was not attempted, and no HTML
crawler or bulk collection was used.

## Full canonical readback: Tyndale

The independent canonical page
`https://www.producthunt.com/products/tyndale/built-with` was opened in an
ordinary anonymous Chrome session and read as rendered. Visible page facts:

- page title: **Products used by Tyndale | Product Hunt**;
- parent product: **Tyndale**, tagline “Translate your app with the AI you
  already pay for”, 60 followers, a command-line/i18n product description,
  website and GitHub links, and `Launched in 2026`;
- page section: **Products used by Tyndale**, with a separate GitHub stack
  entry titled `GitHub - badlogic/pi-mono: AI agent toolkit: coding agent CLI,
  unified LLM API, TUI & web UI libraries, Slack bot, vLLM pods`;
- the same stack entry visibly shows `5.0 (1 review)` and the quote:
  “Pi provides a clean and easy harness with multiple providers accepted. It's
  freedom and power at our hands”;
- `link[rel=canonical]` and `meta[property="og:url"]` both resolve exactly to
  the Built with URL; JSON-LD identifies the parent as a Tyndale
  `WebApplication` authored by Pedro Mendes (`datePublished` 2026-04-23,
  `dateModified` 2026-08-23).

This is a distinct Tyndale product page, not a view of the Pi Coding Agent
product. It is recorded as a **Pi-secondary adoption snapshot** only. It has no
Pi version/configuration/code or controlled benchmark, and its stack/review/
quote data can change. The candidate and matching readback are in:

- `producthunt-tyndale-built-with-candidates-20260830.jsonl`
- `producthunt-tyndale-built-with-readbacks-20260830.jsonl`

The row remains `worker_checked`; primary curator must explicitly decide
whether this secondary Product Hunt object is eligible for the platform quota.

## Discovery-only slugs (not claimed as readbacks)

A bounded Google exact-phrase result also exposed these Product Hunt
`/built-with` routes mentioning the Pi Coding Agent card: `maestri`, `bb`,
`scritty`, `shepherd-terminal-designed-for-agent`, `agent-manager`, and
`shelly-3`. Their result snippets were not used as evidence and their pages
were not opened in this pass; no candidate rows are asserted for them. A future
pass may open one route at a time in an ordinary user-visible session, then
repeat the identity/duplicate and secondary-adoption checks.

## Boundary

All reads were public and read-only: no login, vote, comment, follow, launch,
download, API-token creation, CAPTCHA/robots bypass, or external write occurred.
