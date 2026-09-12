#!/usr/bin/env python3
"""Score Xiaowei goal drafts for completeness and proportionality."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from validate_xiaowei_goal import lint_text


MAX_STANDARD_LENGTH = 7000

CHECKS = {
    "business application": [r"页面", r"功能", r"内容", r"增长", r"实现目标", r"business application"],
    "strategy gate": [r"策略判断", r"Strategy Gate", r"反证", r"kill criteria"],
    "priority recommendation": [r"优先级判断", r"Business Priority"],
    "pause rule": [r"暂停条件", r"Pause Conditions?"],
    "evidence": [r"证据", r"来源", r"验证方式", r"evidence", r"source", r"Verification"],
}


def evaluate_text(text: str, source: str) -> tuple[int, list[str]]:
    issues = lint_text(text, source)
    warnings: list[str] = []

    for name, patterns in CHECKS.items():
        if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            warnings.append(f"{source}: missing evaluation signal `{name}`")

    if "输出长度：标准版" in text and len(text) > MAX_STANDARD_LENGTH:
        warnings.append(f"{source}: standard output may be too long")

    score = 100 - (len(issues) * 10) - (len(warnings) * 3)
    return max(score, 0), issues + warnings


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: evaluate_goal_output.py <file> [<file> ...]", file=sys.stderr)
        return 2

    failed = False
    for raw_path in argv[1:]:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"{path}: cannot read file: {exc}", file=sys.stderr)
            failed = True
            continue

        score, findings = evaluate_text(text, str(path))
        print(f"{path}: score={score}")
        for finding in findings:
            print(f"  - {finding}")
        if score < 80 or any("missing smart field" in finding for finding in findings):
            failed = True

    if failed:
        return 1

    print("Xiaowei goal output evaluation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
