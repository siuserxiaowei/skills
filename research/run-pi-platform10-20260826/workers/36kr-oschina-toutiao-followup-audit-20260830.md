# 36Kr / OSChina / Toutiao bounded public-search follow-up — 2026-08-30

Run: `pi-platform10-20260826`
Scope: append-only worker discovery and canonical readback evidence. Root
candidate files, review queue, ledgers, and public library were not modified.

## Baseline and search boundary

Before search, current `candidates.json`, `review_queue.json`, and all worker
candidate shards were normalized by canonical URL and platform object ID. The
four new URLs below and IDs `3938099874322308`, `7673909764631347766`, and
`7673737737710633518` were absent. Existing 36Kr/OSChina/Toutiao URLs and IDs
were retained as duplicate exclusions. Each platform used no more than two
new exact queries, with ordinary visible Google/Bing routes only:

| platform | query 1 | query 2 |
|---|---|---|
| 36Kr | Google: `"Pi Agent" "36氪"` | Bing: `"36Kr" "pi-coding-agent"` |
| OSChina | Google: `"Pi Agent" OSCHINA Extension` | Bing: `site:oschina.net "pi-coding-agent" 安装` |
| Toutiao | Google: `"Pi Agent" "今日头条" 扩展` | Bing: `site:toutiao.com/article "pi/agent" Harness` |

## Results and canonical readback

### 36Kr

Google query 1 exposed a new canonical 36Kr article:
`https://www.36kr.com/p/3938099874322308`, **黑鲸出水，DeepSeek下半场开始**
(凤凰网科技 / Dale, 2026-08-14 07:43). Direct anonymous Chrome readback
returned the complete body (3,727 characters; SHA-256
`c1796319421291504e3ddcaf5631d27bb6eed656b145590e0505e7aaec618b06`). The
article explicitly reports Pi Agent's 20/30 result in an eight-Harness test and
explains pluginized runtime, Cordis, append-only logs, model support, cost and
v0.1 caveats. It is an authorized 36Kr republication from Phoenix Technology;
that provenance and lack of independent benchmark reproduction are retained.
Bing query 2 returned existing 36Kr URLs and unrelated third-party pages; no
additional new 36Kr canonical was promoted.

### OSChina

Google query 1 returned the OSChina news page **受够了 Alt+Tab？开发者用画布
IDE 给所有窗口安个家** (`/news/446915`). Anonymous direct readback did not
produce a stable article body: the page currently renders a `0`/`NaN` shell,
2026-08-30 placeholder date, and only an AI-generated summary/legal footer,
with no Pi body. It is therefore not a candidate. Bing query 2 was stopped by
the visible “请解决以下难题以继续” challenge before results could be read;
no bypass or alternate automated route was attempted. **OSChina: 0 new.**

### Toutiao

Google query 1 exposed two new canonical article objects, both directly read
anonymously:

1. `https://www.toutiao.com/article/7673909764631347766/` — **DeepSeek Harness
   安装，初体验，没有惊喜。** (人人都是产品经理 / Ai学习的老章,
   2026-08-14 23:29). Body 2,974 chars, SHA-256
   `8edcfd7834e3c4d126fc7288f28ec8c6a832d3f2da4694027e64caee4a9597fd`.
   Pi is a concrete comparison baseline with a token/cache table and explicit
   test-interference caveat.
2. `https://www.toutiao.com/article/7673737737710633518/` — **像玩乐高一样拼
   插件，DeepSeek Harness能带来哪些改变？** (界面新闻 / 宋佳楠,
   2026-08-14 12:21). Body 2,211 chars, SHA-256
   `c6e5e8a8712c49b791e6aaf6b29c5bd8d00b627f42b487e2a72e13e259836cd5`.
   Pi is explicitly identified and compared in the architecture article.

Bing query 2 hit a visible “请解决以下难题以继续” challenge before results;
no bypass was attempted. The two new Toutiao bodies have distinct authors,
titles, hashes, and narratives; comparison against the existing Toutiao DSH,
Pi/DeepSeek, runtime-slot, and GitHub-roundup bodies found no same-content
cluster.

## Safety and handoff

New rows are in `36kr-oschina-toutiao-followup-candidates-20260830.jsonl`
and matching complete observations in
`36kr-oschina-toutiao-followup-readbacks-20260830.jsonl`; all remain
`curator_review_ready` and are not counted as accepted. This audit records
Google/Bing challenge boundaries exactly; no login, interaction, download,
CAPTCHA solving, robots/paywall bypass, or external write occurred. `agent-reach`
is unavailable on this machine, so the ordinary visible search/browser route
was used under the repository's acceptance protocol.
