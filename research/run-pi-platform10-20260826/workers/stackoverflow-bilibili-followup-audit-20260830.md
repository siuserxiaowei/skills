# Stack Overflow / Bilibili follow-up audit (2026-08-30)

This append-only audit records a fresh public read-only probe after loading existing candidate IDs and canonical URLs. No candidate, accepted row, shared ledger, or review queue was modified.

## Stack Overflow

Seven new exact/quoted aliases were queried through the official anonymous Stack Exchange API (`site=stackoverflow`, `filter=withbody`, `pagesize=100`, low rate with three-second spacing): `@mariozechner/pi-coding-agent`, `@earendil-works/pi-agent-core`, `pi-coding-agent npm`, `pi-agent-core npm`, title `pi agent harness`, `Pi AgentHarness`, and `pi.dev` + `earendil`. Every request returned HTTP 200 with `items: []`; response bytes were 67 and per-response SHA-256/quota values are in `stackoverflow-followup2-probes-20260830.jsonl`. No exact-alias question body/title appeared, so no candidate was created. This confirms the reproducible zero-result partial state; Raspberry Pi/Mono and generic “agent” results remain excluded.

## Bilibili

Official public Bilibili search pages 1–2 were used only for discovery. Existing BVIDs and canonical URLs were loaded first; ten new, Pi-primary BVIDs were selected for bounded `x/web-interface/view` and `x/player/v2` checks: `BV14JhK6kEPY`, `BV1mUgP6HEVe`, `BV1VN416DE1h`, `BV1q6816qE4B`, `BV1dVtA6uE7K`, `BV1tSh364EYY`, `BV1fPgA6YEGg`, `BV1CuNG6pERs`, `BV1hn846BE6D`, `BV1Dbuy6eENA`. All detail/player calls returned HTTP 200/code 0; each had an empty public subtitle list and no player subtitles. The player response exposed the native purchase/full-video preview message (`为创作付费，购买观看完整视频|购买观看`) and, where returned, login-required subtitle state. Titles, descriptions, chapters, duration and counters are metadata only and are not watch/transcript evidence under `PLATFORM_ACCEPTANCE.md`.

Full endpoint URLs, CIDs, publication timestamps, response hashes, subtitle counts, and decisions are recorded in `bilibili-followup-probes-20260830.jsonl`. All ten are `discovery_metadata_only`, `candidate_created=false`; no media stream, audio download, ASR, subtitle bypass, login, purchase, CAPTCHA, or interaction was attempted.

**Decision:** zero new Stack Overflow or Bilibili candidates. Keep Stack Overflow at reproducible 0/10 partial and Bilibili at 0/10 blocked/partial. Safe resume requires a new exact-alias Stack Exchange result, or user-assisted normal Bilibili login/full playback with a public transcript/subtitle (without bypassing access controls).

## Additional Bilibili search bound (same date)

One further public search-page check (`pi-coding-agent`, page 1) surfaced seven more previously unseen BVIDs: `BV19qgL6bED7`, `BV1w5Vn6hErQ`, `BV1dqgK6qEzP`, `BV1jVh56UELk`, `BV1hp846TEwu`, `BV1gaN96UEVQ`, and `BV1VkgK6NEZS`. Their official detail and player endpoints were checked sequentially. Every response was HTTP 200/code 0 with zero public subtitles/player subtitles and the same native purchase/full-video preview message. They remain discovery-only negatives; no candidate rows were created.
