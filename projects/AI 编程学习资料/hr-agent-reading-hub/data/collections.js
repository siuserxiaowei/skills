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
