# Product Hunt / Stack Overflow bounded gap audit — 2026-08-30

Scope: inspect public, no-login routes for genuinely new Pi-primary canonical
objects. Existing candidate IDs and normalized URLs were loaded first from
`candidates.json`, `review_queue.json`, and worker shards. No shared ledger,
candidate file, queue, or library was modified.

## Product Hunt

The existing Product Hunt object is `sparse-producthunt-pi-launch` at
`https://www.producthunt.com/products/pi-coding-agent-3`. A fresh anonymous
Chrome readback of that canonical product page returned HTTP 200 and showed:

- title: **Pi Coding Agent: The coding-agent harness you can make your own**;
- visible product description: minimal terminal coding harness with extensions,
  skills, prompt templates, themes, npm/git packages, and deliberate omission of
  sub-agents/plan mode;
- launch team Zac Zuo, `pi.dev` and official GitHub links, “Launched in 2026”,
  and mutable comments/reviews;
- canonical link and `og:url` both equal the product URL;
- Schema.org product JSON-LD `@id` equal to the same URL, product ID `1232648`,
  `datePublished=2026-05-24T20:24:54.036-07:00`, and `dateModified=2026-08-28`.

Rendered body text was 7,214 Unicode characters, SHA-256
`2eab4fababbb2d98b6adf692955eab8f01a4b5b1a7d5179696bb77e900605377` (hash basis:
full visible `document.body.innerText`). This is the already-accepted launch
object, not a new object.

A focused public Product Hunt search for `pi coding agent` was read across pages
1–3 and the launch-search route was read once. Page 1 returned the same product
ID `1232648`; pages 2–3 contained unrelated coding-agent products. The public
`pi` launch search returned unrelated products (ML toolkit `pi-5`, Inflection
Pi, Raspberry Pi, and Pi Charging) plus the already-known Pi Coding Agent
launch; none identify `earendil-works/pi` or `pi-coding-agent` as a new stable
Product Hunt object. `https://www.producthunt.com/products/pi` was also checked
and is an unrelated 2014 growth-hacking product (`secretpi.com`).

The `/reviews`, `/alternatives`, `/customers`, `/makers`, comments, pagination,
and `?launch=` routes are mutable subroutes or views of the same product object.
They have no independent stable publication object and are not counted. The
Product Hunt GraphQL endpoint remains unavailable without an authorized token;
per platform terms no scripted HTML crawler or token creation was attempted.

**Product Hunt result: zero new candidate; existing product remains the sole
Pi-primary object (1/10).**

## Stack Overflow

Before probing, no Stack Overflow candidate ID or canonical URL was present in
the current candidate ledger or queue. The official Stack Exchange API was used
at a low rate (3-second spacing; below the documented 30 requests/second
threshold) with `filter=withbody`, `site=stackoverflow`, and four bounded exact
or quoted intents:

| probe | HTTP/result | response SHA-256 |
|---|---|---|
| `q="pi coding agent"` | 200, 0 items, quota 262 | `ecf2346c086566a511c6e99ec0679e85a58c13cdeece2fb07d3a2f5de4d3f345` |
| `q="pi-mono"` | 200, 7 items, all Raspberry Pi/Mono questions; rejected | `83365e32410afd10427d843fdb8c9df13c05097913f72100919e7128c45c1a92` |
| `q="pi.dev"` | 200, 0 items, quota 260 | `efb75275c4b17e27c25175919f10ce3bda0352fea186bd8be856723b70cc25dc` |
| `q="Pi Agent"` | 200, 2 items, both Raspberry Pi/Cumulocity/WSo2; rejected | `e89a65f3d27b4f728400e5f19efb6dca1205c552206c81a105525810524c39a2` |

Full request URLs, byte counts, quota values, response bodies and timestamps
are in `producthunt-stackoverflow-probes-20260830.jsonl`. The nonzero results
were read as API bodies and fail the frozen identity gate: they concern
Raspberry Pi hardware or generic “PI agent” wording, not
`earendil-works/pi`, `badlogic/pi-mono` as the coding-agent project, or a
specified Pi package.

A direct anonymous browser search for `https://stackoverflow.com/search?q=%22pi-coding-agent%22`
redirected to `https://stackoverflow.com/nocaptcha?...`, whose visible title was
**Human verification - Stack Overflow** and whose body displayed “Check the
CAPTCHA box”. The visible body was 1,464 characters (SHA-256
`d47cbe152371c7426a2133185a391833d5cb95d1b15ae6205ae2dbdaaab89ef1`). No box
was checked or solved. This is an access boundary, not evidence of a candidate;
the documented official API remains the compliant route. No HTML scraping,
login, account action, votes, comments, answers, or edits occurred.

**Stack Overflow result: zero new candidate; retain reproducible partial/
blocked state (0/10).** Retry only when a new exact-alias API result appears or
the user provides a normal authenticated read-only session; do not bypass the
CAPTCHA or substitute Raspberry Pi/Mono matches.
