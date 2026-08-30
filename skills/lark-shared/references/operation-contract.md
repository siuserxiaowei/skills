# 操作计划合同

`scripts/check_plan.py` 检查一个 JSON 对象。它不调用 lark-cli，也不证明飞书端状态。

## 核心字段

| 字段 | 含义 |
|---|---|
| `skill` | 27 个 lark Skill 之一 |
| `argv` | 逐项参数数组，首项必须是 `lark-cli` |
| `profile` | 本次 profile 名，不等于切换全局 profile |
| `identity` | `user` 或 `bot`；核心管理命令可省略 |
| `risk` | `read`、`write`、`high-risk-write` |
| `target.summary` | 人可识别的目标摘要 |
| `target.verified` | 目标是否经只读解析 |
| `authorization.basis` | 用户请求中授权这次影响的依据 |
| `authorization.explicit` | 高风险或对外动作是否获明确同意 |
| `dry_run` | 是否支持、是否已完成且与意图一致 |
| `verification` | 响应、读回或异步终态及预期 |
| `time_zone` | 时间敏感任务的 IANA 时区 |
| `time_kind` | `instant` / `range` 需带偏移；`date-only` / `all-day` 只固定时区与日期语义 |
| `pagination` | 全量或有界读取的策略与上限 |
| `duplicate_control` | 重复敏感动作的幂等键或查重方案 |
| `recovery` | 破坏性动作的恢复或不可恢复说明 |
| `untrusted_input` | 是否处理外部内容 |
| `treat_as_data` | 是否明确把外部内容仅作为数据 |

## 结果

- exit 0：计划满足静态门槛；
- exit 1：输入文件或 JSON 无法解析；
- exit 2：计划存在阻断项；
- stdout：JSON 报告；脚本不会把 argv 交给 shell。

计划通过不代表应执行。命令 help/schema、实际权限、目标现状和用户最新意图仍需现场核对。

业务 API 的 `argv` 必须实际携带与计划一致的 `--profile` 和 `--as`，不能只在旁边声明。高风险计划还必须明确写出精确命令是否支持 dry-run。
