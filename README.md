# Pi Runtime Field Guide

一份面向中文开发者的 Pi Agent 源码学习知识库，覆盖：

- 14 章学习路线，每章先放 3 个无答案问题
- Pi v0.80.2 中文教程基线 → v0.84.3 当前源码差分
- Agent Loop、工具管道、retry、context、compaction、session tree、AgentHarness
- Pi 与 DeepSeek Harness 的源码级架构对照
- 47 条平台路线，其中 33 个平台读到原页；另有经过证据合同校验的 Top 50
- 安全边界、商业化方向与最小可运行实验

## 本地预览

```bash
python3 -m http.server 4173
```

打开 `http://127.0.0.1:4173`。站点没有运行时依赖或构建步骤。

## 研究证据

主要产物位于 [`research/run-pi-agent-runtime-20260826`](./research/run-pi-agent-runtime-20260826)：

- `query_plan.json` / `route-bundle.json`：查询与路由冻结
- `platform_coverage_36.tsv`：canonical 28 + 首轮 adjacent 的历史终态
- `platform_expansion_sources.tsv` / `platform_expansion_audit.json`：12 个补充原页与“33 个原页平台”验收
- `candidates.json` / `sources.tsv` / `evidence_cards.tsv`：策展与证据账本
- `rank-input-manifest.json` / `curate-result.json`：不可变输入与独立主审
- `engine_plan.json` / `engine_execution.json`：三引擎真实 probe、Python rank 重放与完成结果
- `ranking-output/`：Top 50、rejected、coverage、validation 与报告

Top 50 是截至 2026-08-26、在本次主题、时间窗、平台路线与 deterministic-v2 评分下的策展结果，不是“全网绝对排名”。

## 版本冻结

- Pi source：`8fa7eebd235355522c8104166b4f1f959b4e2f10`
- Pi stable release：`v0.84.3`
- DeepSeek Harness：`b150a551b8d465e31e418e1b2eaf5e79bbb7d28e`
- DSH release：`v0.1.1-rc.2`，官方标为 developer preview

## 许可

- 本站前端代码：MIT，见 [`LICENSE`](./LICENSE)
- 原创研究文字：CC BY-SA 4.0，见 [`CONTENT-LICENSE.md`](./CONTENT-LICENSE.md)
- 第三方材料：版权与许可归原作者，见 [`ATTRIBUTION.md`](./ATTRIBUTION.md)
