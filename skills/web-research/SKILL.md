---
name: web-research
description: 互联网研究总入口。用于跨平台且跨阶段，或用户尚未确定工具的研究任务，把“搜索发现、候选核验、内容归档、按需转写分析”路由到 unified-search、content-archive、bookmarks-export 与 asr。若用户只要求搜索、只处理已知链接、只导出私人收藏或只转写已有音视频，应直接使用对应子 Skill。Use when an internet-research request spans multiple stages, the correct child route is unclear, or the user explicitly invokes $web-research.
---

# 互联网研究

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

本 Skill 扮演研究路由层的角色，隶属于用户自己的工具体系；它既不是 OpenCLI 的外壳，也不是 AnySearch 或别的某个 CLI 的封装。底层接入的后端允许更换，但用户意图与安全边界的定义不随后端变动。

## 适用情形

满足以下任一条件时才走本 Skill：

- 一次请求包含两个以上阶段，比如“先检索，再筛选并把来源存档”。
- 一次请求横跨多个平台，并且除检索外还涉及候选确认、归档、转写或更进一步的分析。
- 用户只给出研究目的，没有指明要用搜索、归档还是收藏导出。
- 在动手之前需要先对多个后端做体检，以便挑出一条安全可行的路线。

如果意图是单一且明确的动作，则直接路由到对应子 Skill：

只做一阶段搜索时，不管覆盖一个还是多个平台，一律进入 `$unified-search`——仅仅“跨平台”这一点不足以触发本总路由。

| 用户意图 | 目标 Skill |
|---|---|
| 按关键词检索、批量搜集线索、在平台内部搜索、核验候选结果 | `$unified-search` |
| 读取、下载并存档用户给出的 URL、URL 清单文件、已确认候选或边界明确的容器（X Post、Quote、Article 均在此列） | `$content-archive` |
| 把小红书、抖音或 X/Twitter 上的私人收藏与书签导出成链接 | `$bookmarks-export` |
| 对现有音视频做字幕提取、ASR 转写、口播粗剪或内容分析 | `$asr` |

## 固定流程

```text
研究目标
  -> unified-search
  -> 标准候选清单
  -> 用户确认或原请求已明确选择范围
  -> content-archive
  -> 按需交给 asr、视觉分析或知识库 Skill
```

检索完成后不允许顺手开始下载。收藏导出完成后同样不允许顺手读取正文或抓取媒体；凡是下载动作，都必须由用户在当轮单独、明确地提出。

## 各后端的分工

- AnySearch：负责公共网页、批量检索、垂直检索，以及对搜索候选做轻量的原文核对。
- Twitter/X：关键词检索走 `$unified-search`，固定以 Grok CLI 原生 `x_search` 为首选；已知 X 链接走 `$content-archive`，固定以匿名 FxTwitter → Jina 为首选。
- 平台原生 CLI/API：承担 GitHub、YouTube、B站等平台的结构化公开检索。
- OpenCLI：只充当部分平台的只读适配层，既不是本体系的必备依赖，也不是统一入口。
- 本地平台 Skill：承担已知链接解析、媒体抓取、公众号正文提取与批量存档。
- 浏览器或账号登录态：仅当匿名路线不够用、且目标平台规则许可时，才针对具体目标申请当轮授权。

任何后端已装好、或浏览器已处于登录状态，都不能成为跳过子 Skill 授权门的理由。

## 安全红线

1. 社交平台一律只读：不发布、不评论、不点赞、不收藏、不关注、不私信，账号状态不发生任何改变。
2. 微信桌面端与移动端的 UI 一律禁止操控；发消息、发布、编辑、建草稿、删除、群发、加关注均在禁止之列。
3. 用 Chrome 登录态做小红书、抖音搜索之前，必须先交代平台、原始关键词与预计条数，并得到用户当轮的明确许可。
4. 读取私人收藏、书签、Feed 或账号后台数据，必须先取得当轮针对具体平台与范围的明确许可；该许可不能顺延到下载环节。
5. 优先采用匿名公开路线。验证码、登录墙、付费墙、限流、地区限制及各类访问控制均不得绕过。
6. Cookie、Token、API Key、登录凭证与敏感 URL 参数，既不打印也不落盘。
7. 既有产物不覆盖，临时文件不自动清除。确需清理时须先征得用户明确同意，且只能移入废纸篓。
8. 调用付费 API、或进行可能明显消耗额度的批量转写之前，先交代范围与预估数量。
9. ASR 自动路由在任务提交后不得换服务商重复提交；余额情况不明时，既不能声称充足也不能声称不足。

## 后端体检

凡涉及跨平台或登录态的任务，动手前先执行：

```bash
python3 ~/.agents/skills/web-research/scripts/doctor.py
```

涉及 OpenCLI 的任务再补一条：

```bash
opencli doctor
```

体检结果只能说明后端与安全契约可以被识别，并不意味着登录态或私人数据读取已获授权。

## 层间交接

搜索层向下交接时至少包含：

```json
{
  "schema_version": "1.0",
  "request": {},
  "routes": [],
  "candidates": [],
  "coverage": [],
  "errors": []
}
```

归档层的输入仅限用户已知链接、已确认候选或边界明确的有限容器；收藏层的产出仅限链接文件与不可转移的授权状态。执行层面的事实以各子 Skill 当前的 `SKILL.md` 与 references 为准。

## 入口唯一性与子 Skill 的调用方式

- 互联网研究只设本 Skill 一个总入口，旧的名称不再提供兼容入口。
- 用户显式调用 `$web-research` 时，先对照上表判定任务所处阶段；一旦判定需要子 Skill，必须先把对应当前文件完整读完再动手：
  - `~/.agents/skills/unified-search/SKILL.md`
  - `~/.agents/skills/content-archive/SKILL.md`
  - `~/.agents/skills/bookmarks-export/SKILL.md`
  - `~/.agents/skills/asr/SKILL.md`
- 子 Skill 是各自独立的执行规则集，并非可递归调用的函数。路由完成后即按目标 Skill 的规则执行，目标 Skill 不允许再跳回本总入口。
- 遇到子 Skill、必需后端、登录态或额度不可用的情况，照实说明缺了什么；路由正确不等于外部平台一定成功，两者不得混为一谈。
