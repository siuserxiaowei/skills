# 会议纪要深度拆解交接

## 本轮计划

目标：把三份会议纪要在线 HTML 从“摘要级拆解”升级为“详细研究应用简报”，保持三个独立页面，不合并。

执行路径：

1. 建立隔离 worktree：`.worktrees/deepen-meeting-analysis`。
2. 用 `xiaowei-goal` 三阶段流程重做内容结构：广域调研、Deep Research、业务应用。
3. 每份报告独立深化：信息点级理解、来源池、证据表、事实/推断/假设、风险清单、道法术器势、下一步 `/goal`。
4. 用 pandoc 重新生成三个 HTML。
5. 验证本地文件、GitHub Pages 在线链接和首页入口。

## 50 轮审视阶段摘要

| 轮次 | 阶段摘要 | 证据缺口 | 风险 | 下一步决策 |
|---|---|---|---|---|
| 10 | 目标确认：三个独立在线报告必须更详细，不合并，不公开私有逐字稿。成功标准是每份报告都能独立支撑小伟后续做 App、网站或 AI agent 业务。 | 原始飞书链接私有；公开页面不能放私有链接。 | 把会议里的经验当成已验证事实。 | 公开页面只写结构化转述，事实/推断/假设分开。 |
| 20 | 证据收集：补充 SEO/AI 搜索、MCP/Agent、App Store/Google Play、教育数字化、游戏化、AI 合规、版权、LLM 安全资料。 | 小红书商家规则部分可能需要登录后台。会议销售数字无法外部核验。 | 引用低质量二手文章或过度相信单一来源。 | 优先官方、一手、研究论文；弱证据标注为待验证。 |
| 30 | 实现路径：三份报告各自一个 worker subagent，文件写入范围互不重叠；主线程负责整合、生成、验收、发布。 | worker 需要足够会议上下文，否则可能泛化。 | 三份报告深度不一致。 | 给 worker 提供会议要点、文件范围、必备章节和验证命令。 |
| 40 | 验收路径：检查 Markdown 必备章节、HTML 标题、首页入口、URL 状态码、git diff、发布 commit。 | 浏览器截图不是必要条件，但可作为后续视觉验收。 | HTML 生成遗漏、链接 404、首页未更新。 | 用命令验证为主；发布后 curl 三个在线链接。 |
| 50 | 交接标准：产物路径、提交号、验证证据、风险和明早最该看的三件事完整记录。 | 更深市场判断需要后续授权做竞品/平台后台/用户访谈。 | 继续扩大范围导致迟迟不能交付。 | 本轮先完成三份深度 HTML，后续另开 `/goal` 做市场验证。 |

## 执行记录

- 2026-06-15：确认用户新要求，采用计划工具与 worktree。
- 2026-06-15：在主仓库提交 `.worktrees/` 忽略规则，提交 `4d5f48e`。
- 2026-06-15：创建 worktree `.worktrees/deepen-meeting-analysis`，分支 `docs/deepen-meeting-analysis`。
- 2026-06-15：基线验证 `python3 scripts/validate_xiaowei_goal.py examples/practice-run-ai-website-goal.zh.txt` 通过。
- 2026-06-15：创建实施计划 `docs/superpowers/plans/2026-06-15-deepen-meeting-analysis.md`。
- 2026-06-15：分派三个 worker subagent，分别深化三份报告。
- 2026-06-15：三份 worker 返回状态：报告 1 `DONE`，报告 2 `DONE`，报告 3 `DONE_WITH_CONCERNS`。报告 3 的 concerns 为 pandoc 语言包 warning 和公开来源边界，非阻断。
- 2026-06-15：三份规格验收均返回 `SPEC_PASS`。
- 2026-06-15：整体质量验收返回 `QUALITY_PASS`。
- 2026-06-15：根据质量建议，首页删除历史第四入口，只保留三份会议报告；教育报告弱相关生活信息抽象为创始人节奏管理。

## 产物路径

- 计划文档：`docs/superpowers/plans/2026-06-15-deepen-meeting-analysis.md`
- 交接文档：`docs/meeting-analysis-handoff-20260615.md`
- 报告 1 源稿：`docs/ai-product-application-transformation-20260510.md`
- 报告 1 HTML：`docs/ai-product-application-transformation-20260510.html`
- 报告 2 源稿：`docs/ai-product-development-acquisition-20260510.md`
- 报告 2 HTML：`docs/ai-product-development-acquisition-20260510.html`
- 报告 3 源稿：`docs/ai-education-product-planning-20260510.md`
- 报告 3 HTML：`docs/ai-education-product-planning-20260510.html`

## 验证证据

- `python3 scripts/validate_xiaowei_goal.py examples/practice-run-ai-website-goal.zh.txt`：基线验证通过。
- `pandoc docs/ai-product-application-transformation-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-product-application-transformation-20260510.html`：退出码 0；仅有 pandoc zh-CN 翻译 warning。
- `pandoc docs/ai-product-development-acquisition-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-product-development-acquisition-20260510.html`：退出码 0；仅有 pandoc zh-CN 翻译 warning。
- `pandoc docs/ai-education-product-planning-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-education-product-planning-20260510.html`：退出码 0；仅有 pandoc zh-CN 翻译 warning。
- `rg '信息密度升级说明|Deep Research 证据表|关键判断分层|风险清单与验证动作|道法术器势|下一步 /goal|资料链接' docs/...`：三份 Markdown 均命中核心章节。
- `rg 'feishu\\.cn|larksuite|niz841|from_copylink|NO3Ld|PXoB|CwcG|F7vE|VZOq|XJr2' docs/...`：无命中，未公开飞书私有 URL。
- 待办标记与弱相关生活信息检查：发布文件无命中。
- 首页入口检查：只命中三份会议报告入口，未命中旧页面入口。
- `git diff --check`：无输出，未发现空白错误。
- 发布后补充：三个 GitHub Pages 线上链接状态码。
- 发布后补充：最终 commit SHA。

## 风险

- 飞书纪要属于私有来源，公开页面只做结构化转述，不发布私有链接和原始逐字稿。
- 小红书虚拟商品、卡密、教育类商品规则可能需要后台登录核验；本轮只标注风险，不做确定性合规结论。
- 会议中提到的销售额、订单、注册用户数据来自会议纪要，未做外部审计；公开报告应标注为会议信息。
- AI 生成内容、未成年人教育场景、公开排名、版权归属等问题具有合规风险；本轮只给风险控制建议，不替代法律意见。

## 明早小伟最该看的三件事

1. 三个在线 HTML 的第一屏结论和目录，确认是否符合“小伟风格”和阅读密度。
2. 每份报告里的 `业务落地`、`风险清单`、`下一步 /goal`，决定后续先做哪个业务闭环。
3. `证据缺口`，尤其是小红书规则、真实付费数据、老师留存数据和合规边界。
