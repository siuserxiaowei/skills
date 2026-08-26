#!/usr/bin/env python3
"""Validate and publish the 47 × 10 Pi platform library."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
REQUIRED_ITEM_FIELDS = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations",
}
DISPLAY_NAMES = {
    "csdn": "CSDN", "wechat_official_accounts": "微信公众号", "zhihu": "知乎",
    "xiaohongshu": "小红书", "weibo": "微博", "douyin": "抖音", "x": "X / Twitter",
    "bilibili": "Bilibili", "juejin": "掘金", "youtube": "YouTube", "linuxdo": "Linux.do",
    "github": "GitHub", "baidu_search": "百度搜索", "google_search": "Google 搜索",
    "bing_search": "Bing 搜索", "toutiao": "今日头条", "36kr": "36氪", "infoq": "InfoQ",
    "segmentfault": "SegmentFault", "oschina": "开源中国", "v2ex": "V2EX", "reddit": "Reddit",
    "hacker_news": "Hacker News", "medium": "Medium", "linkedin": "LinkedIn", "kuaishou": "快手",
    "wechat_channels": "微信视频号", "tiktok": "TikTok", "official_web": "Official Web",
    "npm": "npm", "devto": "DEV.to", "stackoverflow": "Stack Overflow",
    "product_hunt": "Product Hunt", "substack": "Substack", "arxiv_openreview": "arXiv / OpenReview",
    "gitee": "Gitee", "zenn": "Zenn", "hackernoon": "HackerNoon", "qiita": "Qiita",
    "hashnode": "Hashnode", "note": "note", "huggingface": "Hugging Face", "bluesky": "Bluesky",
    "gitlab": "GitLab", "composio": "Composio", "pypi": "PyPI", "docker_hub": "Docker Hub",
}


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def normalized_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
        raise ValueError(f"invalid public URL: {raw!r}")
    host = parsed.hostname.lower() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host + port, path, parsed.query, ""))


def validate_item(item: dict, required_platforms: set[str]) -> tuple[str, str]:
    missing = sorted(REQUIRED_ITEM_FIELDS - set(item))
    if missing:
        raise ValueError(f"{item.get('candidate_id', '<unknown>')}: missing {missing}")
    if item["platform_id"] not in required_platforms:
        raise ValueError(f"{item['candidate_id']}: unknown platform {item['platform_id']}")
    if item["evidence_status"] != "accepted":
        raise ValueError(f"{item['candidate_id']}: public library only accepts curator-approved items")
    for field in ("candidate_id", "title", "creator_name", "accessed_at", "summary", "why_useful"):
        if not str(item[field]).strip():
            raise ValueError(f"{item['candidate_id']}: empty {field}")
    if len(item["summary"].strip()) < 18 or len(item["why_useful"].strip()) < 8:
        raise ValueError(f"{item['candidate_id']}: summary/why_useful is too thin")
    return item["candidate_id"], normalized_url(item["canonical_url"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=ROOT / "platform-library.json")
    parser.add_argument("--strict", action="store_true", help="require ten accepted items on every platform")
    args = parser.parse_args()

    manifest = load_json(args.run_dir / "run_manifest.json")
    candidate_doc = load_json(args.run_dir / "candidates.json")
    rules = load_tsv(args.run_dir / "platform_rules.tsv")
    coverage = load_tsv(args.run_dir / "platform_coverage.tsv")
    required = manifest["required_platforms"]
    required_set = set(required)
    if len(required) != 47 or len(required_set) != 47:
        raise ValueError("manifest must freeze exactly 47 unique required platforms")

    rule_by_platform = {row["platform_id"]: row for row in rules}
    coverage_by_platform = {row["platform_id"]: row for row in coverage}
    if len(rule_by_platform) != len(rules) or len(coverage_by_platform) != len(coverage):
        raise ValueError("duplicate platform row in rules or coverage")

    seen_ids: set[str] = set()
    seen_urls: dict[str, str] = {}
    items_by_platform: dict[str, list[dict]] = defaultdict(list)
    for item in candidate_doc.get("items", []):
        candidate_id, canonical = validate_item(item, required_set)
        if candidate_id in seen_ids:
            raise ValueError(f"duplicate candidate_id: {candidate_id}")
        if canonical in seen_urls:
            raise ValueError(f"duplicate URL: {candidate_id} and {seen_urls[canonical]}")
        seen_ids.add(candidate_id)
        seen_urls[canonical] = candidate_id
        public_item = dict(item)
        public_item["canonical_url"] = canonical
        items_by_platform[item["platform_id"]].append(public_item)

    output_platforms = []
    shortages: dict[str, int] = {}
    for platform_id in required:
        platform_items = sorted(
            items_by_platform.get(platform_id, []),
            key=lambda row: (row.get("curator_order", 10_000), row["candidate_id"]),
        )
        accepted_count = len(platform_items)
        shortage = max(0, manifest["per_platform_minimum_accepted"] - accepted_count)
        if shortage:
            shortages[platform_id] = shortage
        rule = rule_by_platform.get(platform_id, {})
        ledger = coverage_by_platform.get(platform_id, {})
        declared_status = ledger.get("coverage_status", "pending") or "pending"
        if declared_status == "complete" and shortage:
            raise ValueError(f"{platform_id}: complete declared with only {accepted_count} accepted items")
        status = "complete" if shortage == 0 else declared_status
        output_platforms.append({
            "platform_id": platform_id,
            "platform_name": ledger.get("platform_name") or rule.get("platform_name") or DISPLAY_NAMES[platform_id],
            "status": status,
            "accepted_count": accepted_count,
            "target_count": manifest["per_platform_minimum_accepted"],
            "rule": rule,
            "coverage": ledger,
            "items": platform_items,
        })

    if args.strict and shortages:
        detail = ", ".join(f"{key}(-{value})" for key, value in shortages.items())
        raise ValueError(f"47 x 10 gate failed: {detail}")

    payload = {
        "schema_version": "pi-platform-library-public/v1",
        "run_id": manifest["run_id"],
        "as_of": manifest["timeframe"]["end"],
        "platform_count": len(output_platforms),
        "minimum_per_platform": manifest["per_platform_minimum_accepted"],
        "accepted_total": sum(len(value) for value in items_by_platform.values()),
        "complete_platforms": sum(not max(0, manifest["per_platform_minimum_accepted"] - len(items_by_platform.get(pid, []))) for pid in required),
        "shortages": shortages,
        "platforms": output_platforms,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(item["platform_id"] for item in candidate_doc.get("items", []))
    print(json.dumps({"output": str(args.output), "accepted_total": payload["accepted_total"], "counts": counts, "shortages": shortages}, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
