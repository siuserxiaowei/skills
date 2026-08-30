# Bilibili `worker-cn-021` browser watch-evidence blocker (2026-08-29)

This is an append-only browser observation. It does not modify
`candidates.json`, `review_queue.json`, ledgers, or accepted coverage.

## Canonical object

- Candidate: `worker-cn-021`
- BVID: `BV1k6E167Ext`
- URL: <https://www.bilibili.com/video/BV1k6E167Ext/>
- Visible title: **推荐一些Pi Agent插件**
- Uploader: **夜未央-天将亮**
- Visible page date: **2026-06-12 18:32:22**

## Bounded anonymous browser observation

The ordinary Chrome canonical page rendered the native player and metadata.
At the initial page state the player displayed **“登录 免费享高清视频”** and
**“试看30秒”**. I did not log in, submit any account action, download media,
or use a download-helper control. I inspected the native 字幕 control only as a
read-only UI action. Its rendered panel showed **“暂无字幕”**, **“登录可享”**,
and the surrounding subtitle list showed **“(未找到字幕)”** together with
**“要求登录 / 请登录才能使用此功能”**. The page's HTML5 video had no native
text tracks (`textTracks=[]`).

A bounded player-state check observed the video clock at approximately
`61.19 / 239` seconds and paused. This is only a player-state observation; it
does not establish that the complete video was viewable or that its spoken
content was understood. No transcript text was exposed in the DOM, and no
semantic claims were extracted from audio, description, chapters, counters, or
related-video cards.

## Decision

`blocked_not_promotable`. The page's login/trial boundary and absent public
subtitle prevent a PLATFORM_ACCEPTANCE-compliant curator readback. Keep the
candidate `worker_checked`; do not promote it. The safe resume point is a
normal user-assisted Bilibili login with read-only playback/subtitle inspection,
or a creator-provided public transcript. Do not bypass the gate or use media
download/ASR workarounds without a separately authorized, compliant route.
