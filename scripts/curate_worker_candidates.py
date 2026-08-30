#!/usr/bin/env python3
"""Promote explicitly selected, re-read worker candidates into candidates.json.

This is a fail-closed mechanical helper for the curator. It never selects by
score or quota: every candidate ID must be named, must carry worker readback
evidence, and its URL must have no existing normalized equivalent.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from build_platform_library import normalized_url


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
READBACK_OVERRIDE_FIELDS = {
    "title",
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
    "limitations",
    "query_id",
    "readback_locator",
    "readback_observation",
    "readback_content_sha256",
    "platform_object_id",
}


def load_readbacks(path: Path | None) -> dict[str, dict]:
    """Load curator readback records keyed by candidate ID.

    A readback file is an append-friendly JSONL evidence artifact.  The helper
    accepts only a narrow field allowlist so it cannot silently change URL or
    platform identity while promoting an item.
    """
    if path is None:
        return {}
    records: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            candidate_id = str(record.get("candidate_id", "")).strip()
            if not candidate_id:
                raise ValueError(f"{path.name}:{line_no}: missing candidate_id")
            if candidate_id in records:
                raise ValueError(f"{path.name}:{line_no}: duplicate {candidate_id}")
            unknown = set(record) - READBACK_OVERRIDE_FIELDS - {"candidate_id"}
            if unknown:
                raise ValueError(f"{path.name}:{line_no}: unsupported fields {sorted(unknown)}")
            for required in (
                "title", "creator_name", "published_at", "date_basis",
                "summary", "why_useful", "readback_backend",
                "readback_locator", "readback_observation",
            ):
                if not str(record.get(required, "")).strip():
                    raise ValueError(f"{path.name}:{line_no}: empty {required}")
            if len(str(record["summary"]).strip()) < 18:
                raise ValueError(f"{path.name}:{line_no}: summary is too thin")
            records[candidate_id] = record
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_ids", nargs="+")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--reviewer", default="primary-curator-codex")
    parser.add_argument(
        "--reviewed-at",
        default=date.today().isoformat(),
        help="curator review date (ISO-8601; defaults to today)",
    )
    parser.add_argument(
        "--readback-file",
        type=Path,
        help="JSONL with independently verified metadata and readback evidence",
    )
    parser.add_argument(
        "--allow-curator-readback",
        action="store_true",
        help="allow a discovery-only row only after the curator independently read the original",
    )
    args = parser.parse_args()

    queue_path = args.run_dir / "review_queue.json"
    candidate_path = args.run_dir / "candidates.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    document = json.loads(candidate_path.read_text(encoding="utf-8"))
    readbacks = load_readbacks(args.readback_file)
    by_id = {item["candidate_id"]: item for item in queue.get("items", [])}
    requested = list(dict.fromkeys(args.candidate_ids))
    missing = [candidate_id for candidate_id in requested if candidate_id not in by_id]
    if missing:
        raise ValueError(f"unknown review-queue candidate IDs: {missing}")

    existing_ids = {item["candidate_id"] for item in document.get("items", [])}
    existing_urls = {normalized_url(item["canonical_url"]): item["candidate_id"] for item in document.get("items", [])}
    promoted = []
    for candidate_id in requested:
        item = by_id[candidate_id]
        if item.get("evidence_status") != "worker_checked":
            raise ValueError(f"{candidate_id}: not worker_checked")
        curator_readback = item.get("readback_backend") == "not_read_back_discovery_only"
        if curator_readback and not args.allow_curator_readback:
            raise ValueError(f"{candidate_id}: discovery-only candidate cannot be promoted")
        if curator_readback and candidate_id not in readbacks:
            raise ValueError(
                f"{candidate_id}: discovery-only promotion needs a --readback-file record"
            )
        if candidate_id in existing_ids:
            raise ValueError(f"{candidate_id}: already present in candidates.json")
        url = normalized_url(item["canonical_url"])
        if url in existing_urls:
            raise ValueError(f"{candidate_id}: normalized URL duplicates {existing_urls[url]}")
        accepted = dict(item)
        if candidate_id in readbacks:
            accepted.update({
                field: value
                for field, value in readbacks[candidate_id].items()
                if field in READBACK_OVERRIDE_FIELDS
            })
        accepted["canonical_url"] = url
        accepted["evidence_status"] = "accepted"
        if curator_readback:
            # The evidence record must name the concrete original-page/detail
            # backend; never replace it with an unauditable generic label.
            accepted["readback_backend"] = readbacks[candidate_id]["readback_backend"]
        accepted["curator_reviewer"] = args.reviewer
        accepted["curator_reviewed_at"] = args.reviewed_at
        accepted["limitations"] = (
            accepted.get("limitations", "")
            + f" 主策展人已于 {args.reviewed_at} 独立回读原页并核对主题、作者、日期与 URL；"
            "技术断言仍按条目所述版本和局限解释。"
        ).strip()
        document.setdefault("items", []).append(accepted)
        existing_ids.add(candidate_id)
        existing_urls[url] = candidate_id
        promoted.append(candidate_id)

    document["items"] = sorted(
        document["items"],
        key=lambda item: (item["platform_id"], item.get("curator_order", 10_000), item["candidate_id"]),
    )
    candidate_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"promoted": promoted, "accepted_total": len(document["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
