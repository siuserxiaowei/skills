#!/usr/bin/env python3
"""Validate and inventory worker candidate shards before queue compilation.

The handoff contract refers to an ``assemble_platform_worker_shards.py``
stage.  Older snapshots did not contain that entry point even though the
worker shards were already present.  This command is intentionally
fail-closed: it never promotes candidates and never rewrites the candidate
shards.  It validates every ``*-candidates.jsonl`` row using the same minimum
schema as the queue compiler, checks cross-shard ID/URL uniqueness, and writes
an auditable, deterministic shard manifest for the next stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
}
ALLOWED_STATUS = {"worker_checked", "curator_review_ready", "metadata_only", "not_ready"}


def canonical_url(raw: object) -> str:
    parsed = urlsplit(str(raw).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public URL: {raw!r}")
    host = parsed.hostname.lower()
    if parsed.port:
        host += f":{parsed.port}"
    return urlunsplit((parsed.scheme.lower(), host, parsed.path.rstrip("/") or "/", parsed.query, ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    workers = args.run_dir / "workers"
    # Accept append-only supplemental shard names such as
    # ``docker-hub-supplemental-candidates-20260829.jsonl`` as well as the
    # original ``<shard>-candidates.jsonl`` convention.  A shard is still
    # validated row-by-row below; this is only filename discovery.
    paths = sorted(workers.glob("*-candidates*.jsonl"))
    if not paths:
        raise ValueError(f"no worker candidate shards under {workers}")

    manifest_rows = []
    seen_ids: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    duplicate_urls: list[dict[str, str]] = []
    total = 0
    for path in paths:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        rows = []
        for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
            missing = sorted(REQUIRED - set(item))
            if missing:
                raise ValueError(f"{path.name}:{line_no}: missing {missing}")
            if item["evidence_status"] not in ALLOWED_STATUS:
                raise ValueError(f"{path.name}:{line_no}: unsupported evidence_status {item['evidence_status']!r}")
            cid = str(item["candidate_id"]).strip()
            if not cid:
                raise ValueError(f"{path.name}:{line_no}: empty candidate_id")
            url = canonical_url(item["canonical_url"])
            if cid in seen_ids:
                raise ValueError(f"duplicate candidate_id {cid} in {path.name} and {seen_ids[cid]}")
            if url in seen_urls:
                # URL duplicates are an expected worker-stage condition: the
                # queue compiler keeps one deterministic representative and
                # records the alias.  Do not silently create a second object,
                # but retain the collision in this manifest for curator audit.
                duplicate_urls.append({
                    "canonical_url": url,
                    "candidate_id": cid,
                    "duplicate_of": seen_urls[url],
                    "shard": path.name,
                })
            else:
                seen_urls[url] = cid
            seen_ids[cid] = path.name
            seen_urls[url] = cid
            rows.append(item)
            total += 1
        counts = Counter(str(row["platform_id"]) for row in rows)
        manifest_rows.append({
            "shard": path.name,
            "sha256": digest,
            "records": len(rows),
            "by_platform": dict(sorted(counts.items())),
        })

    payload = {
        "schema_version": "pi-platform-worker-shard-manifest/v1",
        "run_id": json.loads((args.run_dir / "run_manifest.json").read_text(encoding="utf-8"))["run_id"],
        "candidate_shards": manifest_rows,
        "total_records": total,
        "unique_candidate_ids": len(seen_ids),
        "unique_canonical_urls": len(seen_urls),
        "exact_url_duplicates": duplicate_urls,
    }
    out = args.output or (args.run_dir / "worker_shard_manifest.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "shards": len(paths), "records": total}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
