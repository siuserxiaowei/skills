#!/usr/bin/env python3
"""Validate the isolated npm/PyPI/Docker Hub worker research shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "research"
    / "run-pi-platform10-20260826"
    / "workers"
    / "api-packages-candidates.jsonl"
)
REQUIRED = {
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
    "readback_evidence",
}
PLATFORMS = {"npm", "pypi", "docker_hub"}
TARGET = 15
ALLOWED_STATUSES = {"curator_review_ready", "metadata_only", "not_ready"}


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
            if row["platform_id"] not in PLATFORMS:
                raise ValueError(f"line {line_no}: unexpected platform {row['platform_id']!r}")
            if row["evidence_status"] not in ALLOWED_STATUSES:
                raise ValueError(
                    f"line {line_no}: invalid isolated-shard status {row['evidence_status']!r}"
                )
            if not str(row["readback_evidence"]).strip():
                raise ValueError(f"line {line_no}: empty readback_evidence")
            parsed = urlsplit(str(row["canonical_url"]).strip())
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError(f"line {line_no}: invalid public HTTPS URL")
            if row["candidate_id"] in seen_ids:
                raise ValueError(f"line {line_no}: duplicate candidate_id {row['candidate_id']}")
            if row["canonical_url"] in seen_urls:
                raise ValueError(f"line {line_no}: duplicate canonical_url {row['canonical_url']}")
            seen_ids.add(row["candidate_id"])
            seen_urls.add(row["canonical_url"])
            intents[row["platform_id"]].add(row["query_id"])
            rows.append(row)

    counts = Counter(row["platform_id"] for row in rows)
    status_counts = Counter(
        (row["platform_id"], row["evidence_status"])
        for row in rows
    )
    if counts["npm"] < TARGET or counts["pypi"] < TARGET:
        raise ValueError(f"npm and pypi must each reach discovery target {TARGET}: {dict(counts)}")
    for platform_id in PLATFORMS:
        if len(intents[platform_id]) < 2:
            raise ValueError(f"{platform_id}: fewer than two query intents")
    docker_aliases = [
        row
        for row in rows
        if row["platform_id"] == "docker_hub" and "description_present=False" in row["readback_evidence"]
    ]
    wrongly_ready_aliases = [
        row["candidate_id"]
        for row in docker_aliases
        if row["evidence_status"] == "curator_review_ready"
    ]
    if wrongly_ready_aliases:
        raise ValueError(
            "Docker Hub metadata-only aliases cannot be curator_review_ready: "
            + ", ".join(wrongly_ready_aliases)
        )

    print(
        json.dumps(
            {
                "input": str(args.input),
                "items": len(rows),
                "counts": dict(sorted(counts.items())),
                "status_counts": {
                    platform_id: {
                        status: status_counts[(platform_id, status)]
                        for status in sorted(ALLOWED_STATUSES)
                        if status_counts[(platform_id, status)]
                    }
                    for platform_id in sorted(PLATFORMS)
                },
                "query_intents": {
                    platform_id: sorted(values)
                    for platform_id, values in sorted(intents.items())
                },
                "shortages_to_15": {
                    platform_id: max(0, TARGET - counts[platform_id])
                    for platform_id in sorted(PLATFORMS)
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
