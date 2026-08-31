#!/usr/bin/env python3
"""Run a deterministic daily evolution audit for xiaowei-goal."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHECK_COMMANDS = [
    ("validate examples", ["python3", "scripts/validate_xiaowei_goal.py", *sorted(str(path) for path in (ROOT / "examples").glob("*.txt"))]),
    ("evaluate examples", ["python3", "scripts/evaluate_goal_output.py", *sorted(str(path) for path in (ROOT / "examples").glob("*.txt"))]),
    ("negative tests", ["python3", "scripts/test_validator_negative_cases.py"]),
    ("goal compiler tests", ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]),
    ("contest evidence", ["python3", "scripts/validate_contest_pack.py"]),
    ("installed self-check", ["python3", "scripts/check_installed_skill.py", "."]),
    ("manifest json", ["python3", "-m", "json.tool", "manifest.json"]),
    ("README topics", ["python3", "scripts/check_readme_topics.py"]),
    ("python compile", ["python3", "-m", "py_compile", *sorted(str(path) for path in (ROOT / "scripts").glob("*.py"))]),
    ("diff whitespace", ["git", "diff", "--check"]),
]

REQUIRED_MARKERS = {
    "self-evolution reference": ["references/self-evolution.md"],
    "daily workflow": [".github/workflows/daily-evolution.yml"],
    "daily audit script": ["scripts/daily_evolution_audit.py"],
    "release consistency script": ["scripts/check_release_consistency.py"],
    "strategy gate reference": ["references/strategy-gate.md"],
    "compiler runtime reference": ["references/compiler-runtime.md"],
    "goal compiler CLI": ["scripts/goal_compiler.py"],
    "self-evolution example": ["examples/self-evolution-goal.zh.txt"],
    "daily evolution example": ["examples/daily-self-evolution-goal.zh.txt"],
}


def run_check(name: str, command: list[str]) -> dict[str, str | int | bool]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    output = f"{result.stdout}\n{result.stderr}".strip()
    return {
        "name": name,
        "command": " ".join(command),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": output[-2000:],
    }


def read_manifest() -> dict[str, object]:
    return json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))


def marker_findings() -> list[str]:
    findings: list[str] = []
    for name, paths in REQUIRED_MARKERS.items():
        for relative_path in paths:
            if not (ROOT / relative_path).exists():
                findings.append(f"Missing {name}: `{relative_path}`")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = read_manifest()
    version = str(manifest.get("version", ""))
    if f"version-{version}-blue" not in readme:
        findings.append("README version badge does not match manifest version")

    workflow_path = ROOT / ".github" / "workflows" / "daily-evolution.yml"
    if workflow_path.exists():
        workflow = workflow_path.read_text(encoding="utf-8")
        if "schedule:" not in workflow or "cron:" not in workflow:
            findings.append("Daily evolution workflow is missing a cron schedule")
        if "daily_evolution_audit.py" not in workflow:
            findings.append("Daily evolution workflow does not run daily_evolution_audit.py")
        if "issues: write" not in workflow:
            findings.append("Daily evolution workflow cannot create/update audit issues")

    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not re.search(r"每日进化|daily evolution", skill, flags=re.IGNORECASE):
        findings.append("SKILL.md does not mention daily evolution")
    if not re.search(r"策略判断|Strategy Gate|strategy-gate", skill, flags=re.IGNORECASE):
        findings.append("SKILL.md does not mention Strategy Gate")

    return findings


def render_report(checks: list[dict[str, str | int | bool]], findings: list[str]) -> str:
    failed_checks = [check for check in checks if not check["passed"]]
    action_required = bool(failed_checks or findings)
    lines = [
        "# Daily Evolution Audit",
        "",
        f"Action required: {'yes' if action_required else 'no'}",
        "",
        "## Structural Findings",
    ]

    if findings:
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("- No structural drift detected.")

    lines.extend(["", "## Validation Checks"])
    for check in checks:
        status = "passed" if check["passed"] else "failed"
        lines.append(f"- {check['name']}: {status}")
        if not check["passed"]:
            lines.append("")
            lines.append("```text")
            lines.append(str(check["output"]))
            lines.append("```")

    lines.extend(
        [
            "",
            "## Next Step",
            "If action is required, run `用 xiaowei-goal 执行一次完全自动化自我进化` in an agent session.",
            "The scheduled workflow audits and creates a handoff issue; it does not perform unattended code rewrites without an agent context.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_github_output(path: str | None, action_required: bool) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as output_file:
        output_file.write(f"action_required={'true' if action_required else 'false'}\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default="", help="Path to write the markdown report")
    parser.add_argument("--github-output", default="", help="Path from GITHUB_OUTPUT")
    parser.add_argument("--check-release", action="store_true", help="Check manifest version against tag/release")
    args = parser.parse_args(argv[1:])

    checks = [run_check(name, command) for name, command in CHECK_COMMANDS]
    if args.check_release:
        checks.append(
            run_check(
                "release consistency",
                ["python3", "scripts/check_release_consistency.py", "--require-github-release"],
            )
        )
    findings = marker_findings()
    report = render_report(checks, findings)
    action_required = any(not check["passed"] for check in checks) or bool(findings)

    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    else:
        print(report)

    write_github_output(args.github_output, action_required)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
