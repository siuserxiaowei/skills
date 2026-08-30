# Blocked/public-platform bounded probes (2026-08-29)

The JSONL ledger records one-at-a-time public GET probes with status, byte
count, response hash, and a short visible prefix. No login, CAPTCHA solving,
interaction, media download, API token, or access-control bypass was used.

## Outcomes

- **Weibo:** sitemap-discovered `/2/detail/` URLs `QBbmHyEtb` and `QtrDaaB5D`
  rendered complete Pi-related post bodies anonymously (HTTP 200). They were
  independently read and promoted under `china-weibo-pi-autoresearch-20260829`
  and `china-weibo-pi-minimal-philosophy-20260829`. Existing Wake URL was used
  only as a control; no duplicate candidate was created.
- **Xiaohongshu:** `/explore` returned the public shell with login prompt; no
  Pi note detail was exposed. Remains blocked pending normal logged-in browser.
- **Kuaishou:** `/new-reco` rendered “登录即可享受” shell; no candidate body.
- **WeChat Channels:** landing page returned JavaScript-required
  `finder-helper-web` shell; no video detail/transcript.
- **WeChat Official Accounts:** `mp.weixin.qq.com/` returned account
  login/QR/CAPTCHA UI; no article body.
- **TikTok:** public search returned a shell carrying login/region/risk/CAPTCHA
  assets and no Pi result body; Research API token is absent.
- **Douyin:** known and unknown `/video/` IDs returned the same JSVM shell to a
  bounded HTTP client. Existing Pi SDK item remains AI-chapter metadata only;
  no human-watch claim was added.
- **Stack Overflow:** official Stack Exchange API exact `pi-coding-agent`
  query returned HTTP 200 with `items: []`; no candidate created.
- **Product Hunt:** API endpoint without a token returned 404; `/reviews` is
  the already represented product subroute and was not counted separately.

The append-only probe data is in `blocked-platform-probes-20260829.jsonl`.
