# 70-second Demo Script

## 0–7s — Pain

Visual: `demo-output/walkthrough.html`, hold on the headline.

Voice: “多数 AI 需求不是执行不了，而是一开始就没定义什么叫成功、什么证据会推翻它、什么时候应该停。”

## 7–15s — Raw input and Smart Router

Visual: terminal runs `python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-video`; then open `01-invalid-draft/router.json`.

Voice: “输入只有一句：给我做个 AI 网站，越快越好。Goal Compiler 先判断它是模糊的网站任务、中风险、需要外部证据，策略是先验证需求。”

## 15–25s — Strategy Gate

Visual: open `01-invalid-draft/strategy-gate.json`; highlight `problem_reframe`, `disconfirming_evidence`, and `kill_criteria`.

Voice: “它把目标编译成问题重构、最小验证、反证和 kill criteria，不让一个模糊想法自动膨胀成完整产品。”

## 25–34s — Real failure

Visual: open `01-invalid-draft/validator.FAIL.log`; zoom on `vague metric 好看 is not measurable`.

Voice: “我故意把成功指标写成‘好看’。Validator 真实返回非零退出码：没有阈值、没有证据路径、没有人工签字，全部拒绝。”

## 34–45s — Human metric patch

Visual: split view `human-metric-patch.json` and `02-reviewed-contract/strategy-gate.json`; highlight 60 minutes, 1 page, 1 CTA, assumption label.

Voice: “人必须介入，把‘好看’改成六十分钟内生成一页、一个 CTA、一个假设标记，并确认测量方法和证据文件。”

## 45–52s — Strict pass

Visual: `02-reviewed-contract/validator.PASS.log`.

Voice: “现在 schema、指标、反证、终止条件、工具边界和人工签字全部 PASS。”

## 52–64s — First real output

Visual: open `03-first-output/index.html`, scroll from hero to CTA and the three cards.

Voice: “它不再交付另一份方案，而是真正执行第一步：生成一个明确标注为待验证假设的页面，没有登录、表单提交或外部素材。”

## 64–70s — Evidence and boundary

Visual: `03-first-output/execution-report.json`, then `PROVENANCE.md`.

Voice: “六项机器检查全部通过。Agent 负责语义判断，人负责批准，CLI 负责确定性门禁。来源、原创边界和资产权利都在仓库里。”

## Capture note

The fixed fixture itself is deterministic and uses `liveAiClaimed: false`.
If a live Codex/Claude call is added to the edit, show its real transcript and
use `forward-test-prompt.txt`; do not label the fixture as a live model output.
