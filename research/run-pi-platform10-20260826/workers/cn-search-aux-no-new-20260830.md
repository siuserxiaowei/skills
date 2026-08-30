# 中文平台辅助检索：无新增与可复现阻塞记录（2026-08-30）

本分片是 `pi-platform10-20260826` 的 append-only 公开检索记录，负责
OSCHINA、Toutiao、Weibo，并对 36Kr/InfoQ 做补盲。目标是先审核并去重已有
worker 候选，再在不重复 `candidate_id` 或规范化 `canonical_url` 的前提下寻找
可独立回读的 Pi 原始内容。

## 公开只读边界与工具状态

- 所有页面均以普通匿名浏览器/公开搜索结果做有界发现，再打开 canonical 原页
  回读；未登录、未互动、未下载、未执行页面代码，也未把 SERP 摘要当最终证据。
- 没有绕过验证码、登录、风控、robots、地区限制或付费墙；没有使用未公开 API
  或批量站内抓取。
- 本机 `agent-reach doctor --json` 与 `agent-reach` 命令均不可用
  （`command not found`）；Exa MCP 不可用，Jina Reader 返回 401。未自动安装或
  升级任何系统工具。

## 去重基线

检索前扫描了当前 `review_queue.json`、`candidates.json` 以及全部 worker
`*-candidates*.jsonl` 分片的 candidate ID、平台对象 ID、规范化 URL、标题/作者/
日期组合。当前 queue 快照为 525 submitted、495 unique、30 exact-URL duplicates；
本分片没有把任何已有对象重新提交。

## 分平台结果

### OSCHINA

有界 exact-site 查询（含 `site:my.oschina.net "pi-coding-agent"`）只返回已知
对象或与 Pi 身份门不符的旧文章。现有可独立回读对象仍为：

- `https://my.oschina.net/u/3874284/blog/19741369`（对象 `19741369`）
- `https://my.oschina.net/u/3036583/blog/19743475`（对象 `19743475`）
- `https://www.oschina.net/p/Huiyu-Pi`（对象 `Huiyu-Pi`）

它们已有既存原页回读/主审记录；本轮没有新增 canonical URL 或 candidate。

### Toutiao

有界查询 `site:toutiao.com/article "pi-coding-agent"` 未发现新的可回读强命中。
两条定向回读结果如下：

- `https://www.toutiao.com/article/7605074723264840235/`：原页显示“抱歉，你访问的
  内容不存在”，无正文，未创建候选。
- `https://www.toutiao.com/article/7637320315697250850/`：原页只显示登录界面，
  匿名无法回读正文；按验收协议停在登录门，未绕过、未创建候选。若该对象必须纳入，
  需要用户提供正常登录的只读浏览器会话。

已知 `7673696349073818147`（Hubwiz《智能体工程：Pi SDK》）另有
`toutiao-hubwiz-pi-sdk-crosspost-audit-20260830.md` 的正文级比对，已判定与
Hubwiz/原作者稿为转载簇，不新增 quota；`7672251979535565375`、
`7674868465810883107` 及既有 follow-up 也已在队列/账本中，未重复提交。

### Weibo

有界公开详情/sitemap 路径的 exact Pi 查询只回读到现有对象：

- `https://weibo.com/2/detail/QBbmHyEtb`
- `https://weibo.com/2/detail/QtrDaaB5D`
- `https://weibo.com/2/detail/5334737096278252`

三条均已有 canonical readback（包括 sitemap 发现的两条）并在既有审计中处理；
未发现新的可匿名回读独立正文。Weibo 规则仍按 robots 与低频公开详情边界保留，
不从搜索摘要、推荐流或不可见对象 ID 推断候选。

### 36Kr / InfoQ 补盲

- 36Kr 的 `site:36kr.com/p "Pi Agent"`、`"pi-coding-agent"`、
  `"earendil-works/pi"` 有界查询只返回已知 URL或同名误报。已检查的
  `https://36kr.com/p/3667435997717385` 是 Claude swarm 文章，其中“PI Server
  Agent”只是泛化子代理标签；原页正文不含 `earendil-works/pi`、
  `pi-coding-agent`、`pi-mono` 或 Pi runtime，已拒绝。
- InfoQ 的 `site:xie.infoq.cn/article "Pi Agent"`、`"Pi Coding Agent"`、
  `"earendil-works/pi"` 有界查询未出现超出现有 accepted/held URL 的新 canonical
  对象。现有两条 InfoQ follow-up（`e694c2ef...`、`7fce544d...`）已有独立分片
  回读，仍须主策展人显式晋级，未在本分片重复提交。

## 结论与后续

本分片**未创建新 candidate，也未修改** `candidates.json`、`review_queue.json`、
`queries.tsv`、`sources.tsv`、`evidence_cards.tsv` 或 `platform_coverage.tsv`。
OSCHINA、Weibo、36Kr、InfoQ 当前公开路径没有新增强命中；Toutiao 的
`7605074723264840235` 是失效内容，`7637320315697250850` 的正文被登录门阻塞。
主线程如需继续处理后者，应在获得用户正常登录的只读会话后再回读；不得把登录页或
搜索摘要计入 accepted。
