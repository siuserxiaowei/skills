# China scarce-platform follow-up audit (2026-08-30)

本分片在读取现有 `candidates.json`、`review_queue.json`、全部 worker candidate shards 和既有排除账本后执行；没有重复现有 `candidate_id` 或规范化 `canonical_url`，没有修改根候选/队列/派生账本。

## 新增原页对象

1. **36Kr / 3929369029868677** — 机器之心的 Prime Agent/RLM 长文。匿名 Chrome 完整回读标题、作者、时间和正文；正文 SHA-256 为 `1f60eeaa41e88c3bf608f03770e8d0cf53b20114943c0e763b8220fbcb8b83e2`。正文主线是 Prime Agent，但明确讨论 `Pi-mono` 作为持久 Agent runtime/benchmark 对照，故保留为有明确局限的生态与批评材料，不把 Prime Agent 的成绩冒充 Pi 的成绩。
2. **36Kr / 3953106456804488** — 极客邦科技 InfoQ 授权的 Armin Ronacher/Ben Vinegar 访谈整理。匿名 Chrome 完整回读标题、作者、时间和约 18,904 字符正文；正文 SHA-256 为 `f8a6ec939bb93376a1c4cd8d3c68f2d3ef8c6e520782066b799af3013c49cad8`。正文直接讨论 Pi 核心贡献者、Pi+Hunk 长时任务、会话可移植性、缓存/加密锁定和 supervisor；与既有 Pi/Armin 视频及 InfoQ/36Kr 访谈逐项比对，未发现同一 canonical 对象或高重叠同稿。
3. **Toutiao / 7672987705244795455** — GitHub 增长榜原页。匿名 Chrome 完整回读榜单和第 5 项 `earendil-works/pi` 专门章节；正文 SHA-256 为 `adb0a733dda201e76bae4fb5ed3bf909adec5761ba81f468317cf96c092171a6`。Pi 是十项榜单中的独立章节，摘要只引用该章节，Stars/增长数字保留为日期快照并不当作独立验证。

## 排除/阻塞

- OSChina `https://my.oschina.net/u/9487999/blog/19728084` 在匿名浏览器等待动态渲染后显示“找不到您访问的页面/页面不存在”，没有正文证据，不创建候选。
- 微博、抖音没有新的公开 canonical 原页；Bilibili 新探针字幕为空且播放器显示登录/购买试看，Stack Overflow 新精确别名 API 均 `HTTP 200 / items: []`，详见同日 blocker 分片。
- 新对象均按 URL、平台对象 ID、标题/作者/日期和正文主题去重；未把搜索摘要、转载镜像、评论子路由或榜单外项目章节当作独立对象。

## 证据文件

- `china-scarce-candidates-20260830.jsonl`
- `china-scarce-readbacks-20260830.jsonl`
- `china-scarce-audit-20260830.md`

以上 candidate rows 仅标记 `curator_review_ready`，仍需主策展人显式晋级；本分片未直接写入 `candidates.json`。
