#!/usr/bin/env python3
"""Convert the frozen worker Markdown notes into review-queue JSONL shards.

The notes deliberately mix original-page readbacks with discovery-only rows.
Every imported row remains ``worker_checked``; the evidence grade is preserved
in ``limitations`` and discovery-only rows get an explicit no-readback marker.
Nothing produced here is curator-accepted.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "research" / "run-pi-platform10-20260826"
CHINA_NOTES = ROOT / "research" / "workers" / "china-candidates.md"
GLOBAL_NOTES = ROOT / "research" / "workers" / "international-candidates.md"

CHINA_PLATFORM_MAP = {
    "Bilibili": "bilibili",
    "CSDN": "csdn",
    "CSDN DevPress": "csdn",
    "CSDN / AtomGit": "csdn",
    "掘金": "juejin",
    "知乎": "zhihu",
    "SegmentFault": "segmentfault",
    "InfoQ": "infoq",
    "Linux.do": "linuxdo",
    "V2EX": "v2ex",
    "36氪": "36kr",
    "Gitee": "gitee",
}

GLOBAL_PLATFORM_MAP = {
    "GitHub": "github",
    "Official Web": "official_web",
    "YouTube": "youtube",
    "Hacker News": "hacker_news",
    "DEV.to": "devto",
    "Medium": "medium",
    "Substack": "substack",
    "LinkedIn": "linkedin",
    "arXiv": "arxiv_openreview",
    "npm": "npm",
}

ECOSYSTEM_PLATFORMS = {"v2ex", "official_web", "npm"}


def clean_markdown(value: str) -> str:
    return value.strip().replace("`", "")


def normalize_date(value: str) -> str:
    value = clean_markdown(value)
    if not value or value.lower().startswith("unknown"):
        return "unknown"
    match = re.match(r"(\d{4}-\d{2}(?:-\d{2})?)", value)
    return match.group(1) if match else "unknown"


def content_track(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("安全", "风险", "security", "ssrf", "permission")):
        return "批评与风险"
    if any(word in lowered for word in ("商业", "成本", "市场", "product", "commercial", "roi")):
        return "商业化"
    if any(word in lowered for word in ("架构", "源码", "runtime", "loop", "session", "compaction", "provider")):
        return "进阶"
    if any(word in lowered for word in ("扩展", "插件", "技巧", "workflow", "extension", "tool")):
        return "技巧"
    if any(word in lowered for word in ("入门", "安装", "overview", "beginner", "quickstart")):
        return "入门"
    return "生态与案例"


def base_item(
    *,
    candidate_id: str,
    platform_id: str,
    title: str,
    url: str,
    author: str,
    date: str,
    accessed_at: str,
    content_type: str,
    why_relevant: str,
    observation: str,
    grade: str,
    route: str,
    language: str,
    source_note: str,
    query_id: str,
) -> dict:
    discovery_only = grade == "D" or grade.startswith("discovery_only")
    if discovery_only:
        limitation = (
            f"原 worker 等级为 {grade}，仅完成发现或平台元数据读取；"
            "未回读正文/字幕，不得在主策展复核前标为 accepted。"
        )
        readback_backend = "not_read_back_discovery_only"
    else:
        limitation = (
            f"原 worker 等级为 {grade}，笔记记录已读取原页或原生 detail；"
            "仍须由主策展人独立回读、核对版本与近重复后才能 accepted。"
        )
        readback_backend = clean_markdown(route) or "legacy_worker_original_page"
    published_at = normalize_date(date)
    return {
        "candidate_id": candidate_id,
        "platform_id": platform_id,
        "title": clean_markdown(title),
        "canonical_url": clean_markdown(url),
        "creator_name": clean_markdown(author) or "unknown",
        "published_at": published_at,
        "date_basis": (
            "worker-recorded platform/page metadata"
            if published_at != "unknown"
            else "date not visible in frozen worker notes"
        ),
        "accessed_at": clean_markdown(accessed_at) or "2026-08-26",
        "language": language,
        "content_type": clean_markdown(content_type) or "unknown",
        "content_track": content_track(f"{why_relevant} {observation}"),
        "summary": clean_markdown(observation),
        "why_useful": clean_markdown(why_relevant),
        "discovery_backend": clean_markdown(route) or "legacy_worker_discovery",
        "readback_backend": readback_backend,
        "evidence_status": "worker_checked",
        "limitations": limitation,
        "query_id": query_id,
        "worker_evidence_grade": grade,
        "provenance": source_note,
    }


def parse_china(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| CN-\d+ \|", line):
            continue
        columns = [part.strip() for part in line.strip("|").split("|")]
        if len(columns) != 12:
            raise ValueError(f"unexpected China note column count: {line}")
        (
            note_id, platform, title, url, author, date, item_type,
            why_relevant, observation, grade, route, accessed_at,
        ) = columns
        try:
            platform_id = CHINA_PLATFORM_MAP[platform]
        except KeyError as exc:
            raise ValueError(f"unmapped China platform {platform!r}") from exc
        rows.append(base_item(
            candidate_id=f"worker-{note_id.lower()}",
            platform_id=platform_id,
            title=title,
            url=url,
            author=author,
            date=date,
            accessed_at=accessed_at,
            content_type=item_type,
            why_relevant=why_relevant,
            observation=observation,
            grade=grade,
            route=route,
            language="zh",
            source_note="research/workers/china-candidates.md",
            query_id=(
                f"worker-{platform_id}-"
                + ("architecture_extensions" if int(note_id.split("-")[1]) % 2 == 0 else "exact_pi")
            ),
        ))
    return rows


def parse_global(path: Path) -> list[dict]:
    field_pattern = re.compile(
        r"\*\*([a-z_]+):\*\*\s*(.*?)(?=\s*\|\s*\*\*[a-z_]+:\*\*|$)"
    )
    rows = []
    for match in re.finditer(r"^(\d+)\.\s+(.*)$", path.read_text(encoding="utf-8"), re.M):
        number, raw = match.groups()
        fields = dict(field_pattern.findall(raw))
        if not fields:
            continue
        missing = {
            "platform", "title", "url", "author", "date", "content_type",
            "why_relevant", "excerpt_or_observation", "evidence_grade", "route", "accessed_at",
        } - set(fields)
        if missing:
            raise ValueError(f"global note {number} missing {sorted(missing)}")
        platform = fields["platform"].strip()
        try:
            platform_id = GLOBAL_PLATFORM_MAP[platform]
        except KeyError as exc:
            raise ValueError(f"unmapped global platform {platform!r}") from exc
        rows.append(base_item(
            candidate_id=f"worker-global-{int(number):03d}",
            platform_id=platform_id,
            title=fields["title"],
            url=fields["url"],
            author=fields["author"],
            date=fields["date"],
            accessed_at=fields["accessed_at"],
            content_type=fields["content_type"],
            why_relevant=fields["why_relevant"],
            observation=fields["excerpt_or_observation"],
            grade=fields["evidence_grade"],
            route=fields["route"],
            language="en",
            source_note="research/workers/international-candidates.md",
            query_id=(
                f"worker-{platform_id}-"
                + ("architecture_ecosystem" if int(number) % 2 == 0 else "exact_pi")
            ),
        ))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=RUN_DIR)
    parser.add_argument("--china-notes", type=Path, default=CHINA_NOTES)
    parser.add_argument("--global-notes", type=Path, default=GLOBAL_NOTES)
    args = parser.parse_args()

    china = parse_china(args.china_notes)
    global_rows = parse_global(args.global_notes)
    all_rows = china + global_rows
    if len(all_rows) != 176:
        raise ValueError(f"expected frozen 176-note pool, got {len(all_rows)}")
    ids = [row["candidate_id"] for row in all_rows]
    urls = [row["canonical_url"] for row in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate candidate_id in frozen notes")
    if len(urls) != len(set(urls)):
        raise ValueError("duplicate URL in frozen notes")

    shards = {"china": [], "global": [], "ecosystem": []}
    for row in all_rows:
        if row["platform_id"] in ECOSYSTEM_PLATFORMS:
            shards["ecosystem"].append(row)
        elif row["candidate_id"].startswith("worker-cn-"):
            shards["china"].append(row)
        else:
            shards["global"].append(row)

    workers = args.run_dir / "workers"
    workers.mkdir(parents=True, exist_ok=True)
    for shard, rows in shards.items():
        rows.sort(key=lambda item: (item["platform_id"], item["candidate_id"]))
        write_jsonl(workers / f"{shard}-candidates.jsonl", rows)

    counts = {
        name: {
            "items": len(rows),
            "original_page_or_detail_noted": sum(
                row["readback_backend"] != "not_read_back_discovery_only" for row in rows
            ),
            "discovery_only": sum(
                row["readback_backend"] == "not_read_back_discovery_only" for row in rows
            ),
        }
        for name, rows in shards.items()
    }
    print(json.dumps({"total": len(all_rows), "shards": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
