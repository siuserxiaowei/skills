const PI_SHA = "8fa7eebd235355522c8104166b4f1f959b4e2f10";
const DSH_SHA = "b150a551b8d465e31e418e1b2eaf5e79bbb7d28e";
const pi = (path, lines = "") => `https://github.com/earendil-works/pi/blob/${PI_SHA}/${path}${lines}`;
const dsh = (path, lines = "") => `https://github.com/deepseek-ai/deepseek-harness/blob/${DSH_SHA}/${path}${lines}`;

const chapters = [
  {
    tag: "地图", title: "先分清你正在学哪个 Pi",
    questions: ["Pi 是 Coding Agent、SDK，还是 Agent Harness？", "pi-ai、pi-agent-core、pi-coding-agent、pi-tui 的依赖方向是什么？", "旧名 badlogic/pi-mono 与当前 earendil-works/pi 是什么关系？"],
    copy: `<p>Pi 是一个 monorepo，也是一组可分拆使用的层。<b>pi-ai</b> 统一模型供应商；<b>pi-agent-core</b> 提供低层 Loop 与当前 AgentHarness；<b>pi-coding-agent</b> 把它们组装成终端产品；<b>pi-tui</b> 提供终端 UI primitives。</p><ul><li>学源码时从下往上：provider → runtime → product。</li><li>做产品时从需求往下：CLI / RPC / SDK / core。</li><li>旧仓库已重定向，不要把旧名误认成平行项目。</li></ul>`,
    lab: ["画包图", "只用四个框画出包依赖；给每个框写一句“不负责什么”。"],
    source: ["固定 commit 的根 README", pi("README.md", "#L13-L35")]
  },
  {
    tag: "Provider", title: "pi-ai：先统一差异，再调用模型",
    questions: ["为什么统一 API 不能只把字段名改成一样？", "流式返回一半中断，错误应该 throw 还是落成消息状态？", "跨供应商切换时，哪些历史消息需要转换？"],
    copy: `<p>Provider abstraction 的难点是语义，不是 HTTP 封装。Pi 把流式片段、tool call、usage、stopReason 与错误都收敛到统一消息模型；低层 <code>StreamFn</code> 约定最终以 <code>error|aborted</code> assistant message 表达失败，让 Loop 用同一状态机收口。</p><ul><li>网络错误、限流与服务端瞬时失败才适合透明退避。</li><li>quota、billing 与 context overflow 需要走不同分支。</li><li>应用内富消息在送模型前再收敛，避免 provider 类型污染业务层。</li></ul>`,
    lab: ["错误分类表", "列出 retryable、non-retryable、overflow 三列；为每列写退出、记录与用户提示策略。"],
    source: ["pi-ai 与 retry 源码", pi("packages/ai/src/utils/retry.ts", "#L92-L227")]
  },
  {
    tag: "Messages", title: "消息系统：内富外严",
    questions: ["为什么 AgentMessage 可以比 LLM Message 更丰富？", "transformContext 与 convertToLlm 各自应该做什么？", "工具结果里的结构化 details 为什么不能全塞给模型？"],
    copy: `<p>应用需要附件、UI 状态、审计信息与自定义消息；模型只接受供应商规定的窄消息。Pi 先允许内部消息富化，再用 <code>transformContext</code> 做裁剪/注入，最后用 <code>convertToLlm</code> 收敛到模型边界。</p><p>这条边界让持久层、UI 与模型输入解耦：同一条 tool result 可以同时有模型可读摘要和应用可读结构化 details。</p>`,
    lab: ["设计双视图", "为一个数据库查询工具分别写 model content 与 UI details；说明哪些字段不应进入上下文。"],
    source: ["AgentMessage 边界", pi("packages/agent/README.md", "#L45-L64")]
  },
  {
    tag: "Loop", title: "双层 Agent Loop：两个队列，两种继续",
    questions: ["为什么 steering 与 follow-up 不能合并成一个队列？", "assistant 没有 tool call 就一定应该停止吗？", "模型、工具与宿主分别有哪些停止权？"],
    copy: `<p>内层服务当前 turn chain：assistant 产生 tool call，或宿主注入 steering，就继续。外层在当前链结束后排空 follow-up，把新工作当下一轮。两层对应不同优先级和事件边界。</p><ul><li><code>error|aborted</code> assistant 立即退出。</li><li>tool result 的 <code>terminate</code> 与 <code>shouldStopAfterTurn</code> 提供模型之外的硬停止。</li><li>“完成”还要考虑异步派生工作；<code>agent_settled</code> 不天然等于 transitive done。</li></ul>`,
    lab: ["手跑状态机", "用纸模拟：user → tool A → steering → tool B → follow-up。标出每个 turn_start / turn_end。"],
    source: ["agent-loop.ts", pi("packages/agent/src/agent-loop.ts", "#L155-L275")]
  },
  {
    tag: "Streaming", title: "流式：先结算消息，再允许工具动手",
    questions: ["为什么 message_end 是工具执行前的时序屏障？", "模型在 JSON 参数中途断流时，能不能执行已经解析出的部分？", "partial stream 应不应该持久化并恢复？"],
    copy: `<p>Pi 先把 assistant 流结算为最终消息，再进入工具阶段。若 provider 因长度截断但留下 tool call，Pi 不执行可能残缺的参数，而是生成错误 tool result 交还模型。</p><p>当前低层 AgentHarness 只把 settled response 放进 durable model；partial stream 仍是进程内状态。可观察到片段，不代表能继续同一条 provider stream。</p>`,
    lab: ["截断注入", "构造一个缺右括号的 tool arguments 流，断言工具 body 未被调用且模型收到明确错误。"],
    source: ["截断保护", pi("packages/agent/src/agent-loop.ts", "#L374-L405")]
  },
  {
    tag: "Tools", title: "工具管道：验证、拦截、执行、改写",
    questions: ["工具调用到底有几个可失败阶段？", "beforeToolCall 与 afterToolCall 各自适合放什么策略？", "并行工具如何同时保证吞吐、顺序和 sequential barrier？"],
    copy: `<p>一次调用经历 lookup → prepare/validate → before → execute/update → after → normalized result。找不到工具、参数无效、hook 拒绝与 body throw 都落成 <code>isError</code> tool result，不炸穿整个 Loop。</p><ul><li>并行工具先按源码顺序预检，再 <code>Promise.all</code> 执行，结果按原调用顺序提交。</li><li>sequential 工具形成屏障。</li><li>after hook 可改写 content、details、usage、terminate 与 isError。</li></ul>`,
    lab: ["五阶段探针", "给每个阶段注入一次失败，记录事件顺序、模型可见结果与是否继续。"],
    source: ["工具准备与执行", pi("packages/agent/src/agent-loop.ts", "#L600-L758")]
  },
  {
    tag: "Retry", title: "重试：先问副作用，再谈指数退避",
    questions: ["模型请求重试与工具重试为什么不是同一件事？", "一个发邮件工具超时后，系统凭什么知道邮件没发出去？", "崩溃恢复时哪些工具允许 replay？"],
    copy: `<p>Provider 请求可以按错误分类透明重试；tool body 默认不做内建自动重试，因为它可能已经扣费、发消息或写入。失败会成为模型可见结果，由模型或上层 policy 决定下一步。</p><p>当前 AgentHarness 把 replay policy 分成 <code>never</code> 与 <code>safe</code>：崩溃后副作用工具不应静默重放，安全工具才可重执。</p>`,
    lab: ["幂等账本", "给支付、读文件、搜索、发消息四个工具标 side effect、idempotency key、replay policy 与补偿动作。"],
    source: ["AgentHarness replay safety", pi("packages/agent/docs/harness.md", "#L180-L205")]
  },
  {
    tag: "Events", title: "事件不是通知，是时序契约",
    questions: ["UI 为什么不能只监听最终文本？", "message_end、tool_execution_start、turn_end 的顺序能否改变？", "可观测事件与持久化事实有什么区别？"],
    copy: `<p>事件流承担 UI 更新、工具进度、日志与宿主协调，也规定“何时允许下一阶段发生”。把事件只当通知，会让并发 UI、审批和审计在边界上竞态。</p><p>教学时要区分 ephemeral event 与 durable entry：前者适合流片段和进度，后者必须能参与恢复、回放与 active path 重建。</p>`,
    lab: ["事件快照", "记录一次有两个工具调用的完整事件序列；给每个事件标 ephemeral / durable / derived。"],
    source: ["事件顺序", pi("packages/agent/README.md", "#L65-L120")]
  },
  {
    tag: "Context", title: "Context engineering：预算、变换与溢出",
    questions: ["context window 应该给输入、输出和工具结果各留多少空间？", "为什么 overflow 不应该走普通 provider retry？", "哪些失败消息应留在历史、却从下一次活动上下文移除？"],
    copy: `<p>Context 是运行时预算。Pi coding-agent 在超出阈值时先压缩，再最多重试一次；失败/截断 assistant 仍保留在 session history 供审计，但从下一次模型活动上下文移除。</p><p>稳定系统要同时度量 token、cache prefix、工具输出体积、预留输出和压缩成本，而不是只看总 message 数。</p>`,
    lab: ["预算模拟器", "用 128k window，分别为 system、history、tools、new input、max output 和 safety reserve 分配预算。"],
    source: ["overflow recovery", pi("packages/coding-agent/src/core/agent-session.ts", "#L2131-L2175")]
  },
  {
    tag: "Compaction", title: "压缩：摘要旧世界，保留最近现场",
    questions: ["压缩切点为什么不能落在 tool result 上？", "prior summary 如何进入下一次摘要？", "分支摘要与上下文压缩解决的是同一个问题吗？"],
    copy: `<p>默认触发是 <code>contextTokens &gt; contextWindow - reserveTokens</code>，默认 reserve 16,384。算法向后寻找切点，保留约 20k recent content，摘要更早内容并写入 compaction entry。</p><p>Compaction 为当前路径减压；branch summary 在离开旧分支时，把未进入新 active path 的工作带回来。两者都摘要，但触发和语义不同。</p>`,
    lab: ["手工切点", "给出含 user/assistant/toolCall/toolResult 的 12 条记录，选择合法 cut point 并解释 retained tail。"],
    source: ["Compaction 算法", pi("packages/coding-agent/docs/compaction.md", "#L27-L117")]
  },
  {
    tag: "Sessions", title: "会话树：让回退、分叉和比较自然发生",
    questions: ["为什么 parentId 比“撤销最后 N 条”更稳？", "active path 如何变成模型上下文？", "离开旧分支时，哪些信息应该通过 branch summary 带回？"],
    copy: `<p>每条 entry 带 <code>id</code> 与 <code>parentId</code>，同一 JSONL 文件形成树。切换 leaf 不删除旧记录；模型上下文只沿根到当前叶构建。</p><p>这使回退、平行试验、模型切换比较与历史保留共享同一个数据模型。GUI 只是树的投影，不是树存在的理由。</p>`,
    lab: ["分叉游乐场", "画 7 个节点的树，选择三个 active leaf；为每个 leaf 写出精确 path 和需要的 branch summary。"],
    source: ["Session tree", pi("packages/coding-agent/docs/session-format.md", "#L306-L342")]
  },
  {
    tag: "Harness", title: "当前 AgentHarness：把程序计数器也持久化",
    questions: ["为什么 session log 还不等于 durable harness？", "entry store、register store、usage ledger 分别承载什么？", "原子事务怎样降低“记录成功但副作用状态没落盘”的裂缝？"],
    copy: `<p>AgentHarness 把 immutable entry、mutable register 与 append-only usage ledger 分离，并用 transaction 一起提交 durable program counter 与 effect state。它开始回答进程崩溃后“从哪继续、哪些工具能重放”。</p><p>边界也很诚实：不保证 exactly-once、不恢复 partial stream、不处理多写者复制；源码仍有 NotImplemented 类型，学习时必须把规格与实测分开。</p>`,
    lab: ["崩溃矩阵", "在模型完成前、tool call 落盘后、tool body 后、result 落盘前分别 kill 进程，写出期望恢复动作。"],
    source: ["AgentHarness 存储与事务", pi("packages/agent/docs/harness.md", "#L115-L214")]
  },
  {
    tag: "Security", title: "生产边界：Hook 不是 Sandbox",
    questions: ["beforeToolCall 能阻止什么，又阻止不了什么？", "第三方 extension 为什么比普通 prompt 风险更高？", "生产部署最小威胁模型应该覆盖哪些资产？"],
    copy: `<p>Pi extension 是进程内 TypeScript，能执行任意代码；coding agent 继承启动用户权限。Hook 能做 policy 与 approval，但无法把恶意扩展从宿主权限中隔离。</p><ul><li>不受信工作负载放进 Docker、Gondolin、OpenShell 等 sandbox。</li><li>Secrets 由 broker 按调用发放，不长期暴露给进程。</li><li>记录 approval、tool input/output、退出原因和版本指纹。</li></ul>`,
    lab: ["威胁建模", "为代码仓库、SSH key、云凭证、内网和用户数据画 trust boundary，并给每条跨界调用配置 control。"],
    source: ["官方安全声明", pi("README.md", "#L38-L46")]
  },
  {
    tag: "DSH", title: "DeepSeek Harness：从可读内核走向全插件平台",
    questions: ["Pi 与 DSH 的插件化边界到底差在哪？", "DSH 的 turn / step / request 与 Pi 双层 Loop 如何对应？", "两种“会话树”为什么不能写成同一个概念？"],
    copy: `<p>DSH 用 Cordis 让 model、loop、tool、session、storage、sandbox、policy、scheduler 与 UI 都成为 service/event/effect 插件。单 session 是 append-only event log，fork 复制 prefix 到 child session；Pi coding-agent 则在一个 JSONL 内以 parentId 构树。</p><p>DSH 更像可替换子系统的微内核，Pi 更像清晰 primitives 加成品 coding agent。前者替换更深，后者路径更短。DSH 当前仍是 v0.1.1 RC / developer preview。</p>`,
    lab: ["同题时序图", "对同一个“模型调两个工具、一个需审批、一个失败”的任务，分别画 Pi 与 DSH 时序图。"],
    source: ["DSH architecture", dsh("docs/architecture.md", "#L9-L61")]
  }
];

const comparisons = [
  ["产品边界", "primitives + 成品 coding agent + 当前 durable AgentHarness", "local-first Web/headless harness；profile/bundle 组合全栈", "Pi 更快形成直觉；DSH 更像平台内核"],
  ["Loop", "steering/tool 内环 + follow-up 外环", "driver → turn → step → provider request retry", "比较队列与 durable boundary，不只数层数"],
  ["Provider", "pi-ai 统一多供应商", "DeepSeek adapter + 基于 pi-ai 的通用 adapter", "可以组合，不是纯替代"],
  ["工具治理", "validate / before / execute / after / result", "durable call + guard / permission / sandbox / approval / wrappers / durable result", "DSH seam 更完整；Pi 更易读"],
  ["工具重试", "默认不透明自动重试", "base 同样不自动重试，可用 wrapper plugin", "都必须显式处理幂等与副作用"],
  ["持久化", "单 JSONL entry tree；current harness 加 store/ledger/transaction", "typed append-only session event log", "DSH 回放审计更原生；Pi 导航更直接"],
  ["分叉", "同 session 内 parent tree 与 active path", "复制 session prefix 到 child，跨 session 成谱系", "产品体验相似，恢复和分享边界不同"],
  ["安全", "官方无内建 permission，需扩展 + 外部 sandbox", "base 有 policy/sandbox/approval seams", "Pi 的自由必须配外部治理"],
  ["成熟度", "v0.84.3 stable；公开历史更长", "v0.1.1 RC；developer preview", "当前交付优先 Pi，DSH 适合试点与卡位"]
];

const coverage = [
  ["CSDN","complete",12],["微信公众号","blocked",0],["知乎","complete",5],["小红书","blocked",0],
  ["微博","blocked",0],["抖音","blocked",0],["X / Twitter","partial",4],["Bilibili","complete",35],
  ["掘金","complete",3],["YouTube","complete",15],["Linux.do","complete",8],["GitHub","complete",48],
  ["百度搜索","partial",0],["Google 搜索","blocked",0],["Bing 搜索","partial",0],["今日头条","partial",0],
  ["36氪","complete",5],["InfoQ","complete",3],["SegmentFault","complete",7],["开源中国","partial",0],
  ["V2EX","complete",6],["Reddit","blocked",0],["Hacker News","complete",8],["Medium","partial",3],
  ["LinkedIn","partial",2],["快手","blocked",0],["微信视频号","blocked",0],["TikTok","blocked",0],
  ["Official Web","complete",4],["npm","complete",7],["DEV.to","complete",4],["Stack Overflow","partial",0],
  ["Product Hunt","complete",1],["Substack","complete",4],["arXiv / OpenReview","partial",1],["Gitee","partial",2],
  ["Zenn","complete",1],["HackerNoon","complete",1],["Qiita","complete",1],["Hashnode","partial",1],
  ["note","complete",1],["Hugging Face","partial",1],["Bluesky","complete",1],["GitLab","complete",1],
  ["Composio","complete",1],["PyPI","complete",1],["Docker Hub","partial",1]
];

const expansionSources = [
  ["Zenn", "源码实测", "把 Pi 当自建 Agent 基座，而非又一个成品 CLI", "https://zenn.dev/53able/articles/c619b3f3cabf4e"],
  ["HackerNoon", "实践", "用 SSH extension 管理 VPS", "https://hackernoon.com/how-i-manage-my-vps-with-pis-ssh-extension"],
  ["Qiita", "教程", "从最小聊天循环到自定义工具与 Skill", "https://qiita.com/otakumesi/items/414c2e1836df4d8e278d"],
  ["Hashnode", "相邻案例", "Kata / Pi harness 如何进入编排系统", "https://plzai.hashnode.dev/2026-04-30-openai-symphony-codex-orchestration-linear"],
  ["note", "架构导读", "用“减法设计”理解模型切换、会话树与扩展", "https://note.com/_kihonushi/n/n4e4bd035c453"],
  ["Hugging Face", "生态记录", "公开 session dataset；仅作采用信号，不作源码事实", "https://huggingface.co/datasets/badlogicgames/pi-mono/blob/main/2026-01-16T02-58-05-814Z_14c806f6-4fde-4121-9a73-a8a167199723.jsonl"],
  ["Product Hunt", "商业化", "产品定位、用户评论与生态采用", "https://www.producthunt.com/products/pi-coding-agent-3"],
  ["Bluesky", "公开帖子", "Pi + Tiny LLM + Devcontainer 的本地路线", "https://bsky.app/profile/k33gorg.bsky.social/post/3me6k6usdns2d"],
  ["GitLab", "部署案例", "把 Pi 封装成容器、API、MCP、Telegram 与 cron", "https://gitlab.com/psyb0t/docker-pibox"],
  ["Composio", "集成教程", "Pi 作为推理内核，外接 Slack 与用户级工具授权", "https://docs.composio.dev/examples/general-agent-with-pi"],
  ["PyPI", "跨语言", "用 RPC 从 Python 驱动真实 Pi runtime", "https://pypi.org/project/pi-py-sdk/"],
  ["Docker Hub", "分发工件", "可复现的 pi-coding-agent 多架构镜像层", "https://hub.docker.com/layers/stephengpope/thepopebot/coding-agent-pi-coding-agent-1.2.78/images/sha256-8203151c3ee00422b2a8a9dbed716557c80f49ef2d37bae4ef72e23782cb34db"]
];

function renderChapters() {
  const root = document.querySelector("#chapter-list");
  const completed = new Set(JSON.parse(localStorage.getItem("pi-guide-completed") || "[]"));
  root.innerHTML = chapters.map((chapter, index) => `
    <article class="chapter${index === 0 ? " open" : ""}" data-index="${index}">
      <button class="chapter-head" aria-expanded="${index === 0}">
        <span class="number">${String(index + 1).padStart(2,"0")}</span>
        <h3>${chapter.title}</h3><span class="chapter-tag">${chapter.tag}</span>
      </button>
      <div class="chapter-body">
        <div class="question-box"><span>READ BEFORE ANSWERS</span><ol>${chapter.questions.map(q => `<li>${q}</li>`).join("")}</ol></div>
        <div class="chapter-columns">
          <div class="chapter-copy">${chapter.copy}<a class="source-link" href="${chapter.source[1]}" target="_blank" rel="noreferrer">${chapter.source[0]} ↗</a></div>
          <aside class="chapter-lab"><span>MINIMUM LAB</span><h4>${chapter.lab[0]}</h4><p>${chapter.lab[1]}</p>
            <label class="complete-label"><input type="checkbox" data-complete="${index}" ${completed.has(index) ? "checked" : ""}>我能不看答案讲清这三题</label>
          </aside>
        </div>
      </div>
    </article>`).join("");

  root.addEventListener("click", event => {
    const head = event.target.closest(".chapter-head");
    if (!head) return;
    const article = head.closest(".chapter");
    article.classList.toggle("open");
    head.setAttribute("aria-expanded", String(article.classList.contains("open")));
  });
  root.addEventListener("change", event => {
    const input = event.target.closest("[data-complete]");
    if (!input) return;
    const index = Number(input.dataset.complete);
    input.checked ? completed.add(index) : completed.delete(index);
    localStorage.setItem("pi-guide-completed", JSON.stringify([...completed]));
    updateProgress(completed.size);
  });
  updateProgress(completed.size);
}

function updateProgress(count) {
  document.querySelector("#chapter-progress").style.width = `${count / chapters.length * 100}%`;
  document.querySelector("#progress-copy").textContent = `${count} / ${chapters.length} 已标记完成`;
}

function renderComparisons() {
  document.querySelector("#comparison-body").innerHTML = comparisons.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("");
}

function renderCoverage() {
  document.querySelector("#coverage-grid").innerHTML = coverage.map(([name,status,count]) => `
    <article class="coverage-card ${status}"><span class="coverage-pill">${status}</span><h3>${name}</h3><p>${count ? `${count} 条候选召回` : "严格主题零召回 / 受阻"}</p></article>`).join("");
}

function renderExpansionSources() {
  document.querySelector("#expansion-source-grid").innerHTML = expansionSources.map(([platform, type, title, url]) => `
    <a href="${url}" target="_blank" rel="noreferrer"><span>${platform} · ${type}</span><strong>${title}</strong><i>↗</i></a>`).join("");
}

let allSources = [];
let activeFilter = "全部";

function renderSourceFilters() {
  const filters = ["全部", ...new Set(allSources.map(item => item.track))];
  document.querySelector("#source-filters").innerHTML = filters.map(filter => `<button class="filter-button${filter === activeFilter ? " active" : ""}" data-filter="${filter}">${filter}</button>`).join("");
}

function renderSources() {
  const query = document.querySelector("#source-search").value.trim().toLowerCase();
  const rows = allSources.filter(item => {
    const haystack = `${item.title} ${item.finding} ${item.platform} ${item.author} ${item.track}`.toLowerCase();
    return (activeFilter === "全部" || item.track === activeFilter) && haystack.includes(query);
  });
  document.querySelector("#result-count").textContent = `${rows.length} / ${allSources.length}`;
  document.querySelector("#source-grid").innerHTML = rows.length ? rows.map(item => `
    <article class="source-card">
      <div class="source-card-top"><span class="source-rank">${String(item.curator_rank).padStart(2,"0")}</span><span class="source-platform">${item.actual_platform || item.platform}</span></div>
      <h3>${item.title}</h3><p>${item.finding}</p>
      <div class="source-meta"><span>${item.track} · ${item.evidence_grade}</span><a href="${item.url}" target="_blank" rel="noreferrer">OPEN ↗</a></div>
    </article>`).join("") : `<div class="empty-state">没有匹配资料。换一个关键词试试。</div>`;
}

async function loadSources() {
  try {
    const response = await fetch("./research/run-pi-agent-runtime-20260826/curated-top50.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    allSources = (await response.json()).items;
    renderSourceFilters(); renderSources();
  } catch (error) {
    document.querySelector("#source-grid").innerHTML = `<div class="empty-state">Top 50 数据加载失败：${error.message}</div>`;
    document.querySelector("#result-count").textContent = "ERROR";
  }
}

function bindLibrary() {
  document.querySelector("#source-search").addEventListener("input", renderSources);
  document.querySelector("#source-filters").addEventListener("click", event => {
    const button = event.target.closest("[data-filter]");
    if (!button) return;
    activeFilter = button.dataset.filter;
    renderSourceFilters(); renderSources();
  });
}

function observeReveals() {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".reveal").forEach(el => el.classList.add("visible")); return;
  }
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add("visible"); observer.unobserve(entry.target); }
  }), {threshold: .07});
  document.querySelectorAll(".reveal").forEach(el => observer.observe(el));
}

renderChapters();
renderComparisons();
renderCoverage();
renderExpansionSources();
bindLibrary();
observeReveals();
loadSources();
