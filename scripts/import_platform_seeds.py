#!/usr/bin/env python3
"""Import previously curator-accepted Top 50 items as seeds for the 47 × 10 library."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "research" / "run-pi-agent-runtime-20260826" / "curated-top50.json"
NEW = ROOT / "research" / "run-pi-platform10-20260826" / "candidates.json"
PLATFORM_MAP = {
    "GitHub": "github",
    "YouTube": "youtube",
    "Official Web": "official_web",
    "V2EX": "v2ex",
    "Substack": "substack",
    "知乎": "zhihu",
    "SegmentFault": "segmentfault",
    "Linux.do": "linuxdo",
    "掘金": "juejin",
    "InfoQ": "infoq",
    "Hacker News": "hacker_news",
    "DEV.to": "devto",
    "Bilibili": "bilibili",
    "arXiv": "arxiv_openreview",
}


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:42] or "item"


def main() -> int:
    old_items = json.loads(OLD.read_text(encoding="utf-8"))["items"]
    current = json.loads(NEW.read_text(encoding="utf-8"))
    existing = {
        item["candidate_id"]: item for item in current.get("items", [])
        if item.get("provenance") != "research/run-pi-agent-runtime-20260826/curated-top50.json"
    }
    imported = 0
    for old in old_items:
        if "deepseek-ai/deepseek-harness" in old["url"] and "llm-pi-ai" not in old["url"]:
            continue
        actual = old.get("actual_platform") or old["platform"]
        platform_id = PLATFORM_MAP.get(actual)
        if not platform_id:
            raise ValueError(f"unmapped previous platform: {actual}")
        candidate_id = f"seed-{platform_id}-{old['curator_rank']:02d}-{slug(old['title'])}"
        existing[candidate_id] = {
            "candidate_id": candidate_id,
            "platform_id": platform_id,
            "title": old["title"],
            "canonical_url": old["url"],
            "creator_name": old["author"],
            "published_at": old.get("published_at", "unknown"),
            "date_basis": "page metadata verified in previous curated run",
            "accessed_at": "2026-08-26",
            "language": "zh" if actual in {"知乎", "SegmentFault", "Linux.do", "掘金", "InfoQ", "Bilibili"} else "en",
            "content_type": old["content_type"],
            "content_track": old["track"],
            "summary": old["finding"],
            "why_useful": f"上一轮 Top 50 已完成原页回读与主审，可直接支撑“{old['track']}”学习路径。",
            "discovery_backend": f"previous_run:{old['platform']}",
            "readback_backend": "previous_run_original_page",
            "evidence_status": "accepted",
            "limitations": "复用 2026-08-26 冻结研究包；版本或互动等易变字段仍以原页当前状态为准。",
            "query_id": "seed-previous-top50",
            "curator_order": old["curator_rank"],
            "provenance": "research/run-pi-agent-runtime-20260826/curated-top50.json",
        }
        imported += 1
    current["items"] = sorted(existing.values(), key=lambda item: (item["platform_id"], item.get("curator_order", 10_000), item["candidate_id"]))
    NEW.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"imported": imported, "excluded_dsh_only": len(old_items) - imported, "total": len(current["items"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
