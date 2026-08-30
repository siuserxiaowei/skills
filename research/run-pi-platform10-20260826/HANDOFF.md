# Pi 47 × 10 研究任务交接

状态：`in_progress_not_publishable`

Run ID：`pi-platform10-20260826`

最后更新：2026-08-30 17:58（Asia/Shanghai）

目标：47 个指定平台，每个平台至少 10 条已回读原页、完成主审且全局去重的 Pi 内容。

## 当前可信快照

> 本节与文末“2026-08-30 17:58 停止抓取前最新快照”是当前权威状态；带“历史记录”的段落仅用于审计，不代表最新数字。

- 已接受：451 / 470（物理 `candidates.json` 为 453；2 条内容簇排除不计入有效库）
- 达标平台：35 / 47
- 尚缺：93 条，分布于 12 个平台
- 规则记录：47 / 47，全部 `curator_accepted`
- worker review queue：566 submitted / 535 unique / 31 exact URL duplicates
- 证据账本：451 条有效 accepted 均有 `accepted_readback` source 与 curator-accepted evidence card（sources/evidence 共 584 / 584）
- 覆盖状态：35 complete / 8 partial / 4 blocked
- 发布：未执行；未推 `main`；不得声称 47 × 10 完成
- 既有 queue 复核后，微博新增 8 条移动端 canonical 正文已由主策展人逐条回读并晋级；queue 随之增至 535 条唯一项。其余未接受项均已有明确拒绝、重复、内容簇、元数据不足或阻塞依据。详见 `workers/weibo-logged-followup-audit-20260830.md`、`workers/curator-ready-gap-audit-20260830-1225.md`、`workers/queue-gap-scan-20260830-1526.md`。
- Chrome 用户辅助会话随后停止在只读状态：微博 8 条新增原页已验收；小红书再次搜索时出现“登录后查看搜索结果”弹窗，Bilibili 其余条目仍需原生字幕或完整观看证据，TikTok 仍是登录/地区/风控壳。公众号后台文章因没有指定 Pi 身份锚点而拒绝。详见 `workers/weibo-logged-followup-audit-20260830.md`、`workers/bilibili-followup-audit-20260830.md`、`workers/wechat-official-logged-in-negative-audit-20260830.md` 与 `<local-login-checkpoint-not-published>`。

已达标平台：

```text
csdn zhihu x juejin youtube linuxdo github baidu_search google_search toutiao
bing_search segmentfault v2ex reddit hacker_news medium linkedin official_web
npm devto substack arxiv_openreview zenn qiita note huggingface bluesky infoq
gitlab composio pypi docker_hub gitee oschina weibo
```

仍有接受项但未满 10：

```text
xiaohongshu 5   36kr 8
douyin 1        bilibili 1  product_hunt 3  hackernoon 3
hashnode 6
```

其余平台的精确计数、状态与下一安全步骤以
`platform_coverage.tsv` 和根目录 `platform-library.json` 为准；当前共有 12 个 quota-shortage 平台。

## 本阶段完成内容

## 2026-08-30 17:58 停止抓取前最新快照
- 重建 worker shards、review queue、worker ledgers 和平台库后，账本为物理 accepted 453、内容簇排除 2、有效 accepted 451；queue 566/535/31，queries/sources/evidence 250/584/584。
- 微博 8 条新增对象（`RcqOGfo8f`、`Rc6SojaAG`、`RdoPH7Evz`、`ResXSiAcs`、`R9WYfDIiz`、`Rc7imbU1q`、`QvKULtfwI`、`QvHAIchU0`）均由主策展人逐条回读移动端原生正文并晋级，微博达到 11/10，完整平台增至 35 个。
- 当前严格门禁剩 12 个真实 quota shortage、合计 93 条：微信公众号、小红书、抖音、Bilibili、36Kr、快手、微信视频号、TikTok、Stack Overflow、Product Hunt、HackerNoon、Hashnode。
- 用户要求先查看数据后，本轮已停止进一步抓取；小红书登录弹窗标签仍保留给用户操作，未新增小红书/Bilibili/TikTok 候选。
- 私有飞书子文档（定位信息已脱敏） 仍为 revision 7；本轮未向远端写入，也未删除重复增量区块。

## 2026-08-30 13:35 续跑快照（历史记录）
- 当时重建结果为物理 accepted 445、内容簇排除 2、有效 accepted 443；queue 558/527/31，queries/sources/evidence 249/576/576。
- OSChina 三条独立原页（19695554、19719684、19749892）完成主策展回读并晋级，OSChina 达到 10/10；Product Hunt `bb/built-with` 也已作为 Pi-secondary adoption snapshot 晋级。
- 私有飞书子文档（定位信息已脱敏） fresh fetch 为 revision 7；重复增量区块的范围删除因中间无 ID 的 `<ul>` 被服务端拒绝，文档未改变。

## 2026-08-30 续跑快照（12:55，历史记录）
- Product Hunt Tyndale `/built-with` 原页作为 secondary adoption snapshot 完整回读并晋级，彼时 Product Hunt 为 2/10；页面显示独立 Tyndale 产品、badlogic/pi-mono 技术栈卡和 Pi 采用引用，限制已明确写入条目。
- Bilibili `BV1jX8462EFb` 虽完整观看约 49.8 秒，但原页无 earendil-works/pi、badlogic/pi-mono、pi-coding-agent、相关 npm 或显式 Pi AgentHarness 锚点，按严格身份门槛撤回，不计入；负面审计见 `workers/bilibili-followup-negative-audit-20260830.jsonl`。
- 本轮重建（历史）：物理 accepted 441、2 条内容簇排除、有效 accepted 439；队列 554/523/31；queries/sources/evidence 246/572/572；14 个缺口平台合计 104 条。

## 2026-08-30 续跑快照（10:55，历史记录）

> 以下 10:15 内容均为历史审计记录。

## 2026-08-30 续跑快照（10:15，历史记录）
- Bilibili `worker-cn-021` 已在正常登录 Chrome 只读会话中从约 00:07 播放至片尾（239 秒），采样到播放器可见字幕并核对 Pi 插件链接；显式主审晋级。Bilibili 当前 1/10，仍为 `partial`，其余 34 条候选继续保持 `worker_checked`。
- 小红书正常登录 Chrome 原生搜索后回读 6 个 note detail：4 条正文可见候选加 1 条正文可见替代项（`6a87dff9`）晋级，共 5/10；`6a817203` 因作者正文不可见、长文本仅来自评论区 AI 总结而拒绝，另有 1 条图片-only note 未进入候选。相对日期均保留为 `unknown`，未使用搜索卡片或评论作证据。
- 本批重建结果：440 条物理 accepted、2 条内容簇排除、438 条有效 accepted；552 submitted / 522 unique / 30 exact URL duplicates；queries/sources/evidence 为 246 / 572 / 572；覆盖 33 complete / 10 partial / 4 blocked；14 个平台共短缺 104 条。严格 47×10 仍应失败，未合并 main、未 push、未发布 Pages。
- 现有缺口候选已完成交叉核对：除上述显式拒绝外，没有尚未审计且可安全晋级的 worker_checked 对象；36Kr PenguinHarness、HackerNoon/Product Hunt 子路由与同稿、Stack Overflow 零结果、Bilibili metadata-only 探针均保留明确决策证据。

## 2026-08-30 续跑记录
- 2026-08-30 09:20 主审修正：OSChina `19724125` 不是薄单句提及；其 Pi Agent 采用段含多项可核验事实，按 Pi-secondary adoption snapshot 接受。该时点有效 accepted 为 432（物理 434，内容簇排除 2），OSChina 7/10。36Kr `3925157852493960` 仍因仅一句类比拒绝；后续 10:15 快照另纳入 Bilibili 与小红书用户辅助回读。

- 2026-08-30 08:45 续跑收口：重新组装 57 个 worker shards（547 submitted / 517 unique / 30 exact URL duplicates），重建 ledgers（sources/evidence 566/566）。对 36Kr `3925157852493960` 完整原页复核后，因 Pi 仅一句类比且无 Pi-specific 内容，按严格身份与独立性门槛撤回 accepted，保留 `workers/cn-gap-search-20260830-*` 和 `workers/curator-followup-decisions-20260830.jsonl` 审计证据。当前物理 accepted 434、有效 accepted 432、36Kr 8/10，严格缺口仍为 14 个平台共 111 条（该历史时点）。
- 同批记录：V2EX、DEV.to、Substack、X、Official Web、CSDN、SegmentFault、Hacker News、YouTube 未发现可晋级独立对象；Bilibili 新增 17 个无字幕/完整观看负面探针，Stack Overflow 新增 7 个严格别名零结果，HackerNoon 新增 14 个聚焦探针均无新候选。
- 当前 queue 的 133 条未接受项已全部关联到明确的重复/内容簇/身份不足/metadata-only/阻塞决策；机器可读汇总见 `workers/curator-audit-summary-20260830.json` 与 `workers/unaccepted-audit-final-20260830.json`，无悬空候选等待主审。

- 2026-08-30 05:00 重建快照：三条新增候选已由主策展人独立回读并晋级（36Kr 1、Toutiao 2）。当时物理 accepted 434、内容簇排除 2、有效 accepted 432；队列 546/516/30，sources/evidence 565/565；覆盖 33 complete / 9 partial / 5 blocked。OSChina 最后一轮 Google/Bing 公开探针无新对象；HackerNoon、Product Hunt、Stack Overflow 补搜均无可晋级独立原始内容。

- 先审核并去重原有 worker 队列；优先的 official_web、V2EX、GitLab、Docker Hub、Bluesky 均无新的独立对象；新增 Hashnode/HackerNoon/Product Hunt 有界 probe 同样无新增。
- 显式晋级 InfoQ 两条独立原页、Hashnode Pi 内部架构长文、Juejin 架构原页、两条知乎原页、5 条 Composio Pi 集成文档及 10 条 npm 官方/生态包；本轮 accepted 增量均完成独立回读与全局 URL/内容簇检查。
- PyPI 五条项目页已在普通匿名浏览器完成正文回读并纳入 accepted；截至本轮共十三个官方 Stack Overflow exact-alias API probe 均 `HTTP 200 / items: []`，保留可复现 partial。
- Toutiao `7673696349073818147` 与 Hubwiz Pi SDK 原文经 8/20-token shingle 和代码块哈希核验为转载/翻译同稿，未新增计数。
- Bilibili 原先 35 条均无字幕/完整观看证据；10:15 快照中 `worker-cn-021` 已通过正常登录 Chrome 播放至片尾并采样可见字幕后晋级，其余 34 条仍不因详情/章节而验收。
- 续跑期间完成多条独立原页晋级：Gitee `itpk/codeg`、Hashnode `oh-my-pi`、Think Throo 的 `mom`/TypeBox、InfoQ 周刊、OSChina/Miaoyun 与周刊、以及本轮 Toutiao 两条正文；所有晋级均有匿名公开原页回读、内容哈希和去重审计。05:00 之后新增的 OSChina 主审接受项与 36Kr 临时项撤回相互抵消，最终队列为 547/517/30，账本 566/566，有效 accepted 432，物理 434。
- 本批主审了现有未接受候选；36Kr/InfoQ/V2EX/官方 Web/镜像/同稿/子路由/metadata-only 对象均未重复晋级。Hashnode/HackerNoon/Product Hunt 新一轮公开 probe 记录在 `workers/hashnode-hackernoon-producthunt-followup-20260830-*`。
- 05:10 继续执行 36Kr 精确别名公开检索（`earendil-works`、`pi.dev`）；结果仅为已接受页面或既有候选，36Kr 安全检测页未绕过，未新增候选。08:45 复核发现 `3925157852493960` 仅为 PenguinHarness 主文中的单句 Pi 类比，已撤回其临时晋级并记录 `reject_pi_secondary_thin_comparison`。
- 当前 shell 未发现 `agent-reach` 可执行文件；未安装或升级系统工具，公开检索按现有浏览器/API 验收路线继续。
- Hashnode 原生匿名查询 `pi coding agent extension` 与 `earendil-works pi` 均显示 `No results found.`，已追加 `workers/hashnode-followup3-probes-20260830.jsonl` 与审计说明，未新增候选。

1. 冻结范围、歧义排除、17 个必要字段、每平台 10 条门槛及命名搜索引擎特殊口径仍以 `run_manifest.json` 和 `PLATFORM_ACCEPTANCE.md` 为准。
2. 三类基础 worker shard 与多份 supplemental shard 已结构化落盘；`compile_platform_review_queue.py` 会合并所有 `*-candidates.jsonl`，exact URL 重复只留一份进入 queue。
3. 新增 fail-closed 主审工具 `scripts/curate_worker_candidates.py`：只有显式列出的 ID 才能提升，discovery-only 对象必须另附独立 curator readback。
4. 新增 `scripts/build_worker_ledgers.py`，从当前 queue、accepted 和规则重建 `queries.tsv`、`sources.tsv`、`evidence_cards.tsv`、`platform_coverage.tsv`。
5. 三个命名搜索引擎均执行两个真实 native intent，各 10 条均逐页回源：
   - Google：`workers/google-search-*`
   - 百度 / Bing：`workers/named-search-*`
   - 没有用 DDG、Exa、Jina 或其他引擎冒充；SERP 摘要只用于发现。
6. 内容簇审计剔除了百度百家号与 SegmentFault 的同作者/同日期/同标题跨发，随后以百度原生发现并回读的得物技术 Violin 独立实现文章替代。
7. Reddit 10、X 10、Medium 10、LinkedIn 10 均通过普通公开原生视图或允许的公开接口回读；member-only / unresolved metadata-only 对象未接受。见 `workers/social-global-*`。
8. Juejin 10 条采用外部 exact-site 发现 + 已知 `/post` URL 的低频普通浏览器回读；禁止自动化站内搜索、未公开 API、批量抓取和互动。
9. note、PyPI、Docker Hub 均已达到 10 条有效 accepted；Gitee 现保留 10 条独立对象，镜像与 security challenge blob 未计入；Hashnode 现有 6 条可回读 Pi/Pi-fork 原页。
10. 严格门禁已加固：每条 accepted 必须有 curator source/evidence；命名引擎必须是真实 backend；描述性 backend 可审计通过，但包含 Exa/DDG/Brave 等替代 token 时仍失败。

## 当前真实缺口

数量不足的平台（按有效 accepted 计数；严格门禁当前仅报告以下 12 个）：

```text
wechat_official_accounts -10   xiaohongshu -5    douyin -9
bilibili -9       36kr -2     kuaishou -10
wechat_channels -10 tiktok -10 stackoverflow -10
product_hunt -7   hackernoon -7 hashnode -4
```

## 官方规则主审

47 个平台规则已全部标记 `curator_accepted`；登录/风控平台仍保留 blocked 或 partial 的真实状态。

这些是真实 shortage / rule-review 缺口，不得通过搜索摘要、转载、镜像、泛义 Pi、metadata-only 或低相关对象补数。对于合法可访问内容本来就稀少的平台，保留真实 Top K 与 `partial`。

## 恢复与重建

当前分支和工作树包含大量未提交研究产物。不要重新 clone 到本目录，不要 reset、checkout 覆盖或清理这些文件。

用户指定基线 `c4ce8f3f60feb015e829a27140d554a7f50f316d` 仅被 `git rev-parse --verify` 按哈希字符串回显；对象实际不可读取（`git cat-file -e <hash>^{commit}` 失败）。公开发布树基于 handoff 分支同步快照构建；本轮未合并 main、未强制推送。

```bash
cd <repo-root>
git status --short --branch
python3 scripts/compile_platform_review_queue.py
python3 scripts/build_worker_ledgers.py
python3 scripts/build_platform_library.py
```

继续研究时：

1. 先读 `PLATFORM_ACCEPTANCE.md`、本文件、`platform_coverage.tsv` 与相应 worker discovery/readback 文件。
2. 对需要登录、验证码、付费、地区或平台审批的路线，停在正常 gate；不绕过、不换后端冒名。
3. 每个新对象先落 worker candidate，独立回读 canonical body/detail/transcript，再用显式 ID 主审；不得按分数或配额自动提升。
4. 每轮提升后依次重建 queue、ledgers 和 public library。
5. 跨平台去重不仅看 URL，还要核对标题、作者、日期、正文簇与转载关系。

## 验证与发布门禁

最终验证命令：

```bash
python3 -m unittest discover -s tests -v
node --check app.js
python3 -m py_compile scripts/*.py tests/*.py research/run-pi-platform10-20260826/workers/*validator.py
git diff --check
python3 scripts/build_platform_library.py --strict
```

当前 `--strict` 应失败，而且只应报告 12 个平台的 accepted quota shortage；规则 47 / 47 已全部 `curator_accepted`。

严格门禁当前预期 shortage 为：`wechat_official_accounts`、`xiaohongshu`、`douyin`、`bilibili`、`36kr`、`kuaishou`、`wechat_channels`、`tiktok`、`stackoverflow`、`product_hunt`、`hackernoon`、`hashnode`；当前缺口合计 93 条。

若出现 orphan evidence、accepted readback 缺失、duplicate URL、非命名搜索 backend 或 complete 平台少于两类真实 intent，说明账本回归，必须先修复。

只有 47 × 10 严格门禁通过、桌面与移动端回读通过后，才允许合并到 `main` 并发布 GitHub Pages。

## 不变的安全边界

- 浏览器全程只读；不发布、点赞、关注、评论、收藏、投票、私信、安装或下载。
- 不绕过登录、验证码、robots、付费墙、地区限制、API 审批或平台风控。
- 搜索摘要只能发现，不能作为最终证据。
- 动态/登录平台使用普通可见原生详情；公开 API 只在官方文档与授权范围内使用。
- 不把作者自述、vendor benchmark、目录评分或安全公告自动当作独立复现结论；保留版本和证据局限。
