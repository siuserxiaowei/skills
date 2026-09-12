#!/usr/bin/env python3
"""Ensure known-bad goal drafts fail validation for the intended reasons."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_xiaowei_goal.py"

CASES = [
    ("tests/invalid-goals/missing-smart-router.zh.txt", "decision summary"),
    ("tests/invalid-goals/missing-agent-reach-doctor.zh.txt", "agent-reach doctor"),
    ("tests/invalid-goals/missing-quality-gate.zh.txt", "quality gate"),
    ("tests/invalid-goals/overclaims-full-internet.zh.txt", "unsafe vague phrase"),
    ("tests/invalid-goals/missing-deep-research.zh.txt", "stage 2 deep research"),
    ("tests/invalid-goals/missing-business-priority.zh.txt", "business priority"),
    ("tests/invalid-goals/missing-strategy-gate.zh.txt", "strategy gate"),
    ("tests/invalid-goals/incomplete-strategy-gate.zh.txt", "kill criteria"),
    ("tests/invalid-goals/missing-self-evolution-boundary.zh.txt", "self-evolution"),
    ("tests/invalid-goals/missing-daily-evolution-schedule.zh.txt", "daily evolution"),
]


def main() -> int:
    failures: list[str] = []
    for relative_path, expected in CASES:
        path = ROOT / relative_path
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        combined_output = f"{result.stdout}\n{result.stderr}"
        if result.returncode == 0:
            failures.append(f"{relative_path}: expected failure but validation passed")
            continue
        if expected.lower() not in combined_output.lower():
            failures.append(f"{relative_path}: expected `{expected}` in validator output\n{combined_output}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("Negative validator tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
