#!/usr/bin/env python3
"""Fail-closed validator, deduplicator, and ranker for reviewed research bundles."""

from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import math
import re
import shutil
import socket
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

try:
    from lineage_contract import (
        LineageError,
        validate_curator_against_rank_bundle,
        validate_rank_input_manifest,
        validate_source_outcome_bindings,
    )
except ImportError:  # pragma: no cover - supports importlib-based unit tests
    import importlib.util

    _LINEAGE_PATH = Path(__file__).with_name("lineage_contract.py")
    _LINEAGE_SPEC = importlib.util.spec_from_file_location(
        "top50_lineage_contract", _LINEAGE_PATH
    )
    if _LINEAGE_SPEC is None or _LINEAGE_SPEC.loader is None:
        raise
    _LINEAGE = importlib.util.module_from_spec(_LINEAGE_SPEC)
    _LINEAGE_SPEC.loader.exec_module(_LINEAGE)
    LineageError = _LINEAGE.LineageError
    validate_curator_against_rank_bundle = (
        _LINEAGE.validate_curator_against_rank_bundle
    )
    validate_rank_input_manifest = _LINEAGE.validate_rank_input_manifest
    validate_source_outcome_bindings = _LINEAGE.validate_source_outcome_bindings


TRACKING_PARAMETERS = {
    "fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref", "ref_src",
    "spm", "xhstrackerid",
}
TRACKING_PREFIXES = ("utm_",)
PUBLISHABLE_GRADES = {"strong", "medium"}
REQUIRED_TEXT_FIELDS = (
    "id", "platform", "url", "title", "excerpt", "accessed_at", "author",
    "content_type", "published_at",
)
UNKNOWN_MARKERS = {
    "n/a", "na", "not available", "not known", "unknown", "不详", "未知",
    "暂无", "未提供",
}
SUPPORT_TYPES = {"fact", "inference", "assumption"}
SCORE_WEIGHTS = {
    "relevance": 35.0,
    "source_quality": 20.0,
    "evidence": 20.0,
    "engagement": 15.0,
    "freshness": 10.0,
}
ENGAGEMENT_KEYS = ("views", "likes", "comments", "shares", "stars", "forks")
ENGAGEMENT_COEFFICIENTS = {
    "views": 0.05, "likes": 1.0, "comments": 2.0,
    "shares": 3.0, "stars": 1.0, "forks": 2.0,
}
HANDLED_COVERAGE = {"complete", "partial", "blocked", "rejected", "not_applicable"}
SOURCE_SUMMARY_STATUSES = {"fetched", "verified", "blocked", "rejected"}
SOURCE_REVIEWABLE_SUMMARIES = {"fetched", "verified"}
PRIMARY_SOURCE_TYPES = {
    "primary", "official", "original_author", "original_data",
    "original_code", "original_document", "direct_observation",
}
PLACEHOLDERS = {"", "主题", "请填写主题", "请替换为真实主题", "{{topic}}", "<主题>"}
PACKAGE_FILES = {
    "ranking.json", "top.json", "rejected.json", "run_summary.json",
    "package_validation.json", "run_manifest.json", "candidates.json",
    "queries.tsv", "sources.tsv", "source_outcomes.jsonl", "evidence_cards.tsv",
    "platform_coverage.tsv", "source_gap_backlog.md", "report.md",
}


@dataclass
class ResearchContext:
    manifest: dict[str, Any]
    queries: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    source_outcomes: list[dict[str, Any]]
    evidence_cards: list[dict[str, Any]]
    platform_coverage: list[dict[str, Any]]


@dataclass
class RankingResult:
    selected: list[dict[str, Any]]
    rejected: list[dict[str, Any]]
    dedup_clusters: list[dict[str, Any]]
    near_duplicate_reviews: list[dict[str, Any]]
    summary: dict[str, Any]


def normalized_topic(value: str) -> str:
    topic = unicodedata.normalize("NFKC", value).strip()
    if len(topic) >= 2 and (
        (topic.startswith("《") and topic.endswith("》"))
        or (topic.startswith("【") and topic.endswith("】"))
    ):
        topic = topic[1:-1].strip()
    folded = re.sub(r"\s+", "", topic).casefold()
    template = bool(
        re.fullmatch(r"\{\{[^{}]+\}\}", topic)
        or re.fullmatch(r"<[^<>]+>", topic)
    )
    generic_placeholder = folded in {
        *PLACEHOLDERS, "待填写", "待补充", "tbd", "todo", "placeholder",
    }
    if template or generic_placeholder or not re.search(r"[\w\u4e00-\u9fff]", topic):
        raise ValueError("topic must be a real, non-placeholder string")
    return topic


def normalized_text(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", folded)


def normalized_unknown(value: Any) -> Any:
    """Collapse explicit unknown metadata markers to the contract value."""
    if isinstance(value, str) and unicodedata.normalize("NFKC", value).strip().casefold() in UNKNOWN_MARKERS:
        return "unknown"
    return value


def normalized_candidate_metadata(row: dict[str, Any]) -> dict[str, Any]:
    """Copy a candidate and normalize only contract-defined metadata aliases."""
    item = dict(row)
    if "platform" not in item and "platform_id" in item:
        item["platform"] = item["platform_id"]
    if "excerpt" not in item and "summary" in item:
        item["excerpt"] = item["summary"]
    if "author" not in item and "creator_name" in item:
        item["author"] = item["creator_name"]
    item["author"] = normalized_unknown(item.get("author"))
    item["published_at"] = normalized_unknown(item.get("published_at"))
    item["platform_id"] = item.get("platform_id") or item.get("platform")
    item["creator_name"] = item.get("creator_name") or item.get("author")
    item["summary"] = item.get("summary") or item.get("excerpt")
    return item


def add_contract_score_fields(row: dict[str, Any]) -> None:
    """Expose deterministic-v2 components under the research-contract field names."""
    components = row.get("score_components", {})
    for name in SCORE_WEIGHTS:
        row[f"{name}_score"] = components.get(name, 0.0)


def markdown_text(value: Any, *, single_line: bool = False) -> str:
    """Serialize untrusted plain text without allowing Markdown/HTML structure."""
    text = unicodedata.normalize("NFKC", str(value))
    text = "".join(
        " " if char in "\r\n" and single_line else char
        for char in text
        if char in "\n\r\t" or (ord(char) >= 32 and not 0x7F <= ord(char) <= 0x9F)
    )
    text = re.sub(r"[\u202a-\u202e\u2066-\u2069]", "", text)
    for char in ("\\", "`", "*", "_", "[", "]", "<", ">", "|", "#", "+", "-", "~", "$", "!"):
        text = text.replace(char, "\\" + char)
    return re.sub(r"\s+", " ", text).strip() if single_line else text


def markdown_url(value: str) -> str:
    """Serialize an already validated public URL for a Markdown destination."""
    parts = urlsplit(value)
    path = quote(parts.path, safe="/%:@!$&'*+,;=-._~")
    query = quote(parts.query, safe="=&;%:@!$'*+,/-._~")
    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))


def _resolved_ip_addresses(host: str) -> tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, ...]:
    """Resolve a hostname for this validation; an unresolved host is not public."""
    try:
        infos = socket.getaddrinfo(host, None)
        return tuple(sorted({ipaddress.ip_address(info[4][0]) for info in infos}, key=str))
    except (OSError, ValueError):
        return ()


def _literal_ip_address(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """Recognize standard and legacy IPv4 spellings before treating a host as DNS."""
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        try:
            return ipaddress.ip_address(socket.inet_aton(host))
        except OSError:
            return None


def is_safe_public_url(value: Any, *, resolve_dns: bool = True) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(char.isspace() or ord(char) < 32 for char in value)
    ):
        return False
    try:
        parts = urlsplit(value.strip())
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            return False
        if parts.username is not None or parts.password is not None or "\\" in value:
            return False
        _ = parts.port
        host = parts.hostname.rstrip(".").casefold()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        literal = _literal_ip_address(host)
        addresses = [literal] if literal is not None else []
        if not addresses and resolve_dns:
            addresses = list(_resolved_ip_addresses(host))
            if not addresses:
                return False
        for address in addresses:
            if not address.is_global:
                return False
        return True
    except (ValueError, UnicodeError):
        return False


def canonical_url(value: str) -> str:
    """Normalize exact URL identity; HTTP and HTTPS share one public identity."""
    parts = urlsplit(value.strip())
    host = (parts.hostname or "").casefold().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    port = parts.port
    url_host = f"[{host}]" if ":" in host else host
    netloc = url_host if not port or port in {80, 443} else f"{url_host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if key.casefold() not in TRACKING_PARAMETERS
        and not any(key.casefold().startswith(prefix) for prefix in TRACKING_PREFIXES)
    ]
    safe_path = quote(path, safe="/%:@!$&'()*+,;=-._~")
    return urlunsplit(("https", netloc, safe_path, urlencode(sorted(query)), ""))


def content_fingerprint(row: dict[str, Any]) -> str:
    inspected_content = (
        row.get("body_fingerprint")
        or row.get("transcript_fingerprint")
        or row.get("content_fingerprint_input")
        or row.get("excerpt", "")
    )
    payload = normalized_text(
        "|".join(
            str(value)
            for value in (
                row.get("title", ""),
                row.get("author", ""),
                row.get("published_at", ""),
                inspected_content,
            )
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bounded_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 100.0:
        return None
    return number * 100.0 if 0.0 <= number <= 1.0 else number


def observed_engagement(row: dict[str, Any]) -> float | None:
    metrics = row.get("engagement")
    if not isinstance(metrics, dict) or not metrics:
        return None
    weighted = 0.0
    observed = False
    for key in ENGAGEMENT_KEYS:
        value = metrics.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        number = float(value)
        if not math.isfinite(number) or number < 0:
            continue
        observed = True
        weighted += number * ENGAGEMENT_COEFFICIENTS[key]
    if not observed:
        return None
    return min(100.0, math.log1p(weighted) / math.log1p(10_000.0) * 100.0)


def evidence_signal(row: dict[str, Any]) -> float:
    return {"strong": 100.0, "medium": 75.0}.get(str(row.get("evidence_grade")), 0.0)


def score_candidate(row: dict[str, Any], engagement_score: float = 0.0) -> tuple[dict[str, float], float]:
    raw = {
        "relevance": bounded_number(row.get("relevance")) or 0.0,
        "source_quality": bounded_number(row.get("source_quality")) or 0.0,
        "evidence": evidence_signal(row),
        "engagement": engagement_score,
        "freshness": bounded_number(row.get("freshness")) or 0.0,
    }
    components = {
        name: round(raw[name] * weight / 100.0, 2)
        for name, weight in SCORE_WEIGHTS.items()
    }
    return components, round(sum(components.values()), 2)


def normalize_engagement(rows: list[dict[str, Any]]) -> None:
    groups: dict[str, list[tuple[dict[str, Any], float]]] = {}
    for row in rows:
        signal = observed_engagement(row)
        if signal is None:
            row["engagement_normalization"] = {
                "method": "unobserved", "platform": str(row.get("platform", "unknown")),
                "sample_size": 0, "confidence": "none", "raw_signal": None,
                "normalized_signal": None,
            }
            row["score_components"], row["total_score"] = score_candidate(row, 0.0)
            row["score"] = row["total_score"]
            add_contract_score_fields(row)
            continue
        groups.setdefault(str(row.get("platform", "unknown")), []).append((row, signal))
    for platform, observed in groups.items():
        values = [signal for _, signal in observed]
        lowest, highest = min(values), max(values)
        for row, signal in observed:
            if len(observed) < 3 or highest == lowest:
                normalized = min(signal, 100.0 * 8.0 / 15.0)
                method, confidence = "absolute_log_capped", "low"
            else:
                normalized = (signal - lowest) / (highest - lowest) * 100.0
                method, confidence = "platform_minmax_log_signal", "high"
            row["engagement_normalization"] = {
                "method": method, "platform": platform, "sample_size": len(observed),
                "confidence": confidence, "raw_signal": round(signal, 2),
                "normalized_signal": round(normalized, 2),
            }
            row["score_components"], row["total_score"] = score_candidate(row, normalized)
            row["score"] = row["total_score"]
            add_contract_score_fields(row)


def _as_rows(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be an array of objects")
    return value


def _id_index(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identifier = row.get(key)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"{label} has missing {key}")
        if identifier in result:
            raise ValueError(f"duplicate {label} ID: {identifier}")
        result[identifier] = row
    return result


def _platform_value(row: dict[str, Any], label: str) -> str:
    """Return one non-empty platform value and reject ambiguous aliases."""
    platform = row.get("platform")
    platform_id = row.get("platform_id")
    for field, value in (("platform", platform), ("platform_id", platform_id)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{label} has invalid {field}")
    if isinstance(platform, str) and isinstance(platform_id, str) and platform != platform_id:
        raise ValueError(f"{label} has conflicting platform aliases")
    value = platform if isinstance(platform, str) else platform_id
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} missing platform")
    return value


def _platform_counts(rows: list[Any], label: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{label} row {index + 1} must be an object")
        platform = _platform_value(row, f"{label} row {index + 1}")
        counts[platform] = counts.get(platform, 0) + 1
    return counts


def validate_context(context: ResearchContext, rows: list[Any], topic: str) -> None:
    manifest = context.manifest
    if not isinstance(manifest, dict):
        raise ValueError("research context manifest must be an object")
    for field in ("schema_version", "run_id", "scope", "phases", "counts"):
        if field not in manifest:
            raise ValueError(f"research context manifest missing {field}")
    scope = manifest.get("scope")
    if not isinstance(scope, dict) or normalized_topic(str(scope.get("topic", ""))) != topic:
        raise ValueError("research context topic does not match candidates")
    phases = manifest.get("phases")
    if isinstance(phases, list):
        phases = {str(item.get("stage")): item.get("status") for item in phases if isinstance(item, dict)}
    if not isinstance(phases, dict):
        raise ValueError("research context phases must be an object or stage list")
    for stage in ("scope", "discovery", "fetch", "extraction", "worker_check", "curator_acceptance"):
        if phases.get(stage) not in {"complete", "completed"}:
            raise ValueError(f"research context phase not complete: {stage}")

    curator = manifest.get("curator")
    curator_id = curator.get("id") if isinstance(curator, dict) else manifest.get("curator_id")
    workers = manifest.get("workers", [])
    worker_ids = {
        item.get("id") for item in workers if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    worker_ids.update({row.get("worker_id") for row in rows if isinstance(row, dict) and row.get("worker_id")})
    if not isinstance(curator_id, str) or not curator_id:
        raise ValueError("curator identity is required")
    if curator_id in worker_ids:
        raise ValueError("curator must be independent from every worker")

    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("research context counts must be an object")
    actual_counts = {
        "candidates": len(rows), "queries": len(context.queries), "sources": len(context.sources),
        "evidence_cards": len(context.evidence_cards), "platforms": len(context.platform_coverage),
    }
    for label, actual in actual_counts.items():
        if counts.get(label) != actual:
            singular = {"queries": "query", "sources": "source"}.get(label, label.rstrip("s"))
            raise ValueError(f"{singular} count mismatch: manifest={counts.get(label)!r}, actual={actual}")
    discovered = counts.get("discovered")
    if not isinstance(discovered, int) or isinstance(discovered, bool) or discovered != len(rows):
        raise ValueError("discovered candidate count is not conserved")

    candidate_platform_counts = _platform_counts(rows, "candidate")
    coverage_by_platform: dict[str, dict[str, Any]] = {}
    for item in context.platform_coverage:
        platform = _platform_value(item, "platform coverage row")
        if platform in coverage_by_platform:
            raise ValueError(f"duplicate platform coverage: {platform}")
        coverage_by_platform[platform] = item
        status = item.get("coverage_status") or item.get("status")
        if status not in HANDLED_COVERAGE:
            raise ValueError(f"platform coverage is pending or invalid: {platform}")
        for key in ("discovered_count", "fetched_count", "eligible_count", "blocked_count", "rejected_count"):
            value = item.get(key, 0)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"invalid coverage count {platform}.{key}")
        discovered_count = int(item.get("discovered_count", 0))
        fetched_count = int(item.get("fetched_count", 0))
        eligible_count = int(item.get("eligible_count", 0))
        if fetched_count > discovered_count or eligible_count > fetched_count:
            raise ValueError(f"platform coverage stage counts are impossible: {platform}")
        terminal = eligible_count + int(item.get("blocked_count", 0)) + int(item.get("rejected_count", 0))
        if terminal != discovered_count:
            raise ValueError(f"platform coverage counts are not conserved: {platform}")
    if sum(int(item.get("discovered_count", 0)) for item in context.platform_coverage) != discovered:
        raise ValueError("manifest and platform coverage discovered counts do not match")
    coverage_candidate_counts = {
        platform: int(item.get("discovered_count", 0))
        for platform, item in coverage_by_platform.items()
        if int(item.get("discovered_count", 0)) > 0
    }
    if candidate_platform_counts != coverage_candidate_counts:
        raise ValueError("candidate platform counts and platform coverage disagree")
    manifest_coverage = manifest.get("coverage")
    if manifest_coverage is not None:
        manifest_rows = _as_rows(manifest_coverage, "manifest coverage")
        manifest_by_platform: dict[str, dict[str, Any]] = {}
        for item in manifest_rows:
            platform = _platform_value(item, "manifest coverage row")
            if platform in manifest_by_platform:
                raise ValueError(f"duplicate manifest coverage: {platform}")
            manifest_by_platform[platform] = item
        if set(manifest_by_platform) != set(coverage_by_platform):
            raise ValueError("manifest and platform coverage ledgers disagree")
        for platform, item in coverage_by_platform.items():
            manifest_item = manifest_by_platform[platform]
            for key in (
                "coverage_status", "discovered_count", "fetched_count",
                "eligible_count", "blocked_count", "rejected_count",
            ):
                manifest_value = manifest_item.get(key, manifest_item.get("status") if key == "coverage_status" else 0)
                context_value = item.get(key, item.get("status") if key == "coverage_status" else 0)
                if manifest_value != context_value:
                    raise ValueError(
                        f"manifest and platform coverage ledgers disagree: {platform}.{key}"
                    )
    required = scope.get("required_platforms", [])
    if not isinstance(required, list):
        raise ValueError("required_platforms must be an array")
    if any(not isinstance(platform, str) or not platform for platform in required):
        raise ValueError("required_platforms must contain non-empty strings")
    if len(required) != len(set(required)):
        raise ValueError("required_platforms must not contain duplicates")
    for platform in required:
        if platform not in coverage_by_platform:
            raise ValueError(f"required platform lacks coverage: {platform}")
    query_platform_counts: dict[str, int] = {}
    query_candidate_counts: dict[str, int] = {}
    for item in context.queries:
        platform = _platform_value(item, "query row")
        if platform not in coverage_by_platform:
            raise ValueError(f"query platform lacks coverage: {platform}")
        for field in ("query", "backend", "executed_at", "status", "candidate_count"):
            if field not in item or item[field] in (None, ""):
                raise ValueError(f"query row missing {field}")
        if item.get("status") not in HANDLED_COVERAGE:
            raise ValueError(f"query has pending or invalid status: {item.get('query')}")
        if not isinstance(item.get("candidate_count"), int) or item["candidate_count"] < 0:
            raise ValueError("query candidate_count must be a non-negative integer")
        query_platform_counts[platform] = query_platform_counts.get(platform, 0) + 1
        query_candidate_counts[platform] = query_candidate_counts.get(platform, 0) + int(item["candidate_count"])
    for platform, coverage in coverage_by_platform.items():
        if query_candidate_counts.get(platform, 0) < int(coverage.get("discovered_count", 0)):
            raise ValueError(f"query candidate counts do not cover discoveries: {platform}")
    for platform in required:
        status = coverage_by_platform[platform].get("coverage_status") or coverage_by_platform[platform].get("status")
        if status == "complete" and query_platform_counts.get(str(platform), 0) < 2:
            raise ValueError(f"required complete platform needs at least two queries: {platform}")
    if scope.get("claim_20_plus_platforms"):
        handled = sum(1 for item in context.platform_coverage if (item.get("coverage_status") or item.get("status")) in HANDLED_COVERAGE)
        recalled = sum(1 for item in context.platform_coverage if int(item.get("discovered_count", 0)) > 0)
        if handled < 20 or recalled < 12:
            raise ValueError("20+ platform completion claim lacks 20 handled and 12 recalled platforms")

    # Check the source ledger's local coverage invariant before validating its
    # cross-artifact outcome binding.  This preserves the most actionable
    # failure when a source names a platform absent from the coverage ledger.
    for source in context.sources:
        platform = _platform_value(source, "source row")
        if platform not in coverage_by_platform:
            raise ValueError(f"source platform lacks coverage: {platform}")

    try:
        validate_source_outcome_bindings(
            run_id=str(manifest["run_id"]),
            queries=context.queries,
            sources=context.sources,
            source_outcomes=context.source_outcomes,
        )
    except LineageError as exc:
        raise ValueError(f"source outcome contract validation failed: {exc}") from exc

    source_index = _id_index(context.sources, "source_id", "source")
    outcome_index = _id_index(
        context.source_outcomes,
        "outcome_digest_sha256",
        "source outcome",
    )
    referenced_outcomes: set[str] = set()
    successful_source_counts: dict[str, int] = {}
    for source in context.sources:
        platform = _platform_value(source, "source row")
        if platform not in coverage_by_platform:
            raise ValueError(f"source platform lacks coverage: {platform}")
        if source.get("status") not in SOURCE_SUMMARY_STATUSES:
            raise ValueError(f"source has pending or invalid status: {source.get('source_id')}")
        source_outcome_digest = str(
            source.get("source_outcome_digest_sha256")
        )
        outcome = outcome_index.get(source_outcome_digest)
        if outcome is None:
            raise ValueError(
                f"source outcome is missing: {source.get('source_id')}"
            )
        if source_outcome_digest in referenced_outcomes:
            raise ValueError(
                "multiple source rows must not share one source outcome"
            )
        referenced_outcomes.add(source_outcome_digest)
        if (
            source.get("query_id") != outcome.get("query_id")
            or platform != outcome.get("platform_id")
            or source.get("url") != outcome.get("url")
        ):
            raise ValueError(
                f"source outcome binding mismatch: {source.get('source_id')}"
            )
        if source.get("status") in SOURCE_REVIEWABLE_SUMMARIES and not is_safe_public_url(source.get("url")):
            raise ValueError(f"source is not a safe public URL: {source.get('source_id')}")
        if source.get("status") in SOURCE_REVIEWABLE_SUMMARIES:
            successful_source_counts[platform] = successful_source_counts.get(platform, 0) + 1
    evidence_index = _id_index(context.evidence_cards, "evidence_id", "evidence card")
    for card in context.evidence_cards:
        if card.get("reviewer_id") != curator_id:
            raise ValueError(f"evidence card reviewer is not the run curator: {card.get('evidence_id')}")
        source = source_index.get(str(card.get("source_id")))
        if source is None:
            raise ValueError(f"evidence card source is missing: {card.get('evidence_id')}")
        outcome = outcome_index.get(
            str(source.get("source_outcome_digest_sha256"))
        )
        if source.get("status") not in SOURCE_REVIEWABLE_SUMMARIES:
            continue
        if (
            outcome is None
            or outcome.get("source_status") != "fetched"
            or outcome.get("may_enter_general_review") is not True
        ):
            continue
        if not is_safe_public_url(card.get("source_url")):
            raise ValueError(f"evidence card source is not a safe public URL: {card.get('evidence_id')}")
        if canonical_url(str(card.get("source_url", ""))) != canonical_url(str(source.get("url", ""))):
            raise ValueError(f"evidence card source URL mismatch: {card.get('evidence_id')}")
        for field in ("claim", "access_date", "excerpt_or_observation"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise ValueError(f"evidence card missing {field}: {card.get('evidence_id')}")
        try:
            datetime.fromisoformat(str(card["access_date"]).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"evidence card has invalid access_date: {card.get('evidence_id')}"
            ) from exc
        if card.get("supports") not in SUPPORT_TYPES:
            raise ValueError(
                f"evidence card supports must be one of {sorted(SUPPORT_TYPES)}: "
                f"{card.get('evidence_id')}"
            )
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not is_safe_public_url(row.get("url")):
            continue
        candidate_platform = _platform_value(row, f"candidate row {index + 1}")
        candidate_url = canonical_url(str(row["url"]))
        evidence_ids = row.get("evidence_ids")
        if not isinstance(evidence_ids, list):
            continue
        for evidence_id in evidence_ids:
            card = evidence_index.get(str(evidence_id))
            source = source_index.get(str(card.get("source_id"))) if card else None
            if (
                source is not None
                and source.get("status") in SOURCE_REVIEWABLE_SUMMARIES
                and canonical_url(str(source.get("url", ""))) == candidate_url
                and _platform_value(source, "source row") != candidate_platform
            ):
                raise ValueError(
                    f"candidate direct source platform mismatch: {row.get('id') or row.get('candidate_id')}"
                )
    for platform, coverage in coverage_by_platform.items():
        fetched_count = int(coverage.get("fetched_count", 0))
        if successful_source_counts.get(platform, 0) < fetched_count:
            raise ValueError(f"source counts do not support fetched coverage: {platform}")
    # The indexes are constructed here so malformed bundles fail before ranking.
    if not evidence_index and rows:
        raise ValueError("research context has no evidence cards")


def publication_reasons(row: Any, context: ResearchContext) -> list[str]:
    if not isinstance(row, dict):
        return ["candidate_not_object"]
    reasons: list[str] = []
    for field in REQUIRED_TEXT_FIELDS:
        if not isinstance(row.get(field), str) or not row[field].strip():
            reasons.append(f"missing_{field}")
    if not is_safe_public_url(row.get("url")):
        reasons.append("invalid_public_url")
    if row.get("reviewer_status") != "accepted":
        reasons.append("reviewer_not_accepted")
    if row.get("evidence_grade") not in PUBLISHABLE_GRADES:
        reasons.append("evidence_grade_not_publishable")
    for field in ("relevance", "source_quality", "freshness"):
        if bounded_number(row.get(field)) is None:
            reasons.append(f"invalid_{field}")
    for field in ("accessed_at", "published_at"):
        value = row.get(field)
        if field == "published_at" and value == "unknown":
            continue
        if not isinstance(value, str):
            reasons.append(f"invalid_{field}")
            continue
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            reasons.append(f"invalid_{field}")
    metrics = row.get("engagement")
    if metrics is not None and not isinstance(metrics, dict):
        reasons.append("invalid_engagement")
    elif isinstance(metrics, dict):
        for key, value in metrics.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
                reasons.append(f"invalid_engagement_{key}")

    evidence_ids = row.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids or any(not isinstance(item, str) for item in evidence_ids):
        reasons.append("missing_evidence_ids")
        return reasons
    card_index = {str(item.get("evidence_id")): item for item in context.evidence_cards}
    source_index = {str(item.get("source_id")): item for item in context.sources}
    outcome_index = {
        str(item.get("outcome_digest_sha256")): item
        for item in context.source_outcomes
    }
    accepted_grades: list[str] = []
    accepted_urls: list[str] = []
    scope = context.manifest.get("scope", {})
    primary_only = isinstance(scope, dict) and scope.get("source_policy") == "primary_only"
    for evidence_id in evidence_ids:
        card = card_index.get(evidence_id)
        if card is None:
            reasons.append(f"evidence_card_missing:{evidence_id}")
            continue
        if card.get("reviewer_status") != "accepted":
            reasons.append(f"evidence_card_not_accepted:{evidence_id}")
            continue
        if card.get("evidence_grade") not in PUBLISHABLE_GRADES:
            reasons.append(f"evidence_card_not_publishable:{evidence_id}")
            continue
        source = source_index.get(str(card.get("source_id")))
        if source is None or source.get("status") not in SOURCE_REVIEWABLE_SUMMARIES:
            reasons.append(f"evidence_source_not_publishable:{evidence_id}")
            continue
        outcome = outcome_index.get(
            str(source.get("source_outcome_digest_sha256"))
        )
        if (
            outcome is None
            or outcome.get("source_status") != "fetched"
            or outcome.get("may_enter_general_review") is not True
        ):
            reasons.append(
                f"evidence_source_outcome_not_reviewable:{evidence_id}"
            )
            continue
        if primary_only:
            source_type = str(source.get("source_type") or "").strip().casefold()
            if source_type not in PRIMARY_SOURCE_TYPES:
                reasons.append(f"evidence_source_not_primary:{evidence_id}")
                continue
            if card.get("evidence_grade") != "strong":
                reasons.append(f"primary_source_evidence_not_strong:{evidence_id}")
                continue
        accepted_grades.append(str(card["evidence_grade"]))
        accepted_urls.append(canonical_url(str(card["source_url"])))
    if accepted_grades:
        strongest = "strong" if "strong" in accepted_grades else "medium"
        if row.get("evidence_grade") != strongest:
            reasons.append("candidate_evidence_grade_mismatch")
        if is_safe_public_url(row.get("url")) and canonical_url(str(row["url"])) not in accepted_urls:
            reasons.append("accepted_evidence_url_mismatch")
    return reasons


def _near_duplicate_reviews(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for index, left in enumerate(rows):
        for right in rows[index + 1:]:
            left_text = normalized_text(f"{left.get('title', '')} {left.get('excerpt', '')}")
            right_text = normalized_text(f"{right.get('title', '')} {right.get('excerpt', '')}")
            if not left_text or not right_text:
                continue
            similarity = SequenceMatcher(None, left_text, right_text).ratio()
            if similarity >= 0.92 and left["content_fingerprint"] != right["content_fingerprint"]:
                reviews.append({
                    "candidate_ids": sorted([str(left["id"]), str(right["id"])]),
                    "similarity": round(similarity, 4), "status": "manual_review_required",
                })
                left["dedupe_review_required"] = True
                right["dedupe_review_required"] = True
    return sorted(reviews, key=lambda item: item["candidate_ids"])


def rank_candidates(
    rows: list[Any], top_n: int = 50, *, context: ResearchContext | None = None,
    topic: str | None = None,
) -> RankingResult:
    if context is None:
        raise ValueError("research context is required; candidate self-report is insufficient")
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 100:
        raise ValueError("top_n must be an integer from 1 to 100")
    identifiers: list[str] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        identifier = raw.get("id") or raw.get("candidate_id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("every candidate object must have a stable ID")
        identifiers.append(identifier)
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        raise ValueError(f"duplicate candidate IDs: {', '.join(duplicates)}")
    resolved_topic = normalized_topic(topic or str(context.manifest.get("topic", "")))
    validate_context(context, rows, resolved_topic)

    prepared: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            rejected.append({"id": f"invalid-{index + 1}", "raw_value": raw, "rejection_reasons": ["candidate_not_object"]})
            continue
        item = normalized_candidate_metadata(raw)
        item["id"] = item.get("id") or item.get("candidate_id")
        item["candidate_id"] = item["id"]
        if isinstance(item.get("url"), str) and is_safe_public_url(item.get("url")):
            item["canonical_url"] = canonical_url(item["url"])
        else:
            item["canonical_url"] = ""
        item["content_fingerprint"] = content_fingerprint(item)
        item["dedupe_review_required"] = False
        prepared.append(item)
    normalize_engagement(prepared)

    # Exact identity is transitive across canonical URL, platform-native ID, and
    # exact content fingerprint. Near similarity is only a review signal below.
    parent = list(range(len(prepared)))

    def find(position: int) -> int:
        while parent[position] != position:
            parent[position] = parent[parent[position]]
            position = parent[position]
        return position

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    owners: dict[tuple[str, str], int] = {}
    for index, item in enumerate(prepared):
        identities: list[tuple[str, str]] = []
        if item["canonical_url"] and is_safe_public_url(item.get("url")):
            identities.append(("url", item["canonical_url"]))
        platform_id = str(item.get("platform_native_id") or item.get("native_id") or "")
        if platform_id:
            identities.append((f"native:{item.get('platform', '')}", platform_id))
        if normalized_text(f"{item.get('title', '')}|{item.get('excerpt', '')}"):
            identities.append(("content", item["content_fingerprint"]))
        if not identities:
            identities.append(("invalid", str(item["id"])))
        for identity in identities:
            if identity in owners:
                union(index, owners[identity])
            else:
                owners[identity] = index

    exact_groups: dict[int, list[dict[str, Any]]] = {}
    for index, item in enumerate(prepared):
        exact_groups.setdefault(find(index), []).append(item)

    unique: list[dict[str, Any]] = []
    clusters: list[dict[str, Any]] = []
    for members in exact_groups.values():
        members.sort(key=lambda row: (-row["total_score"], row["canonical_url"], str(row["id"])))
        representative = members[0]
        unique.append(representative)
        if len(members) > 1:
            same_url = len({row["canonical_url"] for row in members}) < len(members)
            same_native = len({
                (str(row.get("platform", "")), str(row.get("platform_native_id") or row.get("native_id") or ""))
                for row in members if row.get("platform_native_id") or row.get("native_id")
            }) < sum(1 for row in members if row.get("platform_native_id") or row.get("native_id"))
            same_content = len({row["content_fingerprint"] for row in members}) < len(members)
            reason = "+".join(name for name, matched in (
                ("canonical_url", same_url), ("platform_native_id", same_native),
                ("content_fingerprint", same_content),
            ) if matched) or "transitive_exact_identity"
            clusters.append({
                "member_candidate_ids": sorted(str(row["id"]) for row in members),
                "representative_candidate_id": str(representative["id"]),
                "dedup_reason": reason,
                "canonical_url": representative["canonical_url"],
            })
            for duplicate in members[1:]:
                duplicate_reasons = []
                if duplicate["canonical_url"] == representative["canonical_url"]:
                    duplicate_reasons.append("duplicate_canonical_url")
                if duplicate["content_fingerprint"] == representative["content_fingerprint"]:
                    duplicate_reasons.append("duplicate_content_fingerprint")
                if (
                    duplicate.get("platform") == representative.get("platform")
                    and (duplicate.get("platform_native_id") or duplicate.get("native_id"))
                    == (representative.get("platform_native_id") or representative.get("native_id"))
                    and (duplicate.get("platform_native_id") or duplicate.get("native_id"))
                ):
                    duplicate_reasons.append("duplicate_platform_native_id")
                duplicate["rejection_reasons"] = duplicate_reasons or ["duplicate_transitive_exact_identity"]
                rejected.append(duplicate)

    near_reviews = _near_duplicate_reviews(unique)
    eligible: list[dict[str, Any]] = []
    for row in unique:
        reasons = publication_reasons(row, context)
        if reasons:
            row["rejection_reasons"] = sorted(set(reasons))
            rejected.append(row)
        else:
            eligible.append(row)
    eligible.sort(key=lambda row: (-row["total_score"], row["canonical_url"], str(row["id"])))
    selected = eligible[:top_n]
    for overflow in eligible[top_n:]:
        overflow["rejection_reasons"] = ["below_top_n_cutoff"]
        rejected.append(overflow)
    for rank, row in enumerate(selected, 1):
        row["rank"] = rank
    platform_counts: dict[str, int] = {}
    for row in selected:
        platform_counts[str(row["platform"])] = platform_counts.get(str(row["platform"]), 0) + 1
    shortfall = max(0, top_n - len(selected))
    if len(selected) + len(rejected) != len(rows):
        raise ValueError("candidate count conservation failed")
    summary = {
        "input_count": len(rows), "unique_count": len(unique),
        "eligible_unique_count": len(eligible), "requested_top_n": top_n,
        "selected_count": len(selected), "rejected_count": len(rejected),
        "exact_duplicate_count": len(rows) - len(unique),
        "near_duplicate_review_count": len(near_reviews), "shortfall": shortfall,
        "top_n_filled": shortfall == 0, "count_conservation_passed": True,
        "platform_counts": dict(sorted(platform_counts.items())),
        "completion_label": f"本次检索范围内 Top {top_n}" if shortfall == 0 else f"本次检索范围内合格结果 {len(selected)} 条",
        "requested_top_n": top_n, "actual_count": len(selected),
        "ranking_version": "deterministic-v2",
    }
    return RankingResult(selected, rejected, sorted(clusters, key=lambda row: row["representative_candidate_id"]), near_reviews, summary)


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} JSON: {exc}") from exc


def _read_tsv(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except OSError as exc:
        raise ValueError(f"cannot read {label} TSV: {exc}") from exc
    if not rows:
        raise ValueError(f"{label} TSV is empty")
    for row in rows:
        for key in ("candidate_count", "discovered_count", "fetched_count", "eligible_count", "blocked_count", "rejected_count"):
            if key in row and row[key] not in (None, ""):
                try:
                    row[key] = int(row[key])
                except ValueError as exc:
                    raise ValueError(f"{label} has invalid integer {key}") from exc
    return rows


def load_bundle(args: argparse.Namespace) -> tuple[str, list[Any], ResearchContext]:
    lineage_manifest = getattr(args, "lineage_manifest", None)
    curator_acceptance = getattr(args, "curator_acceptance", None)
    if lineage_manifest is None or curator_acceptance is None:
        raise ValueError(
            "--lineage-manifest and --curator-acceptance are required"
        )
    try:
        raw_curator = curator_acceptance.read_bytes()
        curator = json.loads(raw_curator.decode("utf-8"))
        if not isinstance(curator, dict):
            raise ValueError("curator acceptance root must be an object")
        run_id = curator.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("curator acceptance run_id is required")
        frozen = validate_rank_input_manifest(lineage_manifest, run_id)
        validate_curator_against_rank_bundle(curator, frozen, run_id)
    except (LineageError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"rank input lineage validation failed: {exc}") from exc
    paths = frozen["paths"]
    expected_paths = {
        "input": args.input,
        "manifest": args.manifest,
        "queries": args.queries,
        "sources": args.sources,
        "source_outcomes": args.source_outcomes,
        "evidence_cards": args.evidence_cards,
        "platform_coverage": args.platform_coverage,
    }
    manifest_keys = {
        "input": "candidates",
        "manifest": "run_manifest",
        "queries": "queries",
        "sources": "sources",
        "source_outcomes": "source_outcomes",
        "evidence_cards": "evidence_cards",
        "platform_coverage": "platform_coverage",
    }
    if any(
        value is None
        or Path(value).resolve(strict=False) != paths[manifest_keys[key]]
        for key, value in expected_paths.items()
    ):
        raise ValueError("rank CLI paths do not match the frozen lineage manifest")
    parsed = frozen["inputs"]
    payload = parsed["candidates"]
    if isinstance(payload, list):
        payload = {"candidates": payload}
    topic = normalized_topic(
        str(payload.get("topic") or parsed["run_manifest"].get("topic") or "")
    )
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidates must be an array")
    context = ResearchContext(
        manifest=parsed["run_manifest"],
        queries=parsed["queries"],
        sources=parsed["sources"],
        source_outcomes=parsed["source_outcomes"],
        evidence_cards=parsed["evidence_cards"],
        platform_coverage=parsed["platform_coverage"],
    )
    return topic, candidates, context


def _write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def report_markdown(topic: str, result: RankingResult) -> str:
    summary = result.summary
    lines = [
        f"# {markdown_text(topic, single_line=True)}：{summary['completion_label']}", "",
        f"- 目标条数：{summary['requested_top_n']}",
        f"- 合格且证据关联通过：{summary['selected_count']}",
        f"- 未入选/重复：{summary['rejected_count']}",
    ]
    if summary["shortfall"]:
        lines += [
            f"- 缺口：{summary['shortfall']}（不以低质量内容填充）", "",
            "> 状态：未达到完整 Top N；只能发布为阶段性 Top K。",
        ]
    lines += ["", "## 排名", ""]
    for row in result.selected:
        safe_title = markdown_text(row["title"], single_line=True)
        lines += [
            f"### {row['rank']}. [{safe_title}]({markdown_url(row['canonical_url'])})", "",
            f"- 平台：{markdown_text(row['platform'], single_line=True)} | 总分：{row['total_score']} | 证据：{markdown_text(row['evidence_grade'], single_line=True)}",
            f"- 作者：{markdown_text(row['author'], single_line=True)} | 内容类型：{markdown_text(row['content_type'], single_line=True)}",
            f"- 发布：{markdown_text(row['published_at'], single_line=True)} | 访问：{markdown_text(row['accessed_at'], single_line=True)}",
            f"- 摘要：{markdown_text(row['excerpt'])}",
            f"- 分项：`{json.dumps(row['score_components'], ensure_ascii=False, sort_keys=True)}`", "",
        ]
    lines += ["## 缺口与未入选", ""]
    for row in result.rejected:
        safe_id = markdown_text(row.get("id", "unknown"), single_line=True)
        safe_reasons = ", ".join(
            markdown_text(item, single_line=True)
            for item in row.get("rejection_reasons", [])
        )
        lines.append(f"- {safe_id}：{safe_reasons}")
    if not result.rejected:
        lines.append("- 无。")
    lines.append("")
    return "\n".join(lines)


def gap_backlog_markdown(context: ResearchContext, result: RankingResult) -> str:
    """Render only mechanically observed gaps, with no invented source conclusions."""
    summary = result.summary
    lines = [
        "# Source gap backlog", "",
        "> 本页只记录结构化账本可直接证明的缺口，不代表来源语义已经由脚本判断。",
        "", "## Top N 缺口", "",
        f"- 请求：{summary['requested_top_n']} 条",
        f"- 实际合格：{summary['selected_count']} 条",
        f"- 短缺：{summary['shortfall']} 条",
    ]
    if summary["shortfall"]:
        lines.append("- 最小补验：继续处理待访问或覆盖不完整的平台，并由独立 curator 验收新增证据卡后重跑排序。")
    else:
        lines.append("- 当前无数量短缺；仍需人工复核语义支持、冲突与排名敏感性。")

    lines += ["", "## 覆盖缺口", ""]
    incomplete = [
        row for row in context.platform_coverage
        if (row.get("coverage_status") or row.get("status")) in {"partial", "blocked", "rejected"}
    ]
    if not incomplete:
        lines.append("- 账本未记录 partial / blocked / rejected 平台。")
    for row in incomplete:
        platform = markdown_text(row.get("platform") or row.get("platform_id") or "unknown", single_line=True)
        status = markdown_text(row.get("coverage_status") or row.get("status") or "unknown", single_line=True)
        note = row.get("next_verification_step") or row.get("notes") or "补充合法访问路径并记录复核结果"
        lines.append(
            f"- {platform}：{status}；最小补验：{markdown_text(note, single_line=True)}"
        )

    reasons: dict[str, int] = {}
    for row in result.rejected:
        for reason in row.get("rejection_reasons", []):
            reasons[str(reason)] = reasons.get(str(reason), 0) + 1
    lines += ["", "## 未入选原因摘要", ""]
    if not reasons:
        lines.append("- 无未入选条目。")
    for reason, count in sorted(reasons.items()):
        lines.append(f"- {markdown_text(reason, single_line=True)}：{count}")
    lines += [
        "", "## 人工补验提醒", "",
        "- 核对每张 accepted 证据卡的 claim 是否不宽于摘录。",
        "- 检查转载链、来源独立性、反证、冲突和未知字段。",
        "- 若存在近似内容标记，人工决定是否为同稿；脚本不会自动删除。",
        "",
    ]
    return "\n".join(lines)


def validate_package(path: Path, result: RankingResult) -> dict[str, Any]:
    """Read back the ranking package and verify its machine-checkable invariants."""
    actual_files = {item.name for item in path.iterdir() if item.is_file()}
    if actual_files != PACKAGE_FILES - {"package_validation.json"}:
        missing = sorted((PACKAGE_FILES - {"package_validation.json"}) - actual_files)
        unexpected = sorted(actual_files - PACKAGE_FILES)
        raise ValueError(
            f"incomplete package; missing={missing!r}, unexpected={unexpected!r}"
        )
    ranking = _read_json(path / "ranking.json", "ranking package")
    top = _read_json(path / "top.json", "top package")
    rejected = _read_json(path / "rejected.json", "rejected package")
    if not all(isinstance(value, dict) for value in (ranking, top, rejected)):
        raise ValueError("package JSON roots must be objects")
    top_items = top.get("items")
    rejected_items = rejected.get("items")
    if not isinstance(top_items, list) or not isinstance(rejected_items, list):
        raise ValueError("package top and rejected items must be arrays")
    if len(top_items) + len(rejected_items) != result.summary["input_count"]:
        raise ValueError("package candidate count conservation failed")
    if [row.get("rank") for row in top_items] != list(range(1, len(top_items) + 1)):
        raise ValueError("package ranks are not contiguous")
    for row in top_items:
        components = row.get("score_components")
        if not isinstance(components, dict) or not math.isclose(
            sum(components.values()), row.get("total_score", math.nan), abs_tol=0.011
        ):
            raise ValueError("package score components do not sum to total")
    return {
        "status": "pass",
        "required_files": sorted(PACKAGE_FILES),
        "structural_validation_passed": True,
        "count_conservation_passed": True,
        "contiguous_ranks_passed": True,
        "score_recalculation_passed": True,
        "semantic_truth_proven": False,
        "note": "Structure and references passed; source-support semantics still require curator judgment.",
    }


def write_package(output_dir: Path, topic: str, rows: list[Any], context: ResearchContext, result: RankingResult) -> None:
    if output_dir.exists():
        raise ValueError(f"output directory must not already exist: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=str(output_dir.parent)))
    try:
        completion_gate = {
            "status": "pass" if result.summary["top_n_filled"] else "shortfall",
            "completion_claim_allowed": result.summary["top_n_filled"],
            "shortfall": result.summary["shortfall"],
            "reason_codes": [] if result.summary["top_n_filled"] else ["insufficient_accepted_unique_candidates"],
        }
        ranking = {
            "schema_version": "2.0", "topic": topic,
            "requested_top": result.summary["requested_top_n"],
            "requested_top_n": result.summary["requested_top_n"],
            "actual_count": result.summary["selected_count"],
            "ranking_version": "deterministic-v2",
            "ranked_candidates": result.selected, "dedup_clusters": result.dedup_clusters,
            "near_duplicate_reviews": result.near_duplicate_reviews,
            "excluded_candidates": result.rejected,
            "score_model": {"name": "deterministic-v2", "weights": SCORE_WEIGHTS},
            "completion_gate": completion_gate,
        }
        json_files = {
            "ranking.json": ranking,
            "top.json": {"topic": topic, "items": result.selected},
            "rejected.json": {"topic": topic, "items": result.rejected},
            "run_summary.json": {"topic": topic, **result.summary},
            "run_manifest.json": context.manifest,
            "candidates.json": {"topic": topic, "candidates": rows},
        }
        for name, value in json_files.items():
            (temporary / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _write_tsv(temporary / "queries.tsv", context.queries)
        _write_tsv(temporary / "sources.tsv", context.sources)
        (temporary / "source_outcomes.jsonl").write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in context.source_outcomes
            ),
            encoding="utf-8",
        )
        _write_tsv(temporary / "evidence_cards.tsv", context.evidence_cards)
        _write_tsv(temporary / "platform_coverage.tsv", context.platform_coverage)
        (temporary / "source_gap_backlog.md").write_text(
            gap_backlog_markdown(context, result), encoding="utf-8"
        )
        (temporary / "report.md").write_text(report_markdown(topic, result), encoding="utf-8")
        validation = validate_package(temporary, result)
        (temporary / "package_validation.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if {item.name for item in temporary.iterdir() if item.is_file()} != PACKAGE_FILES:
            raise ValueError("package validation output did not complete the file set")
        temporary.rename(output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="candidate JSON or complete JSON bundle")
    parser.add_argument("--manifest", type=Path, help="run_manifest.json; overrides bundled manifest")
    parser.add_argument("--queries", type=Path, help="queries.tsv; overrides bundled queries")
    parser.add_argument("--sources", type=Path, help="sources.tsv; overrides bundled sources")
    parser.add_argument(
        "--source-outcomes",
        type=Path,
        help="source_outcomes.jsonl; authoritative route outcomes",
    )
    parser.add_argument("--evidence-cards", type=Path, help="evidence_cards.tsv; overrides bundled cards")
    parser.add_argument("--platform-coverage", type=Path, help="platform_coverage.tsv; optional when manifest embeds coverage")
    parser.add_argument(
        "--lineage-manifest",
        required=True,
        type=Path,
        help="frozen top50-rank-input-manifest/v1",
    )
    parser.add_argument(
        "--curator-acceptance",
        required=True,
        type=Path,
        help="accepted top50-curator-acceptance/v1",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("research-output"))
    parser.add_argument("--top", type=int, default=50)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        topic, rows, context = load_bundle(args)
        result = rank_candidates(rows, top_n=args.top, context=context, topic=topic)
        write_package(args.output_dir, topic, rows, context, result)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
