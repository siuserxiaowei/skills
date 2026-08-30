#!/usr/bin/env python3
"""Validate the isolated Hugging Face, GitLab, and Gitee research shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_INPUT = Path(__file__).with_name("code-hosts-candidates.jsonl")
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
PLATFORMS = {"huggingface", "gitlab", "gitee"}
EXPECTED_COUNTS = {"huggingface": 10, "gitlab": 10, "gitee": 2}
CONTENT_TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    rows: list[dict] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
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
                raise ValueError(f"line {line_no}: missing {missing}")
            empty = sorted(field for field in REQUIRED if not str(row[field]).strip())
            if empty:
                raise ValueError(f"line {line_no}: empty fields {empty}")
            if row["platform_id"] not in PLATFORMS:
                raise ValueError(f"line {line_no}: unexpected platform {row['platform_id']!r}")
            if row["evidence_status"] != "curator_review_ready":
                raise ValueError(
                    f"line {line_no}: status must be curator_review_ready, got "
                    f"{row['evidence_status']!r}"
                )
            if row["content_track"] not in CONTENT_TRACKS:
                raise ValueError(f"line {line_no}: invalid content_track")
            if len(row["summary"].strip()) < 18 or len(row["why_useful"].strip()) < 8:
                raise ValueError(f"line {line_no}: summary/why_useful is too thin")
            parsed = urlsplit(str(row["canonical_url"]).strip())
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError(f"line {line_no}: invalid public HTTPS URL")
            if row["candidate_id"] in seen_ids:
                raise ValueError(f"line {line_no}: duplicate candidate_id")
            normalized_url = (
                parsed.scheme.lower(), parsed.hostname.lower(),
                parsed.path.rstrip("/") or "/", parsed.query,
            )
            normalized_key = json.dumps(normalized_url)
            if normalized_key in seen_urls:
                raise ValueError(f"line {line_no}: duplicate normalized URL")
            seen_ids.add(row["candidate_id"])
            seen_urls.add(normalized_key)
            intents[row["platform_id"]].add(row["query_id"])
            rows.append(row)

    counts = Counter(row["platform_id"] for row in rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError(f"unexpected counts: {dict(counts)}")
    for platform_id in sorted(PLATFORMS):
        if len(intents[platform_id]) < 2:
            raise ValueError(f"{platform_id}: fewer than two query intents")

    print(json.dumps({
        "input": str(args.input),
        "items": len(rows),
        "counts": dict(sorted(counts.items())),
        "query_intents": {
            platform_id: sorted(values)
            for platform_id, values in sorted(intents.items())
        },
        "status": "curator_review_ready",
        "accepted": 0,
        "shortages_to_10": {
            platform_id: max(0, 10 - counts[platform_id])
            for platform_id in sorted(PLATFORMS)
        },
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
