#!/usr/bin/env python3
"""Create a deterministic, draft-first distribution package."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "xiaowei-aibeike/1"
SENSITIVE_KEY = re.compile(r"(?:token|password|passwd|secret|cookie|session|api[_-]?key|authorization)", re.I)
PLATFORM_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def contains_sensitive_key(value: object, location: str = "root") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                return f"{location}.{key}"
            found = contains_sensitive_key(child, f"{location}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = contains_sensitive_key(child, f"{location}[{index}]")
            if found:
                return found
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Absolute or relative path to the source video")
    parser.add_argument("--metadata", required=True, help="JSON file containing campaign and platform copy")
    parser.add_argument("--out", required=True, help="New package directory; existing packages are never overwritten")
    parser.add_argument("--copy-media", action="store_true", help="Copy the source video into the package")
    parser.add_argument("--force", action="store_true", help="Allow writing into an existing empty package directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    metadata_path = Path(args.metadata).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()

    if not source.is_file():
        print(f"error: source does not exist or is not a file: {source}", file=sys.stderr)
        return 2
    if not metadata_path.is_file():
        print(f"error: metadata does not exist: {metadata_path}", file=sys.stderr)
        return 2
    if source == out or source.is_relative_to(out):
        print("error: output package cannot contain or replace the source video", file=sys.stderr)
        return 2

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read metadata JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(metadata, dict):
        print("error: metadata root must be an object", file=sys.stderr)
        return 2
    sensitive = contains_sensitive_key(metadata)
    if sensitive:
        print(f"error: metadata contains a credential-like key at {sensitive}", file=sys.stderr)
        return 2
    platforms = metadata.get("platforms")
    if not isinstance(platforms, dict) or not platforms:
        print("error: metadata.platforms must be a non-empty object", file=sys.stderr)
        return 2
    for platform, record in platforms.items():
        if not isinstance(platform, str) or not PLATFORM_ID.fullmatch(platform):
            print(f"error: invalid platform id: {platform!r}", file=sys.stderr)
            return 2
        if not isinstance(record, dict):
            print(f"error: platform {platform} must be an object", file=sys.stderr)
            return 2
        if not str(record.get("title", "")).strip():
            print(f"error: platform {platform} is missing title", file=sys.stderr)
            return 2
        if "tags" in record and not isinstance(record["tags"], list):
            print(f"error: platform {platform}.tags must be an array", file=sys.stderr)
            return 2

    if out.exists():
        if not args.force or any(out.iterdir()):
            print(f"error: refusing to overwrite non-empty package: {out}", file=sys.stderr)
            return 2
    out.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(source)
    created_at = utc_now()
    campaign_id = str(metadata.get("campaign_id") or source.stem).strip()
    if not campaign_id:
        print("error: campaign_id cannot be empty", file=sys.stderr)
        return 2

    media_path: Path
    if args.copy_media:
        media_path = out / "media" / source.name
        media_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, media_path)
        media_reference = str(media_path.relative_to(out))
    else:
        media_reference = str(source)

    common = {
        "campaign_id": campaign_id,
        "content_anchor": metadata.get("content_anchor", ""),
        "source_fingerprint": source_hash,
        "video": media_reference,
    }
    platform_rows = []
    for platform, supplied in platforms.items():
        record = dict(supplied)
        record.setdefault("description", "")
        record.setdefault("tags", [])
        record["platform"] = platform
        record["campaign_id"] = campaign_id
        record["source_fingerprint"] = source_hash
        record["video"] = record.get("video", media_reference)
        metadata_file = out / "platforms" / platform / "metadata.json"
        status_file = out / "platforms" / platform / "status.json"
        write_json(metadata_file, {**common, **record})
        write_json(status_file, {
            "campaign_id": campaign_id,
            "platform": platform,
            "job_id": f"{campaign_id}:{platform}",
            "status": "prepared",
            "updated_at": created_at,
            "evidence": [],
        })
        platform_rows.append({
            "id": platform,
            "job_id": f"{campaign_id}:{platform}",
            "metadata": str(metadata_file.relative_to(out)),
            "status": str(status_file.relative_to(out)),
            "state": "prepared",
        })

    source_record = {
        "path": str(source),
        "name": source.name,
        "mime": mimetypes.guess_type(source.name)[0] or "application/octet-stream",
        "bytes": source.stat().st_size,
        "sha256": source_hash,
        "locked_at": created_at,
    }
    campaign_record = {
        "schema": SCHEMA,
        "campaign_id": campaign_id,
        "created_at": created_at,
        "content_anchor": metadata.get("content_anchor", ""),
        "mode": "aibeike-handoff",
        "metadata_source": str(metadata_path),
    }
    manifest = {
        "schema": SCHEMA,
        "campaign_id": campaign_id,
        "created_at": created_at,
        "mode": "aibeike-handoff",
        "source": source_record,
        "media": {"path": media_reference, "sha256": source_hash},
        "publish": {"gate": "manual-confirmation-required", "requested": False},
        "platforms": platform_rows,
    }
    write_json(out / "campaign.json", campaign_record)
    write_json(out / "source.json", source_record)
    write_json(out / "manifest.json", manifest)
    (out / "covers").mkdir(exist_ok=True)
    (out / "receipts").mkdir(exist_ok=True)
    print(json.dumps({"package": str(out), "campaign_id": campaign_id, "source_sha256": source_hash, "platforms": list(platforms)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
