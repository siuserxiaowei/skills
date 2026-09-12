# Agent Architecture Reading Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current static AI Agent reading hub into a maintainable, extensible learning product for studying how to build good AI Agents.

**Architecture:** Keep GitHub Pages as a zero-backend static deployment. Split source data, taxonomy, learning paths, UI rendering, and utilities into focused files so future subagents can work without editing one giant `script.js`. Add schema validation and browser smoke checks so every content expansion is safe to publish.

**Tech Stack:** Static HTML/CSS/JavaScript, no runtime backend, no external client dependencies, GitHub Pages, GitHub Actions, Node.js validation scripts using built-in modules only.

## Global Constraints

- Public page must not republish full copyrighted articles; every source entry must use summaries, reading notes, focus points, and original links only.
- GitHub Pages URL remains `https://siuserxiaowei.github.io/hr-agent-reading-hub/` unless the repository is renamed in a separate confirmed task.
- The site must remain usable as plain static files from GitHub Pages root.
- No client-side build step is required for normal deployment.
- Keep visual style: white background, ink text, restrained teal and warm amber accents, 8px radius, no purple-dominant palette, no decorative gradient blobs.
- Mobile width `390px` must have no horizontal overflow.
- Search, category filtering, status filtering, source detail, learning route jump, and read-progress persistence must keep working.
- Use localStorage key `agentArchitectureReadSources` for the new reading state; read the legacy `hrAgentReadSources` key only as fallback.
- Every published source must have: `id`, `title`, `platform`, `category`, `url`, `status`, `priority`, `module`, `usefulFor`, `focus`, `note`.
- Every source URL included in the data set must return HTTP 200 or be explicitly marked as candidate/unverified outside the main `sources` array.

---

## File Structure

- `index.html`: Static shell, landmark regions, navigation, search input, containers only.
- `styles.css`: Design tokens, layout, responsive rules, component classes.
- `data/sources.js`: Main verified source catalog, exports `sources`.
- `data/taxonomy.js`: Categories, first-party platform rules, candidate source list, UI labels.
- `data/learning-paths.js`: Learning route modules and source references.
- `js/state.js`: localStorage read/write and app state helpers.
- `js/render.js`: Pure rendering functions for filters, metrics, cards, reader detail, learning paths, candidates.
- `js/app.js`: DOM bootstrapping, event wiring, page initialization.
- `tools/validate-sources.mjs`: Schema, duplicate-id, category, learning-path source reference, and HTTP URL validation.
- `tools/smoke-check.mjs`: Playwright-based smoke check when Playwright is available in the environment; otherwise prints a clear skip.
- `.github/workflows/pages.yml`: Pages deploy plus validation step before upload.
- `README.md`: Operator documentation and content boundary.

## Execution Strategy

Use worktrees for implementation isolation. First complete Task 1 because it creates module boundaries. After Task 1 is merged, Tasks 2, 3, and 4 can be delegated in parallel because their write sets are disjoint. Task 5 integrates and performs release verification.

## Task 1: Modularize Data And Rendering Foundation

**Files:**
- Create: `data/sources.js`
- Create: `data/taxonomy.js`
- Create: `data/learning-paths.js`
- Create: `js/state.js`
- Create: `js/render.js`
- Create: `js/app.js`
- Modify: `index.html`
- Modify: `script.js`

**Interfaces:**
- `data/sources.js` exports `sources`.
- `data/taxonomy.js` exports `categories`, `candidates`, `firstPartyPlatformNames`.
- `data/learning-paths.js` exports `learningPaths`.
- `js/state.js` exports `createInitialState()`, `saveReadState(state)`, `getSourceById(sources, id)`, `filterSources(sources, state)`.
- `js/render.js` exports `renderApp(context)`.
- `js/app.js` imports all modules and calls `renderApp`.

- [ ] **Step 1: Create module directories**

Run:

```bash
mkdir -p data js
```

Expected: directories exist.

- [ ] **Step 2: Move catalog data**

Move the `sources` array from `script.js` into `data/sources.js` and add:

```js
export const sources = [
  // existing source objects, unchanged
];
```

Expected: all 41 source objects remain byte-for-byte equivalent except for export syntax.

- [ ] **Step 3: Move taxonomy data**

Move `categories`, `candidates`, and first-party platform logic into `data/taxonomy.js`:

```js
export const categories = [
  "全部",
  "入门总览",
  "架构模式",
  "工具与上下文",
  "评估观测",
  "安全治理",
  "框架生态",
  "业务案例",
  "官方文档",
  "Agent 方法论",
  "招聘自动化",
  "飞书基础",
  "工作流案例",
];

export const firstPartyPlatformNames = [
  "OpenAI",
  "Anthropic",
  "Google",
  "Microsoft",
  "LangGraph",
  "LangChain",
  "MCP",
  "NIST",
  "OWASP",
];

export const candidates = [
  // existing candidate strings
];
```

- [ ] **Step 4: Move learning route data**

Move `courseModules` into `data/learning-paths.js` and rename to:

```js
export const learningPaths = [
  // existing route modules
];
```

- [ ] **Step 5: Extract state helpers**

Create `js/state.js` with these exact exports:

```js
export function createInitialState(sources) {
  return {
    category: "全部",
    status: "all",
    query: "",
    selectedId: sources[0]?.id || "",
    read: new Set(JSON.parse(localStorage.getItem("agentArchitectureReadSources") || localStorage.getItem("hrAgentReadSources") || "[]")),
  };
}

export function saveReadState(state) {
  localStorage.setItem("agentArchitectureReadSources", JSON.stringify([...state.read]));
}

export function getSourceById(sources, id) {
  return sources.find((source) => source.id === id);
}

export function filterSources(sources, state) {
  const query = state.query.trim().toLowerCase();
  return sources.filter((source) => {
    const inCategory = state.category === "全部" || source.category === state.category;
    const isRead = state.read.has(source.id);
    const inStatus = state.status === "all" || (state.status === "read" ? isRead : !isRead);
    const haystack = [
      source.title,
      source.platform,
      source.category,
      source.module,
      source.usefulFor,
      source.note,
      ...source.focus,
    ]
      .join(" ")
      .toLowerCase();
    return inCategory && inStatus && (!query || haystack.includes(query));
  });
}
```

- [ ] **Step 6: Extract render helpers**

Create `js/render.js` with `renderApp(context)`, where `context` includes:

```js
{
  sources,
  categories,
  candidates,
  learningPaths,
  firstPartyPlatformNames,
  state,
  elements,
  actions
}
```

Move existing render functions from `script.js` into `js/render.js`. They must call `actions.onCategoryChange`, `actions.onStatusChange`, `actions.onSearchChange`, `actions.onSelectSource`, `actions.onToggleRead`, and `actions.onJumpSource` rather than mutating DOM listeners inline outside the renderer.

- [ ] **Step 7: Create app entrypoint**

Create `js/app.js` that imports data/state/render modules, queries DOM elements, defines action callbacks, and calls `renderApp(context)`.

- [ ] **Step 8: Switch HTML script tag**

Replace:

```html
<script src="./script.js"></script>
```

With:

```html
<script type="module" src="./js/app.js"></script>
```

- [ ] **Step 9: Remove old implementation**

Delete `script.js` after all behavior is moved.

- [ ] **Step 10: Test**

Run:

```bash
python3 -m http.server 5174
```

In another shell, use Playwright or browser tooling to verify:

- `h1` text is `AI Agent 架构阅读台`.
- `.source-card` count is `41`.
- `#totalCount` text is `41`.
- Hero image loads.
- Searching `MCP` leaves at least `2` cards.
- Searching `HR` leaves at least `8` cards.
- Mobile viewport `390x900` has no horizontal overflow.

- [ ] **Step 11: Commit**

```bash
git add index.html data js
git rm script.js
git commit -m "Refactor reading hub into modules"
```

## Task 2: Add Source Validation And CI Gate

**Files:**
- Create: `package.json`
- Create: `tools/validate-sources.mjs`
- Create: `tools/smoke-check.mjs`
- Modify: `.github/workflows/pages.yml`
- Modify: `README.md`

**Interfaces:**
- `npm run validate:sources` runs schema and reference checks.
- `npm run check:links` validates source URL HTTP status.
- `npm run smoke` runs browser smoke checks when Playwright is available.
- Pages workflow must run `npm run validate:sources` before upload.

- [ ] **Step 1: Add package scripts**

Create `package.json`:

```json
{
  "name": "agent-architecture-reading-hub",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "validate:sources": "node tools/validate-sources.mjs",
    "check:links": "node tools/validate-sources.mjs --check-links",
    "smoke": "node tools/smoke-check.mjs"
  }
}
```

- [ ] **Step 2: Implement source validator**

Create `tools/validate-sources.mjs`. It must:

- Import `sources`, `categories`, `learningPaths`.
- Fail if any required source field is missing or empty.
- Fail if any source id is duplicated.
- Fail if any source category is not in `categories`.
- Fail if any source focus is not a non-empty array.
- Fail if any learning path references a missing source id.
- When `--check-links` is present, `fetch` every source URL with redirect support and fail unless status is `200`.

Expected success output:

```text
Validated 41 sources, 7 learning path modules.
```

- [ ] **Step 3: Implement smoke check**

Create `tools/smoke-check.mjs`. It must:

- Try to import Playwright.
- If Playwright is unavailable, print `Playwright unavailable; smoke check skipped.` and exit `0`.
- If available, start a static server on port `5175`, open `http://127.0.0.1:5175`, and verify title, card count, search behavior, hero image load, and mobile overflow.
- Always close browser and server.

- [ ] **Step 4: Update Pages workflow**

Modify `.github/workflows/pages.yml` to run:

```yaml
      - name: Validate sources
        run: npm run validate:sources
```

after checkout/configure and before upload.

- [ ] **Step 5: Update docs**

In `README.md`, add:

```markdown
## 验证

```bash
npm run validate:sources
npm run check:links
npm run smoke
```
```

- [ ] **Step 6: Test**

Run:

```bash
npm run validate:sources
npm run check:links
npm run smoke
```

Expected: validation passes; link check returns all HTTP 200; smoke either passes or clearly skips if Playwright is not installed.

- [ ] **Step 7: Commit**

```bash
git add package.json tools .github/workflows/pages.yml README.md
git commit -m "Add source validation and smoke checks"
```

## Task 3: Improve Reader UX And Learning Controls

**Files:**
- Modify: `index.html`
- Modify: `styles.css`
- Modify: `js/render.js`
- Modify: `js/app.js`
- Modify: `js/state.js`

**Interfaces:**
- Add sort modes: `推荐优先`, `分类`, `平台`.
- Add detail keyboard shortcut: `Esc` clears selected detail focus only on narrow screens.
- Add source count label next to `全部资料`.
- Add category group summary cards above source list.

- [ ] **Step 1: Add sort UI container**

In `index.html`, inside the `section-heading` for `#sources`, add:

```html
<label class="sort-box">
  <span>排序</span>
  <select id="sortSelect">
    <option value="priority">推荐优先</option>
    <option value="category">分类</option>
    <option value="platform">平台</option>
  </select>
</label>
```

- [ ] **Step 2: Extend state**

In `js/state.js`, add `sort: "priority"` to the state object and sort `filterSources()` output by:

- priority order: `先读`, `案例`, `参考`, `补基础`, `扩展`
- category alphabetical for `category`
- platform alphabetical for `platform`

- [ ] **Step 3: Wire sort action**

In `js/app.js`, query `#sortSelect` and add `onSortChange(value)` that updates `state.sort` and rerenders.

- [ ] **Step 4: Render source count and category summary**

In `js/render.js`, update heading area via existing DOM elements or add a new `#activeCount` span in `index.html`. Render `当前显示 N / 总计 41`. Add a `category-summary` section that shows counts for the top-level categories.

- [ ] **Step 5: Style controls**

In `styles.css`, add `.sort-box`, `.category-summary`, `.summary-card` using the existing white card, thin border, teal/amber visual language.

- [ ] **Step 6: Test**

Verify:

- Sorting by platform changes card order.
- Search still works after sorting.
- Category filter still works after sorting.
- Source detail still opens.
- Mobile has no horizontal overflow.

- [ ] **Step 7: Commit**

```bash
git add index.html styles.css js
git commit -m "Improve reader controls and source summaries"
```

## Task 4: Add Content Collections And Study Notes

**Files:**
- Create: `data/collections.js`
- Modify: `index.html`
- Modify: `styles.css`
- Modify: `js/render.js`
- Modify: `js/app.js`

**Interfaces:**
- `data/collections.js` exports `collections`.
- Each collection has `id`, `title`, `description`, `sourceIds`, `outcome`.
- UI renders collections between metrics and source list.

- [ ] **Step 1: Create collections data**

Create `data/collections.js`:

```js
export const collections = [
  {
    id: "agent-foundations",
    title: "先搞懂 Agent 到底是什么",
    description: "判断什么时候该做 Agent，以及 workflow 和 agent 的边界。",
    outcome: "能说清楚 Agent 与普通 AI 应用、RAG、自动化脚本的区别。",
    sourceIds: ["openai-practical-guide-agents", "anthropic-effective-agents", "twelve-factor-agents"],
  },
  {
    id: "tools-context",
    title: "工具与上下文工程",
    description: "学习工具设计、上下文选择、MCP 和长流程信息组织。",
    outcome: "能为一个业务 Agent 设计工具接口、上下文输入和外部资源连接方式。",
    sourceIds: ["anthropic-writing-tools", "anthropic-context-engineering", "mcp-intro", "mcp-spec"],
  },
  {
    id: "evals-observability",
    title: "评估、观测和回归测试",
    description: "学习 tracing、evals、debug 和持续改进。",
    outcome: "能给 Agent demo 加上最基本的质量门禁。",
    sourceIds: ["openai-tracing", "promptfoo-evals", "arize-phoenix"],
  },
  {
    id: "safety-governance",
    title: "安全治理与人工审核",
    description: "学习 guardrails、LLM Top 10、风险治理和高风险动作边界。",
    outcome: "能列出 Agent 的主要风险点，并设计拦截和人工确认机制。",
    sourceIds: ["openai-guardrails", "owasp-llm-top10", "nist-genai-profile"],
  },
  {
    id: "business-cases",
    title: "业务案例：从 HR 到飞书工作流",
    description: "用招聘、飞书多维表格、n8n、Dify 等案例理解 Agent 如何落地。",
    outcome: "能把一个业务流程拆成数据表、状态流、工具调用和人工审核点。",
    sourceIds: ["feishu-resume-template", "feishu-base-workflow", "n8n-recruitment-pipeline", "dify-resume-screening"],
  },
];
```

- [ ] **Step 2: Add collections container**

In `index.html`, insert after `.metrics-row`:

```html
<section id="collections" class="collections-section">
  <div class="section-heading">
    <div>
      <p class="section-kicker">精选合集</p>
      <h2>按学习目标打包阅读</h2>
    </div>
  </div>
  <div id="collectionCards" class="collection-grid"></div>
</section>
```

- [ ] **Step 3: Render collections**

In `js/app.js`, import `collections`, add `collectionCards` to `elements`.

In `js/render.js`, add `renderCollections()` and call it from `renderApp`. Each collection card must show title, description, outcome, source count, and buttons for each source. Clicking a source button must select that source and scroll to `#sources`.

- [ ] **Step 4: Style collections**

Add `.collection-grid`, `.collection-card`, `.collection-links` to `styles.css`.

- [ ] **Step 5: Test**

Verify collection buttons select the right source and source list still works.

- [ ] **Step 6: Commit**

```bash
git add data/collections.js index.html styles.css js
git commit -m "Add curated Agent study collections"
```

## Task 5: Release Integration And Verification

**Files:**
- Modify as needed based on final review.

**Interfaces:**
- Main branch receives only verified, reviewed worktree changes.

- [ ] **Step 1: Merge approved task branches**

For each approved worktree branch:

```bash
git checkout main
git merge --no-ff <branch-name>
```

- [ ] **Step 2: Run local checks**

```bash
npm run validate:sources
npm run check:links
npm run smoke
python3 -m http.server 5174
```

Browser checks:

- Desktop `1440x1000`: h1 text, 41 cards, hero image, collections, learning path, search, read toggle.
- Mobile `390x900`: no horizontal overflow, cards readable, filters usable.

- [ ] **Step 3: Push**

```bash
git push origin main
```

- [ ] **Step 4: Verify GitHub Pages**

Check:

```bash
gh run list --repo siuserxiaowei/hr-agent-reading-hub --workflow pages.yml --limit 1
curl -L -s -o /tmp/agent-hub-online.html -w "%{http_code}\n" https://siuserxiaowei.github.io/hr-agent-reading-hub/
```

Expected: latest run `completed success`, HTTP `200`, page contains `AI Agent 架构阅读台`.

- [ ] **Step 5: Final report**

Report:

- URL
- source count
- features added
- validation commands run
- any remaining backlog

## Parallel Worktree Assignment

After Task 1 is complete and merged:

- Worktree `agent-hub-validation`: Task 2, write set `package.json`, `tools/**`, `.github/workflows/pages.yml`, `README.md`.
- Worktree `agent-hub-reader-ux`: Task 3, write set `index.html`, `styles.css`, `js/render.js`, `js/app.js`, `js/state.js`.
- Worktree `agent-hub-collections`: Task 4, write set `data/collections.js`, `index.html`, `styles.css`, `js/render.js`, `js/app.js`.

If Task 3 and Task 4 both touch the same UI files, merge Task 3 first, then rebase Task 4 before review. Do not manually resolve by deleting either feature.

## Self-Review

- Spec coverage: current user request requires autonomous planning, worktree/subagent execution, and richer Agent learning coverage. This plan covers planning, isolation, parallelizable tasks, validation, deployment, and ongoing extensibility.
- Placeholder scan: no `TBD`, no `TODO`, no "implement later".
- Type consistency: `learningPaths`, `collections`, `sources`, `categories`, `state`, and render actions are named consistently across tasks.
