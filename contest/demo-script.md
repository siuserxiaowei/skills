# 70-second Demo Script

## 0–7s — Pain

Visual: `goal-compiler-board-1920x1080.png`.

Voice: “多数 AI 需求不是执行不了，而是没有定义什么叫成功、什么证据会推翻它、什么时候应该停。”

## 7–16s — Agent semantic result

Visual: run `python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-video`; open `01-agent-result/semantic-input.snapshot.json` and `router.json`.

Voice: “输入只有：给我做个 AI 网站，越快越好。Agent 层负责语义：网站任务、模糊阶段、中风险、需要外部证据。固定录制 fixture 不冒充实时 AI。”

## 16–26s — Strategy Gate

Visual: `01-agent-result/strategy-gate.json`; highlight `problem_reframe`, metric, `disconfirming_evidence`, and `kill_criteria`.

Voice: “语义结果带着问题重构、最小验证、反证和 kill criteria 进入 CLI；CLI 不再自己硬编一套网站答案。”

## 26–38s — Evidence precondition

Visual: `01-agent-result/validator.FAIL.log`; highlight missing `evidence_bundle.sources` and `claims`.

Voice: “这是研究型任务，所以没有真实来源就必须 FAIL。没有来源的市场判断，不能被人工审批或执行。”

## 38–48s — Objective metric gate

Visual: `02-subjective-metric/strategy-gate.json` beside `validator.FAIL.log`; highlight “看起来足够好看” and “主观感受”.

Voice: “我再放入一个主观变体：看起来足够好看。Statement 和 measurement method 都被严格拒绝，只写 FAIL.log。”

## 48–59s — Human remains the decision maker

Visual: `03-human-pending/human-review.pending.json`; highlight false acknowledgements and pending decision.

Voice: “精确指标、证据确认和执行范围必须留给真人。本次记录是 pending，所以不会凭空写 PASS，也不会执行。”

## 59–70s — Tamper-proof boundary

Visual: `tests/test_goal_compiler.py` tamper test, then `PROVENANCE.md`.

Voice: “真人批准时，所有执行字段会绑定一个 SHA-256。审批后改请求、指标、证据、动作或产物都会被阻断。Agent 负责语义，人负责决定，CLI 负责确定性门禁。”

## Capture note

The fixed fixture sets `liveAiClaimed:false`; do not call it a live model run.
If the preserved forward-test is shown, label it `agent_result + human_pending`.
