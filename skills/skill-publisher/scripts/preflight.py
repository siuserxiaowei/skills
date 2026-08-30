#!/usr/bin/env python3
"""Read-only release preflight for Agent Skills repositories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_FILE_NAMES = {
    ".env", ".npmrc", ".pypirc", "id_rsa", "id_dsa", "id_ed25519",
    "credentials", "credentials.json", "service-account.json",
}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".jks", ".keystore"}
ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar"}
TEXT_SCAN_LIMIT = 1_000_000
FILE_COUNT_LIMIT = 20_000


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def run_readonly(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return result.returncode, result.stdout.strip()


def relative(path: Path, root: Path) -> str:
    try:
        value = path.relative_to(root).as_posix()
        return value or "."
    except ValueError:
        return str(path)


def discover_skill_files(root: Path) -> list[Path]:
    patterns = (
        "SKILL.md",
        "*/SKILL.md",
        "skills/*/SKILL.md",
        "skills/*/*/SKILL.md",
        "plugins/*/skills/*/SKILL.md",
    )
    found: dict[str, Path] = {}
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and ".git" not in path.parts:
                found[str(path.resolve())] = path
    return sorted(found.values(), key=lambda item: item.as_posix())


def split_frontmatter(text: str) -> tuple[str | None, str | None, str | None]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None, "SKILL.md must start with YAML frontmatter"
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :]), None
    return None, None, "YAML frontmatter is not closed"


def minimal_yaml(block: str) -> dict[str, Any]:
    """Parse the scalar fields needed for a dependency-free fallback."""
    result: dict[str, Any] = {}
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#") or line[:1].isspace():
            index += 1
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            index += 1
            continue
        key, raw_value = match.groups()
        if raw_value in ("|", ">"):
            values: list[str] = []
            index += 1
            while index < len(lines) and (not lines[index].strip() or lines[index][:1].isspace()):
                if lines[index].strip():
                    values.append(lines[index].strip())
                index += 1
            result[key] = "\n".join(values) if raw_value == "|" else " ".join(values)
            continue
        value = raw_value.strip()
        if (value.startswith("\"") and value.endswith("\"")) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            result[key] = [part.strip() for part in value[1:-1].split(",") if part.strip()]
        else:
            result[key] = value
        index += 1
    return result


def load_frontmatter(block: str) -> tuple[dict[str, Any], str]:
    try:
        import yaml  # type: ignore

        value = yaml.safe_load(block)
        return (value if isinstance(value, dict) else {}), "pyyaml"
    except ImportError:
        return minimal_yaml(block), "minimal"
    except Exception as exc:  # PyYAML supplies detailed parser errors.
        raise ValueError(str(exc)) from exc


def validate_skill(path: Path, root: Path) -> tuple[list[Finding], dict[str, Any] | None, str | None]:
    findings: list[Finding] = []
    label = relative(path, root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [Finding("blocker", "skill-read-failed", label, str(exc))], None, None

    block, body, error = split_frontmatter(text)
    if error:
        return [Finding("blocker", "frontmatter-invalid", label, error)], None, None

    try:
        data, parser = load_frontmatter(block or "")
    except ValueError as exc:
        return [Finding("blocker", "yaml-invalid", label, str(exc))], None, None

    name = data.get("name")
    description = data.get("description")
    allowed_tools = data.get("allowed-tools")

    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or len(name) > 64:
        findings.append(
            Finding("blocker", "name-invalid", label, "name must be 1-64 lowercase letters, digits, and single hyphens")
        )
    elif name != path.parent.name:
        findings.append(
            Finding("blocker", "name-directory-mismatch", label, f"name '{name}' does not match directory '{path.parent.name}'")
        )

    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        findings.append(
            Finding("blocker", "description-invalid", label, "description must be a non-empty string of at most 1024 characters")
        )
    elif not re.search(r"\buse\b|when|用户|当|适用|用于|请求", description, re.IGNORECASE):
        findings.append(
            Finding("warning", "description-routing-weak", label, "description may not say clearly when the Skill should activate")
        )

    if allowed_tools is not None and not isinstance(allowed_tools, str):
        findings.append(
            Finding("blocker", "allowed-tools-invalid", label, "allowed-tools must be a space-separated string, not a list")
        )

    if not (body or "").strip():
        findings.append(Finding("blocker", "body-empty", label, "SKILL.md has no instruction body"))

    return findings, data, parser


def is_probably_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in chunk


def content_secret_findings(path: Path, root: Path) -> list[Finding]:
    try:
        if path.stat().st_size > TEXT_SCAN_LIMIT or not is_probably_text(path):
            return []
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    patterns = (
        ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
        ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}\b")),
        ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
        ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    )
    label = relative(path, root)
    findings: list[Finding] = []
    for code, pattern in patterns:
        if pattern.search(text):
            findings.append(Finding("blocker", code, label, "probable credential material in release file"))
    return findings


def inventory(root: Path) -> tuple[list[dict[str, Any]], list[Finding]]:
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    stack = [root]
    seen = 0

    while stack:
        directory = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            findings.append(Finding("blocker", "directory-read-failed", relative(directory, root), str(exc)))
            continue

        for entry in entries:
            if entry.name == ".git":
                continue
            path = Path(entry.path)
            label = relative(path, root)
            try:
                if entry.is_symlink():
                    findings.append(Finding("blocker", "symlink", label, "symlink target is outside the immutable release inventory"))
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    findings.append(Finding("warning", "special-file", label, "non-regular file requires review"))
                    continue
                file_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                findings.append(Finding("blocker", "file-stat-failed", label, str(exc)))
                continue

            seen += 1
            if seen > FILE_COUNT_LIMIT:
                findings.append(Finding("blocker", "file-limit", ".", f"release exceeds {FILE_COUNT_LIMIT} files"))
                return records, findings

            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                findings.append(Finding("blocker", "file-read-failed", label, str(exc)))
                continue

            records.append({"path": label, "size": file_stat.st_size, "sha256": digest})

            lowered = entry.name.casefold()
            suffix = path.suffix.casefold()
            if lowered in SECRET_FILE_NAMES or suffix in SECRET_SUFFIXES:
                findings.append(Finding("blocker", "secret-file", label, "credential-bearing filename must not be published without explicit review"))
            if suffix in ARCHIVE_SUFFIXES:
                findings.append(Finding("warning", "archive", label, "archive contents are opaque to this preflight"))
            if file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                findings.append(Finding("warning", "executable", label, "executable release file requires behavioral review"))
            findings.extend(content_secret_findings(path, root))

    return sorted(records, key=lambda item: item["path"]), findings


def find_license(root: Path) -> list[str]:
    names = {"license", "license.txt", "license.md", "license.rst", "copying", "copying.txt"}
    return sorted(path.name for path in root.iterdir() if path.is_file() and path.name.casefold() in names)


def git_context(root: Path, target: str | None) -> tuple[dict[str, Any], list[Finding]]:
    context: dict[str, Any] = {"is_repository": False}
    findings: list[Finding] = []
    code, top = run_readonly(["git", "rev-parse", "--show-toplevel"], root)
    if code != 0:
        findings.append(Finding("warning", "not-git-repository", ".", "source is not inside a Git repository"))
        return context, findings

    git_root = Path(top).resolve()
    context["is_repository"] = True
    context["root"] = str(git_root)
    if git_root != root:
        findings.append(
            Finding("warning", "nested-source", ".", f"source belongs to larger repository: {git_root}")
        )

    _, branch = run_readonly(["git", "branch", "--show-current"], git_root)
    _, head = run_readonly(["git", "rev-parse", "HEAD"], git_root)
    _, origin = run_readonly(["git", "remote", "get-url", "origin"], git_root)
    _, full_status = run_readonly(["git", "status", "--porcelain=v1", "--untracked-files=all"], git_root)
    _, staged = run_readonly(["git", "diff", "--cached", "--name-only"], git_root)
    context.update(
        {
            "branch": branch or None,
            "head": head or None,
            "origin": origin or None,
            "worktree_changes": [line for line in full_status.splitlines() if line],
            "staged_paths": [line for line in staged.splitlines() if line],
        }
    )

    if full_status:
        findings.append(Finding("warning", "dirty-worktree", ".", "repository contains uncommitted changes; review exact release content"))
    if staged:
        findings.append(Finding("warning", "staged-changes", ".", "repository already has staged paths; verify they all belong to the release"))
    if target and origin and normalize_repo(origin) != normalize_repo(target):
        findings.append(
            Finding("blocker", "target-origin-mismatch", ".", f"origin '{origin}' does not match target '{target}'")
        )
    return context, findings


def normalize_repo(value: str) -> str:
    cleaned = value.strip().removesuffix(".git").rstrip("/")
    match = re.search(r"github\.com[:/](?P<repo>[^/]+/[^/]+)$", cleaned)
    if match:
        return match.group("repo").casefold()
    return cleaned.casefold()


def tool_context(root: Path) -> dict[str, Any]:
    gh_code, gh_version = run_readonly(["gh", "--version"], root)
    skill_code, _ = run_readonly(["gh", "skill", "--help"], root) if gh_code == 0 else (127, "")
    return {
        "gh_available": gh_code == 0,
        "gh_version": gh_version.splitlines()[0] if gh_code == 0 and gh_version else None,
        "gh_skill_available": skill_code == 0,
    }


def preflight(root: Path, visibility: str, target: str | None) -> dict[str, Any]:
    root = root.resolve()
    findings: list[Finding] = []
    skills: list[dict[str, Any]] = []

    skill_files = discover_skill_files(root)
    if not skill_files:
        findings.append(Finding("blocker", "no-skills", ".", "no SKILL.md found in supported release layouts"))
    parsers: set[str] = set()
    for path in skill_files:
        current, data, parser = validate_skill(path, root)
        findings.extend(current)
        if parser:
            parsers.add(parser)
        skills.append(
            {
                "path": relative(path, root),
                "name": data.get("name") if data else None,
                "description": data.get("description") if data else None,
            }
        )

    files, file_findings = inventory(root)
    findings.extend(file_findings)
    licenses = find_license(root)
    readme_exists = any((root / name).is_file() for name in ("README.md", "README.rst", "README.txt"))

    if visibility == "public" and not licenses:
        findings.append(
            Finding("blocker", "public-license-unresolved", ".", "public release has no root license file; choose a license or explicitly retain default copyright")
        )
    elif not licenses:
        findings.append(Finding("warning", "license-unresolved", ".", "no root license file was found"))
    if visibility == "public" and not readme_exists:
        findings.append(Finding("warning", "public-readme-missing", ".", "public release has no root README"))
    if visibility == "unknown":
        findings.append(Finding("warning", "visibility-unresolved", ".", "resolve public, private, or internal visibility before repository creation"))

    git, git_findings = git_context(root, target)
    findings.extend(git_findings)
    tools = tool_context(root)
    if not tools["gh_skill_available"]:
        findings.append(
            Finding("warning", "gh-skill-unavailable", ".", "official gh skill validation/publishing is unavailable; use an explicit fallback or authorized upgrade")
        )

    counts = {
        "blocker": sum(item.severity == "blocker" for item in findings),
        "warning": sum(item.severity == "warning" for item in findings),
        "info": sum(item.severity == "info" for item in findings),
    }
    return {
        "root": str(root),
        "target": target,
        "visibility": visibility,
        "skills": skills,
        "files": files,
        "summary": {
            "skill_count": len(skills),
            "file_count": len(files),
            "total_bytes": sum(item["size"] for item in files),
            "licenses": licenses,
            "readme": readme_exists,
            "yaml_parsers": sorted(parsers),
        },
        "git": git,
        "tools": tools,
        "findings": [asdict(item) for item in findings],
        "counts": counts,
    }


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Source: {report['root']}",
        f"Target: {report['target'] or '(unresolved)'}",
        f"Visibility: {report['visibility']}",
        f"Skills: {summary['skill_count']}  Files: {summary['file_count']}  Bytes: {summary['total_bytes']}",
        f"License files: {', '.join(summary['licenses']) if summary['licenses'] else '(none)'}",
        f"GitHub Skill CLI: {'available' if report['tools']['gh_skill_available'] else 'unavailable'}",
    ]
    if report["findings"]:
        lines.append("Findings:")
        lines.extend(
            f"  {item['severity'].upper()} [{item['code']}] {item['path']}: {item['message']}"
            for item in report["findings"]
        )
    else:
        lines.append("PASS: no preflight findings")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Agent Skills publication preflight")
    parser.add_argument("source", help="Exact Skill repository or standalone Skill directory")
    parser.add_argument("--visibility", choices=("public", "private", "internal", "unknown"), default="unknown")
    parser.add_argument("--target", help="Expected GitHub OWNER/REPO")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("blocker", "warning", "never"), default="blocker")
    args = parser.parse_args(argv)

    source = Path(args.source)
    if not source.is_dir():
        print(f"ERROR: source is not a directory: {source}", file=sys.stderr)
        return 2

    report = preflight(source, args.visibility, args.target)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))

    if args.fail_on == "never":
        return 0
    if report["counts"]["blocker"]:
        return 1
    if args.fail_on == "warning" and report["counts"]["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
