# Output Compression

Use this reference to keep generated goals proportionate. Smart Router chooses
the output length; this reference defines what each length means.

## Output Lengths

```text
短版：只保留决策字段、核心 /goal、验证方式、停止标准、暂停条件。
标准版：默认。保留决策字段、完整 /goal、任务包/领域包、工具栈、质量门槛、边界和停止条件。
完整版：用于深度研究、高风险决策或用户明确要求。包含标准版加可选调整、风险清单、证据表结构和下一阶段 goal。
```

## Compression Field

Generated goals should include:

```text
输出长度：短版 / 标准版 / 完整版
```

Do not produce a long goal by default. Standard is the default for research
tasks; short is preferred for local execution; full is only for justified high
uncertainty, high risk, or explicit user request.
