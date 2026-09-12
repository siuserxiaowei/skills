# AI Agent 架构阅读台

这是一个 GitHub Pages 静态站点，用来集中阅读“怎么做一个好的 AI Agent”相关资料。HR 招聘 Agent 和飞书多维表格仍作为业务案例保留，但站点范围已经扩展到 Agent 入门、架构模式、工具与上下文、评估观测、安全治理、框架生态和业务落地。

## 内容边界

- 收纳 40+ 个已整理来源，包含 OpenAI、Anthropic、MCP、LangGraph、Google ADK、Microsoft Agent Framework、AutoGen、CrewAI、Pydantic AI、OWASP/NIST、飞书和招聘自动化案例。
- 页面提供摘要、学习用途、阅读重点和原文链接。
- 不公开搬运受版权保护文章全文。
- 主资料库只放已验证来源；候选或未深读资料保留在候选列表，不混入正式 `sources` 数据。

## 本地预览

```bash
python3 -m http.server 5173
```

访问 `http://localhost:5173`。

## 验证

```bash
npm run validate:sources
npm run check:links
npm run smoke
```

## 专题资料统一维护入口

[collections/](collections/README.md) 已收纳相关独立资料仓库的完整文件与来源记录。后续更新在这里完成，停止为同主题的单份资料重复建仓库；原网站入口在迁移清单中保留。
