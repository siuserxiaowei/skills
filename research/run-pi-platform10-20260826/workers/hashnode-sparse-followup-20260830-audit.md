# Hashnode sparse follow-up audit (2026-08-30)

Run: `pi-platform10-20260826`
Scope: append-only public discovery/readback evidence. This audit does not
promote rows or modify `candidates.json`, `review_queue.json`, or ledgers.

## Baseline and duplicate check

Before appending, the current worker snapshot was scanned for both canonical
URLs, Hashnode discussion object IDs, titles, and distinctive body phrases.
At that scan `candidates.json` contained 412 physical rows and
`review_queue.json` contained 495 unique worker rows; neither URL or object ID
was present. The exact URL/title/author/date combinations were also absent
from all `workers/*candidates*.jsonl` shards. Re-scan is still required by the
primary curator immediately before promotion because other workers share the
workspace.

The Unity article is not the same content cluster as the accepted LinkedIn
Gemma/LM Studio post or the Substack local-model guide: it has a different
author, canonical object, detailed Windows/Unity steps, and a distinct body.
The Gitea article has a different author, date, object ID, and workflow narrative
from all existing Hashnode and cross-platform rows; no mirror or trivial
cross-post was found in the frozen local snapshot. These are independent
candidate decisions, not automatic acceptance.

## Canonical readback

1. **A local AI agent in Unity - how to start Pi agent on your own machine**
   (`https://arek7r.hashnode.dev/a-local-ai-agent-in-unity-how-to-start-pi-agent-on-your-own-machine`)
   was opened from the public Hashnode native search route and read end to end
   in ordinary Chrome without login. The page visibly identified Arkadiusz,
   Updated May 31, 2026, 5 min read, and discussion object
   `6a1beaadf77c84962ea967a9`. The 5036-character `article.innerText` has
   SHA-256 `2a6be37a4a66153577de1cbf23dc14dd805a7eb555266935a4dab522ea1ec1af`.
   Its body covers LM Studio/Gemma 4 E4B, a local OpenAI-compatible endpoint,
   Pi's four tools, Windows `models.json`, Unity `Assets` placement,
   skills/extensions, and the default YOLO/permission-gate warning.

2. **Start building a local workflow using Pi.dev**
   (`https://blog.catoxliu.net/start-building-a-local-workflow-using-pi-dev`)
   was likewise opened and read end to end anonymously. The page visibly
   identified `sj`, Updated May 19, 2026, 2 min read, discussion object
   `6a0be89b4e81b73048e2ae63`, canonical/og URL, and
   `article:published_time=2026-05-19T04:35:39.608Z`. Its 1677-character
   `article.innerText` has SHA-256
   `cc63577c025c40205394dafa97385c19a12465289a13227bd9429ee917ebc2`.
   The seven body paragraphs describe a spare machine, Docker-hosted Gitea,
   no direct company Git access, Unreal C++ rules, a Windows NVM conflict
   repaired by Pi, and PR/webhook review automation.

## Decision and boundaries

Two rows are appended in
`hashnode-sparse-followup-20260830-candidates.jsonl`, with matching complete
readbacks in `hashnode-sparse-followup-20260830-readbacks.jsonl`. Both remain
`curator_review_ready`; `accepted=0` in this worker handoff. The articles are
community practice reports, not official specifications or independent
benchmarks, and their versions/configuration claims need primary-curator
review against current Pi documentation. No login, vote, comment, follow,
download, crawler/sitemap scrape, CAPTCHA/paywall bypass, or external write was
used.

## Final bounded native-search check

After the two rows were written, one focused public Hashnode search for
`pi coding agent` was run in ordinary Chrome. The visible Posts results were
the two new rows plus already reviewed generic/duplicate pages: a generic
AI-agent guide, an OpenAI-compatible-provider overview, Huiyu Pi (the same
product cluster already represented by DEV/OSCHINA), and the
`oh-my-pi-coding-agent` tag. No additional independent Pi-primary canonical
detail was exposed. The generic guide/provider page were not appended because
Pi is incidental; Huiyu Pi was withheld as a known cross-platform product
cluster; the tag is a feed, not a content object. This is a no-new-result
check, not a quota-completion claim.

## Additional bounded query negatives

Two further single-query native searches were checked after the final result
above. `pi-mono` returned two Ramu Narasinga posts about a Slack bot/TypeBox,
plus a Raspberry Pi monitoring post; none was a Pi coding-agent canonical
article. `pi.dev` returned the already captured Gitea workflow and unrelated
DRM/Spanish/Debian pages. `pi agent` returned generic agent/versioning pages,
an Omnigent meta-harness page, and tags; the visible results did not expose a
new Pi-primary canonical body. These negatives are retained to make the
search boundary reproducible; no generic AI-agent, Raspberry Pi, or
secondary-mention page was appended.
