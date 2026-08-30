# Chinese gap public-search audit — 2026-08-30

Scope: bounded public, read-only discovery and canonical readback for 36Kr,
OSChina, Weibo and Douyin after loading all current root items and worker
candidate shards. This shard does not edit the root candidate/queue/ledger.

## One new worker candidate

- **36Kr / 3925157852493960** — *Agent成本暴降几十倍，LlamaFactory
  作者开源新工具：0.2元自动造Agent*. Anonymous canonical page showed
  新智元, 2026-08-04 21:22 and the full 5,077-character body
  (`SHA-256 11867eeea6e3f6a37911b0d3e0b666794bc5fe74829d9bbcc05bb1207b432fb8`).
  The article is PenguinHarness-primary but has an explicit Pi Agent harness
  comparison paragraph. It is retained only as `curator_review_ready`, with
  the Pi-secondary limitation; primary curator must decide whether this is
  sufficiently direct under `PLATFORM_ACCEPTANCE.md`.

Before writing, the object ID, normalized URL, candidate ID, title, creator,
date and PenguinHarness keywords were searched across `candidates.json`,
`review_queue.json`, and all worker artifacts; no existing row was found.

## No-new / cluster decisions

- **OSChina** `19209610` was fully read and is a detailed Pi SDK/Pi Agent
  Runtime article, but it is the same-title/same-author/same-body cross-post as
  accepted SegmentFault `worker-cn-058`; no second candidate was created.
- **Weibo** long article `2309405331739202683000` was fully read. Pi occurs
  once only to say DSH did not adopt Pi architecture, while the body is a
  DeepSeek Harness test syndicated across Zhidx/Sina/Toutiao; no candidate.
  Further exact-alias public searches returned zero new indexed objects.
- **Douyin** bounded external discovery found no clean, known public `/video/`
  object with a readable Pi detail/transcript. No ID was guessed; no internal
  search or media playback/download was used.
- **36Kr** exact/open-source searches otherwise returned known URLs,
  cross-post clusters or false positives. The only unseen readable object is
  the PenguinHarness row above.

## Safety

All reads were public, anonymous and read-only. No login, CAPTCHA, challenge,
paywall, robots, internal-search restriction, interaction or media-download
boundary was bypassed. `agent-reach` was unavailable and was not installed or
upgraded. Search summaries were discovery-only; final evidence comes from
canonical pages. Root accounting files remain untouched by this shard.
