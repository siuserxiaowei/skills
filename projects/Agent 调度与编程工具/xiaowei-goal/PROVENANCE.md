# Provenance

## What this repository claims

This repository claims authorship of its concrete implementation and of the
following combined mechanism in `v0.13.0`:

1. require a complete Agent-authored semantic input instead of hiding
   task-specific judgment inside the deterministic CLI
2. reject request/domain/action/artifact/check mismatches, including website
   leakage into coding work
3. require measurable success metrics, disconfirming evidence, kill criteria,
   tool/evidence gates, and a task-specific first safe step
4. block research-required approval until source-backed evidence is recorded
5. save the complete semantic input, reconstruct its derived fields, and record
   an unkeyed `approved_payload_sha256` for review/current-payload drift checks
6. dispatch only a whitelisted text artifact and emit the actual handler and
   check results, while refusing existing output paths

The implementation is in `scripts/goal_compiler.py`; behavior tests are in
`tests/test_goal_compiler.py`; the fixed demo evidence is in
`contest/demo-output/`.

This repository does **not** claim that goal-setting, prompt refinement,
strategy gates, human review, validators, or compiler metaphors were invented
here. It does not claim global, category, or idea-level originality.

## Timeline

- 2026-06-11: the referenced public inspiration repository was published at
  commit [`f29e0189f2ea03392c50b4f1c7230886bd838a13`](https://github.com/joeseesun/qiaomu-goal-meta-skill/commit/f29e0189f2ea03392c50b4f1c7230886bd838a13).
- 2026-06-14: this repository began at commit
  `ddbea3ce5c21cbe9228a32c57bd04decc8b4b499`, with an explicit attribution to
  that public case.
- 2026-06-14 through 2026-06-17: this repository added its own research-first
  routing, Agent Reach/tool routing, evidence quality gate, task/domain packs,
  Smart Router, Strategy Gate, business priority, feedback, output compression,
  validators, negative fixtures, and release guards.
- 2026-08-31: `v0.12.0` added the first executable Goal Compiler contract,
  human-review gate, first-step executor, behavior tests, and contest pack.
- 2026-08-31: `v0.13.0` separated Agent semantics from deterministic CLI work,
  added cross-domain rejection, research-evidence preconditions, approval
  review/payload consistency checks, refuse-existing writes, and an honest
  human-pending demo.
- 2026-08-31: subsequent audit hardening saved the full semantic snapshot,
  bound the execution workspace, verified artifact source IDs and configured
  source record fields, and replaced security overclaims with the exact
  unkeyed-digest boundary.

Git history remains intact so these statements can be audited. No history was
rewritten to obscure inspiration or third-party contribution.

## AI / deterministic / human boundary

- The installed Agent Skill and the invoking agent perform semantic judgment.
- The Python CLI serializes, validates, and executes deterministic rules. It is
  not described as an LLM.
- A human reviewer owns the exact measurable metric, evidence acceptance, and
  approval decision. Pending and synthetic test fixtures are never presented as
  real human sign-off.
- `approved_payload_sha256` and `review_id` are deterministic, unkeyed
  consistency values. They detect drift while the saved review record remains
  fixed; they are not digital signatures and do not authenticate a reviewer or
  stop someone who can rewrite both the payload and the consistency values.
- The bundled fixed demo is a deterministic reference fixture and has
  `liveAiClaimed: false`; it writes only FAIL logs and stops before execution.
- A separate preserved forward-test transcript and JSON are labelled
  `agent_result + human_pending`; they prove a Skill invocation, not a human
  approval or market-evidence collection.

## Assets

All contest HTML, CSS, copy, JSON fixtures, and diagrams in this repository were
created for this project. Test fixtures are explicitly labelled synthetic. The
visual assets use system fonts and contain no external images, logos,
characters, audio, video, or font files. See `ASSET_RIGHTS.csv`.

## License

The repository is licensed under MIT. Inspiration and optional external tools
are documented in `THIRD_PARTY_NOTICES.md`; no third-party source code is
bundled by the Goal Compiler runtime.
