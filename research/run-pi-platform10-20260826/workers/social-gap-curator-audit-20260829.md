# Social-gap curator audit (2026-08-29)

This artifact records a bounded, fail-closed audit of the existing worker queue.
The initial audit did not create candidates; a later same-day Weibo sitemap
follow-up independently read two public `/2/detail/` bodies and promoted them
under IDs `china-weibo-pi-autoresearch-20260829` and
`china-weibo-pi-minimal-philosophy-20260829`. All other platform probes remain
non-promotional.
Canonical URLs and candidate IDs below were compared against the current queue
and accepted ledger; no new URL was fetched in this audit.

## Existing queue rows that remain non-promotable

| candidate ID | platform | decision | reason |
|---|---|---|---|
| `worker-global-076` | Medium | reject/hold | The canonical story is member-only. Only title/author/date and a limited public excerpt are visible; the hidden body was not accessed. |
| `social-medium-pi-vs-opencode-member` | Medium | reject/hold | The canonical story is member-only. A title/excerpt cannot satisfy the original-body readback gate. |
| `worker-global-078` | Substack | do not promote | Its URL is the same canonical object already accepted as `seed-substack-47-pi-agent-vs-claude-code-code-review`; the worker row is a duplicate label, not a second object. |
| `worker-global-079` | Substack | do not promote | Its URL is the same canonical object already accepted as `seed-substack-48-pi-web-browse-web-ssrf`; the worker row is a duplicate label, not a second object. |
| `web-producthunt-reviews` | Product Hunt | reject/hold | `/reviews` is a subroute of the accepted `sparse-producthunt-pi-launch` product object. Reviews/comments are mutable product-page material, not an independent original content object; this row is metadata-only. |
| `social-linkedin-thinkrail` | LinkedIn | reject/hold | The numeric share URL redirected to the normal signup gate during the prior ordinary readback. Visible search metadata did not establish a readable canonical body or exact object type. |
| `social-gap-x-yusukebe-lai` | X | reject/hold | The post is a short recommendation/card linking the already accepted Google-platform `google-lai-so-pi-coding-agent` technical original. It is a distinct social object but too thin to use as another technical-body representative in this quota run. |

## Existing accepted rows checked for social-cluster drift

The following platform families already have ten accepted rows in the current
ledger and were not re-fetched: X, Bluesky, Reddit, V2EX, Bilibili, LinkedIn.
For Bilibili, the accepted rows are based on public detail/chapters rather than
an unobserved video claim; no metadata-only video was promoted in this audit.

## Public access stops (no bypass)

* **Weibo:** the sitemap-discovered exact IDs `QBbmHyEtb` and `QtrDaaB5D`
  returned full anonymous `/2/detail/` bodies (HTTP 200) and were independently
  read and promoted as two novel worker/candidate rows. Search snippets remain
  discovery-only; the existing Wake post is a separate object. A bounded
  control GET of the Wake URL also returned HTTP 200.
* **Douyin:** direct details found through external discovery displayed the
  normal “请登录后继续使用抖音” gate or a loading shell, with no title/body/
  subtitle that could be read. The existing Pi SDK row explicitly contains
  platform AI-generated chapters, not a human transcript; this audit does not
  upgrade it.
* **Xiaohongshu:** the public explore surface displayed phone/QR login. No
  candidate was retained from cards or snippets; a normal logged-in browser
  session is required for any future note readback.
* **Kuaishou / WeChat Channels:** useful discovery/detail routes remained behind
  normal login/QR or risk-control boundaries. No workaround, scraping, or
  snippet substitution was attempted.
* **TikTok:** no approved Research API credentials are configured and the
  ordinary public route may require login/region verification. No candidate was
  created.

These stops are reproducible access boundaries under the curator-accepted
platform rules. Resume only with a normal user-assisted session or separately
authorized API, preserving the platform's login, CAPTCHA, robots, rate and
interaction restrictions.

## Result

Two novel Weibo candidate IDs were added and explicitly promoted after
canonical-body readback; no other candidate ID or URL was added. The detailed
HTTP probes, response hashes, and shell/gate outcomes are in
`blocked-platform-probes-20260829.jsonl`.
