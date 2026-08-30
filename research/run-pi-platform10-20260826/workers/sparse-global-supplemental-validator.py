#!/usr/bin/env python3
"""Validate the canonical-readback-only sparse global supplemental shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_INPUT = Path(__file__).with_name("sparse-global-supplemental-candidates.jsonl")
PLATFORMS = {
    "note", "hackernoon", "product_hunt", "substack", "docker_hub", "gitee",
}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}


def normalize_url(value: str) -> tuple[str, str, str, str]:
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public HTTPS URL: {value!r}")
    return (
        parsed.scheme.lower(), parsed.hostname.lower(),
        parsed.path.rstrip("/") or "/", parsed.query,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    rows: list[dict] = []
    seen_ids: set[str] = set()
    seen_urls: set[tuple[str, str, str, str]] = set()
    intents: dict[str, set[str]] = defaultdict(set)
    with args.input.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
            missing = sorted(REQUIRED - set(row))
            if missing:
                raise ValueError(f"line {line_no}: missing fields {missing}")
            empty = sorted(field for field in REQUIRED if not str(row[field]).strip())
            if empty:
                raise ValueError(f"line {line_no}: empty fields {empty}")
            if row["platform_id"] not in PLATFORMS:
                raise ValueError(f"line {line_no}: unexpected platform")
            if row["evidence_status"] != "curator_review_ready":
                raise ValueError(f"line {line_no}: only curator_review_ready is allowed")
            if row["content_track"] not in TRACKS:
                raise ValueError(f"line {line_no}: invalid content_track")
            if row["readback_backend"] in {
                "not_read_back_discovery_only", "search_result", "metadata_only",
            }:
                raise ValueError(f"line {line_no}: non-detail readback backend")
            if len(str(row["summary"]).strip()) < 18:
                raise ValueError(f"line {line_no}: summary too thin")
            if len(str(row["readback_evidence"]).strip()) < 30:
                raise ValueError(f"line {line_no}: readback evidence too thin")
            candidate_id = row["candidate_id"]
            if candidate_id in seen_ids:
                raise ValueError(f"line {line_no}: duplicate candidate_id")
            url = normalize_url(row["canonical_url"])
            if url in seen_urls:
                raise ValueError(f"line {line_no}: duplicate canonical URL")
            seen_ids.add(candidate_id)
            seen_urls.add(url)
            intents[row["platform_id"]].add(row["query_id"])
            rows.append(row)

    counts = Counter(row["platform_id"] for row in rows)
    print(json.dumps({
        "input": str(args.input),
        "items": len(rows),
        "counts": dict(sorted(counts.items())),
        "query_intents": {
            platform: sorted(values) for platform, values in sorted(intents.items())
        },
        "excluded_no_ready_rows": {
            "hashnode": "no Pi-primary canonical detail row",
            "pypi": "canonical project pages remained Client Challenge; metadata-only rows excluded",
            "stackoverflow": "four exact API intents returned zero strict Pi results",
            "arxiv_openreview": "one canonical paper already accepted; no novel strict item",
        },
        "evidence_status": "curator_review_ready",
        "accepted": 0,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
