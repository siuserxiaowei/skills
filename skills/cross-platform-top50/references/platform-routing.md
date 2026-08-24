# 28 渠道检索路由

仅在执行真实检索时读取本文。下表与 `research-contract.md` 的 canonical 28 对齐；它是覆盖合同，不是给每个平台分配入选名额。所有检索只读：不得发帖、点赞、评论、关注，也不得绕过登录、付费、验证码、robots、地区限制或平台风控。

## 1. 先体检，再做最小真实 probe

`doctor` 只能证明组件看起来可用，不能证明本次查询真能返回结果。每次运行先建能力账本，再选择路由。

1. 若可用，运行 `agent-reach doctor --json`，保存原始输出；多后端平台按 `active_backend` 选路。
2. 若计划使用 OpenCLI 的 Browser 型适配器，再运行 `opencli doctor`。这类适配器依赖 Browser Bridge（Chrome、扩展和可复用的浏览器会话）；“适配器存在”不等于 Bridge 已连接或账号已登录。标为公开 API / `Browser: no` 的适配器不应被 Bridge 状态误判为不可用。
3. 对每个准备实际使用的后端执行一个最小、只读、正常规模的 probe，例如 `opencli zhihu search "<主题>" --limit 1 -f yaml`。不要用 `--help`、版本号或空查询充当 probe。
4. 使用研究合同的 canonical 六字段能力模型，不能压成一个“可用”：
   - `tool_readiness=available|configured|unavailable|unknown`：命令和后端是否存在；
   - `bridge_state=connected|disconnected|not_required|unknown`：Browser Bridge 是否真实连通；
   - `auth_state=authenticated|anonymous|expired|required|unknown`：本次会话是否真正可读；
   - `quota_state=available|rate_limited|exhausted|not_applicable|unknown`：速率、月度额度或平台风控；
   - `authorization=granted_for_current_task|not_required|not_granted`：当前请求是否授权该访问；
   - `probe_result=success|empty|blocked|error`：最小真实查询的结果。
5. probe 成功只授权只读采集，不扩展到写操作。不要自动运行 `pipx upgrade`、`pip install`、`brew install` 或修改 OpenCLI/agent-reach 配置；缺工具时记录安装建议和降级路线。

## 2. 平台层级与覆盖状态

范围冻结时先按 `research-contract.md` 保留默认优先级，再明确适用性。用户点名会把渠道提升为 `required`；合同里的 `adjacent` 属于可选补充，不得冒充已处理的 `important`：

- `required`：用户点名，或该主题天然依赖该平台。平台覆盖状态必须走完 `complete|partial|rejected|blocked|not_applicable` 之一；不能因失败静默删除。
- `important`：默认应处理；若预算或能力不足，必须保留未处理原因和最小补验步骤。
- `not_applicable`：这是覆盖状态而非优先级，表示主题与渠道确实不匹配。必须写明判断依据；它不是省事标签。

`blocked` 表示路线适用但受到登录、限流、权限或访问边界阻塞；不要把 `blocked` 写成 `not_applicable`。搜索引擎只返回某平台的摘要时，该平台最多是 `partial/discovered`，不是已读取原文。

## 3. 路由优先级

本节选择的是平台访问后端；Go/Rust/Python 本地执行结构另按 [三引擎路由](engine-routing.md) 选择。平台 discovery 仍先用专用 CLI/API/搜索适配器；只有候选 URL 已发现且当前任务允许公开 fetch 时才可交给 Go，抓取完成的本地批次才可交给 Rust。换语言不能让登录型平台变成匿名公开平台。

按候选逐级使用：

1. **OpenCLI 专用适配器**：存在真实 `search/read/detail/transcript` 命令且最小 probe 通过时优先；需要 Bridge/登录的适配器按登录接力执行。
2. **官方 CLI / 公开 API**：如 GitHub `gh`、V2EX 公开 API、Exa；仍须 probe 并记录速率/额度。
3. **通用发现**：Exa，或已 probe 通过的 `opencli google|brave|duckduckgo search` 配合 `site:`。它只产生候选。
4. **原页回源**：平台专用 detail/read、`opencli web read --url "<URL>" --stdout true -f md`，或 Jina Reader `curl -sS "https://r.jina.ai/https://example.com/article"`。动态页、登录页和付费页失败时不得把摘要升级为证据。

RSS 若存在，使用已通过 probe 的 OpenCLI 具体适配器、Jina/原始 XML，或把它记作未配置能力；不要凭文档假设某个 MCP 或 Python 包已安装。

多条 route 返回候选时，不用单一路由分数直接拼接。先规范为共同候选合同，再用 `scripts/fuse_candidates.py` 的 weighted RRF 合并；每条保留 list/query/platform/rank/weight，互动不参与融合，结果固定为 `discovery_only`。中文或混合语种 QueryPlan 默认保存 CJK bigram tokens；可选 jieba 只有在运行时实际导入成功才登记为 `jieba`，否则显式回退。排名 token 与平台 `search_query` 分离，不能让 `site:` 或平台名提高相关性。

### 3.1 HTTP 身份与浏览器后端

- 默认 HTTP 返回空白或明显不完整时，先比较原页、Jina/reader、平台专用只读适配器、真实浏览器渲染，以及受控的 `Accept` / `Accept-Language` 内容协商；保存实际后端、状态码、内容类型、语言、`Vary` 和差异。不得伪装成 `OAI-SearchBot`、`ChatGPT-User`、`Claude-User`、`Claude-SearchBot`、`Bytespider` 等第三方官方 bot，也不得把 401/403、robots、登录墙或验证码当成换 UA 重试信号。
- `ego-browser` / ego-lite 仅登记为默认禁用的候选 `browser_session` 后端，当前风险门禁见 [ego-lite 适配评估](ego-lite-assessment.md)。只有门禁已关闭、命令已存在、最小真实 probe 通过、用户对本次登录型研究显式 opt-in，且使用低敏感独立 profile 时才可启用。它只接入 Python 控制面；Go 不接收其 Cookie/Authorization，Rust 不联网。
- 不因本 Skill 被调用而自动安装 ego-lite、运行其安装脚本、移除 quarantine、迁移 Chrome 全量资料、更新版本或切换 profile。安装/迁移是独立的高权限环境变更。首次候选评估记录版本、来源与当前隐私条款；以临时 Task Space 打开公开测试页、读取 snapshot、关闭空间作为最小 probe。
- ego-lite 登录接力仍遵守同一 checkpoint：只读任务使用精确平台 allowlist；用户接管后不得自动夺回控制。默认禁用原始 CDP、`serverFetch` / `browserFetch`、上传、下载和 Cookie/cache mutation；确有必要时必须与当前只读研究范围一致并单独记录。不要把供应商的“本地优先”宣传当作零数据外传证明。
- Wigolo 是另一个默认关闭的 Python 外部 Adapter，不与 ego-lite 合并，也不是核心引擎。只有用户显式启用，且兼容当前主机的原生单文件发行镜像在任何 probe 前通过 magic、源码冻结的发行 SHA-256、同一 FD 摘要与私有快照门禁，随后真实 probe 和安全能力 allowlist 通过，主要任务不是 CJK 或已显式接受 experimental 时才计划。调用方不能注入摘要；JavaScript、Node/npm CLI、任何 shebang/解释型脚本（含无后缀包装器）和未审计/重命名原生程序都失败关闭。当前摘要白名单为空；标准 npm `wigolo@0.2.1` 明确 No-go，没有生产路线。具体命令与负向门禁见 [Wigolo 外部适配合同](wigolo-adapter.md)。

## 4. Canonical 28 路由矩阵

命令中的 `<Q>`、`<URL>`、`<ID>` 必须替换。所有 OpenCLI 路由首次使用前都要通过最小 probe；只有其当前 `--help` 标为 `Browser: yes` 时才要求 Bridge，只有实际返回认证错误时才把登录列为必需。

| # | 渠道（规范名） | 首选发现与取证 | 访问条件、限制与合法降级 |
|---:|---|---|---|
| 1 | CSDN (`csdn`) | Exa 或 `opencli google search "site:blog.csdn.net <Q>" -f yaml`；回源用公开原文或 `opencli web read --url "<URL>" --stdout true -f md` | 当前无 CSDN 专用适配器；SERP 摘要只作候选，原文不可读则 `blocked/rejected` |
| 2 | 微信公众号 (`wechat_official_accounts`) | `opencli weixin search "<Q>" --limit 10 -f yaml`；原文 `opencli weixin download --url "<URL>" --output <DIR> -f yaml` | Browser Bridge；搜狗结果可能触发验证，公众号原文仍须回读，摘要不可接受 |
| 3 | 知乎 (`zhihu`) | `opencli zhihu search "<Q>" --type all --limit 10 -f yaml`；问题/回答用 `question`、`answer-detail`，专栏用 `download --url` | Bridge，部分内容需登录；折叠、登录墙或只见摘要时降为 `partial/blocked` |
| 4 | 小红书 (`xiaohongshu`) | `opencli xiaohongshu search "<Q>" --limit 20 -f yaml`；以搜索结果中含 `xsec_token` 的完整 URL 调 `note` | Bridge + 登录；不能用裸 note ID，正常节奏串行读取，验证码交由用户处理 |
| 5 | 微博 (`weibo`) | `opencli weibo search "<Q>" --limit 10 -f yaml`；详情 `opencli weibo post <ID> -f yaml` | Bridge + 通常需登录；风控/验证码不绕过，公开 `site:weibo.com` 仅补发现 |
| 6 | 抖音 (`douyin`) | `opencli douyin search "<Q>" --limit 10 -f yaml`；候选页的可见描述、互动与视频观察 | Bridge + 登录；当前无通用视频详情/字幕命令，不能从搜索元数据编造内容 |
| 7 | X / Twitter (`x`) | OpenCLI probe 通过时 `opencli twitter search "<Q>" --limit 15 -f yaml`，线程用 `opencli twitter thread <TWEET_ID> -f yaml`、长文用 `opencli twitter article <TWEET_ID> -f yaml`；否则按 doctor 的 `active_backend` 用 `twitter search` | OpenCLI 需 Bridge + 登录；twitter-cli 需有效认证。失败可定向重试并切换后端，但**不自动升级 pipx 包**；最多 3 轮后记缺口 |
| 8 | Bilibili (`bilibili`) | OpenCLI probe 通过时 `opencli bilibili search "<Q>" --type video --limit 20 -f yaml`，再用 `opencli bilibili video <BVID> -f yaml`、`opencli bilibili subtitle <BVID> -f yaml`、`opencli bilibili summary <BVID> -f yaml`；否则按 doctor 的 `active_backend` 用 `bili` | OpenCLI 需 Bridge/可能需登录；无字幕时只能用已观察内容。不要把元数据当逐字稿 |
| 9 | 掘金 (`juejin`) | 当前适配器只有 `hot` / `recommend`，可用于热点浏览；关键词发现用 Exa 或 `site:juejin.cn <Q>`，再回原文 | 不得把分类热榜冒充关键词搜索；付费小册不绕过 |
| 10 | YouTube (`youtube`) | OpenCLI probe 通过时 `opencli youtube search "<Q>" --limit 20 -f yaml`，再用 `opencli youtube video "<URL>" -f yaml` / `opencli youtube transcript "<URL>" -f yaml`；否则按 doctor 的后端用 `yt-dlp --dump-json "ytsearch20:<Q>"` 和字幕路线 | OpenCLI 需 Bridge；yt-dlp 路线需真实 probe。无字幕、区域限制和自动字幕误差分别记录 |
| 11 | Linux.do (`linuxdo`) | `opencli linux-do search "<Q>" --limit 20 -f yaml`；正文用 `opencli linux-do topic-content <ID> -f plain`，讨论用 `opencli linux-do topic <ID> -f yaml` | Bridge + 登录；登录限定主题必须走接力，不得用公开摘要代替正文 |
| 12 | GitHub (`github`) | `gh search repos "<Q>" --sort stars --limit 20`，按目的补 `gh search code "<Q>"` 或 `gh search issues "<Q>"`；详情用 `gh repo view` / `gh api` | 先 `gh auth status` 或最小公开 probe；stars 是互动信号，不证明内容质量或当前适用性 |
| 13 | 百度搜索 (`baidu_search`) | 若无已验证专用检索能力，用 Exa/其他已就绪搜索引擎补中文发现，并在 ledger 写明实际后端 | 这是 discovery channel；不得虚报为“百度已直搜”，SERP 必须回源 |
| 14 | Google Search (`google_search`) | `opencli google search "<Q>" -f yaml`，按平台加 `site:`；记录查询时间与地域上下文 | Bridge；仅发现，不直接形成 accepted evidence |
| 15 | Bing (`bing_search`) | 若无已验证 Bing 专用能力，用 Exa、Google/Brave/DDG 交叉补盲，并标实际后端 | 这是 discovery channel；不得把替代后端记为 Bing 直搜 |
| 16 | 今日头条 (`toutiao`) | `opencli toutiao hot --limit 30 -f yaml` 仅用于热点发现；关键词用 Exa/`site:toutiao.com <Q>` 后回源 | `articles` 是创作者自己的后台列表，不是全站关键词搜索；聚合/转载要追首发 |
| 17 | 36氪 (`36kr`) | `opencli 36kr search "<Q>" --limit 20 -f yaml`；从结果 URL 解析文章 ID，再 `opencli 36kr article <ARTICLE_ID> -f yaml` | Bridge；软文/转载/付费状态必须标注，关键数字回溯原始来源 |
| 18 | InfoQ (`infoq`) | Exa 或 `site:infoq.cn <Q>`；回源公开文章或 `opencli web read --url "<URL>" --stdout true -f md` | 当前无专用适配器；技术结论结合官方文档、代码或演讲原始材料核验 |
| 19 | SegmentFault (`segmentfault`) | Exa 或 `site:segmentfault.com <Q>`；回源公开问答/文章 | 当前无专用适配器；记录版本，原页不可读时不接受 |
| 20 | OSCHINA (`oschina`) | Exa 或 `site:oschina.net <Q>`；回源公开文章/资讯/软件页 | 当前无专用适配器；聚合内容回到原文，项目状态回 GitHub/Gitee/官网 |
| 21 | V2EX (`v2ex`) | 先以 Exa/`site:v2ex.com/t <Q>` 发现 topic ID；再 `opencli v2ex topic <ID> -f yaml`，必要时按节点 `node <NAME>` 浏览 | 公开 API 只有 hot/latest/node/topic/replies，**没有关键词搜索 API**；`site:` 结果不等于已完成，需回 topic API/原页 |
| 22 | Reddit (`reddit`) | `opencli reddit search "<Q>" --limit 15 -f yaml`；详情用 `opencli reddit read <POST_ID_OR_URL> -f yaml` | Bridge + 登录；无匿名零配置保证。登录或地区阻塞时只保留公开线索并发起接力 |
| 23 | Hacker News (`hacker_news`) | `opencli hackernews search "<Q>" --limit 20 -f yaml`；详情/评论用 `opencli hackernews read <ID> -f yaml` | 公开 API、无需登录；原链接与 HN 讨论是两个证据对象 |
| 24 | Medium (`medium`) | `opencli medium search "<Q>" --limit 20 -f yaml`；公开原文回源 | Bridge；付费墙不绕过，优先作者公开原站或 canonical URL |
| 25 | LinkedIn (`linkedin`) | 主题内容优先 Exa/`site:linkedin.com/posts <Q>` 发现，再在已知作者上 `opencli linkedin posts --profile-url <URL>`；timeline 只补已登录 feed | Bridge + 登录；`opencli linkedin search` 是职位搜索，不用于主题帖子检索；`people-search` 消耗月度 Commercial Use Limit，非人物检索不要用。记录 `quota_state=rate_limited|unknown` |
| 26 | 快手 (`kuaishou`) | Exa/搜索引擎 `site:kuaishou.com <Q>`；候选公开页可见元数据/人工观察 | 当前无 OpenCLI `kuaishou` 适配器；验证码/登录由用户处理，无原页证据则 `blocked` |
| 27 | 微信视频号 (`wechat_channels`) | 搜索引擎公开转发页、用户提供的公开视频链接/导出/截图 | 当前 OpenCLI `wechat-channels` 只有登录/发布/身份命令，**没有只读搜索/详情适配器**；本 Skill 禁止为检索调用 publish，只能登录接力或标 blocked |
| 28 | TikTok (`tiktok`) | `opencli tiktok search "<Q>" --limit 10 -f yaml`，公开账号用当前 `opencli tiktok --help` 列出的 `profile` / `user` 只读命令 | Bridge + 登录/地区可达性；互动是热度信号，搜索元数据不足以支持视频内容主张 |

按主题需要，可把 Stack Overflow、DEV、Product Hunt、Gitee、Substack、arXiv、官网/官方文档等列为 `adjacent_sources`。它们可以提高证据质量，但不得替换用户点名的 canonical required 渠道，也不得为了扩大数字把“渠道数”虚报为平台完成数。

## 5. Exa 限流与通用发现降级

Exa 只作为发现后端。调用示例：

```bash
mcporter call 'exa.web_search_exa(query: "site:example.com <Q>", numResults: 10)'
```

- 若返回 HTTP 429、rate limit、quota exhausted 或等价错误，立即写入 `quota_state=rate_limited|exhausted`；读取 `Retry-After` 时尊重它。
- 最多一次有界退避重试；仍失败就切换到已 probe 通过的 `opencli google search`、`opencli brave search` 或 `opencli duckduckgo search`，也可用平台专用适配器。
- 降级后保存 `requested_backend=exa` 与 `actual_backend=<真实后端>`，不得仍声称“Exa 搜索完成”。不要通过并发请求、换账号或自动安装/升级来规避额度。

## 6. 查询组、probe 与账本

每个适用渠道至少记录两类查询：

- 精确词：主题原词、英文名、产品名、旧名、别名。
- 高价值意图词：教程、案例、评测、争议、问题、复盘、实战、源码、访谈、`review`、`tutorial`、`case study`、`best practices` 中与用途相关的词。
- 时效/版本词：易变主题再加年份、版本或日期范围，并核对页面显示的是发布、更新还是生效日期。

查询账本至少写：渠道、层级、查询、计划后端、实际后端、probe 时间、canonical 六字段能力状态、执行时间、候选数、错误、重试、降级和恢复点。相同路径最多 3 轮有新证据的定向修复；不要无限重试。

## 7. 登录接力：checkpoint / resume

当 Bridge 未连接、账号未登录、Cookie 失效或出现验证码时，完成所有不依赖该登录的只读工作，然后一次性创建 checkpoint 并暂停受阻路线。

checkpoint 必须保存：

```text
run_id, topic, platform, stage, exact_probe_or_command,
tool_readiness, bridge_state, auth_state, quota_state,
authorization, probe_result, error_summary, completed_query_ids,
pending_query_ids, candidate_ids, artifact_paths, next_safe_command,
created_at, expires_or_unknown
```

给用户的接力只包含：打开哪个平台、使用哪个 Chrome profile（若已知）、完成登录/验证码、保持 Chrome 与 OpenCLI 扩展可用，并回复“已完成登录接力：<platform>”。不要索取或打印密码、Cookie、token。

resume 时：

1. 读取同一 `run_id` 的 checkpoint，不从头重跑已完成查询；
2. 再执行 `opencli doctor`（如适用）和同一个最小只读 probe；
3. probe 通过后将 `auth_state=authenticated`、`probe_result=success`，从 `pending_query_ids` 续跑；
4. probe 仍失败则更新 checkpoint 和最小下一步，不把用户的“已登录”本身当成功证据；
5. 会话过期、主题或范围改变时新建 checkpoint 版本，保留旧记录。

## 8. 覆盖门禁

- 默认计划覆盖 canonical 28；用户可显式删减。称“20+ 平台完成”前，至少 20 个 canonical 渠道进入 `complete|partial|rejected|blocked|not_applicable`，并且至少 12 个平台实际召回候选。平台覆盖状态与来源抓取状态分开：只有原页成功读取的来源才可记 `fetched`。
- required 渠道不得为 `pending`；important 渠道必须已处理，或有明确的预算/能力缺口。发现引擎本身（百度/Google/Bing）只有回源后的候选可进入证据池。
- 某渠道零入选不等于未覆盖；反之，通过一次通用搜索发现 20 个域名也不等于完成 20 个平台。
- 合格结果不足 N 时交付真实 Top K、缺口和 resume/checkpoint 路径。不得凑数、虚报覆盖、虚报并发，也不得把 `blocked` 或 `not_applicable` 伪装成 fetched。
