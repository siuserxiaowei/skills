# Pi 47 × 10 研究任务交接

状态：`paused_by_user`
Run ID：`pi-platform10-20260826`
交接日期：2026-08-26
目标：站点当前 47 个平台，每个平台至少 10 条已回读原页并通过主审的 Pi 内容。

## 已完成

1. 已冻结 47 个 required 平台、主题歧义排除、每平台 10 条门槛和 17 个单条字段。见 `run_manifest.json` 与 `PLATFORM_ACCEPTANCE.md`。
2. 已运行 `agent-reach doctor --json`、`opencli doctor` 和真实小 probe。GitHub、YouTube、Bilibili、V2EX、Exa、Jina 可用；X 搜索返回 HTTP 404；OpenCLI daemon 可用但 Browser Bridge 未连接。见 `tool_readiness.json`。
3. Python / Go / Rust 三个研究引擎已真实 probe 为 ready。见 `engine_probe.json`。
4. 已保存 37 个平台的 worker-checked 规则：
   - `workers/china-rules.tsv`：18 个中文平台；
   - `workers/global-rules.tsv`：19 个全球平台；
   - 合并后的 `platform_rules.tsv`：37 行规则，不含表头。
5. 已从上一轮冻结研究包复用 42 条主审原页种子，分布于 14 个平台。当前只有 GitHub 达到 10 条；DSH-only GitHub 文档已从 Pi 平台库种子中剔除。
6. 已实现新的 47 × 10 平台墙：平台搜索、状态过滤、进度、规则面板、原页列表、移动端布局和深链接恢复。数据来自仓库根目录 `platform-library.json`。
7. 已实现三个恢复脚本：
   - `scripts/import_platform_seeds.py`：重新导入上一轮主审种子；
   - `scripts/compile_platform_review_queue.py`：独立合并规则与候选分片，规则不会因候选缺失而丢失；
   - `scripts/build_platform_library.py`：生成公共 JSON；`--strict` 会在任一平台少于 10 条时失败。
8. 已验证：`node --check app.js`、Python 编译、桌面平台墙、390px 移动端、平台搜索和控制台错误检查。

## 当前真实计数

- 平台：47
- 目标：470 条（每平台至少 10 条）
- 已接受种子：42 条
- 已达标平台：1 / 47（GitHub，20 条）
- worker-checked 平台规则：37 / 47
- 新候选分片：0 条结构化落盘
- 严格门禁：失败，这是正确状态；不得发布为“47 × 10 已完成”

已接受种子分布：GitHub 20、YouTube 5、Official Web 4、V2EX 2、Substack 2；Bilibili、DEV.to、Hacker News、InfoQ、掘金、Linux.do、SegmentFault、知乎、arXiv/OpenReview 各 1。

## 中断时尚未完成

1. 三个候选文件均未在中断前写出：
   - `workers/china-candidates.jsonl`
   - `workers/global-candidates.jsonl`
   - `workers/ecosystem-candidates.jsonl`
2. 生态/日本/包管理分片的 10 个规则尚未写出：V2EX、Official Web、npm、Zenn、HackerNoon、Qiita、Hashnode、note、Composio、PyPI。
3. 37 行规则仍为 `worker_checked`，未由主策展人逐条核验官方来源。
4. 中文规则中的 `fetched_count` 是 worker 中断前的观察计数，不等于结构化候选，也不等于 accepted；对应 URL 没有全部落盘，不能直接计入 470。
5. 尚未执行公共 URL Go collector、Python extraction、Rust 去重、主策展逐条接受、sources/evidence/coverage 最终账本。
6. 尚未创建登录型平台的 canonical resume checkpoint，也未开始用户扫码/登录接力。
7. 新平台墙没有推送到 `main`，线上 GitHub Pages 保持原正式版本。

## 必须用户接力或合法凭证的平台

优先集中处理：微信公众号、小红书、微博、抖音、百度搜索、今日头条、快手、微信视频号、X、Google Search、Reddit、Medium、LinkedIn、TikTok、Product Hunt、Substack、Bluesky；OSCHINA/Gitee 的部分正文也可能需要普通浏览器验证。

不要绕过登录、验证码、robots、地区限制或平台风控。搜索摘要只能做发现。Google/Baidu/Bing 的 10 条必须由该命名引擎真实发现后逐页回源，替代后端不能冒充。

## 另一台电脑的恢复顺序

```bash
git clone https://github.com/siuserxiaowei/pi-runtime-field-guide.git
cd pi-runtime-field-guide
git fetch origin
git switch codex/pi-platform10-handoff

agent-reach doctor --json
opencli doctor
python3 scripts/compile_platform_review_queue.py --allow-missing
python3 scripts/build_platform_library.py
```

接着按以下顺序推进：

1. 读取本文件、`run_manifest.json`、`PLATFORM_ACCEPTANCE.md`、`tool_readiness.json`。
2. 先补 10 个 ecosystem 规则；再按三个 shard 生成候选 JSONL。worker 只能写 `evidence_status=worker_checked`。
3. 对需要登录的平台先保存 canonical checkpoint，再让用户在内置浏览器完成正常登录/扫码；恢复时只跑 pending query。
4. 运行 `python3 scripts/compile_platform_review_queue.py`，确认 3 个 candidate shard 和 3 个 rule shard 都存在，不再使用 `--allow-missing`。
5. 主策展人逐条回读原页，处理歧义、版本、转载和跨发；只有主审后才能写入 `candidates.json` 且标 `evidence_status=accepted`。
6. 为公开 HTTP URL 执行 robots-aware Go collector；动态/登录平台使用原生 detail/read/transcript。再用 Rust 处理 URL 归一、指纹和近重复复核。
7. 更新 `sources.tsv`、`evidence_cards.tsv`、`platform_coverage.tsv` 与失败账本。
8. 运行严格门禁：

```bash
python3 scripts/build_platform_library.py --strict
node --check app.js
python3 -m http.server 4173
```

只有严格门禁通过、桌面/移动端回读通过后，才合并到 `main` 并发布 GitHub Pages。

## 重要注意

- 当前工作分支是交接分支，不是线上发布分支。
- `platform-library.json` 当前如实显示 42 条与 1 个达标平台，是进行中快照。
- 不要为了 10 条配额使用低相关、搜索摘要、标题猜测、重复转载或未读原页。
- 若某个平台合法可访问内容不足 10 条，保留真实 Top K 与缺口，不能把 `partial/blocked` 改成 `complete`。
