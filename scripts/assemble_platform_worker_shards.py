#!/usr/bin/env python3
"""Assemble per-platform worker JSONL files into the three frozen shards.

The handoff workers wrote one JSONL file per platform under ``workers/new``.
The curator compiler intentionally consumes only the frozen china/global/ecosystem
shards.  This script bridges those layouts without accepting any candidate: every
row remains ``worker_checked`` and still requires curator review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
SHARDS = ("china", "global", "ecosystem")
REQUIRED_FIELDS = {
    "candidate_id",
    "platform_id",
    "title",
    "canonical_url",
    "creator_name",
    "published_at",
    "date_basis",
    "accessed_at",
    "language",
    "content_type",
    "content_track",
    "summary",
    "why_useful",
    "discovery_backend",
    "readback_backend",
    "evidence_status",
    "limitations",
    "query_id",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_url(raw: str) -> str:
    parsed = urlsplit(str(raw).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public URL: {raw!r}")
    host = parsed.hostname.lower() + (f":{parsed.port}" if parsed.port else "")
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))


def load_platform_map(run_dir: Path, required_platforms: set[str]) -> dict[str, str]:
    platform_to_shard: dict[str, str] = {}
    for shard in SHARDS:
        path = run_dir / "workers" / f"{shard}-rules.tsv"
        if not path.exists():
            raise ValueError(f"missing rule shard: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        for row in rows:
            platform_id = row.get("platform_id", "").strip()
            if not platform_id:
                raise ValueError(f"{path.name}: empty platform_id")
            if platform_id in platform_to_shard:
                raise ValueError(
                    f"platform {platform_id!r} appears in both "
                    f"{platform_to_shard[platform_id]!r} and {shard!r} rules"
                )
            platform_to_shard[platform_id] = shard

    missing = sorted(required_platforms - set(platform_to_shard))
    extra = sorted(set(platform_to_shard) - required_platforms)
    if missing or extra:
        raise ValueError(f"rule shard scope mismatch: missing={missing}, extra={extra}")
    return platform_to_shard


def load_platform_file(path: Path, expected_platform: str) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
            missing = sorted(REQUIRED_FIELDS - set(row))
            if missing:
                raise ValueError(f"{path.name}:{line_no}: missing fields {missing}")
            if row["platform_id"] != expected_platform:
                raise ValueError(
                    f"{path.name}:{line_no}: platform_id {row['platform_id']!r} "
                    f"does not match filename {expected_platform!r}"
                )
            if row["evidence_status"] != "worker_checked":
                raise ValueError(
                    f"{path.name}:{line_no}: only worker_checked rows may be assembled"
                )
            if not str(row["candidate_id"]).strip() or not str(row["title"]).strip():
                raise ValueError(f"{path.name}:{line_no}: empty candidate_id/title")
            if len(str(row["summary"]).strip()) < 18:
                raise ValueError(f"{path.name}:{line_no}: summary is too thin")
            if len(str(row["why_useful"]).strip()) < 8:
                raise ValueError(f"{path.name}:{line_no}: why_useful is too thin")
            row["canonical_url"] = normalize_url(row["canonical_url"])
            rows.append(row)
    return rows


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--check", action="store_true", help="validate without writing shards")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_platforms = set(manifest["required_platforms"])
    platform_to_shard = load_platform_map(run_dir, required_platforms)

    source_dir = run_dir / "workers" / "new"
    source_files = sorted(source_dir.glob("*.jsonl"))
    if not source_files:
        raise ValueError(f"no per-platform JSONL files found in {source_dir}")

    shard_rows: dict[str, list[dict]] = {shard: [] for shard in SHARDS}
    source_records: list[dict] = []
    seen_ids: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    for path in source_files:
        platform_id = path.stem
        if platform_id not in platform_to_shard:
            raise ValueError(f"{path.name}: platform is outside the frozen rule shards")
        rows = load_platform_file(path, platform_id)
        for row in rows:
            candidate_id = row["candidate_id"]
            canonical = row["canonical_url"]
            if candidate_id in seen_ids:
                raise ValueError(
                    f"duplicate candidate_id {candidate_id!r}: {seen_ids[candidate_id]} and {path.name}"
                )
            if canonical in seen_urls:
                raise ValueError(
                    f"duplicate canonical URL {canonical!r}: {seen_urls[canonical]} and {candidate_id}"
                )
            seen_ids[candidate_id] = path.name
            seen_urls[canonical] = candidate_id
        shard = platform_to_shard[platform_id]
        shard_rows[shard].extend(rows)
        source_records.append(
            {
                "path": str(path.relative_to(run_dir)),
                "platform_id": platform_id,
                "shard": shard,
                "record_count": len(rows),
                "sha256": sha256(path),
            }
        )

    outputs: dict[str, dict] = {}
    encoded_by_shard: dict[str, bytes] = {}
    for shard in SHARDS:
        rows = sorted(shard_rows[shard], key=lambda row: (row["platform_id"], row["candidate_id"]))
        encoded = (
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        ).encode("utf-8")
        encoded_by_shard[shard] = encoded
        outputs[shard] = {
            "path": f"workers/{shard}-candidates.jsonl",
            "record_count": len(rows),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "platform_counts": dict(sorted(Counter(row["platform_id"] for row in rows).items())),
        }

    report = {
        "schema_version": "pi-worker-shard-assembly/v1",
        "run_id": manifest["run_id"],
        "status": "validated" if args.check else "assembled",
        "source_record_count": sum(record["record_count"] for record in source_records),
        "source_files": source_records,
        "outputs": outputs,
    }
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    if not args.check:
        for shard, encoded in encoded_by_shard.items():
            atomic_write(run_dir / "workers" / f"{shard}-candidates.jsonl", encoded)
        atomic_write(run_dir / "worker_shard_assembly.json", report_bytes)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
