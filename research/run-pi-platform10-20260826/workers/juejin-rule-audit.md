# Juejin rule audit (worker-isolated)

Checked: 2026-08-26 (Asia/Shanghai)

Status: **do not accept the current base `juejin` rule unchanged**. This file is evidence for the primary curator; it does not edit or override a shared rule ledger.

## Official-source readback

- `https://juejin.cn/robots.txt` returned HTTP 200. It disallows `/search`, `/s/`, `/creator`, `/editor`, `/spost` and other platform/account routes. Public `/post` is not listed as disallowed, and the file publishes post sitemaps.
- `https://juejin.cn/terms` is the official user agreement (updated 2025-12-10, effective 2025-12-24). Sections 2.6, 6.1–6.2 and 10.1 restrict unauthorized vertical search, copying/reformatting, and use of robots/spiders to acquire, monitor, copy, disseminate, display, mirror, upload, or download content.
- `https://api.juejin.cn/robots.txt` returned HTTP 404. The absence of a robots file is not authorization to use an undocumented API.

Recommended `official_rule_readback`:

> 2026-08-26 readback of robots.txt and official user agreement: robots disallows platform search/account/editor routes while leaving public `/post` unlisted and publishing post sitemaps; agreement §§2.6, 6.1–6.2 and 10.1 restrict unauthorized vertical search, copying and spider/bot acquisition. API robots returned 404 and grants no authorization.

## Curator recommendation

Narrow discovery to external exact-site discovery. Restrict readback to low-volume, one-at-a-time ordinary user-browser visits of already known public `/post` URLs. Do not use automated Juejin search, undocumented APIs, bulk crawling/extraction, or any login, like, collect, follow, comment, share, or publishing action.

The base row's `coverage_state=complete`, `fetched_count=15`, and note that all fifteen original bodies were read are not supported by its pre-supplemental worker shard: `china-candidates.jsonl` has only three Juejin rows and two unique Juejin URLs after exact-URL deduplication (one row duplicates the accepted seed). With this isolated supplemental set, the evidence can support one accepted seed + one curator readback of an existing distinct queue item + eight distinct new originals, subject to primary-curator import and acceptance. It still cannot retroactively validate the old count claim.
