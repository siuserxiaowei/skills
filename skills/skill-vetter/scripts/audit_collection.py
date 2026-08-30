#!/usr/bin/env python3
"""Audit repository-wide Skill provenance and documentation contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
NAME_RE = re.compile(r"(?m)^name:\s*['\"]?([^'\"\n]+)")
REQUIRED_EXAMPLE_HEADINGS = ("## 正向案例", "## 边界案例", "## 失败与恢复")
REQUIRED_EXAMPLE_LABELS = ("用户请求", "处理", "验收证据", "场景")
NOTICE_NAMES = re.compile(r"(?:^|[-_])(license|notice|sources|copyright)(?:[-_.]|$)", re.IGNORECASE)


@dataclass
class Finding:
    code: str
    path: str
    detail: str


def frontmatter_name(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    match = NAME_RE.search(text[4:end])
    return match.group(1).strip() if match else None


def markdown_targets(text: str) -> list[str]:
    targets = []
    for raw in LINK_RE.findall(text):
        target = raw.strip().split()[0].strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        targets.append(target.split("#", 1)[0])
    return targets


def audit(root: Path, expected_count: int) -> tuple[list[Finding], dict]:
    root = root.resolve()
    skills_root = root / "skills"
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    findings: list[Finding] = []

    if len(skill_dirs) != expected_count:
        findings.append(Finding("skill-count", "skills", f"expected {expected_count}, found {len(skill_dirs)}"))

    manifest_path = root / "SKILL_PROVENANCE.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        manifest = {}
        findings.append(Finding("provenance-invalid", manifest_path.name, str(error)))

    groups = manifest.get("origin_groups", {}) if isinstance(manifest, dict) else {}
    declared = [name for names in groups.values() if isinstance(names, list) for name in names]
    actual = [path.name for path in skill_dirs]
    duplicates = sorted({name for name in declared if declared.count(name) > 1})
    if duplicates:
        findings.append(Finding("provenance-duplicate", manifest_path.name, ", ".join(duplicates)))
    if sorted(declared) != actual:
        missing = sorted(set(actual) - set(declared))
        extra = sorted(set(declared) - set(actual))
        findings.append(Finding("provenance-coverage", manifest_path.name, f"missing={missing} extra={extra}"))
    if manifest.get("bundled_third_party_artifacts") != []:
        findings.append(Finding("third-party-artifacts-declared", manifest_path.name, "expected an empty list"))
    declared_original_assets = set(manifest.get("bundled_original_artifacts", []))
    for relative in sorted(declared_original_assets):
        if not (root / relative).is_file():
            findings.append(Finding("original-asset-missing", manifest_path.name, relative))

    for skill_dir in skill_dirs:
        name = skill_dir.name
        skill_file = skill_dir / "SKILL.md"
        example_file = skill_dir / "references" / "examples.md"
        skill_text = skill_file.read_text(encoding="utf-8")

        if frontmatter_name(skill_text) != name:
            findings.append(Finding("name-mismatch", str(skill_file.relative_to(root)), str(frontmatter_name(skill_text))))
        if "[references/examples.md](references/examples.md)" not in skill_text:
            findings.append(Finding("example-link", str(skill_file.relative_to(root)), "direct example link is missing"))
        if not example_file.is_file():
            findings.append(Finding("example-missing", str(example_file.relative_to(root)), "file is missing"))
            example_text = ""
        else:
            example_text = example_file.read_text(encoding="utf-8")
            for heading in REQUIRED_EXAMPLE_HEADINGS:
                if heading not in example_text:
                    findings.append(Finding("example-heading", str(example_file.relative_to(root)), heading))
            for label in REQUIRED_EXAMPLE_LABELS:
                if label not in example_text:
                    findings.append(Finding("example-label", str(example_file.relative_to(root)), label))
            if len(example_text) < 400:
                findings.append(Finding("example-thin", str(example_file.relative_to(root)), f"{len(example_text)} characters"))

        combined = skill_text + "\n" + example_text
        if len(combined) < 1000:
            findings.append(Finding("guidance-thin", str(skill_file.relative_to(root)), f"{len(combined)} characters"))
        if sum(1 for line in combined.splitlines() if line.startswith("## ")) < 4:
            findings.append(Finding("guidance-structure", str(skill_file.relative_to(root)), "fewer than four level-two sections"))
        for term, code in (("验收", "guidance-verification"), ("边界", "guidance-boundary"), ("失败", "guidance-failure")):
            if term not in combined:
                findings.append(Finding(code, str(skill_file.relative_to(root)), f"missing term: {term}"))

        for path in skill_dir.rglob("*"):
            if path.is_symlink():
                findings.append(Finding("symlink", str(path.relative_to(root)), "symlink is not allowed in this collection"))
            if path.is_file() and NOTICE_NAMES.search(path.name):
                findings.append(Finding("embedded-notice", str(path.relative_to(root)), "per-Skill third-party notice/license/source file"))
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".woff", ".woff2", ".ttf", ".otf", ".zip", ".tar", ".gz"}:
                relative = str(path.relative_to(root))
                if relative not in declared_original_assets:
                    findings.append(Finding("unmanifested-binary", relative, "binary asset lacks an original-asset manifest entry"))

        for md_file in skill_dir.rglob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            for target in markdown_targets(text):
                resolved = (md_file.parent / target).resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    findings.append(Finding("link-outside-root", str(md_file.relative_to(root)), target))
                    continue
                if not resolved.exists():
                    findings.append(Finding("broken-link", str(md_file.relative_to(root)), target))

    summary = {
        "skills": len(skill_dirs),
        "provenance_entries": len(declared),
        "example_files": sum((path / "references" / "examples.md").is_file() for path in skill_dirs),
        "findings": len(findings),
    }
    return findings, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--expected-count", type=int, default=57)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings, summary = audit(Path(args.root), args.expected_count)
    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"skills={summary['skills']} provenance={summary['provenance_entries']} examples={summary['example_files']} findings={summary['findings']}")
        for finding in findings:
            print(f"{finding.code}: {finding.path}: {finding.detail}")
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
