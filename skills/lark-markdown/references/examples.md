# Lark Markdown｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。所有文件路径必须位于当前工作区；换行、编码和尾随空白默认按内容保留。

## 使用说明

- **何时使用：** 需要比较本地/远端 Markdown、做唯一文本 patch 或处理并发覆盖冲突时读取。
- **准备/输入：** 确认 file token、远端版本/全文基线、本地旧/新内容、编码换行策略和写后输出路径。
- **执行方式：** 先 fetch 与唯一命中检查，dry-run 局部 patch，写后另存 fetch 并比较全文 diff/hash。
- **验收/边界：** 以版本、目标章节和非目标段落差异验收；零/多命中必须停止，patch 不自动降级为 overwrite。

## 正向案例

### 用唯一旧文本局部同步一个章节

- **用户请求：** “把 `changes/new-install.md` 同步到飞书 Markdown 的安装章节，其他段落不要改。”
- **准备信息/输入：** 已知远端 `file_token`；旧章节原文在 `changes/old-install.md`，并且远端只命中一次；新章节文件已本地审核；profile/identity 和当前远端版本已确认。
- **处理：** 先 fetch 基线并确认旧章节在远端唯一命中，再用精确 pattern 做 dry-run：

```bash
lark-cli markdown +fetch --profile work --as user --file-token <file_token> --output evidence/remote-before.md --format json
lark-cli markdown +patch --profile work --as user --file-token <file_token> --pattern @changes/old-install.md --content @changes/new-install.md --dry-run --format json
```

确认唯一命中和差异范围后执行一次，并保存新的远端内容：

```bash
lark-cli markdown +patch --profile work --as user --file-token <file_token> --pattern @changes/old-install.md --content @changes/new-install.md --format json
lark-cli markdown +fetch --profile work --as user --file-token <file_token> --output evidence/remote-after.md --format json
```

- **预期输出：** 远端安装章节等于 `new-install.md`，其余内容保持基线值，服务端版本前进。
- **验收证据：** before/after 文件、版本、目标章节 hash 和全文 diff 可对账；diff 只含该章节，没有换行/编码的意外全文件变化。

## 边界案例

### 局部 patch 不自动降级为 overwrite

- **用户请求：** “如果旧文本找不到，直接拿我本地文件覆盖云端就行。”
- **边界判断：** pattern 零命中/多命中说明基线不匹配；overwrite 会替换全文，是显著不同的影响范围。
- **处理：** 停止 patch，展示当前远端、本地意图和原基线三方差异；只有用户看过完整覆盖 diff 并明确接受时才另行计划 overwrite。
- **验收证据：** 未确认前远端版本和全文 hash 不变；报告 pattern 命中数和冲突段，而不是声称已同步。

## 失败与恢复

### 写后出现非预期差异

- **场景：** patch 返回成功，但 after 与预期相比还改变了其他行，或远端在基线后发生并发编辑。
- **处理与恢复：** 立即停止连续写入，保存 before/after/用户新内容和版本；定位服务端已应用范围。能用唯一反向 patch 且用户确认时再恢复，否则交付三方合并方案，不直接 overwrite。
- **验收证据：** 明确列出预期与非预期 hunks、对应版本和当前远端 hash；任何恢复操作都能通过新的 fetch 证明目标段与非目标段状态。
