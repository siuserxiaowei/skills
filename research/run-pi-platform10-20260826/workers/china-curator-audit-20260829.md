# 中文平台候选主审审计（2026-08-29）

本文件是对既有 `review_queue.json` 的只读主审记录；没有修改
`candidates.json`、`sources.tsv`、`evidence_cards.tsv` 或平台配额账本。
候选原页通过普通匿名 Chrome 可见页面逐页回读，未登录、未互动、未下载、未绕过
验证码/安全检测。知乎、Linux.do、36Kr、CSDN、掘金和 SegmentFault 的正文与
元数据均按当前页面核对；Jina/agent-reach CLI 不可用时没有把替代路线伪装成命名
搜索引擎证据。

## 结论

唯一值得主线程考虑进一步 promotion 的现有候选是 `worker-cn-050`（掘金）。
其正文约 7,930 字符，明确设有 `pi-mono`、`pi-ai`、`pi-agent-core` 和
`pi-coding-agent` 章节，且讨论四工具、Agent Loop、Session、Skills/Extensions
和 OpenClaw 的分层。当前 readback 已写入
`china-curator-audit-readbacks-20260829.jsonl`，但仍保持 worker 状态；主线程
需在接受前做跨站正文指纹复核，并自行补写 accepted source/evidence ledger。

没有任何其他审计对象可安全新增到 47×10 主库：

- 知乎 `worker-cn-051` 与已接受 seed 完全同 URL；`worker-cn-052` 与已接受
  SegmentFault `worker-cn-058` 是同一 OpenClaw/Pi Runtime 内容簇；`worker-cn-054`
  是通用 Agent 自实现教程、Pi 仅作四工具对照；`worker-cn-055` 是 Fabarta/
  OpenClaw 企业实践、Pi 仅少量出现。
- 36Kr `worker-cn-080` 与已接受 InfoQ `worker-cn-063` 为同一 Composio benchmark
  稿；`worker-cn-082` 与已接受 InfoQ seed `seed-infoq-42-coding-agents` 为同一
  Mario 演讲稿。`worker-cn-080` 当前直接访问还落入 36Kr 安全检测，未绕过。
- Linux.do `worker-cn-066` 与已接受 seed 同 URL；`worker-cn-068`、`069`、`071`、
  `072` 是 DSH 泛讨论或短帖；`070` 是 DSH PWA/Automator 教程，Pi 仅作为末尾
  `pi-web` 链接；`073` 的 `?page=4` 目标无法在匿名 canonical 页面验证，实际落到
  首页逻辑题正文。
- CSDN `worker-cn-043` 只返回约 1,160 字符目录/首段 shell；`worker-cn-045`
  虽有约 3,532 字符正文，但只泛称 “Pi Agent kernel”，没有
  `earendil-works/pi`、`pi-coding-agent` 或 npm 锚点，严格身份门不通过。
- 掘金 `worker-cn-048` 与已接受 Juejin seed 完全同 URL/同文；SegmentFault
  `worker-cn-059` 与已接受 seed 同 URL，且与 OSCHINA 七牛云指南形成同作者/同日
  内容簇。Gitee `code-hosts-gitee-001` 明确是 `earendil-works/pi` upstream
  mirror，按协议拒绝。

逐候选机器可读决策见
`china-curator-audit-decisions-20260829.jsonl`。该文件包含 19 条 ID、规范化 URL、
重复归属或拒绝理由，便于主线程在显式 promotion 前复核。

## 访问边界

知乎四篇外围文章均可匿名读取正文，但“可读”不等于“Pi 主体”；只保留严格
Pi-primary/Pi-runtime 取向。36Kr 页面上的安全检测没有被点击或绕过。Linux.do
所有回读只使用公开 topic DOM；短帖不会因可见浏览量或回复数而升级。CSDN、掘金、
SegmentFault 的正文仅用于证据判断，不执行文章中的安装、命令、Provider 登录或
外部链接操作。
