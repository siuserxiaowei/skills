# Hashnode / HackerNoon follow-up audit

Run: `pi-platform10-20260826`
Checked: `2026-08-29` (Asia/Shanghai)
Scope: append-only audit/readback evidence. This file does not promote rows or
modify `candidates.json`.

## Route and policy

`agent-reach doctor --json` was attempted first, but the command is not
installed on this host (`command not found`). Per the frozen platform rules,
HackerNoon generic crawling, sitemap scraping, and unlisted crawler identities
remain disallowed by its current robots/terms; Hashnode `/api`, private routes,
and unauthorized GraphQL collection remain disallowed. The reads below used
ordinary public Chrome pages only, with no login, interaction, download, or
challenge bypass.

## Hashnode: one new Pi-primary public article

External Google discovery query: `site:hashnode.dev "Pi Agent" OR "Pi Coding"`.
The result `https://sohan-blog.hashnode.dev/i-took-the-pi-agent-apart-so-you-don-t-have-to`
was opened directly in an ordinary public browser and rendered its complete
article body (52 paragraphs; article text length 12,454 characters in the
visible `article` element). Visible metadata:

- title: **I Took the PI Agent Apart So You Don't Have To**
- author: **Sohan** (`@Srktheman`)
- date: **June 7, 2026** (updated; `article:published_time` is
  `2026-06-07T09:52:43.175Z`)
- canonical URL: the URL above (`link[rel=canonical]` and `og:url`)

The body is Pi-primary, not an incidental mention. It walks through the PI
Core agentic loop (context, compaction, LLM call, tool loop), project-scoped
JSONL tree sessions and branching, the four Read/Bash/Edit/Write tools,
read-only RPC mode with grep/find, TypeScript extensions/TUI, exact provider
usage-based compaction, and lazy-loaded skills. Representative visible body
passages include “PI Core ... agentic loop”, “PI doesn't store conversations as
a flat list. It stores them as a tree”, and “exactly four core tools: Read,
Bash, Edit, and Write.”

This is a curator-review-ready candidate, but is intentionally not promoted in
this subtask. Suggested provisional ID: `web-hashnode-sohan-pi-internals`.
The queue currently has no row with this ID or canonical URL. A separate
curator readback JSONL record is written alongside this audit.

## HackerNoon: two additional Pi-primary stories, but same-author content cluster

The focused public search `site:hackernoon.com "pi.dev" agent` surfaced:

1. `https://hackernoon.com/how-subagents-are-built` — **How Subagents are
   Built**, Anson, June 23rd 2026. Full ordinary-page read succeeded (visible
   `main` text length 12,384). It explicitly centers Pi's lack of bundled
   subagents, compares tool handoff/subagent/orchestrator primitives and other
   harnesses, and reports a multi-`pi -p` session experiment. Metadata and body
   are sufficient for a standalone Pi-primary candidate.
2. `https://hackernoon.com/the-race-to-build-the-right-subagent-primitive` —
   **The Race to Build the Right Subagent Primitive**, Anson, June 25th 2026.
   Full ordinary-page read succeeded (visible `main` text length 12,652). It
   centers Pi's subagent gap and compares Claude Code, Codex, Hermes, OpenCode,
   and Pi implementation choices.

Both stories are canonical English HackerNoon objects, not translated paths.
However, normalized six-word shingle overlap between the two complete visible
article texts is approximately 79% in each direction; the opening Pi framing,
subagent taxonomy, comparisons, and the Pi multi-session example are largely
reused. The second story also links the first as “Previous”/“Also published
here” context. Under the run's content-cluster rule, these should be treated as
one author/series cluster and **not both promoted as independent quota items**.
Keep both as evidence; prefer the June 25 article for the more developed
comparison and retain the June 23 article as a duplicate/cluster negative.

The HackerNoon robots/terms boundary still rules out generic scripted crawling;
the successful ordinary-page read is not a grant to crawl more stories.

## Search negatives / current outcome

The same focused search returned Raspberry Pi and unrelated `pi.dev`/extension
results; they were not opened or counted. A second query for
`site:hackernoon.com "pi.dev" "extension"` returned an unrelated Raspberry Pi
computer-vision article only. No further safe HackerNoon object was identified.

Outcome: **one new Hashnode curator-review-ready candidate; zero new HackerNoon
quota candidates after cluster control**. Existing accepted rows and the shared
ledger remain unchanged.
