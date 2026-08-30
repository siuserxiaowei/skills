#!/usr/bin/env python3
"""Inspect a web-research routing installation without reading account data."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


CHILDREN = {
    "search": ("unified-search", "Search and candidate discovery"),
    "archive": ("content-archive", "Known-URL capture and preservation"),
    "bookmarks": ("bookmarks-export", "Authorized private bookmark export"),
    "transcription": ("asr", "Existing audio/video transcription"),
}

TOOLS = {
    "git": ["git", "--version"],
    "gh": ["gh", "--version"],
    "curl": ["curl", "--version"],
    "ffmpeg": ["ffmpeg", "-version"],
    "yt-dlp": ["yt-dlp", "--version"],
    "opencli": ["opencli", "--version"],
}

FRONTMATTER = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    subject: str
    message: str


def default_skills_root() -> Path:
    configured = os.environ.get("WEB_RESEARCH_SKILLS_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2]


def parse_name(skill_file: Path) -> str | None:
    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = FRONTMATTER.match(text)
    if not match:
        return None
    for line in match.group("body").splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "name":
            return value.strip().strip("'\"") or None
    return None


def inspect_child(role: str, expected_name: str, purpose: str, root: Path) -> dict:
    path = root / expected_name / "SKILL.md"
    exists = path.is_file()
    parsed_name = parse_name(path) if exists else None
    return {
        "role": role,
        "purpose": purpose,
        "path": str(path),
        "exists": exists,
        "declared_name": parsed_name,
        "name_matches": parsed_name == expected_name,
    }


def first_line(value: str, limit: int = 180) -> str:
    compact = " ".join(value.split())
    return compact[:limit]


def inspect_tool(name: str, command: list[str], probe: bool) -> dict:
    executable = shutil.which(command[0])
    result = {"name": name, "available": bool(executable), "path": executable, "version": None}
    if not executable or not probe:
        return result
    try:
        process = subprocess.run(
            [executable, *command[1:]],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            env={"PATH": os.environ.get("PATH", "")},
        )
        result["version"] = first_line(process.stdout)
        result["probe_exit"] = process.returncode
    except (OSError, subprocess.SubprocessError) as exc:
        result["probe_error"] = str(exc)
    return result


def evaluate(children: list[dict], tools: list[dict], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not root.is_dir():
        findings.append(Finding("error", "skills-root-missing", str(root), "skills root does not exist"))
    for child in children:
        if not child["exists"]:
            findings.append(Finding("warning", "child-missing", child["role"], child["path"]))
        elif not child["name_matches"]:
            findings.append(
                Finding(
                    "error",
                    "child-name-mismatch",
                    child["role"],
                    f"expected {Path(child['path']).parent.name!r}, found {child['declared_name']!r}",
                )
            )
    if not any(item["available"] for item in tools if item["name"] in {"curl", "gh", "opencli"}):
        findings.append(Finding("warning", "no-network-client", "tools", "no public retrieval client was found"))
    return findings


def build_report(root: Path, probe_versions: bool) -> dict:
    children = [inspect_child(role, name, purpose, root) for role, (name, purpose) in CHILDREN.items()]
    tools = [inspect_tool(name, command, probe_versions) for name, command in TOOLS.items()]
    findings = evaluate(children, tools, root)
    return {
        "skills_root": str(root),
        "privacy": {
            "credentials_read": False,
            "browser_state_read": False,
            "private_collections_read": False,
            "network_requests_made": False,
            "version_commands_run": probe_versions,
        },
        "children": children,
        "tools": tools,
        "findings": [asdict(item) for item in findings],
        "counts": {
            "error": sum(item.severity == "error" for item in findings),
            "warning": sum(item.severity == "warning" for item in findings),
        },
    }


def render_text(report: dict) -> str:
    lines = [f"skills root: {report['skills_root']}"]
    for child in report["children"]:
        state = "ready" if child["exists"] and child["name_matches"] else "missing/mismatch"
        lines.append(f"child {child['role']}: {state} ({child['path']})")
    available = [tool["name"] for tool in report["tools"] if tool["available"]]
    lines.append("available tools: " + (", ".join(available) if available else "none"))
    for finding in report["findings"]:
        lines.append(f"{finding['severity'].upper()} [{finding['code']}] {finding['subject']}: {finding['message']}")
    if not report["findings"]:
        lines.append("PASS: routing installation has no structural findings")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", type=Path, default=default_skills_root())
    parser.add_argument("--probe-versions", action="store_true", help="run bounded local --version commands")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failure")
    args = parser.parse_args(argv)
    root = args.skills_root.expanduser().resolve(strict=False)
    report = build_report(root, args.probe_versions)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) if args.format == "json" else render_text(report))
    errors = report["counts"]["error"]
    warnings = report["counts"]["warning"]
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
