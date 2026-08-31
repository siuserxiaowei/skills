# Compiler Runtime

Read this reference only when a user asks for an executable contract,
deterministic validation, a Goal Compiler demo, or execution of the first safe
step. Ordinary `/goal` drafting does not need the runtime.

## Three responsibility layers

1. **Agent / Skill — semantics.** Interpret the request and produce the full
   semantic JSON: Smart Router, Strategy Gate, metric, counter-evidence, kill
   criteria, tool/evidence gate, goal plan, task-specific acceptance, and the
   proposed first step. The CLI never substitutes a website template for a
   coding or SEO request.
2. **Human — decision.** Inspect sources when research is required; edit the
   exact metric and scope; explicitly acknowledge metric, evidence, action, and
   execution scope. A pending/example/test record is not a human approval.
3. **CLI — deterministic gate and dispatch.** Serialize the Agent payload,
   validate identity/domain/evidence, bind approval to every execution field,
   and dispatch one whitelisted text artifact plus fixed checks. It is not an
   LLM and does not execute generated Python.

The recorded contest fixture has both `live_ai_claimed:false` and
`liveAiClaimed:false`. This makes the provenance easy to audit; it must not be
described as a live model call.

## Semantic input

`compile` requires `--semantic-input`. Use
`contest/demo-fixtures/semantic-input.demo.json` as a field-level reference,
not as a universal website template. Important invariants:

- `request` must exactly match the CLI request after whitespace normalization.
- `smart_router.task_type` must match the request domain and a supported action.
- `success_metrics[].measurement` needs an objective method plus numeric or
  boolean targets; the chosen metric's `evidence_path` must equal the first
  step's report path.
- `first_step.action`, artifact kind, suffix, media type, validators, output
  path, and domain acceptance must match one immutable action policy.
- an Agent result records a transcript reference; deterministic and test
  fixtures explicitly label their mode and do not claim live AI.

Compile without execution:

```bash
python3 scripts/goal_compiler.py compile \
  --request-file contest/demo-fixtures/request.txt \
  --semantic-input contest/demo-fixtures/semantic-input.demo.json \
  --output /tmp/goal-compiler-draft
```

The output is intentionally pending. For a research task, attach a real
evidence bundle first:

```bash
python3 scripts/goal_compiler.py attach-evidence \
  /tmp/goal-compiler-draft/goal-contract.json \
  --evidence /path/to/evidence.json \
  --output /tmp/goal-with-evidence.json
```

Each required claim type must reference the configured minimum number of
recorded independent sources. Source records include ID, title, URL, source
type, tool/channel, and access limitation. Missing evidence blocks approval.

## Human approval and payload binding

The generated `human-review.pending.json` is only a form. A real reviewer must
fill a separate record with `decision: approved`, a reviewer identity, a
concrete reason, the exact metric override if any, and all four acknowledgements
set to true. Do not sign on the user's behalf.

```bash
python3 scripts/goal_compiler.py apply-review \
  /tmp/goal-with-evidence.json \
  --review /path/to/actual-human-review.json \
  --output /tmp/goal-reviewed.json
```

`apply-review` computes `approved_payload_sha256` over the schema, contract
identity, request, semantic provenance, router, assumptions, strategy, tool
gate, evidence, goal plan, and first step. `validate` and `execute` recompute it.
Changing the request, metric, evidence, action, artifact, checks, content, or
any other execution field after approval invalidates the approval.

```bash
python3 scripts/goal_compiler.py validate /tmp/goal-reviewed.json
python3 scripts/goal_compiler.py execute /tmp/goal-reviewed.json \
  --output /tmp/goal-compiler-first-output
```

Every CLI file target and output directory is refuse-existing. Choose a new
path instead of overwriting prior evidence.

## Action policies

The current whitelist is deliberately small:

- website/app: `write_static_hypothesis_page` → one `.html` file and HTML
  structure/CTA/hypothesis/no-external-URL checks
- coding: `write_python_regression_fixture` → one `.py` file and syntax plus
  regression-marker checks; the generated code is not run
- SEO/competitor/growth/docs/mixed: `write_markdown_validation_brief` → one
  `.md` file and heading/source-reference checks

The execution report records the actual action, handler, artifact kind, content
hash, approval payload hash, and every check result.

## Recorded demo

```bash
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
```

The fixed demo proves four honest states: an Agent-shaped semantic fixture is
recorded, a research/evidence precondition fails, a subjective metric variant
fails, and the exact human approval remains pending. It writes two
`validator.FAIL.log` files and no `validator.PASS.log`; execution is not
attempted. Use `contest/forward-test-prompt.txt` for a real Agent forward test,
and preserve that run's transcript and JSON separately.

## Failure rules

- Reject missing semantic input, unsupported or mismatched domains, unknown
  actions, incompatible artifact/check policies, vague statements, subjective
  methods, absent thresholds, and metric/evidence/action mismatch.
- Reject research-required approval without source-backed evidence.
- Reject request-hash, contract-ID, semantic-hash-format, review-ID, or approved
  payload inconsistencies.
- `execute` must not create its output directory when strict validation fails.
- Never imply that research, market validation, form submission, deployment,
  code execution, or another external side effect happened when it did not.
