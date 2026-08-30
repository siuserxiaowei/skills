# Remaining platform-rule curator audit

- Run: `pi-platform10-20260826`
- Review date: `2026-08-26` (Asia/Shanghai)
- Reviewer: `primary-curator-codex`
- Scope: the 20 platform rules named in `remaining-rule-curator-reviews.tsv`
- Decision: all 20 conservative rule overlays are `curator_accepted`

`curator_accepted` here means that the curator accepts a fail-closed discovery and
readback boundary. It does **not** mean that a platform is unblocked, that an API
key or account is authorized, or that any content object has passed content
acceptance.

The exact official URLs were taken from the current `platform_rules.tsv` rows.
Official pages were re-read in ordinary browser sessions where reachable. When a
policy endpoint returned `403`, `451`, a regional block, or a client-side block,
that result was preserved and the same-day published-rule capture in the worker
rule row was used only to maintain or narrow the boundary. No login, token
creation, CAPTCHA handling, alternate proxy, scripted site-HTML crawler, or
access-control bypass was used.

## Governing curator boundary

Browser readability is evidence that an ordinary user can currently see a
particular page. It is **never** permission to scrape, crawl, call an API, train a
model, copy a corpus, or bypass the platform's published restrictions. The
narrowest of robots, Terms, API documentation, authentication, paywall,
challenge, regional, rate-limit, content-license and ordinary-visibility
boundaries controls each route.

Across every platform:

- search snippets, cards and landing metadata are discovery-only;
- acceptance requires a canonical body, native detail, platform-provided
  transcript, or authorized API detail plus the normal provenance fields;
- login, QR verification, CAPTCHA, paywall, JavaScript challenge, security check,
  regional block, `403`, `451`, `404`, quota and `429` responses are hard stops;
- no votes, likes, follows, comments, reposts, favorites, collections,
  subscriptions, messages, publishing, downloads, uploads or account mutations
  are permitted by this review; and
- public visibility does not supply reuse, redistribution, copyright, training or
  security rights.

## Chinese publishing and video platforms

### `wechat_official_accounts`

Source observation:

- `https://mp.weixin.qq.com/robots.txt` — the current published rule capture
  denies wildcard root access except narrow public landing routes. The fresh
  ordinary-browser navigation to the policy file was client-blocked, so the
  review did not substitute an automated fetch.

Route and boundary: only a canonical article that the user opens through a
normal authenticated WeChat browser may be read. Article search/crawl, QR or
anti-abuse automation, and snippet acceptance are prohibited. Exact probes
produced zero public candidates; the platform remains blocked until legitimate
user-assisted readback exists.

### `zhihu`

Source observation:

- `https://www.zhihu.com/robots.txt` — independent same-day readback returned
  `200`; `User-Agent: *` allows `/tardis/jm` and disallows `/`. Known public
  `zhuanlan` bodies were separately readable without login, while the current
  root route redirected to sign-in.

Route and boundary: external exact-site discovery may locate a finite, already
known public column URL; only a bounded ordinary-browser canonical-body read is
allowed. No automated Zhihu search/crawl is inferred, and login or challenge is
a stop. Peripheral mentions remain ineligible even if readable.

### `xiaohongshu`

Source observation:

- `https://www.xiaohongshu.com/robots.txt` — the current published rule capture
  is `User-Agent: *` plus `Disallow: /`. Fresh policy-file navigation was
  client-blocked. The visible explore route displayed QR/phone login and public
  recommendation cards, which do not authorize automation or establish a
  canonical note readback.

Route and boundary: a user may manually open a note after normal login; the
reviewer may then record only the visible title, creator, date, body and URL.
Search, note retrieval, QR/CAPTCHA and risk-control automation are prohibited.
Exact probes produced zero public candidates.

### `weibo`

Source observation:

- `https://weibo.com/robots.txt` — independent same-day readback returned `200`.
  The `ChatGPT-User` block explicitly allows `/2/detail/` and
  `/ttarticle/p/show`, publishes a sitemap, sets `Crawl-delay: 1`, and declares
  `ai-train=no`; generic root access remains disallowed.

Route and boundary: use external discovery only to locate an already-known
canonical `/2/detail/`, then perform a low-volume ordinary anonymous read no
faster than the published delay. Internal search, bulk extraction, training,
challenge bypass and all interactions remain prohibited. Anonymous detail
readability does not broaden the route.

### `douyin`

Source observation:

- `https://www.douyin.com/robots.txt` — independent same-day readback returned
  `200`. Named-agent blocks disallow follow and search/`enter_from`/`vid`
  variants; the Baiduspider block separately disallows video. A clean, already
  known `/video/` detail was anonymously readable in an ordinary browser.

Route and boundary: only a bounded direct read of the clean known `/video/`
detail is accepted. Search, creator-list probing, media extraction, automated
playback/download and interaction are prohibited. Platform AI-generated
chapters are labelled metadata, not a human transcript or independently
verified technical account.

### `toutiao`

Source observation:

- `https://www.toutiao.com/robots.txt` — independent same-day readback returned
  `200` and disallows `/search`, `/item`, `/group`, `/trending` and
  traffic-aggregation routes; clean `/article/` is not listed.

Route and boundary: bounded external exact-site discovery may lead to a known
`/article/`, followed by one ordinary anonymous canonical-body read. A public
article can still return `404` or be an explicitly credited syndication; those
outcomes must be recorded rather than repaired or counted as an original. No
automated search, aggregation or crawl permission is inferred.

### `36kr`

Source observation:

- `https://www.36kr.com/robots.txt` — independent same-day readback returned
  `200` and disallows `/search`, `/api`, `/detail`, account and project-detail
  routes, while clean `/p/` is not listed. The current homepage displayed a
  normal security check, which was not bypassed.

Route and boundary: use external discovery and low-volume ordinary-browser reads
of already-known public `/p/` canonical URLs only after normal access succeeds.
Do not automate restricted routes. Syndicated benchmark and conference bodies
remain in the same content cluster as their credited InfoQ representative.

### `infoq`

Source observation:

- `https://www.infoq.cn/robots.txt` — the independent plain policy probe returned
  HTTP `451` with a user-agent blacklist response; fresh browser policy-file
  navigation was also client-blocked. The ordinary homepage and known article
  bodies were visible, but that visibility did not relax the rule.

Route and boundary: fail closed to external discovery plus low-volume reads of
already-known canonical articles. Preserve the existing restriction against
automated internal search and data/content/feed routes, stop if circumvention is
needed, and deduplicate matching 36Kr syndications.

### `oschina`

Source observation:

- `https://www.oschina.net/robots.txt` — independent same-day readback returned
  `200`, disallows `/action`, `/admin`, `/code/download_src`, `/webVisit` and
  `/search`, and publishes sitemaps. Known blog/software canonical details could
  render anonymously after an ordinary wait.

Route and boundary: bounded external discovery or already-known canonical
details may be read after normal dynamic rendering. No internal search, bulk
sitemap traversal, API reverse engineering, download or shell-only acceptance
is authorized.

### `kuaishou`

Source observation:

- `https://www.kuaishou.com/robots.txt` — the current published capture contains
  named-bot rules but gives `User-Agent: *` `Disallow: /`. Fresh policy-file
  navigation was client-blocked. The public recommendation shell explicitly
  offered login for useful personalized functions.

Route and boundary: useful discovery and video/transcript readback remain
user-assisted in a normal logged-in browser. The research user agent has no
generic automation grant. Exact probes produced zero public candidates, and no
snippet or automated workaround may replace the missing canonical readback.

### `wechat_channels`

Source observation:

- `https://channels.weixin.qq.com/robots.txt` — the current published capture
  denies generic root access except narrow public landing routes. Fresh
  policy-file navigation was client-blocked, and the root redirected to the
  WeChat Channels login page.

Route and boundary: only a user-opened canonical video or creator transcript
after normal WeChat/QR verification is usable. Landing-page readability is not
content access. Exact probes produced zero public candidates; no QR/CAPTCHA,
search or retrieval automation is permitted.

## Global community, research and package platforms

### `tiktok`

Source observations:

- `https://developers.tiktok.com/docs/en/about-research-api` — Research Tools
  expose specified public video, comment and account fields to approved
  independent or academic researchers working on a non-profit basis; an
  application and approval are mandatory.
- `https://developers.tiktok.com/doc/research-api-faq/` — the canonical page
  redirected to the current FAQ. A developer account alone is insufficient;
  approval is project-specific. The FAQ documents 1,000 requests and up to
  100,000 records per day for the main APIs, with separate follower/following
  limits, and states that creators, advertisers and commercial users are not
  eligible for Research Tools.
- `https://developers.tiktok.com/docs/en/tiktok-api-v2-rate-limit` — rate limits
  are enforced per endpoint on a one-minute sliding window; excess requests
  return HTTP `429` and `rate_limit_exceeded`.

Route and boundary: no Research API approval or token was configured. Use only a
separately approved project within its stated scope or a normal user-assisted
public video read. Preserve login, regional and CAPTCHA gates, honor quotas and
`429`, and never interact. Exact probes produced zero public candidates.

### `stackoverflow`

Source observations:

- `https://stackoverflow.com/legal/acceptable-use-policy` — prohibits automated
  Network-site extraction for generative-AI/model development, training,
  testing, indexing, benchmarking or improvement, and any volume that harms the
  service, absent express written consent.
- `https://stackoverflow.com/legal/api-terms-of-use` — the documented API is the
  programmatic query route and requires visible Stack Exchange attribution.
- `https://api.stackexchange.com/docs/throttle` — more than 30 requests per
  second per IP is described as very abusive; anonymous/keyed applications have
  daily quotas, `backoff` must be obeyed, and semantically identical requests
  should not recur more than once per minute.

Route and boundary: use only bounded public Stack Exchange API discovery and
`filter=withbody` detail readback under the API Terms; do not scrape site HTML or
train on the result. Four exact API intents returned zero strictly relevant Pi
objects, which remains a legitimate zero-result outcome.

### `product_hunt`

Source observations:

- `https://www.producthunt.com/legal` — prohibits crawling, scraping or
  spidering pages/data by manual or automated means and storing a significant
  portion of the content.
- `https://www.producthunt.com/v2/docs` — API v2 is token-only GraphQL; apps are
  public read-only by default, are subject to fair-use rate limiting, and may
  not use the API commercially without separate approval.
- `https://help.producthunt.com/en/articles/484971-does-product-hunt-have-an-api`
  — the official help page tells developers to sign in, visit My Apps, configure
  an application and follow the API documentation.

Route and boundary: generic automated HTML is prohibited. A bounded ordinary
user-visible canonical product read is permitted as normal browsing; automated
discovery/detail requires a separately authorized API token. No token was
created. Comments, reviews, alternatives, customers, makers and subroutes are
components of one product object, not independent candidates.

### `substack`

Source observations:

- `https://substack.com/tos` — prohibits crawling, scraping or spidering any
  page/data by manual or automated means and copying or storing a significant
  portion of Substack content.
- `https://substack.com/api-tos` — Authorized Data is limited to public
  creator/publication fields; caching must be necessary and refreshed/deleted,
  rate limits and access controls may not be bypassed, standalone dataset
  redistribution is prohibited, and source attribution/deletion are required.
- `https://substack.com/content` — preserves intellectual-property, privacy,
  anti-spam and anti-harvesting rules and confirms that restricted or removed
  material can leave public discovery.

Route and boundary: use a bounded ordinary browser for a known free public post,
or a separately authorized Developer API only for its stated metadata scope.
Never automate publication HTML or bypass a paywall, login, subscribe modal or
challenge. One free canonical Pi post was visibly readable; this does not grant
corpus copying.

### `arxiv_openreview`

Source observations:

- `https://info.arxiv.org/help/api/index.html` — confirms public metadata API
  access, asks independent projects to acknowledge arXiv data use, and forbids
  branding that implies endorsement; commercial projects must review the
  relevant program and affiliate guidance.
- `https://info.arxiv.org/help/api/user-manual.html` — documents the Atom query
  API, recommends a three-second delay between consecutive calls, limits slices
  to 2,000, recommends refining result sets above 1,000 and caching identical
  daily results.
- `https://docs.openreview.net/getting-started/using-the-api` — API 2 is the
  current default and API 1 is legacy and still used by some older venues; the
  response formats differ.
- `https://openreview.net/legal/terms` — returned HTTP `403` in the current
  ordinary-browser session and was not bypassed.

Route and boundary: use polite, bounded arXiv Atom searches plus public
abstract/HTML/PDF readback under each work's license. Use only public OpenReview
notes allowed by their `readers`/access controls, never nonpublic notes or
submission/review/comment actions. OpenReview metadata may be CC0; full works
retain their own licenses. Terms inaccessibility narrows rather than expands the
route.

### `hackernoon`

Source observations:

- `https://hackernoon.com/robots.txt` — the same-day published capture defaults
  unknown crawlers to `Disallow: /`, distinguishes named real-time
  retrieval/search agents that are allowed, and blocks training crawlers. Fresh
  policy-file navigation was client-blocked.
- `https://hackernoon.com/terms` — directly re-read Terms prohibit robots or
  other automatic site access, manual monitoring/copying without written
  consent, searchable-database indexing, user mining, security-limit
  circumvention and overloading.
- `https://hackernoon.com/llms.txt` — the current published AI-access capture was
  reviewed alongside robots; it does not override the Terms or create a grant
  for an unnamed generic crawler. Fresh file navigation was client-blocked.

Route and boundary: only ordinary user-visible canonical-story readback or a
currently explicit permitted retrieval agent is acceptable. A successful HTTP
or browser page load is not permission for generic scripted HTML/search.
Signup, subscription, reactions, comments, publishing and contact harvesting
are prohibited; translations remain duplicates.

### `hashnode`

Source observations:

- `https://hashnode.com/robots.txt` — the current published capture allows
  public pages but disallows `/api` and private dashboard/profile/draft routes.
  Fresh policy-file navigation was client-blocked.
- `https://hashnode.com/terms` — direct readback prohibits scraping/crawling that
  exceeds reasonable use, rate-limit circumvention and API harvesting from
  publications the caller does not own or have authorization to access; the API
  may be throttled or suspended.

Route and boundary: use external discovery or a publication sitemap, followed
by an ordinary canonical public-article read. GraphQL is limited to owned or
explicitly authorized publication data. Never bypass a JavaScript/cookie
challenge or automate login. The current content review yielded zero Pi-primary
objects: two false positives and two Pi-secondary pages remain unaccepted.

### `bluesky`

Source observations:

- `https://docs.bsky.app/docs/api/app-bsky-feed-search-posts` — redirected to the
  current official HTTP API reference, which states that most `app.bsky.*` GETs
  are public without a token at `https://public.api.bsky.app`; authenticated
  calls should route through the user's PDS.
- `https://docs.bsky.app/docs/advanced-guides/rate-limits` — redirected to the
  current rate-limit guide, which requires operators' response headers and
  backoff to be respected and identifies HTTP `429` for crossed limits.
- `https://bsky.social/about/support/tos` — authors retain ownership of their
  content; Bluesky's service license does not grant third parties automatic
  reuse rights.

Route and boundary: both `public.api.bsky.app` and `api.bsky.app` returned
regional HTTP `403` in this run. Do not proxy or otherwise circumvent that
block. Retry later or use a normal user-assisted public view; honor deletions,
blocks, attribution and copyright, and perform no write or interaction calls.

### `pypi`

Source observations:

- `https://pypi.org/robots.txt` — the current published capture excludes
  crawler access to `/search`, JSON API and `/simple` routes; fresh policy-file
  navigation was client-blocked.
- `https://docs.pypi.org/api/index-api/` — documents PyPI's PEP 503 HTML and PEP
  691 JSON Index API, including project distribution URLs, hashes, yanked state
  and core-metadata signals.
- `https://docs.pypi.org/api/json/` — documents project/release JSON metadata and
  explicitly warns that metadata is supplied at upload time and may not match
  distribution contents; several response keys are deprecated.
- `https://policies.python.org/pypi.org/Terms-of-Service/` — API use is covered
  by the Terms; abusive or excessively frequent requests may be suspended, API
  tokens may not be shared to exceed limits, and API data may not be collected
  for spam.

Route and boundary: discover a known package name externally, then use its
canonical public project page. Automated package-index access must use a
standards-compliant client and documented Index semantics with caching and
backoff, not a bulk website/search/JSON crawl. No package installation or file
download occurred. Project existence and upload-supplied metadata are neither
provenance nor a security/quality endorsement.

## Zero-result and gate ledger

| Platform | Preserved outcome |
|---|---|
| WeChat Official Accounts | Exact probes produced no public candidate; authenticated user handoff remains required. |
| Xiaohongshu | Exact probes produced no public candidate; login/QR/CAPTCHA boundaries remain intact. |
| Kuaishou | Exact probes produced no public candidate; no generic research-UA automation grant exists. |
| WeChat Channels | Exact probes produced no public candidate; root resolves to login and narrow landing routes are not evidence. |
| TikTok | Exact probes produced no public candidate; Research API approval and credentials are absent. |
| Stack Overflow | Four exact official-API intents produced no strictly relevant Pi result. |
| Bluesky | Both public AppView hosts returned regional `403`; no proxy fallback was used. |
| OpenReview | Official Terms returned `403`; public/readers/license boundaries were retained. |
| InfoQ | Official robots probe returned `451`; no user-agent or alternate-route circumvention was attempted. |

No shared candidate set, review queue, ledger, manifest, handoff, library,
`platform_rules.tsv`, or `curator-rule-reviews.tsv` was rebuilt or modified by
this isolated audit.
