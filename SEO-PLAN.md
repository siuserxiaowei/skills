# BUGFIRE SEO / GEO 发布计划

> 状态：发布前计划
> 制定日期：2026-07-16
> Canonical：待创建用户自有公开仓库后确定
> 数据限制：未使用实时关键词量、Search Console、DataForSEO 或 AI mention 数据；优先级基于产品意图与仓库内容，而非虚构流量预测。

## 1. 目标与定位

BUGFIRE 的 SEO/GEO 目标不是把一个桌面皮肤包装成“编程能力认证”，而是让真正需要以下体验的人能准确找到并理解它：

- 想给 Codex Desktop 添加桌宠或游戏化反馈的 macOS 用户
- 对 Vibe Coding 成长记录、像素宠物、Build 动画感兴趣的开发者
- 想制作 Codex 自定义桌宠、像素宠物包和本地任务板的创作者
- 关心 CDP 注入边界、官方签名和本地隐私的技术用户
- 想基于 Codex Dream Skin 制作独立扩展的维护者

一句话定位：

> BUGFIRE「补丁兽」是运行在 macOS 版 Codex Desktop 里的本地像素桌宠，用模拟 Build、Bug 喷火和 XP 成长提供可玩的编码反馈，不执行真实项目命令，也不代表官方认证。

高级用户还可以用完全本地的 `Bugfire Pack v1` CLI，把自己的背景图、宠物状态图、配色、台词和任务板编译成声明式桌宠包；编译器不下载远程素材，也不执行包内代码。

## 2. 发布前最高优先级

当前本地仓库只有指向 `https://github.com/Fei-Away/Codex-Dream-Skin.git` 的 `upstream`，尚未配置用户自有的 `origin`。**不要把独立产品文档或代码推到 `upstream`。**

发布顺序：

1. 创建用户自有仓库，例如 `Codex-Bugfire-Skin`。
2. 保留只用于同步的 `upstream`，把用户仓库设置为新的 `origin`。
3. 检查差异、许可证和 NOTICE，再推送 `codex/bugfire-pet` 或整理后的主分支。
4. 发布固定版本 `v1.2.0-bugfire.1`，不要只给浮动分支链接。
5. 确定 canonical 后，更新 `llms.txt`、README 分享链接和演示视频描述。

## 3. 建议的仓库元数据

### 仓库名

`Codex-Bugfire-Skin`

### GitHub Description

`BUGFIRE 补丁兽：运行在 Codex Desktop 里的 macOS 像素桌宠，支持模拟 Build、Bug 喷火、本地 XP 成长和自定义宠物包。`

### Topics

```text
codex
codex-desktop
openai-codex
desktop-pet
macos
vibe-coding
pixel-art
developer-tools
gamification
cdp
pet-pack
custom-theme
```

GitHub 允许最多 20 个小写 topics；即使仓库是私有的，topic 名称本身也可能公开，因此不要把内部客户名或未发布代号放进去。

### Social preview

- 画幅：建议 1280 × 640，PNG/JPG/GIF 小于 1 MB
- 主标题：`BUGFIRE · 补丁兽`
- 副标题：`BUILD · BURN BUGS · LEVEL UP`
- 必须出现：原创像素补丁龙、黑色终端、荧光绿日志、熔岩橙火焰
- 不出现：OpenAI 官方徽标、认证章、能力分数、第三方人物/IP
- 最小字：在 320 px 宽缩略图下仍可读

## 4. 关键词与搜索意图地图

以下是目标主题，不代表已测得搜索量。

| 主题簇 | 目标查询示例 | 意图 | 对应页面 |
| --- | --- | --- | --- |
| 品牌 | BUGFIRE 补丁兽、Codex Bugfire Skin | 导航/了解 | README |
| Codex 桌宠 | Codex 桌面宠物、Codex desktop pet、Codex 像素宠物 | 发现工具 | README + 演示视频 |
| Codex 皮肤 | Codex Desktop 皮肤、Codex 换肤 macOS、Codex Dream Skin | 比较/安装 | README + 使用说明 |
| Vibe Coding 游戏化 | vibe coding 宠物、编程 XP 系统、coding gamification | 探索方案 | 产品设计文章 |
| 安装与恢复 | Codex 桌宠安装、Codex skin restore、Codex CDP theme | 操作/排错 | `docs/USAGE.zh-CN.md` |
| 安全隐私 | Codex CDP 安全、桌面皮肤会读取代码吗 | 风险判断 | README 安全段 + 架构文章 |
| 自定义宠物包 | Codex 自定义桌宠、Codex pet pack、custom pixel coding pet | 制作/扩展 | README + `docs/CUSTOMIZATION.zh-CN.md` + macOS 技术说明 |

用词规则：

- 标题和首段自然出现“Codex Desktop 像素桌宠”，不重复堆砌。
- “Vibe Coding 级别”始终解释为本地活动进度，不写成能力测评。
- “证书”始终搭配“个人成长纪念卡 / 非官方认证 / 不代表专业资格”。
- “Build”始终标注“模拟”或“演示”，直到真实命令桥接被单独授权并实现。

## 5. 内容架构

| 优先级 | 内容 | 主要回答的问题 | 状态 |
| --- | --- | --- | --- |
| P0 | 根 README | 是什么、怎么玩、安全吗、如何安装 | 已完成本地稿 |
| P0 | 中文使用说明 | 安装、操作、验证、恢复、排错 | 已完成本地稿 |
| P0 | 自定义宠物包 CLI | 最小素材、声明字段、安全限制、编译、切换与恢复 | 已完成本地稿 |
| P0 | Release 页面 | 版本、变更、资产、校验值、测试环境 | 待公开仓库 |
| P1 | 安全架构文章 | 为什么不改 `.app`，CDP 与 Runtime binding 如何限定 | 已完成本地稿 |
| P1 | 60 秒演示视频 | 首次失败→修复→喷火→升级的完整证据 | 待录制 |
| P1 | 图片与 alt | 首页、宠物舱、失败、Lv3、成长卡、证书、任务页 | 已完成脱敏与文件核对 |
| P2 | 设计复盘 | 五级体系、奖励节奏和非能力认证边界 | 待写 |
| P2 | English README | 面向英文查询的准确概览 | 已完成完整产品概览；独立英文手册待真实需求 |

不要批量生成薄内容页面，也不要为每个等级创建近似重复页面。这个项目更适合一个权威 README、一个完整使用手册、稳定 Release 和少量有实证的技术文章。

## 6. On-page 检查清单

### README

- [x] 第一段直接回答产品是什么
- [x] H1 只出现一次
- [x] 使用问题式 H2/H3
- [x] Build 流程和等级使用表格
- [x] 靠前说明模拟 Build、非官方与隐私边界
- [x] 链接到完整使用手册
- [x] 所有 README 引用的 `docs/images/bugfire-*.png` 文件存在且与说明一致
- [ ] 发布后加入固定 Release 链接
- [ ] 发布后加入正确的 Issue / Discussion 链接

### 图片

| 文件名 | 推荐 alt | 目的 |
| --- | --- | --- |
| `bugfire-home.png` | BUGFIRE 补丁兽在 Codex Desktop 首页右下角的像素桌宠浮巢 | 产品全景 |
| `bugfire-pet-cabin.png` | 展开的 BUGFIRE 宠物舱，显示 Lv2、220/240 XP 与模拟 Build 按钮 | 核心交互 |
| `bugfire-build-failed.png` | BUGFIRE 首次模拟 Build 失败且不增加 XP | 失败规则 |
| `bugfire-level-up.png` | 补丁兽升级并生成 Lv3 BUGFIRE 成长卡 | 反馈闭环 |
| `bugfire-certificate.png` | BUGFIRE 非官方赛季成长纪念证书功能预览 | 里程碑 |
| `bugfire-task.png` | 脱敏任务页中的 Lv3 浮巢与原生输入控件 | 不遮挡输入 |

图片已裁掉原生侧栏；真实项目选择器由 `BUGFIRE DEMO` 覆盖，任务页使用脱敏演示内容。后续新增素材仍需执行同样的隐私检查。

### 链接与版本

- 使用固定提交或 Release 链接支撑可复现事实。
- 不把上游首页误写成 BUGFIRE 的 canonical。
- 内部链接使用相对路径，外部分享使用确定后的绝对 canonical。
- CHANGELOG、README、VERSION 和 Release tag 保持一致。

## 7. GEO 内容设计

每个核心问题采用相同结构：

1. 标题直接匹配用户问题。
2. 第一行给结论。
3. 用 2–4 句补充范围、条件和限制。
4. 提供表格、命令或实际截图作为证据。
5. 对安全、官方关系和认证性质使用一致措辞。

优先维护的可引用答案块：

- “BUGFIRE 是什么？”
- “Build 演示会运行真实命令吗？”
- “它会读取源码、任务或密钥吗？”
- “宠物等级和证书代表什么？”
- “如何完整恢复官方 Codex 外观？”
- “能否制作自己的宠物包，最少需要哪些文件？”

仓库已提供 `llms.txt`。确定公开 URL 后，把其中的相对链接改成稳定绝对链接，并保证文档无需 JavaScript 即可读取。

## 8. 技术 SEO 路径

### 只发布 GitHub 仓库时

- 完整 README、Description、Topics、License、Release 和 Social preview 是主要资产。
- 使用固定 Release URL 作为版本引用入口。
- GitHub 平台负责 robots 和页面渲染；不要声称可以在单仓库控制 crawler。
- 保留原始 Markdown 和 `llms.txt`，便于机器读取。
- GitHub Release 应基于固定 tag，承载安装资产和版本说明；源码自动归档不能替代经过验收的安装包。

### 增加 GitHub Pages / 文档站时

- 设置唯一 canonical 和 HTTPS。
- 生成只包含公开文档页面的 sitemap。
- 允许搜索型 AI crawler；训练型 crawler 依据许可策略单独决定。
- 若希望进入 ChatGPT 搜索摘要，确认没有阻止 `OAI-SearchBot`；它与用于潜在训练控制的 `GPTBot` 不是同一个用途。
- 提供根路径 `/llms.txt`。
- 关键内容服务端输出，不依赖客户端 JavaScript。
- 可添加 `SoftwareApplication`、`TechArticle`、`BreadcrumbList` 与真实视频的 `VideoObject`。
- 不为 Google 富结果新增商业站 `FAQPage`，不使用已弃用的 `HowTo` schema。

## 9. 外部传播与品牌提及

优先顺序：

1. GitHub Release：稳定版本和可复现事实源。
2. Bilibili / YouTube：未经剪辑的完整演示，并链接固定 Release。
3. 开发者社区：分享为什么把失败设计成“无 XP”，附安全边界和源码位置。
4. 维护者社交账号：发布版本变化和真实截图，不写“官方”“认证”“最强”等无法证明的词。
5. 用户案例：只收集自愿、可核验、已获授权的体验，不批量制造评论或问答。

每次对外发布保持一致的实体信息：项目名 `BUGFIRE「补丁兽」`、版本、仓库 URL、非官方声明、MIT 许可和维护者身份。

## 10. 30 天执行节奏

### 第 0–2 天：可发布

- 创建正确的用户自有仓库并修正 remote
- 已补齐并检查 6 张脱敏运行素材
- 跑完测试、doctor、verify 与 restore 证据
- 发布 `v1.2.0-bugfire.1` Release 和校验值
- 在 Release 附上可复现 starter pack 与编译生成的 `pack-report.json`
- 更新 `llms.txt` 为绝对 canonical

### 第 3–7 天：可理解

- 发布 60 秒演示视频
- 写一篇安全架构说明
- 建立 Issue / Discussion 模板，明确所需脱敏信息
- 检查中英文品牌名、版本和免责声明一致性

### 第 8–14 天：可引用

- 发布设计复盘：失败无 XP、修复只结算一次、成长阈值如何设计
- 邀请少量真实用户复现安装与恢复
- 把确认过的兼容版本和已知问题写进 Release

### 第 15–30 天：可衡量

- 查看 GitHub Traffic 的独立访客、来源站点、clone 与 Release 下载
- 若启用 Pages，再接入 Search Console 与 Bing Webmaster Tools
- 记录品牌查询、文档着陆页与真实 Issue，不用点赞数代替使用质量
- 经过足够公开信号后，再进行一次实际 URL 的 SEO/GEO 审核

## 11. 测量框架

| 目标 | 指标 | 数据源 | 当前状态 |
| --- | --- | --- | --- |
| 被发现 | 仓库独立访客、搜索来源 | GitHub Traffic / Search Console | 待发布 |
| 被理解 | README→Usage 点击、安装问题类型 | GitHub 链接与 Issue | 待发布 |
| 被使用 | Release 下载、验证成功反馈 | GitHub Release / 用户反馈 | 待发布 |
| 可恢复 | Restore 成功率、残留问题 | 验证记录 / Issue | 本地测试后公开摘要 |
| AI 可见 | 有来源的 AI 引用与品牌提及 | 平台逐项人工核验或合规工具 | 未验证 |

不要在没有可复现查询、日期、平台和引用链接时写“已被 ChatGPT/Google 收录”。

## 12. 发布验收

- [ ] 新 remote 属于用户自己的 BUGFIRE 仓库，不是上游
- [ ] canonical、Description、Topics、Social preview 已设置
- [ ] README 和 Usage 的命令与当前版本一致
- [ ] 已在干净目录复现 starter → validate → build → switch，并保留 `pack-report.json`
- [ ] 图片全部存在、脱敏、压缩且 alt 准确
- [ ] Release 包含版本、日期、测试摘要、恢复方法和校验值
- [ ] `llms.txt` 使用可访问的绝对链接
- [ ] 非官方、模拟 Build、非能力认证声明在 README 和 Release 中均可见
- [ ] 没有虚构下载量、排名、用户评价、AI 引用或官方背书

## 13. 官方依据

- [GitHub：用 topics 分类仓库](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [GitHub：Social preview 图片要求](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview)
- [GitHub：Release 与固定 tag](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [OpenAI：让网站可用于 ChatGPT 搜索](https://help.openai.com/en/articles/9237897-chatgpt-search)
- [Google Search Central：FAQ 与 HowTo 富结果变更](https://developers.google.com/search/blog/2023/08/howto-faq-changes)
