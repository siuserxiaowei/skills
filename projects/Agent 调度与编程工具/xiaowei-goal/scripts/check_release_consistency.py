#!/usr/bin/env python3
"""Check manifest version, git tag, and optional GitHub release consistency."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def manifest_version() -> str:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    version = str(manifest.get("version", "")).strip()
    if not version:
        raise ValueError("manifest.json is missing `version`")
    return version


def git_output(command: list[str]) -> str:
    result = run(command)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def check_git_tag(tag: str) -> list[str]:
    errors: list[str] = []
    head = git_output(["git", "rev-parse", "HEAD"])

    result = run(["git", "rev-list", "-n", "1", tag])
    if result.returncode != 0:
        return [f"missing git tag `{tag}`"]

    tag_commit = result.stdout.strip()
    if tag_commit != head:
        errors.append(f"git tag `{tag}` points to {tag_commit}, not HEAD {head}")
    return errors


def check_github_release(tag: str, repo: str | None) -> list[str]:
    if not repo:
        return ["cannot check GitHub release without repository name"]

    result = run(
        [
            "gh",
            "release",
            "view",
            tag,
            "-R",
            repo,
            "--json",
            "tagName,isDraft,isPrerelease,targetCommitish",
        ]
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        if detail:
            return [f"missing GitHub release `{tag}`: {detail}"]
        return [f"missing GitHub release `{tag}`"]

    release = json.loads(result.stdout)
    errors: list[str] = []
    if release.get("tagName") != tag:
        errors.append(f"GitHub release tag mismatch: {release.get('tagName')} != {tag}")
    if release.get("isDraft"):
        errors.append(f"GitHub release `{tag}` is still a draft")
    if release.get("isPrerelease"):
        errors.append(f"GitHub release `{tag}` is marked prerelease")
    return errors


def infer_github_repo() -> str:
    result = run(["git", "remote", "get-url", "origin"])
    if result.returncode != 0:
        return ""

    remote = result.stdout.strip()
    patterns = [
        r"github\.com[:/](?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?$",
        r"^https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, remote)
        if match:
            return f"{match.group('owner')}/{match.group('repo')}"
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-github-release", action="store_true")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY") or infer_github_repo())
    args = parser.parse_args(argv[1:])

    try:
        version = manifest_version()
        tag = f"v{version}"
        errors = check_git_tag(tag)
        if args.require_github_release:
            errors.extend(check_github_release(tag, args.repo or None))
    except Exception as exc:  # noqa: BLE001 - CLI should print concise failure.
        print(f"release consistency check failed: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(f"Release consistency passed: {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
