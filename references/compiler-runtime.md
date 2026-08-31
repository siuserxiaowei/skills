# Compiler Runtime

Read this reference only when a user asks for an executable contract, a Goal
Compiler demo, deterministic validation, or execution of the first safe step.
Ordinary `/goal` drafting does not need the runtime.

## Separation of Responsibility

Goal Compiler uses four distinct roles:

1. **Agent / AI judgment** interprets the request and proposes the Smart Router,
   Strategy Gate, measurable metric, disconfirming evidence, kill criteria,
   tool/evidence gate, and first safe step.
2. **Deterministic compiler** serializes those decisions into a versioned JSON
   contract and a readable `/goal`.
3. **Human reviewer** replaces subjective metrics, confirms the intended scope,
   and signs the review record.
4. **Deterministic executor** validates the approved contract and creates only
   the first explicitly allowed artifact plus a check report.

Do not describe the Python CLI as an LLM. The agent supplies semantic judgment;
the CLI supplies reproducibility, gates, evidence paths, and exit codes.

## Contract Requirements

The contract must include:

- request text and a stable request hash
- task type, maturity, risk, external-information need, and routing decision
- problem reframe and smallest bet
- success metrics with a measurement method, numeric or boolean targets, and an
  evidence path
- disconfirming evidence with thresholds and responses
- kill criteria with thresholds and explicit stop actions
- permitted tools, authorization boundaries, evidence requirements, and blocked
  claims
- a safe relative path for the first artifact and at least three checks
- human decision, reviewer identity, changed fields, and sign-off state

The same request and review input should produce byte-stable JSON and HTML. Do
not add wall-clock timestamps to deterministic artifacts.

## CLI Flow

Compile a draft:

```bash
python3 scripts/goal_compiler.py compile \
  --request-file contest/demo-fixtures/request.txt \
  --output /tmp/goal-compiler-draft
```

The draft remains `PENDING HUMAN SIGN-OFF`. Edit the generated review template
or provide another explicit review record, then apply it:

```bash
python3 scripts/goal_compiler.py apply-review \
  /tmp/goal-compiler-draft/goal-contract.json \
  --review contest/demo-fixtures/human-review.json \
  --output /tmp/goal-compiler-reviewed.json
```

Validate and execute:

```bash
python3 scripts/goal_compiler.py validate /tmp/goal-compiler-reviewed.json
python3 scripts/goal_compiler.py execute /tmp/goal-compiler-reviewed.json \
  --output /tmp/goal-compiler-first-output
```

Run the fixed contest demo:

```bash
python3 scripts/goal_compiler.py demo --output /tmp/goal-compiler-demo
```

The demo must prove all four states: vague metric `FAIL`, human metric patch,
strict `PASS`, and a real first artifact with `execution-report.json`.

## Failure Rules

- `validate` returns non-zero for vague metrics such as `好看`, missing numeric
  or boolean thresholds, absent counter-evidence, absent kill criteria, unsafe
  paths, or missing human approval.
- `execute` must not create its output directory when strict validation fails.
- Existing output directories are never overwritten; choose a new path.
- A first-step artifact must not imply that external research, market demand,
  form submission, deployment, or another side effect has happened when it has
  not.
