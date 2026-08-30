# China scarce-platform follow-up audit (2026-08-30)

This append-only shard was created after checking `candidates.json`, `review_queue.json`, and every existing `workers/*-candidates*.jsonl` row. The three new candidate IDs and normalized canonical URLs were absent from those files before writing; no root ledger was edited and no candidate was promoted to `accepted`.

## New original-page readbacks

1. **OSChina / 19728084** — `https://my.oschina.net/u/1756807/blog/19728084`, not the previously probed `u/9487999` shell. Anonymous Chrome showed the canonical title, original badge, creator 右耳朵猫AI, date 2026-07-27, the full weekly article, and the dedicated `#6 earendil-works/pi` section. Article content-container fingerprint: 4,360 Unicode characters, SHA-256 `dc8d1d9489b73ec211f16289555321995fa742160681eeca1a4c5bf34e484edf`. Pi remains one item in a multi-project roundup; stars and security wording are retained as historical snapshots.
2. **Toutiao / 7673908978849432105** — `我扒了 DeepSeek Harness 219 个包…`. Anonymous Chrome showed 2026-08-14 23:26, creator 人人都是产品经理, and the complete 6,808-character article. SHA-256 `7a84c48c54e322963bdd3542d0e20ded04abfbf0a7f240628cdf544c73a082bb`; the body explicitly names `dsh-llm-pi-ai` and `@earendil-works/pi-ai`, alongside Turn/Step events, Session JSONL, tool ordering, compaction, and plugin security.
3. **Toutiao / 7673745790443061810** — `Deepseek Harness 会是 Agent 插件的终极答案吗？ - 文章`. Anonymous Chrome showed 2026-08-14 12:54, creator 风满楼啊啊, and a 26,452-character article. SHA-256 `0930091c4e240c06bd21ff5479e1af705856387678f3035c35ca639ed4b09449`; the dedicated Pi runtime-slots chapter covers Extension API context/memory, model requests, tools, lifecycle, UI, and `pi-autoresearch`.

## Rejection and safety notes

- The OSChina `u/9487999/blog/19728084` URL remains an empty/not-found shell; only `u/1756807/blog/19728084` was used.
- Google/external search was used only for bounded discovery; final evidence is from each platform's canonical page. No login, CAPTCHA solving, interaction, posting, liking, downloading, or bypass of access controls occurred.
- DSH/roundup articles are not treated as Pi benchmark results; their scope and author-reported claims remain in `limitations`. Cross-posts, mirrors, and all existing same-URL/content-cluster objects were excluded.

All rows use `evidence_status=curator_review_ready`; queue compilation intentionally normalizes this to `worker_checked`. Primary curator promotion remains a separate explicit decision.

## Additional bounded gap probes

After the three rows above were written, I ran one focused public 360 Search probe for each sparse platform: `site:36kr.com/p "Pi Agent"`, `site:36kr.com "MiniMax Code 2.0" Pi`, `site:my.oschina.net "Pi Agent"`, and `site:my.oschina.net "pi-coding-agent"`. The 36Kr results were either already-known Pi/Harness URLs or unrelated MiniMax/consumer-Pi stories; the OSCHINA results were already-known objects or unrelated mathematical/Raspberry-Pi/Java-Agent pages. No additional canonical body met the Pi identity and independent-content gates, so no guessed URL or search snippet was added. Search result pages were used only for discovery; no result summary was treated as final evidence.
