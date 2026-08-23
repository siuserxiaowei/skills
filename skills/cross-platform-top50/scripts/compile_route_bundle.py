#!/usr/bin/env python3
"""Compile a validated research scope into deterministic engine-router shards.

This compiler consumes structured JSON produced after scope parsing and access
classification.  It deliberately does not interpret arbitrary natural
language, probe a platform, access the network, or execute an engine plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


REQUEST_SCHEMA = "top50-route-scope/v1"
BUNDLE_SCHEMA = "top50-route-bundle/v1"
ROUTER_REQUEST_SCHEMA = "top50-router-request/v1"
SHARD_RESULT_CONTRACT = "top50-route-shard-result/v1"
SHARD_RESULT_MANIFEST_CONTRACT = "top50-route-shard-result-manifest/v1"

CANONICAL_PLATFORMS = (
    "csdn",
    "wechat_official_accounts",
    "zhihu",
    "xiaohongshu",
    "weibo",
    "douyin",
    "x",
    "bilibili",
    "juejin",
    "youtube",
    "linuxdo",
    "github",
    "baidu_search",
    "google_search",
    "bing_search",
    "toutiao",
    "36kr",
    "infoq",
    "segmentfault",
    "oschina",
    "v2ex",
    "reddit",
    "hacker_news",
    "medium",
    "linkedin",
    "kuaishou",
    "wechat_channels",
    "tiktok",
)
CANONICAL_PLATFORM_SET = frozenset(CANONICAL_PLATFORMS)
CANONICAL_INDEX = {platform_id: index for index, platform_id in enumerate(CANONICAL_PLATFORMS)}

ROOT_FIELDS = frozenset(
    {
        "schema",
        "run_id",
        "topic",
        "top_n",
        "engine_mode",
        "dual_run",
        "login_mode",
        "platform_routes",
        "platform_scope_mode",
        "public_url_count",
        "public_urls_authorized",
        "public_http_binding",
        "local_candidate_count",
        "extraction_complete",
        "risk",
    }
)
REQUIRED_ROOT_FIELDS = frozenset(
    {
        "schema",
        "run_id",
        "topic",
        "top_n",
        "engine_mode",
        "dual_run",
        "login_mode",
        "platform_routes",
    }
)
ROUTE_FIELDS = frozenset({"platform_id", "access_kind", "required"})
PUBLIC_HTTP_BINDING_FIELDS = frozenset(
    {
        "manifest_path",
        "manifest_artifact_sha256",
        "job_set_sha256",
        "job_count",
    }
)
BUNDLE_ROOT_FIELDS = frozenset(
    {
        "schema",
        "run_id",
        "topic",
        "top_n",
        "engine_mode",
        "dual_run",
        "login_mode",
        "risk",
        "platform_scope_mode",
        "assumptions",
        "coverage_targets",
        "shards",
        "omissions",
        "shared_handoffs",
        "artifacts",
        "plan_filenames",
        "bundle_digest_sha256",
    }
)
ASSUMPTION_FIELDS = frozenset({"field", "value", "reason"})
COVERAGE_TARGET_FIELDS = frozenset(
    {"platform_id", "required", "access_kind", "route_status"}
)
SHARD_REQUIRED_FIELDS = frozenset(
    {
        "shard_id",
        "source_kind",
        "stage",
        "platform_ids",
        "required_platform_ids",
        "input_count",
        "workload",
        "status",
        "depends_on",
        "run_dir",
        "plan_filename",
        "merge_contract",
        "login_requested",
    }
)
SHARD_FIELDS = SHARD_REQUIRED_FIELDS | frozenset(
    {"router_request", "reason_code", "checkpoint"}
)
ROUTER_REQUEST_REQUIRED_FIELDS = frozenset(
    {
        "schema",
        "run_id",
        "stage",
        "workload",
        "source_kind",
        "risk",
        "required_capabilities",
        "engine_mode",
        "dual_run",
        "run_dir",
        "top_n",
    }
)
ROUTER_REQUEST_FIELDS = ROUTER_REQUEST_REQUIRED_FIELDS | frozenset(
    {"public_http_binding"}
)
CHECKPOINT_FIELDS = frozenset(
    {
        "contract",
        "path",
        "run_id",
        "access_kind",
        "platform_ids",
        "required_before_plan",
        "next_gate",
    }
)
OMISSION_FIELDS = frozenset({"source_kind", "reason_code", "input_count"})
HANDOFF_FIELDS = frozenset(
    {
        "handoff_id",
        "from_stage",
        "to_stage",
        "input_shard_ids",
        "input_artifact",
        "output_artifact",
        "input_contract",
        "output_contract",
        "required_status",
        "fail_closed",
    }
)
ARTIFACT_FIELDS = frozenset(
    {
        "shard_result_manifest",
        "merge_result",
        "extraction_result",
        "curator_acceptance",
        "ranking_result",
    }
)
PLACEHOLDERS = frozenset(
    {
        "《》",
        "《主题》",
        "《真实主题》",
        "{{topic}}",
        "<主题>",
        "请填写主题",
    }
)


class RouteBundleError(ValueError):
    """The deterministic route-scope contract is invalid or unroutable."""


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _safe_run_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or value in {".", ".."}
        or re.fullmatch(r"[A-Za-z0-9._-]+", value) is None
    ):
        raise RouteBundleError("run_id must be a safe 1-128 character identifier")
    return value


def _validated_topic(value: Any) -> str:
    if not isinstance(value, str):
        raise RouteBundleError("topic must be a string")
    topic = unicodedata.normalize("NFC", value).strip()
    if not topic or len(topic) > 500:
        raise RouteBundleError("topic must contain 1-500 non-whitespace characters")
    if topic.casefold() in PLACEHOLDERS:
        raise RouteBundleError("topic is an unfilled placeholder")
    if any(ord(char) < 32 or ord(char) == 127 for char in topic):
        raise RouteBundleError("topic must not contain control characters")
    if not any(char.isalnum() for char in topic):
        raise RouteBundleError("topic must contain a letter or number")
    return topic


def _validated_integer(value: Any, field: str, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RouteBundleError(f"{field} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        suffix = f" and at most {maximum}" if maximum is not None else ""
        raise RouteBundleError(f"{field} must be at least {minimum}{suffix}")
    return value


def _validated_enum(value: Any, field: str, allowed: Sequence[str]) -> str:
    if value not in allowed:
        raise RouteBundleError(f"{field} must be one of: {', '.join(allowed)}")
    return str(value)


def workload_for_count(count: Any) -> str:
    """Return the frozen workload class: <50, 50-149, or >=150."""
    count = _validated_integer(count, "count", 0)
    if count < 50:
        return "small"
    if count < 150:
        return "medium"
    return "large"


def _validate_routes(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RouteBundleError("platform_routes must be an array")
    routes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise RouteBundleError(f"platform_routes[{index}] must be an object")
        missing = sorted(ROUTE_FIELDS - set(raw))
        unknown = sorted(set(raw) - ROUTE_FIELDS)
        if missing:
            raise RouteBundleError(
                f"platform_routes[{index}] is missing required fields: {', '.join(missing)}"
            )
        if unknown:
            raise RouteBundleError(
                f"platform_routes[{index}] has unknown fields: {', '.join(unknown)}"
            )
        platform_id = raw.get("platform_id")
        if platform_id not in CANONICAL_PLATFORM_SET:
            raise RouteBundleError(f"platform_routes[{index}].platform_id is not canonical")
        if platform_id in seen:
            raise RouteBundleError(f"duplicate platform route: {platform_id}")
        seen.add(str(platform_id))
        access_kind = _validated_enum(
            raw.get("access_kind"),
            f"platform_routes[{index}].access_kind",
            ("platform_cli", "browser_session"),
        )
        required = raw.get("required")
        if not _is_bool(required):
            raise RouteBundleError(f"platform_routes[{index}].required must be a boolean")
        routes.append(
            {
                "platform_id": str(platform_id),
                "access_kind": access_kind,
                "required": required,
            }
        )
    return sorted(routes, key=lambda row: CANONICAL_INDEX[row["platform_id"]])


def _validate_public_http_binding(
    value: Any, *, expected_count: int, field: str = "public_http_binding"
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RouteBundleError(f"{field} must be an object")
    missing = sorted(PUBLIC_HTTP_BINDING_FIELDS - set(value))
    unknown = sorted(set(value) - PUBLIC_HTTP_BINDING_FIELDS)
    if missing:
        raise RouteBundleError(f"{field} is missing required fields: {', '.join(missing)}")
    if unknown:
        raise RouteBundleError(f"{field} has unknown fields: {', '.join(unknown)}")

    manifest_path = value.get("manifest_path")
    if (
        not isinstance(manifest_path, str)
        or not manifest_path.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in manifest_path)
    ):
        raise RouteBundleError(f"{field}.manifest_path must be a non-empty path string")
    manifest_digest = value.get("manifest_artifact_sha256")
    if not isinstance(manifest_digest, str) or re.fullmatch(
        r"[0-9a-f]{64}", manifest_digest
    ) is None:
        raise RouteBundleError(
            f"{field}.manifest_artifact_sha256 must be 64 lowercase hexadecimal characters"
        )
    job_set_digest = value.get("job_set_sha256")
    if not isinstance(job_set_digest, str) or re.fullmatch(
        r"[0-9a-f]{64}", job_set_digest
    ) is None:
        raise RouteBundleError(
            f"{field}.job_set_sha256 must be 64 lowercase hexadecimal characters"
        )
    job_count = _validated_integer(value.get("job_count"), f"{field}.job_count", 1)
    if job_count != expected_count:
        raise RouteBundleError(f"{field}.job_count must equal public_url_count")
    return {
        "manifest_path": manifest_path,
        "manifest_artifact_sha256": manifest_digest,
        "job_set_sha256": job_set_digest,
        "job_count": job_count,
    }


def validate_scope(payload: Any) -> dict[str, Any]:
    """Validate and normalize a structured route scope without interpreting prose."""
    if not isinstance(payload, dict):
        raise RouteBundleError("route scope must be a JSON object")
    missing = sorted(REQUIRED_ROOT_FIELDS - set(payload))
    unknown = sorted(set(payload) - ROOT_FIELDS)
    if missing:
        raise RouteBundleError(f"route scope is missing required fields: {', '.join(missing)}")
    if unknown:
        raise RouteBundleError(f"route scope has unknown fields: {', '.join(unknown)}")
    if payload.get("schema") != REQUEST_SCHEMA:
        raise RouteBundleError(f"schema must be {REQUEST_SCHEMA}")

    run_id = _safe_run_id(payload.get("run_id"))
    topic = _validated_topic(payload.get("topic"))
    top_n = _validated_integer(payload.get("top_n"), "top_n", 1, 100)
    engine_mode = _validated_enum(
        payload.get("engine_mode"), "engine_mode", ("auto", "python", "go", "rust", "hybrid")
    )
    if not _is_bool(payload.get("dual_run")):
        raise RouteBundleError("dual_run must be a boolean")
    login_mode = _validated_enum(
        payload.get("login_mode"), "login_mode", ("public-only", "user-assisted")
    )
    platform_scope_mode = _validated_enum(
        payload.get("platform_scope_mode", "required_plus_default"),
        "platform_scope_mode",
        ("required_plus_default", "include_only"),
    )
    risk = _validated_enum(payload.get("risk", "low"), "risk", ("low", "medium", "high"))
    routes = _validate_routes(payload.get("platform_routes"))
    public_url_count = _validated_integer(payload.get("public_url_count", 0), "public_url_count", 0)
    local_candidate_count = _validated_integer(
        payload.get("local_candidate_count", 0), "local_candidate_count", 0
    )
    public_urls_authorized = payload.get("public_urls_authorized", False)
    extraction_complete = payload.get("extraction_complete", False)
    if not _is_bool(public_urls_authorized):
        raise RouteBundleError("public_urls_authorized must be a boolean")
    if not _is_bool(extraction_complete):
        raise RouteBundleError("extraction_complete must be a boolean")
    public_eligible = public_url_count > 0 and public_urls_authorized
    public_http_binding_value = payload.get("public_http_binding")
    if public_eligible:
        if "public_http_binding" not in payload:
            raise RouteBundleError(
                "public_http_binding is required for an authorized non-empty public URL batch"
            )
        public_http_binding: dict[str, Any] | None = _validate_public_http_binding(
            public_http_binding_value, expected_count=public_url_count
        )
    else:
        if "public_http_binding" in payload:
            raise RouteBundleError(
                "public_http_binding is only allowed for an authorized non-empty public URL batch"
            )
        public_http_binding = None

    return {
        "schema": REQUEST_SCHEMA,
        "run_id": run_id,
        "topic": topic,
        "top_n": top_n,
        "engine_mode": engine_mode,
        "dual_run": payload["dual_run"],
        "login_mode": login_mode,
        "platform_scope_mode": platform_scope_mode,
        "platform_routes": routes,
        "public_url_count": public_url_count,
        "public_urls_authorized": public_urls_authorized,
        "public_http_binding": public_http_binding,
        "local_candidate_count": local_candidate_count,
        "extraction_complete": extraction_complete,
        "risk": risk,
        "_scope_mode_was_defaulted": "platform_scope_mode" not in payload,
        "_risk_was_defaulted": "risk" not in payload,
    }


def _router_request(
    scope: Mapping[str, Any],
    *,
    stage: str,
    source_kind: str,
    workload: str,
    run_dir: str,
    engine_mode: str,
    dual_run: bool,
) -> dict[str, Any]:
    return {
        "schema": ROUTER_REQUEST_SCHEMA,
        "run_id": scope["run_id"],
        "stage": stage,
        "workload": workload,
        "source_kind": source_kind,
        "risk": scope["risk"],
        "required_capabilities": [],
        "engine_mode": engine_mode,
        "dual_run": dual_run,
        "run_dir": run_dir,
        "top_n": scope["top_n"],
    }


def _paths(root: PurePosixPath, shard_id: str) -> tuple[str, str]:
    run_dir = str(
        root / "shards" / ("local-bundle" if shard_id.startswith("local-bundle-") else shard_id)
    )
    plan_filename = str(root / "plans" / f"{shard_id}.plan.json")
    return run_dir, plan_filename


def _base_shard(
    scope: Mapping[str, Any],
    root: PurePosixPath,
    *,
    shard_id: str,
    source_kind: str,
    stage: str,
    platform_ids: Sequence[str],
    required_platform_ids: Sequence[str],
    input_count: int,
    status: str,
    depends_on: Sequence[str],
) -> dict[str, Any]:
    run_dir, plan_filename = _paths(root, shard_id)
    return {
        "shard_id": shard_id,
        "source_kind": source_kind,
        "stage": stage,
        "platform_ids": list(platform_ids),
        "required_platform_ids": list(required_platform_ids),
        "input_count": input_count,
        "workload": workload_for_count(input_count),
        "status": status,
        "depends_on": list(depends_on),
        "run_dir": run_dir,
        "plan_filename": plan_filename,
        "merge_contract": SHARD_RESULT_CONTRACT,
        "login_requested": False,
    }


def _platform_shards(
    scope: Mapping[str, Any], root: PurePosixPath, access_kind: str
) -> list[dict[str, Any]]:
    routes = [route for route in scope["platform_routes"] if route["access_kind"] == access_kind]
    if not routes:
        return []
    platform_ids = [route["platform_id"] for route in routes]
    required_ids = [route["platform_id"] for route in routes if route["required"]]
    stem = "platform-cli" if access_kind == "platform_cli" else "browser-session"
    if access_kind == "platform_cli":
        status = "ready_to_plan"
    elif scope["login_mode"] == "public-only":
        status = "blocked"
    else:
        status = "pending_checkpoint"

    result = []
    for stage in ("discovery", "fetch"):
        shard_id = f"{stem}-{stage}"
        row = _base_shard(
            scope,
            root,
            shard_id=shard_id,
            source_kind=access_kind,
            stage=stage,
            platform_ids=platform_ids,
            required_platform_ids=required_ids,
            input_count=len(platform_ids),
            status=status,
            depends_on=[] if stage == "discovery" else [f"{stem}-discovery"],
        )
        if status == "ready_to_plan":
            row["router_request"] = _router_request(
                scope,
                stage=stage,
                source_kind=access_kind,
                workload=row["workload"],
                run_dir=row["run_dir"],
                engine_mode="python",
                dual_run=False,
            )
        elif status == "blocked":
            row["reason_code"] = "browser_session_disallowed_in_public_only"
        else:
            row["reason_code"] = "browser_session_requires_authenticated_probe"
            row["checkpoint"] = {
                "contract": "top50-login-checkpoint/v1",
                "path": str(root / "checkpoints" / "browser-session.json"),
                "run_id": scope["run_id"],
                "access_kind": "browser_session",
                "platform_ids": platform_ids,
                "required_before_plan": True,
                "next_gate": "authenticated_read_only_probe",
            }
        result.append(row)
    return result


def _data_engine_mode(scope: Mapping[str, Any], source_kind: str) -> str:
    mode = str(scope["engine_mode"])
    if source_kind == "public_http" and mode == "rust":
        raise RouteBundleError("engine_mode=rust cannot execute an eligible public_http fetch stage")
    if source_kind == "local_bundle" and mode == "go":
        raise RouteBundleError("engine_mode=go cannot execute an eligible local_bundle process stage")
    return mode


def _public_http_shard(scope: Mapping[str, Any], root: PurePosixPath) -> dict[str, Any]:
    shard_id = "public-http-fetch"
    row = _base_shard(
        scope,
        root,
        shard_id=shard_id,
        source_kind="public_http",
        stage="fetch",
        platform_ids=[],
        required_platform_ids=[],
        input_count=scope["public_url_count"],
        status="ready_to_plan",
        depends_on=[],
    )
    row["router_request"] = _router_request(
        scope,
        stage="fetch",
        source_kind="public_http",
        workload=row["workload"],
        run_dir=row["run_dir"],
        engine_mode=_data_engine_mode(scope, "public_http"),
        dual_run=scope["dual_run"],
    )
    row["router_request"]["public_http_binding"] = dict(scope["public_http_binding"])
    return row


def _local_bundle_shards(scope: Mapping[str, Any], root: PurePosixPath) -> list[dict[str, Any]]:
    result = []
    for stage in ("process", "rank"):
        shard_id = f"local-bundle-{stage}"
        row = _base_shard(
            scope,
            root,
            shard_id=shard_id,
            source_kind="local_bundle",
            stage=stage,
            platform_ids=[],
            required_platform_ids=[],
            input_count=scope["local_candidate_count"],
            status="ready_to_plan",
            depends_on=[] if stage == "process" else ["local-bundle-process"],
        )
        row["router_request"] = _router_request(
            scope,
            stage=stage,
            source_kind="local_bundle",
            workload=row["workload"],
            run_dir=row["run_dir"],
            engine_mode=_data_engine_mode(scope, "local_bundle") if stage == "process" else "python",
            dual_run=scope["dual_run"] if stage == "process" else False,
        )
        result.append(row)
    return result


def _coverage_targets(scope: Mapping[str, Any]) -> list[dict[str, Any]]:
    routes = {route["platform_id"]: route for route in scope["platform_routes"]}
    platform_ids = (
        list(CANONICAL_PLATFORMS)
        if scope["platform_scope_mode"] == "required_plus_default"
        else [route["platform_id"] for route in scope["platform_routes"]]
    )
    rows = []
    for platform_id in platform_ids:
        route = routes.get(platform_id)
        if route is None:
            rows.append(
                {
                    "platform_id": platform_id,
                    "required": False,
                    "access_kind": None,
                    "route_status": "pending_classification",
                }
            )
            continue
        if route["access_kind"] == "browser_session" and scope["login_mode"] == "public-only":
            route_status = "blocked"
        elif route["access_kind"] == "browser_session":
            route_status = "pending_checkpoint"
        else:
            route_status = "planned"
        rows.append(
            {
                "platform_id": platform_id,
                "required": route["required"],
                "access_kind": route["access_kind"],
                "route_status": route_status,
            }
        )
    return rows


def _shared_handoffs(
    root: PurePosixPath,
    curator_acceptance: str,
    rank_result: str,
    shards: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    ready_pre_curator_shard_ids = [
        str(shard["shard_id"])
        for shard in shards
        if shard["status"] == "ready_to_plan" and shard["stage"] != "rank"
    ]
    return [
        {
            "handoff_id": "shards-to-merge",
            "from_stage": "shard_results",
            "to_stage": "merge",
            "input_shard_ids": ready_pre_curator_shard_ids,
            "input_artifact": str(root / "merge" / "shard-results.manifest.json"),
            "output_artifact": str(root / "merge" / "merged-sources.json"),
            "input_contract": SHARD_RESULT_MANIFEST_CONTRACT,
            "output_contract": "top50-route-merge-result/v1",
            "required_status": "complete",
            "fail_closed": True,
        },
        {
            "handoff_id": "merge-to-curate",
            "from_stage": "merge",
            "to_stage": "curate",
            "input_artifact": str(root / "merge" / "merged-sources.json"),
            "output_artifact": curator_acceptance,
            "input_contract": "top50-route-merge-result/v1",
            "output_contract": "top50-curator-acceptance/v1",
            "required_status": "complete",
            "fail_closed": True,
        },
        {
            "handoff_id": "curate-to-rank",
            "from_stage": "curate",
            "to_stage": "rank",
            "input_artifact": curator_acceptance,
            "output_artifact": rank_result,
            "input_contract": "top50-curator-acceptance/v1",
            "output_contract": "top50-ranking-summary/v1",
            "required_status": "accepted",
            "fail_closed": True,
        },
    ]


def _digest(payload: Mapping[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "bundle_digest_sha256"}
    canonical = json.dumps(
        material, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _bundle_object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise RouteBundleError(f"{field} must be an object")
    return value


def _bundle_array(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise RouteBundleError(f"{field} must be an array")
    return value


def _validate_object_fields(
    value: Mapping[str, Any],
    field: str,
    *,
    allowed: frozenset[str],
    required: frozenset[str] | None = None,
) -> None:
    expected = allowed if required is None else required
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        raise RouteBundleError(f"{field} is missing required fields: {', '.join(missing)}")
    if unknown:
        raise RouteBundleError(f"{field} has unknown fields: {', '.join(unknown)}")


def _canonical_platform_routes(
    coverage_targets: list[Any], *, login_mode: str, platform_scope_mode: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, value in enumerate(coverage_targets):
        field = f"coverage_targets[{index}]"
        row = _bundle_object(value, field)
        _validate_object_fields(row, field, allowed=COVERAGE_TARGET_FIELDS)
        platform_id = row.get("platform_id")
        if platform_id not in CANONICAL_PLATFORM_SET:
            raise RouteBundleError(f"{field}.platform_id is not canonical")
        if platform_id in seen:
            raise RouteBundleError(f"duplicate coverage target: {platform_id}")
        seen.add(str(platform_id))
        required = row.get("required")
        if not _is_bool(required):
            raise RouteBundleError(f"{field}.required must be a boolean")
        access_kind = row.get("access_kind")
        route_status = row.get("route_status")
        if access_kind is None:
            expected_status = "pending_classification"
            if required:
                raise RouteBundleError(
                    f"{field} pending classification cannot be required"
                )
        elif access_kind == "platform_cli":
            expected_status = "planned"
        elif access_kind == "browser_session":
            expected_status = "blocked" if login_mode == "public-only" else "pending_checkpoint"
        else:
            raise RouteBundleError(f"{field}.access_kind is invalid")
        if route_status != expected_status:
            raise RouteBundleError(f"{field}.route_status is inconsistent")
        normalized = {
            "platform_id": str(platform_id),
            "required": required,
            "access_kind": access_kind,
            "route_status": route_status,
        }
        rows.append(normalized)
        if access_kind is not None:
            routes.append(
                {
                    "platform_id": str(platform_id),
                    "access_kind": access_kind,
                    "required": required,
                }
            )

    expected_ids = (
        list(CANONICAL_PLATFORMS)
        if platform_scope_mode == "required_plus_default"
        else sorted(seen, key=CANONICAL_INDEX.__getitem__)
    )
    actual_ids = [row["platform_id"] for row in rows]
    if actual_ids != expected_ids:
        raise RouteBundleError("coverage_targets must use canonical order and scope")
    return rows, routes


def _validate_assumptions(value: Any, bundle: Mapping[str, Any]) -> None:
    assumptions = _bundle_array(value, "assumptions")
    seen: set[str] = set()
    ordered_fields: list[str] = []
    for index, raw in enumerate(assumptions):
        field = f"assumptions[{index}]"
        row = _bundle_object(raw, field)
        _validate_object_fields(row, field, allowed=ASSUMPTION_FIELDS)
        assumption_field = row.get("field")
        if assumption_field not in {"platform_scope_mode", "risk"}:
            raise RouteBundleError(f"{field}.field is invalid")
        if assumption_field in seen:
            raise RouteBundleError(f"duplicate assumption field: {assumption_field}")
        seen.add(str(assumption_field))
        ordered_fields.append(str(assumption_field))
        if row.get("reason") != "omitted_default":
            raise RouteBundleError(f"{field}.reason is invalid")
        expected_value = "required_plus_default" if assumption_field == "platform_scope_mode" else "low"
        if row.get("value") != expected_value:
            raise RouteBundleError(f"{field}.value is inconsistent")
        if bundle.get(str(assumption_field)) != expected_value:
            raise RouteBundleError(f"{field}.value is inconsistent with the bundle")
    if ordered_fields != [
        field for field in ("platform_scope_mode", "risk") if field in seen
    ]:
        raise RouteBundleError("assumptions must use canonical order")


def _validate_omissions(value: Any) -> list[Mapping[str, Any]]:
    omissions = _bundle_array(value, "omissions")
    seen: set[str] = set()
    expected_reasons = {
        "public_http": "public_urls_not_authorized",
        "local_bundle": "extraction_not_complete",
    }
    for index, raw in enumerate(omissions):
        field = f"omissions[{index}]"
        row = _bundle_object(raw, field)
        _validate_object_fields(row, field, allowed=OMISSION_FIELDS)
        source_kind = row.get("source_kind")
        if source_kind not in expected_reasons:
            raise RouteBundleError(f"{field}.source_kind is invalid")
        if source_kind in seen:
            raise RouteBundleError(f"duplicate omission source_kind: {source_kind}")
        seen.add(str(source_kind))
        if row.get("reason_code") != expected_reasons[source_kind]:
            raise RouteBundleError(f"{field}.reason_code is inconsistent")
        _validated_integer(row.get("input_count"), f"{field}.input_count", 1)
    if [row["source_kind"] for row in omissions] != [
        source_kind for source_kind in ("public_http", "local_bundle") if source_kind in seen
    ]:
        raise RouteBundleError("omissions must use canonical order")
    return [_bundle_object(row, f"omissions[{index}]") for index, row in enumerate(omissions)]


def _validate_shard_graph(shards: list[Any]) -> tuple[list[Mapping[str, Any]], list[str]]:
    normalized: list[Mapping[str, Any]] = []
    shard_ids: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    dependencies: dict[str, list[str]] = {}

    for index, value in enumerate(shards):
        row = _bundle_object(value, f"shards[{index}]")
        _validate_object_fields(
            row,
            f"shards[{index}]",
            allowed=SHARD_FIELDS,
            required=SHARD_REQUIRED_FIELDS,
        )
        shard_id = row.get("shard_id")
        if not isinstance(shard_id, str) or not shard_id:
            raise RouteBundleError(f"shards[{index}].shard_id must be a non-empty string")
        if shard_id in by_id:
            raise RouteBundleError(f"duplicate shard_id: {shard_id}")
        status = row.get("status")
        if status not in {"ready_to_plan", "pending_checkpoint", "blocked"}:
            raise RouteBundleError(f"shard {shard_id} has an invalid status")
        stage = row.get("stage")
        if stage not in {"discovery", "fetch", "process", "rank"}:
            raise RouteBundleError(f"shard {shard_id} has an invalid stage")
        raw_dependencies = _bundle_array(
            row.get("depends_on"), f"shard {shard_id}.depends_on"
        )
        if any(not isinstance(dependency, str) or not dependency for dependency in raw_dependencies):
            raise RouteBundleError(
                f"shard {shard_id}.depends_on must contain non-empty shard IDs"
            )
        if len(set(raw_dependencies)) != len(raw_dependencies):
            raise RouteBundleError(f"shard {shard_id}.depends_on contains duplicates")
        if "router_request" in row:
            router_request = _bundle_object(
                row.get("router_request"), f"shard {shard_id}.router_request"
            )
            _validate_object_fields(
                router_request,
                f"shard {shard_id}.router_request",
                allowed=ROUTER_REQUEST_FIELDS,
                required=ROUTER_REQUEST_REQUIRED_FIELDS,
            )
        if "checkpoint" in row:
            checkpoint = _bundle_object(
                row.get("checkpoint"), f"shard {shard_id}.checkpoint"
            )
            _validate_object_fields(
                checkpoint,
                f"shard {shard_id}.checkpoint",
                allowed=CHECKPOINT_FIELDS,
            )

        normalized.append(row)
        shard_ids.append(shard_id)
        by_id[shard_id] = row
        dependencies[shard_id] = list(raw_dependencies)

    for shard_id, dependency_ids in dependencies.items():
        for dependency_id in dependency_ids:
            if dependency_id not in by_id:
                raise RouteBundleError(
                    f"shard {shard_id}.depends_on references unknown shard {dependency_id}"
                )

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(shard_id: str) -> None:
        if shard_id in visited:
            return
        if shard_id in visiting:
            raise RouteBundleError("shard depends_on graph contains a cycle")
        visiting.add(shard_id)
        for dependency_id in dependencies[shard_id]:
            visit(dependency_id)
        visiting.remove(shard_id)
        visited.add(shard_id)

    for shard_id in shard_ids:
        visit(shard_id)

    shard_index = {shard_id: index for index, shard_id in enumerate(shard_ids)}
    for shard_id, dependency_ids in dependencies.items():
        if any(shard_index[dependency_id] >= shard_index[shard_id] for dependency_id in dependency_ids):
            raise RouteBundleError(
                f"shard {shard_id}.depends_on must reference an earlier shard"
            )
    return normalized, shard_ids


def _validate_plan_paths(
    bundle: Mapping[str, Any],
    shards: Sequence[Mapping[str, Any]],
    shard_ids: Sequence[str],
    root: PurePosixPath,
) -> None:
    plan_filenames = _bundle_object(bundle.get("plan_filenames"), "plan_filenames")
    if set(plan_filenames) != set(shard_ids):
        raise RouteBundleError("plan_filenames keys must equal the shard_id set")

    expected_plan_filenames: dict[str, str] = {}
    for row in shards:
        shard_id = str(row["shard_id"])
        expected_run_dir, expected_plan_filename = _paths(root, shard_id)
        if row.get("run_dir") != expected_run_dir:
            raise RouteBundleError(f"shard {shard_id} run_dir is inconsistent")
        if row.get("plan_filename") != expected_plan_filename:
            raise RouteBundleError(f"shard {shard_id} plan_filename is inconsistent")
        expected_plan_filenames[shard_id] = expected_plan_filename
        if row.get("status") == "ready_to_plan":
            router_request = _bundle_object(
                row.get("router_request"), f"shard {shard_id}.router_request"
            )
            if router_request.get("run_dir") != expected_run_dir:
                raise RouteBundleError(
                    f"shard {shard_id} router_request.run_dir is inconsistent"
                )
            if row.get("source_kind") == "public_http":
                binding = _validate_public_http_binding(
                    router_request.get("public_http_binding"),
                    expected_count=row.get("input_count"),
                    field=f"shard {shard_id}.router_request.public_http_binding",
                )
                if router_request.get("public_http_binding") != binding:
                    raise RouteBundleError(
                        f"shard {shard_id}.router_request.public_http_binding is not normalized"
                    )
            elif "public_http_binding" in router_request:
                raise RouteBundleError(
                    f"shard {shard_id}.router_request.public_http_binding is only allowed for public_http"
                )

    if dict(plan_filenames) != expected_plan_filenames:
        raise RouteBundleError("plan_filenames values must equal each shard plan_filename")


def _validate_canonical_shard_semantics(
    bundle: Mapping[str, Any],
    shards: Sequence[Mapping[str, Any]],
    platform_routes: Sequence[Mapping[str, Any]],
    root: PurePosixPath,
) -> None:
    by_id = {str(row["shard_id"]): row for row in shards}
    omission_rows = _validate_omissions(bundle.get("omissions"))
    omissions = {str(row["source_kind"]): row for row in omission_rows}

    public_row = by_id.get("public-http-fetch")
    if public_row is not None and "public_http" in omissions:
        raise RouteBundleError("public_http cannot be both routed and omitted")
    if public_row is not None:
        public_count = _validated_integer(
            public_row.get("input_count"), "public-http-fetch.input_count", 1
        )
        router_request = _bundle_object(
            public_row.get("router_request"), "shard public-http-fetch.router_request"
        )
        public_binding = _validate_public_http_binding(
            router_request.get("public_http_binding"),
            expected_count=public_count,
            field="shard public-http-fetch.router_request.public_http_binding",
        )
        public_authorized = True
    else:
        public_count = (
            int(omissions["public_http"]["input_count"])
            if "public_http" in omissions
            else 0
        )
        public_binding = None
        public_authorized = False

    local_rows = [
        row
        for shard_id, row in by_id.items()
        if shard_id in {"local-bundle-process", "local-bundle-rank"}
    ]
    if local_rows and "local_bundle" in omissions:
        raise RouteBundleError("local_bundle cannot be both routed and omitted")
    if local_rows:
        local_count = _validated_integer(
            local_rows[0].get("input_count"), "local_bundle.input_count", 1
        )
        extraction_complete = True
    else:
        local_count = (
            int(omissions["local_bundle"]["input_count"])
            if "local_bundle" in omissions
            else 0
        )
        extraction_complete = False

    scope: dict[str, Any] = {
        "run_id": bundle["run_id"],
        "top_n": bundle["top_n"],
        "engine_mode": bundle["engine_mode"],
        "dual_run": bundle["dual_run"],
        "login_mode": bundle["login_mode"],
        "risk": bundle["risk"],
        "platform_routes": list(platform_routes),
        "public_url_count": public_count,
        "public_urls_authorized": public_authorized,
        "public_http_binding": public_binding,
        "local_candidate_count": local_count,
        "extraction_complete": extraction_complete,
    }
    if bundle["engine_mode"] == "hybrid" and not (
        public_authorized or extraction_complete
    ):
        raise RouteBundleError("hybrid requires an eligible public_http or local_bundle stage")

    expected_shards: list[dict[str, Any]] = []
    expected_shards.extend(_platform_shards(scope, root, "platform_cli"))
    expected_shards.extend(_platform_shards(scope, root, "browser_session"))
    if public_authorized:
        expected_shards.append(_public_http_shard(scope, root))
    if extraction_complete:
        expected_shards.extend(_local_bundle_shards(scope, root))

    expected_omissions: list[dict[str, Any]] = []
    if public_count > 0 and not public_authorized:
        expected_omissions.append(
            {
                "source_kind": "public_http",
                "reason_code": "public_urls_not_authorized",
                "input_count": public_count,
            }
        )
    if local_count > 0 and not extraction_complete:
        expected_omissions.append(
            {
                "source_kind": "local_bundle",
                "reason_code": "extraction_not_complete",
                "input_count": local_count,
            }
        )
    if list(omission_rows) != expected_omissions:
        raise RouteBundleError("omissions do not match canonical topology")

    actual_ids = [str(row["shard_id"]) for row in shards]
    expected_ids = [str(row["shard_id"]) for row in expected_shards]
    if actual_ids != expected_ids:
        raise RouteBundleError("shards do not match canonical topology")
    for actual, expected in zip(shards, expected_shards):
        if dict(actual) != expected:
            raise RouteBundleError(
                f"shard {actual['shard_id']} semantics do not match canonical topology"
            )


def _validate_handoffs_and_artifacts(
    bundle: Mapping[str, Any],
    shards: Sequence[Mapping[str, Any]],
    root: PurePosixPath,
) -> None:
    handoffs = _bundle_array(bundle.get("shared_handoffs"), "shared_handoffs")
    if len(handoffs) != 3:
        raise RouteBundleError("shared_handoffs must contain exactly three handoffs")
    normalized_handoffs = [
        _bundle_object(value, f"shared_handoffs[{index}]")
        for index, value in enumerate(handoffs)
    ]
    expected_handoff_fields = (
        {
            "handoff_id": "shards-to-merge",
            "from_stage": "shard_results",
            "to_stage": "merge",
            "input_contract": SHARD_RESULT_MANIFEST_CONTRACT,
            "output_contract": "top50-route-merge-result/v1",
            "required_status": "complete",
            "fail_closed": True,
        },
        {
            "handoff_id": "merge-to-curate",
            "from_stage": "merge",
            "to_stage": "curate",
            "input_contract": "top50-route-merge-result/v1",
            "output_contract": "top50-curator-acceptance/v1",
            "required_status": "complete",
            "fail_closed": True,
        },
        {
            "handoff_id": "curate-to-rank",
            "from_stage": "curate",
            "to_stage": "rank",
            "input_contract": "top50-curator-acceptance/v1",
            "output_contract": "top50-ranking-summary/v1",
            "required_status": "accepted",
            "fail_closed": True,
        },
    )
    for index, expected in enumerate(expected_handoff_fields):
        handoff = normalized_handoffs[index]
        allowed_fields = (
            HANDOFF_FIELDS
            if index == 0
            else HANDOFF_FIELDS
        )
        _validate_object_fields(
            handoff,
            f"shared_handoffs[{index}]",
            allowed=allowed_fields,
            required=(
                HANDOFF_FIELDS
                if index == 0
                else HANDOFF_FIELDS - frozenset({"input_shard_ids"})
            ),
        )
        for field, expected_value in expected.items():
            if handoff.get(field) != expected_value:
                raise RouteBundleError(
                    f"shared_handoffs[{index}].{field} is inconsistent"
                )
        if index > 0 and "input_shard_ids" in handoff:
            raise RouteBundleError("only shards-to-merge may define input_shard_ids")

    expected_input_shard_ids = [
        str(row["shard_id"])
        for row in shards
        if row.get("status") == "ready_to_plan" and row.get("stage") != "rank"
    ]
    if normalized_handoffs[0].get("input_shard_ids") != expected_input_shard_ids:
        raise RouteBundleError(
            "shards-to-merge.input_shard_ids must equal the ordered ready pre-rank shard set"
        )

    artifacts = _bundle_object(bundle.get("artifacts"), "artifacts")
    _validate_object_fields(artifacts, "artifacts", allowed=ARTIFACT_FIELDS)
    local_run_dir = root / "shards" / "local-bundle"
    expected_artifacts = {
        "shard_result_manifest": str(root / "merge" / "shard-results.manifest.json"),
        "merge_result": str(root / "merge" / "merged-sources.json"),
        "extraction_result": str(local_run_dir / "extraction-result.json"),
        "curator_acceptance": str(local_run_dir / "curate-result.json"),
        "ranking_result": str(local_run_dir / "ranking-output" / "run_summary.json"),
    }
    if dict(artifacts) != expected_artifacts:
        raise RouteBundleError("artifacts paths are inconsistent with the route run")

    expected_path_chain = (
        (normalized_handoffs[0], "input_artifact", artifacts["shard_result_manifest"]),
        (normalized_handoffs[0], "output_artifact", artifacts["merge_result"]),
        (normalized_handoffs[1], "input_artifact", artifacts["merge_result"]),
        (normalized_handoffs[1], "output_artifact", artifacts["curator_acceptance"]),
        (normalized_handoffs[2], "input_artifact", artifacts["curator_acceptance"]),
        (normalized_handoffs[2], "output_artifact", artifacts["ranking_result"]),
    )
    for handoff, field, expected_path in expected_path_chain:
        if handoff.get(field) != expected_path:
            raise RouteBundleError("artifact path chain across shared_handoffs is inconsistent")


def validate_route_bundle(payload: Any) -> None:
    """Purely validate cross-field invariants of a compiled route bundle.

    JSON Schema validates the serial shape.  This runtime gate validates the
    graph, ordered shard set, deterministic paths, and self-digest without
    reading files, probing engines, or mutating the bundle.
    """
    bundle = _bundle_object(payload, "route bundle")
    _validate_object_fields(bundle, "route bundle", allowed=BUNDLE_ROOT_FIELDS)
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise RouteBundleError(f"route bundle schema must be {BUNDLE_SCHEMA}")
    run_id = _safe_run_id(bundle.get("run_id"))
    _validated_topic(bundle.get("topic"))
    _validated_integer(bundle.get("top_n"), "top_n", 1, 100)
    _validated_enum(
        bundle.get("engine_mode"),
        "engine_mode",
        ("auto", "python", "go", "rust", "hybrid"),
    )
    if not _is_bool(bundle.get("dual_run")):
        raise RouteBundleError("dual_run must be a boolean")
    login_mode = _validated_enum(
        bundle.get("login_mode"), "login_mode", ("public-only", "user-assisted")
    )
    _validated_enum(bundle.get("risk"), "risk", ("low", "medium", "high"))
    platform_scope_mode = _validated_enum(
        bundle.get("platform_scope_mode"),
        "platform_scope_mode",
        ("required_plus_default", "include_only"),
    )
    try:
        _digest(bundle)
    except (TypeError, ValueError) as exc:
        raise RouteBundleError(f"route bundle is not canonically serializable: {exc}") from exc
    _validate_assumptions(bundle.get("assumptions"), bundle)
    _, platform_routes = _canonical_platform_routes(
        _bundle_array(bundle.get("coverage_targets"), "coverage_targets"),
        login_mode=login_mode,
        platform_scope_mode=platform_scope_mode,
    )
    shards_value = _bundle_array(bundle.get("shards"), "shards")
    if not shards_value:
        raise RouteBundleError("shards must contain at least one shard")
    shards, shard_ids = _validate_shard_graph(shards_value)
    root = PurePosixPath("route-runs") / run_id
    _validate_plan_paths(bundle, shards, shard_ids, root)
    _validate_canonical_shard_semantics(bundle, shards, platform_routes, root)
    _validate_handoffs_and_artifacts(bundle, shards, root)

    digest = bundle.get("bundle_digest_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise RouteBundleError("bundle_digest_sha256 must be 64 lowercase hexadecimal characters")
    try:
        expected_digest = _digest(bundle)
    except (TypeError, ValueError) as exc:
        raise RouteBundleError(f"route bundle is not canonically serializable: {exc}") from exc
    if digest != expected_digest:
        raise RouteBundleError("bundle_digest_sha256 does not match the bundle contents")


def compile_route_bundle(payload: Any) -> dict[str, Any]:
    """Compile a structured scope into replayable, independently planned shards."""
    scope = validate_scope(payload)
    public_eligible = scope["public_url_count"] > 0 and scope["public_urls_authorized"]
    local_eligible = scope["local_candidate_count"] > 0 and scope["extraction_complete"]
    if scope["engine_mode"] == "hybrid" and not (public_eligible or local_eligible):
        raise RouteBundleError(
            "hybrid requires an eligible public_http or local_bundle stage"
        )

    root = PurePosixPath("route-runs") / scope["run_id"]
    shards = []
    shards.extend(_platform_shards(scope, root, "platform_cli"))
    shards.extend(_platform_shards(scope, root, "browser_session"))
    omissions = []
    if public_eligible:
        shards.append(_public_http_shard(scope, root))
    elif scope["public_url_count"] > 0:
        omissions.append(
            {
                "source_kind": "public_http",
                "reason_code": "public_urls_not_authorized",
                "input_count": scope["public_url_count"],
            }
        )
    if local_eligible:
        shards.extend(_local_bundle_shards(scope, root))
    elif scope["local_candidate_count"] > 0:
        omissions.append(
            {
                "source_kind": "local_bundle",
                "reason_code": "extraction_not_complete",
                "input_count": scope["local_candidate_count"],
            }
        )
    if not shards:
        raise RouteBundleError("route scope compiles to no shards")

    assumptions = []
    if scope["_scope_mode_was_defaulted"]:
        assumptions.append(
            {
                "field": "platform_scope_mode",
                "value": "required_plus_default",
                "reason": "omitted_default",
            }
        )
    if scope["_risk_was_defaulted"]:
        assumptions.append({"field": "risk", "value": "low", "reason": "omitted_default"})

    plan_filenames = {row["shard_id"]: row["plan_filename"] for row in shards}
    local_run_dir = root / "shards" / "local-bundle"
    extraction_result = str(local_run_dir / "extraction-result.json")
    curator_acceptance = str(local_run_dir / "curate-result.json")
    rank_result = str(local_run_dir / "ranking-output" / "run_summary.json")
    bundle: dict[str, Any] = {
        "schema": BUNDLE_SCHEMA,
        "run_id": scope["run_id"],
        "topic": scope["topic"],
        "top_n": scope["top_n"],
        "engine_mode": scope["engine_mode"],
        "dual_run": scope["dual_run"],
        "login_mode": scope["login_mode"],
        "risk": scope["risk"],
        "platform_scope_mode": scope["platform_scope_mode"],
        "assumptions": assumptions,
        "coverage_targets": _coverage_targets(scope),
        "shards": shards,
        "omissions": omissions,
        "shared_handoffs": _shared_handoffs(
            root, curator_acceptance, rank_result, shards
        ),
        "artifacts": {
            "shard_result_manifest": str(root / "merge" / "shard-results.manifest.json"),
            "merge_result": str(root / "merge" / "merged-sources.json"),
            "extraction_result": extraction_result,
            "curator_acceptance": curator_acceptance,
            "ranking_result": rank_result,
        },
        "plan_filenames": plan_filenames,
    }
    bundle["bundle_digest_sha256"] = _digest(bundle)
    validate_route_bundle(bundle)
    return bundle


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a structured Top 50 route scope into deterministic router-request shards."
    )
    parser.add_argument("--input", required=True, type=Path, help="top50-route-scope/v1 JSON")
    parser.add_argument("--output", required=True, type=Path, help="output bundle JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        with args.input.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        bundle = compile_route_bundle(payload)
        _atomic_write_json(args.output, bundle)
    except (OSError, UnicodeError, json.JSONDecodeError, RouteBundleError) as exc:
        print(f"route bundle error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
