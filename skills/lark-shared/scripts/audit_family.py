#!/usr/bin/env python3
"""Audit the original Lark Skill family for structure and safety regressions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


EXPECTED = {
    "lark-approval", "lark-apps", "lark-attendance", "lark-base",
    "lark-calendar", "lark-contact", "lark-doc", "lark-drive",
    "lark-event", "lark-im", "lark-mail", "lark-markdown",
    "lark-minutes", "lark-note", "lark-okr", "lark-openapi-explorer",
    "lark-shared", "lark-sheets", "lark-skill-maker", "lark-slides",
    "lark-task", "lark-vc", "lark-vc-agent", "lark-whiteboard",
    "lark-wiki", "lark-workflow-meeting-summary",
    "lark-workflow-standup-report",
}
ALLOWED_FRONTMATTER = {"name", "description"}
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def issue(code: str, path: Path, detail: str) -> dict[str, str]:
    return {"code": code, "path": str(path), "detail": detail}


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    match = FRONT_RE.match(text)
    if not match:
        return {}, ["missing or malformed frontmatter"]
    data: dict[str, str] = {}
    problems: list[str] = []
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            problems.append(f"unsupported frontmatter line: {line}")
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if key not in ALLOWED_FRONTMATTER:
            problems.append(f"unexpected frontmatter key: {key}")
            continue
        if key == "description":
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                problems.append("description must be a JSON-quoted string")
                continue
        else:
            value = raw
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{key} must be a non-empty string")
            continue
        data[key] = value.strip()
    return data, problems


def iter_relative_links(text: str) -> Iterable[str]:
    for match in LINK_RE.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if target and not target.startswith(("http://", "https://", "mailto:", "#")):
            yield target


def audit_family(skills_root: Path, expected: set[str] | None = None) -> dict[str, object]:
    expected = set(expected or EXPECTED)
    findings: list[dict[str, str]] = []
    found = {p.name for p in skills_root.glob("lark-*") if p.is_dir()}

    for name in sorted(expected - found):
        findings.append(issue("missing_skill", skills_root / name, "expected Skill directory is absent"))
    for name in sorted(found - expected):
        findings.append(issue("unexpected_skill", skills_root / name, "unregistered lark Skill directory"))

    descriptions: dict[str, str] = {}
    bodies: dict[str, str] = {}
    for name in sorted(expected & found):
        root = skills_root / name
        if any(p.is_symlink() for p in root.rglob("*")):
            findings.append(issue("symlink", root, "Skill family must not contain symlinks"))
        for license_path in root.rglob("LICENSE*"):
            findings.append(issue("embedded_license", license_path, "original family must use the repository-level license"))

        skill_path = root / "SKILL.md"
        if not skill_path.is_file():
            findings.append(issue("missing_skill_md", skill_path, "SKILL.md is required"))
            continue
        text = skill_path.read_text(encoding="utf-8")
        data, problems = parse_frontmatter(text)
        for problem in problems:
            findings.append(issue("frontmatter", skill_path, problem))
        if data.get("name") != name:
            findings.append(issue("name_mismatch", skill_path, f"expected name {name!r}"))
        description = data.get("description", "")
        if description:
            if description in descriptions:
                findings.append(issue("duplicate_description", skill_path, f"duplicates {descriptions[description]}"))
            descriptions[description] = name
        if "lark-cli --version" not in text or "--help" not in text:
            findings.append(issue("missing_runtime_discovery", skill_path, "runtime version/help discovery is required"))
        if "## 验收" not in text or "## 版本与证据" not in text:
            findings.append(issue("missing_contract_section", skill_path, "acceptance and evidence sections are required"))
        bodies[name] = text

        for target in iter_relative_links(text):
            resolved = (skill_path.parent / target).resolve()
            if not resolved.exists():
                findings.append(issue("broken_link", skill_path, target))

        agent_path = root / "agents" / "openai.yaml"
        if not agent_path.is_file():
            findings.append(issue("missing_agent_metadata", agent_path, "agents/openai.yaml is required"))
        else:
            agent = agent_path.read_text(encoding="utf-8")
            if "$" + name not in agent:
                findings.append(issue("missing_default_prompt_token", agent_path, "default prompt must mention $" + name))
            match = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', agent, re.MULTILINE)
            if not match or not 25 <= len(match.group(1)) <= 64:
                findings.append(issue("short_description_length", agent_path, "short_description must be 25-64 characters"))

    fingerprints: dict[str, str] = {}
    for name, text in bodies.items():
        body = FRONT_RE.sub("", text)
        digestible = "\n".join(line.strip() for line in body.splitlines() if line.strip())
        if digestible in fingerprints:
            findings.append(issue("duplicate_skill_body", skills_root / name / "SKILL.md", f"duplicates {fingerprints[digestible]}"))
        fingerprints[digestible] = name

    return {
        "ok": not findings,
        "skill_count": len(found & expected),
        "expected_count": len(expected),
        "findings": findings,
    }


def main() -> int:
    default_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Audit all original Lark Skills for structural and safety regressions.")
    parser.add_argument("--skills-root", type=Path, default=default_root)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = audit_family(args.skills_root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
