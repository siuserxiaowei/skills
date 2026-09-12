# Self-Evolution

Use this reference when the user asks xiaowei-goal to evolve itself, improve
its own behavior, learn from feedback, or automatically update its repository.

This mode is automatic after explicit user trigger. Daily evolution can also
run as a scheduled GitHub Actions audit, but that audit only produces reports
and issue handoffs. It does not rewrite code without an agent session.

## Automatic Evolution Loop

Run the loop end to end without asking follow-up questions unless a pause
condition is hit:

1. Collect feedback signals from the user request, prior execution notes,
   examples, validator failures, README gaps, GitHub Actions logs, and release
   history.
2. Classify each signal as effective, ineffective, too heavy, missing,
   wrong assumption, or next adjustment.
3. Decide whether the change is worth doing with `business-priority.md`.
4. Propose the smallest testable change to SKILL, references, examples,
   validator, scripts, CI, or README.
5. Add or update at least one positive example or negative validator case for
   new behavior.
6. Edit only the allowed paths.
7. Run the full validation suite.
8. Commit, push, wait for CI, and create a semantic version release only when
   local validation and GitHub Actions pass.
9. Clean temporary work directories.

## Automation Boundary

Generated self-evolution goals must include:

```text
自动化边界：用户显式触发后自动收集反馈、修改允许路径、运行校验、提交、推送和发布；不是无人值守后台任务。
```

## Daily Evolution Cadence

When the user asks for daily evolution, add a scheduled workflow:

```text
.github/workflows/daily-evolution.yml
```

The workflow should:

- run daily with cron, default `0 1 * * *` for 09:00 Asia/Shanghai
- support `workflow_dispatch`
- run `python3 scripts/daily_evolution_audit.py`
- run `python3 scripts/check_release_consistency.py --require-github-release`
- upload the audit report as an artifact
- create or update a GitHub issue only when action is required
- avoid unattended code rewrites, commits, tags, and releases

The issue handoff should tell the next agent to run:

```text
用 xiaowei-goal 执行一次完全自动化自我进化
```

This is the safe daily loop: scheduled audit every day, full code evolution only
inside an explicit agent execution context.

## Allowed Paths

Default allowed paths:

```text
SKILL.md
README.md
manifest.json
agents/interface.yaml
.github/workflows/validate.yml
.github/workflows/daily-evolution.yml
references/
examples/
scripts/
tests/
```

Do not modify docs archives, user projects, local installed skill copies,
private files, credentials, production data, or unrelated repositories unless
the user explicitly requests that exact path.

## Required Gates

Before release, run:

```bash
python3 scripts/validate_xiaowei_goal.py examples/*.txt
python3 scripts/evaluate_goal_output.py examples/*.txt
python3 scripts/daily_evolution_audit.py --report /tmp/daily-evolution-report.md
python3 scripts/check_release_consistency.py
python3 scripts/test_validator_negative_cases.py
python3 scripts/check_installed_skill.py .
python3 -m json.tool manifest.json
python3 scripts/check_readme_topics.py
python3 -m py_compile scripts/*.py
git diff --check
```

Also validate YAML files when a workflow or interface file changes.

## Release Policy

- Use a semantic version bump when the skill behavior changes.
- Patch version for validation/doc/example fixes.
- Minor version for new behavior, references, scripts, or validator rules.
- Do not create a release when local checks or GitHub Actions fail.
- Tag the release at the same commit that passed CI.
- Daily scheduled audits do not create releases; they only create reports and issue handoffs.
- Daily scheduled audits must check that `manifest.json` version, `vX.Y.Z` git tag, and GitHub release are aligned.

## Rollback Policy

If the automated evolution produces a bad commit before release, fix forward or
revert only the commit created by the current run. If a release was already
created, create a corrective release; delete tags/releases only when the user
explicitly requests it.

## Pause Conditions

Pause before using credentials, cookies, tokens, paid services, production data,
private content, destructive commands outside temporary workdirs, broad file
deletion, legal/privacy-sensitive decisions, or any change outside the allowed
paths. If CI fails twice for the same reason, stop and report the blocker.

## Required Self-Evolution Goal Fields

Self-evolution goals should explicitly include:

- `自动化边界`
- `反馈来源`
- `允许修改路径`
- `评估方式`
- `验证方式`
- `发布规则`
- `回滚方式`
- `每日节拍` when daily evolution is requested
- `暂停条件`
