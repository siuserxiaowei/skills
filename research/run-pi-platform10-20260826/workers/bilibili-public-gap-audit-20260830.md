# Bilibili public gap probe audit (2026-08-30)

This append-only audit supplements the existing 35-object Bilibili watch-evidence review. It does not edit `candidates.json`, `review_queue.json`, or any shared ledger. Existing candidate IDs, BVIDs, and normalized canonical URLs were checked before probing; the five BVIDs below were not present in the current queue/candidates snapshot.

## Discovery and bounded route

A single bounded Google query (`site:bilibili.com/video "Pi Agent" "pi-coding-agent"`) exposed public canonical details. The query surfaced multiple results, but only five distinct Pi-primary objects were selected for a low-rate official API check. No internal Bilibili search automation, bulk crawling, media download, subtitle bypass, login, purchase, or interaction was used.

For each BVID, the official anonymous endpoints were read sequentially with a two-to-three-second delay:

* `GET https://api.bilibili.com/x/web-interface/view?bvid=...` for title, uploader, CID, duration, publication timestamp, description and public subtitle metadata.
* `GET https://api.bilibili.com/x/player/v2?bvid=...&cid=...` for player subtitle state, login requirement and preview/paywall state.

Full response hashes and fields are recorded in `bilibili-public-gap-probes-20260830.jsonl`.

## Probe outcomes

| BVID | Title / uploader | Duration | API subtitle list | Player state | Decision |
|---|---|---:|---:|---|---|
| `BV1aW3V6WEsT` | 一口气学会Pi Agent极简Harness系统设计 / 肖恩君Sean | 22:30 | 0 | `need_login_subtitle=true`; `preview_toast=为创作付费，购买观看完整视频` | not promotable |
| `BV1ZcVJ6nEJd` | pi与oh-my-pi比较 / 原周率加1 | 00:58 | 0 | login-required subtitle; purchase preview | not promotable |
| `BV1zagQ6BEry` | Pi Agent 源码系统课：从真实运行到自己组装 Agent / 幻想家阿星403 | 54:32 | 0 | login-required subtitle; purchase preview | not promotable |
| `BV1FtgK6yEhY` | 01-Pi Agent 架构详解 loop extention TUI / AI_Julie | 42:02 | 0 | login-required subtitle; purchase preview | not promotable |
| `BV1mAEh6jEYU` | Alejandro AO｜必看 Pi Agent 极简入门 / 63号炼金工坊 | 26:34 | 0 | no subtitle exposed; purchase preview | not promotable |

All five canonical pages were also opened in ordinary Chrome. The visible pages confirmed the titles, uploader/date, Pi-focused descriptions and native player state (`登录 免费享高清视频`, `试看30秒`). The first result's description includes a detailed chapter list (Pi's four tools, TUI/CLI/JSON/RPC forms, session tree, skills/extensions/packages); however, chapters and descriptions are discovery metadata, not a transcript or proof of watching. The other four likewise exposed no public transcript in the ordinary page.

## Acceptance decision and next safe step

No new Bilibili candidate is curator-acceptable under `PLATFORM_ACCEPTANCE.md`: every probed object has an empty public subtitle list, and the player API reports a login/purchase preview boundary. No candidate JSONL row was created. These objects remain documented discovery negatives only and must not be counted toward the Bilibili ten-item quota.

The only safe resume paths are (a) a user-assisted normal Bilibili login with ordinary read-only full playback/subtitle inspection, or (b) a creator-provided public transcript. Do not solve CAPTCHA, bypass purchase/login, download media, or infer spoken content from title, description, chapters, counters, or related cards.
