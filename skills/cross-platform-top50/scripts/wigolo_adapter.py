#!/usr/bin/env python3
"""Fail-closed adapter for a separately installed Wigolo 0.2.x executable."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import math
import os
import platform
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit


PROBE_CONTRACT = "top50-wigolo-probe/v2"
REQUEST_CONTRACT = "top50-wigolo-request/v2"
PLAN_CONTRACT = "top50-wigolo-plan/v2"
RESULT_CONTRACT = "top50-wigolo-result/v3"
ADAPTER_VERSION = "2.1.0"

SUPPORTED_VERSION_MAJOR = 0
SUPPORTED_VERSION_MINOR = 2
ALLOWED_OPERATIONS = ("discovery", "fetch", "cache", "watch")
CAPABILITY_PROBE_ARGS = {
    "discovery": ["search", "--json"],
    "fetch": ["fetch", "--json"],
    "cache": ["cache", "stats", "--json"],
    "watch": ["watch", "list", "--json"],
}
PACKAGE_RUNNERS = {"node", "npx", "npm", "pnpm", "bun", "bunx", "yarn"}
MAX_CAPTURE_CHARS = 100_000
MAX_EXECUTABLE_BYTES = 512 * 1024 * 1024
SCRIPT_SUFFIXES = {".js", ".mjs", ".cjs"}
# Source-frozen release admission.  The audited npm 0.2.1 distribution has no
# native image, so production intentionally starts with no admitted digest.
# A future native release requires a code review that adds its published and
# independently verified SHA-256 here; callers cannot extend this set at run time.
AUDITED_NATIVE_RELEASE_SHA256: frozenset[str] = frozenset()
DEFAULT_PROBE_TIMEOUT = 10.0
MAX_EXECUTION_TIMEOUT = 300.0
MIN_AUTH_KEY_BYTES = 32
MAX_AUTH_KEY_BYTES = 4_096
PLAN_HMAC_CONTEXT = b"cross-platform-top50/wigolo-plan/v2"
RESULT_HMAC_CONTEXT = b"cross-platform-top50/wigolo-result/v3"
_PROCESS_AUTH_KEY = secrets.token_bytes(32)

REQUEST_FIELDS = {
    "contract_version",
    "run_id",
    "enabled",
    "selection_mode",
    "operation",
    "allow_experimental_cjk",
    "timeout_seconds",
    "payload",
}
COMMON_REQUIRED_FIELDS = {
    "contract_version",
    "run_id",
    "selection_mode",
    "operation",
    "allow_experimental_cjk",
    "timeout_seconds",
    "payload",
}
PAYLOAD_FIELDS = {
    "discovery": {
        "query",
        "max_results",
        "from_date",
        "to_date",
        "include_domains",
        "exclude_domains",
    },
    "fetch": {"url", "max_chars", "section"},
    "cache": {"action", "query", "url_pattern", "since", "limit", "max_tokens_out"},
    "watch": {"action"},
}

# Build the child environment from an allowlist. Unknown caller secrets never
# cross the boundary. These values close all audited escalation, auth, hosted,
# proxy, browser, model, and state-mutation paths.
POLICY_ENVIRONMENT = {
    "WIGOLO_HARDCORE": "off",
    "WIGOLO_TLS_TIER": "off",
    "WIGOLO_TLS_DOMAINS": "",
    "WIGOLO_STEALTH": "off",
    "WIGOLO_STEALTH_DRIVER": "playwright",
    "WIGOLO_HUMANIZE": "off",
    "WIGOLO_CDP_DIRECT": "off",
    "WIGOLO_AUTO_PASS": "off",
    "WIGOLO_AI_SOLVE": "off",
    "WIGOLO_HUMAN_SOLVE": "off",
    "WIGOLO_HUMAN_SOLVE_CONSENT": "false",
    "WIGOLO_SOLVER_URL": "",
    "WIGOLO_HOSTED_READER_URL": "",
    "WIGOLO_SCRAPING_BROWSER_WSS": "",
    "WIGOLO_CDP_URL": "",
    "WIGOLO_AUTH_STATE_PATH": "",
    "WIGOLO_CHROME_PROFILE_PATH": "",
    "WIGOLO_PROXY_BYPASS_ON_CHALLENGE": "false",
    "USE_PROXY": "false",
    "PROXY_URL": "",
    "WIGOLO_FETCH_ALLOW_PRIVATE": "false",
    "RESPECT_ROBOTS_TXT": "true",
    "USER_AGENT": "TopFiftyWigoloAdapter/2.1 (+https://github.com/siuserxiaowei/skills)",
    "WIGOLO_SEARCH": "core",
    "WIGOLO_LOCAL_LLM": "off",
    "WIGOLO_LLM_PROVIDER": "",
    "WIGOLO_LLM_API_KEY": "",
    "BRAVE_API_KEY": "",
    "WIGOLO_GITHUB_TOKEN": "",
    "WIGOLO_REDDIT_CLIENT_ID": "",
    "WIGOLO_REDDIT_CLIENT_SECRET": "",
    "SEARCH_PREWARM_BROWSER": "false",
    "WIGOLO_TELEMETRY": "0",
    "WIGOLO_TELEMETRY_ENDPOINT": "",
    "WIGOLO_BROWSER_INSTALL_WAIT_MS": "0",
    "WIGOLO_RERANKER": "none",
    "WIGOLO_CONFIG_PATH": os.devnull,
}
PASSTHROUGH_ENVIRONMENT = {
    "PATH",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
}

Runner = Callable[..., subprocess.CompletedProcess[str]]
_RUNNER: Runner = subprocess.run


class ContractError(ValueError):
    """A request, plan, result, or executable violates the adapter contract."""


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonically serializable: {exc}") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _auth_key_id(key: bytes) -> str:
    return "wigolo-key-" + hashlib.sha256(
        b"cross-platform-top50/wigolo-key-id\0" + key
    ).hexdigest()[:24]


def _hmac_digest(key: bytes, context: bytes, value: Any) -> str:
    return hmac.new(key, context + b"\0" + _canonical_bytes(value), hashlib.sha256).hexdigest()


def _read_auth_key_file(path: str) -> bytes:
    """Read a bounded owner-only key without following the final symlink."""

    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        raise ContractError("auth key file path is invalid")
    candidate = Path(path).expanduser()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(candidate, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ContractError("auth key file must be a regular file")
        if hasattr(os, "geteuid") and before.st_uid != os.geteuid():
            raise ContractError("auth key file must be owned by the current user")
        if stat.S_IMODE(before.st_mode) & 0o077:
            raise ContractError("auth key file permissions must be owner-only (0600 or stricter)")
        if not MIN_AUTH_KEY_BYTES <= before.st_size <= MAX_AUTH_KEY_BYTES:
            raise ContractError(
                f"auth key must contain {MIN_AUTH_KEY_BYTES}..{MAX_AUTH_KEY_BYTES} bytes"
            )
        raw = os.read(descriptor, MAX_AUTH_KEY_BYTES + 1)
        after = os.fstat(descriptor)
        if (
            len(raw) != before.st_size
            or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        ):
            raise ContractError("auth key file changed while reading")
    finally:
        os.close(descriptor)
    return raw


def _resolve_auth_key(auth_key_file: str | None) -> bytes:
    return _PROCESS_AUTH_KEY if auth_key_file is None else _read_auth_key_file(auth_key_file)


def _bounded(value: Any) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= MAX_CAPTURE_CHARS else text[:MAX_CAPTURE_CHARS]


def _diagnostic(code: str, message: str, *, level: str = "error") -> dict[str, str]:
    return {"code": code, "level": level, "message": message}


def _backend(version: str | None = None) -> dict[str, Any]:
    return {
        "id": "wigolo",
        "version": version,
        "license": "AGPL-3.0-only",
        "integration_boundary": "separate_process",
    }


def _safe_backend(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return only the fixed public backend identity, never caller JSON."""

    if not isinstance(value, Mapping) or set(value) != {
        "id",
        "version",
        "license",
        "integration_boundary",
    }:
        return _backend()
    version = value.get("version")
    if version is not None and not isinstance(version, str):
        return _backend()
    if (
        value.get("id") != "wigolo"
        or value.get("license") != "AGPL-3.0-only"
        or value.get("integration_boundary") != "separate_process"
    ):
        return _backend()
    return _backend(version)


def _result(
    *,
    run_id: str,
    operation: str,
    status: str,
    outcome: str,
    diagnostics: list[dict[str, str]],
    backend: Mapping[str, Any] | None = None,
    argv: Sequence[str] = (),
    plan_digest_sha256: str | None = None,
    returncode: int | None = None,
    duration_ms: int = 0,
    data: Any = None,
    auth_key: bytes,
) -> dict[str, Any]:
    value = {
        "contract_version": RESULT_CONTRACT,
        "adapter_version": ADAPTER_VERSION,
        "run_id": str(run_id),
        "operation": str(operation),
        "status": status,
        "outcome": outcome,
        "backend": _safe_backend(backend),
        "argv": list(argv),
        "plan_digest_sha256": plan_digest_sha256,
        "returncode": returncode,
        "duration_ms": max(0, int(duration_ms)),
        "data": data,
        "diagnostics": diagnostics,
    }
    value["auth_key_id"] = _auth_key_id(auth_key)
    value["result_digest_sha256"] = _digest(value)
    value["result_hmac_sha256"] = _hmac_digest(
        auth_key,
        RESULT_HMAC_CONTEXT,
        value,
    )
    return value


def _run(
    runner: Runner,
    argv: list[str],
    *,
    timeout: float,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return runner(
        argv,
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=dict(env),
    )


def safe_environment(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build, rather than inherit, the external process environment."""

    source = os.environ if environ is None else environ
    safe = {
        key: str(source[key])
        for key in PASSTHROUGH_ENVIRONMENT
        if key in source and isinstance(source[key], str)
    }
    safe.update(POLICY_ENVIRONMENT)
    return safe


def _resolve_command(command: str | None) -> tuple[str | None, str | None]:
    raw = (command or "wigolo").strip()
    if not raw or "\x00" in raw:
        return None, "executable_unavailable"
    if Path(raw).name.lower() in PACKAGE_RUNNERS:
        return None, "auto_install_command_forbidden"
    if "/" in raw or "\\" in raw:
        resolved = Path(raw).expanduser().resolve(strict=False)
        if resolved.name.lower() in PACKAGE_RUNNERS:
            return None, "auto_install_command_forbidden"
        return str(resolved), None
    resolved = shutil.which(raw)
    if not resolved:
        return None, "executable_unavailable"
    target = Path(resolved).resolve()
    if target.name.lower() in PACKAGE_RUNNERS:
        return None, "auto_install_command_forbidden"
    return str(target), None


def _supported_version(version: str) -> bool:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?", version)
    return bool(
        match
        and (int(match.group(1)), int(match.group(2)))
        == (SUPPORTED_VERSION_MAJOR, SUPPORTED_VERSION_MINOR)
    )


def _seal_probe(value: dict[str, Any]) -> dict[str, Any]:
    material = dict(value)
    material.pop("probe_id", None)
    material.pop("probe_digest_sha256", None)
    value["probe_id"] = "wigolo-probe-" + _digest(material)[:24]
    value["probe_digest_sha256"] = _digest(value)
    return value


def probe(
    *,
    command: str | None = None,
    runner: Runner | None = None,
    timeout: float = DEFAULT_PROBE_TIMEOUT,
    _binding_sink: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate local dispatch only; do not claim a live route is usable."""

    active_runner = runner or _RUNNER
    started = time.monotonic()
    resolved, resolution_error = _resolve_command(command)
    base: dict[str, Any] = {
        "contract_version": PROBE_CONTRACT,
        "adapter_version": ADAPTER_VERSION,
        "backend": _backend(),
        "command": resolved,
        "ready": False,
        "dispatch_ready": False,
        "live_route_ready": False,
        "readiness_scope": "dispatch_only",
        "status": "unavailable",
        "outcome": resolution_error or "probe_failed",
        "version": None,
        "capabilities": [],
        "checks": [],
        "diagnostics": [],
        "duration_ms": 0,
    }
    if resolution_error:
        base["diagnostics"] = [
            _diagnostic(
                resolution_error,
                "Wigolo must be installed separately; this adapter never installs it.",
            )
        ]
        base["duration_ms"] = round((time.monotonic() - started) * 1000)
        return _seal_probe(base)
    assert resolved is not None

    try:
        with tempfile.TemporaryDirectory(prefix="top50-wigolo-image-") as image_directory:
            source = _resolved_native_source(resolved, allow_command_symlink=True)
            descriptor, metadata = _opened_file(source, executable=True)
            try:
                verified_command, executable_sha256 = _copy_open_native(
                    descriptor,
                    metadata,
                    source,
                    image_directory,
                )
            finally:
                os.close(descriptor)
            if executable_sha256 not in AUDITED_NATIVE_RELEASE_SHA256:
                raise ContractError(
                    "Wigolo native executable SHA-256 is not an audited release"
                )
            if _binding_sink is not None:
                _binding_sink["executable"] = {
                    "path": str(source),
                    "sha256": executable_sha256,
                }
            return _probe_verified_native(
                base=base,
                command=verified_command,
                runner=active_runner,
                timeout=timeout,
                started=started,
            )
    except (OSError, ContractError) as exc:
        base.update(
            outcome="executable_unavailable",
            diagnostics=[
                _diagnostic(
                    "executable_unavailable",
                    f"Wigolo native executable is unavailable: {type(exc).__name__}.",
                )
            ],
            duration_ms=round((time.monotonic() - started) * 1000),
        )
        return _seal_probe(base)


def _probe_verified_native(
    *,
    base: dict[str, Any],
    command: str,
    runner: Runner,
    timeout: float,
    started: float,
) -> dict[str, Any]:
    """Probe only a private snapshot produced from one validated native FD."""

    doctor_argv = [command, "doctor", "--json"]
    try:
        with tempfile.TemporaryDirectory(prefix="top50-wigolo-doctor-") as directory:
            env = safe_environment()
            env.update({"WIGOLO_DATA_DIR": directory, "HOME": directory})
            completed = _run(runner, doctor_argv, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        base.update(
            outcome="version_probe_timeout",
            checks=[{"name": "version", "status": "failed", "argv": doctor_argv, "returncode": None}],
            diagnostics=[_diagnostic("version_probe_timeout", "Wigolo doctor timed out.")],
        )
        base["duration_ms"] = round((time.monotonic() - started) * 1000)
        return _seal_probe(base)
    except OSError as exc:
        base.update(
            outcome="version_probe_failed",
            checks=[{"name": "version", "status": "failed", "argv": doctor_argv, "returncode": None}],
            diagnostics=[_diagnostic("version_probe_failed", f"Wigolo could not start: {type(exc).__name__}.")],
        )
        base["duration_ms"] = round((time.monotonic() - started) * 1000)
        return _seal_probe(base)

    try:
        doctor = json.loads(_bounded(completed.stdout))
    except (json.JSONDecodeError, TypeError):
        doctor = None
    version = doctor.get("version") if isinstance(doctor, dict) else None
    doctor_ok = (
        completed.returncode == 0
        and isinstance(doctor, dict)
        and doctor.get("status") == "ok"
        and doctor.get("exitCode") == 0
        and isinstance(version, str)
    )
    version_check = {
        "name": "version",
        "status": "passed" if doctor_ok else "failed",
        "argv": doctor_argv,
        "returncode": completed.returncode,
    }
    if not doctor_ok:
        base.update(
            outcome="doctor_not_ready",
            checks=[version_check],
            diagnostics=[_diagnostic("doctor_not_ready", "Wigolo doctor did not return its ready JSON contract.")],
        )
        base["duration_ms"] = round((time.monotonic() - started) * 1000)
        return _seal_probe(base)

    base.update(version=version, backend=_backend(version))
    if not _supported_version(version):
        base.update(
            status="incompatible",
            outcome="unsupported_version",
            checks=[version_check],
            diagnostics=[_diagnostic("unsupported_version", f"Audited range is Wigolo 0.2.x, not {version}.")],
        )
        base["duration_ms"] = round((time.monotonic() - started) * 1000)
        return _seal_probe(base)

    checks = [version_check]
    capabilities: list[str] = []
    diagnostics: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="top50-wigolo-probe-") as directory:
        env = safe_environment()
        env.update({"WIGOLO_DATA_DIR": directory, "HOME": directory})
        for capability in ALLOWED_OPERATIONS:
            argv = [command, *CAPABILITY_PROBE_ARGS[capability]]
            try:
                outcome = _run(runner, argv, timeout=timeout, env=env)
                try:
                    payload = json.loads(_bounded(outcome.stdout))
                except (json.JSONDecodeError, TypeError):
                    payload = None
                if capability == "discovery":
                    passed = (
                        outcome.returncode in {0, 1}
                        and isinstance(payload, dict)
                        and isinstance(payload.get("results"), list)
                        and isinstance(payload.get("error"), str)
                    )
                elif capability == "fetch":
                    passed = (
                        outcome.returncode in {0, 1}
                        and isinstance(payload, dict)
                        and payload.get("url") == ""
                        and isinstance(payload.get("error"), str)
                    )
                elif capability == "cache":
                    passed = (
                        outcome.returncode == 0
                        and isinstance(payload, dict)
                        and isinstance(payload.get("stats"), dict)
                    )
                else:
                    passed = (
                        outcome.returncode == 0
                        and isinstance(payload, dict)
                        and isinstance(payload.get("jobs"), list)
                    )
                checks.append(
                    {
                        "name": capability,
                        "status": "passed" if passed else "failed",
                        "argv": argv,
                        "returncode": outcome.returncode,
                    }
                )
                if passed:
                    capabilities.append(capability)
                else:
                    diagnostics.append(
                        _diagnostic("capability_probe_failed", f"{capability} dispatch probe failed.")
                    )
            except (OSError, subprocess.TimeoutExpired):
                checks.append(
                    {"name": capability, "status": "failed", "argv": argv, "returncode": None}
                )
                diagnostics.append(
                    _diagnostic("capability_probe_failed", f"{capability} dispatch probe could not run.")
                )

    dispatch_ready = capabilities == list(ALLOWED_OPERATIONS)
    base.update(
        ready=dispatch_ready,
        dispatch_ready=dispatch_ready,
        live_route_ready=False,
        status="dispatch_ready" if dispatch_ready else "degraded",
        outcome="dispatch_ready" if dispatch_ready else "capability_probe_failed",
        capabilities=capabilities,
        checks=checks,
        diagnostics=diagnostics,
        duration_ms=round((time.monotonic() - started) * 1000),
    )
    return _seal_probe(base)


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _contains_cjk(value: Any) -> bool:
    if isinstance(value, str):
        return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]", value))
    if isinstance(value, Mapping):
        return any(_contains_cjk(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_cjk(item) for item in value)
    return False


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_host(hostname: str) -> bool:
    host = hostname.rstrip(".").lower()
    if (
        not host
        or host == "localhost"
        or host.endswith((".localhost", ".local", ".internal", ".home", ".lan", ".localdomain"))
        or host in {"metadata.google.internal", "metadata.aws.internal"}
    ):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError:
            return False
        labels = ascii_host.split(".")
        return len(ascii_host) <= 253 and len(labels) >= 2 and all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in labels
        )
    return not any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def _public_url(value: Any) -> bool:
    if not _is_text(value):
        return False
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname is not None
        and parsed.username is None
        and parsed.password is None
        and _valid_host(parsed.hostname)
    )


def _domain(value: Any) -> bool:
    return _is_text(value) and not any(char in value for char in "/,:@?#") and _valid_host(value)


def _validate_request(raw: Any) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if not isinstance(raw, dict):
        return None, [_diagnostic("invalid_request", "Request must be an object.")]
    unknown = sorted(set(raw) - REQUEST_FIELDS)
    missing = sorted(COMMON_REQUIRED_FIELDS - set(raw))
    if unknown or missing:
        detail = "unknown=" + ",".join(unknown) if unknown else "missing=" + ",".join(missing)
        return None, [_diagnostic("invalid_request", detail)]
    operation = raw.get("operation")
    if raw.get("contract_version") != REQUEST_CONTRACT:
        return None, [_diagnostic("invalid_request", "Unsupported request contract.")]
    if not _is_text(raw.get("run_id")):
        return None, [_diagnostic("invalid_request", "run_id must be non-empty.")]
    if not isinstance(raw.get("enabled", False), bool):
        return None, [_diagnostic("invalid_request", "enabled must be boolean.")]
    if raw.get("selection_mode") not in {"explicit", "auto"}:
        return None, [_diagnostic("invalid_request", "selection_mode is invalid.")]
    if operation not in ALLOWED_OPERATIONS:
        return None, [_diagnostic("invalid_request", "operation is outside the allowlist.")]
    if not isinstance(raw.get("allow_experimental_cjk"), bool):
        return None, [_diagnostic("invalid_request", "allow_experimental_cjk must be boolean.")]
    timeout = raw.get("timeout_seconds")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not 0 < timeout <= MAX_EXECUTION_TIMEOUT
    ):
        return None, [_diagnostic("invalid_request", "timeout_seconds must be in (0,300].")]
    payload = raw.get("payload")
    if not isinstance(payload, dict):
        return None, [_diagnostic("invalid_request", "payload must be an object.")]
    unknown_payload = sorted(set(payload) - PAYLOAD_FIELDS[str(operation)])
    if unknown_payload:
        return None, [
            _diagnostic("invalid_request", "Unknown payload fields: " + ",".join(unknown_payload))
        ]
    normalized = dict(raw)
    normalized.setdefault("enabled", False)
    normalized["payload"] = dict(payload)
    return normalized, []


def _policy_check(request: Mapping[str, Any]) -> list[dict[str, str]]:
    operation = str(request["operation"])
    payload = request["payload"]
    diagnostics: list[dict[str, str]] = []
    if operation == "discovery":
        query = payload.get("query")
        if not _is_text(query):
            diagnostics.append(_diagnostic("invalid_query", "query must be non-empty."))
        elif query.lstrip().startswith("-"):
            diagnostics.append(_diagnostic("option_injection", "query cannot begin with '-'."))
        maximum = payload.get("max_results")
        if maximum is not None and (
            isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 50
        ):
            diagnostics.append(_diagnostic("invalid_limit", "max_results must be in 1..50."))
        for field in ("from_date", "to_date"):
            if field in payload and not _valid_date(payload[field]):
                diagnostics.append(_diagnostic("invalid_date", f"{field} must use YYYY-MM-DD."))
        for field in ("include_domains", "exclude_domains"):
            values = payload.get(field)
            if values is not None and (
                not isinstance(values, list)
                or not values
                or len(values) > 50
                or len(set(values)) != len(values)
                or any(not _domain(item) for item in values)
            ):
                diagnostics.append(_diagnostic("unsafe_domain", f"{field} is invalid."))
        if (
            _valid_date(payload.get("from_date"))
            and _valid_date(payload.get("to_date"))
            and payload["from_date"] > payload["to_date"]
        ):
            diagnostics.append(
                _diagnostic("invalid_date_range", "from_date cannot be after to_date.")
            )
        included = payload.get("include_domains")
        excluded = payload.get("exclude_domains")
        if isinstance(included, list) and isinstance(excluded, list) and set(included) & set(excluded):
            diagnostics.append(
                _diagnostic("conflicting_domain_filter", "A domain cannot be included and excluded.")
            )
    elif operation == "fetch":
        if not _public_url(payload.get("url")):
            diagnostics.append(
                _diagnostic("unsafe_target", "fetch URL fails the public lexical precheck.")
            )
        maximum = payload.get("max_chars")
        if maximum is not None and (
            isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or not 1 <= maximum <= 200_000
        ):
            diagnostics.append(_diagnostic("invalid_limit", "max_chars must be in 1..200000."))
        if "section" in payload and not _is_text(payload["section"]):
            diagnostics.append(_diagnostic("invalid_section", "section must be non-empty."))
    elif operation == "cache":
        action = payload.get("action")
        if action not in {"stats", "search"}:
            diagnostics.append(
                _diagnostic(
                    "cache_clear_forbidden" if action == "clear" else "invalid_cache_action",
                    "Only stats and lexical search are allowed.",
                )
            )
        query = payload.get("query")
        if action == "search" and not _is_text(query):
            diagnostics.append(_diagnostic("invalid_query", "cache search requires query."))
        elif action == "search" and query.lstrip().startswith("-"):
            diagnostics.append(_diagnostic("option_injection", "cache query cannot begin with '-'."))
        for field in ("url_pattern", "since"):
            if field in payload and not _is_text(payload[field]):
                diagnostics.append(_diagnostic("invalid_cache_filter", f"{field} must be non-empty."))
        for field, maximum in (("limit", 50), ("max_tokens_out", 100_000)):
            value = payload.get(field)
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= maximum
            ):
                diagnostics.append(_diagnostic("invalid_limit", f"{field} is invalid."))
    elif payload.get("action") != "list":
        diagnostics.append(_diagnostic("watch_read_only", "Only watch list is allowed."))
    return diagnostics


def _build_argv(command: str, request: Mapping[str, Any]) -> list[str]:
    operation = request["operation"]
    payload = request["payload"]
    if operation == "discovery":
        argv = [command, "search", payload["query"]]
        for field, flag in (
            ("max_results", "max-results"),
            ("from_date", "from-date"),
            ("to_date", "to-date"),
        ):
            if field in payload:
                argv.append(f"--{flag}={payload[field]}")
        for field, flag in (
            ("include_domains", "include-domains"),
            ("exclude_domains", "exclude-domains"),
        ):
            if field in payload:
                argv.append(f"--{flag}={','.join(payload[field])}")
        return [*argv, "--no-content", "--no-cache", "--json"]
    if operation == "fetch":
        argv = [command, "fetch", payload["url"], "--render-js=never", "--force-refresh"]
        if "max_chars" in payload:
            argv.append(f"--max-chars={payload['max_chars']}")
        if "section" in payload:
            argv.append(f"--section={payload['section']}")
        return [*argv, "--json"]
    if operation == "cache":
        argv = [command, "cache", payload["action"]]
        if payload["action"] == "search":
            argv.extend([payload["query"], "--mode=fts"])
            for field, flag in (
                ("url_pattern", "url-pattern"),
                ("since", "since"),
                ("limit", "limit"),
                ("max_tokens_out", "max-tokens-out"),
            ):
                if field in payload:
                    argv.append(f"--{flag}={payload[field]}")
        return [*argv, "--json"]
    return [command, "watch", "list", "--json"]


def _opened_file(path: Path, *, executable: bool = False) -> tuple[int, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ContractError("Wigolo native executable could not be opened safely") from exc
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or not 0 < metadata.st_size <= MAX_EXECUTABLE_BYTES
        or executable
        and not metadata.st_mode & stat.S_IXUSR
    ):
        os.close(descriptor)
        raise ContractError("Wigolo native executable file is invalid")
    return descriptor, metadata


def _read_at(descriptor: int, offset: int, length: int) -> bytes:
    if offset < 0 or length < 0:
        raise ContractError("native executable header offset is invalid")
    if hasattr(os, "pread"):
        return os.pread(descriptor, length, offset)
    current = os.lseek(descriptor, 0, os.SEEK_CUR)
    try:
        os.lseek(descriptor, offset, os.SEEK_SET)
        return os.read(descriptor, length)
    finally:
        os.lseek(descriptor, current, os.SEEK_SET)


def _host_architecture() -> str:
    machine = platform.machine().strip().lower()
    aliases = {
        "amd64": "x86_64",
        "x64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "arm64",
        "aarch64": "arm64",
        "i386": "x86",
        "i486": "x86",
        "i586": "x86",
        "i686": "x86",
        "x86": "x86",
        "armv7": "arm",
        "armv7l": "arm",
    }
    try:
        return aliases[machine]
    except KeyError as exc:
        raise ContractError("host architecture is unsupported for native Wigolo") from exc


def _validate_macho(descriptor: int, size: int, host_arch: str) -> None:
    header = _read_at(descriptor, 0, min(size, 8))
    thin = {
        b"\xce\xfa\xed\xfe": "little",
        b"\xcf\xfa\xed\xfe": "little",
        b"\xfe\xed\xfa\xce": "big",
        b"\xfe\xed\xfa\xcf": "big",
    }
    cpu_types = {"x86": 7, "x86_64": 0x01000007, "arm": 12, "arm64": 0x0100000C}
    if header[:4] in thin:
        if len(header) < 8:
            raise ContractError("native Mach-O header is truncated")
        cpu_type = int.from_bytes(header[4:8], thin[header[:4]])
        if cpu_types.get(host_arch) != cpu_type:
            raise ContractError("native Mach-O executable is not compatible with this host")
        return

    fat = {
        b"\xca\xfe\xba\xbe": ("big", 20),
        b"\xbe\xba\xfe\xca": ("little", 20),
        b"\xca\xfe\xba\xbf": ("big", 32),
        b"\xbf\xba\xfe\xca": ("little", 32),
    }
    if header[:4] not in fat or len(header) < 8:
        raise ContractError("Wigolo entry is not a native Mach-O executable")
    endian, entry_size = fat[header[:4]]
    count = int.from_bytes(header[4:8], endian)
    if not 1 <= count <= 128 or 8 + count * entry_size > size:
        raise ContractError("native FAT Mach-O header is invalid")
    table = _read_at(descriptor, 8, count * entry_size)
    expected = cpu_types.get(host_arch)
    if expected is None or not any(
        int.from_bytes(table[index : index + 4], endian) == expected
        for index in range(0, len(table), entry_size)
    ):
        raise ContractError("native FAT Mach-O executable is not compatible with this host")


def _validate_elf(descriptor: int, size: int, host_arch: str) -> None:
    header = _read_at(descriptor, 0, min(size, 20))
    if len(header) < 20 or header[:4] != b"\x7fELF":
        raise ContractError("Wigolo entry is not a native ELF executable")
    if header[4] not in {1, 2} or header[5] not in {1, 2} or header[6] != 1:
        raise ContractError("native ELF identification is invalid")
    endian = "little" if header[5] == 1 else "big"
    machine = int.from_bytes(header[18:20], endian)
    expected = {"x86": 3, "x86_64": 62, "arm": 40, "arm64": 183}.get(host_arch)
    if expected != machine:
        raise ContractError("native ELF executable is not compatible with this host")


def _validate_pe(descriptor: int, size: int, host_arch: str) -> None:
    header = _read_at(descriptor, 0, min(size, 64))
    if len(header) < 64 or header[:2] != b"MZ":
        raise ContractError("Wigolo entry is not a native PE executable")
    pe_offset = int.from_bytes(header[0x3C:0x40], "little")
    if pe_offset < 64 or pe_offset + 24 > size:
        raise ContractError("native PE header offset is invalid")
    pe_header = _read_at(descriptor, pe_offset, 24)
    if len(pe_header) < 24 or pe_header[:4] != b"PE\0\0":
        raise ContractError("native PE header is invalid")
    machine = int.from_bytes(pe_header[4:6], "little")
    expected = {"x86": 0x014C, "x86_64": 0x8664, "arm": 0x01C4, "arm64": 0xAA64}.get(host_arch)
    if expected != machine:
        raise ContractError("native PE executable is not compatible with this host")


def _validate_native_image(descriptor: int, metadata: os.stat_result, source: Path) -> None:
    if source.suffix.lower() in SCRIPT_SUFFIXES:
        raise ContractError("Wigolo entry must be a native executable, not a script")
    system = platform.system().strip().lower()
    host_arch = _host_architecture()
    if system == "darwin":
        _validate_macho(descriptor, metadata.st_size, host_arch)
    elif system in {"linux", "freebsd", "openbsd", "netbsd"}:
        _validate_elf(descriptor, metadata.st_size, host_arch)
    elif system == "windows":
        _validate_pe(descriptor, metadata.st_size, host_arch)
    else:
        raise ContractError("host operating system is unsupported for native Wigolo")


def _same_open_file(before: os.stat_result, after: os.stat_result) -> bool:
    return (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )


def _resolved_native_source(path: str, *, allow_command_symlink: bool = False) -> Path:
    candidate = Path(path).expanduser().absolute()
    try:
        if stat.S_ISLNK(candidate.lstat().st_mode) and not allow_command_symlink:
            raise ContractError("bound executable symlinks are not supported")
        return candidate.resolve(strict=True)
    except OSError as exc:
        raise ContractError("bound native executable is unavailable") from exc


def _copy_open_native(
    descriptor: int,
    metadata: os.stat_result,
    source: Path,
    directory: str,
    *,
    expected_sha256: str | None = None,
) -> tuple[str, str]:
    _validate_native_image(descriptor, metadata, source)
    snapshot_root = Path(directory) / "wigolo-verified"
    snapshot_root.mkdir(mode=0o700)
    os.chmod(snapshot_root, 0o700)
    target = snapshot_root / "wigolo-native"
    target_descriptor = os.open(
        target,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o700,
    )
    digest = hashlib.sha256()
    try:
        os.fchmod(target_descriptor, 0o700)
        os.lseek(descriptor, 0, os.SEEK_SET)
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(target_descriptor, view)
                if written <= 0:
                    raise ContractError("verified native snapshot write failed")
                view = view[written:]
        os.fsync(target_descriptor)
    finally:
        os.close(target_descriptor)
    if not _same_open_file(metadata, os.fstat(descriptor)):
        raise ContractError("native Wigolo executable changed before snapshot dispatch")
    actual = digest.hexdigest()
    if expected_sha256 is not None and not hmac.compare_digest(actual, expected_sha256):
        raise ContractError("bound native executable digest does not match")
    if actual not in AUDITED_NATIVE_RELEASE_SHA256:
        raise ContractError("bound native executable is not an audited Wigolo release")
    return str(target), actual


def _snapshot_bound_executable(
    binding: Mapping[str, Any], directory: str
) -> tuple[str, str]:
    """Validate, digest, and copy one native entry from the same open file."""

    source = _resolved_native_source(str(binding.get("path", "")))
    expected = binding.get("sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
        raise ContractError("bound executable digest is invalid")
    descriptor, metadata = _opened_file(source, executable=True)
    try:
        return _copy_open_native(
            descriptor,
            metadata,
            source,
            directory,
            expected_sha256=str(expected),
        )
    finally:
        os.close(descriptor)


def _blocked_request_result(
    raw: Any,
    outcome: str,
    diagnostics: list[dict[str, str]],
    *,
    status: str = "blocked",
    auth_key: bytes,
) -> dict[str, Any]:
    run_id = raw.get("run_id", "invalid") if isinstance(raw, dict) else "invalid"
    operation = raw.get("operation", "unknown") if isinstance(raw, dict) else "unknown"
    return _result(
        run_id=str(run_id),
        operation=str(operation),
        status=status,
        outcome=outcome,
        diagnostics=diagnostics,
        auth_key=auth_key,
    )


def plan_request(
    raw: Any,
    *,
    command: str | None = None,
    runner: Runner | None = None,
    auth_key_file: str | None = None,
) -> dict[str, Any]:
    auth_key = _resolve_auth_key(auth_key_file)
    request, diagnostics = _validate_request(raw)
    if request is None:
        return _blocked_request_result(
            raw,
            "invalid_request",
            diagnostics,
            status="failed",
            auth_key=auth_key,
        )
    if not request["enabled"]:
        return _blocked_request_result(
            request,
            "disabled",
            [_diagnostic("disabled", "Wigolo is disabled by default.", level="info")],
            auth_key=auth_key,
        )
    if request["selection_mode"] != "explicit":
        return _blocked_request_result(
            request,
            "automatic_selection_rejected",
            [_diagnostic("automatic_selection_rejected", "Explicit selection is required.")],
            auth_key=auth_key,
        )
    if _contains_cjk(request["payload"]) and not request["allow_experimental_cjk"]:
        return _blocked_request_result(
            request,
            "experimental_cjk_requires_opt_in",
            [_diagnostic("experimental_cjk_requires_opt_in", "CJK routing is experimental.")],
            auth_key=auth_key,
        )
    policy = _policy_check(request)
    if policy:
        return _blocked_request_result(
            request,
            "policy_rejected",
            policy,
            auth_key=auth_key,
        )

    probe_binding: dict[str, Any] = {}
    observed = probe(command=command, runner=runner, _binding_sink=probe_binding)
    operation = request["operation"]
    if not observed["dispatch_ready"] or operation not in observed["capabilities"]:
        return _result(
            run_id=request["run_id"],
            operation=operation,
            status="blocked",
            outcome="backend_not_ready",
            diagnostics=[
                _diagnostic("backend_not_ready", f"{operation} did not pass the dispatch probe.")
            ],
            backend=observed["backend"],
            auth_key=auth_key,
        )
    executable = probe_binding.get("executable")
    if (
        not isinstance(executable, dict)
        or set(executable) != {"path", "sha256"}
        or not re.fullmatch(r"[0-9a-f]{64}", str(executable.get("sha256")))
    ):
        return _result(
            run_id=request["run_id"],
            operation=operation,
            status="blocked",
            outcome="backend_not_ready",
            diagnostics=[
                _diagnostic(
                    "executable_unavailable",
                    "The native probe did not bind an executable identity.",
                )
            ],
            backend=observed["backend"],
            auth_key=auth_key,
        )
    plan_diagnostics: list[dict[str, str]] = []
    if _contains_cjk(request["payload"]):
        plan_diagnostics.append(
            _diagnostic(
                "experimental_cjk_enabled",
                "CJK routing remains experimental.",
                level="warning",
            )
        )
    value: dict[str, Any] = {
        "contract_version": PLAN_CONTRACT,
        "adapter_version": ADAPTER_VERSION,
        "run_id": request["run_id"],
        "operation": operation,
        "normalized_request": request,
        "request_digest_sha256": _digest(request),
        "probe_id": observed["probe_id"],
        "probe_digest_sha256": observed["probe_digest_sha256"],
        "executable": executable,
        "backend": observed["backend"],
        "argv": _build_argv(executable["path"], request),
        "timeout_seconds": float(request["timeout_seconds"]),
        "policy": {
            "evidence_authority": "none",
            "curator_authority": "none",
            "output_class": "discovery_only",
            "watch_access": "list_only",
        },
        "diagnostics": plan_diagnostics,
        "auth_key_id": _auth_key_id(auth_key),
    }
    value["plan_digest_sha256"] = _digest(value)
    value["plan_hmac_sha256"] = _hmac_digest(
        auth_key,
        PLAN_HMAC_CONTEXT,
        value,
    )
    return value


def _validate_plan(plan: Any, *, auth_key: bytes) -> dict[str, Any]:
    fields = {
        "contract_version",
        "adapter_version",
        "run_id",
        "operation",
        "normalized_request",
        "request_digest_sha256",
        "probe_id",
        "probe_digest_sha256",
        "executable",
        "backend",
        "argv",
        "timeout_seconds",
        "policy",
        "diagnostics",
        "auth_key_id",
        "plan_digest_sha256",
        "plan_hmac_sha256",
    }
    if not isinstance(plan, dict) or set(plan) != fields:
        raise ContractError("plan fields are invalid")
    if plan.get("contract_version") != PLAN_CONTRACT or plan.get("adapter_version") != ADAPTER_VERSION:
        raise ContractError("plan contract or adapter version is invalid")
    supplied_hmac = plan.get("plan_hmac_sha256")
    expected_hmac = _hmac_digest(
        auth_key,
        PLAN_HMAC_CONTEXT,
        {key: value for key, value in plan.items() if key != "plan_hmac_sha256"},
    )
    if (
        plan.get("auth_key_id") != _auth_key_id(auth_key)
        or not isinstance(supplied_hmac, str)
        or not hmac.compare_digest(supplied_hmac, expected_hmac)
    ):
        raise ContractError("plan HMAC authentication failed")
    supplied_digest = plan.get("plan_digest_sha256")
    if not isinstance(supplied_digest, str) or supplied_digest != _digest(
        {
            key: value
            for key, value in plan.items()
            if key not in {"plan_digest_sha256", "plan_hmac_sha256"}
        }
    ):
        raise ContractError("plan digest does not match")
    request, errors = _validate_request(plan.get("normalized_request"))
    if request is None or errors or request != plan["normalized_request"]:
        raise ContractError("plan request is invalid")
    if not request.get("enabled") or request.get("selection_mode") != "explicit":
        raise ContractError("plan request is not explicitly enabled")
    if _contains_cjk(request["payload"]) and not request["allow_experimental_cjk"]:
        raise ContractError("plan request contains unapproved CJK")
    if _policy_check(request):
        raise ContractError("plan request violates adapter policy")
    if plan.get("request_digest_sha256") != _digest(request):
        raise ContractError("request digest does not match")
    if plan.get("run_id") != request["run_id"] or plan.get("operation") != request["operation"]:
        raise ContractError("plan identity does not match request")
    if plan.get("policy") != {
        "evidence_authority": "none",
        "curator_authority": "none",
        "output_class": "discovery_only",
        "watch_access": "list_only",
    }:
        raise ContractError("plan authority policy is invalid")
    if plan.get("backend") != _backend(plan.get("backend", {}).get("version") if isinstance(plan.get("backend"), Mapping) else None):
        raise ContractError("plan backend identity is invalid")
    backend_version = plan["backend"]["version"]
    if not isinstance(backend_version, str) or not _supported_version(backend_version):
        raise ContractError("plan backend version is invalid")
    if not isinstance(plan.get("executable"), dict) or set(plan["executable"]) != {
        "path",
        "sha256",
    }:
        raise ContractError("executable binding is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(plan["executable"].get("sha256"))):
        raise ContractError("executable digest is invalid")
    if plan.get("argv") != _build_argv(plan["executable"]["path"], request):
        raise ContractError("argv does not match normalized request")
    if not re.fullmatch(r"wigolo-probe-[0-9a-f]{24}", str(plan.get("probe_id"))):
        raise ContractError("probe ID is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", str(plan.get("probe_digest_sha256"))):
        raise ContractError("probe digest is invalid")
    timeout = plan.get("timeout_seconds")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not 0 < timeout <= MAX_EXECUTION_TIMEOUT
    ):
        raise ContractError("plan timeout is invalid")
    if float(timeout) != float(request["timeout_seconds"]):
        raise ContractError("plan timeout does not match request")
    expected_diagnostics = (
        [
            _diagnostic(
                "experimental_cjk_enabled",
                "CJK routing remains experimental.",
                level="warning",
            )
        ]
        if _contains_cjk(request["payload"])
        else []
    )
    if plan.get("diagnostics") != expected_diagnostics:
        raise ContractError("plan diagnostics are invalid")
    return dict(plan)


def _text_field(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value.strip()


def _normalize_discovery(
    data: Mapping[str, Any], expected_query: str, max_results: int
) -> dict[str, Any]:
    if data.get("error") not in {None, ""}:
        raise ContractError("discovery output contains an error")
    query = _text_field(data.get("query"), "query")
    results = data.get("results")
    engines = data.get("engines_used")
    elapsed = data.get("total_time_ms")
    if (
        not isinstance(results, list)
        or not results
        or len(results) > max_results
        or not isinstance(engines, list)
        or not engines
        or not all(_is_text(item) for item in engines)
        or len(set(engines)) != len(engines)
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or not math.isfinite(float(elapsed))
        or elapsed < 0
    ):
        raise ContractError("discovery output shape is invalid or empty")
    if query != expected_query.strip():
        raise ContractError("discovery output query does not match the signed request")
    candidates: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for index, item in enumerate(results):
        if not isinstance(item, Mapping):
            raise ContractError("discovery result must be an object")
        title = _text_field(item.get("title"), "title")
        url = _text_field(item.get("url"), "url")
        snippet = _text_field(item.get("snippet"), "snippet")
        score = item.get("relevance_score")
        if (
            not _public_url(url)
            or isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
            or not 0 <= score <= 1
        ):
            raise ContractError("discovery result identity is invalid")
        if url in seen_urls:
            raise ContractError("discovery output contains duplicate URLs")
        seen_urls.add(url)
        candidates.append(
            {
                "candidate_id": "wigolo-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:24],
                "source_rank": index + 1,
                "title": title,
                "url": url,
                "snippet": snippet,
                "relevance_score": float(score),
                "published_at": item.get("published_date")
                if isinstance(item.get("published_date"), str)
                else item.get("published_at")
                if isinstance(item.get("published_at"), str)
                else None,
                "author": item.get("author") if isinstance(item.get("author"), str) else None,
                "evidence_status": "discovery_only",
                "curator_accepted": False,
            }
        )
    return {
        "evidence_authority": "none",
        "curator_authority": "none",
        "query": query,
        "engines_used": [str(item).strip() for item in engines],
        "total_time_ms": float(elapsed),
        "candidates": candidates,
    }


def _normalize_asset_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ContractError(f"{field} must be an array")
    result: list[str] = []
    for item in value:
        candidate = item if isinstance(item, str) else item.get("url") if isinstance(item, Mapping) else None
        if not _public_url(candidate):
            raise ContractError(f"{field} item is invalid")
        if candidate not in result:
            result.append(candidate)
    return result


FORBIDDEN_BACKEND_FIELDS = {
    "challenge",
    "challenge_class",
    "solve_method",
    "escalated",
    "stealth",
    "captcha",
    "user_agent",
    "proxy_url",
    "hosted_reader_url",
    "scraping_browser_wss",
    "tls_tier",
    "render_js",
}


def _normalized_backend_key(value: Any) -> str:
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value))
    return re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")


def _forbidden_backend_claim(value: Any) -> bool:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = _normalized_backend_key(raw_key)
            present = item is not None and item is not False and item != ""
            if key == "render_js":
                if isinstance(item, str) and item.casefold() not in {"never", "off", "false"}:
                    return True
            elif key == "tls_tier":
                if isinstance(item, str) and item.casefold() not in {"off", "none", "disabled"}:
                    return True
            elif key in FORBIDDEN_BACKEND_FIELDS and present:
                return True
            if key in {"fetch_method", "method"} and isinstance(item, str) and item.casefold() in {
                "browser", "playwright", "cdp", "stealth", "hosted", "solver",
            }:
                return True
            if _forbidden_backend_claim(item):
                return True
        return False
    if isinstance(value, list):
        return any(_forbidden_backend_claim(item) for item in value)
    return False


def _normalize_fetch(
    data: Mapping[str, Any], requested_url: str, max_chars: int | None
) -> dict[str, Any]:
    forbidden_present = any(
        field in data
        and data.get(field) is not None
        and data.get(field) is not False
        and data.get(field) != ""
        for field in ("error", "fetch_failed", "challenge_class", "solve_method", "escalated")
    )
    method = data.get("fetch_method")
    if forbidden_present or method != "http" or _forbidden_backend_claim(data):
        raise ContractError("fetch output used a forbidden capability")
    url = _text_field(data.get("url"), "url")
    title = _text_field(data.get("title"), "title")
    markdown = _text_field(data.get("markdown"), "markdown")
    if (
        not _public_url(url)
        or not isinstance(data.get("metadata"), Mapping)
        or not isinstance(data.get("cached"), bool)
        or data.get("cached") is not False
        or (max_chars is not None and len(markdown) > max_chars)
    ):
        raise ContractError("fetch output shape is invalid")
    status = data.get("http_status")
    if status is not None and (
        isinstance(status, bool) or not isinstance(status, int) or not 200 <= status < 400
    ):
        raise ContractError("fetch HTTP status is invalid")
    return {
        "evidence_authority": "none",
        "curator_authority": "none",
        "evidence_status": "discovery_only",
        "requested_url": requested_url,
        "url": url,
        "title": title,
        "content": markdown,
        "content_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "links": _normalize_asset_list(data.get("links"), "links"),
        "images": _normalize_asset_list(data.get("images"), "images"),
        "cached": data["cached"],
        "http_status": status,
        "acquisition": {
            "method": "direct_http",
            "backend_id": "wigolo",
            "render_js": "never",
        },
    }


def _normalize_cache(data: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    if data.get("error") not in {None, ""}:
        raise ContractError("cache output contains an error")
    action = str(payload["action"])
    base: dict[str, Any] = {
        "evidence_authority": "none",
        "curator_authority": "none",
        "action": action,
    }
    if action == "stats":
        stats = data.get("stats")
        if not isinstance(stats, Mapping):
            raise ContractError("cache stats output is invalid")
        total = stats.get("total_urls")
        size = stats.get("total_size_mb", 0.0)
        if (
            isinstance(total, bool)
            or not isinstance(total, int)
            or total < 0
            or isinstance(size, bool)
            or not isinstance(size, (int, float))
            or size < 0
        ):
            raise ContractError("cache stats values are invalid")
        base["stats"] = {
            "total_urls": total,
            "total_size_mb": float(size),
            "oldest": stats.get("oldest") if isinstance(stats.get("oldest"), str) else "",
            "newest": stats.get("newest") if isinstance(stats.get("newest"), str) else "",
        }
        return base
    rows = data.get("results")
    if not isinstance(rows, list):
        raise ContractError("cache search results are invalid")
    normalized = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ContractError("cache result must be an object")
        url = _text_field(row.get("url"), "cache.url")
        title = _text_field(row.get("title"), "cache.title")
        markdown = _text_field(row.get("markdown"), "cache.markdown")
        fetched_at = _text_field(row.get("fetched_at"), "cache.fetched_at")
        if not _public_url(url):
            raise ContractError("cache URL is invalid")
        normalized.append(
            {
                "url": url,
                "title": title,
                "markdown": markdown,
                "content_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
                "fetched_at": fetched_at,
                "evidence_status": "discovery_only",
            }
        )
    base["query"] = str(payload["query"])
    base["results"] = normalized
    return base


def _normalize_watch(data: Mapping[str, Any]) -> dict[str, Any]:
    if data.get("error") not in {None, ""} or not isinstance(data.get("jobs"), list):
        raise ContractError("watch output is invalid")
    jobs = []
    for row in data["jobs"]:
        if not isinstance(row, Mapping):
            raise ContractError("watch job must be an object")
        identifier = _text_field(row.get("id"), "watch.id")
        url = _text_field(row.get("url"), "watch.url")
        interval = row.get("interval_seconds")
        status = row.get("status")
        created = row.get("created_at")
        if (
            not _public_url(url)
            or isinstance(interval, bool)
            or not isinstance(interval, int)
            or interval < 60
            or status not in {"active", "paused", "errored"}
            or isinstance(created, bool)
            or not isinstance(created, (str, int, float))
        ):
            raise ContractError("watch job fields are invalid")
        jobs.append(
            {
                "id": identifier,
                "url": url,
                "interval_seconds": interval,
                "status": status,
                "notification": row.get("notification")
                if isinstance(row.get("notification"), str)
                else None,
                "created_at": created,
                "selector": row.get("selector")
                if isinstance(row.get("selector"), str)
                else None,
            }
        )
    return {
        "evidence_authority": "none",
        "curator_authority": "none",
        "action": "list",
        "jobs": jobs,
    }


def _normalize_backend_output(
    operation: str, request: Mapping[str, Any], data: Any
) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise ContractError("backend output must be an object")
    if operation == "discovery":
        maximum = request["payload"].get("max_results", 10)
        return _normalize_discovery(
            data,
            str(request["payload"]["query"]),
            int(maximum),
        )
    if operation == "fetch":
        maximum = request["payload"].get("max_chars")
        return _normalize_fetch(
            data,
            str(request["payload"]["url"]),
            int(maximum) if isinstance(maximum, int) and not isinstance(maximum, bool) else None,
        )
    if operation == "cache":
        return _normalize_cache(data, request["payload"])
    return _normalize_watch(data)


def execute_plan(
    raw_plan: Any,
    *,
    runner: Runner | None = None,
    environ: Mapping[str, str] | None = None,
    auth_key_file: str | None = None,
) -> dict[str, Any]:
    active_runner = runner or _RUNNER
    auth_key = _resolve_auth_key(auth_key_file)
    run_id = raw_plan.get("run_id", "invalid") if isinstance(raw_plan, dict) else "invalid"
    operation = raw_plan.get("operation", "unknown") if isinstance(raw_plan, dict) else "unknown"
    backend = (
        raw_plan.get("backend")
        if isinstance(raw_plan, dict) and isinstance(raw_plan.get("backend"), Mapping)
        else _backend()
    )
    try:
        plan = _validate_plan(raw_plan, auth_key=auth_key)
    except ContractError as exc:
        return _result(
            run_id=str(run_id),
            operation=str(operation),
            status="failed",
            outcome="invalid_plan",
            diagnostics=[_diagnostic("invalid_plan", str(exc))],
            backend=backend,
            auth_key=auth_key,
        )
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="top50-wigolo-run-") as directory:
            verified_path, _verified_digest = _snapshot_bound_executable(
                plan["executable"], directory
            )
            execution_argv = [verified_path, *list(plan["argv"])[1:]]
            env = safe_environment(environ)
            env.update({"WIGOLO_DATA_DIR": directory, "HOME": directory})
            completed = _run(
                active_runner,
                execution_argv,
                timeout=float(plan["timeout_seconds"]),
                env=env,
            )
    except ContractError as exc:
        return _result(
            run_id=plan["run_id"],
            operation=plan["operation"],
            status="failed",
            outcome="executable_mismatch",
            diagnostics=[_diagnostic("executable_mismatch", str(exc))],
            backend=plan["backend"],
            argv=plan["argv"],
            plan_digest_sha256=plan["plan_digest_sha256"],
            duration_ms=round((time.monotonic() - started) * 1000),
            auth_key=auth_key,
        )
    except subprocess.TimeoutExpired:
        return _result(
            run_id=plan["run_id"],
            operation=plan["operation"],
            status="failed",
            outcome="timeout",
            diagnostics=[_diagnostic("timeout", "Wigolo execution timed out.")],
            backend=plan["backend"],
            argv=plan["argv"],
            plan_digest_sha256=plan["plan_digest_sha256"],
            duration_ms=round((time.monotonic() - started) * 1000),
            auth_key=auth_key,
        )
    except OSError as exc:
        return _result(
            run_id=plan["run_id"],
            operation=plan["operation"],
            status="failed",
            outcome="execution_failed",
            diagnostics=[
                _diagnostic("execution_failed", f"Wigolo could not start: {type(exc).__name__}.")
            ],
            backend=plan["backend"],
            argv=plan["argv"],
            plan_digest_sha256=plan["plan_digest_sha256"],
            duration_ms=round((time.monotonic() - started) * 1000),
            auth_key=auth_key,
        )
    duration = round((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        return _result(
            run_id=plan["run_id"],
            operation=plan["operation"],
            status="failed",
            outcome="backend_error",
            diagnostics=[_diagnostic("backend_error", f"Wigolo exited {completed.returncode}.")],
            backend=plan["backend"],
            argv=plan["argv"],
            plan_digest_sha256=plan["plan_digest_sha256"],
            returncode=completed.returncode,
            duration_ms=duration,
            auth_key=auth_key,
        )
    try:
        raw_data = json.loads(_bounded(completed.stdout))
        normalized = _normalize_backend_output(
            plan["operation"], plan["normalized_request"], raw_data
        )
    except (json.JSONDecodeError, TypeError, ContractError) as exc:
        banned = isinstance(exc, ContractError) and "forbidden capability" in str(exc)
        return _result(
            run_id=plan["run_id"],
            operation=plan["operation"],
            status="failed",
            outcome="policy_rejected" if banned else "invalid_backend_output",
            diagnostics=[
                _diagnostic(
                    "banned_backend_feature_observed" if banned else "invalid_backend_output",
                    str(exc),
                )
            ],
            backend=plan["backend"],
            argv=plan["argv"],
            plan_digest_sha256=plan["plan_digest_sha256"],
            returncode=completed.returncode,
            duration_ms=duration,
            auth_key=auth_key,
        )
    result = _result(
        run_id=plan["run_id"],
        operation=plan["operation"],
        status="complete",
        outcome="success",
        diagnostics=list(plan["diagnostics"]),
        backend=plan["backend"],
        argv=plan["argv"],
        plan_digest_sha256=plan["plan_digest_sha256"],
        returncode=completed.returncode,
        duration_ms=duration,
        data=normalized,
        auth_key=auth_key,
    )
    validate_result(result, auth_key=auth_key)
    return result


def execute_request(
    raw: Any,
    *,
    command: str | None = None,
    runner: Runner | None = None,
    environ: Mapping[str, str] | None = None,
    auth_key_file: str | None = None,
) -> dict[str, Any]:
    """Compatibility API: plan first, then consume that exact signed plan."""

    plan = plan_request(
        raw,
        command=command,
        runner=runner,
        auth_key_file=auth_key_file,
    )
    if plan.get("contract_version") != PLAN_CONTRACT:
        return plan
    return execute_plan(
        plan,
        runner=runner,
        environ=environ,
        auth_key_file=auth_key_file,
    )


def _exact_fields(value: Any, fields: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError(f"{label} fields are invalid")
    return value


def _finite_number(value: Any, label: str, *, minimum: float = 0.0, maximum: float | None = None) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < minimum
        or (maximum is not None and float(value) > maximum)
    ):
        raise ContractError(f"{label} is invalid")
    return float(value)


def _validate_normalized_data(operation: str, data: Any) -> None:
    common = {"evidence_authority", "curator_authority"}
    if operation == "discovery":
        payload = _exact_fields(
            data,
            common | {"query", "engines_used", "total_time_ms", "candidates"},
            "discovery data",
        )
        if not _is_text(payload.get("query")):
            raise ContractError("discovery query is invalid")
        engines = payload.get("engines_used")
        if (
            not isinstance(engines, list)
            or not engines
            or any(not _is_text(item) for item in engines)
            or len(engines) != len(set(engines))
        ):
            raise ContractError("discovery engines are invalid")
        _finite_number(payload.get("total_time_ms"), "discovery total_time_ms")
        rows = payload.get("candidates")
        if not isinstance(rows, list) or not rows:
            raise ContractError("discovery candidates are invalid")
        candidate_fields = {
            "candidate_id", "source_rank", "title", "url", "snippet",
            "relevance_score", "published_at", "author", "evidence_status",
            "curator_accepted",
        }
        for row in rows:
            candidate = _exact_fields(row, candidate_fields, "discovery candidate")
            if (
                not re.fullmatch(r"wigolo-[0-9a-f]{24}", str(candidate.get("candidate_id")))
                or isinstance(candidate.get("source_rank"), bool)
                or not isinstance(candidate.get("source_rank"), int)
                or candidate["source_rank"] < 1
                or not _is_text(candidate.get("title"))
                or not _public_url(candidate.get("url"))
                or not _is_text(candidate.get("snippet"))
                or candidate.get("published_at") is not None
                and not isinstance(candidate.get("published_at"), str)
                or candidate.get("author") is not None
                and not isinstance(candidate.get("author"), str)
                or candidate.get("evidence_status") != "discovery_only"
                or candidate.get("curator_accepted") is not False
            ):
                raise ContractError(
                    "discovery candidate fields are invalid or claim accepted evidence authority"
                )
            _finite_number(
                candidate.get("relevance_score"),
                "discovery candidate relevance_score",
                maximum=1.0,
            )
        return
    if operation == "fetch":
        payload = _exact_fields(
            data,
            common
            | {
                "evidence_status", "requested_url", "url", "title", "content",
                "content_sha256", "links", "images", "cached", "http_status",
                "acquisition",
            },
            "fetch data",
        )
        content = payload.get("content")
        status = payload.get("http_status")
        if (
            payload.get("evidence_status") != "discovery_only"
            or not _public_url(payload.get("requested_url"))
            or not _public_url(payload.get("url"))
            or not _is_text(payload.get("title"))
            or not _is_text(content)
            or payload.get("content_sha256") != hashlib.sha256(str(content).encode("utf-8")).hexdigest()
            or payload.get("cached") is not False
            or status is not None
            and (isinstance(status, bool) or not isinstance(status, int) or not 200 <= status <= 399)
        ):
            raise ContractError("fetch data fields are invalid")
        for field in ("links", "images"):
            values = payload.get(field)
            if (
                not isinstance(values, list)
                or any(not _public_url(item) for item in values)
                or len(values) != len(set(values))
            ):
                raise ContractError(f"fetch {field} are invalid")
        if payload.get("acquisition") != {
            "method": "direct_http",
            "backend_id": "wigolo",
            "render_js": "never",
        }:
            raise ContractError("fetch acquisition fields are invalid")
        return
    if operation == "cache":
        if not isinstance(data, Mapping):
            raise ContractError("cache data fields are invalid")
        action = data.get("action")
        if action == "stats":
            payload = _exact_fields(data, common | {"action", "stats"}, "cache stats data")
            stats = _exact_fields(
                payload.get("stats"),
                {"total_urls", "total_size_mb", "oldest", "newest"},
                "cache stats",
            )
            total = stats.get("total_urls")
            if (
                isinstance(total, bool)
                or not isinstance(total, int)
                or total < 0
                or not isinstance(stats.get("oldest"), str)
                or not isinstance(stats.get("newest"), str)
            ):
                raise ContractError("cache stats values are invalid")
            _finite_number(stats.get("total_size_mb"), "cache total_size_mb")
        elif action == "search":
            payload = _exact_fields(
                data, common | {"action", "query", "results"}, "cache search data"
            )
            if not _is_text(payload.get("query")) or not isinstance(payload.get("results"), list):
                raise ContractError("cache search values are invalid")
            fields = {"url", "title", "markdown", "content_sha256", "fetched_at", "evidence_status"}
            for row in payload["results"]:
                item = _exact_fields(row, fields, "cache search result")
                markdown = item.get("markdown")
                if (
                    not _public_url(item.get("url"))
                    or not _is_text(item.get("title"))
                    or not _is_text(markdown)
                    or item.get("content_sha256") != hashlib.sha256(str(markdown).encode("utf-8")).hexdigest()
                    or not _is_text(item.get("fetched_at"))
                    or item.get("evidence_status") != "discovery_only"
                ):
                    raise ContractError("cache search result fields are invalid")
        else:
            raise ContractError("cache action is invalid")
        return
    if operation == "watch":
        payload = _exact_fields(data, common | {"action", "jobs"}, "watch data")
        if payload.get("action") != "list" or not isinstance(payload.get("jobs"), list):
            raise ContractError("watch data values are invalid")
        fields = {"id", "url", "interval_seconds", "status", "notification", "created_at", "selector"}
        for row in payload["jobs"]:
            item = _exact_fields(row, fields, "watch job")
            interval = item.get("interval_seconds")
            if (
                not _is_text(item.get("id"))
                or not _public_url(item.get("url"))
                or isinstance(interval, bool)
                or not isinstance(interval, int)
                or interval < 60
                or item.get("status") not in {"active", "paused", "errored"}
                or isinstance(item.get("created_at"), bool)
                or not isinstance(item.get("created_at"), (str, int, float))
                or item.get("notification") is not None
                and not isinstance(item.get("notification"), str)
                or item.get("selector") is not None
                and not isinstance(item.get("selector"), str)
            ):
                raise ContractError("watch job fields are invalid")
        return
    raise ContractError("successful result operation is invalid")


def validate_result(
    value: Any,
    *,
    auth_key_file: str | None = None,
    auth_key: bytes | None = None,
) -> dict[str, Any]:
    resolved_key = auth_key if auth_key is not None else _resolve_auth_key(auth_key_file)
    authenticated_fields = {
        "contract_version",
        "adapter_version",
        "run_id",
        "operation",
        "status",
        "outcome",
        "backend",
        "argv",
        "plan_digest_sha256",
        "returncode",
        "duration_ms",
        "data",
        "diagnostics",
        "result_digest_sha256",
        "auth_key_id",
        "result_hmac_sha256",
    }
    if not isinstance(value, dict) or set(value) != authenticated_fields:
        raise ContractError("result fields are invalid")
    if value.get("contract_version") != RESULT_CONTRACT or value.get("adapter_version") != ADAPTER_VERSION:
        raise ContractError("result contract is invalid")
    digest = value.get("result_digest_sha256")
    if not isinstance(digest, str) or digest != _digest(
        {
            key: item
            for key, item in value.items()
            if key not in {"result_digest_sha256", "result_hmac_sha256"}
        }
    ):
        raise ContractError("result digest does not match")
    supplied_hmac = value.get("result_hmac_sha256")
    expected_hmac = _hmac_digest(
        resolved_key,
        RESULT_HMAC_CONTEXT,
        {key: item for key, item in value.items() if key != "result_hmac_sha256"},
    )
    if (
        value.get("auth_key_id") != _auth_key_id(resolved_key)
        or not isinstance(supplied_hmac, str)
        or not hmac.compare_digest(supplied_hmac, expected_hmac)
    ):
        raise ContractError("result HMAC authentication failed")
    if not _is_text(value.get("run_id")) or not _is_text(value.get("operation")):
        raise ContractError("result identity is invalid")
    if value.get("operation") not in {*ALLOWED_OPERATIONS, "unknown"}:
        raise ContractError("result operation is invalid")
    if value.get("backend") != _safe_backend(value.get("backend")):
        raise ContractError("result backend identity is invalid")
    if value.get("status") not in {"complete", "blocked", "failed"}:
        raise ContractError("result status is invalid")
    success = value.get("outcome") == "success"
    if success != (value.get("status") == "complete"):
        raise ContractError("result status and outcome are inconsistent")
    if not isinstance(value.get("argv"), list) or not all(
        isinstance(item, str) for item in value["argv"]
    ):
        raise ContractError("result argv is invalid")
    plan_digest = value.get("plan_digest_sha256")
    if plan_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(plan_digest)):
        raise ContractError("result plan digest is invalid")
    returncode = value.get("returncode")
    if returncode is not None and (isinstance(returncode, bool) or not isinstance(returncode, int)):
        raise ContractError("result return code is invalid")
    duration = value.get("duration_ms")
    if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
        raise ContractError("result duration is invalid")
    diagnostics = value.get("diagnostics")
    if not isinstance(diagnostics, list) or any(
        not isinstance(row, Mapping)
        or set(row) != {"code", "level", "message"}
        or not _is_text(row.get("code"))
        or row.get("level") not in {"info", "warning", "error"}
        or not _is_text(row.get("message"))
        for row in diagnostics
    ):
        raise ContractError("result diagnostics are invalid")
    if not success and value.get("data") is not None:
        raise ContractError("non-success result cannot carry data")
    if value.get("outcome") == "success":
        data = value.get("data")
        if (
            not isinstance(data, Mapping)
            or data.get("evidence_authority") != "none"
            or data.get("curator_authority") != "none"
        ):
            raise ContractError("successful result cannot carry evidence authority")
        _validate_normalized_data(str(value["operation"]), data)
    return dict(value)


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _emit(value: Any) -> None:
    sys.stdout.write(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    )


def _emit_cli_error(message: str) -> None:
    """Write a non-artifact diagnostic when no trusted signing key is available."""

    sys.stderr.write(f"wigolo_adapter: error: {message}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fail-closed Wigolo external adapter")
    subparsers = parser.add_subparsers(dest="command_name", required=True)
    probe_parser = subparsers.add_parser("probe")
    probe_parser.add_argument("--command", default="wigolo")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--input", required=True, help="v2 request JSON path, or -")
    plan_parser.add_argument("--command", default="wigolo")
    plan_parser.add_argument(
        "--auth-key-file",
        help="owner-only (0600) HMAC key file; required for cross-process plans",
    )
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--plan", required=True, help="signed plan JSON path, or -")
    execute_parser.add_argument(
        "--auth-key-file",
        help="same owner-only HMAC key file used to create the plan",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command_name == "probe":
        value = probe(command=args.command)
        _emit(value)
        return 0 if value["dispatch_ready"] else 1
    if not args.auth_key_file:
        _emit_cli_error(
            "--auth-key-file is required so cross-process artifacts can be authenticated."
        )
        return 2
    try:
        auth_key = _read_auth_key_file(args.auth_key_file)
    except (OSError, ContractError) as exc:
        _emit_cli_error(f"Could not read auth key: {type(exc).__name__}.")
        return 2
    source = args.input if args.command_name == "plan" else args.plan
    try:
        payload = _load_json(source)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        is_plan = args.command_name == "execute"
        value = _result(
            run_id="invalid",
            operation="unknown",
            status="failed",
            outcome="invalid_plan" if is_plan else "invalid_request",
            diagnostics=[
                _diagnostic(
                    "invalid_plan" if is_plan else "invalid_request",
                    f"Could not read JSON: {type(exc).__name__}.",
                )
            ],
            auth_key=auth_key,
        )
        _emit(value)
        return 2
    try:
        value = (
            plan_request(
                payload,
                command=args.command,
                auth_key_file=args.auth_key_file,
            )
            if args.command_name == "plan"
            else execute_plan(payload, auth_key_file=args.auth_key_file)
        )
    except (OSError, ContractError) as exc:
        _emit_cli_error(f"Could not authenticate artifact: {type(exc).__name__}.")
        return 2
    _emit(value)
    return 0 if value.get("contract_version") == PLAN_CONTRACT or value.get("outcome") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
