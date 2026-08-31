# Provenance

## What this repository claims

This repository claims authorship of its concrete implementation and of the
following combined mechanism in `v0.12.0`:

1. compile a vague request into a versioned, machine-readable contract
2. expose Smart Router and Strategy Gate decisions instead of hiding defaults
3. require measurable success metrics, disconfirming evidence, kill criteria,
   tool/evidence gates, and a first safe step
4. make a subjective metric fail deterministically
5. require a recorded human metric patch and explicit sign-off
6. execute only the approved first step and emit a machine check report

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
- 2026-08-31: `v0.12.0` added the executable Goal Compiler contract, strict
  human-review gate, first-step executor, behavior tests, and contest evidence
  pack.

Git history remains intact so these statements can be audited. No history was
rewritten to obscure inspiration or third-party contribution.

## AI / deterministic / human boundary

- The installed Agent Skill and the invoking agent perform semantic judgment.
- The Python CLI serializes, validates, and executes deterministic rules. It is
  not described as an LLM.
- A human reviewer owns the measurable metric change and approval decision.
- The bundled fixed demo is a deterministic reference fixture and has
  `liveAiClaimed: false`. A separate forward-test prompt is supplied so a real
  Codex/Claude session can invoke `SKILL.md` without confusing that run with the
  bundled fixture.

## Assets

All contest HTML, CSS, copy, JSON fixtures, and diagrams in this repository were
created for this project. They use system fonts and contain no external images,
logos, characters, audio, video, or font files. See `ASSET_RIGHTS.csv`.

## License

The repository is licensed under MIT. Inspiration and optional external tools
are documented in `THIRD_PARTY_NOTICES.md`; no third-party source code is
bundled by the Goal Compiler runtime.
