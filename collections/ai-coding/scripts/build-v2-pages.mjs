import { mkdir, writeFile } from "node:fs/promises";

const pages = [
  {
    slug: "research",
    file: "research.html",
    name: "研究档案",
    label: "Recommended",
    tagline: "白底、纸纹、细线索引，把工程纪律整理成一份可审阅的技术档案。",
    palette: ["#f7f7f0", "#151713", "#00d084", "#1596a8"],
  },
  {
    slug: "magazine",
    file: "magazine.html",
    name: "杂志长卷",
    label: "Editorial",
    tagline: "用大标题、非对称分栏和强节奏，把同一套知识读成一篇思想专题。",
    palette: ["#fffdf8", "#16110f", "#e83527", "#ffd43b"],
  },
  {
    slug: "blueprint",
    file: "blueprint.html",
    name: "蓝图控制台",
    label: "Systems",
    tagline: "深蓝工程图、坐标线、模块编号，像打开一张 AI 工程系统总图。",
    palette: ["#061b2e", "#d9f6ff", "#65e4ff", "#a8ff60"],
  },
];

const sections = [
  {
    id: "complexity",
    no: "01",
    kicker: "Foundation",
    title: "复杂度是软件工程的第一公敌",
    claim: "软件工程的主战场不是语法，而是人脑有限。好设计持续降低认知负载、变更放大和未知的未知。",
    keywords: ["cognitive load", "change amplification", "unknown unknowns", "deep modules"],
    moves: [
      ["复杂度三症状", "Ousterhout 把复杂度拆成认知负载、变更放大、未知的未知。第三项最危险，因为你甚至不知道边界在哪里。"],
      ["战略编程", "战术编程追求当下最快通过；战略编程愿意多花 10-20% 时间换结构复利。"],
      ["深模块", "界面简单、实现复杂才叫抽象。浅模块只是把同样复杂的东西又包了一层。"],
      ["设计两遍", "重要 design 至少做两版方案再选；如果一个东西难注释，通常是设计还没想清楚。"],
    ],
    line: "复杂度不是一次事故，而是无数小妥协复利出来的。战略编程是一种持续纪律。",
  },
  {
    id: "spec",
    no: "02",
    kicker: "Spec Engineering",
    title: "Spec 是强制 design 的工具",
    claim: "写 spec 不是为了文档好看，而是在代码还没产生沉没成本时，把设计做完。",
    keywords: ["spec forces design", "declarative state", "spec/status", "12-factor"],
    moves: [
      ["Joel 的要点", "用自然语言设计产品，只需要几分钟就能删除、重写、比较方案；等代码写出来再改，成本会变成几周。"],
      ["Kubernetes 范本", "声明式 desired state、spec/status 分离、conditions、opaque resourceVersion 和 lists-over-maps 是工业 API 的硬约束。"],
      ["12-Factor", "deploy 维度也需要 spec：配置进 env，服务视为 attached resources，日志作为 event streams，进程无状态。"],
      ["TigerStyle", "70 行函数、100 列、零依赖、命名按显著性递减，把“怎么写代码”变成可执行契约。"],
    ],
    line: "Spec 的价值是把延后的决策提前，把口头默契转成可审计的工程输入。",
  },
  {
    id: "code",
    no: "03",
    kicker: "Code Discipline",
    title: "代码纪律：让读赢，不让写赢",
    claim: "代码被读的次数远多于被写。所有多花时间写的纪律，最终都是为了让未来读者省时间。",
    keywords: ["assertions", "naming", "bounded loops", "memory lifetime"],
    moves: [
      ["Assertion", "TigerStyle 认为 assert 不是 debug 工具，而是 mental model 的契约。每个函数平均至少两条断言。"],
      ["正负空间", "既断言“这是真的”，也断言“这不可能”。边界穿越处最容易藏 bug。"],
      ["命名学", "不缩写、带单位、显著性递减，例如 latency_ms_max，让变量排序后自然对齐。"],
      ["控制流", "避免递归，循环必须可证有界，复合条件拆开，所有错误必须处理。"],
    ],
    line: "可读性不是审美偏好，而是系统长期演进的生存条件。",
  },
  {
    id: "testing",
    no: "04",
    kicker: "Testing",
    title: "测试是把未知映射到已知",
    claim: "测试不是证明正确，而是把你不知道的状态空间系统化地挖出来检视。",
    keywords: ["MC/DC", "fuzzing", "anomaly injection", "deterministic simulation"],
    moves: [
      ["SQLite", "155.8 KSLOC 核心对应 92,053 KSLOC 测试脚本，约 1:590。真正值得学的是多探针结构。"],
      ["覆盖率层级", "statement 最弱，branch 更强，MC/DC 要证明每个条件能独立影响结果。"],
      ["Anomaly", "OOM、I/O 错误、断电都可以被人为注入，让最差路径成为日常测试输入。"],
      ["Antithesis", "决定性模拟测试让事件顺序、网络延迟、崩溃都可重放；bug 出现后必须能复现。"],
    ],
    line: "你不能预见未知未知，但可以构造系统化探针逼它们现身。",
  },
  {
    id: "api",
    no: "05",
    kicker: "API Contract",
    title: "接口与契约的工业实践",
    claim: "分布式系统里，请求可能丢失、重复、乱序。好 API 用契约消除不确定性，而不是靠希望。",
    keywords: ["idempotency", "resourceVersion", "conditions", "jitter"],
    moves: [
      ["乐观并发", "Kubernetes 用 resourceVersion 做读改写一致性；客户端必须把它当不透明字符串。"],
      ["Conditions", "状态不应塞进单一 phase enum，而应拆成可叠加、可演化的条件数组。"],
      ["Idempotency-Key", "POST 这类副作用操作必须让客户端传唯一 key，服务端按 key 缓存结果。"],
      ["Backoff + jitter", "指数退避避免持续砸服务，jitter 避免所有客户端同时重试造成羊群效应。"],
    ],
    line: "幂等性把“做了没做”的不确定性，从用户心智中移到系统契约里。",
  },
  {
    id: "schema",
    no: "06",
    kicker: "Schema Evolution",
    title: "Schema 演进：时间维度的契约",
    claim: "改一张活表是在同时和昨天的写者、读者、数据与回滚路径谈判。",
    keywords: ["dual-write", "backfill", "Scientist", "level-based reconciliation"],
    moves: [
      ["Stripe 四阶段", "先 dual-write + backfill，再切 read path，再切 write path，最后删除旧数据。"],
      ["不同时改读写", "永远不要一次同时改读和写；每个 phase 都要能回退。"],
      ["Scientist", "dual-read 时同时跑新旧实现并比对差异，不一致就告警。"],
      ["Level-based", "Kubernetes controller 看最新 desired state 收敛，不依赖每个中间 edge 都被观察到。"],
    ],
    line: "在线迁移不是一次发布，而是一组可观测、可回退、可逐步收敛的状态机。",
  },
  {
    id: "agent",
    no: "07",
    kicker: "Agent Design",
    title: "AI Agent 设计：控制流的新维度",
    claim: "Workflow 的控制流由代码定，Agent 的下一步由 LLM 决定。复杂度每升一档都要有测量证明。",
    keywords: ["workflow vs agent", "augmented LLM", "evaluator-optimizer", "ACI"],
    moves: [
      ["复杂度梯度", "从 augmented LLM 到 prompt chaining、routing、parallelization、orchestrator-workers、evaluator-optimizer，再到 autonomous agent。"],
      ["Start simple", "Anthropic 的核心建议是从最简单可行方案开始，只在结果证明需要时增加复杂度。"],
      ["ACI", "给 agent 的 tool 就像给人的 UI。参数、边界、例子、重叠关系都要设计。"],
      ["Poka-yoke", "避免要求模型数行号、嵌套 JSON 转义或在一堆功能重叠的工具里猜。"],
    ],
    line: "Agent 不是魔法，是控制流、工具契约和环境反馈共同组成的新运行时。",
  },
  {
    id: "ai-coding",
    no: "08",
    kicker: "AI Coding Practice",
    title: "AI 编程实战：把 LLM 当成什么",
    claim: "不是把代码外包给 LLM，而是和它协作压缩你的意图。人写约束和签名，模型填实现，人保留判断权。",
    keywords: ["context engineering", "right altitude", "repo map", "human verification"],
    moves: [
      ["最小高信号集", "Context engineering 的目标是找到最小但足够高信号的 token 集，而不是把所有材料塞进去。"],
      ["即时检索", "保留路径、查询、链接，让 agent 用工具按需拉上下文，避免上下文腐烂。"],
      ["Right altitude", "System prompt 要足够具体能指导行为，又足够灵活让模型自己找路径。"],
      ["Aider repo map", "tree-sitter 抽取符号和签名，按相关度排序，给模型结构而非整仓实现。"],
    ],
    line: "LLM 放大的是已有专业能力；不能把“它真的能跑”这件事外包给机器。",
  },
  {
    id: "meta",
    no: "09",
    kicker: "Meta Principles",
    title: "横切的元原则",
    claim: "九个方向最后汇成同一件事：把靠记性、靠默契、靠聪明，换成靠系统、工具和契约。",
    keywords: ["explicitness", "constraints", "auditability", "reader first"],
    moves: [
      ["简单是练出来的", "简单不是第一稿，而是多轮约束、比较和删除后的结果。"],
      ["约束是创造的助产士", "硬限制不是束缚，而是迫使设计者发现更稳的结构。"],
      ["显式打败隐式", "可选/必填、Idempotency-Key、assert 正负空间，都在拒绝“你应该懂”。"],
      ["对模型可见", "AI 时代的工程纪律多了新维度：spec、tool 设计、context 工程都成为 agent runtime 的一部分。"],
    ],
    line: "大神和普通工程师的差距，不在于谁更聪明，而在于谁更不依赖聪明。",
  },
];

const sources = [
  ["Building Effective Agents", "Anthropic Engineering · 2024", "Workflow vs agent 分类法，模式梯度，ACI 概念，start simple 原则。", "https://www.anthropic.com/engineering/building-effective-agents"],
  ["Effective Context Engineering for AI Agents", "Anthropic Applied AI · 2025", "最小高信号 token 集、just-in-time retrieval、compaction、structured notes、sub-agents、right altitude。", "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"],
  ["TIGER_STYLE.md", "TigerBeetle", "NASA Power of Ten、assertion 密度、命名学、控制流硬规则、静态内存。", "https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md"],
  ["A Philosophy of Software Design", "John Ousterhout", "复杂度三症状、战术 vs 战略、深模块、design twice、注释即设计。", "https://web.stanford.edu/~ouster/cgi-bin/aposd.php"],
  ["Painless Functional Specifications", "Joel Spolsky", "Spec 强制设计、沟通只发生一次、排期前置、代码沉没成本。", "https://www.joelonsoftware.com/2000/10/02/painless-functional-specifications-part-1-why-bother/"],
  ["How SQLite Is Tested", "SQLite", "四套测试、MC/DC、anomaly testing、mutation testing、测试/代码 1:590。", "https://www.sqlite.org/testing.html"],
  ["Is Something Bugging You?", "Will Wilson · Antithesis", "决定性模拟测试、FoundationDB 经验、50x productivity 论点。", "https://antithesis.com/blog/is_something_bugging_you/"],
  ["The Twelve-Factor App", "Adam Wiggins", "SaaS app 的 12 条 deploy 契约：config、backing services、logs、process model。", "https://12factor.net/"],
  ["K8s API Conventions", "kubernetes/community", "声明式 API、spec/status、conditions、resourceVersion、lists over maps。", "https://github.com/kubernetes/community/blob/main/contributors/devel/sig-architecture/api-conventions.md"],
  ["Online Migrations at Scale", "Stripe Blog", "dual-write、backfill、dual-read、Scientist、增量切换写路径、删除旧数据。", "https://stripe.com/blog/online-migrations"],
  ["Designing Robust APIs with Idempotency", "Stripe Blog", "Idempotency-Key、指数退避、jitter、thundering herd 防护。", "https://stripe.com/blog/idempotency"],
  ["Using LLMs to Help Write Code", "Simon Willison", "LLM expectations、training cutoff、context is king、测试责任、专家能力放大。", "https://simonwillison.net/2025/Mar/11/using-llms-for-code/"],
  ["Building a Better Repository Map with Tree-Sitter", "Paul Gauthier · Aider", "tree-sitter、PageRank、repo map、结构性压缩优于截断。", "https://aider.chat/2023/10/22/repomap.html"],
  ["Software 2.0", "Andrej Karpathy", "数据集作为 source code，训练把目标函数编译成神经网络权重。", "https://karpathy.medium.com/software-2-0-a64152b37c35"],
  ["Push Ifs Up And Fors Down", "matklad · 2023", "把条件上推、循环下沉，集中分支并让批处理成为基础形态。", "https://matklad.github.io/2023/11/15/push-ifs-up-and-fors-down.html"],
  ["Simple Testing Can Prevent Most Critical Failures", "Yuan et al. · OSDI 2014", "198 个生产故障分析，92% 灾难性故障来自非致命错误处理不当。", "https://www.usenix.org/conference/osdi14/technical-sessions/presentation/yuan"],
];

const escapeHtml = (value) =>
  value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);

const cleanOutput = (value) => `${value
  .split("\n")
  .map((line) => line.trimEnd())
  .join("\n")
  .trimEnd()}\n`;

const navLinks = () => pages.map((page) => `<a href="${page.file}">${page.name}</a>`).join("");

const sectionToc = () => sections
  .map((section) => `<a href="#${section.id}"><b>${section.no}</b><span>${escapeHtml(section.title)}</span></a>`)
  .join("");

const sourceList = (variant = "default") => sources.map((source, index) => `
  <article class="source-item">
    <a href="${source[3]}" target="_blank" rel="noopener noreferrer">${String(index + 1).padStart(2, "0")} · ${escapeHtml(source[0])}</a>
    <span>${escapeHtml(source[1])}</span>
    <p>${escapeHtml(source[2])}</p>
  </article>`).join("");

const moveItems = (section, className = "move") => section.moves.map(([title, body], index) => `
  <article class="${className}">
    <span>${String(index + 1).padStart(2, "0")}</span>
    <h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(body)}</p>
  </article>`).join("");

const keywordRow = (section) => section.keywords.map((keyword) => `<span>${escapeHtml(keyword)}</span>`).join("");

const paletteDots = (page) => page.palette
  .map((_, index) => `<i class="swatch-${page.slug}-${index + 1}"></i>`)
  .join("");

const baseHead = (title) => `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="AI 时代的软件工程纪律知识框架：复杂度、spec、测试、接口契约、Agent 设计与 AI 编程实践。">
<title>${escapeHtml(title)}</title>
<link rel="stylesheet" href="assets/v2.css">
</head>`;

const pageChrome = (page, body) => `${baseHead(`AI 工程纪律 · ${page.name}`)}
<body class="${page.slug}-theme">
<a class="skip-link" href="#content">跳到正文</a>
<nav class="top-switch" aria-label="版本导航">
  <a class="brand-mark" href="index.html">AI 工程纪律</a>
  <div>${navLinks()}</div>
</nav>
${body}
</body>
</html>
`;

const researchPage = () => pageChrome(pages[0], `
<main id="content" class="research-sheet">
  <header class="research-cover">
    <p class="file-code">ARCHIVE / VERIFIED SOURCES / 2026-05-21</p>
    <h1>AI 时代的工程纪律</h1>
    <p class="abstract">一份给 AI 编程实践者的工程档案：把复杂度、spec、代码纪律、测试、契约、schema 演进、Agent 设计与上下文工程放到同一张可审阅的桌面上。</p>
    <div class="archive-stats" role="group" aria-label="页面统计">
      <span><b>09</b> directions</span>
      <span><b>01</b> meta layer</span>
      <span><b>16</b> verified sources</span>
    </div>
  </header>
  <aside class="archive-index" aria-label="目录">${sectionToc()}</aside>
  <section class="research-map" aria-label="框架地图">
    ${sections.map((section) => `<a href="#${section.id}"><span>${section.no}</span>${escapeHtml(section.kicker)}</a>`).join("")}
  </section>
  ${sections.map((section) => `
  <section class="record" id="${section.id}">
    <div class="record-number">${section.no}</div>
    <div class="record-body">
      <p class="record-kicker">${escapeHtml(section.kicker)}</p>
      <h2>${escapeHtml(section.title)}</h2>
      <p class="record-claim">${escapeHtml(section.claim)}</p>
      <div class="keyword-strip">${keywordRow(section)}</div>
      <div class="finding-grid">${moveItems(section, "finding")}</div>
      <p class="evidence-line">${escapeHtml(section.line)}</p>
    </div>
  </section>`).join("")}
  <section class="source-ledger" id="sources">
    <p class="ledger-stamp">已核对来源 · 16 / 16</p>
    <h2>来源参考</h2>
    <div class="source-grid">${sourceList("research")}</div>
  </section>
</main>`);

const magazinePage = () => pageChrome(pages[1], `
<main id="content" class="magazine-issue">
  <header class="magazine-cover">
    <div class="issue-meta">Issue 02 · Engineering Culture · 16 Sources</div>
    <h1><span>工程</span><span>纪律</span></h1>
    <p>当 LLM 开始参与写代码，真正变贵的不是生成速度，而是结构、契约、验证与上下文的缺失。</p>
    <a class="cover-link" href="#chapters">Read the issue</a>
  </header>
  <nav class="magazine-contents" id="chapters" aria-label="目录">${sectionToc()}</nav>
  ${sections.map((section, index) => `
  <section class="feature-spread ${index % 2 ? "feature-reverse" : ""}" id="${section.id}">
    <div class="spread-marker">
      <span>${section.no}</span>
      <p>${escapeHtml(section.kicker)}</p>
    </div>
    <article>
      <h2>${escapeHtml(section.title)}</h2>
      <p class="standfirst">${escapeHtml(section.claim)}</p>
      <div class="magazine-rule">${keywordRow(section)}</div>
      <div class="chapter-list">${moveItems(section, "chapter-note")}</div>
      <blockquote>${escapeHtml(section.line)}</blockquote>
    </article>
  </section>`).join("")}
  <section class="magazine-sources" id="sources">
    <div>
      <p>Bibliography</p>
      <h2>16 个已核对来源</h2>
    </div>
    <div class="source-grid">${sourceList("magazine")}</div>
  </section>
</main>`);

const blueprintPage = () => pageChrome(pages[2], `
<main id="content" class="blueprint-board">
  <header class="blueprint-hero">
    <p class="coordinate">SYS-DISCIPLINE / CONTROL SURFACE / REV 2</p>
    <h1>AI 工程纪律总图</h1>
    <p>把工程判断拆成九个可巡检模块：从复杂度源头到 Agent runtime，每个模块都要有输入、约束、验证和可追踪来源。</p>
    <div class="blueprint-panel">
      <span>Directions 09</span>
      <span>Sources 16</span>
      <span>Status verified</span>
    </div>
  </header>
  <nav class="blueprint-nav" aria-label="目录">${sectionToc()}</nav>
  <section class="module-grid" aria-label="模块总览">
    ${sections.map((section) => `<a href="#${section.id}"><b>${section.no}</b><span>${escapeHtml(section.title)}</span></a>`).join("")}
  </section>
  ${sections.map((section) => `
  <section class="blueprint-module" id="${section.id}">
    <header>
      <span>${section.no}</span>
      <p>${escapeHtml(section.kicker)}</p>
      <h2>${escapeHtml(section.title)}</h2>
    </header>
    <p class="module-claim">${escapeHtml(section.claim)}</p>
    <div class="module-keywords">${keywordRow(section)}</div>
    <div class="module-flow">${moveItems(section, "flow-node")}</div>
    <p class="module-output">${escapeHtml(section.line)}</p>
  </section>`).join("")}
  <section class="blueprint-sources" id="sources">
    <p class="coordinate">REFERENCE BUS / VERIFIED 16</p>
    <h2>来源参考</h2>
    <div class="source-grid">${sourceList("blueprint")}</div>
  </section>
</main>`);

const indexPage = () => `${baseHead("AI 工程纪律 · 版本选择")}
<body class="home-theme">
<main class="version-home" id="content">
  <header class="version-hero">
    <p>AI Engineering Discipline · Visual Editions</p>
    <h1>选择一套阅读界面</h1>
    <p class="home-lede">同一份已核对的 AI 工程纪律知识框架，三种完全不同的视觉表达。默认从研究档案开始。</p>
  </header>
  <section class="version-gallery" aria-label="版本选择">
    ${pages.map((page, index) => `
    <a class="version-card version-${page.slug}" href="${page.file}">
      <span>${page.label}</span>
      <h2>${page.name}</h2>
      <p>${page.tagline}</p>
      <div class="palette" aria-hidden="true">${paletteDots(page)}</div>
      <b>进入版本 ${String(index + 1).padStart(2, "0")}</b>
    </a>`).join("")}
  </section>
  <section class="home-source-note">
    <span>16 个来源已补齐并链接</span>
    <span>不含追踪脚本</span>
    <span>纯静态 GitHub Pages</span>
  </section>
  <details class="home-sources">
    <summary>查看 16 个已核对来源</summary>
    <div class="source-grid compact-source-grid">${sourceList("home")}</div>
  </details>
</main>
</body>
</html>
`;

const css = `
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-width:320px}a{color:inherit}p,h1,h2,h3{margin:0}.skip-link{position:absolute;left:16px;top:-80px;z-index:10;background:#000;color:#fff;padding:10px 14px}.skip-link:focus{top:16px}.top-switch{position:sticky;top:0;z-index:8;display:flex;justify-content:space-between;gap:18px;align-items:center;padding:14px clamp(18px,4vw,56px);border-bottom:1px solid currentColor;backdrop-filter:blur(16px)}.top-switch div{display:flex;gap:10px;flex-wrap:wrap}.top-switch a{text-decoration:none}.brand-mark{font-weight:800;letter-spacing:.08em}.top-switch div a{font-size:13px;padding:7px 10px;border:1px solid currentColor}

.home-theme{font-family:"Avenir Next","Trebuchet MS",sans-serif;background:#101010;color:#f6f2e8}.version-home{min-height:100vh;padding:clamp(28px,5vw,76px);background:linear-gradient(120deg,rgba(0,208,132,.18),transparent 35%),linear-gradient(300deg,rgba(232,53,39,.24),transparent 42%),#101010}.version-hero{max-width:1120px}.version-hero>p:first-child{text-transform:uppercase;letter-spacing:.18em;color:#8df7d0;font-size:12px}.version-hero h1{font-family:Baskerville,Georgia,serif;font-size:104px;line-height:.88;margin:22px 0}.home-lede{max-width:660px;font-size:22px;line-height:1.45;color:#d6d0c5}.version-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin-top:56px}.version-card{min-height:360px;display:flex;flex-direction:column;justify-content:space-between;padding:26px;text-decoration:none;border:1px solid rgba(255,255,255,.28);transition:transform .18s ease,filter .18s ease}.version-card:hover{transform:translateY(-6px);filter:saturate(1.2)}.version-card span{text-transform:uppercase;letter-spacing:.16em;font-size:11px}.version-card h2{font-size:52px;line-height:.94}.version-card p{line-height:1.65;max-width:30ch}.palette{display:flex;gap:8px}.palette i{width:26px;height:26px;border-radius:50%;border:1px solid rgba(0,0,0,.2)}.swatch-research-1{background:#f7f7f0}.swatch-research-2{background:#151713}.swatch-research-3{background:#00d084}.swatch-research-4{background:#1596a8}.swatch-magazine-1{background:#fffdf8}.swatch-magazine-2{background:#16110f}.swatch-magazine-3{background:#e83527}.swatch-magazine-4{background:#ffd43b}.swatch-blueprint-1{background:#061b2e}.swatch-blueprint-2{background:#d9f6ff}.swatch-blueprint-3{background:#65e4ff}.swatch-blueprint-4{background:#a8ff60}.version-card b{font-size:13px;letter-spacing:.08em}.version-research{background:#f7f7f0;color:#151713}.version-magazine{background:#fffdf8;color:#16110f;border-left:10px solid #e83527}.version-blueprint{background:#061b2e;color:#d9f6ff;background-image:linear-gradient(rgba(101,228,255,.16) 1px,transparent 1px),linear-gradient(90deg,rgba(101,228,255,.16) 1px,transparent 1px);background-size:28px 28px}.home-source-note{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.home-source-note span{border:1px solid rgba(255,255,255,.28);padding:8px 12px;color:#d7d2c9}.home-sources{margin-top:28px;border:1px solid rgba(255,255,255,.26);padding:18px}.home-sources summary{cursor:pointer;text-transform:uppercase;letter-spacing:.12em;font-weight:800}.compact-source-grid{margin-top:18px}.home-sources .source-item{border-color:rgba(255,255,255,.22);background:rgba(255,255,255,.04)}

.research-theme{font-family:"Avenir Next","Gill Sans",sans-serif;background:#f4f4ed;color:#151713}.research-theme .top-switch{background:rgba(244,244,237,.86)}.research-sheet{max-width:1280px;margin:auto;padding:0 clamp(18px,4vw,56px) 80px;background-image:linear-gradient(rgba(0,0,0,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.035) 1px,transparent 1px);background-size:24px 24px}.research-cover{padding:78px 0 46px;border-bottom:3px solid #151713}.file-code,.record-kicker,.ledger-stamp{text-transform:uppercase;letter-spacing:.18em;font-size:12px;color:#1596a8}.research-cover h1{font-family:"Iowan Old Style",Georgia,serif;font-size:96px;line-height:.92;letter-spacing:-.04em;margin:20px 0}.abstract{max-width:780px;font-size:23px;line-height:1.5}.archive-stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:34px}.archive-stats span{border:1px solid #151713;background:#f9fff2;padding:10px 14px}.archive-stats b{color:#00a96b}.archive-index{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;margin:26px 0;background:#151713;border:1px solid #151713}.archive-index a{background:#f4f4ed;min-height:74px;padding:12px;text-decoration:none}.archive-index b{display:block;color:#00a96b}.archive-index span{font-size:14px}.research-map{display:grid;grid-template-columns:repeat(9,1fr);gap:8px;margin:34px 0 12px}.research-map a{text-decoration:none;border-top:2px solid #151713;padding-top:10px;font-size:12px;color:#40443d}.research-map span{display:block;color:#00a96b;font-weight:800}.record{display:grid;grid-template-columns:120px 1fr;gap:34px;padding:54px 0;border-bottom:1px solid rgba(21,23,19,.24)}.record-number{font-family:Georgia,serif;font-size:72px;color:#00a96b;line-height:1}.record h2{font-family:"Iowan Old Style",Georgia,serif;font-size:56px;line-height:1;margin:8px 0 18px}.record-claim{font-size:22px;line-height:1.45;max-width:920px}.keyword-strip,.module-keywords,.magazine-rule{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.keyword-strip span,.module-keywords span,.magazine-rule span{border:1px solid currentColor;padding:5px 8px;font-size:12px}.finding-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:26px}.finding{border-left:2px solid #00d084;padding:0 12px 0 14px}.finding span{font-family:Menlo,monospace;color:#1596a8;font-size:12px}.finding h3{font-size:18px;margin:8px 0}.finding p{line-height:1.6;color:#3f443d}.evidence-line{margin-top:28px;padding:18px 20px;border:1px solid #151713;background:#effff8;font-weight:700;line-height:1.6}.source-ledger{padding:70px 0}.source-ledger h2{font-family:Georgia,serif;font-size:54px;margin:8px 0 26px}.source-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.source-item{border:1px solid currentColor;padding:16px;min-height:170px}.source-item a{font-weight:800;text-decoration:none}.source-item span{display:block;margin:10px 0;color:inherit;opacity:.7;font-size:12px}.source-item p{line-height:1.55;font-size:13px;opacity:.86}

.magazine-theme{font-family:"Avenir Next","Gill Sans",sans-serif;background:#fffdf8;color:#16110f}.magazine-theme .top-switch{background:rgba(255,253,248,.86)}.magazine-issue{overflow:hidden}.magazine-cover{min-height:92vh;padding:8vw 6vw 5vw;display:grid;grid-template-columns:1.1fr .9fr;align-items:end;gap:24px;border-bottom:18px solid #16110f;background:radial-gradient(circle at 86% 18%,#ffd43b 0 12%,transparent 13%),linear-gradient(90deg,transparent 0 62%,rgba(232,53,39,.12) 62%)}.issue-meta{grid-column:1/-1;text-transform:uppercase;letter-spacing:.18em;font-weight:800}.magazine-cover h1{font-family:Didot,Bodoni 72,Georgia,serif;font-size:176px;line-height:.75;letter-spacing:-.08em}.magazine-cover h1 span{display:block}.magazine-cover p:not(.issue-meta){font-size:30px;line-height:1.25;max-width:520px}.cover-link{justify-self:start;text-decoration:none;background:#e83527;color:#fffdf8;padding:15px 20px;text-transform:uppercase;letter-spacing:.12em;font-weight:800}.magazine-contents{display:grid;grid-template-columns:repeat(2,1fr);gap:0;border-bottom:1px solid #16110f}.magazine-contents a{display:grid;grid-template-columns:60px 1fr;text-decoration:none;padding:18px 6vw;border-top:1px solid #16110f}.feature-spread{display:grid;grid-template-columns:minmax(160px,24vw) 1fr;gap:clamp(24px,5vw,76px);padding:84px 6vw;border-bottom:1px solid #16110f}.feature-reverse{grid-template-columns:1fr minmax(160px,24vw)}.feature-reverse .spread-marker{order:2}.spread-marker{border-top:10px solid #e83527;padding-top:16px}.spread-marker span{font-family:Didot,Georgia,serif;font-size:88px;line-height:.8}.spread-marker p{text-transform:uppercase;letter-spacing:.16em;font-size:12px;margin-top:18px}.feature-spread h2{font-family:Didot,Bodoni 72,Georgia,serif;font-size:84px;line-height:.88;letter-spacing:-.05em}.standfirst{font-size:26px;line-height:1.38;max-width:900px;margin-top:24px}.chapter-list{display:grid;grid-template-columns:repeat(2,1fr);gap:24px;margin-top:36px}.chapter-note{border-top:2px solid #16110f;padding-top:14px}.chapter-note span{color:#e83527;font-weight:900}.chapter-note h3{font-size:23px;margin:10px 0}.chapter-note p{line-height:1.65}.feature-spread blockquote{margin:40px 0 0;padding:24px 0;border-top:1px solid #e83527;border-bottom:1px solid #e83527;font-family:Georgia,serif;font-size:23px;line-height:1.45}.magazine-sources{display:grid;grid-template-columns:280px 1fr;gap:34px;padding:84px 6vw;background:#16110f;color:#fffdf8}.magazine-sources h2{font-family:Didot,Georgia,serif;font-size:54px}.magazine-sources .source-item{border-color:rgba(255,253,248,.34)}

.blueprint-theme{font-family:"Avenir Next","DIN Alternate","Gill Sans",sans-serif;background:#061b2e;color:#d9f6ff}.blueprint-theme .top-switch{background:rgba(6,27,46,.82);color:#d9f6ff}.blueprint-board{background-image:linear-gradient(rgba(101,228,255,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(101,228,255,.12) 1px,transparent 1px),linear-gradient(rgba(101,228,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(101,228,255,.06) 1px,transparent 1px);background-size:48px 48px,48px 48px,12px 12px,12px 12px;min-height:100vh;padding-bottom:80px}.blueprint-hero{padding:86px 5vw 44px}.coordinate{font-family:Menlo,monospace;color:#a8ff60;text-transform:uppercase;letter-spacing:.14em;font-size:12px}.blueprint-hero h1{font-family:"DIN Condensed","Avenir Next Condensed",Impact,sans-serif;font-size:132px;line-height:.85;text-transform:uppercase;letter-spacing:.02em;margin:22px 0}.blueprint-hero>p:not(.coordinate){max-width:760px;font-size:22px;line-height:1.5;color:#b6e5f2}.blueprint-panel{display:flex;flex-wrap:wrap;gap:0;margin-top:32px;max-width:760px}.blueprint-panel span{border:1px solid #65e4ff;padding:14px 18px;color:#a8ff60}.blueprint-nav{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;margin:0 5vw 36px;background:#65e4ff;border:1px solid #65e4ff}.blueprint-nav a{background:#061b2e;padding:14px;text-decoration:none;min-height:78px}.blueprint-nav b{color:#a8ff60;display:block}.module-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 5vw 60px}.module-grid a{text-decoration:none;border:1px solid rgba(101,228,255,.6);padding:20px;min-height:120px;background:rgba(6,27,46,.72)}.module-grid b{display:block;color:#a8ff60;font-size:28px}.blueprint-module{margin:0 5vw 28px;border:1px solid rgba(101,228,255,.72);background:rgba(3,17,31,.76);padding:28px;position:relative}.blueprint-module:before{content:"";position:absolute;inset:10px;border:1px dashed rgba(101,228,255,.26);pointer-events:none}.blueprint-module header{display:grid;grid-template-columns:88px 160px 1fr;gap:18px;align-items:end}.blueprint-module header span{font-family:Menlo,monospace;font-size:52px;color:#a8ff60}.blueprint-module header p{text-transform:uppercase;letter-spacing:.16em;color:#65e4ff;font-size:12px}.blueprint-module h2{font-size:52px;line-height:1}.module-claim{max-width:920px;font-size:21px;line-height:1.5;margin:24px 0;color:#d9f6ff}.module-keywords span{color:#a8ff60}.module-flow{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}.flow-node{border:1px solid rgba(101,228,255,.46);padding:16px;background:rgba(101,228,255,.06)}.flow-node span{color:#a8ff60;font-family:Menlo,monospace}.flow-node h3{margin:10px 0;font-size:18px}.flow-node p{line-height:1.55;color:#b6e5f2}.module-output{margin-top:22px;border-left:4px solid #a8ff60;padding:14px 18px;background:rgba(168,255,96,.08);font-weight:800}.blueprint-sources{margin:70px 5vw 0}.blueprint-sources h2{font-size:62px;margin:10px 0 24px}.blueprint-sources .source-item{background:rgba(6,27,46,.78);border-color:rgba(101,228,255,.5)}

@media (max-width:980px){.version-gallery,.source-grid,.finding-grid,.chapter-list,.module-flow,.module-grid{grid-template-columns:1fr 1fr}.archive-index,.blueprint-nav{grid-template-columns:1fr 1fr}.research-map{grid-template-columns:repeat(3,1fr)}.magazine-cover,.feature-spread,.feature-reverse,.magazine-sources{grid-template-columns:1fr}.feature-reverse .spread-marker{order:0}.blueprint-module header{grid-template-columns:1fr}.record{grid-template-columns:1fr;gap:12px}.record-number{font-size:44px}}@media (max-width:640px){.top-switch{position:static;align-items:flex-start;flex-direction:column}.version-gallery,.source-grid,.finding-grid,.chapter-list,.module-flow,.module-grid,.archive-index,.blueprint-nav,.research-map,.magazine-contents{grid-template-columns:1fr}.version-home{padding:22px}.version-card{min-height:300px}.research-cover{padding-top:48px}.record{padding:40px 0}.magazine-cover{min-height:auto;padding:56px 22px}.feature-spread{padding:54px 22px}.magazine-sources{padding:56px 22px}.blueprint-hero{padding:56px 22px 32px}.blueprint-nav,.module-grid,.blueprint-module,.blueprint-sources{margin-left:22px;margin-right:22px}.blueprint-module{padding:20px}.archive-stats,.blueprint-panel{display:grid}.research-cover h1,.magazine-cover h1,.blueprint-hero h1{overflow-wrap:anywhere}}
@media (max-width:980px){.version-hero h1{font-size:78px}.version-card h2{font-size:42px}.research-cover h1{font-size:74px}.abstract,.record-claim{font-size:21px}.record h2{font-size:44px}.magazine-cover h1{font-size:126px}.magazine-cover p:not(.issue-meta){font-size:26px}.feature-spread h2{font-size:62px}.standfirst{font-size:23px}.blueprint-hero h1{font-size:90px}.blueprint-module h2{font-size:42px}}@media (max-width:640px){.version-hero h1{font-size:54px}.home-lede{font-size:18px}.version-card h2{font-size:38px}.research-cover h1{font-size:50px}.abstract,.record-claim{font-size:18px}.record h2{font-size:34px}.magazine-cover h1{font-size:86px}.magazine-cover p:not(.issue-meta){font-size:22px}.feature-spread h2{font-size:44px}.standfirst{font-size:20px}.blueprint-hero h1{font-size:54px}.blueprint-hero>p:not(.coordinate){font-size:18px}.blueprint-module h2{font-size:32px}.module-claim{font-size:18px}.source-ledger h2,.magazine-sources h2,.blueprint-sources h2{font-size:40px}}
`;

await mkdir("assets", { recursive: true });
await writeFile("assets/v2.css", cleanOutput(css));
await writeFile("index.html", cleanOutput(indexPage()));
await writeFile("research.html", cleanOutput(researchPage()));
await writeFile("magazine.html", cleanOutput(magazinePage()));
await writeFile("blueprint.html", cleanOutput(blueprintPage()));
