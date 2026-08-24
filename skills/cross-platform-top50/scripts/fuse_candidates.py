#!/usr/bin/env python3
"""Deterministic discovery-candidate fusion with explicit evidence boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Iterable


CONTRACT_INPUT = "top50-fusion-input/v1"
CONTRACT_RESULT = "top50-fusion-result/v1"
ENGINE_ID = "python-fusion"
ENGINE_VERSION = "1.0.0"
RRF_K = 60

ROOT_FIELDS = {
    "contract_version",
    "run_id",
    "topic",
    "lists",
    "selection",
    "time_policy",
    "subject_author_ids",
}
LIST_FIELDS = {"list_id", "platform", "query_id", "weight", "items"}
SELECTION_FIELDS = {
    "max_results",
    "max_per_author",
    "max_first_party_per_author",
    "min_per_platform",
}
TIME_FIELDS = {"mode", "from_date", "to_date"}
REQUIRED_ITEM_FIELDS = {
    "candidate_id",
    "url",
    "title",
    "author_id",
    "published_at",
    "date_confidence",
    "source_role",
    "acquisition_method",
    "evidence_status",
}
ITEM_FIELDS = REQUIRED_ITEM_FIELDS | {"engagement"}
DATE_CONFIDENCE = {"verified", "inferred", "unknown"}
TIME_MODES = {"strict", "advisory", "unbounded"}
FIRST_PARTY_ROLES = {"first_party", "primary", "official", "original_author"}


class FusionError(ValueError):
    """A fail-closed fusion-contract violation."""


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FusionError(f"{label} must be an object")
    return value


def _array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise FusionError(f"{label} must be an array")
    return value


def _fields(value: dict[str, Any], allowed: set[str], required: set[str], label: str) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise FusionError(f"{label} has unknown fields: {', '.join(unknown)}")
    if missing:
        raise FusionError(f"{label} missing fields: {', '.join(missing)}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FusionError(f"{label} must be a non-empty trimmed string")
    return value


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise FusionError(f"{label} must be an integer >= {minimum}")
    return value


def _number(value: Any, label: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FusionError(f"{label} must be a finite number >= {minimum}")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise FusionError(f"{label} must be a finite number >= {minimum}")
    return result


def _day(value: Any, label: str) -> date:
    text = _text(value, label)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise FusionError(f"{label} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != text:
        raise FusionError(f"{label} must be canonical YYYY-MM-DD")
    return parsed


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _first_party(item: dict[str, Any], subject_author_ids: set[str]) -> bool:
    return (
        item["author_id"] in subject_author_ids
        and item["source_role"] in FIRST_PARTY_ROLES
    )


def _date_verdict(
    item: dict[str, Any], mode: str, from_date: date | None, to_date: date | None
) -> str | None:
    confidence = item["date_confidence"]
    published = item["published_at"]
    if confidence == "unknown" or published == "unknown":
        return "date_unknown" if mode == "strict" else None
    if confidence != "verified":
        return "date_not_verified" if mode == "strict" else None
    try:
        published_day = _day(published, f"candidate {item['candidate_id']}.published_at")
    except FusionError:
        return "date_invalid"
    if mode != "unbounded" and (
        (from_date is not None and published_day < from_date)
        or (to_date is not None and published_day > to_date)
    ):
        return "outside_time_window"
    return None


def _validate(request: Any) -> dict[str, Any]:
    root = _object(request, "fusion request")
    _fields(root, ROOT_FIELDS, ROOT_FIELDS, "fusion request")
    if root["contract_version"] != CONTRACT_INPUT:
        raise FusionError(f"contract_version must be {CONTRACT_INPUT}")
    _text(root["run_id"], "run_id")
    _text(root["topic"], "topic")

    selection = _object(root["selection"], "selection")
    _fields(selection, SELECTION_FIELDS, SELECTION_FIELDS, "selection")
    max_results = _integer(selection["max_results"], "selection.max_results", minimum=1)
    max_author = _integer(selection["max_per_author"], "selection.max_per_author", minimum=1)
    max_first_party = _integer(
        selection["max_first_party_per_author"],
        "selection.max_first_party_per_author",
        minimum=max_author,
    )
    min_platform = _integer(selection["min_per_platform"], "selection.min_per_platform")
    if min_platform > max_results:
        raise FusionError("selection.min_per_platform cannot exceed max_results")
    selection.update(
        {
            "max_results": max_results,
            "max_per_author": max_author,
            "max_first_party_per_author": max_first_party,
            "min_per_platform": min_platform,
        }
    )

    time_policy = _object(root["time_policy"], "time_policy")
    _fields(time_policy, TIME_FIELDS, TIME_FIELDS, "time_policy")
    mode = time_policy["mode"]
    if mode not in TIME_MODES:
        raise FusionError(f"time_policy.mode must be one of {sorted(TIME_MODES)}")
    from_date = _day(time_policy["from_date"], "time_policy.from_date")
    to_date = _day(time_policy["to_date"], "time_policy.to_date")
    if from_date > to_date:
        raise FusionError("time_policy.from_date must not follow to_date")

    subjects = _array(root["subject_author_ids"], "subject_author_ids")
    if any(not isinstance(value, str) or not value.strip() for value in subjects):
        raise FusionError("subject_author_ids must contain non-empty strings")
    if len(subjects) != len(set(subjects)):
        raise FusionError("subject_author_ids must be unique")

    lists = _array(root["lists"], "lists")
    if not lists:
        raise FusionError("lists must not be empty")
    list_ids: set[str] = set()
    candidate_identity: dict[str, tuple[str, ...]] = {}
    platforms_seen: set[str] = set()
    for list_index, raw_list in enumerate(lists):
        ranked = _object(raw_list, f"lists[{list_index}]")
        _fields(ranked, LIST_FIELDS, LIST_FIELDS, f"lists[{list_index}]")
        list_id = _text(ranked["list_id"], f"lists[{list_index}].list_id")
        if list_id in list_ids:
            raise FusionError(f"duplicate list_id: {list_id}")
        list_ids.add(list_id)
        platform = _text(ranked["platform"], f"list {list_id}.platform")
        platforms_seen.add(platform)
        _text(ranked["query_id"], f"list {list_id}.query_id")
        ranked["weight"] = _number(ranked["weight"], f"list {list_id}.weight", minimum=0.000001)
        items = _array(ranked["items"], f"list {list_id}.items")
        seen_here: set[str] = set()
        for item_index, raw_item in enumerate(items):
            candidate = _object(raw_item, f"list {list_id}.items[{item_index}]")
            _fields(
                candidate,
                ITEM_FIELDS,
                REQUIRED_ITEM_FIELDS,
                f"candidate in list {list_id}",
            )
            candidate_id = _text(candidate["candidate_id"], "candidate_id")
            if candidate_id in seen_here:
                raise FusionError(f"duplicate candidate_id {candidate_id} within list {list_id}")
            seen_here.add(candidate_id)
            for field in (
                "url",
                "title",
                "author_id",
                "published_at",
                "date_confidence",
                "source_role",
                "acquisition_method",
                "evidence_status",
            ):
                _text(candidate[field], f"candidate {candidate_id}.{field}")
            if candidate["date_confidence"] not in DATE_CONFIDENCE:
                raise FusionError(f"candidate {candidate_id} has invalid date_confidence")
            if candidate["evidence_status"] != "discovery_only":
                raise FusionError(
                    f"candidate {candidate_id} must remain discovery_only before curator review"
                )
            engagement = candidate.get("engagement")
            if engagement is not None:
                engagement = _object(engagement, f"candidate {candidate_id}.engagement")
                for metric, metric_value in engagement.items():
                    _text(metric, f"candidate {candidate_id}.engagement metric")
                    _integer(
                        metric_value,
                        f"candidate {candidate_id}.engagement.{metric}",
                    )
            identity = tuple(
                candidate[field]
                for field in (
                    "url",
                    "title",
                    "author_id",
                    "published_at",
                    "date_confidence",
                    "source_role",
                    "acquisition_method",
                    "evidence_status",
                )
            )
            previous = candidate_identity.get(candidate_id)
            if previous is not None and previous != identity:
                raise FusionError(f"candidate {candidate_id} has conflicting identity")
            candidate_identity[candidate_id] = identity
    if min_platform and len(platforms_seen) * min_platform > max_results:
        raise FusionError(
            "selection platform floor is infeasible for max_results"
        )
    return root


def _rank_key(candidate: dict[str, Any]) -> tuple[float, str]:
    return (-candidate["weighted_rrf_score"], candidate["candidate_id"])


def _select_candidates(
    ranked: list[dict[str, Any]], selection: dict[str, int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Apply a discovery-only platform floor and author caps in one pass.

    Applying the author cap to the entire ranked pool before reserving platform
    breadth would incorrectly discard an otherwise eligible low-weight platform
    candidate.  Selection therefore reserves bounded platform slots first and
    then fills by RRF rank, while every individual pick still obeys the same
    author cap.
    """

    max_results = selection["max_results"]
    floor = selection["min_per_platform"]
    baseline_ids: set[str] = set()
    baseline_author_counts: dict[str, int] = {}
    for candidate in ranked:
        if len(baseline_ids) >= max_results:
            break
        author = candidate["author_id"]
        cap = (
            selection["max_first_party_per_author"]
            if candidate["first_party_signal"]
            else selection["max_per_author"]
        )
        if baseline_author_counts.get(author, 0) >= cap:
            continue
        baseline_ids.add(candidate["candidate_id"])
        baseline_author_counts[author] = baseline_author_counts.get(author, 0) + 1
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    author_counts: dict[str, int] = {}

    def cap_for(candidate: dict[str, Any]) -> int:
        return (
            selection["max_first_party_per_author"]
            if candidate["first_party_signal"]
            else selection["max_per_author"]
        )

    def add(candidate: dict[str, Any]) -> bool:
        if candidate["candidate_id"] in selected_ids or len(selected) >= max_results:
            return False
        author = candidate["author_id"]
        if author_counts.get(author, 0) >= cap_for(candidate):
            return False
        selected.append(candidate)
        selected_ids.add(candidate["candidate_id"])
        author_counts[author] = author_counts.get(author, 0) + 1
        return True

    if floor:
        platforms = sorted(
            {platform for candidate in ranked for platform in candidate["platforms"]}
        )
        for platform in platforms:
            already_selected = sum(
                platform in candidate["platforms"] for candidate in selected
            )
            for candidate in ranked:
                if already_selected >= floor or len(selected) >= max_results:
                    break
                if platform in candidate["platforms"] and add(candidate):
                    already_selected += 1

    for candidate in ranked:
        if len(selected) >= max_results:
            break
        add(candidate)

    rejected: list[dict[str, Any]] = []
    for candidate in ranked:
        if candidate["candidate_id"] in selected_ids:
            continue
        author = candidate["author_id"]
        cap = cap_for(candidate)
        reason = "author_diversity_cap" if author_counts.get(author, 0) >= cap else "selection_limit"
        rejection: dict[str, Any] = {
            "candidate_id": candidate["candidate_id"],
            "reason_code": reason,
        }
        if reason == "author_diversity_cap":
            rejection.update({"author_id": author, "cap": cap})
        rejected.append(rejection)

    selected.sort(key=_rank_key)
    forced = len(selected_ids - baseline_ids)
    return selected, rejected, forced


def fuse(request: Any) -> dict[str, Any]:
    value = _validate(request)
    subject_author_ids = set(value["subject_author_ids"])
    time_policy = value["time_policy"]
    mode = time_policy["mode"]
    from_date = date.fromisoformat(time_policy["from_date"])
    to_date = date.fromisoformat(time_policy["to_date"])

    aggregated: dict[str, dict[str, Any]] = {}
    quarantined_by_id: dict[str, dict[str, str]] = {}
    for ranked in sorted(value["lists"], key=lambda row: row["list_id"]):
        for offset, item in enumerate(ranked["items"], start=1):
            candidate_id = item["candidate_id"]
            reason = _date_verdict(item, mode, from_date, to_date)
            if reason is not None:
                quarantined_by_id.setdefault(
                    candidate_id,
                    {"candidate_id": candidate_id, "reason_code": reason},
                )
                continue
            occurrence = {
                "list_id": ranked["list_id"],
                "platform": ranked["platform"],
                "query_id": ranked["query_id"],
                "rank": offset,
                "weight": ranked["weight"],
            }
            contribution = ranked["weight"] / (RRF_K + offset)
            if candidate_id not in aggregated:
                safe_item = dict(item)
                safe_item.pop("engagement", None)
                safe_item.update(
                    {
                        "weighted_rrf_score": 0.0,
                        "rank_provenance": [],
                        "platforms": [],
                        "query_ids": [],
                        "consensus_count": 0,
                        "first_party_signal": _first_party(item, subject_author_ids),
                        "fusion_signals": ["weighted_rrf"],
                        "curator_accepted": False,
                    }
                )
                aggregated[candidate_id] = safe_item
            candidate = aggregated[candidate_id]
            candidate["weighted_rrf_score"] += contribution
            candidate["rank_provenance"].append(occurrence)
            candidate["platforms"].append(ranked["platform"])
            candidate["query_ids"].append(ranked["query_id"])

    eligible: list[dict[str, Any]] = []
    for candidate in aggregated.values():
        candidate["rank_provenance"] = sorted(
            candidate["rank_provenance"], key=lambda row: row["list_id"]
        )
        candidate["platforms"] = sorted(set(candidate["platforms"]))
        candidate["query_ids"] = sorted(set(candidate["query_ids"]))
        candidate["consensus_count"] = len(candidate["rank_provenance"])
        candidate["weighted_rrf_score"] = float(candidate["weighted_rrf_score"])
        if candidate["consensus_count"] > 1:
            candidate["fusion_signals"].append("multi_list_consensus")
        if candidate["first_party_signal"]:
            candidate["fusion_signals"].append("first_party")
        eligible.append(candidate)
    eligible.sort(key=_rank_key)

    selected, rejected, forced = _select_candidates(eligible, value["selection"])
    rejected.sort(key=lambda row: (row["candidate_id"], row["reason_code"]))
    quarantined = sorted(quarantined_by_id.values(), key=lambda row: row["candidate_id"])

    result: dict[str, Any] = {
        "contract_version": CONTRACT_RESULT,
        "run_id": value["run_id"],
        "topic": value["topic"],
        "method": {"name": "weighted_rrf", "k": RRF_K},
        "selection_policy": {
            **value["selection"],
            "scope": "discovery_breadth_only",
            "evidence_effect": "none",
        },
        "time_policy": dict(value["time_policy"]),
        "selected": selected,
        "quarantined": quarantined,
        "rejected": rejected,
        "summary": {
            "input_lists": len(value["lists"]),
            "unique_candidates": len(aggregated) + len(quarantined_by_id),
            "eligible_candidates": len(eligible),
            "selected_candidates": len(selected),
            "quarantined_candidates": len(quarantined),
            "rejected_candidates": len(rejected),
            "platform_quota_forced": forced,
            "curator_acceptance_created": 0,
        },
    }
    result["result_digest_sha256"] = _digest(result)
    return result


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FusionError(f"output already exists: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _probe() -> dict[str, Any]:
    return {
        "engine_id": ENGINE_ID,
        "version": ENGINE_VERSION,
        "contract": CONTRACT_RESULT,
        "ready": True,
        "capabilities": [
            "weighted_rrf",
            "rank_provenance",
            "author_diversity",
            "first_party_signal",
            "date_quarantine",
            "deterministic_fallback",
        ],
        "evidence_authority": "none",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    probe = subparsers.add_parser("probe")
    probe.add_argument("--json", action="store_true", required=True)
    fuse_parser = subparsers.add_parser("fuse")
    fuse_parser.add_argument("--input", type=Path, required=True)
    fuse_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "probe":
            json.dump(_probe(), sys.stdout, ensure_ascii=False, sort_keys=True)
            sys.stdout.write("\n")
            return 0
        with args.input.open("r", encoding="utf-8") as handle:
            request = json.load(handle)
        result = fuse(request)
        _write_atomic(args.output, result)
        return 0
    except (FusionError, OSError, json.JSONDecodeError) as exc:
        json.dump(
            {"status": "error", "error_type": type(exc).__name__, "error": str(exc)},
            sys.stderr,
            ensure_ascii=False,
            sort_keys=True,
        )
        sys.stderr.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
