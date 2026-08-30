# Social / publishing public-gap supplemental shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26` (Asia/Shanghai)
Candidates: `social-public-gap-candidates.jsonl`
Independent readbacks: `social-public-gap-curator-readbacks.jsonl`

This shard is limited to X, Medium, LinkedIn, Substack, HackerNoon, and Product
Hunt. Every ready row was opened as an ordinary user-visible canonical object.
The candidate shard contains nine novel URLs: eight X statuses and one LinkedIn
post. The readback shard also contains nine overrides that reuse existing queue
IDs for already-known URLs. No row is accepted here, and this shard does not
modify `candidates.json`.

## Outcome

| Platform | Ready rows | Important boundary |
|---|---:|---|
| X | 8 | Native search hit a normal login gate; one focused external exact-site discovery query located canonical status URLs, then every ready candidate was read on X itself. |
| Medium | 2 readback overrides | Two existing queue IDs gained full public body readbacks. David Min remained member-only and was not added. |
| LinkedIn | 3 (2 overrides + 1 novel candidate) | Three stable `/posts/...activity-...` guest pages exposed full post text; the ThinkRail share URN redirected to signup and remains metadata-only outside this shard. |
| Substack | 2 readback overrides | Two free canonical bodies were read; subscribe modals were not used. |
| HackerNoon | 2 readback overrides | Both stories were read only in an ordinary browser. No generic HTTP crawler or site HTML search was used. |
| Product Hunt | 1 readback override | Only the canonical product object is retained. Reviews, comments, alternatives, customers, makers, pages, and launch navigation are not independent objects. |

## Native readback evidence

- X status details exposed author/handle, full post text or native article card,
  stable status ID, and exact timestamp for all eight rows. No likes, replies,
  reposts, follows, bookmarks, messages, or login actions occurred.
- Medium exposed full public bodies for Ga Satrya and Ritza Editor. David Min's
  page visibly said `Member-only story`; only title, author, date, subtitle, and
  the limited public opening were visible, so it remains non-promotable.
- LinkedIn guest pages exposed David Schargel's full 12-point tips, Tanishq K.'s
  complete minimal-base-layer argument, and Corey Cole's deterministic-docs
  post plus visible counterarguments. Exact dates absent from current relative
  labels remain `unknown`, except David retains the frozen worker date basis.
- Substack exposed complete free post bodies and dates. Andrew explicitly calls
  his post a condensed version; Zazen explicitly discloses MiniMax sponsorship.
- HackerNoon exposed full bylines, dates, and bodies through the visible story
  UI. Translation routes were observed as siblings and excluded as duplicates.
- Product Hunt exposed the title/tagline, Pi description, launch team, official
  site/GitHub links, `Launched in 2026`, comments, and reviews. Mutable social
  claims are limitations, not additional candidates.

## Global URL and content-cluster audit

- All 18 canonical URLs were compared against current accepted URLs and worker
  queue URLs. None overlaps an accepted URL. Nine URLs already existed in the
  queue, so their original IDs are reused in the readback file rather than
  introducing duplicate candidate rows: `worker-global-074`, `-075`, `-077`,
  `-080`, `-081`, `-082`, `sparse-hackernoon-ssh-extension`,
  `sparse-hackernoon-vt-theme`, and `sparse-producthunt-pi-launch`.
- The candidate shard therefore contains the eight novel X candidates plus
  `social-gap-linkedin-corey-docs`, a novel LinkedIn canonical URL discovered
  during ordinary public readback.
- Yusuke Wada's X post links the already accepted Google-platform object
  `google-lai-so-pi-coding-agent`. The X post is a distinct native social object,
  not a second technical-original body; retain this distinction during content
  cluster review.
- Curator recommendation: reject `social-gap-x-yusukebe-lai`. Its native body is
  only a brief recommendation/link card, while the Pi-primary technical body is
  already accepted as `google-lai-so-pi-coding-agent`; accepting both would pad
  one content cluster with a thin cross-platform referral object. The other
  seven novel X rows remain recommended for explicit promotion.
- Ga Satrya's Medium footer says the story was first published at gasatrya.com.
  Only one technical-body representative should survive any future cross-host
  expansion.
- Andrew's Substack is explicitly a condensed version of an andrew.ooo article.
  Do not count both as independent content bodies.
- Nader Dabit's outer X status and its embedded native X article are one content
  cluster. Only the outer canonical status candidate is emitted.
- Nico Bailon's X post and `github.com/nicobailon/pi-interactive-shell` are
  distinct platform objects about the same project; they must not be described
  as independent reproductions. The GitHub object remains unaccepted.
- HackerNoon `/lang/*` translations are the same two English stories and are
  excluded. Product Hunt product subroutes and all individual comments/reviews
  remain one launch/product cluster.
- Cross-title/creator/summary checks found one deliberate cross-platform content
  cluster (Yusuke's X link and the accepted Google-discovered lai.so original),
  but no exact accepted URL clone. Product Hunt's generic title matches several
  unrelated platform objects by title only; its product URL and body are unique.
  Author/model performance claims remain explicitly non-reproduced.

## Login, paywall, and metadata-only stops

- X native Latest search redirected to a normal login page. It was not bypassed;
  no further native search was performed. Known public canonical status details
  remained readable without login.
- Medium `Pi: Build Your AI Coding Tool Your Way` by David Min and the existing
  `Pi vs OpenCode` comparison are member-only. Their hidden bodies were not read.
- LinkedIn ThinkRail stable share URN redirected to signup. Existing result
  metadata is insufficient and remains outside the ready rows.
- Product Hunt has no authorized API token. No API was called, and no scripted
  HTML route was used. HackerNoon generic automated HTML remains disallowed.

## Official-rule overlay decision

No new rules overlay was added. X, Medium, and LinkedIn already have
curator-accepted official rule reviews. Substack, HackerNoon, and Product Hunt
still have only worker-checked rules in the shared rule ledger; this shard did
not independently re-read every official source required for a curator overlay.
The existing conservative boundary therefore remains in force: ordinary
user-visible public canonical reads only, no automation crawler, no API without
authorization, no interaction, and no gate bypass.

## Validation

```bash
python3 research/run-pi-platform10-20260826/workers/social-public-gap-validator.py
python3 -m py_compile research/run-pi-platform10-20260826/workers/social-public-gap-validator.py
```
