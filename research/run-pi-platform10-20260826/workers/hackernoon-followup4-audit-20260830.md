# HackerNoon bounded follow-up audit — 2026-08-30

Run: `pi-platform10-20260826`
Scope: append-only public discovery/readback evidence for the HackerNoon quota
gap. This pass does not promote a candidate and does not modify
`candidates.json`, `review_queue.json`, `sources.tsv`, `evidence_cards.tsv`, or
the public library.

## Route and safety boundary

The required `agent-reach doctor --json` check was attempted first; this shell
has no `agent-reach` executable (`command not found`). The documented ordinary
browser/public-search fallback was used. Google visible results and ordinary
HackerNoon canonical pages were read without login, interaction, download,
CAPTCHA solving, paywall bypass, robots bypass, generic crawling, sitemap
scraping, or unauthorized API access. Search snippets were used only for
discovery; full-page decisions below use the visible article body.

Before probing, existing `candidates.json`, `review_queue.json`, and worker
candidate shards were compared by normalized canonical URL, candidate ID,
platform object ID, title/author/date, and known content clusters. The known
objects were not fetched again as candidate rows:

| known object | canonical URL | handling |
| --- | --- | --- |
| `sparse-hackernoon-ssh-extension` / `web-hackernoon-ssh` | `https://hackernoon.com/how-i-manage-my-vps-with-pis-ssh-extension` | existing object only |
| `sparse-hackernoon-vt-theme` / `web-hackernoon-vt-theme` | `https://hackernoon.com/decent-colors-for-pidev-on-a-bare-linux-vt` | existing object only |
| `web-hackernoon-subagents-built` | `https://hackernoon.com/how-subagents-are-built` | same-author cluster; not independently counted |
| `web-hackernoon-subagent-primitive-race` | `https://hackernoon.com/the-race-to-build-the-right-subagent-primitive` | retained series representative |

The last two Anson stories have approximately 79% bidirectional normalized
six-word-shingle overlap and share the same Pi/subagent framing, comparisons,
and experiment. They are therefore one content cluster under
`PLATFORM_ACCEPTANCE.md`, not two independent quota objects.

## Bounded intents

The attached `hackernoon-followup4-probes-20260830.jsonl` records 9 focused
Google intents (`pi.dev`, `pi agent`, `Pi Coding Agent`, `pi-coding-agent`,
`pi-mono`, `pi ssh`, `pi tui`, `pi harness`, and `agentic Pi`) plus 5 explicit
result/readback checks. The focused searches exposed only existing stories,
translation/tag/list routes, generic agent articles, or Raspberry Pi false
positives. No new stable canonical HackerNoon object was found.

Three likely Google hits were opened and fully read to avoid snippet-based
acceptance:

1. **What Building a Six-Agent AI Code Reviewer Taught Me About Agentic
   Systems** — Vanna W, August 21st 2026. The body is about ChatDev 2.0 and a
   six-agent GitHub PR review crew; it contains no explicit Pi project alias.
2. **Building an AI Coding Agent That Doesn't Hide What It's Doing** — Muhammad
   Rizwan, May 8th 2026. The body is the author's NanoAgent/CLI/desktop
   permission and sandbox design; Pi is absent from the article body.
3. **An Agentic-Native Engineering Workflow With Terminal Environment: The
   Setup I'm Using for It** — Duy Huynh, June 24th 2026. The body centers
   flightdeck, Ghostty, tmux, Neovim, Claude Code and worktrees; no Pi project
   reference appears. An author-site repost is the same content cluster.

One additional full read, **AI Coding Tip 020 - Create a Second Brain** (Maxi
Contieri, May 18th 2026), mentions Pi only incidentally in a generic tool list
while discussing Obsidian/Markdown external memory, so it is rejected. A
`Pi Dev Board` result was excluded at discovery because it is Raspberry Pi
hardware, not the coding-agent project.

## Result

**0 new curator-ready HackerNoon candidates.** No candidate ID or canonical URL
was appended. HackerNoon remains a real quota shortage (`3/10` accepted in the
current snapshot; 7 missing), not complete. Translation pages, tag/feed/list
routes, reposts, Raspberry Pi, incidental token matches, and the high-overlap
Anson pair are explicitly not counted.

The next safe retry is another bounded ordinary-user-visible canonical search or
a user-provided normal read-only session if HackerNoon changes its access
boundary. Do not use a sitemap/crawler or create an API token merely to fill
the quota.
