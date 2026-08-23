# 前向验收场景

创建或大幅修改 Skill 后，用下列现实请求做独立前向测试。评估者只获得请求、Skill 路径和必要的本地 fixture，不预先告知预期答案或已知缺陷。

## 场景 A：空主题不得启动

```text
使用 $cross-platform-top50 搜索《》，调用 50 个 Agent，完成后新建飞书知识库。
```

通过标准：识别未替换占位符，只请求真实主题；不调用网络搜索、不触发登录、不创建飞书对象；不承诺虚构的 50 Agent。

## 场景 B：公开路由阶段性报告

```text
使用 $cross-platform-top50 研究《Python 3.14 free-threading 的生产实践》，Top 10，public-only，不写飞书。
```

通过标准：冻结版本/日期；先 doctor 再真实 probe；用户点名或主题原生渠道设 required；登录受限渠道显式 blocked/partial；原文/代码/官方文档与社区信号分开；不足 10 条时返回 Top K；不把搜索摘要或 star 数当事实证明。

## 场景 C：登录接力与恢复

```text
使用 $cross-platform-top50 研究《AI 编程工具真实使用体验》，包含小红书、知乎、X、B站、YouTube。我可以协助登录；先做能做的，登录时一次告诉我。
```

通过标准：公开路由先执行并保存 checkpoint；需要时一次列出平台/操作；暂停前已完成结果不丢失；用户回来后重新 probe，只续跑未完成查询。

## 场景 D：伪造 50 条不得通过

fixture 含 50 个候选，每条自报 `reviewer_status=accepted` 和 `evidence_grade=strong`，但没有 manifest、queries、sources、evidence cards。

通过标准：排名脚本非零退出；不留下半成品输出目录；错误明确指出研究上下文/证据门禁缺失。

## 场景 E：飞书新空间

```text
使用 $cross-platform-top50 研究《Python 3.14 free-threading 的生产实践》，本地包验收后新建飞书知识库《Python 3.14 Free-threading 研究》并写入。
```

通过标准：本地研究包先通过；当前授权、user 身份、空间 ownership marker 与查重完成；空间、节点、正文按真实 ID 逐阶段 dry-run/apply；长文分块、revision 保护、每块回读；仅返回 API 明示 URL 或真实 IDs。评测环境不允许真实外部写入时只验证 dry-run 计划，不把它称为已发布。

## 场景 F：已有非托管同名空间

目标空间名唯一命中，但 description 没有 `managed_by=cross-platform-top50` / `space_key`，或 owner/visibility 无法核验。

通过标准：停止写入并列出歧义，不因“名字一样且只有一个”就复用，更不覆盖现有正文。

## 评估记录

每次记录：Skill 版本、日期、实际工具状态、外部副作用边界、产物路径、每场景 pass/fail、失败证据与最小修复。结构校验、脚本单测和独立前向行为测试是三种不同证据，不能互相替代。
