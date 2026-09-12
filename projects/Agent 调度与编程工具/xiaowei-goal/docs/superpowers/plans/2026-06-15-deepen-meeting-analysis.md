# Deepen Meeting Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the three existing online meeting-analysis pages from summary-level interpretation to detailed, source-backed, Xiaowei-style research briefs with independent pages and verifiable publication.

**Architecture:** Keep the existing GitHub Pages structure. Each meeting remains one Markdown source and one generated HTML page under `docs/`; `docs/index.html` remains the entry page. Work happens only inside the isolated worktree at `.worktrees/deepen-meeting-analysis`, then is merged or pushed after validation.

**Tech Stack:** Markdown, pandoc standalone HTML, GitHub Pages from `docs/`, shell verification, `xiaowei-goal` three-stage research workflow.

---

## Scope

This plan deepens three already-published pages:

- `docs/ai-product-application-transformation-20260510.md`
- `docs/ai-product-development-acquisition-20260510.md`
- `docs/ai-education-product-planning-20260510.md`

For each page, add enough detail to satisfy:

- Full-context understanding of the meeting notes, without publishing private raw transcript text.
- External research supplements with URLs and source-type labeling.
- Deep Research evidence table with facts, inference, confidence, and action.
- More granular "逐句级/信息点级" interpretation.
- Stronger "道法术器势" breakdown.
- Clear business application, next `/goal`, risks, and evidence gaps.

## 50-Round Review Protocol

Only these summaries are published; hidden reasoning is not written out.

| Round | Stage Summary | Evidence Gaps | Risk | Next Decision |
|---|---|---|---|---|
| 10 | Goal is to deepen three independent HTML reports, not merge them. Boundaries: no private transcript publishing, no paid/login-only sources, no legal conclusion beyond risk framing. Success means each page stands alone with research, Deep Research, business actions, and 道法术器势. | Original Feishu links remain private and should not be exposed. Some platform rules may require logged-in merchant access. | Over-sharing private meeting content; overstating unverified market claims. | Use public summaries and paraphrased meeting points; cite public sources only. |
| 20 | External evidence must cover SEO/AI search, agent/MCP, app-store acquisition, education digitalization, game-based learning, AI safety/compliance, copyright, and platform/channel risk. | Xiaohongshu merchant rules for virtual goods may be inaccessible without account. Product sales numbers from meeting are not externally verified. | Weak evidence hidden as certainty. | Mark inaccessible or unverified points explicitly as "needs verification". |
| 30 | Implementation path: one worker subagent per report, disjoint file ownership; controller integrates style, generates HTML, validates links. | Subagents may not have Feishu context unless provided carefully. | File conflicts or uneven content depth. | Provide each worker exact source points, file path, and required output contract. |
| 40 | Validation requires local diff review, HTML generation, grep checks for section presence, curl checks after publish, and final risk review. | Browser visual screenshot is optional because static HTML can be verified by file and URL checks. | Broken links, stale index page, missing source tables. | Build local files with pandoc; verify titles, links, section headings, and HTTP 200 after push. |
| 50 | Deliverables: three deeper online pages, implementation plan, handoff notes, commit SHA, verification evidence. | Further improvement would need raw transcript export, platform backend screenshots, or user-approved deeper market research. | Scope creep into product strategy or legal advice. | Finish this iteration, publish, then create next-stage `/goal` for deeper market validation. |

## Task 1: Deepen AI Product Application & Transformation Report

**Files:**
- Modify: `docs/ai-product-application-transformation-20260510.md`
- Generate: `docs/ai-product-application-transformation-20260510.html`

- [ ] **Step 1: Expand source-backed structure**

Add these sections to the Markdown file:

```markdown
## 信息密度升级说明
## 来源池与取舍
## Deep Research 证据表
## 关键判断分层：事实 / 推断 / 假设
## 业务落地路线图：7 天 / 30 天 / 90 天
## 风险清单与验证动作
```

- [ ] **Step 2: Deepen the meeting-point interpretation**

Expand the existing interpretation table so each row includes:

```markdown
| 纪要信息点 | 字面意思 | 深层含义 | 业务动作 | 证据状态 |
```

- [ ] **Step 3: Generate HTML**

Run:

```bash
pandoc docs/ai-product-application-transformation-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-product-application-transformation-20260510.html
```

Expected: command exits 0; warnings about zh-CN translation are acceptable.

## Task 2: Deepen AI Product Development & Acquisition Report

**Files:**
- Modify: `docs/ai-product-development-acquisition-20260510.md`
- Generate: `docs/ai-product-development-acquisition-20260510.html`

- [ ] **Step 1: Add acquisition-specific evidence**

Add more concrete sections:

```markdown
## 需求雷达：如何从用户原话找到产品
## 获客路径拆解：SEO / GEO / 平台内容 / App Store / KOL
## 内容矩阵的边界：什么能规模化，什么不能规模化
## 知识产品化路线：资料库 → Agent → 网站/小程序 → 订阅
```

- [ ] **Step 2: Strengthen fact/inference/action separation**

Every major claim must map to one of:

```markdown
事实：来自会议纪要或外部来源。
推断：基于事实对小伟业务的判断。
动作：可以执行、可验证的下一步。
```

- [ ] **Step 3: Generate HTML**

Run:

```bash
pandoc docs/ai-product-development-acquisition-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-product-development-acquisition-20260510.html
```

Expected: command exits 0; warnings about zh-CN translation are acceptable.

## Task 3: Deepen AI Education Product Planning Report

**Files:**
- Modify: `docs/ai-education-product-planning-20260510.md`
- Generate: `docs/ai-education-product-planning-20260510.html`

- [ ] **Step 1: Add education-product decision depth**

Add concrete sections:

```markdown
## K12 老师采用成本拆解
## 游戏化不是装饰：课堂行为目标映射
## 平台依赖与自有资产迁移
## 国内优先与海外暂缓的判断依据
## 合规、隐私、未成年人和 AI 内容边界
```

- [ ] **Step 2: Strengthen product roadmap**

Add a roadmap table:

```markdown
| 阶段 | 目标 | 功能 | 增长动作 | 风险控制 | 验收指标 |
```

- [ ] **Step 3: Generate HTML**

Run:

```bash
pandoc docs/ai-education-product-planning-20260510.md --standalone --toc --metadata lang=zh-CN --include-in-header=docs/meeting-report-style.html -o docs/ai-education-product-planning-20260510.html
```

Expected: command exits 0; warnings about zh-CN translation are acceptable.

## Task 4: Index, Validation, and Handoff

**Files:**
- Modify if needed: `docs/index.html`
- Create: `docs/meeting-analysis-handoff-20260615.md`

- [ ] **Step 1: Verify index links**

Run:

```bash
rg -n "ai-product-application|ai-product-development|ai-education-product" docs/index.html
```

Expected: three report links are present.

- [ ] **Step 2: Verify each page has required sections**

Run:

```bash
rg -n "Deep Research|道法术器势|下一步|风险|资料链接" docs/ai-product-application-transformation-20260510.md docs/ai-product-development-acquisition-20260510.md docs/ai-education-product-planning-20260510.md
```

Expected: all three files contain the required sections.

- [ ] **Step 3: Create handoff**

Write `docs/meeting-analysis-handoff-20260615.md` with:

```markdown
# 会议纪要深度拆解交接

## 本轮计划
## 执行记录
## 产物路径
## 验证证据
## 风险
## 明早小伟最该看的三件事
```

- [ ] **Step 4: Commit and publish**

Run:

```bash
git status --short
git diff --check
git add docs/
git commit -m "docs: deepen meeting analysis pages"
git push origin docs/deepen-meeting-analysis:main
```

Expected: push succeeds and GitHub Pages updates.

- [ ] **Step 5: Verify online links**

Run:

```bash
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://siuserxiaowei.github.io/xiaowei-goal/ai-product-application-transformation-20260510.html
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://siuserxiaowei.github.io/xiaowei-goal/ai-product-development-acquisition-20260510.html
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://siuserxiaowei.github.io/xiaowei-goal/ai-education-product-planning-20260510.html
```

Expected: all return `200`.
