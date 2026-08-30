# Bilibili follow-up 3 public audit (2026-08-30)

This append-only audit rechecked two existing queue candidates (`worker-cn-003` / `BV15wGR6CEhY` and `worker-cn-004` / `BV1qy3E6LEKb`). It does not create candidate IDs, change `candidates.json`, or promote anything to `accepted`.

The official anonymous endpoints were read sequentially:

* `GET /x/web-interface/view?bvid=...` for title, uploader, publication metadata, CID, duration, description, chapters and public subtitle metadata.
* `GET /x/player/v2?bvid=...&cid=...` for player subtitle state and access boundary.

Both objects returned HTTP 200 / API code 0. `BV15wGR6CEhY` has CID `38604835521`, duration 1,278 seconds, zero public subtitle entries, `need_login_subtitle=true`, and a purchase-preview message. `BV1qy3E6LEKb` has CID `40314538423`, duration 647 seconds, zero public subtitle entries, `need_login_subtitle=true`, six `view_points` chapter labels, and the same purchase-preview boundary. The ordinary page response was a compressed shell without a stable transcript payload.

Decision: `blocked_no_public_transcript` for both. Titles, descriptions, chapter labels, and package strings are discovery/identity clues only; they do not satisfy the video watch/transcript requirement in `PLATFORM_ACCEPTANCE.md`. A future retry is safe only through a normal user-assisted logged-in playback that visibly reaches the content and samples captions, or a creator-provided public transcript. No login, purchase, download, CAPTCHA, or bypass was attempted.
