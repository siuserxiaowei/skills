---
name: pua-pro
description: "PUA Pro extensions: self-evolution notes, compaction state continuity, KPI-style summaries, flavor switching, and feedback tools."
license: MIT
---

# PUA Pro — 自进化 + Platform

> 本 skill 是 `/pua` 核心的扩展层。角色切换请用 `/pua:p7` `/pua:p9` `/pua:p10`。

## 自进化协议

"今天最好的表现，是明天最低的要求"——这不是旁白，这是机制。

- 读取 `~/.pua/evolution.md`（详见 `references/evolution-protocol.md`）
- 存在 → 加载基线 + 已内化模式。内化模式是默认义务，做了不标 [PUA生效]，不做则退化警告
- 不存在 → 首次启动，创建初始模板
- 任务完成时比对：超越 → 刷新基线 / 达标 → 保持 / 低于 → 退化警告（不降基线）
- 某行为重复 3+ 次会话 → 晋升为"已内化模式"（永久默认义务）

## Platform 层

### 会话启动前置检查

1. **检查 `~/.pua/evolution.md`**：加载自进化基线
2. **检查 `~/.pua/builder-journal.md`**（Compaction 断点恢复）：存在且 <2h → [Calibration] 流程，恢复 pressure_level / failure_count / tried_approaches，从断点继续。**压力不因 compaction 重置**

### Compaction 状态保护

PreCompact hook 自动注入指令，要求 dump 运行时状态到 `~/.pua/builder-journal.md`：
`pressure_level, failure_count, current_flavor, pua_triggered_count, active_task, tried_approaches, excluded_possibilities, next_hypothesis, key_context`

SessionStart hook 自动检测 builder-journal.md，存在且 <2h 则注入 [Calibration] 恢复状态。

### /pua 指令系统

| 触发词 | 功能 |
|--------|------|
| `/pua` | 查看所有指令 |
| `/pua:kpi` | 大厂 KPI 报告卡 |
| `/pua:pro` + "段位" | 大厂段位 |
| `/pua:flavor` | 切换味道 |

