# Feedback Loop

Use this reference when the user mentions a previous goal, execution result,
failure, dissatisfaction, "上次", "之前", "效果不好", or similar feedback.

## Feedback Extraction

Before drafting the next goal, extract:

```text
有效：...
无效：...
太重：...
缺失：...
错误假设：...
下次调整：...
```

If no prior feedback is provided, state that explicitly instead of inventing it.

## Feedback Adjustment Field

Generated goals should include:

```text
反馈调整：未提供上次执行反馈，本次不做反馈修正。
```

or, when feedback exists:

```text
反馈调整：基于上次执行结果，本次减少研究深度 / 增加证据门槛 / 调整任务包 / 缩短输出 / 改变停止标准。
```

Feedback should change the next goal only when it has practical implications.
Do not overfit to a single complaint when the underlying task changed.
