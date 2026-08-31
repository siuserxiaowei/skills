#!/usr/bin/env python3
"""Check whether the installed xiaowei-goal skill looks current."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


MIN_VERSION = (0, 12, 0)
DEFAULT_SKILL_DIR = Path.home() / ".agents" / "skills" / "xiaowei-goal"

REQUIRED_SKILL_PATTERNS = {
    "Agent Reach routing": [
        r"Agent Reach Routing",
        r"agent-reach\s+doctor",
    ],
    "research tool stack": [
        r"Tool Stack Routing",
        r"Scrapling",
        r"browser-use",
        r"Claude for Chrome",
    ],
    "task packs": [
        r"任务包",
        r"task-packs\.md",
    ],
    "quality gate": [
        r"quality gate|Quality Gate|质量门槛",
        r"2\s*个.*独立来源|2\s+independent\s+sources",
    ],
    "smart router": [
        r"Smart Router|smart-router\.md|决策摘要",
        r"任务类型|Task type",
    ],
    "goal compiler": [
        r"Goal Compiler|goal-compiler\.md|选择理由",
        r"默认假设|Default Assumptions",
    ],
    "compiler runtime": [
        r"compiler-runtime\.md|goal_compiler\.py|Executable Contract Mode",
        r"PENDING HUMAN SIGN-OFF|APPROVED BY HUMAN",
    ],
    "xiaowei preferences": [
        r"xiaowei-preferences\.md|偏好应用",
        r"小闭环|页面.*功能.*内容.*增长",
    ],
    "business priority": [
        r"business-priority\.md|优先级判断",
        r"业务价值|business value",
    ],
    "strategy gate": [
        r"strategy-gate\.md|策略判断|Strategy Gate",
        r"反证|kill criteria|最小验证",
    ],
    "output compression": [
        r"output-compression\.md|输出长度",
        r"短版|标准版|完整版",
    ],
    "domain packs": [
        r"domain-packs\.md|领域包",
        r"AI\s*工具站包|Chrome\s*插件包|出海\s*SaaS",
    ],
    "self evolution": [
        r"self-evolution\.md|自我进化|自动进化",
        r"自动化边界|允许修改路径|回滚方式",
    ],
    "goal output evaluation": [
        r"evaluate_goal_output\.py|目标评估|goal output evaluation",
    ],
    "daily evolution": [
        r"daily_evolution_audit\.py|每日进化|daily evolution",
        r"定时|schedule|GitHub Actions",
    ],
    "release consistency": [
        r"check_release_consistency\.py|release.*tag|manifest.*release",
    ],
}


def _parse_version(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _resolve_skill_dir(argv: list[str]) -> Path:
    if len(argv) < 2:
        return DEFAULT_SKILL_DIR

    path = Path(argv[1]).expanduser()
    if path.name == "SKILL.md":
        return path.parent
    return path


def main(argv: list[str]) -> int:
    skill_dir = _resolve_skill_dir(argv)
    skill_file = skill_dir / "SKILL.md"
    manifest_file = skill_dir / "manifest.json"

    errors: list[str] = []
    warnings: list[str] = []

    if not skill_file.exists():
        errors.append(f"{skill_file}: missing SKILL.md")
    else:
        text = skill_file.read_text(encoding="utf-8")
        for group, patterns in REQUIRED_SKILL_PATTERNS.items():
            missing = [pattern for pattern in patterns if not re.search(pattern, text, flags=re.IGNORECASE)]
            if missing:
                errors.append(f"{skill_file}: missing current {group} markers: {missing}")

    if manifest_file.exists():
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{manifest_file}: invalid JSON: {exc}")
        else:
            version = _parse_version(str(manifest.get("version", "")))
            if version is None:
                errors.append(f"{manifest_file}: missing semver `version`")
            elif version < MIN_VERSION:
                errors.append(f"{manifest_file}: version {manifest.get('version')} is older than 0.12.0")
    else:
        warnings.append(f"{manifest_file}: missing manifest.json, checked SKILL.md markers only")

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("Run: npx skills add siuserxiaowei/xiaowei-goal", file=sys.stderr)
        return 1

    print(f"Installed xiaowei-goal looks current: {skill_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
