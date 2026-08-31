# Goal Compiler Contest Pack

Product: **Goal Compiler｜需求编译器**

Track: **VibeWork**

Repository: https://github.com/siuserxiaowei/xiaowei-goal

Live page: https://siuserxiaowei.github.io/xiaowei-goal/

## One-sentence product

Agent/Skill turns a vague request into task-specific semantics; a human owns
the exact metric and approval; a deterministic CLI enforces sources, identity,
saved-semantic/review consistency, and one whitelisted first-step dispatch.

## Recorded demo chain

```text
“给我做个 AI 网站，越快越好”
  → complete recorded semantic fixture (`liveAiClaimed:false`)
  → router.json + strategy-gate.json
  → research evidence missing → validator.FAIL.log
  → subjective metric variant → validator.FAIL.log
  → exact metric + execution approval → HUMAN PENDING
  → execution not attempted
```

Reproduce it:

```bash
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
open /tmp/goal-compiler-demo/walkthrough.html
```

The command refuses an existing output directory. It writes no `PASS.log` and
does not pretend that a fixture is a human signature or live model call.

## Artifact index

- `demo-output/walkthrough.html`: video-ready four-state walkthrough.
- `demo-output/01-agent-result/semantic-input.snapshot.json`: complete recorded
  semantic payload supplied to the CLI.
- `demo-output/01-agent-result/router.json`: task, maturity, risk, and evidence
  route.
- `demo-output/01-agent-result/strategy-gate.json`: metric, counter-evidence,
  and kill criteria.
- `demo-output/01-agent-result/validator.FAIL.log`: actual source + human gate
  failure.
- `demo-output/02-subjective-metric/validator.FAIL.log`: actual objective-metric
  failure.
- `demo-output/03-human-pending/human-review.pending.json`: editable form, not a
  signature.
- `demo-output/demo-report.json`: machine-readable status and provenance.
- `demo-fixtures/website-first-output.html`: proposed page content bound into
  the semantic payload; it is not claimed as executed in the fixed demo.
- `forward-test/transcript.md` and `forward-test/semantic-result.json`: preserved
  Agent forward-test result, still `human_pending`.
- `test-evidence/coding-first-output/`: real deterministic CLI dispatch under a
  `synthetic_test` approval that is accepted only for `test_fixture` contracts;
  it proves cross-domain behavior, not real human approval or a production fix.
  The checked directory is a preserved copy; its execution report records the
  actual approved `/private/tmp/.../first-output` target.
- `goal-compiler-board-1920x1080.png`: 16:9 overview board.

## Three-layer boundary

- **Agent/Skill:** semantic compilation and default assumptions. A real Agent
  run must preserve its transcript; deterministic fixtures say so explicitly.
- **Human:** source review, exact metric edits, and explicit execution approval.
  The repository does not sign on the reviewer's behalf.
- **CLI validator/executor:** deterministic saved-semantic, source and
  review/current-payload consistency gates; approved-workspace plus relative
  output derivation; task/action/artifact/check whitelist; refuse-existing
  writes. Its unkeyed SHA-256 and review ID are not signatures and do not
  authenticate a reviewer.

Cross-domain regressions prove that a coding request cannot inherit CTA,
`15-25 个候选来源`, IdeaSignal, or the website action. The coding test
dispatches a Python regression fixture and records the actual handler/checks.

## Originality boundary

The submission claims its concrete implementation and this combined mechanism,
not the invention of goals, prompts, strategy gates, human review, validators,
or compiler metaphors. See `../PROVENANCE.md`, `../SOURCES.md`,
`../THIRD_PARTY_NOTICES.md`, and `../ASSET_RIGHTS.csv`.

## Submission assets

- `weibo-copy.md`: posting draft.
- `demo-script.md`: 70-second voiceover.
- `shot-list.md`: capture checklist.
- `media-manifest.json`: machine-readable edit plan.
- `submission.json`: factual claims and provenance flags.
