#!/usr/bin/env python3
"""Validate and publish the 47 × 10 Pi platform library."""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
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
REQUIRED_RULE_FIELDS = {
    "platform_id", "official_rule_sources", "discovery_route", "readback_route",
    "login_requirement", "allowed_metadata", "interaction_caveats",
    "rate_or_automation_caveats", "fallback", "last_checked_at",
}
TERMINAL_COVERAGE_STATUSES = {
    "complete", "partial", "blocked", "rejected", "not_applicable",
}
CONTENT_CLUSTER_EXCLUSIONS = "curator-content-cluster-exclusions.tsv"
CONTENT_CLUSTER_EXCLUSION_FIELDS = (
    "candidate_id",
    "kept_candidate_id",
    "cluster_basis",
    "curator_reviewer",
    "reviewed_at",
)
NAMED_SEARCH_BACKEND_ALIASES = {
    "baidu_search": {"baidu", "baidu_search"},
    "google_search": {"google", "google_search"},
    "bing_search": {"bing", "bing_search"},
}
FALLBACK_SEARCH_BACKENDS = {
    "brave", "brave_search", "ddg", "duckduckgo", "duckduckgo_search", "exa",
}
NOT_EXECUTED_MARKERS = {"", "pending", "unknown", "not_executed", "n/a"}
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


def normalized_url(raw: str) -> str:
    parsed = urlsplit(raw.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
        raise ValueError(f"invalid public URL: {raw!r}")
    host = parsed.hostname.lower() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host + port, path, parsed.query, ""))


def normalized_identity_text(raw: object) -> str:
    """Normalize human identity fields for fail-closed exact-cluster checks."""
    folded = unicodedata.normalize("NFKC", str(raw)).casefold()
    return " ".join(re.findall(r"[\w]+", folded, flags=re.UNICODE))


def identity_title_key(raw: object) -> str:
    """Normalize a title while ignoring punctuation and separator whitespace."""
    return "".join(normalized_identity_text(raw).split())


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


def normalized_backend_token(raw: object) -> str:
    """Return the declared backend, ignoring only a provenance prefix.

    Values such as ``previous_run:google_search`` remain auditable while a
    fallback such as ``exa`` cannot satisfy the named Google Search quota.
    """
    token = str(raw).strip().lower().rsplit(":", 1)[-1]
    return token.replace("-", "_").replace(" ", "_")


def uses_named_search_backend(raw: object, allowed_backends: set[str]) -> bool:
    """Accept an auditable named-engine description, never a substitute route.

    Worker evidence commonly records a concrete phrase such as
    ``google_search native web results in in-app browser`` rather than only the
    bare token ``google_search``.  Match backend identifiers on normalized
    token boundaries so those truthful descriptions pass, while values such as
    ``exa:google_search`` or ``DDG discovery then Bing`` remain disqualified.
    """
    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(raw).strip().lower().replace("-", "_"),
    ).strip("_")

    def contains_token(token: str) -> bool:
        normalized_token = re.sub(
            r"[^a-z0-9]+", "_", token.strip().lower().replace("-", "_")
        ).strip("_")
        return bool(
            normalized_token
            and re.search(
                rf"(?:^|_){re.escape(normalized_token)}(?:_|$)", normalized
            )
        )

    if any(contains_token(fallback) for fallback in FALLBACK_SEARCH_BACKENDS):
        return False
    return any(contains_token(backend) for backend in allowed_backends)


def strict_gate_errors(
    required: list[str],
    rule_by_platform: dict[str, dict[str, str]],
    coverage_by_platform: dict[str, dict[str, str]],
    queries: list[dict[str, str]],
    items_by_platform: dict[str, list[dict]],
    shortages: dict[str, int],
    sources: list[dict[str, str]] | None = None,
    evidence_cards: list[dict[str, str]] | None = None,
) -> list[str]:
    """Return every strict publication-gate violation in deterministic order."""
    errors: list[str] = []
    required_set = set(required)
    sources = sources or []
    evidence_cards = evidence_cards or []

    if shortages:
        detail = ", ".join(f"{platform_id}(-{shortages[platform_id]})" for platform_id in required if platform_id in shortages)
        errors.append(f"accepted quota shortages: {detail}")

    accepted_items = [
        item
        for platform_id in required
        for item in items_by_platform.get(platform_id, [])
    ]

    # URL uniqueness alone cannot catch a common failure mode in a multi-site
    # library: the same author publishes the same titled article on two
    # platforms under different URLs.  Exact title+creator+date identity is a
    # deterministic lower bound on content-cluster deduplication; fuzzy or
    # syndication cases still require curator review.
    exact_identity_owners: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for item in accepted_items:
        published_at = str(item.get("published_at", "")).strip().casefold()
        creator = normalized_identity_text(item.get("creator_name", ""))
        title = identity_title_key(item.get("title", ""))
        if title and creator not in {"", "unknown"} and published_at not in {"", "unknown"}:
            exact_identity_owners[(title, creator, published_at)].append(item["candidate_id"])
    duplicate_identities = [
        owners for owners in exact_identity_owners.values() if len(owners) > 1
    ]
    if duplicate_identities:
        errors.append(
            "accepted items duplicate exact title+creator+date identity: "
            + "; ".join(",".join(sorted(owners)) for owners in duplicate_identities)
        )

    accepted_ids = {item["candidate_id"] for item in accepted_items}
    sources_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    evidence_by_candidate: dict[str, list[dict[str, str]]] = defaultdict(list)
    for source in sources:
        sources_by_candidate[str(source.get("candidate_id", ""))].append(source)
    for card in evidence_cards:
        evidence_by_candidate[str(card.get("candidate_id", ""))].append(card)

    missing_source_evidence = []
    invalid_source_evidence = []
    for item in accepted_items:
        candidate_id = item["candidate_id"]
        matching_sources = sources_by_candidate.get(candidate_id, [])
        matching_cards = evidence_by_candidate.get(candidate_id, [])
        if not matching_sources or not matching_cards:
            missing = []
            if not matching_sources:
                missing.append("source")
            if not matching_cards:
                missing.append("evidence")
            missing_source_evidence.append(f"{candidate_id}[{','.join(missing)}]")
            continue
        valid_source = any(
            str(source.get("source_status", "")).strip().lower() == "accepted_readback"
            and str(source.get("readback_backend", "")).strip()
            and str(source.get("readback_backend", "")).strip().lower()
                != "not_read_back_discovery_only"
            and normalized_url(source.get("canonical_url", ""))
                == normalized_url(item["canonical_url"])
            for source in matching_sources
        )
        valid_card = any(
            str(card.get("verification_status", "")).strip().lower() == "accepted"
            and str(card.get("reviewer_status", "")).strip().lower() == "curator_accepted"
            and str(card.get("source_url", "")).strip()
            for card in matching_cards
        )
        if not valid_source or not valid_card:
            invalid_source_evidence.append(
                f"{candidate_id}[source={'ok' if valid_source else 'invalid'},"
                f"evidence={'ok' if valid_card else 'invalid'}]"
            )
    if missing_source_evidence:
        errors.append(
            "accepted items missing source/evidence ledger entries: "
            + ", ".join(missing_source_evidence)
        )
    if invalid_source_evidence:
        errors.append(
            "accepted items lack curator-accepted readback evidence: "
            + ", ".join(invalid_source_evidence)
        )

    orphan_accepted_sources = sorted(
        source.get("candidate_id", "")
        for source in sources
        if str(source.get("source_status", "")).strip().lower() == "accepted_readback"
        and source.get("candidate_id", "") not in accepted_ids
    )
    orphan_accepted_cards = sorted(
        card.get("candidate_id", "")
        for card in evidence_cards
        if str(card.get("reviewer_status", "")).strip().lower() == "curator_accepted"
        and card.get("candidate_id", "") not in accepted_ids
    )
    if orphan_accepted_sources or orphan_accepted_cards:
        errors.append(
            "accepted source/evidence ledgers contain orphan candidate IDs: "
            f"sources={','.join(orphan_accepted_sources) or '<none>'}; "
            f"evidence={','.join(orphan_accepted_cards) or '<none>'}"
        )

    rule_platforms = set(rule_by_platform)
    missing_rules = [platform_id for platform_id in required if platform_id not in rule_platforms]
    extra_rules = sorted(rule_platforms - required_set)
    if len(rule_by_platform) != 47 or missing_rules or extra_rules:
        detail = []
        if missing_rules:
            detail.append(f"missing={','.join(missing_rules)}")
        if extra_rules:
            detail.append(f"unexpected={','.join(extra_rules)}")
        errors.append(f"rules must contain exactly the 47 required platforms ({'; '.join(detail) or f'found={len(rule_by_platform)}'})")

    incomplete_rules = []
    unaccepted_rules = []
    for platform_id in required:
        rule = rule_by_platform.get(platform_id)
        if rule is None:
            continue
        missing_fields = sorted(
            field
            for field in REQUIRED_RULE_FIELDS
            if rule.get(field) is None or not str(rule.get(field, "")).strip()
        )
        if missing_fields:
            incomplete_rules.append(f"{platform_id}[{','.join(missing_fields)}]")
        reviewer_status = str(rule.get("reviewer_status", "")).strip().lower()
        if reviewer_status != "curator_accepted":
            unaccepted_rules.append(f"{platform_id}={reviewer_status or '<empty>'}")
    if incomplete_rules:
        errors.append(f"rules have empty required fields: {'; '.join(incomplete_rules)}")
    if unaccepted_rules:
        errors.append(f"rules are not curator_accepted: {', '.join(unaccepted_rules)}")

    coverage_platforms = set(coverage_by_platform)
    missing_coverage = [platform_id for platform_id in required if platform_id not in coverage_platforms]
    extra_coverage = sorted(coverage_platforms - required_set)
    if len(coverage_by_platform) != 47 or missing_coverage or extra_coverage:
        detail = []
        if missing_coverage:
            detail.append(f"missing={','.join(missing_coverage)}")
        if extra_coverage:
            detail.append(f"unexpected={','.join(extra_coverage)}")
        errors.append(f"coverage must contain exactly the 47 required platforms ({'; '.join(detail) or f'found={len(coverage_by_platform)}'})")

    invalid_coverage = []
    for platform_id in required:
        ledger = coverage_by_platform.get(platform_id)
        if ledger is None:
            continue
        status = str(ledger.get("coverage_status", "")).strip().lower()
        if status not in TERMINAL_COVERAGE_STATUSES:
            invalid_coverage.append(f"{platform_id}={status or '<empty>'}")
    if invalid_coverage:
        allowed = ",".join(sorted(TERMINAL_COVERAGE_STATUSES))
        errors.append(f"coverage has non-terminal status (allowed: {allowed}): {', '.join(invalid_coverage)}")

    executed_intents: dict[str, set[str]] = defaultdict(set)
    executed_queries: dict[str, list[dict[str, str]]] = defaultdict(list)
    for query in queries:
        platform_id = str(query.get("platform_id", "")).strip()
        intent = str(query.get("intent", "")).strip().casefold()
        executed_at = str(query.get("executed_at", "")).strip().lower()
        if platform_id in required_set and intent and executed_at not in NOT_EXECUTED_MARKERS:
            executed_intents[platform_id].add(intent)
            executed_queries[platform_id].append(query)
    insufficient_query_intents = []
    for platform_id in required:
        ledger = coverage_by_platform.get(platform_id, {})
        if str(ledger.get("coverage_status", "")).strip().lower() != "complete":
            continue
        intent_count = len(executed_intents.get(platform_id, set()))
        if intent_count < 2:
            insufficient_query_intents.append(f"{platform_id}={intent_count}")
    if insufficient_query_intents:
        errors.append(f"complete platforms need at least two distinct executed query intents: {', '.join(insufficient_query_intents)}")

    for platform_id, allowed_backends in NAMED_SEARCH_BACKEND_ALIASES.items():
        invalid_queries = []
        for query in executed_queries.get(platform_id, []):
            backend = query.get("actual_backend", "")
            if not uses_named_search_backend(backend, allowed_backends):
                invalid_queries.append(f"{query.get('query_id', '<unknown>')}={backend or '<empty>'}")
        if invalid_queries:
            errors.append(
                f"{platform_id} executed queries must use that named engine in actual_backend: "
                + ", ".join(invalid_queries)
            )
        invalid_items = []
        for item in items_by_platform.get(platform_id, []):
            backend = item.get("discovery_backend", "")
            if not uses_named_search_backend(backend, allowed_backends):
                invalid_items.append(f"{item.get('candidate_id', '<unknown>')}={backend or '<empty>'}")
        if invalid_items:
            errors.append(
                f"{platform_id} items must declare that named engine in discovery_backend: "
                + ", ".join(invalid_items)
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=ROOT / "platform-library.json")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="enforce the complete 47-platform publication acceptance gate",
    )
    args = parser.parse_args()

    manifest = load_json(args.run_dir / "run_manifest.json")
    candidate_doc = load_json(args.run_dir / "candidates.json")
    content_cluster_exclusions = load_content_cluster_exclusions(args.run_dir)
    candidate_items = candidate_doc.get("items", [])
    excluded_ids = validate_content_cluster_exclusions(
        content_cluster_exclusions,
        candidate_items,
    )
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
    for item in candidate_items:
        if item.get("candidate_id") in excluded_ids:
            continue
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
        declared_status = str(ledger.get("coverage_status", "pending") or "pending").strip().lower()
        if declared_status == "complete" and shortage:
            raise ValueError(f"{platform_id}: complete declared with only {accepted_count} accepted items")
        status = declared_status
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

    if args.strict:
        query_path = args.run_dir / "queries.tsv"
        queries = load_tsv(query_path) if query_path.exists() else []
        sources = load_tsv(args.run_dir / "sources.tsv")
        evidence_cards = load_tsv(args.run_dir / "evidence_cards.tsv")
        gate_errors = strict_gate_errors(
            required,
            rule_by_platform,
            coverage_by_platform,
            queries,
            items_by_platform,
            shortages,
            sources,
            evidence_cards,
        )
        if gate_errors:
            raise ValueError("47 x 10 strict gate failed:\n- " + "\n- ".join(gate_errors))

    payload = {
        "schema_version": "pi-platform-library-public/v1",
        "run_id": manifest["run_id"],
        "as_of": manifest["timeframe"]["end"],
        "platform_count": len(output_platforms),
        "minimum_per_platform": manifest["per_platform_minimum_accepted"],
        "accepted_total": sum(len(value) for value in items_by_platform.values()),
        "content_cluster_exclusion_count": len(content_cluster_exclusions),
        "complete_platforms": sum(platform["status"] == "complete" for platform in output_platforms),
        "shortages": shortages,
        "platforms": output_platforms,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(item["platform_id"] for item in candidate_doc.get("items", []))
    print(json.dumps({"output": str(args.output), "accepted_total": payload["accepted_total"], "counts": counts, "shortages": shortages}, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
