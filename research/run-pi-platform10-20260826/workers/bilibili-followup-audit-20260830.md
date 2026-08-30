# Bilibili follow-up audit — 2026-08-30

`BV1jX8462EFb` was opened from the native search and watched in the signed-in Chrome session through the end of its approximately 49.8-second runtime. The canonical page showed the title, creator `重生之我再干前端`, and `2026-08-23 16:30:00` publication timestamp. A transient player caption (`把这个agent的跑通好`) was visible during playback; the subtitle panel and `video.textTracks` exposed no persistent subtitle track. A curator identity review found no visible `earendil-works/pi`, `badlogic/pi-mono`, `pi-coding-agent`, related npm package, or explicit Pi AgentHarness anchor. The row is therefore withdrawn from provisional acceptance and retained only as a full-watch identity-negative audit; it must not count toward the Bilibili quota.

The candidate and narrow readback are append-only worker evidence (`worker_checked`) in the two JSONL shards. No curator acceptance is asserted here. Search cards, comments, and metadata-only API fields were not used as final evidence; no account interaction or download occurred.

`BV1DV4f6QESX` (Pisper) was also watched to 60/60 seconds, but is recorded only in `bilibili-followup-negative-audit-20260830.jsonl`: its page describes the separate Pisper Runtime and does not visibly establish an earendil-works/pi basis. It is therefore not promotable or countable toward the Pi quota.

A bounded retry for unqueued `BV1eSG16SEFT` (`最强Pi Agent 飞书远控插件！随时随地大小Pi`) was attempted, but the existing Chrome extension was unavailable before canonical body/playback readback. It is recorded as `blocked_chrome_unavailable` in the negative audit shard; search metadata is intentionally not promoted.

## 12:20 bounded retry (existing queue candidate)

`worker-cn-023` / `BV1iUbD6CEVY` was selected from the existing review queue (no new candidate or URL). A new Chrome tab was opened at the exact canonical URL, but the page-state/DOM observation timed out and reset the browser connection before title, body, player, or caption state could be captured. No playback or identity claim was made. The row remains `worker_checked` and is recorded as `blocked_chrome_unavailable` in `bilibili-followup-negative-audit-20260830.jsonl`; metadata, search cards, chapters, and recommendation redirects are not evidence.
