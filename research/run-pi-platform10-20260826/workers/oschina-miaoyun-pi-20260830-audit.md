# OSCHINA MIAOYUN / MiniMax Code 2.0 Pi-secondary audit (2026-08-30)

## Decision

追加一条 `curator_review_ready` 候选，交由主策展人判断 Pi-secondary 身份强度；本审计未修改
`candidates.json`、`review_queue.json`、`sources.tsv`、`evidence_cards.tsv` 或
`platform_coverage.tsv`，也未把候选计入 accepted。

- Candidate ID: `china-scarce-oschina-19724125-miaoyun-pi-20260830`
- Canonical URL: `https://my.oschina.net/u/5247004/blog/19724125`
- OSCHINA object ID: `19724125`
- Title: `MIAOYUN | 每周AI新鲜事儿 260717`
- Creator: `MIAOYUN秒云`
- Visible publication date: `2026-07-20`

## Original-page readback

普通匿名 Chrome 打开 OSCHINA canonical 页面，HTTP 200；页面显示“原创”、标题、作者
和 `2026-07-20`，canonical/og:url 均指向上述 URL。完整正文逐段回读；可见正文约 8,368
字符，SHA-256=`c51ba944cfd982d3ce89765561366a50a0c46c2833e85af9a3bb5e66d7cea49f`。

在正文 `AI Agent` 栏目中，作者单列“稀宇科技更新『MiniMax Code 2.0』桌面端，底层重构强化长任务”段落，逐字写明：

> 7月16日，稀宇科技推出重构后的「MiniMax Code 2.0」桌面端，基于开源框架Pi Agent重构底层链路，大幅提升会话启动速度与长任务稳定性，优化图表、文件预览编辑等功能；打通恒生、企查查数据上线金融分析模块，可自动完成产业链调研、投资报告等全流程工作，本月还将新增远程操控、浏览器控制等能力，现已开放下载。

这是一段原页正文中的明确 Pi 项目采用声明，而非搜索摘要；但 Pi 只占整篇多主题 AI 周报的一段，因此明确标为 `Pi-secondary`，不把它包装成 Pi 专属教程或源码证据。

## Identity and deduplication

检索前后扫描当前 `candidates.json`、`review_queue.json` 和所有
`workers/*-candidates*.jsonl`，未发现 candidate ID、OSCHINA object ID `19724125` 或规范化 URL。
标题/作者/日期组合也未出现。现有 OSCHINA 19741369/19743475/19743056/19743916/Huiyu-Pi
对象与该周报不同；与 SegmentFault 的 IMClaw/HagiCode 文章、InfoQ/36Kr Pi 指南或访谈
按 URL、标题、作者、日期和主题结构比较，未见同一 canonical 或高重叠正文簇。Google
quoted exact-phrase 查询只返回该 OSCHINA 页及其 AI 概览，没有可验证的逐字跨站副本。

## Limitations and safe boundary

- 这是 Pi-secondary 产业采用/新闻快照，产品团队的会话速度、长任务稳定性和功能上线
  说法未独立复现；不能当作 Pi 本身的性能结论。
- 页面顶部的 OSCHINA AI 自动总结未作为证据；摘要只引用作者正文 Pi 段落。
- 未登录、未互动、未下载、未执行代码，也未绕过验证码、robots、付费墙或风控。

Evidence files:

- `oschina-miaoyun-pi-20260830-candidates.jsonl`
- `oschina-miaoyun-pi-20260830-readbacks.jsonl`
- `oschina-miaoyun-pi-20260830-audit.md`
