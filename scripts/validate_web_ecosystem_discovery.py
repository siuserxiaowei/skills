#!/usr/bin/env python3
"""Validate the isolated seven-platform web/ecosystem research shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "research/run-pi-platform10-20260826/workers/web-ecosystem-candidates.jsonl"
PLATFORMS = {"official_web", "product_hunt", "composio", "zenn", "hackernoon", "hashnode", "note"}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name", "published_at",
    "date_basis", "accessed_at", "language", "content_type", "content_track", "summary",
    "why_useful", "discovery_backend", "readback_backend", "evidence_status", "limitations",
    "query_id", "readback_evidence",
}
ALLOWED_STATUSES = {"curator_review_ready", "metadata_only", "not_ready"}
TARGET = 15


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    rows: list[dict] = []
    ids: set[str] = set()
    urls: set[str] = set()
    intents: dict[str, set[str]] = defaultdict(set)
    with args.input.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
            missing = REQUIRED - set(item)
            if missing:
                raise ValueError(f"line {line_no}: missing fields {sorted(missing)}")
            if item["platform_id"] not in PLATFORMS:
                raise ValueError(f"line {line_no}: unexpected platform {item['platform_id']!r}")
            if item["evidence_status"] not in ALLOWED_STATUSES:
                raise ValueError(f"line {line_no}: invalid status {item['evidence_status']!r}")
            parsed = urlsplit(str(item["canonical_url"]).strip())
            if parsed.scheme != "https" or not parsed.hostname or parsed.username:
                raise ValueError(f"line {line_no}: canonical_url must be a public HTTPS URL")
            if item["candidate_id"] in ids:
                raise ValueError(f"line {line_no}: duplicate candidate_id {item['candidate_id']!r}")
            if item["canonical_url"] in urls:
                raise ValueError(f"line {line_no}: duplicate canonical_url {item['canonical_url']!r}")
            if not str(item["readback_evidence"]).strip():
                raise ValueError(f"line {line_no}: empty readback_evidence")
            if item["evidence_status"] == "curator_review_ready":
                backend = str(item["readback_backend"]).lower()
                if any(token in backend for token in ("snippet", "search_result", "not_read", "metadata_only")):
                    raise ValueError(f"line {line_no}: ready row uses non-body readback backend")
                if len(str(item["summary"]).strip()) < 20 or len(str(item["readback_evidence"]).strip()) < 40:
                    raise ValueError(f"line {line_no}: ready row lacks substantive body evidence")
            lower = " ".join(str(item.get(key, "")) for key in ("title", "summary", "why_useful", "readback_evidence")).lower()
            ambiguity = any(term in lower for term in ("raspberry pi", "pi network", "mathematical constant"))
            if ambiguity and item["evidence_status"] != "not_ready":
                raise ValueError(f"line {line_no}: ambiguous Pi object is not explicitly rejected")
            ids.add(item["candidate_id"])
            urls.add(item["canonical_url"])
            intents[item["platform_id"]].add(item["query_id"])
            rows.append(item)

    counts = Counter(item["platform_id"] for item in rows)
    status_counts = Counter((item["platform_id"], item["evidence_status"]) for item in rows)
    missing_platforms = PLATFORMS - set(counts)
    if missing_platforms:
        raise ValueError(f"missing platforms: {sorted(missing_platforms)}")
    for platform_id in PLATFORMS:
        if len(intents[platform_id]) < 2:
            raise ValueError(f"{platform_id}: fewer than two actually recorded query intents")

    # Platform-specific integrity gates derived from the frozen rules.
    for item in rows:
        url = item["canonical_url"]
        if item["platform_id"] == "product_hunt" and item["evidence_status"] == "curator_review_ready":
            if "ordinary_user_visible_product_hunt_page" not in item["readback_backend"]:
                raise ValueError("Product Hunt ready rows require ordinary user-visible browser readback")
        if item["platform_id"] == "hashnode" and "/api" in urlsplit(url).path:
            raise ValueError("Hashnode /api paths are outside this shard's authorization")
        if item["platform_id"] == "zenn" and "/search" in urlsplit(url).path:
            raise ValueError("Zenn /search is disallowed")
        if item["platform_id"] == "note" and urlsplit(url).path.startswith(("/search", "/api")):
            raise ValueError("note search/API paths are disallowed")
        if item["platform_id"] == "hackernoon" and "/lang/" in urlsplit(url).path:
            raise ValueError("HackerNoon translations of one story must not pad candidate counts")

    print(json.dumps({
        "input": str(args.input),
        "items": len(rows),
        "counts": dict(sorted(counts.items())),
        "status_counts": {
            platform_id: {status: status_counts[(platform_id, status)] for status in sorted(ALLOWED_STATUSES) if status_counts[(platform_id, status)]}
            for platform_id in sorted(PLATFORMS)
        },
        "query_intents": {platform_id: sorted(intents[platform_id]) for platform_id in sorted(PLATFORMS)},
        "shortages_to_15": {platform_id: max(0, TARGET - counts[platform_id]) for platform_id in sorted(PLATFORMS)},
        "ready_shortages_to_15": {platform_id: max(0, TARGET - status_counts[(platform_id, "curator_review_ready")]) for platform_id in sorted(PLATFORMS)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
