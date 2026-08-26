#!/usr/bin/env python3
"""Merge worker-checked shards into a deterministic curator review queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
SHARDS = ("china", "global", "ecosystem")
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
}


def canonical_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public URL {raw!r}")
    host = parsed.hostname.lower() + (f":{parsed.port}" if parsed.port else "")
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
            missing = sorted(REQUIRED - set(row))
            if missing:
                raise ValueError(f"{path.name}:{line_no}: missing {missing}")
            if row["evidence_status"] != "worker_checked":
                raise ValueError(f"{path.name}:{line_no}: worker may only submit worker_checked")
            row["canonical_url"] = canonical_url(row["canonical_url"])
            row["worker_shard"] = path.stem.replace("-candidates", "")
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((args.run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    required_platforms = set(manifest["required_platforms"])

    items: list[dict] = []
    rule_rows: list[dict[str, str]] = []
    missing_shards = []
    for shard in SHARDS:
        candidate_path = args.run_dir / "workers" / f"{shard}-candidates.jsonl"
        rule_path = args.run_dir / "workers" / f"{shard}-rules.tsv"
        if candidate_path.exists():
            items.extend(load_jsonl(candidate_path))
        else:
            missing_shards.append(f"{shard}:candidates")
        if rule_path.exists():
            with rule_path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle, delimiter="\t"):
                    row.setdefault("reviewer_status", "worker_checked")
                    rule_rows.append(row)
        else:
            missing_shards.append(f"{shard}:rules")
    if missing_shards and not args.allow_missing:
        raise ValueError(f"missing worker shards: {missing_shards}")

    seen_ids: set[str] = set()
    seen_urls: dict[str, str] = {}
    duplicate_rows: list[dict[str, str]] = []
    unique_items: list[dict] = []
    for item in sorted(items, key=lambda row: (row["platform_id"], row["candidate_id"])):
        if item["platform_id"] not in required_platforms:
            raise ValueError(f"{item['candidate_id']}: platform outside frozen scope")
        if item["candidate_id"] in seen_ids:
            raise ValueError(f"duplicate candidate_id {item['candidate_id']}")
        seen_ids.add(item["candidate_id"])
        if item["canonical_url"] in seen_urls:
            duplicate_rows.append({
                "candidate_id": item["candidate_id"],
                "duplicate_of": seen_urls[item["canonical_url"]],
                "canonical_url": item["canonical_url"],
            })
            continue
        seen_urls[item["canonical_url"]] = item["candidate_id"]
        unique_items.append(item)

    rule_by_platform: dict[str, dict[str, str]] = {}
    for row in rule_rows:
        platform_id = row.get("platform_id", "")
        if platform_id not in required_platforms:
            raise ValueError(f"rule outside frozen scope: {platform_id}")
        if platform_id in rule_by_platform:
            raise ValueError(f"duplicate rule row: {platform_id}")
        rule_by_platform[platform_id] = row

    queue = {
        "schema_version": "pi-platform-review-queue/v1",
        "run_id": manifest["run_id"],
        "status": "worker_checked",
        "worker_shards_present": sorted(set(item["worker_shard"] for item in unique_items)),
        "missing_worker_shards": missing_shards,
        "counts": {
            "submitted": len(items),
            "unique": len(unique_items),
            "exact_url_duplicates": len(duplicate_rows),
            "rules": len(rule_by_platform),
            "by_platform": dict(sorted(Counter(item["platform_id"] for item in unique_items).items())),
        },
        "items": unique_items,
        "duplicates": duplicate_rows,
    }
    raw = json.dumps(queue, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    queue["queue_digest_sha256"] = hashlib.sha256(raw).hexdigest()
    (args.run_dir / "review_queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fieldnames = [
        "platform_id", "platform_name", "official_rule_sources", "discovery_route", "readback_route",
        "login_requirement", "allowed_metadata", "interaction_caveats", "rate_or_automation_caveats",
        "fallback", "last_checked_at", "reviewer_status", "notes",
    ]
    extra_fields = sorted({key for row in rule_rows for key in row} - set(fieldnames))
    fieldnames.extend(extra_fields)
    with (args.run_dir / "platform_rules.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for platform_id in manifest["required_platforms"]:
            if platform_id in rule_by_platform:
                writer.writerow(rule_by_platform[platform_id])
    print(json.dumps(queue["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
