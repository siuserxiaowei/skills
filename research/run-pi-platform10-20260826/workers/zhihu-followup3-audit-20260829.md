# Zhihu follow-up 3 audit (2026-08-29)

本轮在父代理授权后，将此前已完整回读的 5 个 Zhihu canonical 原文写入
append-only candidate/readback 文件。没有修改 `candidates.json`、
`review_queue.json`、ledger 或 accepted coverage。写入前重新检查了当前主账本、
所有 `*-candidates*.jsonl` worker shards 和已有 Zhihu follow-up 文件，5 个 URL/ID
均未出现冲突。

## Route and boundary

`agent-reach doctor --json` 已尝试但本机命令不存在；按公开网页 fallback，使用普通匿名
Chrome 直接打开已知 Zhihu `/p/` URL。Google focused exact-title 查询只用于发现，
原文正文、作者和可见日期均在 canonical 页面读取。未登录、未互动、未下载、未绕过
验证码/挑战，也未把搜索摘要作为证据。

## New objects

- `china-followup3-zhihu-2028858973692916778-refuse-bloat` — counterxing，编辑
  2026-04-18，3,905 chars，SHA-256 `6bdb86dd642b62fdc0267f4708679b5c94f4ec5c18ecf85e8242dda66eff737a`。
  Pi-agent-core/coding-agent 双层循环、工具、模型和会话树深挖。
- `china-followup3-zhihu-2070274194219217372-core-architecture` — 酌沧AI，编辑
  2026-08-10，4,452 chars，SHA-256 `6155345075b464b070edfde786eeb704e6fbc92d1bdf9d1794765cae1ed1b0fe`。
  pi-ai/agent-core/coding-agent 分层、事件与压缩。
- `china-followup3-zhihu-2037280128980496933-minimalist-advocate` — lufeikevin，编辑
  2026-05-11（首发未知），2,304 chars，SHA-256 `68a8441b9d0fd224e65dbb3b007e434f0e4ddece47d1a0a473a120e797714b8c`。
  入门比较、安装和会话命令。
- `china-followup3-zhihu-2012965687170204516-three-projects` — 还是菜，发布
  2026-03-05，11,993 chars，SHA-256 `e0230d2ff5d28f6b7ffa80d3bd4651f7d2b95a5a5e0ea392691ef9915728f9db`。
  OpenCode/Kimi/Pi-Mono 比较；标记 `independent_candidate_pi_primary_review_required`，
  由主策展人决定是否计入 Pi quota。
- `china-followup3-zhihu-2071312132931637529-deepseek-v4` — Ai学习的老章，发布
  2026-08-13，6,563 chars，SHA-256 `64695065197622fccd8826caed0b860d72a08983c4a4cca54161cfa1ee47a957`。
  Pi + DeepSeek-V4-Flash、pi-peer/pi-rlm 和扩展生态；同样标记需主策展人复核 Pi-primary。

前 3 条是最强的 Pi-primary 独立对象；后 2 条正文完整但包含较多比较/生态和作者
自报数据，已在字段与回读中显式保留限制。全部状态为 `curator_review_ready`，不能
直接算 accepted。
