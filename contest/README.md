# Goal Compiler Contest Pack

Product name: **Goal Compiler｜需求编译器**

Track: **VibeWork**

Repository: https://github.com/siuserxiaowei/xiaowei-goal

Live page: https://siuserxiaowei.github.io/xiaowei-goal/

## One-sentence product

It compiles a vague request into a machine-readable goal with measurable
success, disconfirming evidence, kill criteria, tool/evidence gates, human
sign-off, and a real first safe output.

## Proven demo chain

```text
“给我做个 AI 网站，越快越好”
  → router.json + strategy-gate.json
  → subjective metric “好看”
  → validator.FAIL.log
  → human-metric-patch.json
  → validator.PASS.log
  → first-output/index.html
  → execution-report.json
```

Reproduce it:

```bash
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
open /tmp/goal-compiler-demo/walkthrough.html
```

The command refuses to overwrite an existing output directory.

## Artifact index

- `demo-output/walkthrough.html`: single-page, video-ready overview.
- `demo-output/01-invalid-draft/router.json`: task type, maturity, risk, and external-information route.
- `demo-output/01-invalid-draft/strategy-gate.json`: invalid contract state with metric `好看`.
- `demo-output/01-invalid-draft/validator.FAIL.log`: actual negative-gate log.
- `demo-output/human-metric-patch.json`: explicit human change and approval.
- `demo-output/02-reviewed-contract/strategy-gate.json`: corrected measurable gate.
- `demo-output/02-reviewed-contract/validator.PASS.log`: actual pass log.
- `demo-output/02-reviewed-contract/goal.md`: executable human-readable goal.
- `demo-output/03-first-output/index.html`: real first output.
- `demo-output/03-first-output/execution-report.json`: six deterministic checks.
- `demo-output/demo-report.json`: whole-chain machine report.

## AI, human, and CLI boundary

- Agent/Skill: semantic compilation, default assumptions, routing, strategy,
  counter-evidence, and tool choice.
- Human: changes the subjective metric and explicitly approves the contract.
- CLI: deterministic serialization, validation, exit codes, safe execution, and
  evidence files.

The bundled fixed fixture is not presented as a live model call. Its metadata
sets `liveAiClaimed` to `false`. Use `forward-test-prompt.txt` for an independent
Codex/Claude invocation of the Skill, and preserve that run's own transcript if
it is shown in the final video.

## Originality boundary

The submission claims the concrete implementation and combined mechanism, not
the invention of goals, prompts, strategy gates, human review, validators, or
compiler metaphors. See `../PROVENANCE.md`, `../SOURCES.md`, and
`../THIRD_PARTY_NOTICES.md`.

## Submission assets

- `weibo-copy.md`: posting draft.
- `demo-script.md`: 70-second voiceover and exact artifact sequence.
- `shot-list.md`: capture checklist.
- `media-manifest.json`: machine-readable media plan.
- `submission.json`: factual claims and provenance flags.
- `goal-compiler-board-1920x1080.png`: ready-to-use 16:9 overview board.
