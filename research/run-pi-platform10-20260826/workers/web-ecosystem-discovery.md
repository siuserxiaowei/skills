# Web ecosystem discovery shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26`
Machine-readable shard: `web-ecosystem-candidates.jsonl`

This is an isolated seven-platform discovery/readback artifact. Its local states
are `curator_review_ready`, `metadata_only`, and `not_ready`; none means
`accepted`, and this shard is intentionally not imported into the shared
`candidates.json`. Every row contains the frozen 17 fields plus `query_id` and
`readback_evidence`.

## Outcome

| Platform | Rows | Ready | Metadata | Not ready | Actual intents | Short to 15 rows | Short to 15 ready |
|---|---:|---:|---:|---:|---:|---:|---:|
| Official Web | 15 | 15 | 0 | 0 | 2 | 0 | 0 |
| Composio | 15 | 15 | 0 | 0 | 5 | 0 | 0 |
| Zenn | 10 | 10 | 0 | 0 | 4 | 5 | 5 |
| note | 10 | 9 | 0 | 1 | 4 | 5 | 6 |
| HackerNoon | 2 | 2 | 0 | 0 | 2 | 13 | 13 |
| Hashnode | 4 | 0 | 2 | 2 | 3 | 11 | 15 |
| Product Hunt | 2 | 1 | 1 | 0 | 2 | 13 | 14 |

The strict 15-candidate discovery target is met only by Official Web and
Composio. The other shortages are real. Translations, same-name objects,
generic articles that only mention Pi, and Product Hunt sub-navigation were not
used to fabricate independent content objects.

## Method and per-platform findings

### Official Web

- Intents: `official-release-features` and `official-runtime-safety`.
- `https://pi.dev/news.xml` was read directly after the host's robots policy was
  checked. Fifteen distinct canonical Pi release-note objects were selected.
- Each row preserves its version/date and multiple observed change groups. A
  release page is a first-party versioned object, but it is not independent
  validation of security or performance.

### Composio

- Intents: Pi docs, comparisons, extension/skill guides, harness benchmarks,
  and Pi-specific toolkit integrations.
- Both `docs.composio.dev` and `composio.dev` robots allow the selected public
  paths. Discovery used the public sitemap/`llms.txt` plus exact external search;
  canonical pages were then read.
- The 15 rows include six articles/benchmarks, two Pi documentation pages, and
  seven distinct Pi-specific MCP integration guides. No signup, API key, OAuth,
  tool execution, or downstream mutation occurred.
- Vendor benchmarks and comparisons must be independently reproduced; the
  toolkit pages describe potentially mutating actions but were only read.

### Zenn

- Intents: provider/setup practice, architecture/source reading, extension
  practice, and design transfer.
- Zenn `/search` was not used. Exact aliases were discovered externally, then
  ten free canonical articles/scraps were read directly in an ordinary public
  session.
- Strong pages include a build/test/extension experiment, OpenCode Go provider
  practice, a persistent-memory extension, WSL setup, tool-surface comparison,
  and capability-first design transfer.
- Five-row shortage remains. Several pages use the former
  `badlogic/pi-mono` name or older package/version details and need current
  pi.dev mapping during primary curation.

### note

- Intents: setup, design, extensions, and ecosystem.
- note `/search` and `/api` were not used. External exact-alias discovery was
  followed by low-frequency direct reads of ten free public note pages.
- Nine are Pi-primary and ready for curator review. One three-repository roundup
  is retained as `not_ready` to document why a superficially relevant result
  does not meet the Pi-primary gate.
- Five-row discovery shortage and six-row ready shortage remain. Generated
  code, numerical benchmark claims, and version-sensitive commands require
  independent verification.

### HackerNoon

- Intents: Pi extensions/remote operations and Pi TUI/theme compatibility.
- Because current robots/terms reject generic crawlers, both canonical stories
  were read only through an ordinary user-visible Chrome session. No generic
  HTTP crawler was used for the story bodies.
- One story gives a VPS/SSH extension case with a lockout safety lesson; the
  other supplies an eight-color Linux VT theme workaround. HackerNoon's
  translated copies are the same stories and were excluded.
- Thirteen-row shortage remains. Resume with focused user-browser searches for
  new canonical English stories; do not count translations as new objects.

### Hashnode

- Intents: exact former-name matches, Pi ecosystem, and Pi orchestration.
- External discovery was followed by ordinary Chrome reads of four public
  canonical articles; no `/api`, unauthorized GraphQL, or publication-owner
  data route was used.
- Two exact `pi-mono` titles are false positives: their bodies discuss generic
  LangChain/test tooling or an unrelated imaginary monorepo. They are explicit
  `not_ready` negative evidence.
- Two other articles contain genuine Pi passages, but Pi is secondary to
  Claude Code/OpenClaw or Symphony, so both remain `metadata_only`. Hashnode has
  zero curator-ready rows and a 15-row ready shortage.
- Resume by discovering Pi-primary Hashnode posts and reading them in a normal
  browser; publication-owner authorization would be required before API use.

### Product Hunt

- Intents: launch/product positioning and user adoption/reviews.
- The ordinary public Chrome page was used; site HTML was not scripted with
  curl and no API was called because no authorized Product Hunt token exists.
- The primary product launch page is ready for curator review. The separate
  reviews route is `metadata_only` because it overlaps the same product object
  and contains mutable user claims. Alternatives, awards, customers, and team
  routes were not used as independent Pi content.
- Thirteen-row discovery shortage remains. Product Hunt appears content-scarce
  for this exact project. Resume only with a user-browser search or an
  authorized noncommercial API token; never vote, comment, follow, or scrape.

## Ambiguity and duplicate controls

- Excluded Raspberry Pi, Pi Network, mathematical pi, policy iteration, and
  unrelated same-name tools.
- HackerNoon translations are duplicates of the English canonical story.
- Product Hunt subroutes are not automatically separate objects.
- Hashnode misleading-title cases remain explicit negative outcomes rather
  than being silently promoted.
- Release notes remain separate because each is a stable, versioned,
  independently readable first-party change object; the primary curator may
  still decide how many sibling releases add enough learning value.

## Reproduction and validation

```bash
python3 scripts/build_web_ecosystem_discovery.py
python3 scripts/validate_web_ecosystem_discovery.py
```

The builder is deterministic and network-free: it preserves the evidence read
on this run. The validator checks all 19 fields, the seven-platform boundary,
HTTPS URLs, unique IDs/URLs, allowed local states, non-empty readback evidence,
at least two recorded intents per platform, and platform-specific disallowed
routes/duplicate patterns. Re-running the research itself requires repeating
the browser/robots-aware readbacks described above.
