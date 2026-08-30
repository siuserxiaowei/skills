# Lark Minutes｜案例与详细说明

命令结构按本机 `lark-cli 1.0.71` 验证。妙记逐字稿属于敏感会议资料，示例仅在工作区内保存所需产物，并明确区分原始逐字稿与 AI 派生内容。

## 使用说明

- **何时使用：** 需要搜索妙记、提取带逐字证据的行动项，或处理 artifact 缺失/权限差异时读取。
- **准备/输入：** 准备 minute token 或唯一搜索条件、profile/user、所需 artifact、输出目录与最小披露范围。
- **执行方式：** 先 search 消歧，再按需 detail 下载；把 summary/todo/chapter/transcript 分源处理，写操作另行确认。
- **验收/边界：** 用 minute 元数据、artifact 状态、文件大小和逐字时间点验收；AI summary 不能冒充原话，整理不授权改 speaker/transcript。

## 正向案例

### 从妙记整理带原始依据的行动项

- **用户请求：** “从 8 月 28 日‘支付重构周会’妙记里整理行动项，每条标出说话人和时间点。”
- **准备信息/输入：** profile 为 `work`、user 身份有权访问；若无 token，以标题、日期和参与人唯一定位；输出目录为 `evidence/minutes`；只需要 summary、todo、chapter 与 transcript。
- **处理：**

```bash
lark-cli minutes +search --profile work --as user --query '支付重构周会' --start 2026-08-28 --end 2026-08-29 --participant-ids me --page-size 15 --format json
lark-cli minutes +detail --profile work --as user --minute-tokens <minute_token> --summary --todo --chapter --transcript --output-dir evidence/minutes --format json
```

将服务端 todo 与逐字稿逐项核对；负责人/截止日没有原文支持时标为推断或未知，不补写事实。
- **预期输出：** 一份行动项清单，每项含内容、负责人/未知、截止日/未知、说话人、时间点和来源类型。
- **验收证据：** minute token、会议标题/时间、artifact 状态、逐字稿文件路径与大小可追溯；每条行动项能定位原始时间点，AI summary 文字不会伪装成逐字引用。

## 边界案例

### 整理不授权修改妙记产物

- **用户请求：** “整理一下，顺便把说话人和原文里写错的词都改掉。”
- **边界判断：** 整理是只读派生工作；speaker/word/summary/todo 更新会改变共享会议产物，命中范围和影响不同。
- **处理：** 先交付只读整理；另列每个拟修改词、上下文、命中次数和 speaker 映射，获得对象级确认后才规划写操作。
- **验收证据：** 只读阶段 minute 的标题、speaker 映射、transcript revision 和服务端 todo 保持不变；交付中明确哪些更正未执行。

## 失败与恢复

### 逐字稿不可见但摘要可见

- **场景：** `+detail` 返回 summary/todo，但 transcript artifact 为未生成或无权限。
- **处理与恢复：** 区分生成中、缺 scope 和文档权限；生成中只做有界状态复查，无权限时说明申请权限路径。允许交付摘要级结果，但取消逐字引用和说话人时间点承诺。
- **验收证据：** 报告每个 artifact 的独立状态、minute token 和查询时间；输出标题标注“仅基于 AI summary/todo”，覆盖范围不宣称为完整逐字稿。
