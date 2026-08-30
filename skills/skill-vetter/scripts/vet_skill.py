#!/usr/bin/env python3
"""Static inventory and risk leads for an Agent Skill package.

The scanner never executes candidate code, follows no symlinks, and uses only the
Python standard library. Findings are evidence for manual review, not a safety
certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


TEXT_SUFFIXES = {
    "", ".bash", ".c", ".cfg", ".conf", ".cpp", ".css", ".env", ".go",
    ".h", ".html", ".ini", ".java", ".js", ".json", ".jsx", ".md",
    ".mjs", ".php", ".pl", ".ps1", ".py", ".rb", ".rs", ".sh", ".sql",
    ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml", ".zsh",
}
EXECUTABLE_SUFFIXES = {".bash", ".js", ".mjs", ".php", ".pl", ".ps1", ".py", ".rb", ".sh", ".zsh"}
MANIFEST_NAMES = {
    "Cargo.toml", "Gemfile", "go.mod", "package.json", "Pipfile",
    "pyproject.toml", "requirements.txt",
}
LOCK_NAMES = {
    "Cargo.lock", "Gemfile.lock", "go.sum", "package-lock.json", "Pipfile.lock",
    "pnpm-lock.yaml", "poetry.lock", "uv.lock", "yarn.lock",
}
ARCHIVE_SUFFIXES = {".7z", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".xz", ".zip"}
MEDIA_SUFFIXES = {
    ".avif", ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".m4a", ".mov",
    ".mp3", ".mp4", ".ogg", ".pdf", ".png", ".svgz", ".wav", ".webm", ".webp",
}
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
URL_RE = re.compile(r"https?://[^\s\]\[(){}<>\"']+")
IP_HOST_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
UNICODE_CONTROL_RE = re.compile("[\u200b\u200c\u200d\u2060\u202a-\u202e\u2066-\u2069\ufeff]")


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    path: str
    line: int | None
    evidence: str
    rationale: str


RULES: tuple[tuple[str, str, re.Pattern[str], str], ...] = (
    ("EXEC-PIPE-SHELL", "critical", re.compile(r"(?:curl|wget)\b[^\n|]{0,500}\|\s*(?:ba)?sh\b", re.I), "Remote content is piped directly to a shell."),
    ("EXEC-DESTRUCTIVE-BROAD", "critical", re.compile(r"\brm\s+(?:(?:-[^\s#]*[rR][^\s#]*f[^\s#]*|-[^\s#]*f[^\s#]*[rR][^\s#]*|-[rR]\s+-f|-f\s+-[rR]|--recursive\s+--force|--force\s+--recursive)\s+)(?:/|/\*|~|\$HOME|\$\{HOME\})(?:\s|$)|\b(?:mkfs|diskutil\s+eraseDisk)\b", re.I), "A destructive command targets a broad system or user boundary."),
    ("EXEC-RM-RECURSIVE", "high", re.compile(r"\brm\s+(?:-[^\s#]*[rR][^\s#]*f[^\s#]*|-[^\s#]*f[^\s#]*[rR][^\s#]*|-[rR]\s+-f|-f\s+-[rR]|--recursive\s+--force|--force\s+--recursive)\b", re.I), "Recursive forced deletion requires exact target validation and a recovery plan."),
    ("EXFIL-NETCAT", "critical", re.compile(r"\b(?:nc|ncat|netcat|socat)\b[^\n]*(?:-e|EXEC:|TCP:)", re.I), "A general-purpose network relay may execute or exfiltrate data."),
    ("PRIV-SUDO", "high", re.compile(r"(^|[;&|]\s*)sudo\b", re.I), "The package requests elevated privileges."),
    ("EXEC-DYNAMIC", "high", re.compile(r"(?<![.\w])(?:eval|exec|execSync)\s*\(|\b(?:child_process|os)\.(?:exec|execSync|system)\s*\(|shell\s*=\s*True", re.I), "Dynamic code or shell execution requires data-flow review."),
    ("CREDENTIAL-PATH", "high", re.compile(r"(?:~/|/Users/[^/]+/|/home/[^/]+/)?\.(?:ssh|aws|gnupg|kube)(?:/|\b)|(?:Cookies|Login Data|Keychain)", re.I), "The package references a credential or browser-session store."),
    ("PERSISTENCE", "high", re.compile(r"(?:LaunchAgents|LaunchDaemons|crontab\b|systemctl\s+enable|schtasks\b|HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)", re.I), "The package may establish persistence."),
    ("OBFUSCATION", "medium", re.compile(r"(?:base64\.(?:b64decode|decodebytes)|\bbase64\s+(?:--decode|-d)\b|fromCharCode\s*\(|openssl\s+enc\s+-d)", re.I), "Encoded or reconstructed content needs contextual review."),
    ("DYNAMIC-INSTALL", "medium", re.compile(r"\b(?:pip3?|npm|pnpm|yarn|gem|cargo)\s+install\b", re.I), "Runtime package installation expands the reviewed supply chain."),
    ("PROMPT-OVERRIDE", "medium", re.compile(r"(?:ignore|disregard|override)\s+(?:all\s+)?(?:previous|prior|system|developer)\s+(?:instructions|messages?)", re.I), "An instruction-override phrase may indicate prompt injection or an unsafe example."),
    ("SECRET-VARIABLE", "medium", re.compile(r"\b(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|OPENAI_API_KEY|ANTHROPIC_API_KEY|PRIVATE_KEY|PASSWORD)\b"), "A sensitive variable is referenced and its use must be traced."),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Skill directory to inspect")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("never", "low", "medium", "high", "critical"), default="high")
    parser.add_argument("--max-bytes", type=int, default=2_000_000, help="Maximum bytes read from one text file")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_probably_text(path: Path, sample: bytes) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES or path.name in MANIFEST_NAMES | LOCK_NAMES:
        return b"\x00" not in sample
    return b"\x00" not in sample and all(byte in b"\t\n\r" or 32 <= byte <= 126 or byte >= 128 for byte in sample)


def executable_context(path: Path) -> bool:
    try:
        mode_exec = bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    except OSError:
        mode_exec = False
    return path.suffix.lower() in EXECUTABLE_SUFFIXES or mode_exec


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def contextual_severity(severity: str, path: Path) -> str:
    if executable_context(path):
        return severity
    return {"critical": "high", "high": "medium"}.get(severity, severity)


def validate_skill_entry(path: Path, rel: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if not text.startswith("---\n"):
        return [Finding("FRONTMATTER-MISSING", "high", rel, 1, "file does not begin with ---", "The skill entrypoint lacks required YAML frontmatter.")]
    closing = text.find("\n---\n", 4)
    if closing < 0:
        return [Finding("FRONTMATTER-UNCLOSED", "high", rel, 1, "closing --- not found", "The required YAML frontmatter is malformed or unclosed.")]
    frontmatter = text[4:closing]
    name_match = re.search(r"^name:\s*['\"]?([^'\"\n]+)['\"]?\s*$", frontmatter, re.M)
    description_match = re.search(r"^description:\s*(.+?)\s*$", frontmatter, re.M)
    if not name_match:
        findings.append(Finding("FRONTMATTER-NAME", "high", rel, 2, "name is missing", "Skill discovery requires a frontmatter name."))
    else:
        name = name_match.group(1).strip()
        if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
            findings.append(Finding("FRONTMATTER-NAME", "medium", rel, line_number(text, name_match.start()), name, "The name should use 1-64 lowercase letters, digits, or hyphens."))
        if path.parent.name != name:
            findings.append(Finding("FRONTMATTER-NAME-MISMATCH", "low", rel, line_number(text, name_match.start()), f"name={name}; folder={path.parent.name}", "A name and folder mismatch can cause ambiguous installation or discovery."))
    if not description_match or not description_match.group(1).strip(" '\""):
        findings.append(Finding("FRONTMATTER-DESCRIPTION", "high", rel, 2, "description is missing or empty", "Skill discovery requires a discriminating description."))
    return findings


def binary_finding(path: Path, rel: str, size: int, digest: str, sample: bytes) -> Finding:
    executable_magics = (b"\x7fELF", b"MZ", b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")
    evidence = f"{size} bytes; sha256={digest}"
    if sample.startswith(executable_magics):
        return Finding("BINARY-EXECUTABLE", "high", rel, None, evidence, "Native executable code requires platform-specific analysis before trust.")
    if path.suffix.lower() in ARCHIVE_SUFFIXES or sample.startswith((b"PK\x03\x04", b"\x1f\x8b")):
        return Finding("BINARY-ARCHIVE", "medium", rel, None, evidence, "Archive contents are not covered until extracted and scanned within a safe boundary.")
    if path.suffix.lower() in MEDIA_SUFFIXES:
        return Finding("BINARY-ASSET", "info", rel, None, evidence, "Media assets need format and metadata review when they influence model behavior or generated output.")
    return Finding("BINARY-OPAQUE", "medium", rel, None, evidence, "An opaque artifact requires format-specific inspection.")


def repository_license(root: Path) -> str | None:
    current = root
    while current != current.parent:
        if (current / ".git").exists():
            for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"):
                candidate = current / name
                if candidate.is_file():
                    return os.path.relpath(candidate, root)
            return None
        current = current.parent
    return None


def scan_text(path: Path, rel: str, text: str) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    domains: set[str] = set()
    for match in UNICODE_CONTROL_RE.finditer(text):
        findings.append(Finding("HIDDEN-UNICODE", "medium", rel, line_number(text, match.start()), repr(match.group(0)), "Invisible or bidirectional control characters can conceal instructions or code."))
    for rule_id, base_severity, pattern, rationale in RULES:
        for match in pattern.finditer(text):
            snippet = " ".join(match.group(0).split())[:240]
            findings.append(Finding(rule_id, contextual_severity(base_severity, path), rel, line_number(text, match.start()), snippet, rationale))
    for match in URL_RE.finditer(text):
        raw = match.group(0).rstrip(".,;:")
        host = (urlparse(raw).hostname or "").lower()
        if not host:
            continue
        domains.add(host)
        if IP_HOST_RE.fullmatch(host) or host in {"localhost", "0.0.0.0"}:
            findings.append(Finding("NETWORK-IP-HOST", "medium", rel, line_number(text, match.start()), raw[:240], "Literal or local network destinations need an explicit justification."))
    return findings, domains


def walk_without_following(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name != ".git")
        for name in sorted(files):
            yield Path(current, name)
        for name in dirs:
            candidate = Path(current, name)
            if candidate.is_symlink():
                yield candidate


def scan(root: Path, max_bytes: int) -> dict[str, object]:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"not a directory: {root}")

    findings: list[Finding] = []
    files: list[dict[str, object]] = []
    domains: set[str] = set()
    manifests: list[str] = []
    locks: list[str] = []
    license_files: list[str] = []
    skill_files: list[str] = []
    skipped: list[dict[str, str]] = []

    for path in walk_without_following(resolved):
        rel = relative(path, resolved)
        if path.is_symlink():
            target = os.readlink(path)
            findings.append(Finding("SYMLINK", "medium", rel, None, target, "Symlinks can escape the reviewed package boundary."))
            files.append({"path": rel, "kind": "symlink", "target": target})
            continue
        try:
            size = path.stat().st_size
            digest = sha256_file(path)
            with path.open("rb") as handle:
                sample = handle.read(min(size, 8192))
        except OSError as exc:
            skipped.append({"path": rel, "reason": str(exc)})
            continue

        record: dict[str, object] = {"path": rel, "bytes": size, "sha256": digest}
        if path.name == "SKILL.md":
            skill_files.append(rel)
        if path.name in MANIFEST_NAMES:
            manifests.append(rel)
        if path.name in LOCK_NAMES:
            locks.append(rel)
        if path.name.lower().startswith(("license", "copying", "notice")):
            license_files.append(rel)

        if not is_probably_text(path, sample):
            record["kind"] = "binary"
            findings.append(binary_finding(path, rel, size, digest, sample))
        elif size > max_bytes:
            record["kind"] = "text-skipped-size"
            skipped.append({"path": rel, "reason": f"text file exceeds --max-bytes ({size} > {max_bytes})"})
            findings.append(Finding("UNREVIEWED-LARGE-FILE", "high", rel, None, f"{size} bytes", "A relevant file was not statically inspected."))
        else:
            record["kind"] = "text"
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="replace")
                findings.append(Finding("INVALID-UTF8", "low", rel, None, "replacement decoding used", "Unexpected encoding can hide or alter reviewed content."))
            text_findings, text_domains = scan_text(path, rel, text)
            findings.extend(text_findings)
            domains.update(text_domains)
            if path.name == "SKILL.md":
                findings.extend(validate_skill_entry(path, rel, text))
        files.append(record)

    if not skill_files:
        findings.append(Finding("MISSING-SKILL", "high", ".", None, "SKILL.md not found", "The package lacks the required skill entrypoint."))
    elif len(skill_files) > 1:
        findings.append(Finding("MULTIPLE-SKILLS", "low", ".", None, ", ".join(skill_files), "Confirm the intended package boundary and entrypoints."))
    inherited_license = repository_license(resolved) if not license_files else None
    if inherited_license:
        license_files.append(inherited_license)
    if not license_files:
        findings.append(Finding("MISSING-LICENSE", "medium", ".", None, "no license or notice file", "Redistribution and modification rights are not established by the artifact."))
    if manifests and not locks:
        findings.append(Finding("UNLOCKED-DEPENDENCIES", "medium", ".", None, ", ".join(manifests), "Dependency manifests exist without a recognized lockfile."))

    findings.sort(key=lambda item: (-SEVERITY_ORDER[item.severity], item.path, item.line or 0, item.rule_id))
    return {
        "scanner": {"name": "skill-vetter-static", "version": "1.0.0"},
        "root": str(resolved),
        "summary": {
            "files": len(files),
            "text_files": sum(item.get("kind") == "text" for item in files),
            "binary_files": sum(item.get("kind") == "binary" for item in files),
            "skipped": len(skipped),
            "findings": {severity: sum(item.severity == severity for item in findings) for severity in SEVERITY_ORDER},
        },
        "domains": sorted(domains),
        "manifests": sorted(manifests),
        "lockfiles": sorted(locks),
        "license_files": sorted(license_files),
        "skipped": skipped,
        "files": files,
        "findings": [asdict(item) for item in findings],
        "limitations": [
            "Pattern matches require contextual review.",
            "Archives, binaries, generated behavior, remote resources, and runtime-only paths are not decoded or executed.",
            "No finding is not proof of safety.",
        ],
    }


def render_text(report: dict[str, object]) -> str:
    summary = report["summary"]
    assert isinstance(summary, dict)
    counts = summary["findings"]
    assert isinstance(counts, dict)
    lines = [
        "SKILL VETTING STATIC REPORT",
        f"Root: {report['root']}",
        f"Coverage: {summary['files']} files; {summary['text_files']} text; {summary['binary_files']} binary; {summary['skipped']} skipped",
        "Findings: " + ", ".join(f"{name}={counts[name]}" for name in ("critical", "high", "medium", "low", "info")),
        "Domains: " + (", ".join(report["domains"]) if report["domains"] else "none observed"),
        "",
    ]
    for raw in report["findings"]:
        assert isinstance(raw, dict)
        location = raw["path"] + (f":{raw['line']}" if raw["line"] else "")
        lines.append(f"[{raw['severity'].upper()}] {raw['rule_id']} {location}")
        lines.append(f"  Evidence: {raw['evidence']}")
        lines.append(f"  Why: {raw['rationale']}")
    lines.extend(["", "Limitations:"] + [f"- {item}" for item in report["limitations"]])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        report = scan(args.path, args.max_bytes)
    except (OSError, ValueError) as exc:
        print(f"skill-vetter: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    if args.fail_on == "never":
        return 0
    threshold = SEVERITY_ORDER[args.fail_on]
    findings = report["findings"]
    assert isinstance(findings, list)
    return 2 if any(SEVERITY_ORDER[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
