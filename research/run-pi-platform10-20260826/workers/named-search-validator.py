#!/usr/bin/env python3
"""Validate the native Bing/Baidu discovery plus canonical-readback shard."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
DEFAULT_INPUT = HERE / "named-search-candidates.jsonl"
PLATFORMS = {"bing_search", "baidu_search"}
INTENTS = {
    "bing_search": {
        "bing-native-exact-pi-coding-agent",
        "bing-native-pi-coding-agent-extensions",
    },
    "baidu_search": {
        "baidu-native-exact-pi-coding-agent",
        "baidu-native-pi-coding-agent-extensions",
    },
}
REQUIRED = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}


def normalize_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public HTTPS URL: {raw!r}")
    host = parsed.hostname.lower() + (f":{parsed.port}" if parsed.port else "")
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(("https", host, path, parsed.query, ""))


def jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def collect_global_urls(input_path: Path) -> dict[str, list[tuple[str, bool]]]:
    """Return URL owners as (candidate_id, promoted-ledger-copy) tuples.

    A row already promoted into candidates.json or review_queue.json is the
    same object when its candidate_id is unchanged.  That copy must not make
    its source shard fail validation.  Worker-to-worker collisions remain
    errors even when a worker accidentally reuses an ID.
    """
    urls: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    json_paths = [RUN_DIR / "candidates.json", RUN_DIR / "review_queue.json"]
    for path in json_paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("items", []):
            if row.get("canonical_url"):
                urls[normalize_url(row["canonical_url"])].append(
                    (str(row.get("candidate_id", "")), True)
                )
    for path in sorted(HERE.glob("*-candidates.jsonl")):
        if path.resolve() == input_path.resolve():
            continue
        for row in jsonl(path):
            if row.get("canonical_url"):
                urls[normalize_url(row["canonical_url"])].append(
                    (str(row.get("candidate_id", "")), False)
                )
    return urls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()
    rows = jsonl(args.input)
    global_urls = collect_global_urls(args.input)
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    intents: dict[str, set[str]] = defaultdict(set)
    for line_no, row in enumerate(rows, 1):
        missing = sorted(REQUIRED - set(row))
        if missing:
            raise ValueError(f"line {line_no}: missing {missing}")
        empty = sorted(field for field in REQUIRED if not str(row[field]).strip())
        if empty:
            raise ValueError(f"line {line_no}: empty {empty}")
        platform = row["platform_id"]
        if platform not in PLATFORMS:
            raise ValueError(f"line {line_no}: unexpected platform {platform}")
        if row["evidence_status"] != "curator_review_ready":
            raise ValueError(f"line {line_no}: invalid evidence status")
        if row["content_track"] not in TRACKS:
            raise ValueError(f"line {line_no}: invalid track")
        if row["query_id"] not in INTENTS[platform]:
            raise ValueError(f"line {line_no}: invalid named-engine query ID")
        backend = str(row["discovery_backend"]).lower()
        expected = "bing_search" if platform == "bing_search" else "baidu_search"
        if expected not in backend or any(x in backend for x in ("ddg", "duckduckgo", "exa", "jina", "brave")):
            raise ValueError(f"line {line_no}: non-native discovery backend")
        if any(x in str(row["readback_backend"]).lower() for x in ("snippet", "search_result", "metadata_only")):
            raise ValueError(f"line {line_no}: readback is not canonical detail/body")
        if len(str(row["summary"]).strip()) < 18 or len(str(row["readback_evidence"]).strip()) < 40:
            raise ValueError(f"line {line_no}: thin summary/readback evidence")
        candidate_id = row["candidate_id"]
        url = normalize_url(row["canonical_url"])
        if candidate_id in seen_ids:
            raise ValueError(f"line {line_no}: duplicate candidate_id")
        if url in seen_urls:
            raise ValueError(f"line {line_no}: duplicate URL within shard")
        conflicting_owners = [
            owner_id
            for owner_id, promoted_copy in global_urls.get(url, [])
            if not (promoted_copy and owner_id == candidate_id)
        ]
        if conflicting_owners:
            owners = ", ".join(sorted(set(conflicting_owners)))
            raise ValueError(
                f"line {line_no}: global URL collision: {url} ({owners})"
            )
        seen_ids.add(candidate_id)
        seen_urls.add(url)
        intents[platform].add(row["query_id"])
    for platform in PLATFORMS:
        if intents[platform] != INTENTS[platform]:
            raise ValueError(f"{platform}: both actual named-engine intents are required")
    readbacks = jsonl(HERE / "named-search-curator-readbacks.jsonl")
    readback_ids = [row.get("candidate_id") for row in readbacks]
    if set(readback_ids) != seen_ids or len(readback_ids) != len(seen_ids):
        raise ValueError("curator readback overlay must match candidate IDs one-to-one")
    counts = Counter(row["platform_id"] for row in rows)
    print(json.dumps({
        "input": str(args.input),
        "items": len(rows),
        "counts": dict(sorted(counts.items())),
        "intents": {key: sorted(value) for key, value in sorted(intents.items())},
        "shortages_to_10": {p: max(0, 10 - counts[p]) for p in sorted(PLATFORMS)},
        "global_collisions": 0,
        "readback_overlay_rows": len(readbacks),
        "accepted": 0,
        "status": "native_named_engine_readback_valid",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
