# PyPI / Stack Overflow / TikTok / WeChat Channels follow-up — 2026-08-30

This is an append-only public-read audit. Existing candidate IDs and normalized
canonical URLs were checked before probing. No candidate, accepted ledger, or
queue row was created in this pass.

## PyPI

The fifteen existing `api-packages-pypi-*` rows already have anonymous
canonical project-page body readbacks in
`pypi-stackoverflow-followup-readbacks-20260829.jsonl` and are represented in
the shared accepted ledger. No duplicate project IDs or URLs were added. No
package was downloaded, installed, or executed.

## Stack Overflow

Eight new exact package/repository alias queries were sent to the official
Stack Exchange API (`filter=withbody`, `site=stackoverflow`) at low rate;
all returned HTTP 200 with `items: []` and are recorded in
`stackoverflow-followup3-probes-20260830.jsonl`. Additional alternate-endpoint
checks are in `stackoverflow-followup4-probes-20260830.jsonl`: `search` with
`intitle=pi coding agent` and the exact `pi-coding-agent` tag-info route both
returned zero items. The alternate `/questions?intitle=pi-coding-agent` route
returned generic unrelated questions (100 records), so none was promoted.
One malformed alternate query returned HTTP 400; it yielded no content and no
candidate. No HTML scraping or account action occurred.

## TikTok

Unauthenticated exact search/tag routes returned HTTP 200 shells carrying
login/region/risk/CAPTCHA assets but no public Pi result body. An unauthenticated
search endpoint for `earendil-works/pi` returned an empty response. These probes
are recorded in `tiktok-wechat-channels-followup-probes-20260830.jsonl`.
No Research API approval/token is configured; no login, CAPTCHA, region bypass,
or interaction was attempted. Therefore no TikTok candidate is valid.

## WeChat Channels

The public root returned the JavaScript-required `finder-helper-web` shell;
the public feed route with `keyword=Pi` returned HTTP 200 JSON
`Illegal request` (`errCode=10012`). `robots.txt` exposes only narrow landing
routes and no searchable content. Exact response sizes and SHA-256 values are
in the same JSONL probe file. No QR/login bypass or candidate creation was
attempted.

Result: no new promotable object; Stack Overflow remains a reproducible
zero-result/partial platform, while TikTok and WeChat Channels remain blocked
pending approved API or normal user-assisted read-only detail access.
