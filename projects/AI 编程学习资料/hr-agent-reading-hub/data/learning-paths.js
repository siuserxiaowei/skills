export const learningPaths = [
  {
    time: "第 1 步",
    title: "先判断：什么时候该做 Agent",
    body: "不要把所有 AI 应用都叫 Agent。先判断任务是否需要多步执行、工具调用、状态保持和反馈闭环。",
    sourceIds: ["openai-practical-guide-agents", "anthropic-effective-agents", "twelve-factor-agents"],
  },
  {
    time: "第 2 步",
    title: "设计工具与上下文",
    body: "一个好 Agent 的能力边界很大程度由工具、上下文、资源和提示结构决定，而不是只由模型决定。",
    sourceIds: ["anthropic-writing-tools", "anthropic-context-engineering", "mcp-intro", "mcp-spec"],
  },
  {
    time: "第 3 步",
    title: "把工作流、状态和记忆做清楚",
    body: "长流程 Agent 需要显式状态、检查点、短期/长期记忆和人工介入点，否则很难稳定交付。",
    sourceIds: ["langgraph-overview", "langgraph-memory", "langchain-human-loop"],
  },
  {
    time: "第 4 步",
    title: "横向比较工程框架",
    body: "不同框架都在解决 agent、tool、memory、handoff、eval、deploy 等问题；先理解抽象，再选工具。",
    sourceIds: ["openai-agents-python", "google-adk", "microsoft-agent-framework", "pydantic-ai"],
  },
  {
    time: "第 5 步",
    title: "加入评估、观测和回归测试",
    body: "从 demo 到可用系统，核心差距是能否追踪、评估、复现和持续改进。",
    sourceIds: ["openai-tracing", "promptfoo-evals", "arize-phoenix"],
  },
  {
    time: "第 6 步",
    title: "补上安全治理和人工审核",
    body: "Agent 能调用工具后，权限、提示注入、敏感数据、越权动作和高风险决策都必须被设计进系统。",
    sourceIds: ["openai-guardrails", "owasp-llm-top10", "nist-genai-profile"],
  },
  {
    time: "第 7 步",
    title: "回到业务案例做闭环",
    body: "最后用 HR、飞书、多维表格、n8n、Dify 等案例，把方法论落到真实业务流程和数据回写里。",
    sourceIds: ["feishu-resume-template", "feishu-base-workflow", "n8n-recruitment-pipeline", "dify-resume-screening"],
  },
];
