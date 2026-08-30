# Social-global Pi canonical readback shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26` (Asia/Shanghai)
Machine-readable shard: `social-global-candidates.jsonl`

This is an isolated, read-only discovery/readback artifact for required global
social platforms. Rows are worker evidence only. `curator_review_ready` means a
canonical object was read and may be reviewed by the primary curator; it does
not mean `accepted`.

## Read-only boundary

No likes, follows, votes, comments, messages, posts, subscriptions, login
bypass, CAPTCHA bypass, paywall bypass, or other interaction was performed.
Search/result pages were used only for discovery. Every ready row was opened as
a canonical platform detail object and its body and platform metadata were
read. Relative Reddit labels were not converted to dates; exact ISO timestamps
came from the canonical thread's `time[datetime]` attribute.

## Coverage outcome

| Platform | Rows | Ready | Metadata only | Executed query intents | Shortage to 10 |
|---|---:|---:|---:|---:|---:|
| Reddit | 10 | 10 | 0 | 2 | 0 |
| X | 3 | 3 | 0 | 2 | 7 |
| Medium | 6 | 5 | 1 | 2 | 4 |
| LinkedIn | 7 | 6 | 1 | 2 | 3 |

Two actual read-only Reddit intent routes were executed:

- `reddit-native-search-pi-coding-agent`: the public Reddit Pi query and the
  public `r/PiCodingAgent` feed were inspected, then selected canonical threads
  were read.
- `reddit-native-search-pi-coding-agent-extensions`: the public subreddit
  native search for `extension` was inspected, then extension-focused canonical
  threads were read.

The 10 Reddit objects cover unattended execution, local-model troubleshooting, memory
extensions, benchmark claims, filesystem overreach, writing-style extensions,
cross-harness session search, plan/PR verification, filesystem/network
sandboxing, and extension validation. Community assertions remain author claims
unless independently reproduced; limitations are stated row by row.

X rows were read through native Latest search and canonical post detail. Medium
rows were read as ordinary public story pages; one member-only comparison keeps
only its visible public metadata/excerpt. LinkedIn rows use native search and
stable share/UGC URN detail objects; one unresolved share-vs-UGC object remains
metadata-only. No metadata-only row is eligible for acceptance without a fresh
canonical detail/body readback.

## Other social platforms

- Existing frozen run evidence and accepted seeds were cross-checked; the
  Medium David Min exact URL was not duplicated. A novel Owain Lewis Substack
  row remains owned by the separate sparse-global shard, so it is also not
  duplicated here.
- TikTok and Bluesky were not padded with search snippets or alternative
  search-engine results. A canonical object must remain readable through a
  rules-compliant route before it can be added.
- Product Hunt remains represented only by the separate web-ecosystem shard;
  product subroutes are not counted as independent content objects.

## Official rule readback

These official pages were independently opened and read on 2026-08-26. The
routes below are deliberately more conservative than merely being technically
reachable.

### Reddit

- `https://redditinc.com/policies/data-api-terms` (last revised 2026-07-20)
  requires authorized Access Info/OAuth and truthful user-agent/identity for
  API access, forbids rate-limit circumvention, limits retention/use, preserves
  user ownership, and says commercial or above-limit research may need a
  separate agreement.
- `https://redditinc.com/policies/developer-terms` (last revised 2026-03-24)
  also requires authorized access, honoring deletion/removal, no masking or
  bypass, and compliance with use limits.
- This shard did not use the API. It used two bounded native public queries and
  canonical thread views, with no account or engagement action.

### X

- `https://x.com/en/tos` says access must use currently available published
  interfaces, prohibits scraping without express written permission and
  working around technical limits, and incorporates developer terms for
  developer features.
- `https://help.x.com/en/rules-and-policies/x-automation` (updated April 2026)
  forbids non-API website automation/scripting and rate-limit circumvention;
  it also prohibits automated likes and restricts bulk/aggressive/duplicate
  actions and unsolicited replies/messages.
- `https://help.x.com/en/rules-and-policies/authenticity` (April 2025) prohibits
  unauthorized automation and content/engagement spam.
- `https://docs.x.com/developer-terms/policy` and
  `https://docs.x.com/developer-terms/agreement` govern approved API/X Content
  use. They require an approved use case, privacy/control safeguards, current
  content/removal handling, rate-limit compliance, strict redistribution
  limits, and prohibit using the API for certain benchmarking, unauthorized
  commercial scope, or foundation/frontier-model training.
- These rows record only bounded user-visible native Latest results and
  canonical post-detail reads. They do not authorize an automated crawler, API
  reuse, bulk collection, login entry, or engagement.

### Medium

- `https://help.medium.com/hc/en-us/articles/213477928-Medium-Rules`
  prohibits automatic/systematic/programmatic interaction and, absent express
  written consent, access/search outside published interfaces, automatic
  devices/crawlers/browser add-ons, and manual copying or monitoring for an
  unauthorized purpose. It also forbids bulk interaction and requires privacy
  and copyright compliance.
- `https://help.medium.com/hc/en-us/articles/214151487-Medium-API-Terms-of-Use`
  requires API authorization and attribution, limits UGC retention, bars
  auto-generated actions and spam, and permits rate limiting.
- These rows are limited to bounded, ordinary user-visible public story
  readbacks; no bulk extraction or interaction was performed. The member-only
  comparison remains metadata-only and its hidden body was not accessed.
  Repeating or scaling this route would require Medium permission or a
  currently published authorized interface.

### LinkedIn

- `https://www.linkedin.com/legal/crawling-terms` says automated crawling or
  indexing requires express permission, must obey authorized paths and robots,
  use true identity, and never circumvent controls.
- `https://www.linkedin.com/legal/user-agreement` (effective 2025-11-03)
  prohibits software/scripts/robots/crawlers/browser add-ons that scrape or copy
  service data, bypassing access controls/use limits, and bots or other
  unauthorized automated access and engagement.
- The recorded route is bounded ordinary user-visible native search/detail
  navigation only, not a crawler, export, API, or bulk-collection workflow. Six
  stable share/UGC objects have visible post-text readback; the unresolved
  ThinkRail object remains metadata-only.

## Validation

```bash
python3 research/run-pi-platform10-20260826/workers/social-global-validator.py
```

The validator checks all required fields, canonical Reddit HTTPS routes,
unique candidate IDs and URLs, the allowed worker evidence states, non-empty
readback evidence, and coverage of both executed intents.
