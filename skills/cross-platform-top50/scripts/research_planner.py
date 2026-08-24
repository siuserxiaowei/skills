#!/usr/bin/env python3
"""Compile a bounded cross-platform query plan with stable ranking semantics.

Search queries are adapter-facing discovery inputs and may contain platform
syntax.  Ranking queries describe user intent without platform-specific terms,
so candidates from different routes can be compared against the same target.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REQUEST_SCHEMA = "top50-research-query-request/v1"
PLAN_SCHEMA = "top50-research-query-plan/v1"
MAX_QUERIES = 500
MAX_ALIASES = 20

RECENT_SOCIAL_MODES = ("auto", "strict", "off")
FUSION_TIME_MODE_BY_RECENT_SOCIAL_MODE = {
    "auto": "advisory",
    "strict": "strict",
    "off": "unbounded",
}

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
CANONICAL_INDEX = {name: index for index, name in enumerate(CANONICAL_PLATFORMS)}
LANGUAGE_ORDER = ("zh", "en")
INTENT_ORDER = (
    "exact",
    "tutorial",
    "practice",
    "review",
    "case_study",
    "controversy",
    "failure",
    "primary_source",
)
ROUTE_KIND_ORDER = (
    "platform_api",
    "platform_cli",
    "authorized_browser",
    "public_discovery",
)
DEFAULT_ROUTE_KINDS = {
    "csdn": ("platform_cli", "authorized_browser", "public_discovery"),
    "wechat_official_accounts": ("authorized_browser", "public_discovery"),
    "zhihu": ("platform_api", "authorized_browser", "public_discovery"),
    "xiaohongshu": ("platform_api", "authorized_browser", "public_discovery"),
    "weibo": ("platform_api", "authorized_browser", "public_discovery"),
    "douyin": ("platform_api", "authorized_browser", "public_discovery"),
    "x": ("platform_cli", "authorized_browser", "public_discovery"),
    "bilibili": ("platform_api", "platform_cli", "public_discovery"),
    "juejin": ("platform_cli", "authorized_browser", "public_discovery"),
    "youtube": ("platform_cli", "authorized_browser", "public_discovery"),
    "linuxdo": ("platform_cli", "authorized_browser", "public_discovery"),
    "github": ("platform_cli", "public_discovery"),
}

CHINA_TIME_PLATFORMS = {
    "csdn",
    "wechat_official_accounts",
    "zhihu",
    "xiaohongshu",
    "weibo",
    "douyin",
    "bilibili",
    "juejin",
    "linuxdo",
    "baidu_search",
    "toutiao",
    "36kr",
    "infoq",
    "segmentfault",
    "oschina",
    "v2ex",
    "kuaishou",
    "wechat_channels",
}

PLATFORM_EXPANSIONS = {
    "csdn": ("site:blog.csdn.net", "CSDN"),
    "wechat_official_accounts": ("site:mp.weixin.qq.com", "公众号"),
    "zhihu": ("site:zhihu.com", "知乎"),
    "xiaohongshu": ("小红书",),
    "weibo": ("site:weibo.com", "微博"),
    "douyin": ("site:douyin.com", "抖音"),
    "x": ("site:x.com",),
    "bilibili": ("site:bilibili.com", "B站"),
    "juejin": ("site:juejin.cn", "掘金"),
    "youtube": ("site:youtube.com",),
    "linuxdo": ("site:linux.do",),
    "github": ("site:github.com",),
    "baidu_search": ("百度",),
    "google_search": (),
    "bing_search": ("Bing",),
    "toutiao": ("site:toutiao.com", "今日头条"),
    "36kr": ("site:36kr.com",),
    "infoq": ("site:infoq.cn",),
    "segmentfault": ("site:segmentfault.com",),
    "oschina": ("site:oschina.net",),
    "v2ex": ("site:v2ex.com",),
    "reddit": ("site:reddit.com",),
    "hacker_news": ("site:news.ycombinator.com",),
    "medium": ("site:medium.com",),
    "linkedin": ("site:linkedin.com",),
    "kuaishou": ("site:kuaishou.com", "快手"),
    "wechat_channels": ("视频号",),
    "tiktok": ("site:tiktok.com",),
}

for _platform_id in CANONICAL_PLATFORMS:
    DEFAULT_ROUTE_KINDS.setdefault(
        _platform_id, ("authorized_browser", "public_discovery")
    )

INTENT_EXPANSIONS = {
    "zh": {
        "exact": (),
        "tutorial": ("教程", "指南"),
        "practice": ("实战", "实践"),
        "review": ("评测", "对比"),
        "case_study": ("案例", "复盘"),
        "controversy": ("争议", "反例"),
        "failure": ("失败", "踩坑"),
        "primary_source": ("官方", "源码"),
    },
    "en": {
        "exact": (),
        "tutorial": ("tutorial", "guide"),
        "practice": ("implementation", "best practices"),
        "review": ("review", "comparison"),
        "case_study": ("case study", "retrospective"),
        "controversy": ("criticism", "counterexample"),
        "failure": ("failure", "pitfalls"),
        "primary_source": ("official", "source code"),
    },
}

PLACEHOLDERS = {
    "《》",
    "《主题》",
    "《真实主题》",
    "{{topic}}",
    "<主题>",
    "请填写主题",
}
ROOT_FIELDS = {
    "schema",
    "run_id",
    "topic",
    "purpose",
    "platforms",
    "aliases",
    "languages",
    "intents",
    "timeframe",
    "recent_social_mode",
    "tokenizer_mode",
    "max_queries",
}
REQUIRED_ROOT_FIELDS = ROOT_FIELDS - {
    "aliases",
    "max_queries",
    "recent_social_mode",
}


class QueryPlanError(ValueError):
    """The query request or compiled plan is unsafe or internally inconsistent."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _digest(value: Mapping[str, Any], *, omit: Sequence[str] = ()) -> str:
    payload = {key: item for key, item in value.items() if key not in set(omit)}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{hashlib.sha256(_canonical_bytes(parts)).hexdigest()[:24]}"


def _normalized_text(value: Any, field: str, *, maximum: int = 500) -> str:
    if not isinstance(value, str):
        raise QueryPlanError(f"{field} must be a string")
    text = unicodedata.normalize("NFC", value).strip()
    if not text or len(text) > maximum:
        raise QueryPlanError(f"{field} must contain 1-{maximum} characters")
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        raise QueryPlanError(f"{field} must not contain control characters")
    return text


def _topic(value: Any) -> str:
    topic = _normalized_text(value, "topic")
    if topic.casefold() in PLACEHOLDERS or not any(character.isalnum() for character in topic):
        raise QueryPlanError("topic is an unfilled placeholder")
    return topic


def _safe_identifier(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or value in {".", ".."}
        or re.fullmatch(r"[A-Za-z0-9._-]+", value) is None
    ):
        raise QueryPlanError(f"{field} must be a safe 1-128 character identifier")
    return value


def _unique_texts(values: Any, field: str, *, maximum_items: int) -> list[str]:
    if not isinstance(values, list) or len(values) > maximum_items:
        raise QueryPlanError(f"{field} must be an array with at most {maximum_items} items")
    normalized: dict[str, str] = {}
    for value in values:
        text = _normalized_text(value, field, maximum=200)
        normalized.setdefault(text.casefold(), text)
    return sorted(normalized.values(), key=lambda item: (item.casefold(), item))


def _load_jieba() -> Any | None:
    try:
        return importlib.import_module("jieba")
    except (ImportError, ModuleNotFoundError):
        return None


def _cjk_bigrams(text: str) -> list[str]:
    runs = re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", text)
    result: list[str] = []
    for run in runs:
        if len(run) == 1:
            result.append(run)
        else:
            result.extend(run[index : index + 2] for index in range(len(run) - 1))
    return result


def _latin_tokens(text: str) -> list[str]:
    return [
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*", text)
    ]


def _unique_in_order(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def tokenize_for_ranking(text: str, *, mode: str) -> tuple[list[str], str]:
    normalized = _normalized_text(text, "ranking text", maximum=2_000)
    if mode not in {"cjk_bigram", "jieba"}:
        raise QueryPlanError("tokenizer_mode must be cjk_bigram or jieba")
    if mode == "jieba":
        jieba = _load_jieba()
        if jieba is not None:
            tokens = [str(token).strip().casefold() for token in jieba.lcut(normalized)]
            return _unique_in_order(tokens), "jieba"
        actual = "cjk_bigram_fallback"
    else:
        actual = "cjk_bigram"
    return _unique_in_order(_cjk_bigrams(normalized) + _latin_tokens(normalized)), actual


def _validated_timeframe(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"start", "end"}:
        raise QueryPlanError("timeframe must contain exactly start and end")
    try:
        start = date.fromisoformat(str(value["start"]))
        end = date.fromisoformat(str(value["end"]))
    except ValueError as exc:
        raise QueryPlanError("timeframe dates must use YYYY-MM-DD") from exc
    if start > end:
        raise QueryPlanError("timeframe start must not be after end")
    return {"start": start.isoformat(), "end": end.isoformat()}


def _validated_window_timezone(value: Any, platform_id: str) -> str:
    default = "Asia/Shanghai" if platform_id in CHINA_TIME_PLATFORMS else "UTC"
    timezone_name = default if value is None else _normalized_text(
        value, "window_timezone", maximum=128
    )
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise QueryPlanError("window_timezone must be a valid IANA timezone") from exc
    return timezone_name


def _validated_platforms(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise QueryPlanError("platforms must be a non-empty array")
    by_id: dict[str, dict[str, Any]] = {}
    for row in value:
        if not isinstance(row, Mapping) or not {"platform_id", "required"}.issubset(row) or set(row) - {
            "platform_id",
            "required",
            "route_kinds",
            "window_timezone",
        }:
            raise QueryPlanError("platform route fields are invalid")
        platform_id = row.get("platform_id")
        if platform_id not in CANONICAL_INDEX:
            raise QueryPlanError(f"platform is not canonical: {platform_id}")
        if not isinstance(row.get("required"), bool):
            raise QueryPlanError("platform required must be boolean")
        default_routes = DEFAULT_ROUTE_KINDS.get(
            str(platform_id), ("authorized_browser", "public_discovery")
        )
        supplied_routes = row.get("route_kinds", list(default_routes))
        if not isinstance(supplied_routes, list) or not supplied_routes:
            raise QueryPlanError("route_kinds must be a non-empty array")
        if any(route not in ROUTE_KIND_ORDER for route in supplied_routes):
            raise QueryPlanError("route_kinds contains an unknown route")
        if len(set(supplied_routes)) != len(supplied_routes):
            raise QueryPlanError("route_kinds must not contain duplicate routes")
        indexes = [ROUTE_KIND_ORDER.index(route) for route in supplied_routes]
        if indexes != sorted(indexes):
            raise QueryPlanError("route_kinds must follow canonical route order")
        chain = [
            {
                "route_id": f"{platform_id}:{route_kind}",
                "route_kind": route_kind,
                "order": index,
                "status": "planned",
                "requires_probe": True,
                "activation": "probe_then_execute"
                if index == 1
                else "fallback_after_recorded_outcome",
            }
            for index, route_kind in enumerate(supplied_routes, start=1)
        ]
        platform_contract = {
            "platform_id": str(platform_id),
            "required": bool(row["required"]),
            "window_timezone": _validated_window_timezone(
                row.get("window_timezone"), str(platform_id)
            ),
            "query_expansion": list(PLATFORM_EXPANSIONS[str(platform_id)]),
            "adapter_chain": chain,
        }
        if platform_id in by_id and by_id[platform_id] != platform_contract:
            raise QueryPlanError(f"platform {platform_id} has conflicting declarations")
        by_id[str(platform_id)] = platform_contract
    return sorted(by_id.values(), key=lambda row: CANONICAL_INDEX[row["platform_id"]])


def _ordered_enum_list(value: Any, field: str, order: Sequence[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        raise QueryPlanError(f"{field} must be a non-empty array")
    if any(item not in order for item in value):
        raise QueryPlanError(f"{field[:-1] if field.endswith('s') else field} is not supported")
    return [item for item in order if item in set(value)]


def _search_query(
    topic: str,
    aliases: Sequence[str],
    intent_expansion: Sequence[str],
    platform_expansion: Sequence[str],
) -> str:
    entity = " OR ".join(f'"{value}"' for value in [topic, *aliases])
    parts = [f"({entity})"]
    if intent_expansion:
        parts.append(f"({' OR '.join(intent_expansion)})")
    parts.extend(platform_expansion)
    return " ".join(parts)


def _ranking_query(
    topic: str, purpose: str, aliases: Sequence[str], intent_expansion: Sequence[str]
) -> str:
    parts = [topic]
    parts.extend(aliases)
    parts.extend(intent_expansion)
    parts.append(purpose)
    return " ".join(_unique_in_order(parts))


def _validated_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise QueryPlanError("request must be a JSON object")
    unexpected = set(payload) - ROOT_FIELDS
    missing = REQUIRED_ROOT_FIELDS - set(payload)
    if unexpected:
        raise QueryPlanError(f"request has unexpected fields: {', '.join(sorted(unexpected))}")
    if missing:
        raise QueryPlanError(f"request is missing fields: {', '.join(sorted(missing))}")
    if payload.get("schema") != REQUEST_SCHEMA:
        raise QueryPlanError(f"schema must be {REQUEST_SCHEMA}")
    aliases = _unique_texts(payload.get("aliases", []), "aliases", maximum_items=MAX_ALIASES)
    topic = _topic(payload.get("topic"))
    aliases = [alias for alias in aliases if alias.casefold() != topic.casefold()]
    max_queries = payload.get("max_queries", MAX_QUERIES)
    if isinstance(max_queries, bool) or not isinstance(max_queries, int) or not 1 <= max_queries <= MAX_QUERIES:
        raise QueryPlanError(f"max_queries must be an integer from 1 to {MAX_QUERIES}")
    tokenizer_mode = payload.get("tokenizer_mode")
    if tokenizer_mode not in {"cjk_bigram", "jieba"}:
        raise QueryPlanError("tokenizer_mode must be cjk_bigram or jieba")
    recent_social_mode = payload.get("recent_social_mode", "auto")
    if recent_social_mode not in RECENT_SOCIAL_MODES:
        raise QueryPlanError(
            "recent_social_mode must be auto, strict, or off"
        )
    return {
        "run_id": _safe_identifier(payload.get("run_id"), "run_id"),
        "topic": topic,
        "purpose": _normalized_text(payload.get("purpose"), "purpose"),
        "platforms": _validated_platforms(payload.get("platforms")),
        "aliases": aliases,
        "languages": _ordered_enum_list(payload.get("languages"), "languages", LANGUAGE_ORDER),
        "intents": _ordered_enum_list(payload.get("intents"), "intents", INTENT_ORDER),
        "timeframe": _validated_timeframe(payload.get("timeframe")),
        "recent_social_mode": recent_social_mode,
        "tokenizer_mode": tokenizer_mode,
        "max_queries": max_queries,
    }


def compile_query_plan(payload: Any, *, _validate: bool = True) -> dict[str, Any]:
    request = _validated_request(payload)
    count = len(request["platforms"]) * len(request["languages"]) * len(request["intents"])
    if count > request["max_queries"]:
        raise QueryPlanError(
            f"query count {count} exceeds the bounded maximum {request['max_queries']}"
        )
    queries: list[dict[str, Any]] = []
    for platform in request["platforms"]:
        for language in request["languages"]:
            for intent in request["intents"]:
                intent_expansion = list(INTENT_EXPANSIONS[language][intent])
                ranking_query = _ranking_query(
                    request["topic"], request["purpose"], request["aliases"], intent_expansion
                )
                tokens, tokenizer = tokenize_for_ranking(
                    ranking_query, mode=request["tokenizer_mode"]
                )
                query_identity = (
                    request["run_id"],
                    platform["platform_id"],
                    language,
                    intent,
                    request["topic"],
                    request["aliases"],
                    request["timeframe"],
                    platform["window_timezone"],
                )
                queries.append(
                    {
                        "query_id": _stable_id("query", *query_identity),
                        "platform_id": platform["platform_id"],
                        "required": platform["required"],
                        "language": language,
                        "intent": intent,
                        "search_query": _search_query(
                            request["topic"],
                            request["aliases"],
                            intent_expansion,
                            platform["query_expansion"],
                        ),
                        "ranking_query": ranking_query,
                        "platform_expansion": platform["query_expansion"],
                        "intent_expansion": intent_expansion,
                        "ranking_tokens": tokens,
                        "ranking_tokenizer": tokenizer,
                        "date_filter": request["timeframe"],
                        "window_timezone": platform["window_timezone"],
                        "unknown_date_policy": "isolate",
                        "route_plan": [
                            route["route_id"] for route in platform["adapter_chain"]
                        ],
                        "route_plan_status": "not_started",
                        "status": "pending",
                    }
                )
    identity = {
        "run_id": request["run_id"],
        "topic": request["topic"],
        "purpose": request["purpose"],
        "platforms": request["platforms"],
        "aliases": request["aliases"],
        "languages": request["languages"],
        "intents": request["intents"],
        "timeframe": request["timeframe"],
        "recent_social_mode": request["recent_social_mode"],
        "tokenizer_mode": request["tokenizer_mode"],
    }
    plan: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        **identity,
        "date_policy": "isolate_unknown",
        "fusion_time_policy": {
            "mode": FUSION_TIME_MODE_BY_RECENT_SOCIAL_MODE[
                request["recent_social_mode"]
            ],
            "from_date": request["timeframe"]["start"],
            "to_date": request["timeframe"]["end"],
        },
        "idempotency_key": _digest(identity),
        "counts": {"platforms": len(request["platforms"]), "queries": len(queries)},
        "queries": queries,
    }
    plan["plan_digest_sha256"] = _digest(plan)
    if _validate:
        validate_query_plan(plan)
    return plan


def validate_query_plan(plan: Any) -> None:
    if not isinstance(plan, Mapping):
        raise QueryPlanError("plan must be a JSON object")
    if plan.get("schema") != PLAN_SCHEMA:
        raise QueryPlanError(f"plan schema must be {PLAN_SCHEMA}")
    digest = plan.get("plan_digest_sha256")
    if not isinstance(digest, str) or digest != _digest(plan, omit=("plan_digest_sha256",)):
        raise QueryPlanError("plan digest does not match its contents")
    request = {
        "schema": REQUEST_SCHEMA,
        "run_id": plan.get("run_id"),
        "topic": plan.get("topic"),
        "purpose": plan.get("purpose"),
        "platforms": [
            {
                "platform_id": row.get("platform_id"),
                "required": row.get("required"),
                "route_kinds": [
                    route.get("route_kind")
                    for route in row.get("adapter_chain", [])
                    if isinstance(route, Mapping)
                ],
                "window_timezone": row.get("window_timezone"),
            }
            for row in plan.get("platforms", [])
            if isinstance(row, Mapping)
        ],
        "aliases": plan.get("aliases"),
        "languages": plan.get("languages"),
        "intents": plan.get("intents"),
        "timeframe": plan.get("timeframe"),
        "recent_social_mode": plan.get("recent_social_mode"),
        "tokenizer_mode": plan.get("tokenizer_mode"),
    }
    expected = compile_query_plan(request, _validate=False)
    if expected != plan:
        raise QueryPlanError("plan does not match the deterministic query contract")


def _write_json_new(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists():
        raise QueryPlanError(f"output already exists: {path}")
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
    compile_parser = subparsers.add_parser("compile", help="compile a query plan")
    compile_parser.add_argument("--input", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with args.input.open("r", encoding="utf-8") as handle:
            request = json.load(handle)
        plan = compile_query_plan(request)
        _write_json_new(args.output, plan)
    except (OSError, json.JSONDecodeError, QueryPlanError) as exc:
        print(f"research_planner: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "complete", "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
