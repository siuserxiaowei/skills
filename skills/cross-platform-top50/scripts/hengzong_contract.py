#!/usr/bin/env python3
"""Original, fail-closed contracts for dated horizontal/vertical research.

This module intentionally implements a data contract rather than a search
backend.  It makes research coverage, temporal provenance, unresolved gaps,
and independent curation machine-checkable before a brief can be called
verified.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import stat
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urlsplit


REQUEST_CONTRACT = "top50-hengzong-request/v1"
PLAN_CONTRACT = "top50-hengzong-plan/v1"
BRIEF_CONTRACT = "top50-hengzong-brief/v1"
ACCEPTANCE_CONTRACT = "top50-hengzong-curator-acceptance/v1"

HARD_MAX_GEO_LANGUAGE_CELLS = 24
HARD_MAX_QUERIES_PER_GROUP = 8
HARD_MAX_TOTAL_QUERIES = 192
GOAL_TYPES = {"opportunity", "decision", "landscape", "diagnosis"}
SCENARIO_IDS = {"constrained", "continuity", "acceleration"}
TEMPORAL_ROLES = {"past_event", "present_effect", "implication"}
STANCES = {"support", "refute"}

REQUEST_FIELDS = {
    "contract_version",
    "run_id",
    "brief_date",
    "as_of",
    "goal",
    "scope",
    "query_bounds",
    "producer",
}
PLAN_FIELDS = {
    "contract_version",
    "run_id",
    "stage",
    "status",
    "brief_date",
    "as_of",
    "goal",
    "scope",
    "query_bounds",
    "producer",
    "canonical_workstreams",
    "query_groups",
    "counts",
    "plan_id",
    "result_digest_sha256",
}
BRIEF_FIELDS = {
    "contract_version",
    "run_id",
    "stage",
    "status",
    "brief_date",
    "as_of",
    "goal",
    "scope",
    "producer",
    "plan_binding",
    "workstream_results",
    "sources",
    "claims",
    "causal_chains",
    "scenarios",
    "opportunity_map",
    "retained_gaps",
    "blocking_reasons",
    "result_digest_sha256",
}
ACCEPTANCE_FIELDS = {
    "contract_version",
    "run_id",
    "stage",
    "status",
    "curator",
    "brief_binding",
    "reviewed_workstream_ids",
    "accepted_claim_ids",
    "decision",
    "counts",
    "result_digest_sha256",
}


class ContractError(ValueError):
    """An artifact is malformed, inconsistent, or has been changed."""


class BlockingError(ContractError):
    """Research cannot safely progress and must return a non-success status."""

    def __init__(self, message: str, code: str = "research_blocked") -> None:
        super().__init__(message)
        self.code = code
        self.status = "blocking"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def artifact_digest(value: Mapping[str, Any]) -> str:
    material = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key != "result_digest_sha256"
    }
    return canonical_json_sha256(material)


def plan_id_for(value: Mapping[str, Any]) -> str:
    material = {
        key: copy.deepcopy(item)
        for key, item in value.items()
        if key not in {"plan_id", "result_digest_sha256"}
    }
    return "hzplan-" + canonical_json_sha256(material)[:24]


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{label} must be an object")
    return value


def _sequence(value: Any, label: str, *, nonempty: bool = False) -> List[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    if nonempty and not value:
        raise ContractError(f"{label} must not be empty")
    return value


def _exact_fields(value: Mapping[str, Any], expected: Set[str], label: str) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unexpected:
            details.append("unexpected " + ", ".join(unexpected))
        raise ContractError(f"{label} fields are invalid: {'; '.join(details)}")


def _strings(value: Any, label: str, *, nonempty: bool = False) -> List[str]:
    rows = _sequence(value, label, nonempty=nonempty)
    if any(not _nonempty(row) for row in rows):
        raise ContractError(f"{label} entries must be non-empty strings")
    normalized = [str(row).strip() for row in rows]
    if len(normalized) != len(set(normalized)):
        raise ContractError(f"{label} entries must be unique")
    return normalized


def _integer(
    value: Any,
    label: str,
    *,
    minimum: int = 0,
    maximum: Optional[int] = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{label} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        limit = f" between {minimum} and {maximum}" if maximum is not None else f" >= {minimum}"
        raise ContractError(f"{label} must be{limit}")
    return value


def _parse_date(value: Any, label: str) -> date:
    if not _nonempty(value):
        raise ContractError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(str(value))
    except ValueError as exc:
        raise ContractError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ContractError(f"{label} must use YYYY-MM-DD")
    return parsed


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not _nonempty(value):
        raise ContractError(f"{label} must be an ISO timestamp")
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError as exc:
        raise ContractError(f"{label} must be an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ContractError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _valid_url(value: Any, label: str) -> str:
    if not _nonempty(value):
        raise ContractError(f"{label} must be a public http(s) URL")
    parsed = urlsplit(str(value))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ContractError(f"{label} must be a public http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ContractError(f"{label} must not contain credentials")
    return str(value)


def _check_digest(value: Mapping[str, Any], label: str) -> None:
    supplied = value.get("result_digest_sha256")
    if not _sha256(supplied) or supplied != artifact_digest(value):
        raise ContractError(f"{label} result digest does not match its content")


def _validate_goal(value: Any) -> Dict[str, str]:
    goal = _mapping(value, "goal")
    _exact_fields(goal, {"type", "objective", "audience", "decision"}, "goal")
    if goal.get("type") not in GOAL_TYPES:
        raise ContractError(f"goal.type must be one of {sorted(GOAL_TYPES)}")
    for field in ("objective", "audience", "decision"):
        if not _nonempty(goal.get(field)):
            raise ContractError(f"goal.{field} must be non-empty")
    return {field: str(goal[field]).strip() for field in goal}


def _validate_scope(value: Any, *, as_of: datetime) -> Dict[str, Any]:
    scope = _mapping(value, "scope")
    _exact_fields(
        scope,
        {"start_date", "end_date", "geographies", "languages"},
        "scope",
    )
    start = _parse_date(scope.get("start_date"), "scope.start_date")
    end = _parse_date(scope.get("end_date"), "scope.end_date")
    if start > end:
        raise ContractError("scope.start_date must not be after scope.end_date")
    if end > as_of.date():
        raise ContractError("scope.end_date must not be after as_of")
    geographies = _strings(scope.get("geographies"), "scope.geographies", nonempty=True)
    languages = _strings(scope.get("languages"), "scope.languages", nonempty=True)
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "geographies": geographies,
        "languages": languages,
    }


def _validate_bounds(value: Any) -> Dict[str, int]:
    bounds = _mapping(value, "query_bounds")
    _exact_fields(
        bounds,
        {
            "max_geo_language_cells",
            "max_queries_per_group",
            "max_total_queries",
        },
        "query_bounds",
    )
    return {
        "max_geo_language_cells": _integer(
            bounds.get("max_geo_language_cells"),
            "query_bounds.max_geo_language_cells",
            minimum=1,
        ),
        "max_queries_per_group": _integer(
            bounds.get("max_queries_per_group"),
            "query_bounds.max_queries_per_group",
            minimum=1,
        ),
        "max_total_queries": _integer(
            bounds.get("max_total_queries"),
            "query_bounds.max_total_queries",
            minimum=1,
        ),
    }


def _validate_producer(value: Any, label: str = "producer") -> Dict[str, Any]:
    producer = _mapping(value, label)
    _exact_fields(producer, {"engine_id", "engine_version", "worker_ids"}, label)
    for field in ("engine_id", "engine_version"):
        if not _nonempty(producer.get(field)):
            raise ContractError(f"{label}.{field} must be non-empty")
    worker_ids = _strings(producer.get("worker_ids"), f"{label}.worker_ids", nonempty=True)
    return {
        "engine_id": str(producer["engine_id"]).strip(),
        "engine_version": str(producer["engine_version"]).strip(),
        "worker_ids": worker_ids,
    }


def _validated_request(value: Any) -> Dict[str, Any]:
    request = _mapping(value, "request")
    _exact_fields(request, REQUEST_FIELDS, "request")
    if request.get("contract_version") != REQUEST_CONTRACT:
        raise ContractError(f"request contract_version must be {REQUEST_CONTRACT}")
    if not _nonempty(request.get("run_id")):
        raise ContractError("request.run_id must be non-empty")
    brief_date = _parse_date(request.get("brief_date"), "brief_date")
    as_of = _parse_timestamp(request.get("as_of"), "as_of")
    if brief_date != as_of.date():
        raise ContractError("brief_date must equal the UTC date of as_of")
    goal = _validate_goal(request.get("goal"))
    scope = _validate_scope(request.get("scope"), as_of=as_of)
    bounds = _validate_bounds(request.get("query_bounds"))
    producer = _validate_producer(request.get("producer"))
    return {
        "contract_version": REQUEST_CONTRACT,
        "run_id": str(request["run_id"]).strip(),
        "brief_date": brief_date.isoformat(),
        "as_of": str(request["as_of"]),
        "goal": goal,
        "scope": scope,
        "query_bounds": bounds,
        "producer": producer,
    }


def _workstream_specs(goal: Mapping[str, str]) -> List[Dict[str, str]]:
    objective = goal["objective"]
    kind = goal["type"]
    common = [
        (
            "H1-boundary-and-baseline",
            "horizontal",
            f"围绕“{objective}”，哪些定义、边界、基准事实和代表性参与者决定比较口径？",
            "scope_and_baseline",
        ),
        (
            "H2-current-signals-and-counterevidence",
            "horizontal",
            f"围绕“{objective}”，当前跨地区、语言和来源的共同信号、分歧与反证是什么？",
            "current_signals",
        ),
        (
            "H3-adoption-and-stakeholders",
            "horizontal",
            f"围绕“{objective}”，不同用户、供应方和约束方的采用行为及利益冲突是什么？",
            "stakeholder_adoption",
        ),
        (
            "V1-past-to-present-mechanisms",
            "vertical",
            f"围绕“{objective}”，哪些过去事件通过何种机制形成当前效果？",
            "causal_timeline",
        ),
        (
            "V2-scenarios-and-invalidators",
            "vertical",
            f"围绕“{objective}”，未来受限、延续和加速三种情景的触发条件与失效条件是什么？",
            "scenario_tests",
        ),
    ]
    final_by_goal = {
        "opportunity": (
            "V3-future-value-paths",
            "vertical",
            f"围绕“{objective}”，未来行业价值池、未满足需求、可交付方案和领先指标是什么？",
            "future_opportunity",
        ),
        "decision": (
            "V3-decision-and-reversal-tests",
            "vertical",
            f"围绕“{objective}”，哪个选择满足决策标准，哪些新证据会推翻该选择？",
            "decision_reversal",
        ),
        "landscape": (
            "V3-structure-and-transition-paths",
            "vertical",
            f"围绕“{objective}”，行业结构可能沿哪些路径变化，分水岭信号是什么？",
            "landscape_transition",
        ),
        "diagnosis": (
            "V3-remedies-and-disconfirmation",
            "vertical",
            f"围绕“{objective}”，哪些干预可解决根因，哪些观测会否定诊断？",
            "remedy_disconfirmation",
        ),
    }
    rows = common + [final_by_goal[kind]]
    return [
        {
            "workstream_id": workstream_id,
            "axis": axis,
            "question": question,
            "deliverable": deliverable,
        }
        for workstream_id, axis, question, deliverable in rows
    ]


def _query_templates(objective: str, geography: str, language: str) -> List[Tuple[str, str]]:
    return [
        (
            "landscape",
            f"{objective} {geography} {language} 定义 参与者 采用 数据",
        ),
        (
            "primary_and_counterevidence",
            f"{objective} {geography} {language} 官方 数据 实测 争议 反例",
        ),
        (
            "timeline_and_future",
            f"{objective} {geography} {language} 事件 影响 情景 机会 风险",
        ),
    ]


def _query_groups(
    goal: Mapping[str, str],
    scope: Mapping[str, Any],
    bounds: Mapping[str, int],
    workstreams: Sequence[Mapping[str, str]],
) -> Tuple[List[Dict[str, Any]], int]:
    geographies = list(scope["geographies"])
    languages = list(scope["languages"])
    cell_count = len(geographies) * len(languages)
    if cell_count > bounds["max_geo_language_cells"]:
        raise BlockingError(
            "geo×language cells exceed the declared max_geo_language_cells",
            "geo_language_bound_exceeded",
        )
    if cell_count > HARD_MAX_GEO_LANGUAGE_CELLS:
        raise BlockingError(
            f"geo×language cells exceed the hard limit of {HARD_MAX_GEO_LANGUAGE_CELLS}",
            "geo_language_hard_limit",
        )
    if bounds["max_queries_per_group"] > HARD_MAX_QUERIES_PER_GROUP:
        raise BlockingError(
            f"max_queries_per_group exceeds the hard limit of {HARD_MAX_QUERIES_PER_GROUP}",
            "query_group_hard_limit",
        )
    if bounds["max_total_queries"] > HARD_MAX_TOTAL_QUERIES:
        raise BlockingError(
            f"max_total_queries exceeds the hard limit of {HARD_MAX_TOTAL_QUERIES}",
            "total_query_hard_limit",
        )
    if bounds["max_total_queries"] < cell_count:
        raise BlockingError(
            "max_total_queries cannot provide one query for every geo×language cell",
            "total_query_bound_too_small",
        )
    per_group = min(
        3,
        bounds["max_queries_per_group"],
        bounds["max_total_queries"] // cell_count,
    )
    workstream_ids = [row["workstream_id"] for row in workstreams]
    groups: List[Dict[str, Any]] = []
    total_queries = 0
    for geography in geographies:
        for language in languages:
            group_id = "qg-" + canonical_json_sha256(
                {"geography": geography, "language": language}
            )[:16]
            templates = _query_templates(goal["objective"], geography, language)[:per_group]
            queries: List[Dict[str, Any]] = []
            for index, (query_path, text) in enumerate(templates):
                assigned = workstream_ids[index::per_group]
                query_id = "query-" + canonical_json_sha256(
                    {
                        "group_id": group_id,
                        "query_path": query_path,
                        "query": text,
                    }
                )[:20]
                queries.append(
                    {
                        "query_id": query_id,
                        "query": text,
                        "query_path": query_path,
                        "route": "platform-native-plus-public-index",
                        "workstream_ids": assigned,
                    }
                )
            groups.append(
                {
                    "group_id": group_id,
                    "geography": geography,
                    "language": language,
                    "queries": queries,
                }
            )
            total_queries += len(queries)
    return groups, total_queries


def build_plan(request: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = _validated_request(request)
    workstreams = _workstream_specs(normalized["goal"])
    query_groups, total_queries = _query_groups(
        normalized["goal"], normalized["scope"], normalized["query_bounds"], workstreams
    )
    plan: Dict[str, Any] = {
        "contract_version": PLAN_CONTRACT,
        "run_id": normalized["run_id"],
        "stage": "hengzong_plan",
        "status": "complete",
        "brief_date": normalized["brief_date"],
        "as_of": normalized["as_of"],
        "goal": normalized["goal"],
        "scope": normalized["scope"],
        "query_bounds": normalized["query_bounds"],
        "producer": normalized["producer"],
        "canonical_workstreams": workstreams,
        "query_groups": query_groups,
        "counts": {
            "workstreams": len(workstreams),
            "horizontal_workstreams": sum(row["axis"] == "horizontal" for row in workstreams),
            "vertical_workstreams": sum(row["axis"] == "vertical" for row in workstreams),
            "geo_language_cells": len(query_groups),
            "query_groups": len(query_groups),
            "total_queries": total_queries,
        },
    }
    plan["plan_id"] = plan_id_for(plan)
    plan["result_digest_sha256"] = artifact_digest(plan)
    validate_plan(plan)
    return plan


def validate_plan(value: Mapping[str, Any]) -> Dict[str, Any]:
    plan = _mapping(value, "plan")
    _exact_fields(plan, PLAN_FIELDS, "plan")
    if plan.get("contract_version") != PLAN_CONTRACT:
        raise ContractError(f"plan contract_version must be {PLAN_CONTRACT}")
    if plan.get("stage") != "hengzong_plan" or plan.get("status") != "complete":
        raise ContractError("plan must have stage=hengzong_plan and status=complete")
    request_material = {
        "contract_version": REQUEST_CONTRACT,
        "run_id": plan.get("run_id"),
        "brief_date": plan.get("brief_date"),
        "as_of": plan.get("as_of"),
        "goal": plan.get("goal"),
        "scope": plan.get("scope"),
        "query_bounds": plan.get("query_bounds"),
        "producer": plan.get("producer"),
    }
    normalized = _validated_request(request_material)
    expected_workstreams = _workstream_specs(normalized["goal"])
    if plan.get("canonical_workstreams") != expected_workstreams:
        raise ContractError(
            "canonical workstreams do not match the complete goal-sensitive workstream set"
        )
    expected_groups, total_queries = _query_groups(
        normalized["goal"],
        normalized["scope"],
        normalized["query_bounds"],
        expected_workstreams,
    )
    if plan.get("query_groups") != expected_groups:
        raise ContractError(
            "query_groups must be the bounded geo×language plan for every canonical workstream"
        )
    expected_counts = {
        "workstreams": len(expected_workstreams),
        "horizontal_workstreams": sum(
            row["axis"] == "horizontal" for row in expected_workstreams
        ),
        "vertical_workstreams": sum(
            row["axis"] == "vertical" for row in expected_workstreams
        ),
        "geo_language_cells": len(expected_groups),
        "query_groups": len(expected_groups),
        "total_queries": total_queries,
    }
    if plan.get("counts") != expected_counts:
        raise ContractError("plan counts do not match its canonical workstreams and queries")
    if plan.get("plan_id") != plan_id_for(plan):
        raise ContractError("plan_id does not match the complete plan")
    _check_digest(plan, "plan")
    return {
        "status": "complete",
        "run_id": normalized["run_id"],
        "plan_id": plan["plan_id"],
        "counts": expected_counts,
    }


def _unique_rows(
    value: Any,
    label: str,
    id_field: str,
    *,
    nonempty: bool = False,
) -> Tuple[List[Mapping[str, Any]], Dict[str, Mapping[str, Any]]]:
    rows = _sequence(value, label, nonempty=nonempty)
    if any(not isinstance(row, Mapping) for row in rows):
        raise ContractError(f"{label} entries must be objects")
    identifiers: List[str] = []
    by_id: Dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        identifier = row.get(id_field)
        if not _nonempty(identifier):
            raise ContractError(f"{label}[{index}].{id_field} must be non-empty")
        normalized = str(identifier).strip()
        if normalized in by_id:
            raise ContractError(f"{label}.{id_field} values must be unique")
        identifiers.append(normalized)
        by_id[normalized] = row
    return rows, by_id


def _validate_plan_binding(value: Any, plan: Mapping[str, Any]) -> None:
    binding = _mapping(value, "plan_binding")
    _exact_fields(
        binding,
        {"contract_version", "plan_id", "result_digest_sha256"},
        "plan_binding",
    )
    expected = {
        "contract_version": PLAN_CONTRACT,
        "plan_id": plan["plan_id"],
        "result_digest_sha256": plan["result_digest_sha256"],
    }
    if dict(binding) != expected:
        raise ContractError("plan_binding does not bind the validated complete plan")


def _validate_sources(
    value: Any,
    *,
    scope_start: date,
    as_of: datetime,
) -> Dict[str, Mapping[str, Any]]:
    rows, sources = _unique_rows(value, "sources", "source_id", nonempty=True)
    expected_fields = {
        "source_id",
        "url",
        "title",
        "publisher",
        "independence_group",
        "published_at",
        "as_of",
        "pre_scope_context",
    }
    for index, row in enumerate(rows):
        label = f"sources[{index}]"
        _exact_fields(row, expected_fields, label)
        _valid_url(row.get("url"), f"{label}.url")
        for field in ("title", "publisher", "independence_group"):
            if not _nonempty(row.get(field)):
                raise ContractError(f"{label}.{field} must be non-empty")
        published = _parse_timestamp(row.get("published_at"), f"{label}.published_at")
        source_as_of = _parse_timestamp(row.get("as_of"), f"{label}.as_of")
        if source_as_of != as_of:
            raise ContractError(f"{label}.as_of must match the brief as_of")
        if published > as_of:
            raise ContractError(f"{label}.published_at must not be after as_of")
        expected_context = published.date() < scope_start
        if row.get("pre_scope_context") is not expected_context:
            raise ContractError(
                f"{label}.pre_scope_context must reflect published_at versus scope.start_date"
            )
    return sources


def _validate_claims(
    value: Any,
    *,
    sources: Mapping[str, Mapping[str, Any]],
    scope_start: date,
    as_of: datetime,
) -> Dict[str, Mapping[str, Any]]:
    rows, claims = _unique_rows(value, "claims", "claim_id", nonempty=True)
    expected_fields = {
        "claim_id",
        "text",
        "temporal_role",
        "event_date",
        "as_of",
        "pre_scope_context",
        "scope",
        "evidence_links",
    }
    evidence_fields = {"source_id", "stance", "locator", "evidence_date", "scope"}
    roles: Set[str] = set()
    observed_refute = False
    for claim_index, row in enumerate(rows):
        label = f"claims[{claim_index}]"
        _exact_fields(row, expected_fields, label)
        for field in ("text", "scope"):
            if not _nonempty(row.get(field)):
                raise ContractError(f"{label}.{field} must be non-empty")
        role = row.get("temporal_role")
        if role not in TEMPORAL_ROLES:
            raise ContractError(f"{label}.temporal_role is invalid")
        roles.add(str(role))
        claim_as_of = _parse_timestamp(row.get("as_of"), f"{label}.as_of")
        if claim_as_of != as_of:
            raise ContractError(f"{label}.as_of must match the brief as_of")
        event_value = row.get("event_date")
        if event_value is None:
            if role != "implication":
                raise ContractError(f"{label}.event_date is required for {role}")
            expected_context = False
        else:
            event = _parse_date(event_value, f"{label}.event_date")
            if event > as_of.date():
                raise ContractError(f"{label}.event_date must not be after as_of")
            expected_context = event < scope_start
        if row.get("pre_scope_context") is not expected_context:
            raise ContractError(
                f"{label}.pre_scope_context must reflect event_date versus scope.start_date"
            )
        links = _sequence(row.get("evidence_links"), f"{label}.evidence_links", nonempty=True)
        support_groups: Set[str] = set()
        all_groups: Set[str] = set()
        for link_index, link_value in enumerate(links):
            link = _mapping(link_value, f"{label}.evidence_links[{link_index}]")
            link_label = f"{label}.evidence_links[{link_index}]"
            _exact_fields(link, evidence_fields, link_label)
            source_id = link.get("source_id")
            if source_id not in sources:
                raise ContractError(f"{link_label}.source_id is not present in sources")
            stance = link.get("stance")
            if stance not in STANCES:
                raise ContractError(f"{link_label}.stance must be support or refute")
            for field in ("locator", "scope"):
                if not _nonempty(link.get(field)):
                    raise ContractError(f"{link_label}.{field} must be non-empty")
            evidence_date = _parse_date(
                link.get("evidence_date"), f"{link_label}.evidence_date"
            )
            if evidence_date > as_of.date():
                raise ContractError(f"{link_label}.evidence_date must not be after as_of")
            group = str(sources[str(source_id)]["independence_group"])
            all_groups.add(group)
            if stance == "support":
                support_groups.add(group)
            else:
                observed_refute = True
        if not support_groups:
            raise ContractError(f"{label} needs at least one supporting source")
        if role in {"past_event", "present_effect"} and len(all_groups) < 2:
            raise ContractError(
                f"{label} needs two independent evidence groups for an observed event/effect"
            )
    if roles != TEMPORAL_ROLES:
        raise ContractError("claims must cover past_event, present_effect, and implication")
    if not observed_refute:
        raise ContractError("claim-source ledger must retain at least one refute link")
    return claims


def _validate_workstream_results(
    value: Any,
    *,
    workstream_ids: Set[str],
    claim_ids: Set[str],
) -> None:
    rows, by_id = _unique_rows(
        value, "workstream_results", "workstream_id", nonempty=True
    )
    if set(by_id) != workstream_ids:
        raise ContractError(
            "workstream_results must contain every canonical workstream exactly once"
        )
    expected_fields = {"workstream_id", "status", "finding", "claim_ids"}
    referenced: Set[str] = set()
    for index, row in enumerate(rows):
        label = f"workstream_results[{index}]"
        _exact_fields(row, expected_fields, label)
        if row.get("status") != "complete":
            raise ContractError(f"{label}.status must be complete")
        if not _nonempty(row.get("finding")):
            raise ContractError(f"{label}.finding must be non-empty")
        identifiers = set(_strings(row.get("claim_ids"), f"{label}.claim_ids", nonempty=True))
        if not identifiers <= claim_ids:
            raise ContractError(f"{label}.claim_ids contains an unknown claim")
        referenced.update(identifiers)
    if referenced != claim_ids:
        raise ContractError("every claim must be assigned to at least one workstream")


def _validate_causal_chains(
    value: Any, claims: Mapping[str, Mapping[str, Any]]
) -> int:
    rows, _ = _unique_rows(value, "causal_chains", "chain_id", nonempty=True)
    expected_fields = {
        "chain_id",
        "past_event_claim_id",
        "present_effect_claim_id",
        "implication_claim_id",
        "mechanism",
        "caveat",
    }
    role_fields = {
        "past_event_claim_id": "past_event",
        "present_effect_claim_id": "present_effect",
        "implication_claim_id": "implication",
    }
    for index, row in enumerate(rows):
        label = f"causal_chains[{index}]"
        _exact_fields(row, expected_fields, label)
        for field in ("mechanism", "caveat"):
            if not _nonempty(row.get(field)):
                raise ContractError(f"{label}.{field} must be non-empty")
        seen: Set[str] = set()
        for field, role in role_fields.items():
            claim_id = row.get(field)
            if claim_id not in claims:
                raise ContractError(f"{label}.{field} references an unknown claim")
            if claims[str(claim_id)].get("temporal_role") != role:
                raise ContractError(f"{label}.{field} must reference a {role} claim")
            seen.add(str(claim_id))
        if len(seen) != 3:
            raise ContractError(f"{label} must use three distinct temporal claims")
    return len(rows)


def _validate_scenarios(
    value: Any, claim_ids: Set[str], brief_date: date
) -> int:
    rows, by_id = _unique_rows(value, "scenarios", "scenario_id", nonempty=True)
    if set(by_id) != SCENARIO_IDS or len(rows) != 3:
        raise ContractError(
            "scenarios must contain the three canonical constrained, continuity, and acceleration cases"
        )
    expected_fields = {"scenario_id", "summary", "triggers", "invalidators"}
    signal_fields = {"signal", "check_by", "claim_ids"}
    for index, row in enumerate(rows):
        label = f"scenarios[{index}]"
        _exact_fields(row, expected_fields, label)
        if not _nonempty(row.get("summary")):
            raise ContractError(f"{label}.summary must be non-empty")
        for collection in ("triggers", "invalidators"):
            signals = _sequence(row.get(collection), f"{label}.{collection}", nonempty=True)
            for signal_index, signal_value in enumerate(signals):
                signal = _mapping(
                    signal_value, f"{label}.{collection}[{signal_index}]"
                )
                signal_label = f"{label}.{collection}[{signal_index}]"
                _exact_fields(signal, signal_fields, signal_label)
                if not _nonempty(signal.get("signal")):
                    raise ContractError(f"{signal_label}.signal must be non-empty")
                if _parse_date(signal.get("check_by"), f"{signal_label}.check_by") < brief_date:
                    raise ContractError(f"{signal_label}.check_by must not predate brief_date")
                linked = set(
                    _strings(signal.get("claim_ids"), f"{signal_label}.claim_ids", nonempty=True)
                )
                if not linked <= claim_ids:
                    raise ContractError(f"{signal_label}.claim_ids contains an unknown claim")
    return len(rows)


def _validate_opportunity_map(
    value: Any,
    *,
    claim_ids: Set[str],
    implication_ids: Set[str],
    required: bool,
) -> int:
    rows, _ = _unique_rows(
        value, "opportunity_map", "opportunity_id", nonempty=required
    )
    expected_fields = {
        "opportunity_id",
        "industry",
        "horizon",
        "unmet_need",
        "enabling_change",
        "offer",
        "beneficiaries",
        "constraints",
        "leading_indicators",
        "claim_ids",
    }
    for index, row in enumerate(rows):
        label = f"opportunity_map[{index}]"
        _exact_fields(row, expected_fields, label)
        for field in ("industry", "horizon", "unmet_need", "enabling_change", "offer"):
            if not _nonempty(row.get(field)):
                raise ContractError(f"{label}.{field} must be non-empty")
        for field in ("beneficiaries", "constraints", "leading_indicators"):
            _strings(row.get(field), f"{label}.{field}", nonempty=True)
        linked = set(_strings(row.get("claim_ids"), f"{label}.claim_ids", nonempty=True))
        if not linked <= claim_ids:
            raise ContractError(f"{label}.claim_ids contains an unknown claim")
        if not linked & implication_ids:
            raise ContractError(f"{label} must cite at least one implication claim")
    return len(rows)


def _validate_retained_gaps(value: Any, *, as_of: datetime) -> int:
    rows, _ = _unique_rows(value, "retained_gaps", "gap_id")
    gap_fields = {"gap_id", "statement", "status", "attempts"}
    attempt_fields = {
        "attempt_id",
        "query",
        "query_path",
        "route",
        "executed_at",
        "outcome",
    }
    allowed_outcomes = {
        "no_results",
        "no_eligible_evidence",
        "insufficient_independence",
        "blocked_authorization",
        "conflicting_evidence",
    }
    for gap_index, row in enumerate(rows):
        label = f"retained_gaps[{gap_index}]"
        _exact_fields(row, gap_fields, label)
        if not _nonempty(row.get("statement")):
            raise ContractError(f"{label}.statement must be non-empty")
        if row.get("status") != "retained":
            raise ContractError(f"{label}.status must be retained")
        attempts, _ = _unique_rows(
            row.get("attempts"), f"{label}.attempts", "attempt_id", nonempty=True
        )
        if len(attempts) < 2:
            raise ContractError(f"{label}.attempts requires at least two attempts")
        seen: Dict[str, Set[str]] = {"query": set(), "query_path": set(), "route": set()}
        for attempt_index, attempt in enumerate(attempts):
            attempt_label = f"{label}.attempts[{attempt_index}]"
            _exact_fields(attempt, attempt_fields, attempt_label)
            for field in ("query", "query_path", "route"):
                if not _nonempty(attempt.get(field)):
                    raise ContractError(f"{attempt_label}.{field} must be non-empty")
                seen[field].add(str(attempt[field]).strip())
            executed = _parse_timestamp(
                attempt.get("executed_at"), f"{attempt_label}.executed_at"
            )
            if executed > as_of:
                raise ContractError(f"{attempt_label}.executed_at must not be after as_of")
            if attempt.get("outcome") not in allowed_outcomes:
                raise ContractError(f"{attempt_label}.outcome is invalid")
        for field, values in seen.items():
            if len(values) != len(attempts):
                raise ContractError(
                    f"{label} can be retained only when every attempt uses a distinct {field}"
                )
    return len(rows)


def _blocking_reason(value: Any) -> Tuple[str, str]:
    rows = _sequence(value, "blocking_reasons", nonempty=True)
    first = _mapping(rows[0], "blocking_reasons[0]")
    _exact_fields(first, {"code", "message"}, "blocking_reasons[0]")
    if not _nonempty(first.get("code")) or not _nonempty(first.get("message")):
        raise ContractError("blocking_reasons code and message must be non-empty")
    return str(first["code"]).strip(), str(first["message"]).strip()


def validate_brief_structure(
    value: Mapping[str, Any], plan: Mapping[str, Any]
) -> Dict[str, Any]:
    validate_plan(plan)
    brief = _mapping(value, "brief")
    _exact_fields(brief, BRIEF_FIELDS, "brief")
    if brief.get("contract_version") != BRIEF_CONTRACT:
        raise ContractError(f"brief contract_version must be {BRIEF_CONTRACT}")
    if brief.get("stage") != "hengzong_synthesis":
        raise ContractError("brief.stage must be hengzong_synthesis")
    if brief.get("status") == "verified":
        raise ContractError("a producer brief cannot self-verify; independent curation is required")
    if brief.get("status") not in {"ready_for_curator", "blocking"}:
        raise ContractError("brief.status must be ready_for_curator or blocking")
    _check_digest(brief, "brief")
    if brief.get("status") == "blocking":
        code, message = _blocking_reason(brief.get("blocking_reasons"))
        raise BlockingError(message, code)
    if brief.get("blocking_reasons") != []:
        raise ContractError("a ready_for_curator brief must have no blocking_reasons")
    for field in ("run_id", "brief_date", "as_of", "goal", "scope"):
        if brief.get(field) != plan.get(field):
            raise ContractError(f"brief.{field} must match the bound plan")
    brief_date = _parse_date(brief.get("brief_date"), "brief.brief_date")
    as_of = _parse_timestamp(brief.get("as_of"), "brief.as_of")
    scope_start = _parse_date(brief["scope"]["start_date"], "brief.scope.start_date")
    _validate_producer(brief.get("producer"), "brief.producer")
    _validate_plan_binding(brief.get("plan_binding"), plan)
    sources = _validate_sources(
        brief.get("sources"), scope_start=scope_start, as_of=as_of
    )
    claims = _validate_claims(
        brief.get("claims"),
        sources=sources,
        scope_start=scope_start,
        as_of=as_of,
    )
    claim_ids = set(claims)
    workstream_ids = {
        str(row["workstream_id"]) for row in plan["canonical_workstreams"]
    }
    _validate_workstream_results(
        brief.get("workstream_results"),
        workstream_ids=workstream_ids,
        claim_ids=claim_ids,
    )
    chains = _validate_causal_chains(brief.get("causal_chains"), claims)
    scenarios = _validate_scenarios(brief.get("scenarios"), claim_ids, brief_date)
    implication_ids = {
        claim_id
        for claim_id, row in claims.items()
        if row.get("temporal_role") == "implication"
    }
    opportunities = _validate_opportunity_map(
        brief.get("opportunity_map"),
        claim_ids=claim_ids,
        implication_ids=implication_ids,
        required=brief["goal"]["type"] == "opportunity",
    )
    gaps = _validate_retained_gaps(brief.get("retained_gaps"), as_of=as_of)
    return {
        "status": "ready_for_curator",
        "run_id": brief["run_id"],
        "workstream_ids": sorted(workstream_ids),
        "claim_ids": sorted(claim_ids),
        "counts": {
            "workstreams": len(workstream_ids),
            "sources": len(sources),
            "claims": len(claims),
            "independence_groups": len(
                {str(row["independence_group"]) for row in sources.values()}
            ),
            "causal_chains": chains,
            "scenarios": scenarios,
            "opportunities": opportunities,
            "retained_gaps": gaps,
        },
    }


def build_curator_acceptance(
    brief: Mapping[str, Any],
    *,
    brief_artifact_sha256: str,
    curator_id: str,
    reviewed_workstream_ids: Sequence[str],
    accepted_claim_ids: Sequence[str],
) -> Dict[str, Any]:
    if not _sha256(brief_artifact_sha256):
        raise ContractError("brief_artifact_sha256 must be a lowercase SHA-256")
    if not _nonempty(curator_id):
        raise ContractError("curator_id must be non-empty")
    workstreams = _strings(
        list(reviewed_workstream_ids), "reviewed_workstream_ids", nonempty=True
    )
    claims = _strings(list(accepted_claim_ids), "accepted_claim_ids", nonempty=True)
    if brief.get("contract_version") != BRIEF_CONTRACT:
        raise ContractError("acceptance can bind only a hengzong brief")
    if not _sha256(brief.get("result_digest_sha256")):
        raise ContractError("brief must carry a result digest")
    acceptance: Dict[str, Any] = {
        "contract_version": ACCEPTANCE_CONTRACT,
        "run_id": brief.get("run_id"),
        "stage": "hengzong_curate",
        "status": "accepted",
        "curator": {
            "curator_id": str(curator_id).strip(),
            "reviewed_at": brief.get("as_of"),
        },
        "brief_binding": {
            "contract_version": BRIEF_CONTRACT,
            "artifact_sha256": brief_artifact_sha256,
            "result_digest_sha256": brief.get("result_digest_sha256"),
        },
        "reviewed_workstream_ids": sorted(workstreams),
        "accepted_claim_ids": sorted(claims),
        "decision": "accepted",
        "counts": {
            "reviewed_workstreams": len(workstreams),
            "accepted_claims": len(claims),
        },
    }
    acceptance["result_digest_sha256"] = artifact_digest(acceptance)
    return acceptance


def _validate_acceptance(
    value: Mapping[str, Any],
    *,
    brief: Mapping[str, Any],
    structure: Mapping[str, Any],
    brief_artifact_sha256: str,
) -> None:
    acceptance = _mapping(value, "acceptance")
    _exact_fields(acceptance, ACCEPTANCE_FIELDS, "acceptance")
    if acceptance.get("contract_version") != ACCEPTANCE_CONTRACT:
        raise ContractError(f"acceptance contract_version must be {ACCEPTANCE_CONTRACT}")
    if acceptance.get("run_id") != brief.get("run_id"):
        raise ContractError("acceptance.run_id must match the brief")
    if acceptance.get("stage") != "hengzong_curate":
        raise ContractError("acceptance.stage must be hengzong_curate")
    if acceptance.get("status") != "accepted" or acceptance.get("decision") != "accepted":
        raise ContractError("acceptance status and decision must both be accepted")
    _check_digest(acceptance, "acceptance")
    curator = _mapping(acceptance.get("curator"), "acceptance.curator")
    _exact_fields(curator, {"curator_id", "reviewed_at"}, "acceptance.curator")
    curator_id = curator.get("curator_id")
    if not _nonempty(curator_id):
        raise ContractError("acceptance.curator.curator_id must be non-empty")
    _parse_timestamp(curator.get("reviewed_at"), "acceptance.curator.reviewed_at")
    worker_ids = set(_strings(brief["producer"]["worker_ids"], "brief.producer.worker_ids"))
    if str(curator_id).strip() in worker_ids:
        raise ContractError("curator must be independent from every research worker")
    binding = _mapping(acceptance.get("brief_binding"), "acceptance.brief_binding")
    _exact_fields(
        binding,
        {"contract_version", "artifact_sha256", "result_digest_sha256"},
        "acceptance.brief_binding",
    )
    expected_binding = {
        "contract_version": BRIEF_CONTRACT,
        "artifact_sha256": brief_artifact_sha256,
        "result_digest_sha256": brief["result_digest_sha256"],
    }
    if dict(binding) != expected_binding:
        raise ContractError("acceptance brief artifact binding does not match the exact brief")
    reviewed = set(
        _strings(
            acceptance.get("reviewed_workstream_ids"),
            "acceptance.reviewed_workstream_ids",
            nonempty=True,
        )
    )
    expected_workstreams = set(structure["workstream_ids"])
    if reviewed != expected_workstreams:
        raise ContractError("acceptance workstream set must equal the full canonical set")
    accepted = set(
        _strings(
            acceptance.get("accepted_claim_ids"),
            "acceptance.accepted_claim_ids",
            nonempty=True,
        )
    )
    expected_claims = set(structure["claim_ids"])
    if accepted != expected_claims:
        raise ContractError("acceptance claim set must equal the complete brief claim set")
    expected_counts = {
        "reviewed_workstreams": len(expected_workstreams),
        "accepted_claims": len(expected_claims),
    }
    if acceptance.get("counts") != expected_counts:
        raise ContractError("acceptance counts do not match the reviewed sets")


def validate_brief(
    brief: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    acceptance: Optional[Mapping[str, Any]] = None,
    brief_artifact_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    structure = validate_brief_structure(brief, plan)
    if acceptance is None or brief_artifact_sha256 is None:
        raise BlockingError(
            "independent curator acceptance bound to the exact brief artifact is required",
            "independent_curator_required",
        )
    if not _sha256(brief_artifact_sha256):
        raise ContractError("brief artifact SHA-256 is invalid")
    _validate_acceptance(
        acceptance,
        brief=brief,
        structure=structure,
        brief_artifact_sha256=brief_artifact_sha256,
    )
    return {
        "status": "verified",
        "run_id": structure["run_id"],
        "curator_id": acceptance["curator"]["curator_id"],
        "counts": structure["counts"],
    }


def _read_json(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise OSError("artifact must be a regular file")
            raw = handle.read()
            after = os.fstat(handle.fileno())
        if (
            (before.st_dev, before.st_ino, before.st_size)
            != (after.st_dev, after.st_ino, after.st_size)
            or len(raw) != after.st_size
        ):
            raise OSError("artifact changed while being read")
        decoded = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(decoded, dict):
        raise ContractError(f"JSON artifact {path} must contain an object")
    return decoded, hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _emit(value: Mapping[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build-plan", help="build a deterministic research plan")
    build.add_argument("--request", required=True, type=Path)
    build.add_argument("--output", type=Path)

    validate_plan_parser = commands.add_parser("validate-plan", help="validate a plan")
    validate_plan_parser.add_argument("--plan", required=True, type=Path)

    accept = commands.add_parser(
        "build-acceptance", help="bind an independent curator decision to a brief"
    )
    accept.add_argument("--brief", required=True, type=Path)
    accept.add_argument("--curator-id", required=True)
    accept.add_argument("--workstream-id", action="append", default=[])
    accept.add_argument("--claim-id", action="append", default=[])
    accept.add_argument("--output", type=Path)

    validate = commands.add_parser(
        "validate-brief", help="validate a brief and its independent acceptance"
    )
    validate.add_argument("--brief", required=True, type=Path)
    validate.add_argument("--plan", required=True, type=Path)
    validate.add_argument("--acceptance", type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build-plan":
            request_value, _ = _read_json(args.request)
            plan = build_plan(request_value)
            if args.output:
                _write_json(args.output, plan)
            _emit(plan)
            return 0
        if args.command == "validate-plan":
            plan, _ = _read_json(args.plan)
            _emit(validate_plan(plan))
            return 0
        if args.command == "build-acceptance":
            brief, artifact_sha256 = _read_json(args.brief)
            acceptance = build_curator_acceptance(
                brief,
                brief_artifact_sha256=artifact_sha256,
                curator_id=args.curator_id,
                reviewed_workstream_ids=args.workstream_id,
                accepted_claim_ids=args.claim_id,
            )
            if args.output:
                _write_json(args.output, acceptance)
            _emit(acceptance)
            return 0
        if args.command == "validate-brief":
            brief, artifact_sha256 = _read_json(args.brief)
            plan, _ = _read_json(args.plan)
            acceptance = None
            if args.acceptance:
                acceptance, _ = _read_json(args.acceptance)
            _emit(
                validate_brief(
                    brief,
                    plan,
                    acceptance=acceptance,
                    brief_artifact_sha256=artifact_sha256,
                )
            )
            return 0
        raise ContractError("unknown command")
    except BlockingError as exc:
        _emit({"status": exc.status, "code": exc.code, "message": str(exc)})
        return 3
    except ContractError as exc:
        _emit({"status": "invalid", "code": "contract_invalid", "message": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
