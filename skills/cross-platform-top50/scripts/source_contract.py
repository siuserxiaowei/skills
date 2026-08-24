#!/usr/bin/env python3
"""Normalize source-route outcomes and maintain resumable research checkpoints.

The module records acquisition provenance without treating successful transport
or a search snippet as reviewed evidence.  Retry decisions are deterministic,
bounded, and terminal access controls are never retried automatically.
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
from datetime import date, datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


OBSERVATION_SCHEMA = "top50-source-observation/v1"
OUTCOME_SCHEMA = "top50-source-outcome/v1"
CHECKPOINT_SCHEMA = "top50-research-checkpoint/v1"
RESUME_SCHEMA = "top50-checkpoint-resume/v1"

CANONICAL_PLATFORMS = {
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
}
ACCESS_KINDS = {"platform_cli", "browser_session", "public_http", "reader_proxy"}
ACQUISITION_METHODS = {
    "platform_native",
    "direct_http",
    "authorized_browser",
    "platform_cli",
    "search_index",
    "user_supplied",
    "reader_proxy",
}
EVIDENCE_TIERS = {
    "full_content",
    "partial_content",
    "metadata_only",
    "search_snippet",
    "user_observation",
}
PAYLOAD_SHAPES = {"content_cards", "suggestions", "empty", "unknown"}
DATE_CONFIDENCES = {"observed", "inferred", "unknown"}
DATE_BASES = {
    "platform_timestamp",
    "document_metadata",
    "content_text",
    "search_index",
    "user_report",
    "unavailable",
}
RESULT_STATES = {
    "success",
    "empty",
    "rate_limited",
    "transient_error",
    "parse_error",
    "authentication_required",
    "challenge",
    "robots_blocked",
    "unauthorized",
    "not_found",
}
AUTHORIZATIONS = {
    "granted_for_current_task",
    "not_required",
    "not_granted",
}
RETRYABLE_STATES = {"rate_limited", "transient_error"}
TERMINAL_ACCESS_STATES = {
    "authentication_required",
    "challenge",
    "robots_blocked",
    "unauthorized",
}
OBSERVATION_FIELDS = {
    "schema",
    "run_id",
    "query_id",
    "route_id",
    "platform_id",
    "adapter_id",
    "access_kind",
    "acquisition_method",
    "evidence_tier",
    "url",
    "observed_at",
    "http_status",
    "result_state",
    "attempt",
    "max_attempts",
    "breaker_failure_count",
    "breaker_threshold",
    "breaker_cooldown_seconds",
    "timeframe",
    "window_timezone",
    "published_at",
    "published_at_confidence",
    "date_basis",
    "content_sha256",
    "response_endpoint",
    "payload_shape",
    "content_card_count",
    "backend_id",
    "probe_id",
    "authorization",
    "error_code",
    "error_summary",
    "retry_after_seconds",
}
CHECKPOINT_INPUT_FIELDS = {
    "run_id",
    "topic",
    "platform_id",
    "stage",
    "exact_probe_or_command",
    "tool_readiness",
    "bridge_state",
    "auth_state",
    "quota_state",
    "authorization",
    "probe_result",
    "error_summary",
    "completed_query_ids",
    "pending_query_ids",
    "candidate_ids",
    "artifact_paths",
    "next_safe_command",
    "ttl_seconds",
}
STAGES = {"scope", "discovery", "fetch", "extraction", "worker_check"}
CHECKPOINT_FIELDS = CHECKPOINT_INPUT_FIELDS | {
    "schema",
    "checkpoint_id",
    "idempotency_key",
    "created_at",
    "updated_at",
    "expires_at",
    "status",
    "resume_count",
    "error_history",
    "checkpoint_digest_sha256",
}

OUTCOME_FIELDS = {
    "schema",
    "run_id",
    "query_id",
    "route_id",
    "platform_id",
    "adapter_id",
    "url",
    "observed_at",
    "normalized_at",
    "source_status",
    "eligibility",
    "may_enter_time_bounded_ranking",
    "may_enter_general_review",
    "date_qualification",
    "discoveries_allowed",
    "discovery_count",
    "timeframe",
    "window_timezone",
    "published_at",
    "published_at_confidence",
    "date_basis",
    "acquisition",
    "error",
    "recovery_basis",
    "retry",
    "breaker",
    "outcome_digest_sha256",
}
ACQUISITION_FIELDS = {
    "method",
    "access_kind",
    "evidence_tier",
    "backend_id",
    "probe_id",
    "authorization",
    "http_status",
    "content_sha256",
    "response_endpoint",
    "payload_shape",
    "content_card_count",
}
ERROR_FIELDS = {"code", "summary"}
RECOVERY_BASIS_FIELDS = {
    "result_state",
    "attempt",
    "max_attempts",
    "retry_after_seconds",
    "breaker_failure_count",
    "breaker_threshold",
    "breaker_cooldown_seconds",
}
RETRY_FIELDS = {
    "decision",
    "attempt",
    "max_attempts",
    "remaining_attempts",
    "delay_seconds",
    "reason",
}
BREAKER_FIELDS = {
    "action",
    "scope",
    "reason",
    "failure_count",
    "threshold",
    "cooldown_seconds",
}


class SourceContractError(ValueError):
    """An outcome or checkpoint violates the canonical source contract."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Mapping[str, Any], *, omit: Sequence[str] = ()) -> str:
    payload = {key: item for key, item in value.items() if key not in set(omit)}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _value_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: Any, field: str, *, maximum: int = 1_000) -> str:
    if not isinstance(value, str):
        raise SourceContractError(f"{field} must be a string")
    result = unicodedata.normalize("NFC", value).strip()
    if not result or len(result) > maximum:
        raise SourceContractError(f"{field} must contain 1-{maximum} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in result):
        raise SourceContractError(f"{field} must not contain control characters")
    return result


def _optional_text(value: Any, field: str, *, maximum: int = 1_000) -> str | None:
    if value is None:
        return None
    return _text(value, field, maximum=maximum)


def _identifier(value: Any, field: str) -> str:
    result = _text(value, field, maximum=128)
    if result in {".", ".."} or re.fullmatch(r"[A-Za-z0-9._:-]+", result) is None:
        raise SourceContractError(f"{field} must be a safe identifier")
    return result


def _enum(value: Any, field: str, allowed: set[str]) -> str:
    if value not in allowed:
        raise SourceContractError(f"{field} is not supported")
    return str(value)


def _parse_timestamp(value: Any, field: str) -> datetime:
    text = _text(value, field, maximum=40)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceContractError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise SourceContractError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _timeframe(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"start", "end"}:
        raise SourceContractError("timeframe must contain exactly start and end")
    try:
        start = date.fromisoformat(str(value["start"]))
        end = date.fromisoformat(str(value["end"]))
    except ValueError as exc:
        raise SourceContractError("timeframe must use YYYY-MM-DD dates") from exc
    if start > end:
        raise SourceContractError("timeframe start must not be after end")
    return {"start": start.isoformat(), "end": end.isoformat()}


def _window_timezone(value: Any) -> str:
    timezone_name = _text(value, "window_timezone", maximum=128)
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise SourceContractError(
            "window_timezone must be a valid IANA timezone"
        ) from exc
    return timezone_name


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise SourceContractError("timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _sha256_or_none(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise SourceContractError(f"{field} must be a lowercase SHA-256 or null")
    return value


def _public_url(value: Any) -> str:
    url = _text(value, "url", maximum=4_096)
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SourceContractError("url must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise SourceContractError("url must not contain credentials")
    return url


def _bounded_integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise SourceContractError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def _sorted_identifiers(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise SourceContractError(f"{field} must be an array")
    return sorted({_identifier(item, field) for item in value})


def _safe_relative_path(value: Any, field: str) -> str:
    text = _text(value, field, maximum=1_024)
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SourceContractError(f"{field} must be a safe relative path")
    return str(path)


def _command(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > 64:
        raise SourceContractError(f"{field} must be a non-empty bounded argument array")
    command = [_text(item, field, maximum=1_000) for item in value]
    secret_markers = (
        "--cookie",
        "--header",
        "authorization",
        "api-key",
        "api_key",
        "access-token",
        "access_token",
        "bearer",
    )
    if any(marker in argument.casefold() for argument in command for marker in secret_markers):
        raise SourceContractError(f"{field} must not contain secret-bearing arguments")
    return command


def _source_status(result_state: str, evidence_tier: str) -> str:
    if result_state == "success":
        return "discovered_only" if evidence_tier == "search_snippet" else "fetched"
    return {
        "empty": "empty",
        "rate_limited": "rate_limited",
        "transient_error": "error",
        "parse_error": "error",
        "authentication_required": "blocked_auth",
        "challenge": "blocked_challenge",
        "robots_blocked": "blocked_robots",
        "unauthorized": "blocked_unauthorized",
        "not_found": "not_found",
    }[result_state]


def _retry_policy(
    result_state: str,
    attempt: int,
    max_attempts: int,
    retry_after_seconds: int | None,
    breaker_failure_count: int,
    breaker_threshold: int,
    breaker_cooldown_seconds: int,
) -> tuple[dict[str, Any], dict[str, str]]:
    if result_state in TERMINAL_ACCESS_STATES:
        return (
            {
                "decision": "terminal",
                "attempt": attempt,
                "max_attempts": max_attempts,
                "remaining_attempts": 0,
                "delay_seconds": None,
                "reason": "access_control_requires_user_or_route_change",
            },
            {
                "action": "do_not_count",
                "scope": "",
                "reason": "terminal_access_state",
                "failure_count": breaker_failure_count,
                "threshold": breaker_threshold,
                "cooldown_seconds": breaker_cooldown_seconds,
            },
        )
    if result_state in RETRYABLE_STATES:
        if attempt >= max_attempts:
            return (
                {
                    "decision": "exhausted",
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "remaining_attempts": 0,
                    "delay_seconds": None,
                    "reason": "bounded_attempts_exhausted",
                },
                {
                    "action": "open",
                    "scope": "",
                    "reason": "retry_budget_exhausted",
                    "failure_count": breaker_failure_count,
                    "threshold": breaker_threshold,
                    "cooldown_seconds": breaker_cooldown_seconds,
                },
            )
        delay = retry_after_seconds if retry_after_seconds is not None else min(300, 2 ** attempt)
        return (
            {
                "decision": "retry_after",
                "attempt": attempt,
                "max_attempts": max_attempts,
                "remaining_attempts": max_attempts - attempt,
                "delay_seconds": delay,
                "reason": "server_rate_limit" if result_state == "rate_limited" else "transient_failure",
            },
            {
                "action": "open"
                if breaker_failure_count + 1 >= breaker_threshold
                else "count_failure",
                "scope": "",
                "reason": result_state,
                "failure_count": breaker_failure_count + 1,
                "threshold": breaker_threshold,
                "cooldown_seconds": breaker_cooldown_seconds,
            },
        )
    return (
        {
            "decision": "do_not_retry",
            "attempt": attempt,
            "max_attempts": max_attempts,
            "remaining_attempts": max(0, max_attempts - attempt),
            "delay_seconds": None,
            "reason": "completed_or_nonretryable_result",
        },
        {
            "action": "record_success" if result_state == "success" else "do_not_count",
            "scope": "",
            "reason": result_state,
            "failure_count": 0 if result_state == "success" else breaker_failure_count,
            "threshold": breaker_threshold,
            "cooldown_seconds": breaker_cooldown_seconds,
        },
    )


def _validated_observation(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise SourceContractError("source observation must be a JSON object")
    unexpected = set(payload) - OBSERVATION_FIELDS
    missing = OBSERVATION_FIELDS - set(payload)
    if unexpected:
        raise SourceContractError(f"source observation has unexpected fields: {', '.join(sorted(unexpected))}")
    if missing:
        raise SourceContractError(f"source observation is missing fields: {', '.join(sorted(missing))}")
    if payload.get("schema") != OBSERVATION_SCHEMA:
        raise SourceContractError(f"schema must be {OBSERVATION_SCHEMA}")
    attempt = _bounded_integer(payload.get("attempt"), "attempt", 1, 5)
    maximum = _bounded_integer(payload.get("max_attempts"), "max_attempts", 1, 5)
    if attempt > maximum:
        raise SourceContractError("attempt must not exceed max_attempts")
    result_state = _enum(payload.get("result_state"), "result_state", RESULT_STATES)
    failure_count = _bounded_integer(
        payload.get("breaker_failure_count"), "breaker_failure_count", 0, 99
    )
    breaker_threshold = _bounded_integer(
        payload.get("breaker_threshold"), "breaker_threshold", 1, 20
    )
    if failure_count > breaker_threshold:
        raise SourceContractError("breaker_failure_count must not exceed breaker_threshold")
    breaker_cooldown = _bounded_integer(
        payload.get("breaker_cooldown_seconds"),
        "breaker_cooldown_seconds",
        1,
        86_400,
    )
    timeframe = _timeframe(payload.get("timeframe"))
    evidence_tier = _enum(payload.get("evidence_tier"), "evidence_tier", EVIDENCE_TIERS)
    content_sha256 = _sha256_or_none(payload.get("content_sha256"), "content_sha256")
    payload_shape = _enum(payload.get("payload_shape"), "payload_shape", PAYLOAD_SHAPES)
    if (
        result_state == "success"
        and evidence_tier != "search_snippet"
        and payload_shape == "content_cards"
        and content_sha256 is None
    ):
        raise SourceContractError("successful content acquisition requires content_sha256")
    if result_state != "success" and content_sha256 is not None:
        raise SourceContractError("failed acquisition cannot declare content_sha256")
    response_endpoint = _public_url(payload.get("response_endpoint"))
    content_card_count = _bounded_integer(
        payload.get("content_card_count"), "content_card_count", 0, 100_000
    )
    if payload_shape == "content_cards" and content_card_count < 1:
        raise SourceContractError("content_cards payload requires at least one content card")
    if payload_shape != "content_cards" and content_card_count != 0:
        raise SourceContractError("non-content payload shape cannot declare content cards")
    if result_state != "success" and content_card_count != 0:
        raise SourceContractError("non-success payload cannot declare content cards")
    confidence = _enum(
        payload.get("published_at_confidence"), "published_at_confidence", DATE_CONFIDENCES
    )
    published_at = payload.get("published_at")
    parsed_published = _parse_timestamp(published_at, "published_at") if published_at is not None else None
    if (parsed_published is None) != (confidence == "unknown"):
        raise SourceContractError("published_at and published_at_confidence are inconsistent")
    date_basis = _enum(payload.get("date_basis"), "date_basis", DATE_BASES)
    if confidence == "unknown" and date_basis != "unavailable":
        raise SourceContractError("unknown published_at requires date_basis=unavailable")
    retry_after = payload.get("retry_after_seconds")
    if retry_after is not None:
        retry_after = _bounded_integer(retry_after, "retry_after_seconds", 1, 86_400)
        if result_state != "rate_limited":
            raise SourceContractError("retry_after_seconds is only valid for rate_limited")
    http_status = payload.get("http_status")
    if http_status is not None:
        http_status = _bounded_integer(http_status, "http_status", 100, 599)
    if (
        result_state == "success"
        and http_status is not None
        and not 200 <= http_status < 300
    ):
        raise SourceContractError(
            "successful outcome requires a 2xx http_status when one is observed"
        )
    if result_state == "rate_limited" and http_status != 429:
        raise SourceContractError("rate_limited result_state requires http_status=429")
    error_code = _optional_text(payload.get("error_code"), "error_code", maximum=128)
    error_summary = _optional_text(payload.get("error_summary"), "error_summary", maximum=2_000)
    if result_state == "success" and (error_code is not None or error_summary is not None):
        raise SourceContractError("successful outcome cannot declare an error")
    if result_state != "success" and (error_code is None or error_summary is None):
        raise SourceContractError("non-success outcome requires error_code and error_summary")
    platform = _enum(payload.get("platform_id"), "platform_id", CANONICAL_PLATFORMS)
    authorization = _enum(payload.get("authorization"), "authorization", AUTHORIZATIONS)
    if authorization == "not_granted" and result_state == "success":
        raise SourceContractError("authorization not_granted cannot produce a successful outcome")
    return {
        "run_id": _identifier(payload.get("run_id"), "run_id"),
        "query_id": _identifier(payload.get("query_id"), "query_id"),
        "route_id": _identifier(payload.get("route_id"), "route_id"),
        "platform_id": platform,
        "adapter_id": _identifier(payload.get("adapter_id"), "adapter_id"),
        "access_kind": _enum(payload.get("access_kind"), "access_kind", ACCESS_KINDS),
        "acquisition_method": _enum(
            payload.get("acquisition_method"), "acquisition_method", ACQUISITION_METHODS
        ),
        "evidence_tier": evidence_tier,
        "url": _public_url(payload.get("url")),
        "observed_at": _timestamp(_parse_timestamp(payload.get("observed_at"), "observed_at")),
        "http_status": http_status,
        "result_state": result_state,
        "attempt": attempt,
        "max_attempts": maximum,
        "breaker_failure_count": failure_count,
        "breaker_threshold": breaker_threshold,
        "breaker_cooldown_seconds": breaker_cooldown,
        "timeframe": timeframe,
        "window_timezone": _window_timezone(payload.get("window_timezone")),
        "published_at": _timestamp(parsed_published) if parsed_published else None,
        "published_at_confidence": confidence,
        "date_basis": date_basis,
        "content_sha256": content_sha256,
        "response_endpoint": response_endpoint,
        "payload_shape": payload_shape,
        "content_card_count": content_card_count,
        "backend_id": _identifier(payload.get("backend_id"), "backend_id"),
        "probe_id": _identifier(payload.get("probe_id"), "probe_id"),
        "authorization": authorization,
        "error_code": error_code,
        "error_summary": error_summary,
        "retry_after_seconds": retry_after,
    }


def _date_qualification(
    *,
    published_at: str | None,
    confidence: str,
    timeframe: Mapping[str, Any],
    window_timezone: str,
) -> str:
    normalized_timeframe = _timeframe(timeframe)
    timezone_name = _window_timezone(window_timezone)
    if confidence == "unknown":
        if published_at is not None:
            raise SourceContractError(
                "published_at and published_at_confidence are inconsistent"
            )
        return "unknown_isolated"
    if published_at is None:
        raise SourceContractError("source outcome semantic date is missing")
    published_date = _parse_timestamp(published_at, "published_at").astimezone(
        ZoneInfo(timezone_name)
    ).date()
    window_start = date.fromisoformat(normalized_timeframe["start"])
    window_end = date.fromisoformat(normalized_timeframe["end"])
    if published_date < window_start:
        return "before_window"
    if published_date > window_end:
        return "after_window"
    if confidence == "inferred":
        return "within_window_inferred"
    if confidence == "observed":
        return "within_window"
    raise SourceContractError("published_at_confidence is not supported")


def _derived_source_status(
    result_state: str, evidence_tier: str, payload_shape: str
) -> str:
    source_status = _source_status(result_state, evidence_tier)
    if result_state == "success" and payload_shape in {"suggestions", "unknown"}:
        return "rejected_payload_shape"
    if result_state == "success" and payload_shape == "empty":
        return "empty"
    return source_status


def _derived_eligibility(source_status: str, date_qualification: str) -> str:
    if source_status.startswith("blocked_"):
        return "blocked"
    if source_status == "discovered_only":
        return "discovery_only"
    if source_status == "fetched" and date_qualification == "unknown_isolated":
        return "isolated_unknown_date"
    if source_status == "fetched" and date_qualification == "within_window_inferred":
        return "inferred_date_review_only"
    if source_status == "fetched" and date_qualification in {
        "before_window",
        "after_window",
    }:
        return "outside_timeframe"
    if source_status == "fetched" and date_qualification == "within_window":
        return "eligible_for_review"
    return "not_eligible"


def _recovery_basis(observation: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "result_state": observation["result_state"],
        "attempt": observation["attempt"],
        "max_attempts": observation["max_attempts"],
        "retry_after_seconds": observation["retry_after_seconds"],
        "breaker_failure_count": observation["breaker_failure_count"],
        "breaker_threshold": observation["breaker_threshold"],
        "breaker_cooldown_seconds": observation["breaker_cooldown_seconds"],
    }


def _derived_recovery(
    basis: Mapping[str, Any], *, platform_id: str, adapter_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    retry, breaker = _retry_policy(
        str(basis["result_state"]),
        int(basis["attempt"]),
        int(basis["max_attempts"]),
        basis["retry_after_seconds"],
        int(basis["breaker_failure_count"]),
        int(basis["breaker_threshold"]),
        int(basis["breaker_cooldown_seconds"]),
    )
    breaker["scope"] = f"{platform_id}:{adapter_id}"
    return retry, breaker


def normalize_source_outcome(
    payload: Any, *, now: datetime | None = None, _validate: bool = True
) -> dict[str, Any]:
    observation = _validated_observation(payload)
    now_value = now or datetime.now(timezone.utc)
    normalized_at = _timestamp(now_value)
    recovery_basis = _recovery_basis(observation)
    retry, breaker = _derived_recovery(
        recovery_basis,
        platform_id=observation["platform_id"],
        adapter_id=observation["adapter_id"],
    )
    source_status = _derived_source_status(
        observation["result_state"],
        observation["evidence_tier"],
        observation["payload_shape"],
    )
    date_qualification = _date_qualification(
        published_at=observation["published_at"],
        confidence=observation["published_at_confidence"],
        timeframe=observation["timeframe"],
        window_timezone=observation["window_timezone"],
    )
    eligibility = _derived_eligibility(source_status, date_qualification)
    outcome: dict[str, Any] = {
        "schema": OUTCOME_SCHEMA,
        "run_id": observation["run_id"],
        "query_id": observation["query_id"],
        "route_id": observation["route_id"],
        "platform_id": observation["platform_id"],
        "adapter_id": observation["adapter_id"],
        "url": observation["url"],
        "observed_at": observation["observed_at"],
        "normalized_at": normalized_at,
        "source_status": source_status,
        "eligibility": eligibility,
        "may_enter_time_bounded_ranking": eligibility == "eligible_for_review",
        "may_enter_general_review": eligibility
        in {
            "eligible_for_review",
            "isolated_unknown_date",
            "inferred_date_review_only",
        },
        "date_qualification": date_qualification,
        "discoveries_allowed": observation["result_state"] == "success"
        and observation["payload_shape"] == "content_cards"
        and observation["content_card_count"] > 0,
        "discovery_count": observation["content_card_count"]
        if observation["result_state"] == "success"
        and observation["payload_shape"] == "content_cards"
        else 0,
        "timeframe": observation["timeframe"],
        "window_timezone": observation["window_timezone"],
        "published_at": observation["published_at"],
        "published_at_confidence": observation["published_at_confidence"],
        "date_basis": observation["date_basis"],
        "acquisition": {
            "method": observation["acquisition_method"],
            "access_kind": observation["access_kind"],
            "evidence_tier": observation["evidence_tier"],
            "backend_id": observation["backend_id"],
            "probe_id": observation["probe_id"],
            "authorization": observation["authorization"],
            "http_status": observation["http_status"],
            "content_sha256": observation["content_sha256"],
            "response_endpoint": observation["response_endpoint"],
            "payload_shape": observation["payload_shape"],
            "content_card_count": observation["content_card_count"],
        },
        "error": {
            "code": observation["error_code"],
            "summary": observation["error_summary"],
        },
        "recovery_basis": recovery_basis,
        "retry": retry,
        "breaker": breaker,
    }
    outcome["outcome_digest_sha256"] = _digest(outcome)
    if _validate:
        validate_source_outcome(outcome)
    return outcome


def validate_source_outcome(outcome: Any) -> None:
    if not isinstance(outcome, Mapping):
        raise SourceContractError("source outcome must be a JSON object")
    unexpected = set(outcome) - OUTCOME_FIELDS
    missing = OUTCOME_FIELDS - set(outcome)
    if unexpected or missing:
        details = unexpected if unexpected else missing
        kind = "unexpected" if unexpected else "missing"
        raise SourceContractError(
            f"source outcome has {kind} fields: {', '.join(sorted(details))}"
        )
    if outcome.get("schema") != OUTCOME_SCHEMA:
        raise SourceContractError(f"source outcome schema must be {OUTCOME_SCHEMA}")
    digest = outcome.get("outcome_digest_sha256")
    if not isinstance(digest, str) or digest != _digest(
        outcome, omit=("outcome_digest_sha256",)
    ):
        raise SourceContractError("source outcome digest does not match its contents")
    acquisition = outcome.get("acquisition")
    error = outcome.get("error")
    recovery_basis = outcome.get("recovery_basis")
    retry = outcome.get("retry")
    breaker = outcome.get("breaker")
    nested = (
        ("acquisition", acquisition, ACQUISITION_FIELDS),
        ("error", error, ERROR_FIELDS),
        ("recovery_basis", recovery_basis, RECOVERY_BASIS_FIELDS),
        ("retry", retry, RETRY_FIELDS),
        ("breaker", breaker, BREAKER_FIELDS),
    )
    for field, value, fields in nested:
        if not isinstance(value, Mapping) or set(value) != fields:
            raise SourceContractError(
                f"source outcome {field} fields do not match the contract"
            )

    # Reconstruct the exact observation projection carried by this outcome and
    # run it through the canonical observation validator.  A digest only binds
    # bytes; it must not let a caller re-seal impossible acquisition semantics
    # such as success+401, not_granted authorization, missing content hashes,
    # or success records with an error object.
    observation = _validated_observation(
        {
            "schema": OBSERVATION_SCHEMA,
            "run_id": outcome.get("run_id"),
            "query_id": outcome.get("query_id"),
            "route_id": outcome.get("route_id"),
            "platform_id": outcome.get("platform_id"),
            "adapter_id": outcome.get("adapter_id"),
            "access_kind": acquisition.get("access_kind"),
            "acquisition_method": acquisition.get("method"),
            "evidence_tier": acquisition.get("evidence_tier"),
            "url": outcome.get("url"),
            "observed_at": outcome.get("observed_at"),
            "http_status": acquisition.get("http_status"),
            "result_state": recovery_basis.get("result_state"),
            "attempt": recovery_basis.get("attempt"),
            "max_attempts": recovery_basis.get("max_attempts"),
            "breaker_failure_count": recovery_basis.get(
                "breaker_failure_count"
            ),
            "breaker_threshold": recovery_basis.get("breaker_threshold"),
            "breaker_cooldown_seconds": recovery_basis.get(
                "breaker_cooldown_seconds"
            ),
            "timeframe": outcome.get("timeframe"),
            "window_timezone": outcome.get("window_timezone"),
            "published_at": outcome.get("published_at"),
            "published_at_confidence": outcome.get("published_at_confidence"),
            "date_basis": outcome.get("date_basis"),
            "content_sha256": acquisition.get("content_sha256"),
            "response_endpoint": acquisition.get("response_endpoint"),
            "payload_shape": acquisition.get("payload_shape"),
            "content_card_count": acquisition.get("content_card_count"),
            "backend_id": acquisition.get("backend_id"),
            "probe_id": acquisition.get("probe_id"),
            "authorization": acquisition.get("authorization"),
            "error_code": error.get("code"),
            "error_summary": error.get("summary"),
            "retry_after_seconds": recovery_basis.get("retry_after_seconds"),
        }
    )
    expected_acquisition = {
        "method": observation["acquisition_method"],
        "access_kind": observation["access_kind"],
        "evidence_tier": observation["evidence_tier"],
        "backend_id": observation["backend_id"],
        "probe_id": observation["probe_id"],
        "authorization": observation["authorization"],
        "http_status": observation["http_status"],
        "content_sha256": observation["content_sha256"],
        "response_endpoint": observation["response_endpoint"],
        "payload_shape": observation["payload_shape"],
        "content_card_count": observation["content_card_count"],
    }
    expected_error = {
        "code": observation["error_code"],
        "summary": observation["error_summary"],
    }
    expected_root_projection = {
        "run_id": observation["run_id"],
        "query_id": observation["query_id"],
        "route_id": observation["route_id"],
        "platform_id": observation["platform_id"],
        "adapter_id": observation["adapter_id"],
        "url": observation["url"],
        "observed_at": observation["observed_at"],
        "timeframe": observation["timeframe"],
        "window_timezone": observation["window_timezone"],
        "published_at": observation["published_at"],
        "published_at_confidence": observation["published_at_confidence"],
        "date_basis": observation["date_basis"],
    }
    if dict(acquisition) != expected_acquisition or dict(error) != expected_error:
        raise SourceContractError(
            "source outcome acquisition or error projection is not canonical"
        )
    if dict(recovery_basis) != _recovery_basis(observation):
        raise SourceContractError(
            "source outcome recovery basis is not the canonical observation projection"
        )
    if any(outcome.get(field) != value for field, value in expected_root_projection.items()):
        raise SourceContractError(
            "source outcome identity, URL, date, or observation time is not canonical"
        )
    normalized_at = _parse_timestamp(outcome.get("normalized_at"), "normalized_at")
    if outcome.get("normalized_at") != _timestamp(normalized_at):
        raise SourceContractError("source outcome normalized_at is not canonical UTC")
    if normalized_at < _parse_timestamp(observation["observed_at"], "observed_at"):
        raise SourceContractError(
            "source outcome normalized_at must not precede observed_at"
        )

    platform_id = observation["platform_id"]
    adapter_id = observation["adapter_id"]
    confidence = observation["published_at_confidence"]
    expected_qualification = _date_qualification(
        published_at=outcome.get("published_at"),
        confidence=confidence,
        timeframe=outcome.get("timeframe"),
        window_timezone=_window_timezone(outcome.get("window_timezone")),
    )
    if outcome.get("date_qualification") != expected_qualification:
        raise SourceContractError(
            "source outcome date qualification is not derived from timeframe"
        )

    result_state = _enum(
        recovery_basis.get("result_state"), "recovery_basis.result_state", RESULT_STATES
    )
    attempt = _bounded_integer(
        recovery_basis.get("attempt"), "recovery_basis.attempt", 1, 5
    )
    max_attempts = _bounded_integer(
        recovery_basis.get("max_attempts"), "recovery_basis.max_attempts", 1, 5
    )
    if attempt > max_attempts:
        raise SourceContractError("recovery_basis attempt must not exceed max_attempts")
    retry_after = recovery_basis.get("retry_after_seconds")
    if retry_after is not None:
        retry_after = _bounded_integer(
            retry_after, "recovery_basis.retry_after_seconds", 1, 86_400
        )
        if result_state != "rate_limited":
            raise SourceContractError(
                "recovery_basis retry_after_seconds requires rate_limited"
            )
    failure_count = _bounded_integer(
        recovery_basis.get("breaker_failure_count"),
        "recovery_basis.breaker_failure_count",
        0,
        99,
    )
    threshold = _bounded_integer(
        recovery_basis.get("breaker_threshold"),
        "recovery_basis.breaker_threshold",
        1,
        20,
    )
    if failure_count > threshold:
        raise SourceContractError(
            "recovery_basis breaker_failure_count must not exceed threshold"
        )
    cooldown = _bounded_integer(
        recovery_basis.get("breaker_cooldown_seconds"),
        "recovery_basis.breaker_cooldown_seconds",
        1,
        86_400,
    )
    normalized_basis = {
        "result_state": result_state,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "retry_after_seconds": retry_after,
        "breaker_failure_count": failure_count,
        "breaker_threshold": threshold,
        "breaker_cooldown_seconds": cooldown,
    }
    expected_retry, expected_breaker = _derived_recovery(
        normalized_basis, platform_id=platform_id, adapter_id=adapter_id
    )
    if dict(retry) != expected_retry or dict(breaker) != expected_breaker:
        raise SourceContractError(
            "source outcome recovery decisions are not deterministic"
        )

    evidence_tier = _enum(
        acquisition.get("evidence_tier"), "acquisition.evidence_tier", EVIDENCE_TIERS
    )
    payload_shape = _enum(
        acquisition.get("payload_shape"), "acquisition.payload_shape", PAYLOAD_SHAPES
    )
    content_card_count = _bounded_integer(
        acquisition.get("content_card_count"),
        "acquisition.content_card_count",
        0,
        100_000,
    )
    expected_status = _derived_source_status(
        result_state, evidence_tier, payload_shape
    )
    if outcome.get("source_status") != expected_status:
        raise SourceContractError("source outcome source status is not deterministic")
    expected_eligibility = _derived_eligibility(
        expected_status, expected_qualification
    )
    if outcome.get("eligibility") != expected_eligibility:
        raise SourceContractError("source outcome semantic eligibility is invalid")
    if outcome.get("may_enter_time_bounded_ranking") != (
        expected_eligibility == "eligible_for_review"
    ):
        raise SourceContractError("source outcome semantic strict-rank flag is invalid")
    expected_general_review = expected_eligibility in {
        "eligible_for_review",
        "isolated_unknown_date",
        "inferred_date_review_only",
    }
    if outcome.get("may_enter_general_review") != expected_general_review:
        raise SourceContractError("source outcome semantic review flag is invalid")
    expected_discovery_count = (
        content_card_count
        if result_state == "success" and payload_shape == "content_cards"
        else 0
    )
    if outcome.get("discoveries_allowed") != (expected_discovery_count > 0) or outcome.get(
        "discovery_count"
    ) != expected_discovery_count:
        raise SourceContractError(
            "source outcome payload shape cannot produce discoveries deterministically"
        )


def _checkpoint_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": payload["run_id"],
        "topic": payload["topic"],
        "platform_id": payload["platform_id"],
        "stage": payload["stage"],
        "exact_probe_or_command": payload["exact_probe_or_command"],
        "tool_readiness": payload["tool_readiness"],
        "bridge_state": payload["bridge_state"],
        "auth_state": payload["auth_state"],
        "quota_state": payload["quota_state"],
        "authorization": payload["authorization"],
        "probe_result": payload["probe_result"],
        "error_summary": payload["error_summary"],
        "initial_query_ids": sorted(
            set(payload["completed_query_ids"]) | set(payload["pending_query_ids"])
        ),
        "artifact_paths": payload["artifact_paths"],
        "next_safe_command": payload["next_safe_command"],
        "ttl_seconds": payload["ttl_seconds"],
    }


def _validated_checkpoint_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise SourceContractError("checkpoint input must be a JSON object")
    unexpected = set(payload) - CHECKPOINT_INPUT_FIELDS
    missing = CHECKPOINT_INPUT_FIELDS - set(payload)
    if unexpected:
        raise SourceContractError(f"checkpoint input has unexpected fields: {', '.join(sorted(unexpected))}")
    if missing:
        raise SourceContractError(f"checkpoint input is missing fields: {', '.join(sorted(missing))}")
    platform = _enum(payload.get("platform_id"), "platform_id", CANONICAL_PLATFORMS)
    stage = _enum(payload.get("stage"), "stage", STAGES)
    completed = _sorted_identifiers(payload.get("completed_query_ids"), "completed_query_ids")
    pending = _sorted_identifiers(payload.get("pending_query_ids"), "pending_query_ids")
    if set(completed) & set(pending):
        raise SourceContractError("completed and pending query IDs must be disjoint")
    if not pending:
        raise SourceContractError("checkpoint must contain pending query IDs")
    paths = payload.get("artifact_paths")
    required_paths = {"manifest", "queries", "sources", "candidates"}
    if not isinstance(paths, Mapping) or set(paths) != required_paths:
        raise SourceContractError("artifact_paths must bind manifest, queries, sources, and candidates")
    normalized_paths = {
        key: _safe_relative_path(paths[key], f"artifact_paths.{key}")
        for key in sorted(required_paths)
    }
    run_id = _identifier(payload.get("run_id"), "run_id")
    if any(run_id not in PurePosixPath(path).parts for path in normalized_paths.values()):
        raise SourceContractError("artifact_paths must point to the same run_id")
    ttl_seconds = _bounded_integer(payload.get("ttl_seconds"), "ttl_seconds", 60, 604_800)
    return {
        "run_id": run_id,
        "topic": _text(payload.get("topic"), "topic", maximum=500),
        "platform_id": platform,
        "stage": stage,
        "exact_probe_or_command": _command(
            payload.get("exact_probe_or_command"), "exact_probe_or_command"
        ),
        "tool_readiness": _enum(
            payload.get("tool_readiness"),
            "tool_readiness",
            {"available", "configured", "unavailable", "unknown"},
        ),
        "bridge_state": _enum(
            payload.get("bridge_state"),
            "bridge_state",
            {"connected", "disconnected", "not_required", "unknown"},
        ),
        "auth_state": _enum(
            payload.get("auth_state"),
            "auth_state",
            {"authenticated", "anonymous", "expired", "required", "unknown"},
        ),
        "quota_state": _enum(
            payload.get("quota_state"),
            "quota_state",
            {"available", "rate_limited", "exhausted", "not_applicable", "unknown"},
        ),
        "authorization": _enum(payload.get("authorization"), "authorization", AUTHORIZATIONS),
        "probe_result": _enum(
            payload.get("probe_result"),
            "probe_result",
            {"success", "empty", "blocked", "error"},
        ),
        "error_summary": _text(payload.get("error_summary"), "error_summary", maximum=2_000),
        "completed_query_ids": completed,
        "pending_query_ids": pending,
        "candidate_ids": _sorted_identifiers(payload.get("candidate_ids"), "candidate_ids"),
        "artifact_paths": normalized_paths,
        "next_safe_command": _command(payload.get("next_safe_command"), "next_safe_command"),
        "ttl_seconds": ttl_seconds,
    }


def create_checkpoint(
    payload: Any, *, now: datetime | None = None, _validate: bool = True
) -> dict[str, Any]:
    normalized = _validated_checkpoint_input(payload)
    now_value = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    identity = _checkpoint_identity(normalized)
    checkpoint: dict[str, Any] = {
        "schema": CHECKPOINT_SCHEMA,
        **normalized,
        "checkpoint_id": _value_digest(
            [normalized["run_id"], normalized["platform_id"], normalized["stage"]]
        ),
        "idempotency_key": _value_digest(identity),
        "created_at": _timestamp(now_value),
        "updated_at": _timestamp(now_value),
        "expires_at": _timestamp(now_value + timedelta(seconds=normalized["ttl_seconds"])),
        "status": "paused",
        "resume_count": 0,
        "error_history": [normalized["error_summary"]],
    }
    checkpoint["checkpoint_digest_sha256"] = _digest(checkpoint)
    if _validate:
        validate_checkpoint(checkpoint)
    return checkpoint


def validate_checkpoint(checkpoint: Any) -> None:
    if not isinstance(checkpoint, Mapping):
        raise SourceContractError(
            f"checkpoint schema must be {CHECKPOINT_SCHEMA}; expected a JSON object"
        )
    unexpected = set(checkpoint) - CHECKPOINT_FIELDS
    missing = CHECKPOINT_FIELDS - set(checkpoint)
    if unexpected or missing:
        details = unexpected if unexpected else missing
        kind = "unexpected" if unexpected else "missing"
        raise SourceContractError(
            f"checkpoint has {kind} fields: {', '.join(sorted(details))}"
        )
    if checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise SourceContractError(f"checkpoint schema must be {CHECKPOINT_SCHEMA}")
    digest = checkpoint.get("checkpoint_digest_sha256")
    if not isinstance(digest, str) or digest != _digest(
        checkpoint, omit=("checkpoint_digest_sha256",)
    ):
        raise SourceContractError("checkpoint digest does not match its contents")
    created = _parse_timestamp(checkpoint.get("created_at"), "created_at")
    updated = _parse_timestamp(checkpoint.get("updated_at"), "updated_at")
    expires = _parse_timestamp(checkpoint.get("expires_at"), "expires_at")
    if not created <= updated < expires:
        raise SourceContractError("checkpoint timestamps are inconsistent")
    ttl_seconds = _bounded_integer(
        checkpoint.get("ttl_seconds"), "ttl_seconds", 60, 604_800
    )
    if expires != created + timedelta(seconds=ttl_seconds):
        raise SourceContractError("checkpoint expiry is not derived from ttl_seconds")
    completed = _sorted_identifiers(checkpoint.get("completed_query_ids"), "completed_query_ids")
    pending = _sorted_identifiers(checkpoint.get("pending_query_ids"), "pending_query_ids")
    candidates = _sorted_identifiers(checkpoint.get("candidate_ids"), "candidate_ids")
    if (
        completed != checkpoint.get("completed_query_ids")
        or pending != checkpoint.get("pending_query_ids")
        or candidates != checkpoint.get("candidate_ids")
    ):
        raise SourceContractError("checkpoint query IDs must be sorted and unique")
    if set(completed) & set(pending):
        raise SourceContractError("completed and pending checkpoint query IDs overlap")
    status = _enum(
        checkpoint.get("status"), "checkpoint status", {"paused", "resuming", "complete"}
    )
    if (not pending) != (status == "complete"):
        raise SourceContractError("checkpoint complete status does not match pending work")
    resume_count = checkpoint.get("resume_count")
    if isinstance(resume_count, bool) or not isinstance(resume_count, int) or resume_count < 0:
        raise SourceContractError("checkpoint resume_count must be a non-negative integer")
    history = checkpoint.get("error_history")
    if not isinstance(history, list) or not history:
        raise SourceContractError("checkpoint error_history must be a non-empty array")
    normalized_history = [
        _text(item, "error_history", maximum=2_000) for item in history
    ]
    if normalized_history[0] != checkpoint.get("error_summary"):
        raise SourceContractError("checkpoint error history must retain the pause error")
    expected_checkpoint_id = _value_digest(
        [checkpoint.get("run_id"), checkpoint.get("platform_id"), checkpoint.get("stage")]
    )
    if checkpoint.get("checkpoint_id") != expected_checkpoint_id:
        raise SourceContractError("checkpoint ID does not match its identity")
    if checkpoint.get("idempotency_key") != _value_digest(_checkpoint_identity(checkpoint)):
        raise SourceContractError("checkpoint idempotency key does not match its pause state")


def resume_checkpoint(
    checkpoint: Any, *, probe: Any, now: datetime | None = None
) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    if checkpoint.get("status") == "complete" or not checkpoint.get("pending_query_ids"):
        raise SourceContractError("checkpoint is complete and has no pending work")
    now_value = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if now_value >= _parse_timestamp(checkpoint.get("expires_at"), "expires_at"):
        raise SourceContractError("checkpoint has expired and requires a new pause state")
    if not isinstance(probe, Mapping) or set(probe) != {
        "observed_at",
        "result",
        "equivalent_command",
    }:
        raise SourceContractError("resume requires a fresh probe with equivalent command evidence")
    observed_at = _parse_timestamp(probe.get("observed_at"), "probe.observed_at")
    if observed_at <= _parse_timestamp(checkpoint.get("updated_at"), "updated_at"):
        raise SourceContractError("resume requires a fresh probe after the checkpoint update")
    if observed_at > now_value + timedelta(minutes=5):
        raise SourceContractError("probe observation cannot be in the future")
    if probe.get("result") != "success":
        raise SourceContractError("fresh probe did not succeed")
    equivalent = _command(probe.get("equivalent_command"), "probe.equivalent_command")
    if equivalent != checkpoint.get("next_safe_command"):
        raise SourceContractError("fresh probe is not equivalent to next_safe_command")
    return {
        "schema": RESUME_SCHEMA,
        "checkpoint_id": checkpoint["checkpoint_id"],
        "run_id": checkpoint["run_id"],
        "platform_id": checkpoint["platform_id"],
        "status": "resuming",
        "resumed_at": _timestamp(now_value),
        "resume_count": int(checkpoint.get("resume_count", 0)) + 1,
        "completed_query_ids": list(checkpoint["completed_query_ids"]),
        "query_ids_to_execute": list(checkpoint["pending_query_ids"]),
        "probe": {
            "observed_at": _timestamp(observed_at),
            "result": "success",
            "equivalent_command": equivalent,
        },
    }


def checkpoint_after_resume(
    checkpoint: Mapping[str, Any], *, receipt: Mapping[str, Any]
) -> dict[str, Any]:
    advanced = dict(checkpoint)
    advanced["status"] = "resuming"
    advanced["resume_count"] = receipt["resume_count"]
    advanced["updated_at"] = receipt["resumed_at"]
    advanced["checkpoint_digest_sha256"] = _digest(
        advanced, omit=("checkpoint_digest_sha256",)
    )
    validate_checkpoint(advanced)
    return advanced


def advance_checkpoint(
    checkpoint: Any,
    *,
    completed_query_ids: Sequence[str],
    candidate_ids: Sequence[str] = (),
    error_summary: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    validate_checkpoint(checkpoint)
    now_value = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if now_value >= _parse_timestamp(checkpoint.get("expires_at"), "expires_at"):
        raise SourceContractError("checkpoint has expired")
    completed_now = _sorted_identifiers(list(completed_query_ids), "completed_query_ids")
    pending = set(checkpoint["pending_query_ids"])
    if not completed_now or not set(completed_now).issubset(pending):
        raise SourceContractError("only pending query IDs may be completed")
    errors = list(checkpoint.get("error_history", []))
    if error_summary is not None:
        errors.append(_text(error_summary, "error_summary", maximum=2_000))
    advanced = dict(checkpoint)
    advanced["completed_query_ids"] = sorted(
        set(checkpoint["completed_query_ids"]) | set(completed_now)
    )
    advanced["pending_query_ids"] = sorted(pending - set(completed_now))
    advanced["candidate_ids"] = sorted(
        set(checkpoint["candidate_ids"])
        | set(_sorted_identifiers(list(candidate_ids), "candidate_ids"))
    )
    advanced["updated_at"] = _timestamp(now_value)
    advanced["status"] = "complete" if not advanced["pending_query_ids"] else "paused"
    advanced["error_history"] = errors
    advanced["checkpoint_digest_sha256"] = _digest(
        advanced, omit=("checkpoint_digest_sha256",)
    )
    # The idempotency key intentionally identifies the original pause request;
    # advancing work does not create a second logical checkpoint.
    validate_checkpoint_progress(advanced, original_key=str(checkpoint["idempotency_key"]))
    return advanced


def validate_checkpoint_progress(checkpoint: Any, *, original_key: str) -> None:
    validate_checkpoint(checkpoint)
    if checkpoint.get("idempotency_key") != original_key:
        raise SourceContractError("advanced checkpoint changed idempotency identity")


def write_checkpoint_atomic(path: Path, checkpoint: Mapping[str, Any]) -> None:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SourceContractError(f"existing checkpoint is unreadable: {path}") from exc
        if existing == checkpoint:
            return
        validate_checkpoint(existing)
        validate_checkpoint(checkpoint)
        same_identity = (
            existing.get("checkpoint_id") == checkpoint.get("checkpoint_id")
            and existing.get("idempotency_key") == checkpoint.get("idempotency_key")
            and existing.get("created_at") == checkpoint.get("created_at")
            and existing.get("expires_at") == checkpoint.get("expires_at")
        )
        monotonic = (
            set(existing.get("completed_query_ids", []))
            <= set(checkpoint.get("completed_query_ids", []))
            and set(checkpoint.get("pending_query_ids", []))
            <= set(existing.get("pending_query_ids", []))
            and set(existing.get("candidate_ids", []))
            <= set(checkpoint.get("candidate_ids", []))
            and _parse_timestamp(checkpoint.get("updated_at"), "updated_at")
            >= _parse_timestamp(existing.get("updated_at"), "updated_at")
            and int(checkpoint.get("resume_count", -1))
            >= int(existing.get("resume_count", 0))
        )
        if not same_identity:
            raise SourceContractError(f"refusing to replace a different checkpoint: {path}")
        if not monotonic:
            raise SourceContractError(f"refusing checkpoint rollback: {path}")
        existing_history = existing.get("error_history", [])
        replacement_history = checkpoint.get("error_history", [])
        if replacement_history[: len(existing_history)] != existing_history:
            raise SourceContractError(
                f"refusing checkpoint error history loss: {path}"
            )
        _write_json_replace(path, checkpoint)
        return
    _write_json_new(path, checkpoint)


def _write_json_replace(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _write_json_new(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists():
        raise SourceContractError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    outcome_parser = subparsers.add_parser(
        "normalize-outcome", help="normalize one source observation"
    )
    outcome_parser.add_argument("--input", type=Path, required=True)
    outcome_parser.add_argument("--output", type=Path, required=True)
    checkpoint_parser = subparsers.add_parser(
        "create-checkpoint", help="create a resumable checkpoint"
    )
    checkpoint_parser.add_argument("--input", type=Path, required=True)
    checkpoint_parser.add_argument("--output", type=Path, required=True)
    resume_parser = subparsers.add_parser(
        "resume-checkpoint", help="validate a fresh probe and resume a checkpoint"
    )
    resume_parser.add_argument("--checkpoint", type=Path, required=True)
    resume_parser.add_argument("--probe", type=Path, required=True)
    advance_parser = subparsers.add_parser(
        "advance-checkpoint", help="record monotonic checkpoint progress"
    )
    advance_parser.add_argument("--checkpoint", type=Path, required=True)
    advance_parser.add_argument("--progress", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "normalize-outcome":
            with args.input.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            output = normalize_source_outcome(payload)
            _write_json_new(args.output, output)
        elif args.command == "create-checkpoint":
            with args.input.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            output = create_checkpoint(payload)
            write_checkpoint_atomic(args.output, output)
        elif args.command == "resume-checkpoint":
            with args.checkpoint.open("r", encoding="utf-8") as handle:
                checkpoint = json.load(handle)
            with args.probe.open("r", encoding="utf-8") as handle:
                probe = json.load(handle)
            output = resume_checkpoint(checkpoint, probe=probe)
            resumed_checkpoint = checkpoint_after_resume(checkpoint, receipt=output)
            write_checkpoint_atomic(args.checkpoint, resumed_checkpoint)
        else:
            with args.checkpoint.open("r", encoding="utf-8") as handle:
                checkpoint = json.load(handle)
            with args.progress.open("r", encoding="utf-8") as handle:
                progress = json.load(handle)
            if not isinstance(progress, Mapping) or set(progress) != {
                "completed_query_ids",
                "candidate_ids",
                "error_summary",
            }:
                raise SourceContractError(
                    "progress must contain exactly completed_query_ids, candidate_ids, and error_summary"
                )
            output = advance_checkpoint(
                checkpoint,
                completed_query_ids=progress["completed_query_ids"],
                candidate_ids=progress["candidate_ids"],
                error_summary=progress["error_summary"],
            )
            write_checkpoint_atomic(args.checkpoint, output)
    except (OSError, json.JSONDecodeError, SourceContractError) as exc:
        print(f"source_contract: {exc}", file=sys.stderr)
        return 2
    if args.command in {"resume-checkpoint", "advance-checkpoint"}:
        if args.command == "resume-checkpoint":
            print(json.dumps(output))
        else:
            print(
                json.dumps(
                    {"status": output["status"], "checkpoint": str(args.checkpoint)}
                )
            )
    else:
        print(json.dumps({"status": "complete", "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
