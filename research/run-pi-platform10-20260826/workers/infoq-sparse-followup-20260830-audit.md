# InfoQ sparse follow-up audit (2026-08-30)

本分片仅追加两条 InfoQ Writing 原始内容及其主审回读证据；没有修改
`candidates.json`、`review_queue.json`、`queries.tsv`、`sources.tsv`、
`evidence_cards.tsv` 或 `platform_coverage.tsv`。两条候选当前均为
`curator_review_ready`，不得在主策展人显式晋级前计入 accepted。

## 路径与边界

- 发现：Google 的有界 exact-site 查询（Pi Harness/AGENTS.md、Pi Agent route）。
- 回读：普通匿名 Chrome 访问各自 InfoQ Writing canonical URL；页面 HTTP 200，正文完整渲染。
- 未登录、未互动、未下载、未执行代码，未把 SERP 摘要当正文证据；InfoQ robots/安全边界未绕过。
- `agent-reach doctor --json` 在本机仍不可用（command not found），没有安装或升级工具。

## Candidate A — Pi + AGENTS.md Harness

- ID：`china-followup-infoq-e694c2ef78899b4bbbc16f4ff-pi-agents`
- URL：`https://xie.infoq.cn/article/e694c2ef78899b4bbbc16f4ff`
- 标题：**老掉牙的编程原则，才是 Pi 最强的 Harness（附完整 AGENTS.md）**
- 作者：**王翊仰**；页面发布：**2026-07-01**；页面字数：**5361 字**。
- `.article-detaile` 可见正文：**6262 字符**；SHA-256：
  `71550424580a9bd4c0c15120ed6b7e5306c951644233ad64c87360e62139ebd5`。
- 正文逐段明确 Pi 是主线：极简 agent loop/bash、没有内置 subagent、工具层与
  用户写入 `AGENTS.md` 的约束层、DRY/KISS/SOLID/YAGNI、权限与安全规则、
  可验证的工程工作流，并附完整 AGENTS.md 代码块。
- 去重：以当前 `review_queue.json`、`candidates.json` 和全部 worker candidate
  shards 扫描 candidate ID、InfoQ object ID、规范化 URL、标题/作者/日期；未见
  `e694c2ef78899b4bbbc16f4ff` 或同 URL。与已接受 InfoQ 演讲稿、InfoQ/36Kr/Baidu
  访谈簇的开场、作者、日期、正文指纹和结构不同，暂记 `independent_candidate`。
- 局限：作者自报速度/token 与设计观点不是独立 benchmark；规则和实现随版本漂移，
  需要回到当前 `earendil-works/pi` 源码核验。

## Candidate B — 精细控制 vs 开箱即用

- ID：`china-followup-infoq-7fce544d6cbdfded6b5cc6676-pi-route`
- URL：`https://xie.infoq.cn/article/7fce544d6cbdfded6b5cc6676`
- 标题：**“精细控制”和“开箱即用”的 Agent 开发路线**
- 作者：**Paul**；页面发布：**2026-05-16**；页面字数：**852 字**。
- `.article-detaile` 可见正文：**1261 字符**；SHA-256：
  `534d795469b7a0b39a565ef81acb08ebbd3800914127c078091fa2eac2fed19b`。
- 正文先说明 Agent Runtime 场景，再明确比较 DeepAgents 与 Pi；Pi 技术段落列出
  Agent Loop、Session Management、Context Compaction、Proxy Stream、ExecutionEnv、
  Skills/Templates 和 20+ 扩展点，并链接 `github.com/earendil-works/pi`、`pi.dev/packages`。
- 去重：当前本地队列/账本及所有 candidate shards 未见此 URL、InfoQ object ID、标题/作者/日期组合；
  与现有 InfoQ/36Kr/Baidu 访谈、Mario 演讲稿不是同一正文簇，暂记
  `independent_candidate`。
- 局限：正文很短且是比较/选型文章，Pi 内容虽为主要技术段落但深度有限；性能、自由度和
  路线判断均为作者观点，不能替代受控复现。

## 追加文件与复核

- Candidates：`infoq-sparse-followup-20260830-candidates.jsonl`
- Readbacks：`infoq-sparse-followup-20260830-readbacks.jsonl`
- 读取哈希、正文长度、作者/日期、canonical URL 和去重判定均与上述审计一致。
- 本分片没有晋级操作；主线程可在全局内容簇复核后，按显式 candidate ID 逐条调用
  `curate_worker_candidates.py --readback-file ... --allow-curator-readback`。
