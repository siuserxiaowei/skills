#!/usr/bin/env python3
"""Audit repository-wide Skill provenance and documentation contracts."""

from __future__ import annotations

import argparse
import hashlib
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
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_ORIGIN_GROUPS = {"repository_authored_baseline_current", "new_original", "independently_rebuilt"}


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
    if not isinstance(groups, dict):
        findings.append(Finding("provenance-groups", manifest_path.name, "expected an object"))
        groups = {}
    if manifest.get("schema_version") != 2:
        findings.append(Finding("provenance-schema", manifest_path.name, "expected schema_version 2"))
    unknown_groups = sorted(set(groups) - EXPECTED_ORIGIN_GROUPS)
    if unknown_groups:
        findings.append(Finding("provenance-group", manifest_path.name, f"unknown={unknown_groups}"))
    for group_name, names in list(groups.items()):
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            findings.append(Finding("provenance-group-members", manifest_path.name, group_name))
            groups[group_name] = []
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
    original_assets = manifest.get("bundled_original_artifacts", [])
    if not isinstance(original_assets, list) or not all(isinstance(item, str) for item in original_assets):
        findings.append(Finding("original-assets-invalid", manifest_path.name, "expected a list of paths"))
        original_assets = []
    declared_original_assets = set(original_assets)
    for relative in sorted(declared_original_assets):
        if not (root / relative).is_file():
            findings.append(Finding("original-asset-missing", manifest_path.name, relative))

    assurance = manifest.get("originality_assurance", {})
    if not isinstance(assurance, dict):
        findings.append(Finding("originality-assurance", manifest_path.name, "expected an object"))
        assurance = {}
    for key in ("policy", "historical_baseline_commit", "gate", "default_failure_level", "thresholds"):
        if key not in assurance:
            findings.append(Finding("originality-assurance", manifest_path.name, f"missing {key}"))
    for key in ("policy", "gate"):
        relative = assurance.get(key)
        if isinstance(relative, str) and not (root / relative).is_file():
            findings.append(Finding("originality-evidence-missing", manifest_path.name, relative))
    baseline = assurance.get("historical_baseline_commit")
    if baseline is not None and (not isinstance(baseline, str) or not COMMIT_RE.fullmatch(baseline)):
        findings.append(Finding("originality-baseline", manifest_path.name, "expected a full 40-character Git commit"))
    if assurance.get("default_failure_level") not in {"material", "unreviewed", "review"}:
        findings.append(Finding("originality-failure-level", manifest_path.name, "expected material, unreviewed, or review"))
    thresholds = assurance.get("thresholds")
    if thresholds is not None and not isinstance(thresholds, dict):
        findings.append(Finding("originality-thresholds", manifest_path.name, "expected an object"))

    rebuilt = groups.get("independently_rebuilt", [])
    source_groups = manifest.get("known_source_groups")
    source_declared = []
    if not isinstance(source_groups, list):
        findings.append(Finding("known-source-register", manifest_path.name, "expected a list"))
    else:
        for index, item in enumerate(source_groups):
            if not isinstance(item, dict):
                findings.append(Finding("known-source-register", manifest_path.name, f"entry {index} is not an object"))
                continue
            if not isinstance(item.get("source"), str) or not isinstance(item.get("locator"), str):
                findings.append(Finding("known-source-register", manifest_path.name, f"entry {index} lacks source/locator"))
            names = item.get("skills")
            if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
                findings.append(Finding("known-source-register", manifest_path.name, f"entry {index} has invalid skills"))
            else:
                source_declared.extend(names)
    source_duplicates = sorted({name for name in source_declared if source_declared.count(name) > 1})
    if source_duplicates:
        findings.append(Finding("known-source-duplicate", manifest_path.name, ", ".join(source_duplicates)))
    if sorted(source_declared) != sorted(rebuilt):
        missing = sorted(set(rebuilt) - set(source_declared))
        extra = sorted(set(source_declared) - set(rebuilt))
        findings.append(Finding("known-source-coverage", manifest_path.name, f"missing={missing} extra={extra}"))

    new_original = groups.get("new_original", [])
    new_evidence = manifest.get("new_original_evidence")
    if not isinstance(new_evidence, dict):
        findings.append(Finding("new-original-evidence", manifest_path.name, "expected an object"))
        new_evidence = {}
    if set(new_evidence) != set(new_original):
        findings.append(
            Finding(
                "new-original-coverage",
                manifest_path.name,
                f"missing={sorted(set(new_original) - set(new_evidence))} extra={sorted(set(new_evidence) - set(new_original))}",
            )
        )
    for name, item in sorted(new_evidence.items()):
        if not isinstance(item, dict):
            findings.append(Finding("new-original-evidence", manifest_path.name, f"{name} is not an object"))
            continue
        first_commit = item.get("first_commit")
        anchor = item.get("anchor")
        if not isinstance(first_commit, str) or not COMMIT_RE.fullmatch(first_commit):
            findings.append(Finding("new-original-commit", manifest_path.name, name))
        if not isinstance(anchor, str) or not anchor.startswith(f"skills/{name}/") or not (root / anchor).is_file():
            findings.append(Finding("new-original-anchor", manifest_path.name, f"{name}: {anchor}"))

    reviewed = manifest.get("reviewed_similarity_findings")
    seen_review_keys = set()
    if not isinstance(reviewed, list):
        findings.append(Finding("similarity-review-register", manifest_path.name, "expected a list"))
    else:
        for index, item in enumerate(reviewed):
            if not isinstance(item, dict):
                findings.append(Finding("similarity-review-register", manifest_path.name, f"entry {index} is not an object"))
                continue
            skill = item.get("skill")
            relative = item.get("path")
            digest = item.get("sha256")
            key = (skill, relative)
            if key in seen_review_keys:
                findings.append(Finding("similarity-review-duplicate", manifest_path.name, str(key)))
            seen_review_keys.add(key)
            if skill not in rebuilt or not isinstance(relative, str) or not relative.startswith(f"skills/{skill}/"):
                findings.append(Finding("similarity-review-scope", manifest_path.name, f"entry {index}"))
                continue
            target = root / relative
            if not target.is_file():
                findings.append(Finding("similarity-review-missing", manifest_path.name, relative))
            elif not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                findings.append(Finding("similarity-review-hash", manifest_path.name, relative))
            elif hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                findings.append(Finding("similarity-review-stale", manifest_path.name, relative))
            if not isinstance(item.get("disposition"), str) or not isinstance(item.get("rationale"), str) or len(item.get("rationale", "")) < 20:
                findings.append(Finding("similarity-review-rationale", manifest_path.name, f"entry {index}"))

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
