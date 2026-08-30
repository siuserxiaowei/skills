# Hashnode Think Throo Pi-mono follow-up audit — 2026-08-30

Run: `pi-platform10-20260826`
Scope: append-only worker discovery/readback evidence for the Hashnode quota;
no root ledger, `candidates.json`, queue, or public library was edited here.

## Baseline and route

Before probing, current `candidates.json` and `review_queue.json` were loaded
and normalized URLs/IDs were checked. Neither Think Throo canonical URL below,
its Hashnode discussion object ID, nor either exact title/author pair was
present. The public Hashnode native search route was used in an ordinary Chrome
session with `pi-mono codebase` (and the already checked `pi-mono`) intent. No
GraphQL/API/private route, login automation, interaction, download, or crawler
was used.

## Independent canonical objects

Hashnode search returned two separate native post discussions by Ramu Narasinga,
each linking to a different public Think Throo canonical article:

1. `hashnode-thinkthroo-mom-20260830` —
   `https://thinkthroo.com/blog/mom-a-slack-bot-powered-by-an-llm-in-pi-mono-codebase`
   (discussion object `69d52348881fa5dfc5780c2a`). The full canonical body was
   read. It is Pi-mono-primary: mom/“Master Of Mischief”, Slack context,
   self-managed skills, bash/file access, Docker sandbox, persistent workspace,
   and a `packages/mom/src/main.ts` `createSlackContext` excerpt. Visible body
   length 3076; SHA-256 `e33bc021da0971c8923a60405e7e3073887e513564560f4dfa21428f789e1619`.

2. `hashnode-thinkthroo-typebox-20260830` —
   `https://thinkthroo.com/blog/typebox-a-json-schema-type-builder`
   (discussion object `69d5234d881fa5dfc5780c3c`). The full canonical body was
   read. It is a distinct Pi-mono codebase-analysis article: TypeBox basics,
   `agent/types.ts` `AgentTool` contracts, and
   `coding-agent/core/extensions/types.ts` `ToolDefinition` schemas/execution/
   rendering hooks. Visible body length 5128; SHA-256
   `1914d8fe009b431ca944e34b1e1d360ba7a457f7680f7e7b9b612e04a1374ee1`.

The two pages are separate canonical URLs, separate Hashnode post objects and
different technical subjects/references. They are part of the author's broader
codebase-analysis series but are not mirrors, translations, or trivial
cross-posts; both are retained as independent candidates. Hashnode's native
discussion detail visibly showed `Apr 7, 2026`; the canonical page exposes
`2026 / April`, so the worker rows retain `2026-04-07` with that date basis.

## Files and decision

- `hashnode-thinkthroo-candidates-20260830.jsonl` contains two
  `worker_checked` rows with all required candidate fields.
- `hashnode-thinkthroo-readbacks-20260830.jsonl` contains matching complete
  original-page readback observations and content hashes.

Both rows are worker evidence only. Primary curator must independently inspect
the readbacks and explicitly promote IDs before they count as accepted. No
HackerNoon or Product Hunt object was found in this pass; existing HackerNoon
stories and the sole Product Hunt product remain unchanged and their known
cluster/subroute exclusions still apply.

## Cross-platform negative checks

The public HackerNoon `tagged/pi.dev` page was opened in the same ordinary
browser session and reported exactly one blog post, the already accepted
`decent-colors-for-pidev-on-a-bare-linux-vt`; no additional canonical story was
listed. A focused Google query for `site:hackernoon.com "Pi" "pi.dev" -Raspberry`
returned the already queued SSH-extension, VT-theme, and Anson subagent stories
plus tag/list pages and unrelated terminal articles; translations were not
counted. Product Hunt public search for `pi coding agent` returned the existing
Pi Coding Agent product (ID 1232648) and unrelated products; reviews,
alternatives, launch pages and comments remain subroutes/views of that one
object. These checks add no candidate.
