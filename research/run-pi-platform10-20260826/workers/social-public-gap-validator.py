#!/usr/bin/env python3
"""Validate the bounded social/publishing public-gap supplemental shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_INPUT = Path(__file__).with_name("social-public-gap-candidates.jsonl")
DEFAULT_READBACKS = Path(__file__).with_name("social-public-gap-curator-readbacks.jsonl")
PLATFORMS = {"x", "linkedin"}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}


def normalized(value: str) -> tuple[str, str, str, str]:
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public HTTPS URL: {value!r}")
    return parsed.scheme, parsed.hostname.lower(), parsed.path.rstrip("/") or "/", parsed.query


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--readbacks", type=Path, default=DEFAULT_READBACKS)
    args = parser.parse_args()
    rows: list[dict] = []
    ids: set[str] = set()
    urls: set[tuple[str, str, str, str]] = set()
    with args.input.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = sorted(REQUIRED - set(row))
            if missing:
                raise ValueError(f"line {line_no}: missing {missing}")
            empty = sorted(field for field in REQUIRED if not str(row[field]).strip())
            if empty:
                raise ValueError(f"line {line_no}: empty {empty}")
            if row["platform_id"] not in PLATFORMS:
                raise ValueError(f"line {line_no}: platform outside shard")
            if row["evidence_status"] != "curator_review_ready":
                raise ValueError(f"line {line_no}: only curator_review_ready is allowed")
            if row["content_track"] not in TRACKS:
                raise ValueError(f"line {line_no}: bad content track")
            if len(row["summary"].strip()) < 18 or len(row["readback_evidence"].strip()) < 60:
                raise ValueError(f"line {line_no}: thin body evidence")
            candidate_id = row["candidate_id"]
            url = normalized(row["canonical_url"])
            if candidate_id in ids or url in urls:
                raise ValueError(f"line {line_no}: duplicate ID or URL")
            backend = row["readback_backend"].lower()
            if any(token in backend for token in ("serp", "snippet", "metadata_only", "not_read")):
                raise ValueError(f"line {line_no}: non-canonical evidence backend")
            host, path = url[1], url[2]
            platform = row["platform_id"]
            if platform == "x" and not (host == "x.com" and "/status/" in path):
                raise ValueError(f"line {line_no}: X row is not canonical status detail")
            if platform == "linkedin" and not (
                host.endswith("linkedin.com") and "/posts/" in path and "activity-" in path
            ):
                raise ValueError(f"line {line_no}: LinkedIn row is not a stable public post")
            ids.add(candidate_id)
            urls.add(url)
            rows.append(row)
    counts = Counter(row["platform_id"] for row in rows)
    expected = {"x": 8, "linkedin": 1}
    if dict(counts) != expected:
        raise ValueError(f"unexpected coverage: {dict(counts)} != {expected}")
    readbacks = []
    readback_ids: set[str] = set()
    with args.readbacks.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            required = {
                "candidate_id", "title", "creator_name", "published_at",
                "date_basis", "summary", "why_useful", "readback_backend",
                "readback_locator", "readback_observation",
            }
            missing = sorted(required - set(row))
            if missing:
                raise ValueError(f"readback line {line_no}: missing {missing}")
            candidate_id = row["candidate_id"]
            if candidate_id in readback_ids:
                raise ValueError(f"readback line {line_no}: duplicate candidate ID")
            if len(row["summary"].strip()) < 18 or len(row["readback_observation"].strip()) < 40:
                raise ValueError(f"readback line {line_no}: thin evidence")
            readback_ids.add(candidate_id)
            readbacks.append(row)
    expected_existing_ids = {
        "worker-global-074", "worker-global-075", "worker-global-077",
        "worker-global-080", "worker-global-081", "worker-global-082",
        "sparse-hackernoon-ssh-extension", "sparse-hackernoon-vt-theme",
        "sparse-producthunt-pi-launch",
    }
    if len(readbacks) != 18:
        raise ValueError(f"expected 18 independent readbacks, got {len(readbacks)}")
    if not ids.issubset(readback_ids):
        raise ValueError("every novel candidate must have an independent readback")
    if not expected_existing_ids.issubset(readback_ids):
        raise ValueError("missing an existing-candidate readback override")
    if "social-gap-linkedin-corey-docs" not in readback_ids:
        raise ValueError("missing novel LinkedIn readback")
    print(json.dumps({
        "input": str(args.input), "novel_candidate_items": len(rows),
        "novel_candidate_counts": dict(sorted(counts.items())),
        "independent_readbacks": len(readbacks),
        "existing_queue_id_overrides": len(expected_existing_ids),
        "novel_linkedin_candidates": 1,
        "evidence_status": "curator_review_ready", "accepted": 0,
        "boundaries": {"paywall_bypass": False, "login_bypass": False, "interaction": False,
                       "serp_as_evidence": False, "generic_hackernoon_or_producthunt_crawler": False},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
