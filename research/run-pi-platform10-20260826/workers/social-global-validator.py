#!/usr/bin/env python3
"""Validate the isolated canonical social-platform readback shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_INPUT = Path(__file__).with_name("social-global-candidates.jsonl")
PLATFORMS = {"x", "reddit", "medium", "linkedin", "substack", "bluesky"}
ALLOWED_STATUSES = {"curator_review_ready", "metadata_only", "not_ready"}
CONTENT_TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
EXECUTED_INTENTS = {
    "reddit": {
        "reddit-native-search-pi-coding-agent",
        "reddit-native-search-pi-coding-agent-extensions",
    },
    "x": {
        "x-latest-pi-coding-agent",
        "x-latest-pi-coding-agent-extensions",
    },
    "medium": {
        "medium-native-search-pi-coding-agent",
        "medium-native-search-pi-coding-agent-extensions",
    },
    "linkedin": {
        "linkedin-native-search-pi-coding-agent",
        "linkedin-native-search-pi-coding-agent-extensions",
    },
    "substack": {
        "substack-public-search-pi-coding-agent",
        "substack-public-search-pi-coding-agent-extensions",
    },
    "bluesky": {
        "bluesky-appview-search-pi-coding-agent",
        "bluesky-appview-search-pi-coding-agent-extensions",
    },
}


def normalized_url(value: str) -> tuple[str, str, str, str]:
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
            row = json.loads(line)
            missing = sorted(REQUIRED - set(row))
            if missing:
                raise ValueError(f"line {line_no}: missing fields {missing}")
            empty = sorted(field for field in REQUIRED if not str(row[field]).strip())
            if empty:
                raise ValueError(f"line {line_no}: empty fields {empty}")
            platform = row["platform_id"]
            if platform not in PLATFORMS:
                raise ValueError(f"line {line_no}: unexpected platform {platform!r}")
            if row["evidence_status"] not in ALLOWED_STATUSES:
                raise ValueError(f"line {line_no}: invalid evidence status")
            if row["content_track"] not in CONTENT_TRACKS:
                raise ValueError(f"line {line_no}: invalid content_track")
            if len(row["summary"].strip()) < 18 or len(row["why_useful"].strip()) < 8:
                raise ValueError(f"line {line_no}: summary/why_useful is too thin")
            candidate_id = row["candidate_id"]
            key = normalized_url(row["canonical_url"])
            if candidate_id in seen_ids:
                raise ValueError(f"line {line_no}: duplicate candidate_id")
            if key in seen_urls:
                raise ValueError(f"line {line_no}: duplicate normalized URL")
            if platform == "reddit":
                host, path = key[1], key[2]
                if host not in {"reddit.com", "www.reddit.com"} or "/comments/" not in path:
                    raise ValueError(f"line {line_no}: not a canonical Reddit thread")
            if row["query_id"] not in EXECUTED_INTENTS[platform]:
                raise ValueError(f"line {line_no}: unknown query intent")
            seen_ids.add(candidate_id)
            seen_urls.add(key)
            intents[platform].add(row["query_id"])
            rows.append(row)
    if any(row["platform_id"] == "reddit" for row in rows):
        if intents["reddit"] != EXECUTED_INTENTS["reddit"]:
            raise ValueError("Reddit rows must cover both executed query intents")
    for platform, seen in intents.items():
        ready_count = sum(
            row["platform_id"] == platform
            and row["evidence_status"] == "curator_review_ready"
            for row in rows
        )
        if ready_count and seen != EXECUTED_INTENTS[platform]:
            raise ValueError(
                f"{platform}: ready rows must cover both executed query intents"
            )
    counts = Counter(row["platform_id"] for row in rows)
    statuses = Counter(row["evidence_status"] for row in rows)
    print(json.dumps({
        "input": str(args.input),
        "items": len(rows),
        "counts": dict(sorted(counts.items())),
        "statuses": dict(sorted(statuses.items())),
        "intents": {key: sorted(value) for key, value in sorted(intents.items())},
        "shortages_to_10": {
            platform: max(0, 10 - counts[platform]) for platform in sorted(PLATFORMS)
        },
        "accepted": 0,
        "status": "worker_readback_valid",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
