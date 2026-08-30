#!/usr/bin/env python3
"""Validate a lark-cli operation plan without executing it."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SKILLS = {
    "lark-approval", "lark-apps", "lark-attendance", "lark-base",
    "lark-calendar", "lark-contact", "lark-doc", "lark-drive",
    "lark-event", "lark-im", "lark-mail", "lark-markdown",
    "lark-minutes", "lark-note", "lark-okr", "lark-openapi-explorer",
    "lark-shared", "lark-sheets", "lark-skill-maker", "lark-slides",
    "lark-task", "lark-vc", "lark-vc-agent", "lark-whiteboard",
    "lark-wiki", "lark-workflow-meeting-summary",
    "lark-workflow-standup-report",
}
RISKS = {"read", "write", "high-risk-write"}
CORE_COMMANDS = {"--version", "auth", "config", "doctor", "help", "profile", "schema", "skills", "update", "whoami"}
SHELLS = {"bash", "cmd", "cmd.exe", "fish", "powershell", "pwsh", "sh", "zsh"}
SECRET_FLAGS = {
    "--access-token", "--app-secret", "--client-secret", "--device-code",
    "--tenant-access-token", "--token", "--webhook-secret",
}
PATH_FLAGS = {
    "--file", "--input", "--output", "--output-dir", "--patch-file",
    "--source", "--target",
}


def finding(code: str, message: str, field: str = "") -> dict[str, str]:
    item = {"code": code, "message": message}
    if field:
        item["field"] = field
    return item


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_relative_path(raw: str) -> bool:
    if not raw or raw == "-":
        return True
    if raw.startswith("@"):
        raw = raw[1:]
    if raw.startswith("~") or os.path.isabs(raw):
        return False
    normalized = raw.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    return ".." not in parts


def _has_flag(argv: list[str], flag: str) -> bool:
    return any(part == flag or part.startswith(flag + "=") for part in argv)


def _flag_value(argv: list[str], flag: str) -> str | None:
    for index, part in enumerate(argv):
        if part.startswith(flag + "="):
            return part.split("=", 1)[1]
        if part == flag and index + 1 < len(argv):
            return argv[index + 1]
    return None


def validate_plan(plan: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(plan, dict):
        return {
            "ok": False,
            "ready": False,
            "errors": [finding("invalid_plan", "Plan must be a JSON object.")],
            "warnings": [],
        }

    skill = plan.get("skill")
    if skill not in SKILLS:
        errors.append(finding("unknown_skill", "skill must name one supported lark Skill.", "skill"))

    argv = plan.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        errors.append(finding("invalid_argv", "argv must be a non-empty array of strings.", "argv"))
        argv = []
    elif Path(argv[0]).name in SHELLS:
        errors.append(finding("shell_wrapper", "Pass lark-cli an argv array directly; shell wrappers are not allowed.", "argv"))
    elif Path(argv[0]).name != "lark-cli":
        errors.append(finding("wrong_executable", "argv[0] must resolve to lark-cli.", "argv"))

    if argv and any(_has_flag(argv, flag) for flag in SECRET_FLAGS):
        errors.append(finding("secret_in_argv", "Secrets and device codes must not be stored in the operation plan.", "argv"))

    for index, item in enumerate(argv):
        path_flag = next((flag for flag in PATH_FLAGS if item == flag or item.startswith(flag + "=")), None)
        if path_flag:
            value = item.split("=", 1)[1] if "=" in item else (argv[index + 1] if index + 1 < len(argv) else "")
            if not _safe_relative_path(value):
                errors.append(finding("unsafe_path", f"{path_flag} must use a cwd-relative path without parent traversal.", "argv"))
        if item.startswith("@") and not _safe_relative_path(item):
            errors.append(finding("unsafe_path", "Input references must stay inside the working directory.", "argv"))

    risk = plan.get("risk")
    if risk not in RISKS:
        errors.append(finding("invalid_risk", "risk must be read, write, or high-risk-write.", "risk"))

    command = argv[1] if len(argv) > 1 else ""
    api_call = bool(command and command not in CORE_COMMANDS)
    profile = plan.get("profile")
    identity = plan.get("identity")
    if api_call and (not isinstance(profile, str) or not profile):
        errors.append(finding("missing_profile", "Business API plans must pin a profile.", "profile"))
    elif api_call:
        argv_profile = _flag_value(argv, "--profile")
        if argv_profile != profile:
            errors.append(finding("profile_mismatch", "argv must pin the same --profile declared by the plan.", "argv"))
    if api_call and identity not in {"user", "bot"}:
        errors.append(finding("missing_identity", "Business API plans must choose user or bot.", "identity"))
    elif api_call:
        argv_identity = _flag_value(argv, "--as")
        if argv_identity != identity:
            errors.append(finding("identity_mismatch", "argv must pin the same --as identity declared by the plan.", "argv"))

    target = _mapping(plan.get("target"))
    authorization = _mapping(plan.get("authorization"))
    verification = _mapping(plan.get("verification"))
    dry_run = _mapping(plan.get("dry_run"))
    is_write = risk in {"write", "high-risk-write"}

    if is_write:
        if not target.get("summary") or target.get("verified") is not True:
            errors.append(finding("unverified_target", "Writes require a human-readable, read-verified target.", "target"))
        if not authorization.get("basis"):
            errors.append(finding("missing_authorization_basis", "Writes require the user-intent basis for this exact effect.", "authorization"))
        if not verification.get("mode") or not verification.get("expected"):
            errors.append(finding("missing_readback", "Writes require a response, readback, or async-terminal verification.", "verification"))

    external_effect = plan.get("external_effect") is True
    if external_effect and authorization.get("explicit") is not True:
        errors.append(finding("external_effect_unconfirmed", "External communication or publication requires explicit authorization.", "authorization.explicit"))

    has_yes = _has_flag(argv, "--yes")
    if has_yes and authorization.get("explicit") is not True:
        errors.append(finding("unguarded_yes", "--yes is allowed only after explicit confirmation.", "argv"))
    if risk == "high-risk-write":
        if authorization.get("explicit") is not True:
            errors.append(finding("high_risk_unconfirmed", "High-risk writes require explicit confirmation.", "authorization.explicit"))
        if not has_yes:
            errors.append(finding("missing_confirmation_flag", "The confirmed high-risk argv must include --yes when the command requires it.", "argv"))
        if dry_run.get("supported") not in {True, False}:
            errors.append(finding("dry_run_unknown", "High-risk plans must state whether the exact command supports dry-run.", "dry_run.supported"))
        elif dry_run.get("supported") is True and (
            dry_run.get("completed") is not True or dry_run.get("matches_intent") is not True
        ):
            errors.append(finding("dry_run_incomplete", "Complete and review the supported dry-run before a high-risk write.", "dry_run"))

    if risk == "read" and has_yes:
        warnings.append(finding("unexpected_yes", "A read plan should not carry --yes.", "argv"))

    if plan.get("destructive") is True and not plan.get("recovery"):
        errors.append(finding("missing_recovery", "Destructive plans must state recovery or explain irreversibility.", "recovery"))

    if plan.get("duplicate_sensitive") is True and not plan.get("duplicate_control"):
        errors.append(finding("missing_duplicate_control", "Duplicate-sensitive actions need an idempotency key or deterministic lookup.", "duplicate_control"))

    if plan.get("time_sensitive") is True:
        zone = plan.get("time_zone")
        if not isinstance(zone, str) or not zone:
            errors.append(finding("missing_time_zone", "Time-sensitive work requires an IANA time zone.", "time_zone"))
        else:
            try:
                ZoneInfo(zone)
            except ZoneInfoNotFoundError:
                errors.append(finding("invalid_time_zone", "time_zone is not available in the IANA database.", "time_zone"))
        time_kind = plan.get("time_kind", "instant")
        if time_kind not in {"instant", "range", "date-only", "all-day"}:
            errors.append(finding("invalid_time_kind", "time_kind must be instant, range, date-only, or all-day.", "time_kind"))
        if time_kind in {"instant", "range"} and plan.get("time_has_offset") is not True:
            errors.append(finding("missing_time_offset", "API timestamps must preserve an explicit offset.", "time_has_offset"))

    pagination = _mapping(plan.get("pagination"))
    if plan.get("complete_result") is True:
        if pagination.get("strategy") not in {"all", "bounded"}:
            errors.append(finding("missing_pagination", "Complete reads need all-pages or an explicit bounded strategy.", "pagination"))
        if pagination.get("strategy") == "bounded" and not isinstance(pagination.get("limit"), int):
            errors.append(finding("missing_page_limit", "Bounded pagination requires an integer limit.", "pagination.limit"))

    if plan.get("untrusted_input") is True and plan.get("treat_as_data") is not True:
        errors.append(finding("untrusted_control", "External content must be marked as data, never instructions.", "treat_as_data"))

    if argv and command == "api" and len(argv) > 3 and ("?" in argv[3] or "#" in argv[3]):
        errors.append(finding("raw_api_path", "Raw API paths must not contain a query string or fragment.", "argv"))

    return {
        "ok": not errors,
        "ready": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "skill": skill,
            "risk": risk,
            "profile": profile,
            "identity": identity,
            "external_effect": external_effect,
        },
    }


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically check one lark-cli operation plan without executing it.")
    parser.add_argument("plan", help="JSON plan path, or - for stdin")
    parser.add_argument("--pretty", action="store_true", help="indent the JSON report")
    args = parser.parse_args()
    try:
        plan = load_json(args.plan)
    except (OSError, json.JSONDecodeError) as exc:
        report = {"ok": False, "ready": False, "errors": [finding("input_error", str(exc))], "warnings": []}
        print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
        return 1
    report = validate_plan(plan)
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
