#!/usr/bin/env python3
"""Validate the isolated public-China canonical-readback supplemental shard."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


HERE = Path(__file__).resolve().parent
RUN = HERE.parent
CANDIDATES = HERE / "china-public-gap-supplemental-candidates.jsonl"
READBACKS = HERE / "china-public-gap-curator-readbacks.jsonl"
PLATFORMS = {"zhihu", "weibo", "douyin", "toutiao", "36kr", "infoq", "oschina"}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "platform_object_id", "readback_evidence",
}
READBACK_REQUIRED = {
    "candidate_id", "title", "creator_name", "published_at", "date_basis",
    "summary", "why_useful", "readback_backend", "readback_locator",
    "readback_observation",
}
EXPECTED_SUPPLEMENTAL = {
    "china-oschina-19743475-pi-cn", "china-oschina-19741369-pi-dsh",
    "china-oschina-huiyu-pi", "china-weibo-wake-session-manager",
    "china-douyin-pi-sdk-part3", "china-toutiao-pi-deepseek-v4-flash",
}
EXPECTED_EXISTING = {
    "worker-cn-053", "worker-cn-063", "worker-cn-081", "worker-cn-083",
    "worker-cn-084", "worker-cn-065",
}


def normalize_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public HTTPS URL: {raw!r}")
    host = parsed.hostname.lower() + (f":{parsed.port}" if parsed.port else "")
    return urlunsplit(("https", host, parsed.path.rstrip("/") or "/", parsed.query, ""))


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: {exc}") from exc
    return rows


def main() -> int:
    candidates = load_jsonl(CANDIDATES)
    readbacks = load_jsonl(READBACKS)
    ids: set[str] = set()
    urls: set[str] = set()
    for line_no, row in enumerate(candidates, 1):
        missing = sorted(REQUIRED - set(row))
        empty = sorted(field for field in REQUIRED if not str(row.get(field, "")).strip())
        if missing or empty:
            raise ValueError(f"candidate line {line_no}: missing={missing} empty={empty}")
        if row["candidate_id"] in ids or normalize_url(row["canonical_url"]) in urls:
            raise ValueError(f"candidate line {line_no}: duplicate ID or URL")
        if row["platform_id"] not in PLATFORMS or row["evidence_status"] != "curator_review_ready":
            raise ValueError(f"candidate line {line_no}: invalid platform/status")
        if len(row["summary"].strip()) < 18 or len(row["readback_evidence"].strip()) < 50:
            raise ValueError(f"candidate line {line_no}: thin evidence")
        ids.add(row["candidate_id"])
        urls.add(normalize_url(row["canonical_url"]))
    if ids != EXPECTED_SUPPLEMENTAL:
        raise ValueError(f"unexpected supplemental IDs: {sorted(ids ^ EXPECTED_SUPPLEMENTAL)}")

    overlay_ids: set[str] = set()
    for line_no, row in enumerate(readbacks, 1):
        missing = sorted(READBACK_REQUIRED - set(row))
        empty = sorted(field for field in READBACK_REQUIRED if not str(row.get(field, "")).strip())
        if missing or empty or row.get("candidate_id") in overlay_ids:
            raise ValueError(f"readback line {line_no}: missing={missing} empty={empty} duplicate={row.get('candidate_id') in overlay_ids}")
        if len(row["summary"].strip()) < 18 or len(row["readback_observation"].strip()) < 30:
            raise ValueError(f"readback line {line_no}: thin readback")
        overlay_ids.add(row["candidate_id"])
    expected_overlay = EXPECTED_SUPPLEMENTAL | EXPECTED_EXISTING
    if overlay_ids != expected_overlay:
        raise ValueError(f"unexpected readback IDs: {sorted(overlay_ids ^ expected_overlay)}")

    # Supplemental URLs must be novel globally; same-ID promoted copies are allowed only later.
    global_urls: dict[str, set[str]] = {}
    for path in [RUN / "candidates.json", RUN / "review_queue.json"]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("items", []):
            if row.get("canonical_url"):
                global_urls.setdefault(normalize_url(row["canonical_url"]), set()).add(
                    str(row.get("candidate_id", ""))
                )
    for path in sorted(HERE.glob("*-candidates.jsonl")):
        if path.resolve() == CANDIDATES.resolve():
            continue
        for row in load_jsonl(path):
            if row.get("canonical_url"):
                global_urls.setdefault(normalize_url(row["canonical_url"]), set()).add(
                    str(row.get("candidate_id", ""))
                )
    collisions = []
    for row in candidates:
        owners = global_urls.get(normalize_url(row["canonical_url"]), set())
        conflicting = sorted(owner for owner in owners if owner != row["candidate_id"])
        if conflicting:
            collisions.append((row["candidate_id"], conflicting))
    if collisions:
        raise ValueError(f"global URL collisions: {collisions}")

    # Known content clusters are intentionally fail-closed in the promotion list.
    forbidden = {"worker-cn-080", "worker-cn-082", "worker-cn-054", "worker-cn-055"}
    if overlay_ids & forbidden:
        raise ValueError("excluded syndication/peripheral ID leaked into readbacks")
    print(json.dumps({
        "supplemental_items": len(candidates),
        "counts": dict(sorted(Counter(x["platform_id"] for x in candidates).items())),
        "readback_overlay_rows": len(readbacks),
        "existing_worker_ready": sorted(EXPECTED_EXISTING),
        "supplemental_ready": sorted(EXPECTED_SUPPLEMENTAL),
        "excluded_clusters": {
            "benchmark": ["worker-cn-080", "worker-cn-063"],
            "mario_talk": ["worker-cn-082", "worker-cn-064"],
            "cxuan_pi_deepseek": ["china-toutiao-pi-deepseek-v4-flash", "worker-cn-066"],
            "zhihu_segmentfault_openclaw_architecture": ["worker-cn-052", "worker-cn-058"],
            "huiyu_pi_product": ["china-oschina-huiyu-pi", "worker-global-071", "community-api-devto-3805275"],
            "imclaw_syndication": ["china-oschina-excluded-19471470", "sf-browser-47690919-imclaw"],
        },
        "global_url_collisions": 0,
        "accepted": 0,
        "status": "curator_review_ready_only",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
