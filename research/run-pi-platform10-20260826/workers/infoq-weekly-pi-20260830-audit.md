# InfoQ weekly Pi candidate audit (2026-08-30)

## Decision

追加一条 `curator_review_ready` 候选，等待主策展人显式晋级；本审计没有修改
`candidates.json`、`review_queue.json`、`sources.tsv`、`evidence_cards.tsv` 或
`platform_coverage.tsv`，也没有把候选计入 accepted。

- Candidate ID: `china-scarce-infoq-a480c489bfe1a087fa110c49e-pi-weekly-20260830`
- Canonical URL: `https://xie.infoq.cn/article/a480c489bfe1a087fa110c49e`
- Title: `Github 周刊 2026W30 | Kimi Code CLI 发布、Bonsai 27B 本地推理、OmniRoute 免费 Token、Apache Ossie 开源`
- Creator: `whincwu`
- Visible publication date: `2026-07-28`
- InfoQ object ID: `a480c489bfe1a087fa110c49e`

## Original-page readback

普通匿名 Chrome 打开 InfoQ Writing canonical 页面，HTTP 200；页面显示标题、作者
`whincwu`、发布日期 `2026-07-28`、本文字数 `2441`，canonical 和 `og:url` 都指向
上述 URL。完整 `.article-detaile` 正文已逐段读完；去除首尾空白后的可见正文为
3,774 个 Unicode 字符，SHA-256 为
`734f4a81cf2f306ffc6acea294add5c4c8bd64857ffdbeea2517cb052a4de971`。

正文中有三个与 Pi 直接相关、可定位的部分：

1. 导语明确说 Pi 以“完整用户级权限”的激进设计挑战安全默认值；
2. 第 6 项是独立的 `earendil-works/pi` 项目条目，列出 TypeScript、交互式 CLI、
   Agent 运行时和统一的 OpenAI/Anthropic/Google 等多供应商 LLM 接口；
3. 第 17 项另列 `agegr/pi-web`，描述会话浏览、实时聊天、模型配置、技能管理和
   项目文件预览的本地 Web UI。

这些内容来自原页正文而非 SERP 摘要、图片 OCR 或页尾微信公众号外链。该对象是
多项目周刊，但 Pi 拥有明确编号章节和项目链接，因此符合“直接相关、可回读原页”的
候选门槛；它不代表独立的性能复现实验。

## Global deduplication

检索前后扫描当前 `candidates.json`、`review_queue.json` 和全部
`workers/*-candidates*.jsonl`，未发现 candidate ID、InfoQ object ID 或规范化 URL
`a480c489bfe1a087fa110c49e`。标题/作者/日期组合也未出现。正文开场、Pi 条目上下文、
项目列表结构和内容指纹均不同于已接受的 InfoQ `sLVv23...`、`XpFUa...`、`D8E3...`、
`dSex...`、`e428...`、`5283...`、`e694...`、`7fce...` 以及 36Kr/Baidu 的
Armin/Mario 访谈或 Pi 访谈整理；未发现同稿簇或一稿多发关系。InfoQ 页尾虽链接
微信公众号原文，但本候选只计 InfoQ canonical 对象，不另建外链候选。

## Boundary and limitations

- 周刊中的 Stars、周增量和权限/安全评价是 2026-07-28 的作者快照，未独立复现。
- Pi 是 19 项项目中的一项（另有 pi-web 生态项），不是全文唯一主题；摘要只引用
  Pi 的明确章节和导语，不把其他项目拆成候选。
- 未登录、未互动、未下载、未执行代码，未绕过验证码、robots、付费墙或风控。

Evidence files:

- `infoq-weekly-pi-20260830-candidates.jsonl`
- `infoq-weekly-pi-20260830-readbacks.jsonl`
- `infoq-weekly-pi-20260830-audit.md`
