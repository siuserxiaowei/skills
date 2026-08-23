#!/usr/bin/env python3
"""Probe, plan, and execute the three permanent Top 50 engine structures.

The router is a fail-closed control plane.  It does not infer readiness from a
file on disk: every selected backend must return a compatible probe contract,
and every executed subprocess must return a compatible result contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from lineage_contract import (
        LineageError,
        command_paths_match_bundle,
        validate_curator_business_semantics,
        validate_curator_against_rank_bundle,
        validate_process_business_semantics,
        validate_rank_input_manifest,
    )
except ImportError:  # pragma: no cover - supports importlib-based unit tests
    import importlib.util

    _LINEAGE_PATH = Path(__file__).with_name("lineage_contract.py")
    _LINEAGE_SPEC = importlib.util.spec_from_file_location(
        "top50_router_lineage_contract", _LINEAGE_PATH
    )
    if _LINEAGE_SPEC is None or _LINEAGE_SPEC.loader is None:
        raise
    _LINEAGE = importlib.util.module_from_spec(_LINEAGE_SPEC)
    _LINEAGE_SPEC.loader.exec_module(_LINEAGE)
    LineageError = _LINEAGE.LineageError
    command_paths_match_bundle = _LINEAGE.command_paths_match_bundle
    validate_curator_business_semantics = (
        _LINEAGE.validate_curator_business_semantics
    )
    validate_curator_against_rank_bundle = (
        _LINEAGE.validate_curator_against_rank_bundle
    )
    validate_process_business_semantics = (
        _LINEAGE.validate_process_business_semantics
    )
    validate_rank_input_manifest = _LINEAGE.validate_rank_input_manifest


REQUEST_SCHEMA = "top50-router-request/v1"
PROBE_SCHEMA = "top50-router-probe/v1"
PLAN_SCHEMA = "top50-router-plan/v1"
RESULT_SCHEMA = "top50-router-result/v1"
EXTERNAL_ENGINE_CONTRACT = "top50-engine/v1"
PYTHON_ENGINE_CONTRACT = "top50-python-adapter/v1"

STAGE_COMPLETION_CONTRACTS = {
    "discovery": "top50-discovery-result/v1",
    "fetch": "top50-fetch-result/v1",
    "extraction": "top50-extraction-result/v1",
    "process": "top50-process-result/v1",
    "curate": "top50-curator-acceptance/v1",
}

ENGINES = ("python", "go", "rust")
REQUEST_STAGES = ("discovery", "fetch", "process", "rank")
PLAN_STAGES = ("discovery", "fetch", "extraction", "process", "curate", "rank")
REQUEST_ENUMS = {
    "stage": {*REQUEST_STAGES, "full"},
    "workload": {"small", "medium", "large"},
    "source_kind": {"public_http", "platform_cli", "browser_session", "local_bundle"},
    "risk": {"low", "medium", "high"},
    "engine_mode": {"auto", "python", "go", "rust", "hybrid"},
}
EXPECTED_ENGINE_IDS = {"go": "go-collector", "rust": "rust-processor"}
EXPECTED_PROBE_CONTRACTS = {
    "python": PYTHON_ENGINE_CONTRACT,
    "go": EXTERNAL_ENGINE_CONTRACT,
    "rust": EXTERNAL_ENGINE_CONTRACT,
}

PYTHON_CAPABILITIES = (
    "control",
    "platform_orchestration",
    "platform_cli",
    "browser_session",
    "rank",
    "contract_validation",
    "publish_orchestration",
)

# Backends may expose precise low-level names.  Routing understands those names
# without rewriting the probe evidence or claiming capabilities not reported by
# the engine.
CAPABILITY_ALIASES = {
    "public_http": {"public_http", "public_http_fetch", "bounded_public_http", "public_http_collect"},
    "discovery": {"discovery", "public_http_discovery"},
    "fetch": {"fetch", "public_http_fetch", "bounded_public_http", "collect", "public_http_collect"},
    "concurrent_fetch": {"concurrent_fetch", "bounded_concurrency"},
    "process": {"process", "candidate_processing", "normalize", "normalization"},
    "normalize": {"normalize", "normalization", "candidate_normalization"},
    "fingerprint": {"fingerprint", "content_fingerprinting", "strict_content_fingerprinting"},
    "deduplicate": {"deduplicate", "deduplication", "transitive_exact_clustering"},
    "security_preflight": {"security_preflight", "safe_url_validation"},
    "rank": {"rank", "ranking"},
    "platform_orchestration": {"platform_orchestration"},
    "contract_validation": {"contract_validation"},
}

MAX_EVIDENCE_CHARS = 100_000
DEFAULT_PROBE_TIMEOUT = 20.0
DEFAULT_EXECUTION_TIMEOUT = 300.0

PLAN_FIELDS = {
    "schema",
    "run_id",
    "created_at",
    "request",
    "candidates",
    "selected_engines",
    "stages",
    "fallbacks",
    "reason_codes",
    "probe_evidence",
    "dual_run",
    "handoffs",
    "pause_conditions",
}
PLAN_REQUIRED_FIELDS = set(PLAN_FIELDS)
STEP_REQUIRED_FIELDS = {
    "id",
    "stage",
    "engine",
    "role",
    "input_contract",
    "output_contract",
    "execution_mode",
    "command",
    "timeout_seconds",
    "fallback_chain",
}
STEP_FIELDS = {
    "id",
    "stage",
    "engine",
    "role",
    "input_contract",
    "output_contract",
    "execution_mode",
    "command",
    "timeout_seconds",
    "fallback_chain",
    "output_path",
    "validates_step",
    "gate",
    "completion_artifact",
    "input_binding",
}
GATE_FIELDS = {
    "type",
    "path",
    "contract",
    "required_status",
    "run_id",
    "stage",
    "artifact_sha256",
    "fail_closed",
}
COMPLETION_FIELDS = {"path", "contract", "required_status", "run_id", "stage"}
PUBLIC_HTTP_BINDING_FIELDS = {
    "manifest_path",
    "manifest_artifact_sha256",
    "job_set_sha256",
    "job_count",
}
TRANSPARENT_USER_AGENT = "TopFiftyCollector/0.1 (+https://github.com/siuserxiaowei/skills)"
ROBOTS_PRODUCT_TOKEN = "TopFiftyCollector"
ALLOWED_REQUEST_HEADERS = {"accept", "accept-language", "accept-encoding"}
INPUT_BINDING_FIELDS = {
    "relation",
    "path",
    "artifact_sha256",
    "contract",
    "run_id",
    "stage",
    "required_status",
    "producer_engine_id",
    "result_digest_sha256",
    "record_kind",
    "record_count",
    "record_ids_sha256",
}
STAGE_INPUT_ALTERNATIVES = {
    "discovery": ({"scope_query_plan"},),
    "fetch": ({"discovery_result"}, {"frozen_http_manifest"}),
    "extraction": ({"fetch_result"},),
    "process": ({"extraction_result"},),
    "curate": ({"process_result", "rank_input_manifest"},),
}
RELATION_RECORD_KINDS = {
    "scope_query_plan": "query",
    "discovery_result": "discovery",
    "frozen_http_manifest": "job",
    "fetch_result": "job",
    "extraction_result": "candidate",
    "process_result": "candidate",
    "rank_input_manifest": "file",
}


class RouterError(ValueError):
    """A contract, routing, or execution precondition failed."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _duration_ms(started: float) -> int:
    return max(0, round((time.monotonic() - started) * 1000))


def _bounded(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = str(value)
    if len(text) <= MAX_EVIDENCE_CHARS:
        return text
    return text[:MAX_EVIDENCE_CHARS] + "\n...[truncated by engine router]"


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def _unique_strings(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if any(not _is_nonempty_string(item) for item in value):
        return None
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        return None
    return normalized


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _validate_public_http_binding(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != PUBLIC_HTTP_BINDING_FIELDS:
        raise RouterError(
            "public_http_binding must contain exactly manifest_path, "
            "manifest_artifact_sha256, job_set_sha256, and job_count"
        )
    if not _is_nonempty_string(value.get("manifest_path")):
        raise RouterError("public_http_binding.manifest_path must be non-empty")
    if not _is_sha256(value.get("manifest_artifact_sha256")) or not _is_sha256(
        value.get("job_set_sha256")
    ):
        raise RouterError("public_http_binding digests must be lowercase SHA-256")
    count = value.get("job_count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise RouterError("public_http_binding.job_count must be a positive integer")
    return dict(value)


def validate_request(payload: Any) -> dict[str, Any]:
    """Validate and return a defensive copy of top50-router-request/v1."""
    if not isinstance(payload, dict):
        raise RouterError("router request must be a JSON object")
    required = {
        "schema",
        "run_id",
        "stage",
        "workload",
        "source_kind",
        "risk",
        "required_capabilities",
        "engine_mode",
        "dual_run",
    }
    optional = {
        "engine_paths",
        "run_dir",
        "top_n",
        "timeout_seconds",
        "public_http_binding",
    }
    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required - optional)
    if missing:
        raise RouterError(f"router request is missing required fields: {', '.join(missing)}")
    if unknown:
        raise RouterError(f"router request has unknown fields: {', '.join(unknown)}")
    if payload.get("schema") != REQUEST_SCHEMA:
        raise RouterError(f"schema must be {REQUEST_SCHEMA}")
    run_id = payload.get("run_id")
    if (
        not _is_nonempty_string(run_id)
        or len(run_id) > 128
        or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in run_id)
        or run_id in {".", ".."}
    ):
        raise RouterError("run_id must be a safe 1-128 character identifier")
    for field, allowed in REQUEST_ENUMS.items():
        if payload.get(field) not in allowed:
            raise RouterError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    capabilities = _unique_strings(payload.get("required_capabilities"))
    if capabilities is None:
        raise RouterError("required_capabilities must be a unique string array")
    if not isinstance(payload.get("dual_run"), bool):
        raise RouterError("dual_run must be a boolean")
    paths = payload.get("engine_paths", {})
    if not isinstance(paths, dict):
        raise RouterError("engine_paths must be an object keyed by python, go, or rust")
    unknown_engines = sorted(set(paths) - set(ENGINES))
    if unknown_engines:
        raise RouterError(f"engine_paths has unknown engines: {', '.join(unknown_engines)}")
    if any(not _is_nonempty_string(path) for path in paths.values()):
        raise RouterError("every engine_paths value must be a non-empty path string")
    if "run_dir" in payload and not _is_nonempty_string(payload["run_dir"]):
        raise RouterError("run_dir must be a non-empty path string")
    top_n = payload.get("top_n", 50)
    if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 100:
        raise RouterError("top_n must be an integer from 1 to 100")
    timeout = payload.get("timeout_seconds", DEFAULT_EXECUTION_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 3600:
        raise RouterError("timeout_seconds must be greater than 0 and at most 3600")
    requires_public_binding = (
        payload.get("source_kind") == "public_http"
        and payload.get("stage") in {"fetch", "full"}
    )
    if requires_public_binding:
        if "public_http_binding" not in payload:
            raise RouterError("public_http_binding is required for public_http fetch/full")
        public_http_binding = _validate_public_http_binding(payload["public_http_binding"])
    else:
        if "public_http_binding" in payload:
            raise RouterError("public_http_binding is only allowed for public_http fetch/full")
        public_http_binding = None

    normalized = dict(payload)
    normalized["required_capabilities"] = capabilities
    normalized["engine_paths"] = dict(paths)
    normalized["top_n"] = top_n
    normalized["timeout_seconds"] = float(timeout)
    if public_http_binding is not None:
        normalized["public_http_binding"] = public_http_binding
    return normalized


def _empty_probe(engine: str, command: Sequence[str], reason: str) -> dict[str, Any]:
    return {
        "engine": engine,
        "ready": False,
        "version": None,
        "contract": None,
        "engine_id": None,
        "capabilities": [],
        "command": list(command),
        "base_command": list(command[:-2]) if list(command[-2:]) == ["probe", "--json"] else list(command),
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "reason": reason,
        "duration_ms": 0,
    }


def _probe_process(engine: str, command: Sequence[str], timeout: float) -> dict[str, Any]:
    if not isinstance(command, (list, tuple)) or not command or any(
        not _is_nonempty_string(item) for item in command
    ):
        raise RouterError("probe command must be a non-empty argv array")
    started = time.monotonic()
    evidence = _empty_probe(engine, command, "probe_failed")
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        evidence.update(
            {
                "reason": "probe_timeout",
                "stdout": _bounded(exc.stdout),
                "stderr": _bounded(exc.stderr),
                "duration_ms": _duration_ms(started),
            }
        )
        return evidence
    except (FileNotFoundError, PermissionError, OSError) as exc:
        evidence.update(
            {
                "reason": "executable_unavailable",
                "stderr": _bounded(exc),
                "duration_ms": _duration_ms(started),
            }
        )
        return evidence
    evidence.update(
        {
            "returncode": completed.returncode,
            "stdout": _bounded(completed.stdout),
            "stderr": _bounded(completed.stderr),
            "duration_ms": _duration_ms(started),
        }
    )
    if completed.returncode != 0:
        evidence["reason"] = "probe_nonzero_exit"
    return evidence


def _normalize_probe(engine: str, raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize injected or executed evidence and enforce the probe contract."""
    if engine not in ENGINES or not isinstance(raw, Mapping):
        raise RouterError("probe evidence must be an object for a known engine")
    result = _empty_probe(engine, [], str(raw.get("reason") or "not_ready"))
    result.update({key: value for key, value in raw.items() if key in result or key == "raw_probe"})
    result["engine"] = engine
    command = raw.get("command", [])
    if not isinstance(command, list) or any(not isinstance(item, str) for item in command):
        command = []
    result["command"] = command
    base = raw.get("base_command")
    if not isinstance(base, list) or not base or any(not _is_nonempty_string(item) for item in base):
        if command[-2:] == ["probe", "--json"] or command[-1:] == ["--help"]:
            base = command[:-2] if command[-2:] == ["probe", "--json"] else command[:-1]
        else:
            base = command
    result["base_command"] = list(base)

    if not bool(raw.get("ready")):
        result["ready"] = False
        result["capabilities"] = []
        return result
    contract = raw.get("contract", raw.get("contract_version"))
    if contract != EXPECTED_PROBE_CONTRACTS[engine]:
        result.update({"ready": False, "contract": contract, "capabilities": [], "reason": "contract_mismatch"})
        return result
    version = raw.get("version", raw.get("engine_version"))
    if not _is_nonempty_string(version):
        result.update({"ready": False, "contract": contract, "capabilities": [], "reason": "invalid_probe_version"})
        return result
    capabilities = _unique_strings(raw.get("capabilities"))
    if capabilities is None or not capabilities:
        result.update({"ready": False, "contract": contract, "capabilities": [], "reason": "invalid_probe_capabilities"})
        return result
    engine_id = raw.get("engine_id", raw.get("id"))
    expected_id = EXPECTED_ENGINE_IDS.get(engine)
    if expected_id and engine_id is not None and engine_id != expected_id:
        result.update({"ready": False, "contract": contract, "capabilities": [], "reason": "engine_id_mismatch"})
        return result
    status = raw.get("status")
    if status not in {None, "ready"}:
        result.update({"ready": False, "contract": contract, "capabilities": [], "reason": "engine_status_not_ready"})
        return result
    result.update(
        {
            "ready": True,
            "version": version.strip(),
            "contract": contract,
            "engine_id": engine_id or ("python-ranker" if engine == "python" else expected_id),
            "capabilities": capabilities,
            "reason": "ready",
        }
    )
    return result


def probe_external_engine(engine: str, base_command: Sequence[str], timeout: float = DEFAULT_PROBE_TIMEOUT) -> dict[str, Any]:
    """Run an external engine's machine-readable probe and validate it."""
    if engine not in {"go", "rust"}:
        raise RouterError("external engine must be go or rust")
    if not isinstance(base_command, (list, tuple)) or not base_command:
        raise RouterError("external engine base command must be an argv array")
    command = list(base_command) + ["probe", "--json"]
    evidence = _probe_process(engine, command, timeout)
    evidence["base_command"] = list(base_command)
    if evidence["returncode"] is None or evidence["returncode"] != 0:
        return evidence
    try:
        payload = json.loads(evidence["stdout"])
    except (json.JSONDecodeError, TypeError):
        evidence["reason"] = "invalid_probe_json"
        return evidence
    if not isinstance(payload, dict):
        evidence["reason"] = "invalid_probe_json"
        return evidence
    canonical_fields = {
        "contract_version", "engine_id", "engine_version", "status", "capabilities"
    }
    if set(payload) != canonical_fields:
        evidence["reason"] = "invalid_probe_contract_fields"
        return evidence
    raw = {
        **evidence,
        "ready": True,
        "contract": payload["contract_version"],
        "engine_id": payload["engine_id"],
        "version": payload["engine_version"],
        "status": payload.get("status"),
        "capabilities": payload.get("capabilities"),
        "raw_probe": payload,
    }
    normalized = _normalize_probe(engine, raw)
    normalized["raw_probe"] = payload
    return normalized


def _path_command(path: Path) -> list[str]:
    if path.suffix.casefold() == ".py":
        return [sys.executable, str(path)]
    return [str(path)]


def probe_python_engine(ranker_path: Path, timeout: float = DEFAULT_PROBE_TIMEOUT) -> dict[str, Any]:
    """Execute the ranker CLI; readiness does not imply any network ability."""
    path = Path(ranker_path).expanduser()
    base = _path_command(path)
    command = base + ["--help"]
    if not path.is_file():
        evidence = _empty_probe("python", command, "executable_unavailable")
        evidence["base_command"] = base
        evidence["stderr"] = f"ranker path does not exist: {path}"
        return evidence
    evidence = _probe_process("python", command, timeout)
    evidence["base_command"] = base
    if evidence["returncode"] != 0 or not evidence["stdout"].strip():
        if evidence["returncode"] == 0:
            evidence["reason"] = "invalid_help_output"
        return evidence
    return _normalize_probe(
        "python",
        {
            **evidence,
            "ready": True,
            "contract": PYTHON_ENGINE_CONTRACT,
            "engine_id": "python-ranker",
            "version": "deterministic-v2",
            "capabilities": list(PYTHON_CAPABILITIES),
            "base_command": base,
        },
    )


def _default_engine_commands(skill_root: Path, engine_paths: Mapping[str, str]) -> dict[str, Any]:
    ranker = Path(engine_paths.get("python", str(skill_root / "scripts" / "rank_candidates.py"))).expanduser()
    if "go" in engine_paths:
        go_command = [str(Path(engine_paths["go"]).expanduser())]
    else:
        go_command = ["go", "-C", str(skill_root / "engines" / "go-collector"), "run", "."]
    if "rust" in engine_paths:
        rust_command = [str(Path(engine_paths["rust"]).expanduser())]
    else:
        rust_command = [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(skill_root / "engines" / "rust-processor" / "Cargo.toml"),
            "--",
        ]
    return {"python": ranker, "go": go_command, "rust": rust_command}


def probe_all(
    engine_paths: Mapping[str, str] | None = None,
    *,
    skill_root: Path | None = None,
    timeout: float = DEFAULT_PROBE_TIMEOUT,
) -> dict[str, Any]:
    root = skill_root or Path(__file__).resolve().parents[1]
    paths = dict(engine_paths or {})
    commands = _default_engine_commands(root, paths)
    engines = {
        "python": probe_python_engine(commands["python"], timeout=timeout),
        "go": probe_external_engine("go", commands["go"], timeout=timeout),
        "rust": probe_external_engine("rust", commands["rust"], timeout=timeout),
    }
    return {"schema": PROBE_SCHEMA, "probed_at": _now(), "engines": engines}


def _has_capability(capabilities: Iterable[str], requested: str) -> bool:
    actual = set(capabilities)
    accepted = CAPABILITY_ALIASES.get(requested, {requested})
    return bool(actual & accepted) or requested in actual


def _engine_supports_stage(engine: str, stage: str, source_kind: str, capabilities: Sequence[str]) -> bool:
    if engine == "python":
        if stage in {"discovery", "fetch"}:
            return _has_capability(capabilities, "platform_orchestration")
        if stage == "process":
            return _has_capability(capabilities, "contract_validation")
        if stage == "extraction":
            return _has_capability(capabilities, "control")
        if stage == "curate":
            return _has_capability(capabilities, "control")
        return stage == "rank" and _has_capability(capabilities, "rank")
    if engine == "go":
        if source_kind != "public_http" or stage != "fetch":
            return False
        return _has_capability(capabilities, stage) or _has_capability(capabilities, "public_http")
    if engine == "rust":
        return stage == "process" and (
            _has_capability(capabilities, "process")
            or _has_capability(capabilities, "normalize")
            or _has_capability(capabilities, "security_preflight")
        )
    return False


def _default_chain(stage: str, source_kind: str, workload: str) -> list[str]:
    if stage == "discovery":
        # URL/query discovery belongs to the Python control plane. Go only
        # fetches URLs that discovery has already found and authorized.
        return ["python"]
    if stage == "fetch":
        if source_kind == "public_http" and workload in {"medium", "large"}:
            return ["go", "python"]
        return ["python"]
    if stage == "process":
        return ["rust", "python"] if workload == "large" else ["python", "rust"]
    return ["python"]


def _preferred_chain(engine_mode: str, default: Sequence[str]) -> list[str]:
    if engine_mode in {"auto", "hybrid"}:
        return list(default)
    return [engine_mode, *[engine for engine in default if engine != engine_mode]]


def _stage_contracts(engine: str, stage: str) -> tuple[str, str]:
    if engine == "go":
        return "top50-collector/v1", "top50-collector-result/v1"
    if engine == "rust":
        return "top50-processor/v1", "top50-processor-result/v1"
    if stage == "rank":
        return "top50-research-bundle/v1", "top50-ranking-summary/v1"
    if stage == "curate":
        return "top50-raw-processed-bundle/v1", "top50-curator-accepted-bundle/v1"
    if stage == "extraction":
        return "top50-raw-fetch-bundle/v1", "top50-extraction-result/v1"
    return "top50-python-orchestration/v1", "top50-python-orchestration-result/v1"


def _stage_command(
    engine: str,
    stage: str,
    evidence: Mapping[str, Any],
    request: Mapping[str, Any],
    role: str,
) -> tuple[list[str], str | None, str]:
    """Return argv, output path, and execution mode for a selected stage."""
    base = evidence.get("base_command", [])
    if not isinstance(base, list) or not base or any(not isinstance(item, str) for item in base):
        return [], None, "orchestrated"
    run_dir = Path(str(request.get("run_dir", Path("router-runs") / str(request["run_id"]))))
    suffix = "validator" if role == "validator" else "primary"
    if engine == "go":
        binding = request.get("public_http_binding")
        if not isinstance(binding, Mapping):
            return [], None, "orchestrated"
        input_path = Path(str(binding["manifest_path"]))
        output_path = run_dir / f"go-collector-{suffix}-result.json"
        artifacts = run_dir / f"go-artifacts-{suffix}"
        checkpoint = run_dir / f"go-collector-{suffix}.checkpoint.json"
        command = [
            *base,
            "collect",
            "--input",
            str(input_path),
            "--expected-input-sha256",
            str(binding["manifest_artifact_sha256"]),
            "--output",
            str(output_path),
            "--artifacts",
            str(artifacts),
            "--checkpoint",
            str(checkpoint),
        ]
        return command, str(output_path), "subprocess"
    if engine == "rust":
        input_path = run_dir / "rust-processor-input.json"
        output_path = run_dir / f"rust-processor-{suffix}-result.json"
        return [*base, "process", "--input", str(input_path), "--output", str(output_path)], str(output_path), "subprocess"
    if stage in {"extraction", "curate"}:
        return [], None, "orchestrated"
    if stage == "rank":
        output_dir = run_dir / ("ranking-output-validator" if role == "validator" else "ranking-output")
        command = [
            *base,
            "--input",
            str(run_dir / "candidates.json"),
            "--manifest",
            str(run_dir / "run_manifest.json"),
            "--queries",
            str(run_dir / "queries.tsv"),
            "--sources",
            str(run_dir / "sources.tsv"),
            "--evidence-cards",
            str(run_dir / "evidence_cards.tsv"),
            "--platform-coverage",
            str(run_dir / "platform_coverage.tsv"),
            "--lineage-manifest",
            str(run_dir / "rank-input-manifest.json"),
            "--curator-acceptance",
            str(run_dir / "curate-result.json"),
            "--output-dir",
            str(output_dir),
            "--top",
            str(request.get("top_n", 50)),
        ]
        return command, str(output_dir / "run_summary.json"), "subprocess"
    # Discovery/fetch/process are orchestrated by Python through platform CLIs,
    # browser sessions, and the reviewed bundle.  The ranker probe deliberately
    # does not pretend that rank_candidates.py is itself a network collector.
    return [], None, "orchestrated"


def _candidate_rows(request: Mapping[str, Any], probes: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    requested_stages = REQUEST_STAGES if request["stage"] == "full" else (request["stage"],)
    rows = []
    for engine in ENGINES:
        evidence = probes[engine]
        eligible = [
            stage
            for stage in requested_stages
            if evidence["ready"]
            and _engine_supports_stage(engine, stage, str(request["source_kind"]), evidence["capabilities"])
        ]
        rows.append(
            {
                "engine": engine,
                "ready": bool(evidence["ready"]),
                "version": evidence.get("version"),
                "contract": evidence.get("contract"),
                "capabilities": list(evidence.get("capabilities", [])),
                "eligible_stages": eligible,
                "reason": evidence.get("reason"),
            }
        )
    return rows


def build_plan(payload: Any, *, probes: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Build a deterministic capability plan from request and real probe evidence."""
    request = validate_request(payload)
    if probes is None:
        probe_bundle = probe_all(request["engine_paths"])
        raw_probes: Mapping[str, Mapping[str, Any]] = probe_bundle["engines"]
    else:
        raw_probes = probes
    if set(raw_probes) != set(ENGINES):
        raise RouterError("probe evidence must contain exactly python, go, and rust")
    normalized = {engine: _normalize_probe(engine, raw_probes[engine]) for engine in ENGINES}

    requested_stages = list(REQUEST_STAGES) if request["stage"] == "full" else [request["stage"]]
    if "process" in requested_stages:
        requested_stages.insert(requested_stages.index("process"), "extraction")
    if "rank" in requested_stages:
        requested_stages.insert(requested_stages.index("rank"), "curate")
    reason_codes: list[str] = []
    if request["source_kind"] in {"platform_cli", "browser_session"}:
        reason_codes.append("source_requires_python_orchestration")
    if (
        request["stage"] == "full"
        and request["workload"] == "large"
        and request["source_kind"] == "public_http"
        and request["engine_mode"] in {"auto", "hybrid"}
    ):
        reason_codes.append("auto_hybrid_large_public_http")

    stages: list[dict[str, Any]] = []
    fallbacks: list[dict[str, Any]] = []
    for stage in requested_stages:
        default = _default_chain(stage, request["source_kind"], request["workload"])
        chain = _preferred_chain(request["engine_mode"], default)
        preferred = request["engine_mode"] if request["engine_mode"] in ENGINES else None
        if stage in {"extraction", "curate"}:
            # Extraction and curator acceptance are evidence gates owned by the
            # Python control plane; a language engine_mode cannot bypass it.
            chain = ["python"]
            preferred = None
        elif preferred and not normalized[preferred]["ready"]:
            raise RouterError(f"forced engine {preferred} is unavailable for stage {stage}")
        if preferred and normalized[preferred]["ready"] and not _engine_supports_stage(
            preferred, stage, request["source_kind"], normalized[preferred]["capabilities"]
        ):
            raise RouterError(f"forced engine {preferred} cannot satisfy stage {stage}")

        selected = None
        for engine in chain:
            evidence = normalized[engine]
            if evidence["ready"] and _engine_supports_stage(
                engine, stage, request["source_kind"], evidence["capabilities"]
            ):
                selected = engine
                break
        if selected is None:
            raise RouterError(f"no ready engine can satisfy stage {stage}; fallback chain: {' -> '.join(chain)}")
        if preferred:
            reason_codes.append(f"explicit_engine_mode_{preferred}")
        elif stage not in {"extraction", "curate"} and chain and selected != chain[0]:
            reason_codes.append(f"auto_fallback_{chain[0]}_to_{selected}")
        input_contract, output_contract = _stage_contracts(selected, stage)
        command, output_path, execution_mode = _stage_command(selected, stage, normalized[selected], request, "primary")
        step = {
            "id": f"{stage}-primary",
            "stage": stage,
            "engine": selected,
            "role": "primary",
            "input_contract": input_contract,
            "output_contract": output_contract,
            "execution_mode": execution_mode,
            "command": command,
            "timeout_seconds": request["timeout_seconds"],
            "fallback_chain": chain,
        }
        if output_path:
            step["output_path"] = output_path
        if selected == "go" and stage == "fetch":
            step["input_binding"] = dict(request["public_http_binding"])
        if stage == "rank":
            run_dir = Path(str(request.get("run_dir", Path("router-runs") / str(request["run_id"]))))
            curator_path = run_dir / "curate-result.json"
            step["gate"] = {
                "type": "curator_acceptance",
                "path": str(curator_path),
                "contract": "top50-curator-acceptance/v1",
                "required_status": "accepted",
                "run_id": request["run_id"],
                "stage": "curate",
                "fail_closed": True,
            }
        if execution_mode == "orchestrated":
            run_dir = Path(str(request.get("run_dir", Path("router-runs") / str(request["run_id"]))))
            completion_contract = STAGE_COMPLETION_CONTRACTS[stage]
            step["completion_artifact"] = {
                "path": str(run_dir / f"{stage}-result.json"),
                "contract": completion_contract,
                "required_status": "accepted" if stage == "curate" else "complete",
                "run_id": request["run_id"],
                "stage": stage,
            }
        if stage == "process":
            run_dir = Path(str(request.get("run_dir", Path("router-runs") / str(request["run_id"]))))
            step["gate"] = {
                "type": "stage_artifact",
                "path": str(run_dir / "extraction-result.json"),
                "contract": "top50-extraction-result/v1",
                "required_status": "complete",
                "run_id": request["run_id"],
                "stage": "extraction",
                "fail_closed": True,
            }
        stages.append(step)
        fallbacks.append(
            {
                "stage": stage,
                "chain": chain,
                "selected": selected,
                "unavailable": [engine for engine in chain if not normalized[engine]["ready"]],
            }
        )

    effective_dual = bool(request["dual_run"])
    dual_reason = "dual_run_independent_validation" if request["dual_run"] else "high_risk_independent_validation"
    wants_validation = bool(request["dual_run"] or request["risk"] == "high")
    if wants_validation:
        target = None
        validator = None
        for stage_name in ("process", "fetch", "discovery", "rank"):
            primary = next((step for step in stages if step["stage"] == stage_name and step["role"] == "primary"), None)
            if primary is None:
                continue
            for engine in primary["fallback_chain"]:
                if (
                    engine != primary["engine"]
                    and normalized[engine]["ready"]
                    and _engine_supports_stage(
                        engine, stage_name, request["source_kind"], normalized[engine]["capabilities"]
                    )
                ):
                    target, validator = primary, engine
                    break
            if target:
                break
        if target and validator:
            input_contract, output_contract = _stage_contracts(validator, target["stage"])
            command, output_path, execution_mode = _stage_command(
                validator, target["stage"], normalized[validator], request, "validator"
            )
            validation_step = {
                "id": f"{target['stage']}-validator",
                "stage": target["stage"],
                "engine": validator,
                "role": "validator",
                "input_contract": input_contract,
                "output_contract": output_contract,
                "execution_mode": execution_mode,
                "command": command,
                "timeout_seconds": request["timeout_seconds"],
                "fallback_chain": [validator],
                "validates_step": target["id"],
            }
            if output_path:
                validation_step["output_path"] = output_path
            if validator == "go" and target["stage"] == "fetch":
                validation_step["input_binding"] = dict(request["public_http_binding"])
            if execution_mode == "orchestrated":
                run_dir = Path(
                    str(request.get("run_dir", Path("router-runs") / str(request["run_id"])))
                )
                validation_step["completion_artifact"] = {
                    "path": str(run_dir / f"{target['stage']}-validator-result.json"),
                    "contract": STAGE_COMPLETION_CONTRACTS[target["stage"]],
                    "required_status": "complete",
                    "run_id": request["run_id"],
                    "stage": target["stage"],
                }
            target_index = stages.index(target)
            stages.insert(target_index + 1, validation_step)
            effective_dual = True
            reason_codes.append(dual_reason)
        elif request["dual_run"]:
            raise RouterError("dual_run requested but no independent ready validator can satisfy the stage")
        else:
            reason_codes.append("high_risk_dual_validation_unavailable")

    selected_engines: list[str] = []
    for step in stages:
        if step["engine"] not in selected_engines:
            selected_engines.append(step["engine"])
    if request["engine_mode"] in ENGINES:
        forced = request["engine_mode"]
        for capability in request["required_capabilities"]:
            if forced in selected_engines and not _has_capability(normalized[forced]["capabilities"], capability):
                raise RouterError(f"forced engine {forced} cannot satisfy required capability {capability}")
    missing_capabilities = [
        capability
        for capability in request["required_capabilities"]
        if not any(_has_capability(normalized[engine]["capabilities"], capability) for engine in selected_engines)
    ]
    if missing_capabilities:
        raise RouterError(f"required capabilities cannot be satisfied: {', '.join(missing_capabilities)}")

    handoffs: list[dict[str, Any]] = []
    for previous, following in zip(stages, stages[1:]):
        handoff = {
            "from_step": previous["id"],
            "to_step": following["id"],
            "preserve_raw_results": following["stage"] in {"extraction", "curate"},
            "fail_closed": following["stage"] in {"process", "rank"},
        }
        if following["stage"] == "process":
            handoff["required_status"] = "complete"
        if following["stage"] == "rank":
            handoff["required_status"] = "accepted"
        handoffs.append(handoff)

    return {
        "schema": PLAN_SCHEMA,
        "run_id": request["run_id"],
        "created_at": _now(),
        "request": request,
        "candidates": _candidate_rows(request, normalized),
        "selected_engines": selected_engines,
        "stages": stages,
        "fallbacks": fallbacks,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "probe_evidence": normalized,
        "dual_run": effective_dual,
        "handoffs": handoffs,
        "pause_conditions": [
            "unaccepted evidence",
            "missing curator acceptance artifact",
            "curator acceptance contract mismatch",
        ],
    }


def _validate_plan(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise RouterError(f"plan schema must be {PLAN_SCHEMA}")
    unknown_plan_fields = sorted(set(plan) - PLAN_FIELDS)
    if unknown_plan_fields:
        raise RouterError(f"plan has unknown fields: {', '.join(unknown_plan_fields)}")
    missing_plan_fields = sorted(PLAN_REQUIRED_FIELDS - set(plan))
    if missing_plan_fields:
        raise RouterError(f"plan is missing fields: {', '.join(missing_plan_fields)}")
    if not _is_nonempty_string(plan.get("run_id")):
        raise RouterError("plan run_id must be a non-empty string")
    request = validate_request(plan.get("request"))
    if request["run_id"] != plan["run_id"]:
        raise RouterError("plan request run_id must match plan run_id")
    probes = plan.get("probe_evidence")
    if not isinstance(probes, dict) or set(probes) != set(ENGINES):
        raise RouterError("plan probe_evidence must contain exactly python, go, and rust")
    for engine, evidence in probes.items():
        if engine not in ENGINES or not isinstance(evidence, Mapping):
            raise RouterError("plan probe_evidence has an invalid engine")
        if evidence.get("engine") != engine:
            raise RouterError(f"plan probe identity mismatch for {engine}")
        expected_id = EXPECTED_ENGINE_IDS.get(engine, "python-ranker")
        if evidence.get("engine_id") not in {None, expected_id}:
            raise RouterError(f"plan probe identity mismatch for {engine}")
        if evidence.get("contract") not in {None, EXPECTED_PROBE_CONTRACTS[engine]}:
            raise RouterError(f"plan probe contract mismatch for {engine}")
    default_commands = _default_engine_commands(
        Path(__file__).resolve().parents[1], request.get("engine_paths", {})
    )
    expected_bases = {
        "python": _path_command(Path(default_commands["python"])),
        "go": list(default_commands["go"]),
        "rust": list(default_commands["rust"]),
    }
    for engine, evidence in probes.items():
        if evidence.get("base_command") != expected_bases[engine]:
            raise RouterError(f"plan probe base_command does not match request engine_paths for {engine}")

    canonical_artifacts: dict[tuple[str, str], dict[str, Any]] = {}
    canonical_request_stages = list(REQUEST_STAGES) if request["stage"] == "full" else [request["stage"]]
    if "process" in canonical_request_stages:
        canonical_request_stages.insert(canonical_request_stages.index("process"), "extraction")
    if "rank" in canonical_request_stages:
        canonical_request_stages.insert(canonical_request_stages.index("rank"), "curate")
    run_dir = Path(str(request.get("run_dir", Path("router-runs") / str(request["run_id"]))))
    for stage_name in canonical_request_stages:
        if stage_name in STAGE_COMPLETION_CONTRACTS:
            canonical_artifacts[(stage_name, "completion")] = {
                "path": str(run_dir / f"{stage_name}-result.json"),
                "contract": STAGE_COMPLETION_CONTRACTS[stage_name],
                "required_status": "accepted" if stage_name == "curate" else "complete",
                "run_id": request["run_id"],
                "stage": stage_name,
            }
    canonical_artifacts[("process", "gate")] = {
        "type": "stage_artifact", "path": str(run_dir / "extraction-result.json"),
        "contract": "top50-extraction-result/v1", "required_status": "complete",
        "run_id": request["run_id"], "stage": "extraction", "fail_closed": True,
    }
    canonical_artifacts[("rank", "gate")] = {
        "type": "curator_acceptance", "path": str(run_dir / "curate-result.json"),
        "contract": "top50-curator-acceptance/v1", "required_status": "accepted",
        "run_id": request["run_id"], "stage": "curate", "fail_closed": True,
    }

    stages = plan.get("stages")
    if not isinstance(stages, list) or not stages:
        raise RouterError("plan stages must be a non-empty array")
    for index, step in enumerate(stages):
        if not isinstance(step, dict):
            raise RouterError(f"plan stage {index} must be an object")
        unknown_step_fields = sorted(set(step) - STEP_FIELDS)
        if unknown_step_fields:
            raise RouterError(
                f"plan stage {index} has unknown fields: {', '.join(unknown_step_fields)}"
            )
        missing_step_fields = sorted(STEP_REQUIRED_FIELDS - set(step))
        if missing_step_fields:
            raise RouterError(
                f"plan stage {index} is missing fields: {', '.join(missing_step_fields)}"
            )
        if step.get("stage") not in PLAN_STAGES or step.get("engine") not in ENGINES:
            raise RouterError(f"plan stage {index} has an invalid stage or engine")
        if step.get("role") not in {"primary", "validator"}:
            raise RouterError(f"plan stage {index} has an invalid role")
        mode = step.get("execution_mode", "subprocess")
        command = step.get("command")
        if mode == "subprocess" and (
            not isinstance(command, list)
            or not command
            or any(not _is_nonempty_string(item) for item in command)
        ):
            raise RouterError(f"plan stage {index} command must be a non-empty argv array")
        if mode not in {"subprocess", "orchestrated", "covered"}:
            raise RouterError(f"plan stage {index} has an invalid execution_mode")
        timeout = step.get("timeout_seconds", DEFAULT_EXECUTION_TIMEOUT)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 3600:
            raise RouterError(f"plan stage {index} timeout_seconds is invalid")
        if not _is_nonempty_string(step.get("output_contract")):
            raise RouterError(f"plan stage {index} output_contract is required")
        if step.get("id") != f"{step['stage']}-{step['role']}":
            raise RouterError(f"plan stage {index} id does not match stage and role")
        fallback_chain = _unique_strings(step.get("fallback_chain"))
        if not fallback_chain or step["engine"] not in fallback_chain:
            raise RouterError(f"plan stage {index} has an invalid fallback chain")
        expected_input, expected_output = _stage_contracts(step["engine"], step["stage"])
        allowed_outputs = {expected_output}
        if mode == "orchestrated" and isinstance(step.get("completion_artifact"), dict):
            allowed_outputs.add(step["completion_artifact"]["contract"])
        if step.get("input_contract") != expected_input or step.get("output_contract") not in allowed_outputs:
            raise RouterError(f"plan stage {index} has a contract mismatch")
        expected_input_binding = (
            request.get("public_http_binding")
            if step.get("engine") == "go" and step.get("stage") == "fetch"
            else None
        )
        if step.get("input_binding") != expected_input_binding:
            raise RouterError(f"plan stage {index} input_binding was not canonically generated")
        if step.get("engine") == "rust" and step.get("stage") == "process":
            if _command_flag_value(command, "--expected-input-sha256") is not None:
                raise RouterError(
                    "Rust expected input digest is a runtime-only binding"
                )
        gate = step.get("gate")
        if gate is not None:
            if isinstance(gate, dict) and set(gate) - GATE_FIELDS:
                raise RouterError(f"plan stage {index} gate has unknown fields")
            valid_gate = (
                isinstance(gate, dict)
                and gate.get("type") in {"curator_acceptance", "stage_artifact"}
                and _is_nonempty_string(gate.get("contract"))
                and _is_nonempty_string(gate.get("required_status"))
                and _is_nonempty_string(gate.get("path"))
                and gate.get("run_id") == plan["run_id"]
                and gate.get("fail_closed") is True
            )
            if isinstance(gate, dict) and gate.get("type") == "curator_acceptance":
                valid_gate = (
                    valid_gate
                    and gate.get("contract") == "top50-curator-acceptance/v1"
                    and gate.get("required_status") == "accepted"
                    and gate.get("stage") == "curate"
                )
            if isinstance(gate, dict) and gate.get("type") == "stage_artifact":
                valid_gate = (
                    valid_gate
                    and gate.get("contract") == "top50-extraction-result/v1"
                    and gate.get("required_status") == "complete"
                    and gate.get("stage") == "extraction"
                )
            if isinstance(gate, dict) and "artifact_sha256" in gate:
                digest = gate.get("artifact_sha256")
                valid_gate = valid_gate and isinstance(digest, str) and len(digest) == 64 and all(
                    char in "0123456789abcdef" for char in digest
                )
            if not valid_gate:
                raise RouterError(f"plan stage {index} has an invalid stage gate")
        completion = step.get("completion_artifact")
        if isinstance(completion, dict) and set(completion) - COMPLETION_FIELDS:
            raise RouterError(f"plan stage {index} completion artifact has unknown fields")
        if completion is not None and (
            mode != "orchestrated"
            or not isinstance(completion, dict)
            or not _is_nonempty_string(completion.get("path"))
            or not _is_nonempty_string(completion.get("contract"))
            or completion.get("required_status") not in {"complete", "accepted"}
            or completion.get("run_id") != plan["run_id"]
            or completion.get("stage") != step.get("stage")
        ):
            raise RouterError(f"plan stage {index} has an invalid completion artifact contract")

        expected_command, expected_output_path, expected_mode = _stage_command(
            str(step["engine"]),
            str(step["stage"]),
            probes[str(step["engine"])],
            request,
            str(step["role"]),
        )
        if (
            step.get("execution_mode") != expected_mode
            or step.get("command") != expected_command
            or step.get("output_path") != expected_output_path
        ):
            raise RouterError(
                f"plan stage {index} command, output_path, or execution_mode was not canonically generated"
            )
        if expected_mode == "covered":
            raise RouterError("covered execution requires a separately verified artifact contract")
        if expected_mode == "orchestrated":
            expected_completion = dict(canonical_artifacts[(str(step["stage"]), "completion")])
            if step.get("role") == "validator":
                expected_completion["path"] = str(run_dir / f"{step['stage']}-validator-result.json")
                expected_completion["contract"] = STAGE_COMPLETION_CONTRACTS[str(step["stage"])]
            if step.get("completion_artifact") != expected_completion:
                raise RouterError(f"plan stage {index} completion artifact was not canonically generated")
        elif step.get("completion_artifact") is not None:
            raise RouterError(f"plan stage {index} has an unexpected completion artifact")
        if step.get("stage") in {"process", "rank"} and step.get("role") == "primary":
            expected_gate = canonical_artifacts[(str(step["stage"]), "gate")]
            actual_gate = step.get("gate")
            if not isinstance(actual_gate, dict):
                raise RouterError(f"plan stage {index} is missing its canonical gate")
            gate_without_optional_digest = {
                key: value for key, value in actual_gate.items() if key != "artifact_sha256"
            }
            if gate_without_optional_digest != expected_gate:
                raise RouterError(f"plan stage {index} gate was not canonically generated")
        elif step.get("gate") is not None:
            raise RouterError(f"plan stage {index} has an unexpected gate")

    stage_names = [step["stage"] for step in stages if step["role"] == "primary"]
    expected_stage_names = list(REQUEST_STAGES) if request["stage"] == "full" else [request["stage"]]
    if "process" in expected_stage_names:
        expected_stage_names.insert(expected_stage_names.index("process"), "extraction")
    if "rank" in expected_stage_names:
        expected_stage_names.insert(expected_stage_names.index("rank"), "curate")
    covered_prefixes = {
        "process": (["process"], ["extraction", "process"]),
        "rank": (["rank"], ["curate", "rank"]),
    }
    permitted_topologies = covered_prefixes.get(request["stage"], (expected_stage_names,))
    if stage_names not in permitted_topologies:
        raise RouterError("plan stage topology does not match the request")
    for step in stages:
        if (
            step["stage"] == "process"
            and step["role"] == "primary"
            and "extraction" in stage_names
            and step.get("execution_mode") != "covered"
            and not step.get("gate")
        ):
            raise RouterError("process stage requires the extraction gate")
        if (
            step["stage"] == "rank"
            and step["role"] == "primary"
            and "curate" in stage_names
            and step.get("execution_mode") != "covered"
            and not step.get("gate")
        ):
            raise RouterError("rank stage requires the curator acceptance gate")
    validators = [step for step in stages if step["role"] == "validator"]
    if bool(validators) != bool(plan.get("dual_run")):
        raise RouterError("plan validators must match dual_run")
    for validator in validators:
        primary_id = f"{validator['stage']}-primary"
        if validator.get("validates_step") != primary_id:
            raise RouterError("validator must identify its primary step")
        primary_index = next(
            (index for index, step in enumerate(stages) if step.get("id") == primary_id), None
        )
        validator_index = stages.index(validator)
        if primary_index is None or validator_index != primary_index + 1:
            raise RouterError("validator must immediately follow its primary step")
        primary = stages[primary_index]
        if validator["engine"] == primary["engine"]:
            raise RouterError("validator engine must be independent from its primary")
        if validator.get("command") == primary.get("command"):
            raise RouterError("validator command must be independent from its primary")
        if validator.get("output_path") and validator.get("output_path") == primary.get("output_path"):
            raise RouterError("validator output_path must be independent from its primary")
    validated_primary_ids = [validator.get("validates_step") for validator in validators]
    if len(validated_primary_ids) != len(set(validated_primary_ids)):
        raise RouterError("each primary may have at most one validator")

    selected = plan.get("selected_engines")
    actual_selected = list(dict.fromkeys(step["engine"] for step in stages))
    if selected != actual_selected:
        raise RouterError("selected_engines does not match plan stages")
    for engine in actual_selected:
        evidence = probes[engine]
        expected_id = EXPECTED_ENGINE_IDS.get(engine, "python-ranker")
        capabilities = _unique_strings(evidence.get("capabilities"))
        if (
            evidence.get("ready") is not True
            or evidence.get("engine_id") != expected_id
            or evidence.get("contract") != EXPECTED_PROBE_CONTRACTS[engine]
            or not _is_nonempty_string(evidence.get("version"))
            or capabilities is None
            or not capabilities
        ):
            raise RouterError(f"selected engine {engine} has incomplete probe evidence")
    for step in stages:
        evidence = probes[step["engine"]]
        capabilities = evidence["capabilities"]
        if not _engine_supports_stage(
            step["engine"], step["stage"], request["source_kind"], capabilities
        ):
            raise RouterError(
                f"selected engine {step['engine']} probe does not support stage {step['stage']}"
            )
    fallback_rows = plan.get("fallbacks")
    if isinstance(fallback_rows, list) and fallback_rows:
        primary_steps = [step for step in stages if step["role"] == "primary"]
        if len(fallback_rows) != len(primary_steps):
            raise RouterError("fallback rows do not match primary stages")
        for row, step in zip(fallback_rows, primary_steps):
            if (
                not isinstance(row, dict)
                or row.get("stage") != step["stage"]
                or row.get("chain") != step["fallback_chain"]
                or row.get("selected") != step["engine"]
            ):
                raise RouterError("fallback evidence does not match plan stages")
    return dict(plan)


def _contract_of(payload: Mapping[str, Any]) -> Any:
    return payload.get("contract_version", payload.get("contract", payload.get("schema")))


def _load_execution_output(step: Mapping[str, Any], stdout: str) -> dict[str, Any]:
    candidates: list[tuple[str, str]] = []
    parsed_candidates: list[tuple[str, dict[str, Any]]] = []
    if stdout.strip():
        candidates.append(("stdout", stdout))
    output_path = step.get("output_path")
    if _is_nonempty_string(output_path):
        path = Path(str(output_path))
        if path.is_file():
            candidates.append(("output_path", path.read_text(encoding="utf-8")))
    if not candidates:
        raise RouterError("engine produced no JSON output on stdout or output_path")
    last_error = None
    for source, value in candidates:
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            last_error = f"{source}: {exc}"
            continue
        if not isinstance(parsed, dict):
            last_error = f"{source}: root is not an object"
            continue
        # rank_candidates writes a summary rather than an engine envelope. The
        # router makes that adapter contract explicit before comparing the two
        # possible transport representations.
        if step["output_contract"] == "top50-ranking-summary/v1" and "requested_top_n" in parsed:
            summary = {
                key: item for key, item in parsed.items() if key != "topic"
            }
            parsed = {
                "contract_version": "top50-ranking-summary/v1",
                "engine_id": "python-ranker",
                "run_id": step.get("run_id"),
                "stage": "rank",
                "status": "complete",
                "summary": summary,
            }
        parsed_candidates.append((source, parsed))
    if not parsed_candidates:
        raise RouterError(f"engine output is not valid JSON ({last_error or 'unknown error'})")
    if len(parsed_candidates) != len(candidates):
        raise RouterError(f"engine output is not valid JSON ({last_error or 'one source is invalid'})")
    canonical = {
        source: _canonical_json_sha256(parsed) for source, parsed in parsed_candidates
    }
    if len(set(canonical.values())) != 1:
        raise RouterError("stdout and output_path JSON results do not match")
    # The atomic output artifact is the downstream fact source whenever the
    # native engine produced one; stdout is only a matching transport copy.
    return dict(parsed_candidates[-1][1])


def _semantic_payload(value: Any, *, root: bool = True) -> Any:
    volatile = {
        "contract",
        "contract_version",
        "schema",
        "engine",
        "engine_id",
        "engine_version",
        "stage",
        "generated_at",
        "created_at",
        "started_at",
        "finished_at",
        "completed_at",
        "duration_ms",
        "result_digest_sha256",
        "semantic_digest",
        "status",
    }
    if isinstance(value, dict):
        return {
            key: _semantic_payload(item, root=False)
            for key, item in sorted(value.items())
            if not root or key not in volatile
        }
    if isinstance(value, list):
        return [_semantic_payload(item, root=False) for item in value]
    return value


def semantic_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(_semantic_payload(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_json_sha256(payload: Mapping[str, Any], *, omit: Iterable[str] = ()) -> str:
    material = {key: value for key, value in payload.items() if key not in set(omit)}
    canonical = json.dumps(
        material, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _canonical_value_sha256(value: Any) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _command_flag_value(command: Sequence[str], flag: str) -> str | None:
    positions = [index for index, item in enumerate(command) if item == flag]
    if len(positions) != 1 or positions[0] + 1 >= len(command):
        return None
    value = command[positions[0] + 1]
    return value if _is_nonempty_string(value) else None


def _read_go_manifest(
    step: Mapping[str, Any],
) -> tuple[tuple[dict[str, dict[str, Any]], dict[str, Any]] | None, str | None]:
    input_path = _command_flag_value(step.get("command", []), "--input")
    if input_path is None:
        return None, "Go collect command must contain exactly one --input path"
    try:
        manifest = _read_json(Path(input_path))
    except RouterError as exc:
        return None, str(exc)
    if not isinstance(manifest, dict) or manifest.get("run_id") != step.get("run_id"):
        return None, "Go manifest run_id does not match the plan"
    jobs = manifest.get("jobs")
    if not _is_array_of_objects(jobs) or not jobs:
        return None, "Go manifest jobs must be a non-empty array"
    identities: dict[str, dict[str, Any]] = {}
    for job in jobs:
        job_id = job.get("job_id")
        if not _is_nonempty_string(job_id) or job_id in identities:
            return None, "Go manifest job_id values must be non-empty and unique"
        identities[str(job_id)] = job
    return (identities, manifest), None


def _validate_go_input_binding(step: Mapping[str, Any]) -> str | None:
    binding = step.get("input_binding")
    if not isinstance(binding, Mapping):
        return "Go step is missing its public HTTP input binding"
    input_path = _command_flag_value(step.get("command", []), "--input")
    expected_digest = _command_flag_value(
        step.get("command", []), "--expected-input-sha256"
    )
    if (
        input_path != binding.get("manifest_path")
        or expected_digest != binding.get("manifest_artifact_sha256")
    ):
        return "Go command does not match its frozen input binding"
    fingerprint = _sha256_file(Path(str(input_path))) if input_path else None
    if fingerprint is None or fingerprint[1] != binding.get("manifest_artifact_sha256"):
        return "Go manifest artifact SHA-256 does not match the plan"
    try:
        manifest = _read_json(Path(str(input_path)))
    except RouterError as exc:
        return str(exc)
    if not isinstance(manifest, dict):
        return "Go manifest must be a JSON object"
    jobs = manifest.get("jobs")
    if not _is_array_of_objects(jobs):
        return "Go manifest jobs must be an array of objects"
    ordered_jobs = sorted(jobs, key=lambda row: str(row.get("job_id", "")))
    if len(ordered_jobs) != binding.get("job_count"):
        return "Go manifest job count does not match the plan"
    if _canonical_value_sha256(ordered_jobs) != binding.get("job_set_sha256"):
        return "Go manifest job set digest does not match the plan"
    return None


def _sha256_file(path: Path) -> tuple[int, str] | None:
    """Hash one regular, non-symlink file from a single open descriptor."""
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                return None
            digest = hashlib.sha256()
            size = 0
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
            after = os.fstat(handle.fileno())
    except (OSError, ValueError):
        return None
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ) or size != after.st_size:
        return None
    return size, digest.hexdigest()


def _header_value(headers: Mapping[str, Any], name: str) -> str:
    for key, value in headers.items():
        if isinstance(key, str) and key.casefold() == name.casefold():
            return value if isinstance(value, str) else ""
    return ""


def _stable_item_diff(
    primary: Mapping[str, Any], validator: Mapping[str, Any]
) -> dict[str, Any] | None:
    collections = (
        ("processed_candidates", "candidate_id"),
        ("candidates", "candidate_id"),
        ("ranked_candidates", "candidate_id"),
        ("results", "job_id"),
        ("items", "candidate_id"),
        ("items", "job_id"),
    )
    for field, identity in collections:
        left_items = primary.get(field)
        right_items = validator.get(field)
        if not _is_array_of_objects(left_items) or not _is_array_of_objects(right_items):
            continue
        if any(not _is_nonempty_string(item.get(identity)) for item in [*left_items, *right_items]):
            continue
        left = {str(item[identity]): item for item in left_items}
        right = {str(item[identity]): item for item in right_items}
        changed = []
        for identifier in sorted(set(left) & set(right)):
            left_semantic = _semantic_payload(left[identifier], root=False)
            right_semantic = _semantic_payload(right[identifier], root=False)
            if left_semantic == right_semantic:
                continue
            left_digest = hashlib.sha256(
                json.dumps(left_semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest()
            right_digest = hashlib.sha256(
                json.dumps(right_semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest()
            changed_fields = sorted(
                key
                for key in set(left[identifier]) | set(right[identifier])
                if key != identity and left[identifier].get(key) != right[identifier].get(key)
            )
            changed.append(
                {
                    "id": identifier,
                    "primary_digest": left_digest,
                    "validator_digest": right_digest,
                    "changed_fields": changed_fields,
                }
            )
        return {
            "identity_kind": identity,
            "collection": field,
            "added_ids": sorted(set(right) - set(left)),
            "removed_ids": sorted(set(left) - set(right)),
            "changed": changed,
        }
    return None


def _sorted_semantic_objects(value: Any, *, omit: Iterable[str] = ()) -> Any:
    """Canonicalize an unordered collection of business objects for comparison."""
    if not _is_array_of_objects(value):
        return value
    omitted = set(omit)
    normalized = [
        {
            key: _semantic_payload(item, root=False)
            for key, item in row.items()
            if key not in omitted
        }
        for row in value
    ]
    return sorted(
        normalized,
        key=lambda item: json.dumps(
            item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )


def _comparison_projection(payload: Mapping[str, Any], stage: str | None = None) -> Any:
    """Project the complete business result for a cross-engine stage comparison."""
    business = _semantic_payload(payload)
    if not isinstance(business, dict):
        return business
    effective_stage = stage or (str(payload["stage"]) if _is_nonempty_string(payload.get("stage")) else None)
    if effective_stage == "process":
        # Engine-local cluster/review IDs do not carry business meaning.  The
        # memberships, evidence, dispositions and counts do, and collection
        # order is not part of the cross-engine contract.
        return {
            "processed_candidates": _sorted_semantic_objects(
                business.get("processed_candidates")
            ),
            "exact_clusters": _sorted_semantic_objects(
                business.get("exact_clusters"), omit={"cluster_id"}
            ),
            "near_duplicate_reviews": _sorted_semantic_objects(
                business.get("near_duplicate_reviews"), omit={"review_id"}
            ),
            "counts": business.get("counts"),
        }
    if effective_stage == "fetch":
        return {"results": business.get("results")}
    if effective_stage == "rank":
        projection: dict[str, Any] = {"summary": business.get("summary")}
        for field in ("selected", "selected_candidates", "ranked_candidates"):
            if field in business:
                projection[field] = business[field]
        return projection
    return business


def _comparison_digest(payload: Mapping[str, Any], stage: str | None = None) -> str:
    """Hash a stage's full business projection without trusting declared hashes."""
    canonical = json.dumps(
        _comparison_projection(payload, stage),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _is_array_of_objects(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_process_business_payload(
    payload: Mapping[str, Any], *, label: str
) -> str | None:
    """Validate the process-stage invariants shared by Python and Rust."""
    try:
        validate_process_business_semantics(payload, label=label)
    except LineageError as exc:
        return str(exc)
    return None


def _validate_fetch_request_identity(
    item: Mapping[str, Any], backend_kind: str
) -> str | None:
    """Reject caller-selected HTTP identities instead of chasing bot deny-lists.

    Direct HTTP backends have one exact, transparent project identity. Managed
    adapters and browser sessions are identified by their backend/probe fields;
    they cannot smuggle an arbitrary caller-supplied User-Agent into the
    canonical fetch artifact.
    """
    request_user_agent = item.get("request_user_agent")
    if backend_kind in {"go_collector", "transparent_http"}:
        if request_user_agent != TRANSPARENT_USER_AGENT:
            return "direct HTTP fetch lacks the fixed transparent project identity"
        if (
            backend_kind == "go_collector"
            and item.get("robots_user_agent") != ROBOTS_PRODUCT_TOKEN
        ):
            return "Go fetch lacks the collector's transparent robots identity"
        return None
    if request_user_agent is not None and request_user_agent != "":
        return "managed fetch cannot declare a caller-selected user agent"
    return None


def _binding_record_ids(relation: str, payload: Mapping[str, Any]) -> list[str] | None:
    if relation == "scope_query_plan":
        rows, field = payload.get("queries"), "query_id"
    elif relation == "discovery_result":
        rows, field = payload.get("discoveries"), "discovery_id"
    elif relation == "frozen_http_manifest":
        rows, field = payload.get("jobs"), "job_id"
    elif relation == "fetch_result":
        rows, field = payload.get("results"), "job_id"
    elif relation == "extraction_result":
        rows, field = payload.get("candidates"), "candidate_id"
    elif relation == "process_result":
        rows, field = payload.get("processed_candidates"), "candidate_id"
    elif relation == "rank_input_manifest":
        rows, field = payload.get("files"), "input_id"
    else:
        return None
    if not _is_array_of_objects(rows):
        return None
    identifiers = _unique_strings([row.get(field) for row in rows])
    return sorted(identifiers) if identifiers is not None else None


def _validate_input_bindings(
    stage: str,
    payload: Mapping[str, Any],
    run_id: str,
) -> tuple[dict[str, Mapping[str, Any]] | None, str | None]:
    bindings = payload.get("input_bindings")
    relation_alternatives = STAGE_INPUT_ALTERNATIVES.get(stage)
    if relation_alternatives is None:
        return None, f"no input binding contract is registered for {stage}"
    if not isinstance(bindings, list) or not bindings:
        return None, "stage artifact input_bindings must be a non-empty array"
    by_relation: dict[str, Mapping[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or set(binding) != INPUT_BINDING_FIELDS:
            return None, "stage input binding fields are invalid"
        relation = binding.get("relation")
        allowed_relations = set().union(*relation_alternatives)
        if relation not in allowed_relations or relation in by_relation:
            return None, "stage input bindings have missing, duplicate, or unexpected relations"
        if (
            not _is_nonempty_string(binding.get("path"))
            or not _is_sha256(binding.get("artifact_sha256"))
            or not _is_nonempty_string(binding.get("contract"))
            or binding.get("run_id") != run_id
            or not _is_nonempty_string(binding.get("stage"))
            or binding.get("required_status") not in {"complete", "accepted"}
            or not _is_nonempty_string(binding.get("producer_engine_id"))
            or not _is_sha256(binding.get("result_digest_sha256"))
            or binding.get("record_kind") != RELATION_RECORD_KINDS[relation]
            or not _is_nonnegative_int(binding.get("record_count"))
            or not _is_sha256(binding.get("record_ids_sha256"))
        ):
            return None, "stage input binding metadata is invalid"
        path = Path(str(binding["path"]))
        try:
            upstream, artifact_sha256 = _read_json_artifact(path)
        except RouterError as exc:
            return None, str(exc)
        if not isinstance(upstream, Mapping):
            return None, "bound upstream artifact must be a JSON object"
        if (
            artifact_sha256 != binding["artifact_sha256"]
            or _contract_of(upstream) != binding["contract"]
            or upstream.get("run_id") != run_id
            or upstream.get("stage") != binding["stage"]
            or upstream.get("status") != binding["required_status"]
        ):
            return None, "bound upstream artifact identity or SHA-256 does not match"
        producer = upstream.get("producer")
        if (
            not isinstance(producer, Mapping)
            or producer.get("engine_id") != binding["producer_engine_id"]
        ):
            return None, "bound upstream producer identity does not match"
        declared_digest = upstream.get("result_digest_sha256")
        if (
            declared_digest != binding["result_digest_sha256"]
            or not _is_sha256(declared_digest)
            or declared_digest
            != _canonical_json_sha256(upstream, omit={"result_digest_sha256"})
        ):
            return None, "bound upstream result digest does not match"
        record_ids = _binding_record_ids(str(relation), upstream)
        if (
            record_ids is None
            or len(record_ids) != binding["record_count"]
            or _canonical_value_sha256(record_ids) != binding["record_ids_sha256"]
        ):
            return None, "bound upstream record set does not match"
        by_relation[str(relation)] = upstream
    if set(by_relation) not in relation_alternatives:
        return None, "stage input bindings do not match the fixed DAG"
    return by_relation, None


def _valid_stage_envelope(stage: str, payload: Mapping[str, Any], run_id: str) -> str | None:
    if stage not in STAGE_COMPLETION_CONTRACTS:
        return f"no stage artifact validator is registered for {stage}"
    required_status = "accepted" if stage == "curate" else "complete"
    if (
        _contract_of(payload) != STAGE_COMPLETION_CONTRACTS[stage]
        or payload.get("run_id") != run_id
        or payload.get("stage") != stage
        or payload.get("status") != required_status
    ):
        return "stage artifact contract, run_id, stage, or status is invalid"
    producer = payload.get("producer")
    if (
        not isinstance(producer, Mapping)
        or not _is_nonempty_string(producer.get("engine_id"))
        or not _is_nonempty_string(producer.get("engine_version"))
    ):
        return "stage artifact producer identity is required"
    if not isinstance(payload.get("input_bindings"), list):
        return "stage artifact input_bindings must be an array"
    if not isinstance(payload.get("counts"), Mapping):
        return "stage artifact counts must be an object"
    digest = payload.get("result_digest_sha256")
    if not _is_sha256(digest) or digest != _canonical_json_sha256(
        payload, omit={"result_digest_sha256"}
    ):
        return "stage artifact result_digest_sha256 is invalid"
    return None


def _validate_stage_artifact(
    stage: str,
    payload: Any,
    run_id: str,
    *,
    source_kind: str | None = None,
) -> str | None:
    if not isinstance(payload, Mapping):
        return "stage artifact must be a JSON object"
    envelope_error = _valid_stage_envelope(stage, payload, run_id)
    if envelope_error:
        return envelope_error
    bound_inputs, binding_error = _validate_input_bindings(stage, payload, run_id)
    if binding_error or bound_inputs is None:
        return binding_error or "stage input bindings are unavailable"

    counts = payload["counts"]
    if stage == "discovery":
        queries = payload.get("queries")
        discoveries = payload.get("discoveries")
        if not _is_array_of_objects(queries) or not _is_array_of_objects(discoveries):
            return "discovery artifact queries and discoveries must be arrays of objects"
        query_ids: set[str] = set()
        declared_discoveries: list[str] = []
        for query in queries:
            query_id = query.get("query_id")
            discovered_ids = _unique_strings(query.get("discovered_ids"))
            if (
                not _is_nonempty_string(query_id)
                or query_id in query_ids
                or discovered_ids is None
                or query.get("status") not in {"complete", "empty", "blocked", "error"}
                or not _is_nonempty_string(query.get("platform"))
                or not _is_nonempty_string(query.get("backend_id"))
                or not _is_nonempty_string(query.get("probe_id"))
                or query.get("authorization") not in {"granted", "not_required", "not_granted"}
            ):
                return "discovery query records are incomplete or invalid"
            if query.get("authorization") == "not_granted" and discovered_ids:
                return "an unauthorized discovery query cannot produce discoveries"
            query_ids.add(str(query_id))
            declared_discoveries.extend(discovered_ids)
        discovery_ids: set[str] = set()
        for item in discoveries:
            discovery_id = item.get("discovery_id")
            if (
                not _is_nonempty_string(discovery_id)
                or discovery_id in discovery_ids
                or item.get("query_id") not in query_ids
                or not all(
                    _is_nonempty_string(item.get(field))
                    for field in ("platform", "url", "canonical_url", "access_kind")
                )
            ):
                return "discovery records are incomplete or have invalid references"
            discovery_ids.add(str(discovery_id))
        if sorted(declared_discoveries) != sorted(discovery_ids):
            return "discovery IDs do not conserve the query ledger"
        if counts != {"queries": len(queries), "discoveries": len(discoveries)}:
            return "discovery counts do not match the payload"
        return None

    if stage == "fetch":
        allowed_backend_kinds = {
            "public_http": {"go_collector", "transparent_http", "reader_proxy"},
            "platform_cli": {"platform_adapter"},
            "browser_session": {"browser_session"},
        }
        if source_kind not in allowed_backend_kinds:
            return "fetch artifact source_kind is missing or invalid"
        results = payload.get("results")
        if not _is_array_of_objects(results):
            return "fetch artifact results must be an array of objects"
        seen: set[str] = set()
        success = blocked = 0
        for item in results:
            job_id = item.get("job_id")
            transport = item.get("transport_status")
            backend_kind = item.get("backend_kind")
            if (
                not _is_nonempty_string(job_id)
                or job_id in seen
                or transport
                not in {
                    "transport_success",
                    "transport_failed",
                    "blocked_by_robots",
                    "blocked_by_policy",
                }
                or item.get("content_class") != "unclassified"
                or item.get("access_kind") != source_kind
                or backend_kind not in allowed_backend_kinds[source_kind]
                or item.get("authorization")
                not in {"granted_for_current_task", "not_required"}
                or not _is_nonempty_string(item.get("probe_id"))
                or not all(
                    _is_nonempty_string(item.get(field))
                    for field in ("query_id", "platform", "url", "final_url", "backend_id")
                )
            ):
                return "fetch result identities or transport semantics are invalid"
            identity_error = _validate_fetch_request_identity(item, str(backend_kind))
            if identity_error:
                return identity_error
            seen.add(str(job_id))
            if transport == "transport_success":
                success += 1
                artifact = item.get("artifact")
                if (
                    not isinstance(artifact, Mapping)
                    or not _is_nonempty_string(artifact.get("path"))
                    or not _is_sha256(artifact.get("body_sha256"))
                    or not _is_nonnegative_int(artifact.get("bytes"))
                ):
                    return "transport success lacks a complete response artifact"
                http_status = item.get("http_status")
                if backend_kind in {"go_collector", "transparent_http"}:
                    if (
                        not isinstance(http_status, int)
                        or not 200 <= http_status <= 299
                        or item.get("robots_status")
                        not in {"allowed", "unavailable_allowed", "allowed_by_test_policy"}
                    ):
                        return "transparent HTTP success lacks HTTP or robots provenance"
                else:
                    if item.get("probe_result") != "success" or item.get(
                        "auth_state"
                    ) not in {"anonymous", "authenticated"}:
                        return "managed fetch success lacks probe or authentication provenance"
                    if http_status is not None and (
                        not isinstance(http_status, int) or not 200 <= http_status <= 299
                    ):
                        return "managed fetch reports an invalid observed HTTP status"
                    if backend_kind == "reader_proxy" and not _is_nonempty_string(
                        item.get("provider_id")
                    ):
                        return "reader proxy success requires provider provenance"
            else:
                blocked += int(transport in {"blocked_by_robots", "blocked_by_policy"})
                if not _is_nonempty_string(item.get("error_code")):
                    return "non-success fetch results require an error_code"
        if counts != {"jobs": len(results), "transport_success": success, "blocked": blocked}:
            return "fetch counts do not match the payload"
        discovery = bound_inputs.get("discovery_result")
        manifest = bound_inputs.get("frozen_http_manifest")
        if discovery is not None:
            discovered = {
                str(row["discovery_id"]): row for row in discovery["discoveries"]
            }
            if any(
                str(row["job_id"]) not in discovered
                or row["query_id"] != discovered[str(row["job_id"])]["query_id"]
                or row["platform"] != discovered[str(row["job_id"])]["platform"]
                or row["url"] != discovered[str(row["job_id"])]["canonical_url"]
                for row in results
            ):
                return "fetch jobs do not preserve the bound discovery identities"
        if manifest is not None:
            jobs = {str(row["job_id"]): row for row in manifest["jobs"]}
            if set(jobs) != seen or any(
                row["query_id"] != jobs[str(row["job_id"])]["query_id"]
                or row["platform"] != jobs[str(row["job_id"])]["platform"]
                or row["url"] != jobs[str(row["job_id"])]["url"]
                for row in results
            ):
                return "fetch jobs do not conserve the frozen HTTP manifest"
        return None

    if stage == "extraction":
        outcomes = payload.get("source_outcomes")
        candidates = payload.get("candidates")
        if not _is_array_of_objects(outcomes) or not _is_array_of_objects(candidates):
            return "extraction outcomes and candidates must be arrays of objects"
        source_classes: dict[str, str] = {}
        declared_candidate_ids: list[str] = []
        content_sources = blocked_sources = 0
        allowed_classes = {
            "content",
            "login_wall",
            "captcha",
            "challenge",
            "consent_wall",
            "paywall",
            "access_denied",
            "empty_or_incomplete",
            "unsupported_media",
            "extraction_error",
        }
        for outcome in outcomes:
            source_id = outcome.get("source_id")
            candidate_ids = _unique_strings(outcome.get("candidate_ids"))
            content_class = outcome.get("content_class")
            if (
                not _is_nonempty_string(source_id)
                or source_id in source_classes
                or content_class not in allowed_classes
                or candidate_ids is None
                or not all(
                    _is_nonempty_string(outcome.get(field))
                    for field in ("upstream_job_id", "body_sha256", "extractor_id")
                )
            ):
                return "extraction source outcomes are incomplete or invalid"
            if not _is_sha256(outcome.get("body_sha256")):
                return "extraction body digest is invalid"
            if content_class != "content" and candidate_ids:
                return "non-content extraction outcomes cannot produce candidates"
            content_sources += int(content_class == "content")
            blocked_sources += int(content_class != "content")
            source_classes[str(source_id)] = str(content_class)
            declared_candidate_ids.extend(candidate_ids)
        candidate_ids: set[str] = set()
        for candidate in candidates:
            candidate_id = candidate.get("candidate_id")
            source_id = candidate.get("source_id")
            if (
                not _is_nonempty_string(candidate_id)
                or candidate_id in candidate_ids
                or source_classes.get(str(source_id)) != "content"
                or not all(
                    _is_nonempty_string(candidate.get(field))
                    for field in (
                        "platform",
                        "url",
                        "title",
                        "author",
                        "published_at",
                        "content_type",
                        "excerpt_or_observation",
                    )
                )
            ):
                return "extraction candidates are incomplete or reference non-content outcomes"
            candidate_ids.add(str(candidate_id))
        if sorted(declared_candidate_ids) != sorted(candidate_ids):
            return "extraction candidate IDs do not conserve source outcomes"
        if counts != {
            "input_sources": len(outcomes),
            "content_sources": content_sources,
            "blocked_sources": blocked_sources,
            "candidates": len(candidates),
        }:
            return "extraction counts do not match the payload"
        upstream = bound_inputs["fetch_result"]
        expected_success_ids = {
            str(row["job_id"])
            for row in upstream["results"]
            if row["transport_status"] == "transport_success"
        }
        actual_upstream_ids = {str(row["upstream_job_id"]) for row in outcomes}
        if actual_upstream_ids != expected_success_ids:
            return "extraction outcomes do not conserve successful fetch jobs"
        return None

    if stage == "process":
        process_error = _validate_process_business_payload(
            payload, label="process artifact"
        )
        if process_error:
            return process_error
        upstream = bound_inputs["extraction_result"]
        input_ids = sorted(str(row["candidate_id"]) for row in upstream["candidates"])
        output_ids = sorted(
            str(row["candidate_id"]) for row in payload["processed_candidates"]
        )
        if input_ids != output_ids:
            return "process candidates do not conserve the extraction candidate set"
        return None

    process_result = bound_inputs["process_result"]
    process_error = _validate_process_business_payload(
        process_result, label="bound process artifact"
    )
    if process_error:
        return process_error
    process_ids = {
        str(row["candidate_id"])
        for row in process_result["processed_candidates"]
    }
    try:
        validate_curator_business_semantics(
            payload,
            expected_candidate_ids=sorted(process_ids),
            processed_candidate_ids=sorted(process_ids),
        )
    except LineageError as exc:
        return str(exc)
    rank_manifest = bound_inputs["rank_input_manifest"]
    descriptors = {
        str(row["input_id"]): row for row in rank_manifest.get("files", [])
    }
    for field, input_id in (
        ("evidence_ledger_binding", "evidence_cards"),
        ("source_ledger_binding", "sources"),
    ):
        binding = payload[field]
        descriptor = descriptors.get(input_id)
        if (
            descriptor is None
            or set(binding) != {"artifact_sha256"}
            or not _is_sha256(binding.get("artifact_sha256"))
            or binding.get("artifact_sha256") != descriptor.get("artifact_sha256")
        ):
            return f"{field} does not match the frozen rank input manifest"
    return None


def _validate_engine_result(
    step: Mapping[str, Any], payload: Mapping[str, Any], run_id: str
) -> str | None:
    """Validate native/adapted business success; a zero exit code is insufficient."""
    engine = str(step["engine"])
    stage = str(step["stage"])
    if payload.get("run_id") != run_id:
        return "engine result run_id does not match the plan"

    if engine == "go":
        if payload.get("engine_id") != "go-collector":
            return "Go result engine_id must be go-collector"
        if payload.get("status") != "complete":
            return "Go collector status must be complete"
        results = payload.get("results")
        if not _is_array_of_objects(results):
            return "Go collector results must be an array of objects"
        manifest_data, manifest_error = _read_go_manifest(step)
        if manifest_error:
            return manifest_error
        assert manifest_data is not None
        manifest_jobs, manifest = manifest_data
        artifacts_path = _command_flag_value(step.get("command", []), "--artifacts")
        if artifacts_path is None:
            return "Go collect command must contain exactly one --artifacts path"
        try:
            artifacts_root = Path(artifacts_path).resolve(strict=False)
        except (OSError, ValueError):
            return "Go artifacts path is invalid"
        result_ids: set[str] = set()
        for item in results:
            job_id = item.get("job_id")
            if (
                not _is_nonempty_string(job_id)
                or job_id in result_ids
                or item.get("status") != "transport_success"
            ):
                return "every Go result must have a job_id and transport_success status"
            result_ids.add(str(job_id))
            manifest_job = manifest_jobs.get(str(job_id))
            if manifest_job is None:
                return "Go result contains a job_id absent from the manifest"
            for field in ("query_id", "platform", "url"):
                if item.get(field) != manifest_job.get(field):
                    return f"Go result {field} does not match the manifest"
            method = manifest_job.get("method")
            if method not in {"GET", "HEAD"}:
                return "Go manifest method must be GET or HEAD"
            headers = manifest_job.get("headers")
            if not isinstance(headers, dict):
                return "Go manifest headers must be an object"
            required_strings = (
                "final_url",
                "content_type",
                "body_sha256",
                "artifact_path",
                "robots_url",
                "robots_status",
                "robots_user_agent",
                "request_accept",
                "request_accept_language",
                "request_accept_encoding",
                "response_content_language",
                "response_content_encoding",
                "response_vary",
                "robots_rule",
            )
            if any(not isinstance(item.get(field), str) for field in required_strings):
                return "Go success result is missing provenance string fields"
            if not all(
                _is_nonnegative_int(item.get(field)) for field in ("attempts", "http_status", "bytes")
            ):
                return "Go success result counters are invalid"
            if not 1 <= item["attempts"] <= manifest.get("max_attempts", 0):
                return "Go success result attempts are outside the manifest limit"
            if not 200 <= item["http_status"] <= 299:
                return "Go success result HTTP status must be 2xx"
            if not _is_nonempty_string(item["final_url"]):
                return "Go success result final_url is required"
            if item["robots_status"] not in {"allowed", "unavailable_allowed", "allowed_by_test_policy"}:
                return "Go success result robots status is not an allow decision"
            if item["robots_user_agent"] != ROBOTS_PRODUCT_TOKEN:
                return "Go success result robots user agent must match the collector identity"
            if not _is_nonempty_string(item["robots_url"]):
                return "Go success result robots URL is required"
            expected_headers = {
                "request_accept": _header_value(headers, "Accept"),
                "request_accept_language": _header_value(headers, "Accept-Language"),
                "request_accept_encoding": _header_value(headers, "Accept-Encoding"),
            }
            if any(item[field] != expected for field, expected in expected_headers.items()):
                return "Go request content-negotiation provenance does not match the manifest"
            digest = item["body_sha256"]
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                return "Go success result body_sha256 is invalid"
            artifact = Path(item["artifact_path"])
            try:
                artifact_parent = artifact.resolve(strict=False).parent
            except (OSError, ValueError):
                return "Go artifact path is invalid"
            if not artifact.is_absolute() or artifact_parent != artifacts_root or artifact.is_symlink():
                return "Go artifact path escapes the declared artifacts directory"
            artifact_fingerprint = _sha256_file(artifact)
            if artifact_fingerprint != (item["bytes"], digest):
                return "Go artifact bytes or SHA-256 do not match the result"
            if method == "HEAD" and item["bytes"] != 0:
                return "Go HEAD result must have an empty body artifact"
        if result_ids != set(manifest_jobs):
            return "Go result job set does not conserve the manifest"
        return None

    if engine == "rust":
        if payload.get("engine_id") != "rust-processor":
            return "Rust result engine_id must be rust-processor"
        process_error = _validate_process_business_payload(payload, label="Rust result")
        if process_error:
            return process_error
        runtime_binding = step.get("runtime_input_binding")
        if isinstance(runtime_binding, Mapping):
            actual_ids = sorted(
                str(candidate["candidate_id"])
                for candidate in payload["processed_candidates"]
            )
            if (
                len(actual_ids) != runtime_binding.get("candidate_count")
                or _canonical_value_sha256(actual_ids)
                != runtime_binding.get("candidate_ids_sha256")
            ):
                return "Rust result candidate set does not conserve the extraction input"
        digest = payload.get("result_digest_sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or digest != _canonical_json_sha256(payload, omit={"result_digest_sha256"})
        ):
            return "Rust result digest is missing or invalid"
        return None

    if engine == "python" and stage == "rank":
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            return "ranking result summary is required"
        if payload.get("engine_id") != "python-ranker" or payload.get("status") != "complete":
            return "ranking adapter identity or status is invalid"
        for field in ("requested_top_n", "selected_count", "rejected_count", "shortfall"):
            if not _is_nonnegative_int(summary.get(field)):
                return f"ranking summary {field} must be a non-negative integer"
        return None

    if engine == "python":
        if payload.get("engine_id") not in {"python-orchestrator", "python-ranker"}:
            return "Python result engine_id is invalid"
        if payload.get("status") not in {"complete", "accepted"}:
            return "Python result status is not successful"
        if payload.get("stage") != stage:
            return "Python result stage does not match the plan"
        return None
    return "unknown engine result"


def _execute_step(step: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    command = step["command"]
    started = time.monotonic()
    record: dict[str, Any] = {
        "id": step.get("id"),
        "stage": step["stage"],
        "engine": step["engine"],
        "role": step["role"],
        "command": list(command),
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "duration_ms": 0,
        "status": "failed",
    }
    try:
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            timeout=float(step.get("timeout_seconds", DEFAULT_EXECUTION_TIMEOUT)),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        record.update(
            {
                "error_code": "timeout",
                "stdout": _bounded(exc.stdout),
                "stderr": _bounded(exc.stderr),
                "duration_ms": _duration_ms(started),
            }
        )
        return record
    except (FileNotFoundError, PermissionError, OSError) as exc:
        record.update(
            {
                "error_code": "executable_unavailable",
                "stderr": _bounded(exc),
                "duration_ms": _duration_ms(started),
            }
        )
        return record
    record.update(
        {
            "returncode": completed.returncode,
            "stdout": _bounded(completed.stdout),
            "stderr": _bounded(completed.stderr),
            "duration_ms": _duration_ms(started),
        }
    )
    if completed.returncode != 0:
        record["error_code"] = "nonzero_exit"
        return record
    try:
        parsed = _load_execution_output(step, completed.stdout)
    except (RouterError, OSError, UnicodeError) as exc:
        record.update({"error_code": "invalid_json_output", "validation_error": str(exc)})
        return record
    if _contract_of(parsed) != step["output_contract"]:
        record.update(
            {
                "error_code": "output_contract_mismatch",
                "validation_error": (
                    f"expected {step['output_contract']}, got {_contract_of(parsed)!r}"
                ),
                "parsed_output": parsed,
            }
        )
        return record
    validation_error = _validate_engine_result(step, parsed, run_id)
    if validation_error:
        record.update(
            {
                "error_code": "invalid_engine_result",
                "validation_error": validation_error,
                "parsed_output": parsed,
            }
        )
        return record
    record.update(
        {
            "status": "complete",
            "parsed_output": parsed,
            "semantic_digest": semantic_digest(parsed),
        }
    )
    return record


def _check_stage_gate(
    step: Mapping[str, Any], source_kind: str | None = None
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    gate = step.get("gate")
    if not gate:
        return None, None, None
    started = time.monotonic()
    failure = {
        "id": step.get("id"),
        "stage": step["stage"],
        "engine": step["engine"],
        "role": step["role"],
        "command": list(step.get("command", [])),
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "duration_ms": 0,
        "status": "failed",
        "error_code": (
            "curator_acceptance_required"
            if gate.get("type") == "curator_acceptance"
            else "stage_artifact_required"
        ),
    }
    try:
        payload, actual_digest = _read_json_artifact(Path(str(gate["path"])))
    except RouterError as exc:
        failure["validation_error"] = str(exc)
        failure["duration_ms"] = _duration_ms(started)
        return failure, None, None
    if (
        not isinstance(payload, dict)
        or _contract_of(payload) != gate["contract"]
        or payload.get("status") != gate["required_status"]
        or payload.get("run_id") != gate["run_id"]
        or payload.get("stage") != gate["stage"]
    ):
        failure["validation_error"] = (
            "stage gate artifact has the wrong contract, status, run_id, or stage"
        )
        failure["duration_ms"] = _duration_ms(started)
        return failure, None, None
    validation_error = _validate_stage_artifact(
        str(gate["stage"]),
        payload,
        str(gate["run_id"]),
        source_kind=source_kind,
    )
    if validation_error:
        failure["validation_error"] = validation_error
        failure["duration_ms"] = _duration_ms(started)
        return failure, None, None
    expected_digest = gate.get("artifact_sha256")
    if expected_digest:
        if actual_digest != expected_digest:
            failure["validation_error"] = "stage gate artifact digest mismatch"
            failure["duration_ms"] = _duration_ms(started)
            return failure, None, None
    return None, payload, actual_digest


def execute_plan(payload: Any) -> dict[str, Any]:
    """Execute argv-only plan steps and validate every machine result."""
    plan = _validate_plan(payload)
    for engine in plan["selected_engines"]:
        evidence = plan["probe_evidence"][engine]
        if engine == "python":
            fresh = probe_python_engine(Path(evidence["base_command"][-1]), timeout=DEFAULT_PROBE_TIMEOUT)
        else:
            fresh = probe_external_engine(engine, evidence["base_command"], timeout=DEFAULT_PROBE_TIMEOUT)
        if (
            fresh.get("ready") is not True
            or fresh.get("engine_id") != evidence.get("engine_id")
            or fresh.get("version") != evidence.get("version")
            or fresh.get("contract") != evidence.get("contract")
            or fresh.get("capabilities") != evidence.get("capabilities")
        ):
            raise RouterError(f"fresh {engine} probe does not match the execution plan")
    executions: list[dict[str, Any]] = []
    for step in plan["stages"]:
        gate_failure, gate_payload, gate_artifact_sha256 = _check_stage_gate(
            step, str(plan["request"]["source_kind"])
        )
        if gate_failure:
            executions.append(gate_failure)
            break
        if step.get("stage") == "rank":
            if not isinstance(gate_payload, Mapping):
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "rank_input_binding_mismatch",
                        "validation_error": "rank requires a verified curator snapshot",
                    }
                )
                break
            _, rank_binding_error = _validate_rank_runtime_binding(
                step, gate_payload, str(plan["run_id"])
            )
            if rank_binding_error:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "rank_input_binding_mismatch",
                        "validation_error": rank_binding_error,
                    }
                )
                break
        if step.get("engine") == "go" and step.get("stage") == "fetch":
            input_error = _validate_go_input_binding(step)
            if input_error:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "input_binding_mismatch",
                        "validation_error": input_error,
                    }
                )
                break
        runtime_step = dict(step)
        runtime_step["run_id"] = plan["run_id"]
        if step.get("engine") == "rust" and step.get("stage") == "process":
            if not isinstance(gate_payload, Mapping) or not gate_artifact_sha256:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "input_binding_mismatch",
                        "validation_error": "Rust process requires a verified extraction snapshot",
                    }
                )
                break
            runtime_binding, input_error = _compile_rust_input_from_extraction(
                step, gate_payload, gate_artifact_sha256
            )
            if input_error or runtime_binding is None:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "input_binding_mismatch",
                        "validation_error": input_error or "Rust input binding is unavailable",
                    }
                )
                break
            runtime_step["runtime_input_binding"] = runtime_binding
            runtime_step["command"] = [
                *runtime_step["command"],
                "--expected-input-sha256",
                str(runtime_binding["artifact_sha256"]),
            ]
            runtime_digest = _command_flag_value(
                runtime_step["command"], "--expected-input-sha256"
            )
            if runtime_digest != runtime_binding["artifact_sha256"]:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "input_binding_mismatch",
                        "validation_error": "Rust runtime command does not match its compiled input binding",
                    }
                )
                break
        mode = step.get("execution_mode", "subprocess")
        if mode == "orchestrated":
            completion = step.get("completion_artifact")
            if not isinstance(completion, dict):
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "pending_orchestrator",
                        "error_code": "orchestrator_required",
                    }
                )
                break
            path = Path(str(completion["path"]))
            if not path.is_file():
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "pending_orchestrator",
                        "error_code": "orchestrator_required",
                        "completion_artifact": str(path),
                    }
                )
                break
            try:
                completion_payload, completion_digest = _read_json_artifact(path)
            except RouterError as exc:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "completion_artifact_mismatch",
                        "validation_error": str(exc),
                    }
                )
                break
            if (
                not isinstance(completion_payload, dict)
                or _contract_of(completion_payload) != completion["contract"]
                or completion_payload.get("status") != completion["required_status"]
                or completion_payload.get("run_id") != completion["run_id"]
                or completion_payload.get("stage") != completion["stage"]
            ):
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "completion_artifact_mismatch",
                        "validation_error": "completion artifact contract, status, run_id, or stage mismatch",
                    }
                )
                break
            validation_error = _validate_stage_artifact(
                str(step["stage"]),
                completion_payload,
                str(plan["run_id"]),
                source_kind=str(plan["request"]["source_kind"]),
            )
            if validation_error:
                executions.append(
                    {
                        "id": step.get("id"),
                        "stage": step["stage"],
                        "engine": step["engine"],
                        "role": step["role"],
                        "status": "failed",
                        "error_code": "completion_artifact_mismatch",
                        "validation_error": validation_error,
                    }
                )
                break
            executions.append(
                {
                    "id": step.get("id"),
                    "stage": step["stage"],
                    "engine": step["engine"],
                    "role": step["role"],
                    "status": "covered",
                    "completion_artifact": str(path),
                    "completion_artifact_sha256": completion_digest,
                    "semantic_digest": semantic_digest(completion_payload),
                    "parsed_output": completion_payload,
                }
            )
            if gate_artifact_sha256:
                executions[-1]["gate_artifact_sha256"] = gate_artifact_sha256
            continue
        if mode != "subprocess":
            executions.append(
                {
                    "id": step.get("id"),
                    "stage": step["stage"],
                    "engine": step["engine"],
                    "role": step["role"],
                    "status": "pending_orchestrator" if mode == "orchestrated" else "covered",
                    "error_code": "orchestrator_required" if mode == "orchestrated" else None,
                }
            )
            if mode == "orchestrated":
                break
            continue
        execution = _execute_step(runtime_step, plan["run_id"])
        if "runtime_input_binding" in runtime_step:
            execution["input_binding"] = runtime_step["runtime_input_binding"]
        if gate_artifact_sha256:
            execution["gate_artifact_sha256"] = gate_artifact_sha256
        executions.append(execution)
        if execution["status"] != "complete":
            break

    status = "complete"
    if any(item["status"] == "pending_orchestrator" for item in executions):
        status = "pending_orchestrator"
    elif any(item["status"] not in {"complete", "covered"} for item in executions):
        status = "failed"
    if len(executions) < len(plan["stages"]):
        if status != "pending_orchestrator":
            status = "failed"

    comparisons = []
    for validator in (
        item
        for item in executions
        if item.get("role") == "validator" and item.get("status") in {"complete", "covered"}
    ):
        primary = next(
            (
                item
                for item in executions
                if item.get("stage") == validator.get("stage")
                and item.get("role") == "primary"
                and item.get("status") in {"complete", "covered"}
            ),
            None,
        )
        if primary:
            primary_output = primary.get("parsed_output")
            validator_output = validator.get("parsed_output")
            diff = None
            if isinstance(primary_output, Mapping) and isinstance(validator_output, Mapping):
                diff = _stable_item_diff(primary_output, validator_output)
            matched = primary.get("semantic_digest") == validator.get("semantic_digest")
            if isinstance(primary_output, Mapping) and isinstance(validator_output, Mapping):
                comparison_stage = str(validator["stage"])
                matched = _comparison_digest(
                    primary_output, comparison_stage
                ) == _comparison_digest(validator_output, comparison_stage)
            if diff is not None:
                matched = matched and not diff["added_ids"] and not diff["removed_ids"] and not diff["changed"]
            comparison = {
                "stage": validator["stage"],
                "primary_engine": primary["engine"],
                "validator_engine": validator["engine"],
                "primary_digest": primary.get("semantic_digest"),
                "validator_digest": validator.get("semantic_digest"),
                "matched": matched,
            }
            if diff is not None:
                comparison["diff"] = diff
            comparisons.append(comparison)
            if not matched:
                status = "validation_mismatch"
    validation = {
        "required": bool(plan.get("dual_run")),
        "matched": bool(comparisons) and all(item["matched"] for item in comparisons)
        if plan.get("dual_run")
        else all(item["matched"] for item in comparisons),
        "comparisons": comparisons,
    }
    if plan.get("dual_run") and not comparisons and status == "complete":
        status = "failed"
        validation["matched"] = False

    return {
        "schema": RESULT_SCHEMA,
        "run_id": plan["run_id"],
        "completed_at": _now(),
        "status": status,
        "selected_engines": list(plan.get("selected_engines", [])),
        "executions": executions,
        "validation": validation,
    }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RouterError(f"cannot read JSON from {path}: {exc}") from exc


def _read_json_artifact(path: Path) -> tuple[Any, str]:
    """Parse and hash the exact same immutable byte snapshot."""
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise OSError("trusted artifacts must be regular files")
            raw = handle.read()
            after = os.fstat(handle.fileno())
        if (before.st_dev, before.st_ino, before.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ) or len(raw) != after.st_size:
            raise OSError("artifact changed while it was read")
        payload = json.loads(raw.decode("utf-8"))
        return payload, hashlib.sha256(raw).hexdigest()
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RouterError(f"cannot read JSON artifact from {path}: {exc}") from exc


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        if temporary_name:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass
        raise


def _processor_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Project an inspected extraction candidate into the Rust input contract."""
    projected: dict[str, Any] = {
        "candidate_id": candidate["candidate_id"],
        "platform": candidate["platform"],
        "url": candidate["url"],
        "title": candidate["title"],
        "author": candidate["author"],
        "published_at": candidate["published_at"],
        "excerpt": candidate["excerpt_or_observation"],
    }
    for source, target in (
        ("platform_native_id", "platform_native_id"),
        ("body_or_transcript_sha256", "body_or_transcript_sha256"),
    ):
        if candidate.get(source) is not None:
            projected[target] = candidate[source]
    return projected


def _compile_rust_input_from_extraction(
    step: Mapping[str, Any],
    extraction: Mapping[str, Any],
    extraction_artifact_sha256: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Atomically materialize the one Rust input authorized by extraction."""
    input_path_value = _command_flag_value(step.get("command", []), "--input")
    if input_path_value is None:
        return None, "Rust process command must contain exactly one --input path"
    candidates = extraction.get("candidates")
    if not _is_array_of_objects(candidates):
        return None, "extraction candidates are missing for Rust input compilation"
    try:
        processor_candidates = [_processor_candidate(candidate) for candidate in candidates]
    except KeyError as exc:
        return None, f"extraction candidate is missing Rust input field {exc.args[0]}"
    candidate_ids = [str(candidate["candidate_id"]) for candidate in processor_candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        return None, "Rust processor input candidate IDs are not unique"
    processor_input = {
        "contract_version": "top50-processor/v1",
        "run_id": extraction["run_id"],
        "candidates": processor_candidates,
    }
    input_path = Path(input_path_value)
    try:
        _write_json_atomic(input_path, processor_input)
        snapshot, artifact_sha256 = _read_json_artifact(input_path)
    except (RouterError, OSError, UnicodeError) as exc:
        return None, str(exc)
    if snapshot != processor_input:
        return None, "Rust processor input changed during atomic compilation"
    return {
        "relation": "extraction_to_processor_input",
        "path": str(input_path),
        "artifact_sha256": artifact_sha256,
        "contract": "top50-processor/v1",
        "run_id": extraction["run_id"],
        "stage": "process",
        "producer_engine_id": str(extraction["producer"]["engine_id"]),
        "upstream_artifact_sha256": extraction_artifact_sha256,
        "upstream_result_digest_sha256": extraction["result_digest_sha256"],
        "candidate_count": len(candidate_ids),
        "candidate_ids_sha256": _canonical_value_sha256(sorted(candidate_ids)),
    }, None


def _validate_rank_runtime_binding(
    step: Mapping[str, Any], curator: Mapping[str, Any], run_id: str
) -> tuple[dict[str, Any] | None, str | None]:
    lineage_path_value = _command_flag_value(
        step.get("command", []), "--lineage-manifest"
    )
    curator_path_value = _command_flag_value(
        step.get("command", []), "--curator-acceptance"
    )
    if lineage_path_value is None or curator_path_value is None:
        return None, "rank command is missing lineage or curator inputs"
    gate = step.get("gate")
    if not isinstance(gate, Mapping) or curator_path_value != gate.get("path"):
        return None, "rank command curator path does not match its gate"
    try:
        frozen = validate_rank_input_manifest(Path(lineage_path_value), run_id)
        validate_curator_against_rank_bundle(curator, frozen, run_id)
    except LineageError as exc:
        return None, str(exc)
    flag_paths: dict[str, Path] = {}
    for input_id, flag in (
        ("candidates", "--input"),
        ("run_manifest", "--manifest"),
        ("queries", "--queries"),
        ("sources", "--sources"),
        ("evidence_cards", "--evidence-cards"),
        ("platform_coverage", "--platform-coverage"),
    ):
        value = _command_flag_value(step.get("command", []), flag)
        if value is None:
            return None, f"rank command is missing {flag}"
        flag_paths[input_id] = Path(value)
    if not command_paths_match_bundle(flag_paths, frozen):
        return None, "rank command paths do not match the frozen input manifest"
    return frozen, None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe_parser = subparsers.add_parser("probe", help="probe all three engine structures")
    probe_parser.add_argument("--json", action="store_true", help="emit one compact JSON object")
    probe_parser.add_argument("--python-path", type=str)
    probe_parser.add_argument("--go-path", type=str)
    probe_parser.add_argument("--rust-path", type=str)
    probe_parser.add_argument("--timeout", type=float, default=DEFAULT_PROBE_TIMEOUT)

    plan_parser = subparsers.add_parser("plan", help="compile a router request into a capability plan")
    plan_parser.add_argument("--input", required=True, type=Path)
    plan_parser.add_argument("--output", required=True, type=Path)
    plan_parser.add_argument("--probe-timeout", type=float, default=DEFAULT_PROBE_TIMEOUT)

    execute_parser = subparsers.add_parser("execute", help="execute and validate an existing plan")
    execute_parser.add_argument("--plan", required=True, type=Path)
    execute_parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "probe":
            paths = {
                engine: value
                for engine, value in (
                    ("python", args.python_path),
                    ("go", args.go_path),
                    ("rust", args.rust_path),
                )
                if value
            }
            result = probe_all(paths, timeout=args.timeout)
            print(
                json.dumps(result, ensure_ascii=False, sort_keys=True)
                if args.json
                else json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
            )
            return 0
        if args.command == "plan":
            request = validate_request(_read_json(args.input))
            probes = probe_all(request["engine_paths"], timeout=args.probe_timeout)["engines"]
            plan = build_plan(request, probes=probes)
            _write_json_atomic(args.output, plan)
            print(json.dumps({"schema": PLAN_SCHEMA, "run_id": plan["run_id"], "output": str(args.output)}))
            return 0
        result = execute_plan(_read_json(args.plan))
        _write_json_atomic(args.output, result)
        print(json.dumps({"schema": RESULT_SCHEMA, "run_id": result["run_id"], "status": result["status"]}))
        return 0 if result["status"] == "complete" else 3
    except (RouterError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
