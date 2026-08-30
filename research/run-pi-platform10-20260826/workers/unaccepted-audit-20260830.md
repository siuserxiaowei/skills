# Unaccepted candidate audit — 2026-08-30

Scope: read-only audit of `review_queue.json` candidates absent from `candidates.json`; no shared ledger/candidate edits. Queue snapshot: 493 items, 134 unaccepted. Each candidate was joined to `evidence_cards.tsv` by `candidate_id` and searched across worker readback/decision artifacts.

## Result

No candidate meets all promotion conditions (17-field record, independently readable canonical original, Pi identity, non-duplicate/non-content-cluster, and curator-level evidence) without a fresh primary readback. Explicit decisions and blockers below are authoritative.

| candidate_id | platform | evidence cards | worker status | recommendation | rationale/source files |
|---|---:|---:|---|---|---|
| `worker-cn-080` | 36kr | 1 | worker_checked | `reject_content_cluster` | reject_content_cluster: 36Kr 正文与已接受 InfoQ worker-cn-063 的 Composio 八 Harness/DeepSeek benchmark 逐段同稿；保留 InfoQ 代表。直接打开本 URL 还触发 36Kr 安全检测，本轮不绕过。 |
| `worker-cn-082` | 36kr | 1 | worker_checked | `reject_content_cluster` | reject_content_cluster: 36Kr 页面明确署名 InfoQ，正文与已接受 InfoQ 演讲整理同稿；保留首发/可审计 InfoQ URL。 |
| `arxiv-2607-19262-biosecbench-pi` | arxiv_openreview | 1 | curator_review_ready | `hold_strict_pi_primary_review` | hold_strict_pi_primary_review |
| `worker-global-083` | arxiv_openreview | 1 | worker_checked | `reject_duplicate_no_candidate_created; reject_exact_url_duplicate` | reject_duplicate_no_candidate_created; reject_exact_url_duplicate: Exact arXiv version and SHarD/Pi security-control paper are already accepted; duplicate-control artifact records current body hash. |
| `worker-cn-001` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-002` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-003` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-004` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-005` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-006` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-007` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-008` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-009` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-010` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-011` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-012` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-013` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-014` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-015` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-016` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-017` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-018` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-019` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-020` | bilibili | 1 | worker_checked | `demoted_to_worker_checked; worker_checked_only` | demoted_to_worker_checked: No public subtitle/transcript or documented playback observation; detail metadata/chapters alone do not satisfy video watch evidence.; worker_checked_only |
| `worker-cn-021` | bilibili | 1 | worker_checked | `blocked_not_promotable; needs_curator_transcript_review` | blocked_not_promotable: A metadata/detail row and a partial player clock are not equivalent to a watched transcript. The public canonical page requires login for subtitle use and advertises a 30-second tr; blocked_not_promotable: The only subtitle entry has no URL/content and the player API requires login and reports that the full video is purchase-gated. Metadata, description, chapters, or a subtitle count; needs_curator_transcript_review |
| `worker-cn-022` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-023` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-024` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-025` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-026` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-027` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-028` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-029` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-030` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-031` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-032` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-033` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-034` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-035` | bilibili | 1 | worker_checked | `worker_checked_only` | worker_checked_only |
| `worker-cn-043` | csdn | 1 | worker_checked | `reject_incomplete_body` | reject_incomplete_body: 页面返回完整目录和首段后即截断（正文约 1,160 字符），无法回读后续章节；属于 metadata/partial shell，不能接受。 |
| `worker-cn-045` | csdn | 1 | worker_checked | `reject_identity_weak` | reject_identity_weak: 正文虽可读，但只泛称 Pi/Agent kernel，未出现 earendil-works/pi、pi-coding-agent 或相关 npm 锚点；三层 OpenCode/Goose/Pi 选型文不足以通过严格身份门。原 /v1/ URL 还重定向到 awstech canonical。 |
| `community-api-devto-4231446` | devto | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | 此 URL 已存在上一轮 accepted seed；保留为最新官方 API 回读证据，编译时应按 canonical URL 去重，不得重复计数。 |
| `worker-global-072` | devto | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 medium/original-practitioner，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `code-hosts-gitee-001` | gitee | 1 | curator_review_ready | `reject_upstream_mirror` | reject_upstream_mirror: Public README explicitly says the repository synchronizes the official earendil-works/pi GitHub repository; mirror is not an independent original content object.; reject_upstream_mirror: 公开 README 明确是 earendil-works/pi 同步镜像；按本轮验收协议和用户指令不把 upstream mirror 当独立原始内容。 |
| `worker-global-001` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-002` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-003` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-004` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-007` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-008` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-009` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-010` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-011` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-012` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-013` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-014` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-015` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-019` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-021` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-022` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-023` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-024` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-025` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-026` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-027` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-028` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-029` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-030` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-031` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-032` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-033` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-034` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-035` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-036` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-037` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-038` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-039` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-040` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-041` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-042` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-043` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-044` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-045` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-046` | github | 1 | worker_checked | `not_ready_primary_curator_readback_required` | 原 worker 等级为 discovery_only/index，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-063` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-064` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-065` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-067` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-068` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-069` | hacker_news | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/platform-search，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `web-hashnode-channels` | hashnode | 1 | metadata_only | `reject_pi_secondary` | reject_pi_secondary: The article is OpenClaw/Claude Code Channels primary; Pi Coding Agent appears as a named comparison section only. Metadata-only queue treatment is correct. |
| `web-hashnode-gary-components` | hashnode | 1 | not_ready | `reject_same_name_false_positive` | reject_same_name_false_positive: Body uses invented generic @pi-mono/lint-style examples and does not match the specified Pi project structure. |
| `web-hashnode-gary-tools` | hashnode | 1 | not_ready | `reject_same_name_false_positive` | reject_same_name_false_positive: Body discusses generic LangChain, Playwright, Zod, Retryable, TypeScript, Jest and Git LFS rather than earendil-works/pi internals. |
| `web-hashnode-symphony` | hashnode | 1 | metadata_only | `reject_pi_incidental` | reject_pi_incidental: The article is Symphony-primary; one pi-coding-agent/Kata CLI passage is incidental and not an independent Pi object. |
| `china-followup-infoq-KyLqAEKpkvrH3tJwMgiw-pi-podcast` | infoq | 1 | not_ready | `reject_duplicate_content_cluster` | reject_duplicate_content_cluster |
| `worker-cn-064` | infoq | 1 | worker_checked | `reject_exact_or_cluster_duplicate` | reject_exact_or_cluster_duplicate: Complete canonical body readback exists, but this URL/content is already represented by the accepted InfoQ seed; the same Mario Zechner talk also has a 36Kr syndicated copy. Do not |
| `worker-cn-048` | juejin | 1 | worker_checked | `reject_duplicate_exact_url` | reject_duplicate_exact_url: 与已接受 Juejin seed 完全相同 URL、作者、标题和正文；另有 Baidu 搜索代表同稿，不能重复计数。 |
| `social-linkedin-thinkrail` | linkedin | 1 | metadata_only | `not_ready_metadata_or_rejection` | 数字 URN 可见，但 share 与 UGC 对象类型尚需 canonical re-verification；在直接 URL 解析并重读原文前不得接受。 Supplemental shard status is metadata-only/not-ready; an independent rules-compliant original-page readback is mandatory before acceptance. |
| `worker-cn-066` | linuxdo | 1 | worker_checked | `already_accepted_no_promotion; reject_duplicate_exact_url` | already_accepted_no_promotion: review_queue 中唯一 Toutiao 候选已在 candidates.json 以 accepted 存在（curator_reviewed_at=2026-08-29）；不重复 promotion。独立匿名 canonical 页面显示标题、cxuanAI、2026-08-10 12:16 和完整正文，明确命中 @earendil-works/; already_accepted_no_promotion: 该 review_queue 候选已在 candidates.json 以 accepted 存在（curator_reviewed_at=2026-08-29），不可重复 promotion。正文是可回读的 Pi 实践文章，但与 Linux.do worker-cn-066 同作者同一 DeepSeek 配置/体验内容簇，不能复制计数。; reject_duplicate_exact_url: 与已接受 seed 完全相同 URL 和同一作者配置/体验正文；新增 readback 不能创造第二对象。 |
| `worker-cn-068` | linuxdo | 1 | worker_checked | `reject_thin_secondary` | reject_thin_secondary: 匿名原页仅约 166 字符，首帖是 DSH/Codex 泛问题，Pi 只在一条简短回复中出现；正文过薄且非 Pi 主体。 |
| `worker-cn-069` | linuxdo | 1 | worker_checked | `reject_thin_secondary` | reject_thin_secondary: 约 283 字符，核心是 DSH 预览版安装体验；Pi 只作为配置背景，不能满足独立 Pi 内容证据门槛。 |
| `worker-cn-070` | linuxdo | 1 | worker_checked | `reject_secondary` | reject_secondary: 正文是 DeepSeek Harness 的 macOS PWA/Automator 教程，末尾仅链接 pi-web；Pi 不是内容主体。 |
| `worker-cn-071` | linuxdo | 1 | worker_checked | `reject_speculative_secondary` | reject_speculative_secondary: 主题围绕 DSH 发布和未经核验的聊天记录，Pi/DSH 关系停留在猜测，缺乏可审计 Pi 原始内容。 |
| `worker-cn-072` | linuxdo | 1 | worker_checked | `reject_secondary` | reject_secondary: 正文与解决方案讨论 DSH 的问题定义和论文，Pi 仅作为 fork 对照，非独立 Pi 原始内容。 |
| `worker-cn-073` | linuxdo | 1 | worker_checked | `reject_unverified_locator` | reject_unverified_locator: 队列声称第 4 页/第 61 页的 Pi 与 OpenCode 测试，但匿名直接 canonical readback 落到第一页逻辑题正文，未能验证目标回复；不能用猜测或页面参数替代正文证据。 |
| `social-medium-pi-vs-opencode-member` | medium | 1 | metadata_only | `not_ready_metadata_or_rejection` | Member-only；未绕过付费墙，不得把隐藏或完整正文作为证据，也不得从标题推断结论。 Supplemental shard status is metadata-only/not-ready; an independent rules-compliant original-page readback is mandatory before acceptance. |
| `worker-global-076` | medium | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 medium/secondary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `web-note-lazy-radar` | note | 1 | not_ready | `not_ready_metadata_or_rejection` | Original page was read, but Pi is only one item in a broader repository roundup; retain as a rejected discovery outcome unless the curator finds enough Pi-primary depth. Supplemental shard status is metadata-only/not-rea |
| `worker-global-089` | npm | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 medium/registry-metadata，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-090` | npm | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 strong/primary-metadata，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-016` | official_web | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-017` | official_web | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-018` | official_web | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `worker-global-020` | official_web | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 strong/primary，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `web-producthunt-reviews` | product_hunt | 1 | metadata_only | `reject_subroute_metadata_only` | reject_subroute_metadata_only: Reviews is a mutable sub-route of the accepted Pi Coding Agent product object, with no independent stable publication object/date; metadata-only treatment is correct. |
| `worker-cn-059` | segmentfault | 1 | worker_checked | `reject_duplicate_exact_url_and_cluster` | reject_duplicate_exact_url_and_cluster: URL 已由 SegmentFault seed 接受；正文还是七牛云 2026-08-19 的 Pi 完整指南，与 OSCHINA 同作者同日指南形成内容簇，不能重复计数。 |
| `web-substack-nader-agent-stack` | substack | 1 | curator_review_ready | `reject_cross_platform_content_cluster` | reject_cross_platform_content_cluster: Full 47,766-character Pi-primary body was read, but the article explicitly says it was originally posted on X and the accepted X object represents the same tutorial cluster. Do not |
| `worker-global-078` | substack | 1 | worker_checked | `reject_exact_url_duplicate` | reject_exact_url_duplicate: Complete public body and hash are available, but canonical URL is already accepted under the seed ID. |
| `worker-global-079` | substack | 1 | worker_checked | `reject_exact_url_duplicate` | reject_exact_url_duplicate: Complete public body and hash are available, but canonical URL is already accepted under the seed ID. |
| `community-api-v2ex-1202087` | v2ex | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | 标题将 Cron 误写为 Corn；主题正文较短，未独立回读 GitHub 项目或验证安全性。 |
| `community-api-v2ex-1226191` | v2ex | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | AI 分类器不是安全证明；无人值守审批仍需最小权限、sandbox 和独立审计，未安装扩展。 |
| `community-api-v2ex-1229821` | v2ex | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | 模型 ID、窗口和上游供应情况会变化；需要用户自己的 V2EX access token，未执行配置。 |
| `community-api-v2ex-1234716` | v2ex | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | DSH 当时仍为 preview，社区说法和模型后训练推断需回到官方资料。 |
| `community-api-v2ex-1235481` | v2ex | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | 此 URL 已存在 accepted seed；保留作最新 API readback，编译时必须按 canonical URL 去重。讨论包含 Oh-My-Pi 等分支经验。 |
| `worker-cn-079` | v2ex | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 M，笔记记录已读取原页或原生 detail；仍须由主策展人独立回读、核对版本与近重复后才能 accepted。 |
| `social-gap-x-yusukebe-lai` | x | 1 | curator_review_ready | `not_ready_worker_checked_no_curator_decision` | 这是导流/推荐帖，技术细节属于所链接的 blog.lai.so 原文；该原文已在 Google 平台作为 google-lai-so-pi-coding-agent 接受，因此跨平台内容簇检查必须保留两者不同对象类型，不能把本帖当作第二份技术原文。未登录、未互动。 |
| `worker-global-047` | youtube | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-048` | youtube | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-053` | youtube | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-global-058` | youtube | 1 | worker_checked | `not_ready_worker_checked_no_curator_decision` | 原 worker 等级为 discovery_only/metadata，仅完成发现或平台元数据读取；未回读正文/字幕，不得在主策展复核前标为 accepted。 |
| `worker-cn-051` | zhihu | 1 | worker_checked | `reject_duplicate_exact_url` | reject_duplicate_exact_url: 与已接受知乎条目完全相同的 canonical URL；本轮匿名正文虽可读，但不能作为第二对象计数。 |
| `worker-cn-052` | zhihu | 1 | worker_checked | `reject_content_cluster` | reject_content_cluster: 完整正文是 OpenClaw 架构/Pi Runtime 解构，与已接受 SegmentFault worker-cn-058 属同一跨站内容簇；保留更适合作为 Pi Runtime 代表的既有条目。 |
| `worker-cn-054` | zhihu | 1 | worker_checked | `hold_peripheral_pi` | hold_peripheral_pi: 原页完整且可读，但全文主线是通用 AI Agent 理论与自实现教程，Pi 主要作为四工具对照，未达到本轮严格 Pi-primary/Pi-runtime 取向；不安全地扩充知乎配额。 |
| `worker-cn-055` | zhihu | 1 | worker_checked | `reject_peripheral_pi` | reject_peripheral_pi: 原页完整但主题是 Fabarta/OpenClaw 企业实践，正文仅少量提及 Pi/PI Agent，不足以形成独立 Pi 内容对象。 |

## Focused audit notes

- `community-api-devto-4231446`: exact canonical URL already represented by accepted `seed-devto-46-the-coding-agent-i-could-shape-around-my-workflow`; do not promote.
- `code-hosts-gitee-001`: README explicitly says it synchronizes `earendil-works/pi`; upstream mirror, not an independent original.
- `arxiv-2607-19262-biosecbench-pi`: full HTML was read, but Pi is one harness axis in a BioSecBench paper; existing decision is `hold_strict_pi_primary_review`, not accepted.
- `web-substack-nader-agent-stack`: complete body but explicitly “originally posted on X”; same tutorial cluster as accepted X object.
- V2EX `1202087`, `1226191`, `1229821`, `1234716`, `1235481`: exact canonical URLs already represented by accepted IDs; `worker-cn-079` remains worker-only.
- All 35 Bilibili candidates remain non-acceptable under the watch/subtitle blocker; metadata or detail/chapters are not viewing evidence.
- Stack Overflow has no candidates in this queue snapshot; prior exact-alias API probes remain zero-result and are not substituted with unrelated content.

## Counts by platform

- `36kr`: 2
- `arxiv_openreview`: 2
- `bilibili`: 35
- `csdn`: 2
- `devto`: 2
- `gitee`: 1
- `github`: 40
- `hacker_news`: 6
- `hashnode`: 4
- `infoq`: 2
- `juejin`: 1
- `linkedin`: 1
- `linuxdo`: 7
- `medium`: 2
- `note`: 1
- `npm`: 2
- `official_web`: 4
- `product_hunt`: 1
- `segmentfault`: 1
- `substack`: 3
- `v2ex`: 6
- `x`: 1
- `youtube`: 4
- `zhihu`: 4
