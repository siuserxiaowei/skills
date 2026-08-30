#!/usr/bin/env python3
"""Build truthful in-progress ledgers from worker rules and review candidates.

This command records what has actually been discovered/read at worker stage. It
does not accept candidates and does not declare any platform complete.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "research" / "run-pi-platform10-20260826"
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
CONTENT_CLUSTER_EXCLUSIONS = "curator-content-cluster-exclusions.tsv"
CONTENT_CLUSTER_EXCLUSION_FIELDS = (
    "candidate_id",
    "kept_candidate_id",
    "cluster_basis",
    "curator_reviewer",
    "reviewed_at",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


_NON_EXECUTED_PROBE_RE = re.compile(
    r"^(?:blocked|unavailable|missing|not[ _-]+executed|pending|unknown|n/?a)"
    r"(?:$|\s*[:;(,-])",
    re.IGNORECASE,
)


def probe_was_executed(probe_result: str) -> bool:
    """Return whether a rule's probe represents an attempted route.

    Worker rule prose often records a successful bounded probe together with
    per-object exclusions, e.g. Docker's ``provenance-blocked`` aliases.  The
    previous substring check treated any occurrence of ``blocked`` (or
    ``missing``) as if the entire intent had not run, which erased executed
    intents from the query ledger and made the strict two-intent gate fail.
    Only an explicit terminal status at the start of the field is considered
    non-executed; explanatory mentions later in a successful/partial result do
    not invalidate the probe.
    """
    observed = " ".join(str(probe_result or "").split()).strip()
    if not observed:
        return False
    return _NON_EXECUTED_PROBE_RE.match(observed) is None


def load_content_cluster_exclusions(run_dir: Path) -> dict[str, dict[str, str]]:
    """Load the curator overlay with an exact, fail-closed TSV schema."""
    path = run_dir / CONTENT_CLUSTER_EXCLUSIONS
    if not path.exists():
        return {}

    result: dict[str, dict[str, str]] = {}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t", strict=True)
            actual_fields = tuple(reader.fieldnames or ())
            if actual_fields != CONTENT_CLUSTER_EXCLUSION_FIELDS:
                raise ValueError(
                    f"{CONTENT_CLUSTER_EXCLUSIONS}: expected exact columns "
                    f"{list(CONTENT_CLUSTER_EXCLUSION_FIELDS)}, got {list(actual_fields)}"
                )
            for line_no, row in enumerate(reader, 2):
                if None in row:
                    raise ValueError(
                        f"{CONTENT_CLUSTER_EXCLUSIONS}:{line_no}: unexpected extra column data"
                    )
                missing = sorted(
                    field
                    for field in CONTENT_CLUSTER_EXCLUSION_FIELDS
                    if row.get(field) is None or not str(row[field]).strip()
                )
                if missing:
                    raise ValueError(
                        f"{CONTENT_CLUSTER_EXCLUSIONS}:{line_no}: empty {missing}"
                    )
                candidate_id = row["candidate_id"]
                if candidate_id in result:
                    raise ValueError(
                        f"duplicate content-cluster exclusion: {candidate_id}"
                    )
                result[candidate_id] = row
    except csv.Error as exc:
        raise ValueError(f"{CONTENT_CLUSTER_EXCLUSIONS}: malformed TSV: {exc}") from exc
    return result


def validate_content_cluster_exclusions(
    exclusions: dict[str, dict[str, str]],
    accepted_items: list[dict],
) -> set[str]:
    """Validate that every overlay edge resolves to unambiguous accepted items."""
    accepted_id_counts = Counter(
        str(item.get("candidate_id", ""))
        for item in accepted_items
        if str(item.get("candidate_id", ""))
    )
    duplicate_accepted_ids = sorted(
        candidate_id
        for candidate_id, count in accepted_id_counts.items()
        if count > 1
    )
    if duplicate_accepted_ids:
        raise ValueError(
            "duplicate candidate_id in candidates.json: "
            + ",".join(duplicate_accepted_ids)
        )

    valid_accepted_ids = {
        str(item.get("candidate_id", ""))
        for item in accepted_items
        if str(item.get("candidate_id", ""))
        and item.get("evidence_status") == "accepted"
    }
    excluded_ids = set(exclusions)
    unknown_exclusions = sorted(excluded_ids - valid_accepted_ids)
    missing_kept_ids = sorted({
        row["kept_candidate_id"]
        for row in exclusions.values()
        if row["kept_candidate_id"] not in valid_accepted_ids
    })
    self_references = sorted(
        candidate_id
        for candidate_id, row in exclusions.items()
        if row["kept_candidate_id"] == candidate_id
    )
    excluded_kept_ids = sorted({
        row["kept_candidate_id"]
        for candidate_id, row in exclusions.items()
        if row["kept_candidate_id"] in excluded_ids
        and row["kept_candidate_id"] != candidate_id
    })
    if unknown_exclusions or missing_kept_ids or self_references or excluded_kept_ids:
        raise ValueError(
            "content-cluster exclusion ledger drift: "
            f"unknown_excluded={','.join(unknown_exclusions) or '<none>'}; "
            f"missing_kept={','.join(missing_kept_ids) or '<none>'}; "
            f"self_reference={','.join(self_references) or '<none>'}; "
            f"kept_is_excluded={','.join(excluded_kept_ids) or '<none>'}"
        )
    return excluded_ids


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()

    manifest = load_json(args.run_dir / "run_manifest.json")
    queue = load_json(args.run_dir / "review_queue.json")
    accepted_all = load_json(args.run_dir / "candidates.json").get("items", [])
    content_cluster_exclusions = load_content_cluster_exclusions(args.run_dir)
    excluded_ids = validate_content_cluster_exclusions(
        content_cluster_exclusions,
        accepted_all,
    )
    queue_items_all = queue.get("items", [])
    queue_items = [
        item for item in queue_items_all
        if item.get("candidate_id") not in excluded_ids
    ]
    accepted = [
        item for item in accepted_all
        if item.get("candidate_id") not in excluded_ids
    ]
    rules = load_tsv(args.run_dir / "platform_rules.tsv")
    required = manifest["required_platforms"]
    rule_by_platform = {row["platform_id"]: row for row in rules}
    worker_by_platform: dict[str, list[dict]] = defaultdict(list)
    for item in queue_items:
        worker_by_platform[item["platform_id"]].append(item)
    accepted_counts = Counter(item["platform_id"] for item in accepted)
    accepted_by_platform: dict[str, list[dict]] = defaultdict(list)
    for item in accepted:
        accepted_by_platform[item["platform_id"]].append(item)

    query_rows = []
    query_counts = Counter()
    query_candidate_counts = Counter(
        item.get("query_id", "") for item in queue_items if item.get("query_id")
    )
    all_queue_items_by_query: dict[str, list[dict]] = defaultdict(list)
    for item in queue_items_all:
        if item.get("query_id"):
            all_queue_items_by_query[item["query_id"]].append(item)
    recorded_query_ids: set[str] = set()
    for platform_id in required:
        rule = rule_by_platform.get(platform_id, {})
        raw_intents = rule.get("query_intents", "")
        intents = [value.strip() for value in raw_intents.split(";") if value.strip()]
        for intent in intents:
            original_matching_items = [
                item
                for item in all_queue_items_by_query.get(intent, [])
                if item.get("platform_id") == platform_id
            ]
            # When the frozen candidate shard already carries this exact query
            # ID, keep that authoritative ID and backend instead of emitting a
            # second synthetic ``worker-*`` copy of the same executed intent.
            query_id = (
                intent
                if original_matching_items
                else f"worker-{platform_id}-{intent}"
            )
            executed = probe_was_executed(rule.get("probe_result", ""))
            actual_backend = (
                original_matching_items[0].get("discovery_backend", "")
                if original_matching_items
                else rule.get("discovery_route", "") if executed else "not_executed"
            )
            query_rows.append({
                "query_id": query_id,
                "platform_id": platform_id,
                "intent": intent,
                "query": intent,
                "planned_backend": rule.get("discovery_route", ""),
                "actual_backend": actual_backend,
                "executed_at": rule.get("last_checked_at", "") if executed else "not_executed",
                "result_count": (
                    query_candidate_counts[intent]
                    if original_matching_items
                    else rule.get("fetched_count", "")
                ),
                "probe_result": rule.get("probe_result", "worker_rule_record"),
                "notes": "由已核验 worker 规则恢复；若平台规则未记录 query_intents，则不虚构执行记录。",
            })
            recorded_query_ids.add(query_id)
            query_counts[platform_id] += 1

    for item in queue_items:
        query_id = item.get("query_id", "")
        if not query_id or query_id in recorded_query_ids:
            continue
        platform_id = item["platform_id"]
        query_rows.append({
            "query_id": query_id,
            "platform_id": platform_id,
            "intent": query_id.rsplit("-", 1)[-1],
            "query": query_id.rsplit("-", 1)[-1],
            "planned_backend": item.get("discovery_backend", ""),
            "actual_backend": item.get("discovery_backend", ""),
            "executed_at": item.get("accessed_at", ""),
            "result_count": query_candidate_counts[query_id],
            "probe_result": "success",
            "notes": "从冻结 worker 候选的 provenance/query_id 恢复；条目仍需主策展复核。",
        })
        recorded_query_ids.add(query_id)
        query_counts[platform_id] += 1

    # Accepted records are authoritative for shared candidate IDs.  Keep the
    # remaining worker rows as a discovery backlog, and include accepted-only
    # seeds so every published item has a source/evidence ledger entry.
    accepted_by_id = {item["candidate_id"]: item for item in accepted}
    ledger_items = {
        item["candidate_id"]: item for item in queue_items
    }
    ledger_items.update(accepted_by_id)

    source_rows = []
    evidence_rows = []
    for item in sorted(
        ledger_items.values(),
        key=lambda row: (row["platform_id"], row["candidate_id"]),
    ):
        digest = hashlib.sha256(
            (item.get("title", "") + "\n" + item.get("summary", "")).encode("utf-8")
        ).hexdigest()
        source_id = f"source-{item['candidate_id']}"
        readback = item.get("readback_backend", "")
        is_accepted = item.get("evidence_status") == "accepted"
        read_back = readback != "not_read_back_discovery_only"
        source_status = (
            "accepted_readback"
            if is_accepted
            else "worker_readback_noted" if read_back else "discovery_only"
        )
        verification_status = (
            "accepted"
            if is_accepted
            else "worker_readback_noted" if read_back else "discovery_only"
        )
        source_rows.append({
            "source_id": source_id,
            "candidate_id": item["candidate_id"],
            "platform_id": item["platform_id"],
            "canonical_url": item["canonical_url"],
            "source_status": source_status,
            "readback_backend": readback,
            "accessed_at": item.get("accessed_at", ""),
            "content_digest": digest,
            "notes": " | ".join(filter(None, (
                item.get("limitations", ""),
                f"readback_locator={item.get('readback_locator')}"
                if item.get("readback_locator") else "",
                f"readback_observation={item.get('readback_observation')}"
                if item.get("readback_observation") else "",
            ))),
        })
        evidence_rows.append({
            "evidence_id": f"evidence-{item['candidate_id']}",
            "candidate_id": item["candidate_id"],
            "platform_id": item["platform_id"],
            "claim": item.get("summary", ""),
            "source_id": source_id,
            "source_url": item["canonical_url"],
            "access_date": item.get("accessed_at", ""),
            "excerpt_or_observation": item.get("summary", ""),
            "evidence_grade": "accepted" if is_accepted else item.get("worker_evidence_grade", "worker_checked"),
            "verification_status": verification_status,
            "reviewer_status": "curator_accepted" if is_accepted else "worker_checked",
            "review_notes": item.get("limitations", ""),
        })

    coverage_rows = []
    for platform_id in required:
        rule = rule_by_platform.get(platform_id, {})
        rows = worker_by_platform.get(platform_id, [])
        fetched = sum(row.get("readback_backend") != "not_read_back_discovery_only" for row in rows)
        discovered = len(rows)
        accepted_count = accepted_counts[platform_id]
        accepted_items = accepted_by_platform.get(platform_id, [])
        accepted_readback_ready = all(
            item.get("readback_backend")
            and item.get("readback_backend") != "not_read_back_discovery_only"
            for item in accepted_items
        )
        rule_accepted = rule.get("reviewer_status") == "curator_accepted"
        can_complete = (
            accepted_count >= manifest["per_platform_minimum_accepted"]
            and query_counts[platform_id] >= 2
            and accepted_readback_ready
            and rule_accepted
        )
        if can_complete:
            status = "complete"
            error = ""
            next_step = "Periodic link, rule and version revalidation"
        elif not rule:
            status = "partial" if discovered or accepted_count else "pending"
            error = "platform rule is still missing"
            next_step = "research and curator-review the platform rule before publication"
        else:
            observed = str(rule.get("coverage_state", "") or rule.get("probe_result", "")).lower()
            status = "blocked" if "block" in observed else "partial"
            error = rule.get("notes", "") if status == "blocked" else ""
            next_step = rule.get("next_step", "") or rule.get("next_safe_step", "") or rule.get("fallback", "")
        coverage_rows.append({
            "platform_id": platform_id,
            "platform_name": rule.get("platform_name", "") or DISPLAY_NAMES[platform_id],
            "tier": "required",
            "query_count": query_counts[platform_id],
            "route_count": 1 if rule else 0,
            "discovered_count": discovered,
            "fetched_count": fetched,
            "eligible_count": 0,
            "accepted_count": accepted_count,
            "blocked_count": max(0, manifest["per_platform_discovery_target"] - discovered) if status == "blocked" else 0,
            "coverage_status": status,
            "access_mode": rule.get("login_requirement", "unknown"),
            "last_checked_at": rule.get("last_checked_at", ""),
            "errors": error,
            "fallback_used": "no",
            "notes": "worker-stage ledger; discovered/fetched do not imply curator acceptance",
            "next_verification_step": next_step,
        })

    write_tsv(args.run_dir / "queries.tsv", [
        "query_id", "platform_id", "intent", "query", "planned_backend", "actual_backend",
        "executed_at", "result_count", "probe_result", "notes",
    ], query_rows)
    write_tsv(args.run_dir / "sources.tsv", [
        "source_id", "candidate_id", "platform_id", "canonical_url", "source_status",
        "readback_backend", "accessed_at", "content_digest", "notes",
    ], source_rows)
    write_tsv(args.run_dir / "evidence_cards.tsv", [
        "evidence_id", "candidate_id", "platform_id", "claim", "source_id", "source_url",
        "access_date", "excerpt_or_observation", "evidence_grade", "verification_status",
        "reviewer_status", "review_notes",
    ], evidence_rows)
    write_tsv(args.run_dir / "platform_coverage.tsv", [
        "platform_id", "platform_name", "tier", "query_count", "route_count", "discovered_count",
        "fetched_count", "eligible_count", "accepted_count", "blocked_count", "coverage_status",
        "access_mode", "last_checked_at", "errors", "fallback_used", "notes", "next_verification_step",
    ], coverage_rows)

    print(json.dumps({
        "queries": len(query_rows),
        "sources": len(source_rows),
        "evidence_cards": len(evidence_rows),
        "coverage_rows": len(coverage_rows),
        "worker_readback_noted": sum(row["source_status"] == "worker_readback_noted" for row in source_rows),
        "accepted_readback": sum(row["source_status"] == "accepted_readback" for row in source_rows),
        "accepted_total_before_exclusions": len(accepted_all),
        "accepted_total_after_exclusions": sum(accepted_counts.values()),
        "content_cluster_exclusion_count": len(content_cluster_exclusions),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
