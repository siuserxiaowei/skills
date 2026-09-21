#!/usr/bin/env python3
"""Validate a distribution package without contacting any platform."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SENSITIVE_KEY = re.compile(r"(?:token|password|passwd|secret|cookie|session|api[_-]?key|authorization)", re.I)
ALLOWED_STATES = {"prepared", "drafted", "scheduled", "published", "failed", "blocked"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def unsafe_key(value: object, location: str = "root") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                return f"{location}.{key}"
            found = unsafe_key(child, f"{location}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = unsafe_key(child, f"{location}[{index}]")
            if found:
                return found
    return None


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def package_path(root: Path, reference: str) -> Path:
    candidate = Path(reference).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="Path to an xiaowei-aibeike package")
    parser.add_argument("--require-platform", action="append", default=[], help="Require a platform to be present")
    args = parser.parse_args()
    root = Path(args.package).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest_path = root / "manifest.json"
    if not root.is_dir():
        errors.append(f"package directory does not exist: {root}")
    elif not manifest_path.is_file():
        errors.append("manifest.json is missing")
    if errors:
        report = {"valid": False, "checked_at": now(), "package": str(root), "errors": errors, "warnings": warnings}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read manifest.json: {exc}")
        manifest = {}
    if not isinstance(manifest, dict):
        errors.append("manifest root must be an object")
        manifest = {}
    sensitive = unsafe_key(manifest)
    if sensitive:
        errors.append(f"credential-like key found at {sensitive}")
    if manifest.get("schema") != "xiaowei-aibeike/1":
        errors.append("unsupported or missing manifest schema")
    publish = manifest.get("publish")
    if not isinstance(publish, dict) or publish.get("gate") != "manual-confirmation-required":
        errors.append("publish.gate must be manual-confirmation-required")
    if isinstance(publish, dict) and publish.get("requested") is not False:
        errors.append("publish.requested must remain false until a separate explicit publish action")

    source = manifest.get("source")
    if not isinstance(source, dict):
        errors.append("source record is missing")
    else:
        source_path = Path(str(source.get("path", ""))).expanduser()
        if not source_path.is_file():
            errors.append(f"source file is missing: {source_path}")
        else:
            actual = sha256(source_path)
            expected = str(source.get("sha256", ""))
            if actual != expected:
                errors.append("source SHA-256 does not match the locked fingerprint")
            if source.get("bytes") != source_path.stat().st_size:
                errors.append("source byte size does not match the locked record")

    media = manifest.get("media")
    if not isinstance(media, dict):
        errors.append("media record is missing")
    else:
        media_path = package_path(root, str(media.get("path", "")))
        if not media_path.is_file():
            errors.append(f"media file is missing: {media_path}")
        elif sha256(media_path) != str(media.get("sha256", "")):
            errors.append(f"media SHA-256 does not match the locked fingerprint: {media_path}")

    rows = manifest.get("platforms")
    if not isinstance(rows, list) or not rows:
        errors.append("platforms must be a non-empty array")
        rows = []
    seen: set[str] = set()
    for required in args.require_platform:
        if not any(isinstance(row, dict) and row.get("id") == required for row in rows):
            errors.append(f"required platform is missing: {required}")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("platform row must be an object")
            continue
        platform = str(row.get("id", ""))
        if not platform or platform in seen:
            errors.append(f"platform id is missing or duplicated: {platform!r}")
            continue
        seen.add(platform)
        state = row.get("state")
        if state not in ALLOWED_STATES:
            errors.append(f"{platform}: invalid state {state!r}")
        for field in ("metadata", "status"):
            reference = row.get(field)
            if not isinstance(reference, str) or Path(reference).is_absolute():
                errors.append(f"{platform}: {field} must be a relative package path")
                continue
            path = package_path(root, reference)
            try:
                path.relative_to(root)
            except ValueError:
                errors.append(f"{platform}: {field} escapes the package")
                continue
            if not path.is_file():
                errors.append(f"{platform}: missing {field} file: {reference}")
        metadata_file = package_path(root, str(row.get("metadata", "")))
        if metadata_file.is_file():
            try:
                metadata = load_json(metadata_file)
                sensitive = unsafe_key(metadata)
                if sensitive:
                    errors.append(f"{platform}: credential-like key found at {sensitive}")
                if not isinstance(metadata, dict) or not str(metadata.get("title", "")).strip():
                    errors.append(f"{platform}: title is empty")
                if isinstance(metadata, dict) and not str(metadata.get("description", "")).strip():
                    warnings.append(f"{platform}: description is empty; verify the editor accepts that")
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"{platform}: cannot read metadata: {exc}")

    report = {"valid": not errors, "checked_at": now(), "package": str(root), "errors": errors, "warnings": warnings}
    report_path = root / "validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
