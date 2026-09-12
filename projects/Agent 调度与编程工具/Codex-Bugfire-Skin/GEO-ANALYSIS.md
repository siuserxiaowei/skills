# BUGFIRE GEO 可发现性分析

> 分析日期：2026-07-16
> 分析对象：本地仓库 `Codex-Bugfire-Skin` 的 README、使用文档与发布结构
> 重要限制：该独立扩展尚未配置用户自有的公开仓库或规范 URL；当前只有指向 `Fei-Away/Codex-Dream-Skin` 的只读同步语义 remote `upstream`，没有 `origin`，且本次没有推送。因此本文评估的是**发布准备度**，不是实际收录、排名或 AI 引用表现。

## 1. GEO Readiness Score：72/100（仓库发布准备度）

本轮改造前的只读基线约为 `41/100`：根 README 仍以通用 Dream Skin 为主、没有 BUGFIRE 答案块、公开截图和机器导航。完成中英文首页、事实表、FAQ、使用说明、自定义宠物包 CLI 文档、`llms.txt` 与 6 张脱敏运行素材后，仓库级准备度按同一启发式提升到 `72/100`。新增宠物包文档补全了事实，但没有解决公开 URL、Release 或第三方来源等主要缺口，因此不单独上调分数。评分公式就是下表五项得分直接相加；这是 `v1` 人工审计量表，用于前后版本保持同一口径，不是统计模型。这些数字只表示内容与证据完整度，不是搜索排名或 AI 引用保证。

| 维度 | 得分 | 判断依据 |
| --- | ---: | --- |
| Passage-level citability | 23/25 | 中英文 README 首段直接定义产品，关键事实、限制、门槛和 FAQ 可独立引用 |
| Structural readability | 19/20 | H1→H2→H3 清晰，问题式标题、步骤、表格、FAQ 和使用说明完整 |
| Multi-modal content | 15/15 | 6 张已检查的脱敏运行素材覆盖首页、宠物舱、失败、Lv3 成长卡、任务页与证书 PNG |
| Authority & brand signals | 8/20 | 有固定上游提交、版本与安全边界；没有公开维护者页面、独立 Release 或第三方提及证据 |
| Technical accessibility | 7/20 | README、Markdown、相对链接和 `llms.txt` 可机器读取；仍没有公开 canonical、索引或 crawler 访问证据 |

这个 72 分不表示 BUGFIRE 已经会出现在 Google AI Overviews、ChatGPT 或 Perplexity。最大的缺口不是文案，而是尚未发布到用户自有、可抓取、可长期引用的规范地址。

## 2. 平台准备度

| 平台 | 准备度 | 当前判断 |
| --- | ---: | --- |
| Google AI Overviews | 58/100 | README 结构和答案块较好，但尚无独立 URL、索引状态、Search Console 或传统搜索排名证据 |
| ChatGPT 搜索 | 70/100 | 双语定义、事实表、限制、来源、运行证据与 `llms.txt` 较清晰；公开实体信号仍缺失 |
| Perplexity | 66/100 | 文档、截图和固定代码证据适合摘要；尚无公开 Release、社区讨论或第三方来源可交叉引用 |
| Bing Copilot | 58/100 | 没有可检查的 Bing 索引、IndexNow 或规范站点；现阶段只能评估仓库内容准备度 |

以上平台分数是基于同一仓库交付物的内部准备度估计，不是平台官方评分，也没有使用付费关键词或 LLM mention 数据源；在获得公开 URL 和可复现查询前，不应用它们做对外效果承诺。

## 3. AI Crawler Access Status

| Crawler | 状态 | 原因 |
| --- | --- | --- |
| GPTBot | 未验证 | 独立扩展无公开规范 URL |
| OAI-SearchBot | 未验证 | 独立扩展无公开规范 URL |
| ChatGPT-User | 未验证 | 独立扩展无公开规范 URL |
| ClaudeBot | 未验证 | 独立扩展无公开规范 URL |
| PerplexityBot | 未验证 | 独立扩展无公开规范 URL |
| CCBot / 训练类 crawler | 未配置 | 尚未决定公开站点的训练数据授权策略 |

如果只发布为 GitHub 仓库，crawler 访问由 GitHub 的平台级策略决定，单个仓库不能可靠地配置自己的 `robots.txt`。如果后续启用 GitHub Pages 或独立文档站，再明确允许搜索型 crawler，并依据项目许可决定是否允许训练型 crawler。

## 4. llms.txt Status

仓库根目录已新增 [`llms.txt`](llms.txt)，包含产品定义、关键文档、可引用事实、安全边界和许可说明。当前状态是“本地已准备、线上未生效”。

发布到用户自有仓库或文档站后，需要完成两件事：

1. 把相对链接替换为稳定的绝对规范 URL。
2. 确认 `llms.txt` 能从站点根路径直接访问，而不是只能在前端 JavaScript 中加载。

## 5. Brand Mention Analysis

| 渠道 | 已验证状态 | 下一步 |
| --- | --- | --- |
| Wikipedia / Wikidata | 未检查、无主张 | 早期小工具不应为 SEO 强行创建条目；先积累独立可靠来源 |
| Reddit | 未检查、无主张 | 发布真实演示与技术说明，避免自问自答或批量灌水 |
| YouTube / Bilibili | 未检查、无主张 | 制作 30–60 秒失败→修复→喷火升级的完整录屏 |
| LinkedIn / 即刻 / X | 未检查、无主张 | 由维护者实名说明设计动机、安全边界和固定版本 |
| GitHub | 上游来源可验证，独立 fork 未发布 | 先建立用户自有仓库与 Release，再获取可引用的版本页 |

没有公开数据支持“已有品牌曝光”或“已被 AI 收录”的说法，所以本报告不作此类结论。

## 6. Passage-Level Citability

当前文档中最适合 AI 单段引用的内容包括：

1. README 第一段：用直接定义说明 BUGFIRE 是什么、运行在哪里、提供什么体验，以及不是什么。
2. “BUGFIRE 能做什么？”：在一个自包含段落里说明 72 px 浮巢、首次存档、失败/修复路径与隐私边界。
3. “隐私和安全边界”：明确 CDP、Runtime binding、本地存档字段及不读取的数据。
4. “五级成长体系”：用表格给出等级、XP、阶段与技能的精确映射。
5. 使用手册的“什么时候生成证书？”：列出 Lv5、10 次成功、3 次修复三项门槛和固定免责声明。
6. “如何制作自定义宠物包？”：明确最小素材、六种状态、校验限制、无远程下载、权利声明和进度切换行为。
7. “为什么不修改 Codex.app？”：用独立安全架构页说明签名验证、回环 CDP、Runtime binding、进程身份、存档和 Restore 边界。

GEO 常用的 134–167 词建议来自英文内容实践，不能机械换算为中文字数。本项目更适合保持“一个标题回答一个问题、首句给结论、2–4 句补充限制”的短答案结构。

## 7. Server-Side Rendering Check

- README、Markdown 文档和 `llms.txt` 都是静态源文件，不依赖客户端 JavaScript 才能读取。
- 若发布为公开 GitHub 仓库，README 通常由 GitHub 服务端渲染，原始 Markdown 也可直接访问。
- BUGFIRE 本身是桌面端注入工具，不是公共网站；renderer 的实现方式与搜索抓取无关。
- 由于没有独立扩展的公开 URL，本次无法验证 HTTP 状态、canonical、robots、缓存头或索引结果。

## 8. Top 5 Highest-Impact Changes

1. **建立用户自有公开仓库和 canonical。** 不要把 BUGFIRE 分支推到当前 `upstream`；先创建正确目标并设为 `origin`，再设置仓库描述、topics 和 Release。
2. **发布可复现的 `v1.2.0-bugfire.1` Release。** 包含变更日志、安装包校验值、验证结果、恢复步骤、固定截图、starter pack 和 `pack-report.json`，让 AI 可以引用稳定版本事实。
3. **发布短视频证据。** 静态截图已经齐全；下一步增加一段未经跳剪的失败→修复→喷火→升级录屏，并链接固定 Release。
4. **增加可核验的维护者和更新时间。** 在公开仓库说明维护者、联系/Issue 入口、版本日期和测试环境；不要虚构资历或官方关系。
5. **获取真实第三方提及。** 通过技术文章、视频说明和用户反馈积累独立来源，优先真实使用过程，不购买或批量制造“品牌提及”。

## 9. Schema Recommendations

GitHub README 不是可靠承载 JSON-LD 的页面，不建议把 `<script type="application/ld+json">` 塞进 README。若后续建立 GitHub Pages 或独立文档站，可考虑：

- `SoftwareApplication`：名称、版本、操作系统、许可、下载/代码地址、应用类别
- `TechArticle`：安装与安全架构文章的作者、发布日期、更新时间和引用来源
- `BreadcrumbList`：文档站的层级导航
- `VideoObject`：真实演示视频的时长、缩略图和上传日期

FAQ 可保留为可见内容帮助搜索与 AI 摘要，但不要为了 Google 富结果新增 `FAQPage` 标记；也不要使用已弃用的 `HowTo` schema。

## 10. Content Reformatting Suggestions

### 本次已经完成

- 把 README 第一段改为直接的“BUGFIRE 是什么”答案块
- 使用问题式 H2/H3 覆盖安装、玩法、安全、恢复与常见疑问
- 把 Build 流程、等级、路径和平台准备度改成表格
- 将“模拟 Build”“非官方”“不代表专业资格”放在靠前且可独立引用的位置
- 新增中文使用手册、`llms.txt` 和发布计划
- 完成自定义宠物包 CLI 的最小素材、字段契约、安全边界与进度切换说明
- 新增可独立引用的安全架构页，区分历史 live evidence、静态测试和当前实时状态

### 发布前仍需完成

- 当前 6 张 `docs/images/bugfire-*.png` 已存在并完成隐私检查；发布后继续保持 alt 与真实状态一致
- 给 Release 添加真实测试输出摘要和校验值，不只写“已验证”
- 确定规范仓库 URL 后，把 README、`llms.txt` 和所有分享文案中的链接统一为 canonical
- 当前英文 README 已是完整产品概览；英文用户成为明确受众后，再补充独立英文使用手册，不复用上游通用皮肤文案

## 11. 数据与工具限制

本次只分析了本地仓库内容、Git remote 和文件结构。没有独立公开 URL，因此没有进行站点抓取、robots 检查、Google/Bing 索引检查、Core Web Vitals、Search Console、DataForSEO 关键词量或 AI 平台品牌提及查询。所有“未验证”均保持为未知，而不是推断为允许、阻止、已收录或未收录。
