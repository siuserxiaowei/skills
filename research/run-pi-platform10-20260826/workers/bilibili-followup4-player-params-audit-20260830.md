# Bilibili follow-up 4: alternate player endpoint audit (2026-08-30)

This append-only audit rechecked the five existing Bilibili queue candidates `worker-cn-003`, `worker-cn-004`, `worker-cn-007`, `worker-cn-008`, and `worker-cn-014`. It does not add candidate IDs and does not edit `candidates.json`, `review_queue.json`, or accepted ledgers.

For each known BVID/CID, the official anonymous `x/player/v2`, `x/player/wbi/v2`, and `x/player/playurl` endpoints were queried with ordinary public parameters. The two subtitle-capable responses (`v2` and `wbi/v2`) returned HTTP 200 / API code 0 but `subtitle.subtitles=[]` and `need_login_subtitle=true`; each also exposed the platform's purchase-preview message. `playurl` returned HTTP 200 / API code 0 with `result=suee`, but no transcript or caption payload. Full response hashes are recorded in the JSONL artifact.

All five remain `blocked_no_public_transcript` / `worker_checked`. Chapter labels, descriptions, package names, and search metadata remain discovery clues only. No login, purchase, media download, CAPTCHA, subtitle bypass, or account interaction occurred. The only safe retry is a normal user-assisted logged-in playback with visible captions or a creator-provided public transcript.
