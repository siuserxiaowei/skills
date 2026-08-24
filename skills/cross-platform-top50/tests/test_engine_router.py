from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
import atexit
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "engine_router.py"
SPEC = importlib.util.spec_from_file_location("engine_router", SCRIPT)
assert SPEC and SPEC.loader
router = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = router
SPEC.loader.exec_module(router)

PLANNER_SCRIPT = SCRIPT.with_name("research_planner.py")
PLANNER_SPEC = importlib.util.spec_from_file_location(
    "research_planner_for_engine_router_tests", PLANNER_SCRIPT
)
assert PLANNER_SPEC and PLANNER_SPEC.loader
planner = importlib.util.module_from_spec(PLANNER_SPEC)
sys.modules[PLANNER_SPEC.name] = planner
PLANNER_SPEC.loader.exec_module(planner)

_ARTIFACT_FIXTURES = tempfile.TemporaryDirectory(prefix="top50-router-test-artifacts-")
atexit.register(_ARTIFACT_FIXTURES.cleanup)
_ARTIFACT_SEQUENCE = 0
_QUERY_PLAN_SEQUENCE = 0


def probe(
    engine: str,
    *,
    ready: bool = True,
    capabilities: tuple[str, ...] = (),
    contract: str = "top50-engine/v1",
    version: str = "1.2.3",
    base_command: list[str] | None = None,
) -> dict[str, object]:
    engine_id = {
        "python": "python-ranker",
        "go": "go-collector",
        "rust": "rust-processor",
    }.get(engine)
    return {
        "engine": engine,
        "engine_id": engine_id if ready else None,
        "ready": ready,
        "version": version if ready else None,
        "contract": contract if ready else None,
        "capabilities": list(capabilities) if ready else [],
        "command": [f"/{engine}"],
        "base_command": list(base_command or [f"/{engine}"]),
        "returncode": 0 if ready else 127,
        "stdout": "{}" if ready else "",
        "stderr": "" if ready else "not found",
        "reason": "ready" if ready else "executable_unavailable",
        "duration_ms": 1,
    }


def all_ready(engine_paths: dict[str, str] | None = None) -> dict[str, dict[str, object]]:
    commands = router._default_engine_commands(SCRIPT.parents[1], engine_paths or {})
    bases = {
        "python": router._path_command(Path(commands["python"])),
        "go": list(commands["go"]),
        "rust": list(commands["rust"]),
    }
    return {
        "python": probe(
            "python",
            capabilities=(
                "control",
                "platform_orchestration",
                "platform_cli",
                "browser_session",
                "rank",
                "contract_validation",
                "publish_orchestration",
            ),
            contract="top50-python-adapter/v1",
            version="deterministic-v2",
            base_command=bases["python"],
        ),
        "go": probe(
            "go",
            capabilities=("public_http_collect", "get", "bounded_concurrency"),
            base_command=bases["go"],
        ),
        "rust": probe(
            "rust",
            capabilities=(
                "process",
                "normalize",
                "fingerprint",
                "deduplicate",
                "security_preflight",
            ),
            base_command=bases["rust"],
        ),
    }


def request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "top50-router-request/v1",
        "run_id": "run-001",
        "stage": "full",
        "workload": "large",
        "source_kind": "public_http",
        "risk": "low",
        "required_capabilities": [],
        "engine_mode": "auto",
        "dual_run": False,
    }
    value.update(overrides)
    if value["stage"] in {"discovery", "full"} and "query_plan_binding" not in overrides:
        plan_run_id = str(value["run_id"])
        if not plan_run_id or any(
            character
            not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in plan_run_id
        ):
            plan_run_id = "run-001"
        value["query_plan_binding"] = query_plan_binding(plan_run_id)
    if (
        value["source_kind"] == "public_http"
        and value["stage"] in {"fetch", "full"}
        and "public_http_binding" not in overrides
    ):
        run_dir = Path(str(value.get("run_dir", Path("router-runs") / str(value["run_id"]))))
        value["public_http_binding"] = {
            "manifest_path": str(run_dir / "go-collector-input.json"),
            "manifest_artifact_sha256": "a" * 64,
            "job_set_sha256": "b" * 64,
            "job_count": 1,
        }
    return value


def query_plan_binding(run_id: str, query_ids: list[str] | None = None) -> dict[str, object]:
    global _QUERY_PLAN_SEQUENCE
    _QUERY_PLAN_SEQUENCE += 1
    requested_count = max(1, len(query_ids)) if query_ids is not None else 1
    intents = (
        "exact",
        "tutorial",
        "practice",
        "review",
        "case_study",
        "controversy",
        "failure",
        "primary_source",
    )[:requested_count]
    intents = list(intents)
    if len(intents) != requested_count:
        raise AssertionError("router QueryPlan fixture supports at most eight queries")
    plan: dict[str, object] = planner.compile_query_plan(
        {
            "schema": "top50-research-query-request/v1",
            "run_id": run_id,
            "topic": "Agent research",
            "purpose": "Router contract testing",
            "platforms": [{"platform_id": "github", "required": True}],
            "aliases": [],
            "languages": ["en"],
            "intents": intents,
            "timeframe": {"start": "2026-07-25", "end": "2026-08-24"},
            "tokenizer_mode": "cjk_bigram",
        }
    )
    actual_ids = [str(row["query_id"]) for row in plan["queries"]]
    path = (
        Path(_ARTIFACT_FIXTURES.name)
        / f"query-plan-{_QUERY_PLAN_SEQUENCE:05d}.json"
    )
    path.write_text(json.dumps(plan), encoding="utf-8")
    return {
        "path": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "plan_digest_sha256": plan["plan_digest_sha256"],
        "query_count": len(actual_ids),
        "query_ids_sha256": canonical_digest(sorted(actual_ids)),
    }


def make_engine(path: Path, body: str) -> Path:
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, pathlib, sys, time\n"
        "probe_sidecar = pathlib.Path(sys.argv[0] + '.probe.json')\n"
        "if sys.argv[1:] == ['probe', '--json'] and probe_sidecar.is_file():\n"
        "    print(probe_sidecar.read_text()); raise SystemExit(0)\n"
        + textwrap.dedent(body),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def rust_digest(payload: dict[str, object]) -> str:
    material = {key: value for key, value in payload.items() if key != "result_digest_sha256"}
    canonical = json.dumps(
        material, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def canonical_digest(value: object) -> str:
    canonical = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def discovery_binding_from_plan(binding: dict[str, object]) -> dict[str, object]:
    return {
        "relation": "research_query_plan",
        "path": binding["path"],
        "artifact_sha256": binding["artifact_sha256"],
        "contract": "top50-research-query-plan/v1",
        "run_id": json.loads(Path(str(binding["path"])).read_text())["run_id"],
        "stage": "scope",
        "required_status": "complete",
        "producer_engine_id": "research-planner",
        "result_digest_sha256": binding["plan_digest_sha256"],
        "record_kind": "query",
        "record_count": binding["query_count"],
        "record_ids_sha256": binding["query_ids_sha256"],
    }


def bound_artifact(
    relation: str,
    payload: dict[str, object],
    *,
    record_kind: str,
    record_ids: list[str],
) -> dict[str, object]:
    global _ARTIFACT_SEQUENCE
    _ARTIFACT_SEQUENCE += 1
    payload = copy.deepcopy(payload)
    payload.setdefault("status", "complete")
    payload.setdefault("producer", {"engine_id": "fixture-producer", "engine_version": "1.0.0"})
    payload["result_digest_sha256"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "result_digest_sha256"}
    )
    path = Path(_ARTIFACT_FIXTURES.name) / f"{_ARTIFACT_SEQUENCE:05d}-{relation}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return {
        "relation": relation,
        "path": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "contract": payload["contract_version"],
        "run_id": payload["run_id"],
        "stage": payload["stage"],
        "required_status": payload["status"],
        "producer_engine_id": payload["producer"]["engine_id"],
        "result_digest_sha256": payload["result_digest_sha256"],
        "record_kind": record_kind,
        "record_count": len(record_ids),
        "record_ids_sha256": canonical_digest(sorted(record_ids)),
    }


def bind_existing_artifact(
    relation: str,
    path: Path,
    payload: dict[str, object],
    *,
    record_kind: str,
    record_ids: list[str],
) -> dict[str, object]:
    return {
        "relation": relation,
        "path": str(path),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "contract": payload["contract_version"],
        "run_id": payload["run_id"],
        "stage": payload["stage"],
        "required_status": payload["status"],
        "producer_engine_id": payload["producer"]["engine_id"],
        "result_digest_sha256": payload["result_digest_sha256"],
        "record_kind": record_kind,
        "record_count": len(record_ids),
        "record_ids_sha256": canonical_digest(sorted(record_ids)),
    }


def public_http_binding(
    manifest_path: str,
    jobs: list[dict[str, object]],
    *,
    artifact_sha256: str = "a" * 64,
) -> dict[str, object]:
    ordered_jobs = sorted(jobs, key=lambda row: str(row["job_id"]))
    return {
        "manifest_path": manifest_path,
        "manifest_artifact_sha256": artifact_sha256,
        "job_set_sha256": canonical_digest(ordered_jobs),
        "job_count": len(ordered_jobs),
    }


def stage_artifact(
    stage: str,
    *,
    run_id: str = "run-execute",
    status: str | None = None,
    **overrides: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": {
            "discovery": "top50-discovery-result/v1",
            "fetch": "top50-fetch-result/v1",
            "extraction": "top50-extraction-result/v1",
            "process": "top50-process-result/v1",
            "curate": "top50-curator-acceptance/v1",
        }[stage],
        "run_id": run_id,
        "stage": stage,
        "status": status or ("accepted" if stage == "curate" else "complete"),
        "producer": {"engine_id": "python-control-plane", "engine_version": "0.1.0"},
        "input_bindings": [],
        "counts": {},
    }
    if stage == "discovery":
        value.update({"queries": [], "discoveries": [], "counts": {"queries": 0, "discoveries": 0}})
    elif stage == "fetch":
        value.update({"results": [], "counts": {"jobs": 0, "transport_success": 0, "blocked": 0}})
    elif stage == "extraction":
        value.update(
            {
                "source_outcomes": [],
                "candidates": [],
                "counts": {"input_sources": 0, "content_sources": 0, "blocked_sources": 0, "candidates": 0},
            }
        )
    elif stage == "process":
        value.update(
            {
                "engine_id": "python-orchestrator",
                "processed_candidates": [],
                "exact_clusters": [],
                "near_duplicate_reviews": [],
                "counts": {
                    "input_candidates": 0,
                    "processed_candidates": 0,
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 0,
                },
            }
        )
    else:
        value.update(
            {
                "curator": {"id": "curator-001"},
                "worker_ids": [],
                "decisions": [],
                "accepted_candidate_ids": [],
                "evidence_ledger_binding": {"artifact_sha256": "b" * 64},
                "source_ledger_binding": {"artifact_sha256": "c" * 64},
                "counts": {"input_candidates": 0, "accepted": 0, "rejected": 0, "blocked": 0},
            }
        )
    value.update(overrides)
    if not value["input_bindings"]:
        if stage == "discovery":
            query_ids = [str(row["query_id"]) for row in value["queries"]]
            plan_binding = query_plan_binding(run_id, query_ids)
            value["input_bindings"] = [
                discovery_binding_from_plan(plan_binding)
            ]
        elif stage == "fetch":
            discoveries = [
                {
                    "discovery_id": str(row["job_id"]),
                    "query_id": str(row["query_id"]),
                    "platform": str(row["platform"]),
                    "url": str(row["url"]),
                    "canonical_url": str(row["url"]),
                    "access_kind": str(row["access_kind"]),
                }
                for row in value["results"]
            ]
            upstream = {
                "contract_version": "top50-discovery-result/v1",
                "run_id": run_id,
                "stage": "discovery",
                "queries": [],
                "discoveries": discoveries,
            }
            value["input_bindings"] = [
                bound_artifact(
                    "discovery_result",
                    upstream,
                    record_kind="discovery",
                    record_ids=[str(row["discovery_id"]) for row in discoveries],
                )
            ]
        elif stage == "extraction":
            results = [
                {
                    "job_id": str(row["upstream_job_id"]),
                    "transport_status": "transport_success",
                }
                for row in value["source_outcomes"]
            ]
            upstream = {
                "contract_version": "top50-fetch-result/v1",
                "run_id": run_id,
                "stage": "fetch",
                "results": results,
            }
            value["input_bindings"] = [
                bound_artifact(
                    "fetch_result",
                    upstream,
                    record_kind="job",
                    record_ids=[str(row["job_id"]) for row in results],
                )
            ]
        elif stage == "process":
            candidates = [
                {"candidate_id": str(row["candidate_id"])}
                for row in value["processed_candidates"]
            ]
            upstream = {
                "contract_version": "top50-extraction-result/v1",
                "run_id": run_id,
                "stage": "extraction",
                "candidates": candidates,
            }
            value["input_bindings"] = [
                bound_artifact(
                    "extraction_result",
                    upstream,
                    record_kind="candidate",
                    record_ids=[str(row["candidate_id"]) for row in candidates],
                )
            ]
        else:
            candidate_ids = [str(row["candidate_id"]) for row in value["decisions"]]
            process = {
                "contract_version": "top50-process-result/v1",
                "run_id": run_id,
                "stage": "process",
                "processed_candidates": [
                    {
                        "candidate_id": item,
                        "requires_fetch_time_dns_validation": False,
                    }
                    for item in candidate_ids
                ],
                "exact_clusters": [],
                "near_duplicate_reviews": [],
                "counts": {
                    "input_candidates": len(candidate_ids),
                    "processed_candidates": len(candidate_ids),
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 0,
                },
            }
            files = [
                {"input_id": "candidates", "artifact_sha256": "a" * 64},
                {"input_id": "run_manifest", "artifact_sha256": "d" * 64},
                {"input_id": "queries", "artifact_sha256": "e" * 64},
                {"input_id": "sources", "artifact_sha256": value["source_ledger_binding"]["artifact_sha256"]},
                {"input_id": "evidence_cards", "artifact_sha256": value["evidence_ledger_binding"]["artifact_sha256"]},
                {"input_id": "platform_coverage", "artifact_sha256": "f" * 64},
            ]
            rank_manifest = {
                "contract_version": "top50-rank-input-manifest/v1",
                "run_id": run_id,
                "stage": "worker_check",
                "files": files,
            }
            value["input_bindings"] = [
                bound_artifact(
                    "process_result",
                    process,
                    record_kind="candidate",
                    record_ids=candidate_ids,
                ),
                bound_artifact(
                    "rank_input_manifest",
                    rank_manifest,
                    record_kind="file",
                    record_ids=[str(row["input_id"]) for row in files],
                ),
            ]
    value["result_digest_sha256"] = canonical_digest(
        {key: item for key, item in value.items() if key != "result_digest_sha256"}
    )
    return value


def fetch_result(
    *,
    source_kind: str,
    backend_kind: str,
    request_user_agent: str = "",
    **overrides: object,
) -> dict[str, object]:
    value: dict[str, object] = {
        "job_id": "job-001",
        "query_id": "query-001",
        "platform": "web",
        "url": "https://example.com/",
        "final_url": "https://example.com/article",
        "backend_id": "backend-001",
        "backend_kind": backend_kind,
        "access_kind": source_kind,
        "probe_id": "probe-001",
        "probe_result": "success",
        "auth_state": "anonymous",
        "authorization": "granted_for_current_task",
        "transport_status": "transport_success",
        "http_status": 200,
        "request_user_agent": request_user_agent,
        "robots_status": "not_applicable",
        "robots_user_agent": "",
        "artifact": {"path": "artifacts/job-001.body", "body_sha256": "a" * 64, "bytes": 123},
        "content_class": "unclassified",
        "error_code": "",
    }
    value.update(overrides)
    return value


class RequestValidationTests(unittest.TestCase):
    def test_discovery_requires_exact_research_query_plan_snapshot(self) -> None:
        binding = query_plan_binding("run-001")
        normalized = router.validate_request(
            request(stage="discovery", query_plan_binding=binding)
        )
        self.assertEqual(normalized["query_plan_binding"], binding)

        old_path = Path(str(binding["path"]))
        old = json.loads(old_path.read_text(encoding="utf-8"))
        old["schema"] = "top50-scope-query-plan/v1"
        old["plan_digest_sha256"] = canonical_digest(
            {key: value for key, value in old.items() if key != "plan_digest_sha256"}
        )
        old_path.write_text(json.dumps(old), encoding="utf-8")
        old_binding = {
            **binding,
            "artifact_sha256": hashlib.sha256(old_path.read_bytes()).hexdigest(),
            "plan_digest_sha256": old["plan_digest_sha256"],
        }
        with self.assertRaisesRegex(router.RouterError, "research-query-plan"):
            router.validate_request(
                request(stage="discovery", query_plan_binding=old_binding)
            )

    def test_discovery_rejects_query_plan_drift_replacement_and_bypass(self) -> None:
        missing = request(stage="fetch", source_kind="platform_cli")
        missing["stage"] = "discovery"
        with self.assertRaisesRegex(router.RouterError, "query_plan_binding"):
            router.validate_request(missing)

        for field, value in (
            ("artifact_sha256", "0" * 64),
            ("plan_digest_sha256", "1" * 64),
            ("query_count", 99),
            ("query_ids_sha256", "2" * 64),
        ):
            binding = query_plan_binding("run-001")
            tampered = {**binding, field: value}
            with self.subTest(field=field), self.assertRaises(router.RouterError):
                router.validate_request(
                    request(stage="discovery", query_plan_binding=tampered)
                )

        replacement = query_plan_binding("other-run")
        with self.assertRaisesRegex(router.RouterError, "run_id"):
            router.validate_request(
                request(stage="discovery", query_plan_binding=replacement)
            )

    def test_public_fetch_requires_a_frozen_manifest_binding(self) -> None:
        jobs = [
            {
                "job_id": "job-001",
                "query_id": "query-001",
                "platform": "web",
                "url": "https://example.com/",
                "method": "GET",
                "headers": {"Accept": "text/html"},
            }
        ]
        binding = public_http_binding("research-runs/run-001/go-collector-input.json", jobs)
        normalized = router.validate_request(
            request(stage="fetch", public_http_binding=binding)
        )
        self.assertEqual(normalized["public_http_binding"], binding)

        for invalid in (
            {key: value for key, value in request(stage="fetch").items() if key != "public_http_binding"},
            request(stage="fetch", public_http_binding={**binding, "job_count": 0}),
            request(stage="fetch", public_http_binding={**binding, "job_set_sha256": "short"}),
            request(
                stage="process",
                source_kind="local_bundle",
                public_http_binding=binding,
            ),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(router.RouterError):
                router.validate_request(invalid)

    def test_rejects_wrong_schema_and_unknown_enums(self) -> None:
        for invalid in (
            request(schema="top50-router-request/v0"),
            request(stage="crawl"),
            request(workload="huge"),
            request(source_kind="private_session"),
            request(risk="critical"),
            request(engine_mode="fastest"),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(router.RouterError):
                router.validate_request(invalid)

    def test_rejects_missing_unknown_and_scalar_contract_fields(self) -> None:
        invalid_values = (
            [],
            {key: value for key, value in request().items() if key != "run_id"},
            request(extra=True),
            request(run_id="../escape"),
            request(dual_run="yes"),
            request(run_dir=""),
            request(top_n=0),
            request(timeout_seconds=0),
        )
        for invalid in invalid_values:
            with self.subTest(invalid=invalid), self.assertRaises(router.RouterError):
                router.validate_request(invalid)

    def test_rejects_invalid_required_capabilities_and_engine_paths(self) -> None:
        for invalid in (
            request(required_capabilities="rank"),
            request(required_capabilities=["rank", "rank"]),
            request(required_capabilities=[""]),
            request(engine_paths=[]),
            request(engine_paths={"perl": "/tmp/perl"}),
            request(engine_paths={"go": []}),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(router.RouterError):
                router.validate_request(invalid)


class PlanningTests(unittest.TestCase):
    def test_auto_full_large_public_http_builds_python_go_rust_curator_rank_hybrid(self) -> None:
        jobs = [
            {
                "job_id": "job-001",
                "query_id": "query-001",
                "platform": "web",
                "url": "https://example.com/",
                "method": "GET",
                "headers": {"Accept": "text/html"},
            }
        ]
        binding = public_http_binding("research-runs/run-001/go-collector-input.json", jobs)
        plan = router.build_plan(request(public_http_binding=binding), probes=all_ready())

        self.assertEqual(plan["schema"], "top50-router-plan/v1")
        self.assertEqual(plan["selected_engines"], ["python", "go", "rust"])
        self.assertEqual(
            [(step["stage"], step["engine"]) for step in plan["stages"]],
            [
                ("discovery", "python"),
                ("fetch", "go"),
                ("extraction", "python"),
                ("process", "rust"),
                ("curate", "python"),
                ("rank", "python"),
            ],
        )
        self.assertIn("auto_hybrid_large_public_http", plan["reason_codes"])
        self.assertEqual({item["engine"] for item in plan["candidates"]}, {"python", "go", "rust"})
        self.assertEqual(set(plan["probe_evidence"]), {"python", "go", "rust"})
        self.assertTrue(all("fallback_chain" in step for step in plan["stages"]))
        discovery = next(step for step in plan["stages"] if step["stage"] == "discovery")
        self.assertEqual(discovery["fallback_chain"], ["python"])
        self.assertNotIn("auto_fallback_go_to_python", plan["reason_codes"])
        curator_handoff = next(item for item in plan["handoffs"] if item["to_step"] == "curate-primary")
        rank_handoff = next(item for item in plan["handoffs"] if item["to_step"] == "rank-primary")
        self.assertTrue(curator_handoff["preserve_raw_results"])
        self.assertEqual(rank_handoff["required_status"], "accepted")
        self.assertTrue(rank_handoff["fail_closed"])
        self.assertEqual(plan["stages"][-1]["gate"]["required_status"], "accepted")
        artifacts = {
            step["stage"]: step["completion_artifact"]
            for step in plan["stages"]
            if step["stage"] in {"discovery", "extraction", "curate"}
        }
        self.assertEqual(artifacts["discovery"]["contract"], "top50-discovery-result/v1")
        self.assertEqual(artifacts["extraction"]["contract"], "top50-extraction-result/v1")
        self.assertEqual(artifacts["curate"]["contract"], "top50-curator-acceptance/v1")
        self.assertEqual(artifacts["curate"]["required_status"], "accepted")
        fetch = next(step for step in plan["stages"] if step["stage"] == "fetch")
        self.assertEqual(fetch["input_binding"], binding)

    def test_public_fetch_plan_binds_the_exact_manifest_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "go-collector-input.json"
            jobs = [
                {
                    "job_id": "job-001",
                    "query_id": "query-001",
                    "platform": "web",
                    "url": "https://example.com/",
                    "method": "GET",
                    "headers": {"Accept": "text/html"},
                }
            ]
            payload = {
                "contract_version": "top50-collector/v1",
                "run_id": "run-001",
                "concurrency": 1,
                "per_host_interval_ms": 0,
                "timeout_ms": 1000,
                "max_response_bytes": 1024,
                "max_attempts": 1,
                "jobs": jobs,
            }
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            binding = public_http_binding(
                str(manifest), jobs, artifact_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest()
            )
            plan = router.build_plan(
                request(stage="fetch", run_dir=directory, public_http_binding=binding),
                probes=all_ready(),
            )
        fetch = plan["stages"][0]
        self.assertEqual(fetch["input_binding"], binding)

    def test_small_platform_cli_routes_to_python_not_go(self) -> None:
        plan = router.build_plan(
            request(stage="discovery", workload="small", source_kind="platform_cli"),
            probes=all_ready(),
        )

        self.assertEqual(plan["selected_engines"], ["python"])
        self.assertEqual(plan["stages"][0]["engine"], "python")
        self.assertIn("source_requires_python_orchestration", plan["reason_codes"])

    def test_user_can_force_a_capable_engine(self) -> None:
        plan = router.build_plan(
            request(
                stage="process",
                source_kind="local_bundle",
                engine_mode="rust",
                required_capabilities=["fingerprint"],
            ),
            probes=all_ready(),
        )

        self.assertEqual(plan["selected_engines"], ["python", "rust"])
        self.assertEqual(plan["stages"][-1]["engine"], "rust")
        self.assertIn("explicit_engine_mode_rust", plan["reason_codes"])

    def test_missing_explicit_engine_fails_closed_without_fallback(self) -> None:
        probes = all_ready()
        probes["go"] = probe("go", ready=False)

        with self.assertRaisesRegex(router.RouterError, "forced engine go"):
            router.build_plan(
                request(stage="fetch", workload="large", engine_mode="go"), probes=probes
            )

    def test_auto_mode_falls_back_when_go_is_missing(self) -> None:
        probes = all_ready()
        probes["go"] = probe("go", ready=False)

        plan = router.build_plan(
            request(stage="fetch", workload="large", engine_mode="auto"), probes=probes
        )

        self.assertEqual(plan["selected_engines"], ["python"])
        self.assertEqual(plan["stages"][0]["fallback_chain"], ["go", "python"])
        self.assertIn("auto_fallback_go_to_python", plan["reason_codes"])

    def test_wrong_probe_contract_is_not_ready_and_falls_back(self) -> None:
        probes = all_ready()
        probes["go"] = probe(
            "go", capabilities=("public_http", "fetch"), contract="top50-engine/v0"
        )

        plan = router.build_plan(
            request(stage="fetch", workload="large", engine_mode="auto"), probes=probes
        )

        self.assertEqual(plan["selected_engines"], ["python"])
        self.assertFalse(plan["probe_evidence"]["go"]["ready"])
        self.assertEqual(plan["probe_evidence"]["go"]["reason"], "contract_mismatch")

    def test_required_capability_that_no_ready_engine_has_fails_closed(self) -> None:
        with self.assertRaisesRegex(router.RouterError, "required capabilities"):
            router.build_plan(
                request(stage="fetch", required_capabilities=["imaginary_capability"]),
                probes=all_ready(),
            )

    def test_go_collect_probe_does_not_claim_discovery_capability(self) -> None:
        probes = all_ready()
        probes["python"] = probe("python", ready=False)
        with self.assertRaisesRegex(router.RouterError, "required capability"):
            router.build_plan(
                request(
                    stage="fetch",
                    workload="large",
                    engine_mode="go",
                    required_capabilities=["discovery"],
                ),
                probes=probes,
            )

    def test_dual_run_adds_one_independent_validator_not_three_repeats(self) -> None:
        plan = router.build_plan(
            request(stage="process", source_kind="local_bundle", dual_run=True),
            probes=all_ready(),
        )

        self.assertEqual(len(plan["stages"]), 3)
        process_steps = [step for step in plan["stages"] if step["stage"] == "process"]
        self.assertEqual({step["role"] for step in process_steps}, {"primary", "validator"})
        self.assertLessEqual(len(plan["selected_engines"]), 2)
        self.assertNotEqual(process_steps[0]["engine"], process_steps[1]["engine"])
        self.assertIn("dual_run_independent_validation", plan["reason_codes"])
        validator = next(step for step in process_steps if step["role"] == "validator")
        self.assertEqual(validator["execution_mode"], "orchestrated")
        self.assertEqual(
            validator["completion_artifact"]["contract"],
            "top50-process-result/v1",
        )
        self.assertEqual(validator["completion_artifact"]["run_id"], "run-001")

    def test_high_risk_process_automatically_requests_dual_validation(self) -> None:
        plan = router.build_plan(
            request(stage="process", source_kind="local_bundle", risk="high"),
            probes=all_ready(),
        )

        self.assertTrue(plan["dual_run"])
        self.assertEqual(len(plan["selected_engines"]), 2)

    def test_forced_engine_missing_required_capability_fails_closed(self) -> None:
        with self.assertRaisesRegex(router.RouterError, "forced engine"):
            router.build_plan(
                request(
                    stage="rank",
                    engine_mode="go",
                    required_capabilities=["rank"],
                ),
                probes=all_ready(),
            )

    def test_rank_plan_always_inserts_curator_acceptance_gate(self) -> None:
        plan = router.build_plan(
            request(stage="rank", workload="small", source_kind="local_bundle"),
            probes=all_ready(),
        )

        self.assertEqual(
            [(step["stage"], step["engine"]) for step in plan["stages"]],
            [("curate", "python"), ("rank", "python")],
        )
        self.assertEqual(plan["stages"][0]["execution_mode"], "orchestrated")
        self.assertEqual(plan["stages"][1]["gate"]["type"], "curator_acceptance")
        self.assertIn("unaccepted evidence", plan["pause_conditions"])

    def test_process_plan_inserts_extraction_gate_before_rust(self) -> None:
        plan = router.build_plan(
            request(stage="process", workload="large", source_kind="local_bundle"),
            probes=all_ready(),
        )

        self.assertEqual(
            [(step["stage"], step["engine"]) for step in plan["stages"]],
            [("extraction", "python"), ("process", "rust")],
        )
        self.assertEqual(plan["stages"][1]["gate"]["contract"], "top50-extraction-result/v1")
        self.assertEqual(plan["stages"][1]["gate"]["required_status"], "complete")

    def test_curate_completion_is_the_exact_artifact_consumed_by_rank(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = router.build_plan(
                request(stage="rank", run_dir=directory), probes=all_ready()
            )

        curate = next(step for step in plan["stages"] if step["stage"] == "curate")
        rank = next(step for step in plan["stages"] if step["stage"] == "rank")
        completion = curate["completion_artifact"]
        gate = rank["gate"]
        for field in ("path", "contract", "required_status", "run_id", "stage"):
            with self.subTest(field=field):
                self.assertEqual(gate[field], completion[field])

    def test_go_commands_always_use_stable_per_role_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary_checkpoint = root / "go-collector-primary.checkpoint.json"
            primary_checkpoint.write_text("preserve-me", encoding="utf-8")
            primary = router.build_plan(
                request(stage="fetch", workload="large", engine_mode="go", run_dir=directory),
                probes=all_ready(),
            )
            validator = router.build_plan(
                request(
                    stage="fetch",
                    workload="large",
                    engine_mode="python",
                    dual_run=True,
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            rebuilt = router.build_plan(
                request(stage="fetch", workload="large", engine_mode="go", run_dir=directory),
                probes=all_ready(),
            )
            primary_step = next(step for step in primary["stages"] if step["engine"] == "go")
            validator_step = next(step for step in validator["stages"] if step["engine"] == "go")
            rebuilt_step = next(step for step in rebuilt["stages"] if step["engine"] == "go")
            for step, suffix in (
                (primary_step, "primary"),
                (validator_step, "validator"),
            ):
                with self.subTest(role=suffix):
                    checkpoint_index = step["command"].index("--checkpoint")
                    self.assertEqual(
                        step["command"][checkpoint_index + 1],
                        str(root / f"go-collector-{suffix}.checkpoint.json"),
                    )
            self.assertEqual(primary_step["command"], rebuilt_step["command"])
            self.assertEqual(primary_checkpoint.read_text(encoding="utf-8"), "preserve-me")

    def test_generated_plan_security_fields_cannot_be_removed_or_tampered(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = router.build_plan(
                request(run_dir=directory), probes=all_ready()
            )

        mutations: list[tuple[str, object]] = []

        missing_stage = copy.deepcopy(original)
        del missing_stage["stages"][1]
        mutations.append(("stage", missing_stage))

        wrong_contract = copy.deepcopy(original)
        wrong_contract["stages"][-1]["output_contract"] = "top50-ranking-summary/v0"
        mutations.append(("contract", wrong_contract))

        wrong_selected = copy.deepcopy(original)
        wrong_selected["selected_engines"] = ["python"]
        mutations.append(("selected_engines", wrong_selected))

        wrong_probe = copy.deepcopy(original)
        wrong_probe["probe_evidence"]["rust"]["engine_id"] = "go-collector"
        mutations.append(("probe_identity", wrong_probe))

        wrong_fallback = copy.deepcopy(original)
        process = next(step for step in wrong_fallback["stages"] if step["stage"] == "process")
        process["fallback_chain"] = ["python"]
        mutations.append(("fallback", wrong_fallback))

        missing_extraction_gate = copy.deepcopy(original)
        process = next(
            step for step in missing_extraction_gate["stages"] if step["stage"] == "process"
        )
        del process["gate"]
        mutations.append(("extraction_gate", missing_extraction_gate))

        missing_curator_gate = copy.deepcopy(original)
        rank = next(step for step in missing_curator_gate["stages"] if step["stage"] == "rank")
        del rank["gate"]
        mutations.append(("curator_gate", missing_curator_gate))

        router._validate_plan(original)
        for label, mutated in mutations:
            with self.subTest(label=label), self.assertRaises(router.RouterError):
                router._validate_plan(mutated)

    def test_rust_expected_digest_is_runtime_only_and_cannot_be_prebound_in_plan(self) -> None:
        plan = router.build_plan(
            request(
                stage="process",
                workload="large",
                source_kind="local_bundle",
                engine_mode="rust",
            ),
            probes=all_ready(),
        )
        step = next(item for item in plan["stages"] if item["stage"] == "process")
        step["command"].extend(["--expected-input-sha256", "a" * 64])

        with self.assertRaisesRegex(router.RouterError, "runtime-only"):
            router._validate_plan(plan)

    def test_selected_probe_evidence_is_complete_exact_and_stage_capable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = router.build_plan(
                request(run_dir=directory), probes=all_ready()
            )

        mutations: list[tuple[str, dict[str, object]]] = []
        for field in ("ready", "engine_id", "contract", "version", "capabilities"):
            mutated = copy.deepcopy(original)
            del mutated["probe_evidence"]["go"][field]
            mutations.append((f"missing_go_{field}", mutated))

        not_ready = copy.deepcopy(original)
        not_ready["probe_evidence"]["go"]["ready"] = False
        mutations.append(("go_not_ready", not_ready))

        no_fetch_capability = copy.deepcopy(original)
        no_fetch_capability["probe_evidence"]["go"]["capabilities"] = ["bounded_concurrency"]
        mutations.append(("go_no_fetch_capability", no_fetch_capability))

        missing_probe = copy.deepcopy(original)
        del missing_probe["probe_evidence"]["rust"]
        mutations.append(("missing_rust_probe", missing_probe))

        extra_probe = copy.deepcopy(original)
        extra_probe["probe_evidence"]["perl"] = copy.deepcopy(
            extra_probe["probe_evidence"]["go"]
        )
        mutations.append(("extra_probe", extra_probe))

        router._validate_plan(original)
        for label, mutated in mutations:
            with self.subTest(label=label), self.assertRaises(router.RouterError):
                router._validate_plan(mutated)

    def test_plan_and_stage_reject_schema_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = router.build_plan(
                request(run_dir=directory), probes=all_ready()
            )

        mutations = []
        top_level = copy.deepcopy(original)
        top_level["unexpected"] = True
        mutations.append(("top_level", top_level))

        stage = copy.deepcopy(original)
        stage["stages"][0]["unexpected"] = True
        mutations.append(("stage", stage))

        gate = copy.deepcopy(original)
        gate["stages"][-1]["gate"]["unexpected"] = True
        mutations.append(("gate", gate))

        completion = copy.deepcopy(original)
        completion["stages"][0]["completion_artifact"]["unexpected"] = True
        mutations.append(("completion", completion))

        for label, mutated in mutations:
            with self.subTest(label=label), self.assertRaises(router.RouterError):
                router._validate_plan(mutated)


class ProbeTests(unittest.TestCase):
    def test_probe_requires_executable_contract_and_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = make_engine(
                root / "good",
                """
                if sys.argv[1:] == ['probe', '--json']:
                    print(json.dumps({'contract_version':'top50-engine/v1',
                        'engine_id':'go-collector','engine_version':'9.1.0',
                        'status':'ready','capabilities':['public_http_collect','get']}))
                """,
            )
            bad = make_engine(root / "bad", "print('not-json')\n")

            good_result = router.probe_external_engine("go", [str(good)], timeout=2)
            bad_result = router.probe_external_engine("rust", [str(bad)], timeout=2)

        self.assertTrue(good_result["ready"])
        self.assertEqual(good_result["version"], "9.1.0")
        self.assertEqual(good_result["capabilities"], ["public_http_collect", "get"])
        self.assertFalse(bad_result["ready"])
        self.assertEqual(bad_result["reason"], "invalid_probe_json")

    def test_external_probe_rejects_legacy_alias_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            legacy = make_engine(
                Path(directory) / "legacy",
                """
                print(json.dumps({'contract':'top50-engine/v1','id':'go-collector',
                    'version':'9.1.0','capabilities':['public_http_collect']}))
                """,
            )
            result = router.probe_external_engine("go", [str(legacy)], timeout=2)

        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "invalid_probe_contract_fields")

    def test_external_probe_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = make_engine(
                Path(directory) / "probe-extra",
                "print(json.dumps({'contract_version':'top50-engine/v1',"
                "'engine_id':'go-collector','engine_version':'0.1.0',"
                "'status':'ready','capabilities':['public_http_collect'],"
                "'unexpected':'not-canonical'}))\n",
            )

            result = router.probe_external_engine("go", [str(engine)], timeout=2)

        self.assertFalse(result["ready"])
        self.assertEqual(result["reason"], "invalid_probe_contract_fields")

    def test_external_probe_rejects_wrong_id_status_version_and_capabilities(self) -> None:
        cases = (
            ({"engine_id": "rust-processor"}, "engine_id_mismatch"),
            ({"status": "warming"}, "engine_status_not_ready"),
            ({"engine_version": ""}, "invalid_probe_version"),
            ({"capabilities": []}, "invalid_probe_capabilities"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, (override, reason) in enumerate(cases):
                payload = {
                    "contract_version": "top50-engine/v1",
                    "engine_id": "go-collector",
                    "engine_version": "1.0.0",
                    "status": "ready",
                    "capabilities": ["public_http_collect"],
                    **override,
                }
                engine = make_engine(
                    Path(directory) / f"bad-{index}",
                    f"print(json.dumps({payload!r}))\n",
                )
                with self.subTest(reason=reason):
                    result = router.probe_external_engine("go", [str(engine)], timeout=2)
                    self.assertFalse(result["ready"])
                    self.assertEqual(result["reason"], reason)

    def test_external_probe_rejects_non_object_json_and_invalid_api_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = make_engine(Path(directory) / "array", "print('[]')\n")
            result = router.probe_external_engine("go", [str(engine)], timeout=2)

        self.assertEqual(result["reason"], "invalid_probe_json")
        with self.assertRaises(router.RouterError):
            router.probe_external_engine("python", ["unused"])
        with self.assertRaises(router.RouterError):
            router.probe_external_engine("go", [])

    def test_probe_times_out_and_missing_command_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            slow = make_engine(Path(directory) / "slow", "time.sleep(5)\n")
            timed = router.probe_external_engine("go", [str(slow)], timeout=0.05)
            missing = router.probe_external_engine("rust", [str(Path(directory) / "missing")], timeout=1)

        self.assertFalse(timed["ready"])
        self.assertEqual(timed["reason"], "probe_timeout")
        self.assertFalse(missing["ready"])
        self.assertEqual(missing["reason"], "executable_unavailable")

    def test_python_probe_executes_ranker_help_and_limits_capabilities(self) -> None:
        result = router.probe_python_engine(SCRIPT.parents[0] / "rank_candidates.py", timeout=3)

        self.assertTrue(result["ready"])
        self.assertEqual(result["contract"], "top50-python-adapter/v1")
        self.assertIn("rank", result["capabilities"])
        self.assertNotIn("public_http", result["capabilities"])
        self.assertEqual(result["command"][-1], "--help")

    def test_python_probe_rejects_missing_ranker_and_empty_help(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = router.probe_python_engine(root / "missing.py", timeout=1)
            empty = make_engine(root / "empty", "pass\n")
            invalid = router.probe_python_engine(empty, timeout=1)

        self.assertEqual(missing["reason"], "executable_unavailable")
        self.assertEqual(invalid["reason"], "invalid_help_output")


class ExecutionTests(unittest.TestCase):
    def executable_plan(
        self,
        command: list[str],
        *,
        contract: str = "top50-processor-result/v1",
        engine: str = "rust",
        stage: str = "process",
    ) -> dict[str, object]:
        if not isinstance(command, list):
            raise router.RouterError("plan command must be an argv array")
        effective_request_stage = "fetch" if engine == "go" else "process"
        executable = command[0]
        engine_paths = {engine: executable}
        probe_payload = {
            "contract_version": "top50-engine/v1",
            "engine_id": "go-collector" if engine == "go" else "rust-processor",
            "engine_version": "1.0.0",
            "status": "ready",
            "capabilities": (
                ["public_http_collect", "get", "bounded_concurrency"]
                if engine == "go"
                else ["process", "normalize", "fingerprint", "deduplicate", "security_preflight"]
            ),
        }
        Path(executable + ".probe.json").write_text(json.dumps(probe_payload), encoding="utf-8")
        probes = all_ready(engine_paths)
        probes[engine]["version"] = "1.0.0"
        binding = None
        if engine == "go":
            input_index = command.index("--input") + 1 if "--input" in command else None
            manifest_path = Path(command[input_index]) if input_index is not None else Path(executable).parent / "go-collector-input.json"
            if not manifest_path.is_file():
                manifest_path.write_text(
                    json.dumps(
                        {
                            "contract_version": "top50-collector/v1",
                            "run_id": "run-execute",
                            "concurrency": 1,
                            "per_host_interval_ms": 0,
                            "timeout_ms": 1000,
                            "max_response_bytes": 1024,
                            "max_attempts": 1,
                            "jobs": [
                                {
                                    "job_id": "job-001",
                                    "query_id": "query-001",
                                    "platform": "web",
                                    "url": "https://example.com/",
                                    "method": "GET",
                                    "headers": {"Accept": "text/plain"},
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_jobs = manifest_payload.get("jobs", [])
            binding = public_http_binding(
                str(manifest_path),
                manifest_jobs,
                artifact_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )
        plan = router.build_plan(
            request(
                run_id="run-execute",
                stage=effective_request_stage,
                engine_mode=engine,
                run_dir=str(Path(executable).parent),
                timeout_seconds=2,
                engine_paths=engine_paths,
                **({"public_http_binding": binding} if binding is not None else {}),
            ),
            probes=probes,
        )
        primary = next(
            step for step in plan["stages"] if step["stage"] == stage and step["role"] == "primary"
        )
        if engine == "go" and "--input" in command:
            supplied_manifest = Path(command[command.index("--input") + 1])
            canonical_manifest = Path(primary["command"][primary["command"].index("--input") + 1])
            if supplied_manifest.is_file() and supplied_manifest != canonical_manifest:
                canonical_manifest.write_bytes(supplied_manifest.read_bytes())
        plan["stages"] = [primary]
        plan["selected_engines"] = [engine]
        plan["fallbacks"] = []
        plan["handoffs"] = []
        self._last_primary = primary
        return plan

    def allow_process(self, plan: dict[str, object], root: Path) -> Path:
        gate = next(step["gate"] for step in plan["stages"] if step["stage"] == "process")
        artifact = Path(gate["path"])
        artifact.parent.mkdir(parents=True, exist_ok=True)
        candidate_ids: list[str] = []
        validator_steps = [
            step
            for step in plan["stages"]
            if step.get("stage") == "process"
            and step.get("role") == "validator"
            and isinstance(step.get("completion_artifact"), dict)
        ]
        for step in validator_steps:
            completion_path = Path(step["completion_artifact"]["path"])
            if completion_path.is_file():
                completion = json.loads(completion_path.read_text(encoding="utf-8"))
                candidate_ids = [
                    str(row["candidate_id"])
                    for row in completion.get("processed_candidates", [])
                ]
                break
        outcomes = [
            {
                "source_id": f"source-{candidate_id}",
                "upstream_job_id": f"job-{candidate_id}",
                "body_sha256": hashlib.sha256(candidate_id.encode()).hexdigest(),
                "content_class": "content",
                "extractor_id": "fixture-v1",
                "candidate_ids": [candidate_id],
                "reason_codes": [],
            }
            for candidate_id in candidate_ids
        ]
        candidates = [
            {
                "candidate_id": candidate_id,
                "source_id": f"source-{candidate_id}",
                "platform": "web",
                "url": f"https://example.com/{candidate_id}",
                "title": f"Candidate {candidate_id}",
                "author": "Fixture Author",
                "published_at": "2026-08-24",
                "content_type": "text/html",
                "excerpt_or_observation": f"Inspected fixture excerpt for {candidate_id}.",
            }
            for candidate_id in candidate_ids
        ]
        extraction = stage_artifact(
            "extraction",
            source_outcomes=outcomes,
            candidates=candidates,
            counts={
                "input_sources": len(outcomes),
                "content_sources": len(outcomes),
                "blocked_sources": 0,
                "candidates": len(candidates),
            },
        )
        artifact.write_text(json.dumps(extraction), encoding="utf-8")
        binding = bind_existing_artifact(
            "extraction_result",
            artifact,
            extraction,
            record_kind="candidate",
            record_ids=candidate_ids,
        )
        for step in validator_steps:
            completion_path = Path(step["completion_artifact"]["path"])
            if completion_path.is_file():
                completion = json.loads(completion_path.read_text(encoding="utf-8"))
                completion["input_bindings"] = [binding]
                completion["result_digest_sha256"] = canonical_digest(
                    {
                        key: value
                        for key, value in completion.items()
                        if key != "result_digest_sha256"
                    }
                )
                completion_path.write_text(json.dumps(completion), encoding="utf-8")
        return artifact

    def dual_rust_plan(self, primary: Path, validator: Path, root: Path) -> dict[str, object]:
        paths = {"rust": str(primary), "python": str(validator)}
        primary_probe = {
            "contract_version": "top50-engine/v1", "engine_id": "rust-processor",
            "engine_version": "1.0.0", "status": "ready",
            "capabilities": ["process", "normalize", "fingerprint", "deduplicate", "security_preflight"],
        }
        Path(str(primary) + ".probe.json").write_text(json.dumps(primary_probe), encoding="utf-8")
        # The validator is represented by the Python orchestration contract and
        # resumes from its canonical completion artifact rather than executing
        # a second forged subprocess command.
        validator.write_text(
            validator.read_text(encoding="utf-8").replace(
                "import json, pathlib, sys, time",
                "import json, pathlib, sys, time\nif sys.argv[1:] == ['--help']:\n    print('ranker help'); raise SystemExit(0)",
            ),
            encoding="utf-8",
        )
        probes = all_ready(paths)
        probes["rust"]["version"] = "1.0.0"
        plan = router.build_plan(
            request(run_id="run-execute", stage="process", source_kind="local_bundle", engine_mode="rust", dual_run=True, run_dir=str(root), engine_paths=paths),
            probes=probes,
        )
        validator_step = next(step for step in plan["stages"] if step["role"] == "validator")
        # Execute the fixture once to recover its intended business result and
        # adapt only the orchestration envelope to the generated validator.
        completed = subprocess.run([str(validator)], text=True, capture_output=True, check=True)
        payload = json.loads(completed.stdout)
        payload = stage_artifact(
            "process",
            processed_candidates=payload.get("processed_candidates", []),
            exact_clusters=payload.get("exact_clusters", []),
            near_duplicate_reviews=payload.get("near_duplicate_reviews", []),
            counts=payload.get("counts", {}),
        )
        Path(validator_step["completion_artifact"]["path"]).write_text(json.dumps(payload), encoding="utf-8")
        return plan

    @staticmethod
    def rust_output(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "contract_version": "top50-processor-result/v1",
            "engine_id": "rust-processor",
            "engine_version": "1.0.0",
            "run_id": "run-execute",
            "processed_candidates": [],
            "exact_clusters": [],
            "near_duplicate_reviews": [],
            "counts": {
                "input_candidates": 0,
                "processed_candidates": 0,
                "exact_clusters": 0,
                "exact_duplicate_candidates": 0,
                "near_duplicate_reviews": 0,
                "dns_validation_required": 0,
            },
        }
        value.update(overrides)
        for candidate in value.get("processed_candidates", []):
            candidate.setdefault("requires_fetch_time_dns_validation", False)
        value["result_digest_sha256"] = rust_digest(value)
        return value

    @staticmethod
    def go_output(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "contract_version": "top50-collector-result/v1",
            "engine_id": "go-collector",
            "engine_version": "1.0.0",
            "run_id": "run-execute",
            "status": "complete",
            "results": [],
        }
        value.update(overrides)
        return value

    def test_execute_captures_streams_and_validates_json_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = make_engine(
                Path(directory) / "engine",
                f"print(json.dumps({self.rust_output()!r})); "
                "print('diagnostic', file=sys.stderr)\n",
            )
            plan = self.executable_plan([str(engine)])
            self.allow_process(plan, Path(directory))
            result = router.execute_plan(plan)

        self.assertEqual(result["schema"], "top50-router-result/v1")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["executions"][0]["returncode"], 0)
        self.assertEqual(result["executions"][0]["parsed_output"]["processed_candidates"], [])
        self.assertEqual(result["executions"][0]["stderr"].strip(), "diagnostic")

    def test_subprocess_outputs_fail_closed_on_identity_status_and_required_fields(self) -> None:
        cases = (
            (
                "go_partial",
                "go",
                "fetch",
                "top50-collector-result/v1",
                self.go_output(status="partial"),
            ),
            (
                "go_wrong_run",
                "go",
                "fetch",
                "top50-collector-result/v1",
                self.go_output(run_id="other-run"),
            ),
            (
                "go_wrong_engine",
                "go",
                "fetch",
                "top50-collector-result/v1",
                self.go_output(engine_id="rust-processor"),
            ),
            (
                "go_missing_results",
                "go",
                "fetch",
                "top50-collector-result/v1",
                {key: value for key, value in self.go_output().items() if key != "results"},
            ),
            (
                "rust_wrong_run",
                "rust",
                "process",
                "top50-processor-result/v1",
                self.rust_output(run_id="other-run"),
            ),
            (
                "rust_wrong_engine",
                "rust",
                "process",
                "top50-processor-result/v1",
                self.rust_output(engine_id="go-collector"),
            ),
            (
                "rust_missing_candidates",
                "rust",
                "process",
                "top50-processor-result/v1",
                {
                    key: value
                    for key, value in self.rust_output().items()
                    if key != "processed_candidates"
                },
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, engine_name, stage, contract, payload in cases:
                executable = make_engine(
                    root / label,
                    f"print(json.dumps({payload!r}))\n",
                )
                plan = self.executable_plan(
                    [str(executable)], contract=contract, engine=engine_name, stage=stage
                )
                if stage == "process":
                    self.allow_process(plan, root)
                with self.subTest(label=label):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], "invalid_engine_result")

    def test_rust_result_digest_is_recomputed_not_length_checked(self) -> None:
        forged = self.rust_output()
        forged["result_digest_sha256"] = "f" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = make_engine(root / "rust", f"print(json.dumps({forged!r}))\n")
            plan = self.executable_plan([str(engine)])
            self.allow_process(plan, root)

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["executions"][0]["error_code"], "invalid_engine_result")

    def test_go_result_requires_unique_manifest_conserving_job_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "go-input.json"
            manifest.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-collector/v1",
                        "run_id": "run-execute",
                        "jobs": [
                            {"job_id": "job-1", "query_id": "q-1", "platform": "web", "url": "https://example.com/1"},
                            {"job_id": "job-2", "query_id": "q-2", "platform": "web", "url": "https://example.com/2"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            cases = (
                ("empty", self.go_output(results=[])),
                (
                    "duplicate",
                    self.go_output(
                        results=[
                            {"job_id": "job-1", "query_id": "q-1", "platform": "web", "url": "https://example.com/1", "status": "transport_success"},
                            {"job_id": "job-1", "query_id": "q-1", "platform": "web", "url": "https://example.com/1", "status": "transport_success"},
                        ]
                    ),
                ),
                (
                    "wrong_identity",
                    self.go_output(
                        results=[
                            {"job_id": "job-1", "query_id": "wrong", "platform": "web", "url": "https://example.com/1", "status": "transport_success"},
                            {"job_id": "job-2", "query_id": "q-2", "platform": "web", "url": "https://example.com/2", "status": "transport_success"},
                        ]
                    ),
                ),
                (
                    "wrong_url",
                    self.go_output(
                        results=[
                            {"job_id": "job-1", "query_id": "q-1", "platform": "web", "url": "https://attacker.example/", "status": "transport_success"},
                            {"job_id": "job-2", "query_id": "q-2", "platform": "web", "url": "https://example.com/2", "status": "transport_success"},
                        ]
                    ),
                ),
            )
            for label, payload in cases:
                engine = make_engine(
                    root / f"go-{label}", f"print(json.dumps({payload!r}))\n"
                )
                plan = self.executable_plan(
                    [
                        str(engine),
                        "collect",
                        "--input",
                        str(manifest),
                        "--output",
                        str(root / f"{label}.json"),
                        "--artifacts",
                        str(root / "artifacts"),
                    ],
                    contract="top50-collector-result/v1",
                    engine="go",
                    stage="fetch",
                )
                with self.subTest(label=label):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], "invalid_engine_result")

    def test_native_go_result_requires_the_exact_robots_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "go-input.json"
            job = {
                "job_id": "job-1",
                "query_id": "q-1",
                "platform": "web",
                "url": "https://example.com/1",
                "method": "GET",
                "headers": {},
            }
            manifest.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-collector/v1",
                        "run_id": "run-execute",
                        "concurrency": 1,
                        "per_host_interval_ms": 0,
                        "timeout_ms": 1000,
                        "max_response_bytes": 1024,
                        "max_attempts": 1,
                        "jobs": [job],
                    }
                ),
                encoding="utf-8",
            )
            artifacts = root / "artifacts"
            artifacts.mkdir()
            artifact = artifacts / "job-1.body"
            artifact.write_bytes(b"")
            base_result = {
                "job_id": "job-1",
                "query_id": "q-1",
                "platform": "web",
                "url": "https://example.com/1",
                "final_url": "https://example.com/1",
                "status": "transport_success",
                "attempts": 1,
                "http_status": 200,
                "content_type": "text/plain",
                "bytes": 0,
                "body_sha256": hashlib.sha256(b"").hexdigest(),
                "artifact_path": str(artifact),
                "robots_url": "https://example.com/robots.txt",
                "robots_status": "allowed",
                "robots_rule": "",
                "robots_user_agent": router.ROBOTS_PRODUCT_TOKEN,
                "request_accept": "",
                "request_accept_language": "",
                "request_accept_encoding": "",
                "response_content_language": "",
                "response_content_encoding": "",
                "response_vary": "",
            }
            plan = self.executable_plan(
                [
                    str(root / "go-engine"),
                    "collect",
                    "--input",
                    str(manifest),
                    "--output",
                    str(root / "result.json"),
                    "--artifacts",
                    str(artifacts),
                ],
                contract="top50-collector-result/v1",
                engine="go",
                stage="fetch",
            )
            runtime_step = dict(plan["stages"][0])
            runtime_step["run_id"] = "run-execute"
            runtime_artifacts = Path(
                runtime_step["command"][
                    runtime_step["command"].index("--artifacts") + 1
                ]
            )
            runtime_artifacts.mkdir(parents=True, exist_ok=True)
            runtime_artifact = runtime_artifacts / "job-1.body"
            runtime_artifact.write_bytes(b"")
            base_result["artifact_path"] = str(runtime_artifact)
            for robots_user_agent in (
                "GrokBot",
                "OAI-SearchBot",
                "Googlebot",
                "TopFiftyCollector/0.1",
                "",
            ):
                native = self.go_output(results=[dict(base_result)])
                native["results"][0]["robots_user_agent"] = robots_user_agent
                with self.subTest(robots_user_agent=robots_user_agent):
                    self.assertIsNotNone(
                        router._validate_engine_result(runtime_step, native, "run-execute")
                    )

            valid = self.go_output(results=[base_result])
            self.assertIsNone(
                router._validate_engine_result(runtime_step, valid, "run-execute")
            )

    def test_result_contracts_reject_semantically_inconsistent_rust_and_minimal_go_shells(self) -> None:
        candidate = {
            "candidate_id": "one",
            "requires_fetch_time_dns_validation": True,
        }
        invalid_rust = self.rust_output(
            processed_candidates=[candidate],
            counts={
                **self.rust_output()["counts"],
                "input_candidates": 99,
                "processed_candidates": 1,
                "dns_validation_required": 0,
            },
        )
        minimal_go = self.go_output(
            results=[
                {
                    "job_id": "job-1",
                    "query_id": "q-1",
                    "platform": "web",
                    "url": "https://example.com/1",
                    "status": "transport_success",
                }
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rust_engine = make_engine(root / "rust", f"print(json.dumps({invalid_rust!r}))\n")
            rust_plan = self.executable_plan([str(rust_engine)])
            self.allow_process(rust_plan, root)

            manifest = root / "go-input.json"
            manifest.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-collector/v1",
                        "run_id": "run-execute",
                        "jobs": [{
                            "job_id": "job-1", "query_id": "q-1", "platform": "web",
                            "url": "https://example.com/1", "method": "GET", "headers": {},
                        }],
                    }
                ),
                encoding="utf-8",
            )
            go_engine = make_engine(root / "go", f"print(json.dumps({minimal_go!r}))\n")
            go_plan = self.executable_plan(
                [str(go_engine), "collect", "--input", str(manifest), "--output", str(root / "go.json"), "--artifacts", str(root / "artifacts")],
                contract="top50-collector-result/v1", engine="go", stage="fetch",
            )

            rust_result = router.execute_plan(rust_plan)
            go_result = router.execute_plan(go_plan)

        self.assertEqual(rust_result["status"], "failed")
        self.assertEqual(go_result["status"], "failed")

    def test_stdout_and_output_path_must_describe_the_same_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stdout_payload = self.rust_output()
            path_payload = self.rust_output(run_id="attacker-run")
            output_path = root / "result.json"
            engine = make_engine(
                root / "engine",
                f"pathlib.Path({str(output_path)!r}).write_text(json.dumps({path_payload!r})); print(json.dumps({stdout_payload!r}))\n",
            )
            plan = self.executable_plan([str(engine)])
            canonical_output = Path(plan["stages"][0]["output_path"])
            engine.write_text(
                engine.read_text(encoding="utf-8").replace(str(output_path), str(canonical_output)),
                encoding="utf-8",
            )
            self.allow_process(plan, root)

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["executions"][0]["error_code"], "invalid_json_output")

    def test_plan_rejects_command_and_covered_gate_bypass_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "marker"
            attacker = make_engine(root / "attacker", f"pathlib.Path({str(marker)!r}).write_text('ran')\n")
            process_plan = router.build_plan(
                request(run_id="run-execute", stage="process", run_dir=directory), probes=all_ready()
            )
            process_plan["stages"][1]["command"] = [str(attacker)]
            with self.assertRaises(router.RouterError):
                router.execute_plan(process_plan)
            self.assertFalse(marker.exists())

            rank_plan = router.build_plan(
                request(run_id="run-execute", stage="rank", source_kind="local_bundle", run_dir=directory),
                probes=all_ready(),
            )
            for step in rank_plan["stages"]:
                step["execution_mode"] = "covered"
                step["command"] = []
                step.pop("completion_artifact", None)
                step.pop("gate", None)
            with self.assertRaises(router.RouterError):
                router.execute_plan(rank_plan)

    def test_dual_validator_must_be_independent_and_unique(self) -> None:
        plan = router.build_plan(
            request(run_id="run-execute", stage="process", risk="high"), probes=all_ready()
        )
        primary = next(step for step in plan["stages"] if step["role"] == "primary" and step["stage"] == "process")
        validator = next(step for step in plan["stages"] if step["role"] == "validator")
        validator.update(
            {
                "engine": primary["engine"],
                "command": list(primary["command"]),
                "output_path": primary.get("output_path"),
                "input_contract": primary["input_contract"],
                "output_contract": primary["output_contract"],
            }
        )
        plan["selected_engines"] = list(dict.fromkeys(step["engine"] for step in plan["stages"]))
        with self.assertRaises(router.RouterError):
            router.execute_plan(plan)

        duplicate = copy.deepcopy(plan)
        duplicate["stages"].append(copy.deepcopy(validator))
        with self.assertRaises(router.RouterError):
            router.execute_plan(duplicate)

    def test_execute_reports_timeout_nonzero_and_invalid_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            slow = make_engine(root / "slow", "time.sleep(5)\n")
            nonzero = make_engine(root / "nonzero", "print('bad', file=sys.stderr); sys.exit(7)\n")
            malformed = make_engine(root / "malformed", "print('{}')\n")
            cases = (
                (slow, "timeout"),
                (nonzero, "nonzero_exit"),
                (malformed, "output_contract_mismatch"),
            )
            for engine, error_code in cases:
                plan = self.executable_plan([str(engine)])
                self.allow_process(plan, root)
                if error_code == "timeout":
                    plan["stages"][0]["timeout_seconds"] = 0.05
                with self.subTest(error_code=error_code):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], error_code)

    def test_execute_does_not_silently_runtime_fallback_after_engine_failure(self) -> None:
        """Fallback chains are recovery evidence, not an implicit retry authorization."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fallback_marker = root / "fallback-ran"
            primary = make_engine(root / "primary", "raise SystemExit(7)\n")
            plan = self.executable_plan([str(primary)])
            self.allow_process(plan, root)
            plan["stages"][0]["fallback_chain"] = ["rust", "python"]

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["executions"][0]["error_code"], "nonzero_exit")
        self.assertFalse(fallback_marker.exists())

    def test_execute_reports_missing_command_and_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            missing.write_text(
                "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                "if sys.argv[1:] == ['probe', '--json']:\n"
                " print(json.dumps({'contract_version':'top50-engine/v1','engine_id':'rust-processor','engine_version':'1.0.0','status':'ready','capabilities':['process','normalize','fingerprint','deduplicate','security_preflight']})); raise SystemExit(0)\n"
                "pathlib.Path(sys.argv[0]).unlink(); raise SystemExit(127)\n",
                encoding="utf-8",
            )
            missing.chmod(missing.stat().st_mode | stat.S_IXUSR)
            malformed = make_engine(Path(directory) / "malformed-json", "print('{')\n")
            cases = ((missing, "nonzero_exit"), (malformed, "invalid_json_output"))
            for engine, code in cases:
                with self.subTest(code=code):
                    plan = self.executable_plan([str(engine)])
                    self.allow_process(plan, Path(directory))
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], code)

    def test_execute_rejects_string_command_without_running_shell(self) -> None:
        with self.assertRaisesRegex(router.RouterError, "argv array"):
            self.executable_plan("printf exploited")  # type: ignore[arg-type]

    def test_dual_run_detects_semantic_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = make_engine(
                root / "first",
                f"print(json.dumps({self.rust_output(processed_candidates=[{'candidate_id': 'same', 'title': 'before', 'requires_fetch_time_dns_validation': False}], counts={**self.rust_output()['counts'], 'input_candidates': 1, 'processed_candidates': 1})!r}))\n",
            )
            second = make_engine(
                root / "second",
                f"print(json.dumps({self.rust_output(processed_candidates=[{'candidate_id': 'same', 'title': 'after', 'requires_fetch_time_dns_validation': False}], counts={**self.rust_output()['counts'], 'input_candidates': 1, 'processed_candidates': 1})!r}))\n",
            )
            plan = self.dual_rust_plan(first, second, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "validation_mismatch")
        self.assertFalse(result["validation"]["matched"])

    def test_dual_run_ignores_engine_local_cluster_ids_when_membership_matches(self) -> None:
        counts = {
            **self.rust_output()["counts"],
            "input_candidates": 2,
            "processed_candidates": 2,
            "exact_clusters": 1,
            "exact_duplicate_candidates": 1,
        }
        candidates = [
            {"candidate_id": "one", "requires_fetch_time_dns_validation": False},
            {"candidate_id": "two", "requires_fetch_time_dns_validation": False},
        ]
        primary_payload = self.rust_output(
            processed_candidates=candidates,
            exact_clusters=[
                {"cluster_id": "cluster-a", "representative_candidate_id": "one", "candidate_ids": ["one", "two"]}
            ],
            counts=counts,
        )
        validator_payload = self.rust_output(
            processed_candidates=candidates,
            exact_clusters=[
                {"cluster_id": "cluster-b", "representative_candidate_id": "one", "candidate_ids": ["one", "two"]}
            ],
            counts=counts,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = make_engine(
                root / "primary", f"print(json.dumps({primary_payload!r}))\n"
            )
            validator_engine = make_engine(
                root / "validator", f"print(json.dumps({validator_payload!r}))\n"
            )
            plan = self.dual_rust_plan(primary, validator_engine, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["validation"]["matched"])

    def test_dual_run_detects_exact_cluster_membership_disagreement(self) -> None:
        candidates = [
            {"candidate_id": "one", "title": "same input"},
            {"candidate_id": "two", "title": "same input"},
        ]
        primary_payload = self.rust_output(processed_candidates=candidates)
        primary_payload["counts"].update(
            {
                "input_candidates": 2,
                "processed_candidates": 2,
            }
        )
        primary_payload["result_digest_sha256"] = rust_digest(primary_payload)
        validator_payload = self.rust_output(
            processed_candidates=candidates,
            exact_clusters=[
                {
                    "cluster_id": "validator-local-id",
                    "representative_candidate_id": "one",
                    "candidate_ids": ["one", "two"],
                }
            ],
        )
        validator_payload["counts"].update(
            {
                "input_candidates": 2,
                "processed_candidates": 2,
                "exact_clusters": 1,
                "exact_duplicate_candidates": 1,
            }
        )
        validator_payload["result_digest_sha256"] = rust_digest(validator_payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = make_engine(
                root / "primary", f"print(json.dumps({primary_payload!r}))\n"
            )
            validator_engine = make_engine(
                root / "validator", f"print(json.dumps({validator_payload!r}))\n"
            )
            plan = self.dual_rust_plan(primary, validator_engine, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "validation_mismatch")
        self.assertFalse(result["validation"]["matched"])

    def test_dual_run_detects_counts_disagreement_when_candidates_match(self) -> None:
        candidates = [
            {"candidate_id": "same", "title": "same business item", "requires_fetch_time_dns_validation": False},
            {"candidate_id": "other", "title": "another business item", "requires_fetch_time_dns_validation": False},
        ]
        primary_payload = self.rust_output(
            processed_candidates=candidates,
            counts={
                **self.rust_output()["counts"],
                "input_candidates": 2,
                "processed_candidates": 2,
            },
        )
        validator_payload = self.rust_output(
            processed_candidates=candidates,
            counts={
                **self.rust_output()["counts"],
                "input_candidates": 2,
                "processed_candidates": 2,
                "near_duplicate_reviews": 1,
            },
            near_duplicate_reviews=[
                {
                    "review_id": "review-001",
                    "candidate_ids": ["same", "other"],
                }
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = make_engine(
                root / "primary", f"print(json.dumps({primary_payload!r}))\n"
            )
            validator_engine = make_engine(
                root / "validator", f"print(json.dumps({validator_payload!r}))\n"
            )
            plan = self.dual_rust_plan(primary, validator_engine, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "validation_mismatch")
        self.assertFalse(result["validation"]["matched"])

    def test_rank_comparison_includes_shortfall_when_selected_items_match(self) -> None:
        primary = {
            "contract_version": "top50-ranking-summary/v1",
            "engine_id": "python-ranker",
            "run_id": "run-execute",
            "stage": "rank",
            "status": "complete",
            "summary": {
                "requested_top_n": 2,
                "selected_count": 1,
                "rejected_count": 0,
                "shortfall": 1,
            },
            "ranked_candidates": [{"candidate_id": "same", "rank": 1}],
        }
        validator = copy.deepcopy(primary)
        validator["summary"]["shortfall"] = 0

        self.assertNotEqual(
            router._comparison_digest(primary),
            router._comparison_digest(validator),
        )

    def test_dual_run_reports_stable_id_added_removed_and_changed_diff(self) -> None:
        primary_payload = self.rust_output(
            processed_candidates=[
                {"candidate_id": "same", "title": "before"},
                {"candidate_id": "removed", "title": "gone"},
            ]
        )
        primary_payload["counts"]["processed_candidates"] = 2
        primary_payload["counts"]["input_candidates"] = 2
        primary_payload["result_digest_sha256"] = rust_digest(primary_payload)
        validator_payload = self.rust_output(
            processed_candidates=[
                {"candidate_id": "added", "title": "new"},
                {"candidate_id": "same", "title": "after"},
            ]
        )
        validator_payload["counts"]["processed_candidates"] = 2
        validator_payload["counts"]["input_candidates"] = 2
        validator_payload["result_digest_sha256"] = rust_digest(validator_payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = make_engine(root / "first", f"print(json.dumps({primary_payload!r}))\n")
            second = make_engine(root / "second", f"print(json.dumps({validator_payload!r}))\n")
            plan = self.dual_rust_plan(first, second, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            comparison = router._stable_item_diff(primary_payload, validator_payload)

        assert comparison is not None
        self.assertEqual(comparison["identity_kind"], "candidate_id")
        self.assertEqual(comparison["added_ids"], ["added"])
        self.assertEqual(comparison["removed_ids"], ["removed"])
        self.assertEqual(comparison["changed"][0]["id"], "same")
        self.assertEqual(comparison["changed"][0]["changed_fields"], ["title"])

    def test_rank_never_executes_without_accepted_curator_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "marker"
            ranker = make_engine(
                root / "ranker",
                f"pathlib.Path({str(marker)!r}).write_text('ran'); "
                "print(json.dumps({'contract':'top50-engine-result/v1'}))\n",
            )
            plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="rank",
                    source_kind="local_bundle",
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            plan["stages"][0]["execution_mode"] = "covered"
            plan["stages"][0].pop("completion_artifact", None)
            plan["stages"][1]["command"] = [str(ranker)]
            plan["stages"][1]["output_contract"] = "top50-ranking-summary/v1"
            plan["stages"][1]["output_path"] = str(root / "missing-summary.json")
            with self.assertRaises(router.RouterError):
                router.execute_plan(plan)

        self.assertFalse(marker.exists())

    def test_rust_never_executes_without_complete_extraction_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "marker"
            rust = make_engine(
                root / "rust",
                f"pathlib.Path({str(marker)!r}).write_text('ran'); "
                "print(json.dumps({'contract':'top50-engine-result/v1'}))\n",
            )
            plan = self.executable_plan([str(rust)])
            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["executions"][0]["error_code"], "stage_artifact_required")
        self.assertFalse(marker.exists())

    def test_valid_stage_artifact_allows_process_to_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = stage_artifact("extraction")
            engine = make_engine(
                root / "engine",
                f"print(json.dumps({self.rust_output()!r}))\n",
            )
            plan = self.executable_plan([str(engine)])
            artifact = Path(plan["stages"][0]["gate"]["path"])
            artifact.write_text(json.dumps(payload), encoding="utf-8")
            plan["stages"][0]["gate"]["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()

            result = router.execute_plan(plan)
            artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            result["executions"][0]["gate_artifact_sha256"],
            artifact_digest,
        )

    def test_stage_artifact_rejects_empty_input_bindings(self) -> None:
        for stage in ("discovery", "fetch", "extraction", "process", "curate"):
            payload = stage_artifact(stage)
            payload["input_bindings"] = []
            payload["result_digest_sha256"] = canonical_digest(
                {
                    key: value
                    for key, value in payload.items()
                    if key != "result_digest_sha256"
                }
            )
            with self.subTest(stage=stage):
                self.assertIn(
                    "input_bindings",
                    router._validate_stage_artifact(
                        stage,
                        payload,
                        "run-execute",
                        source_kind="public_http" if stage == "fetch" else None,
                    )
                    or "",
                )

    def test_discovery_consumes_the_same_query_plan_bound_by_router_request(self) -> None:
        plan_binding = query_plan_binding("run-execute")
        plan_payload = json.loads(Path(str(plan_binding["path"])).read_text())
        frozen_query_id = str(plan_payload["queries"][0]["query_id"])
        frozen_platform = str(plan_payload["queries"][0]["platform_id"])
        payload = stage_artifact(
            "discovery",
            queries=[
                {
                    "query_id": frozen_query_id,
                    "discovered_ids": [],
                    "status": "empty",
                    "platform": frozen_platform,
                    "backend_id": "github-cli",
                    "probe_id": "probe-001",
                    "authorization": "not_required",
                }
            ],
            counts={"queries": 1, "discoveries": 0},
        )
        payload["input_bindings"] = [discovery_binding_from_plan(plan_binding)]
        payload["result_digest_sha256"] = canonical_digest(
            {
                key: value
                for key, value in payload.items()
                if key != "result_digest_sha256"
            }
        )
        binding = payload["input_bindings"][0]
        request_binding = {
            "path": binding["path"],
            "artifact_sha256": binding["artifact_sha256"],
            "plan_digest_sha256": binding["result_digest_sha256"],
            "query_count": binding["record_count"],
            "query_ids_sha256": binding["record_ids_sha256"],
        }
        self.assertIsNone(
            router._validate_stage_artifact(
                "discovery",
                payload,
                "run-execute",
                query_plan_binding=request_binding,
            )
        )

        other_binding = query_plan_binding("run-execute")
        self.assertIn(
            "exact router QueryPlan",
            router._validate_stage_artifact(
                "discovery",
                payload,
                "run-execute",
                query_plan_binding=other_binding,
            )
            or "",
        )

        wrong_query_platform = copy.deepcopy(payload)
        wrong_query_platform["queries"][0]["platform"] = "youtube"
        wrong_query_platform["result_digest_sha256"] = canonical_digest(
            {
                key: value
                for key, value in wrong_query_platform.items()
                if key != "result_digest_sha256"
            }
        )
        self.assertIn(
            "platform",
            router._validate_stage_artifact(
                "discovery",
                wrong_query_platform,
                "run-execute",
                query_plan_binding=request_binding,
            )
            or "",
        )

        wrong_discovery_platform = copy.deepcopy(payload)
        wrong_discovery_platform["queries"][0].update(
            {"status": "complete", "discovered_ids": ["discovery-001"]}
        )
        wrong_discovery_platform["discoveries"] = [
            {
                "discovery_id": "discovery-001",
                "query_id": frozen_query_id,
                "platform": "youtube",
                "url": "https://example.com/article",
                "canonical_url": "https://example.com/article",
                "access_kind": "public_http",
            }
        ]
        wrong_discovery_platform["counts"] = {"queries": 1, "discoveries": 1}
        wrong_discovery_platform["result_digest_sha256"] = canonical_digest(
            {
                key: value
                for key, value in wrong_discovery_platform.items()
                if key != "result_digest_sha256"
            }
        )
        self.assertIn(
            "platform",
            router._validate_stage_artifact(
                "discovery",
                wrong_discovery_platform,
                "run-execute",
                query_plan_binding=request_binding,
            )
            or "",
        )

        legacy = copy.deepcopy(payload)
        legacy["input_bindings"][0]["relation"] = "scope_query_plan"
        legacy["result_digest_sha256"] = canonical_digest(
            {
                key: value
                for key, value in legacy.items()
                if key != "result_digest_sha256"
            }
        )
        self.assertIsNotNone(
            router._validate_stage_artifact(
                "discovery",
                legacy,
                "run-execute",
                query_plan_binding=request_binding,
            )
        )

    def test_stage_input_binding_rejects_replacement_and_identity_drift(self) -> None:
        payload = stage_artifact("process")
        original = copy.deepcopy(payload["input_bindings"][0])
        cases = {
            "artifact_sha256": {"artifact_sha256": "0" * 64},
            "contract": {"contract": "top50-extraction-result/v0"},
            "run_id": {"run_id": "other-run"},
            "stage": {"stage": "fetch"},
            "producer": {"producer_engine_id": "other-engine"},
            "result_digest": {"result_digest_sha256": "1" * 64},
            "record_count": {"record_count": 99},
            "record_ids": {"record_ids_sha256": "2" * 64},
        }
        for label, mutation in cases.items():
            mutated = copy.deepcopy(payload)
            mutated["input_bindings"][0].update(mutation)
            mutated["result_digest_sha256"] = canonical_digest(
                {
                    key: value
                    for key, value in mutated.items()
                    if key != "result_digest_sha256"
                }
            )
            with self.subTest(label=label):
                self.assertIsNotNone(
                    router._validate_stage_artifact("process", mutated, "run-execute")
                )
        self.assertEqual(payload["input_bindings"][0], original)

        upstream_path = Path(str(original["path"]))
        upstream = json.loads(upstream_path.read_text(encoding="utf-8"))
        upstream["candidates"].append({"candidate_id": "replacement"})
        upstream_path.write_text(json.dumps(upstream), encoding="utf-8")
        self.assertIn(
            "bound upstream",
            router._validate_stage_artifact("process", payload, "run-execute") or "",
        )

    def test_process_completion_rejects_candidate_set_drift_from_extraction(self) -> None:
        payload = stage_artifact(
            "process",
            processed_candidates=[
                {
                    "candidate_id": "processed-b",
                    "requires_fetch_time_dns_validation": False,
                }
            ],
            counts={
                "input_candidates": 1,
                "processed_candidates": 1,
                "exact_clusters": 0,
                "exact_duplicate_candidates": 0,
                "near_duplicate_reviews": 0,
                "dns_validation_required": 0,
            },
        )
        upstream = {
            "contract_version": "top50-extraction-result/v1",
            "run_id": "run-execute",
            "stage": "extraction",
            "candidates": [{"candidate_id": "extracted-a"}],
        }
        payload["input_bindings"] = [
            bound_artifact(
                "extraction_result",
                upstream,
                record_kind="candidate",
                record_ids=["extracted-a"],
            )
        ]
        payload["result_digest_sha256"] = canonical_digest(
            {
                key: value
                for key, value in payload.items()
                if key != "result_digest_sha256"
            }
        )

        self.assertIn(
            "do not conserve",
            router._validate_stage_artifact("process", payload, "run-execute") or "",
        )

    def test_python_process_rejects_rust_incompatible_semantics(self) -> None:
        valid_candidates = [
            {
                "candidate_id": "one",
                "requires_fetch_time_dns_validation": True,
            },
            {
                "candidate_id": "two",
                "requires_fetch_time_dns_validation": False,
            },
        ]
        cases = {
            "missing_dns_flag": {
                "processed_candidates": [{"candidate_id": "one"}],
                "counts": {
                    "input_candidates": 1,
                    "processed_candidates": 1,
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 0,
                },
            },
            "wrong_dns_count": {
                "processed_candidates": valid_candidates,
                "counts": {
                    "input_candidates": 2,
                    "processed_candidates": 2,
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 0,
                },
            },
            "forged_cluster": {
                "processed_candidates": valid_candidates,
                "exact_clusters": [
                    {
                        "cluster_id": "duplicate",
                        "candidate_ids": ["one", "ghost"],
                        "representative_candidate_id": "outside",
                    },
                    {
                        "cluster_id": "duplicate",
                        "candidate_ids": ["one", "two"],
                        "representative_candidate_id": "one",
                    },
                ],
                "counts": {
                    "input_candidates": 2,
                    "processed_candidates": 2,
                    "exact_clusters": 2,
                    "exact_duplicate_candidates": 999,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 1,
                },
            },
            "forged_review": {
                "processed_candidates": valid_candidates,
                "near_duplicate_reviews": [
                    {"review_id": "same", "candidate_ids": ["one"]},
                    {"review_id": "same", "candidate_ids": ["one", "two", "ghost"]},
                ],
                "counts": {
                    "input_candidates": 2,
                    "processed_candidates": 2,
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 2,
                    "dns_validation_required": 1,
                },
            },
        }
        for label, overrides in cases.items():
            payload = stage_artifact("process", **overrides)
            with self.subTest(label=label):
                self.assertIsNotNone(
                    router._validate_stage_artifact("process", payload, "run-execute")
                )

    def test_rust_process_compiles_input_from_extraction_in_clean_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = make_engine(
                root / "rust",
                "input_path = pathlib.Path(sys.argv[sys.argv.index('--input') + 1])\n"
                "payload = json.loads(input_path.read_text())\n"
                "assert payload['contract_version'] == 'top50-processor/v1'\n"
                "assert payload['run_id'] == 'run-execute'\n"
                "assert [row['candidate_id'] for row in payload['candidates']] == ['fresh-id']\n"
                "candidate = {'candidate_id':'fresh-id','requires_fetch_time_dns_validation':False}\n"
                "result = {'contract_version':'top50-processor-result/v1','engine_id':'rust-processor',"
                "'engine_version':'1.0.0','run_id':'run-execute','processed_candidates':[candidate],"
                "'exact_clusters':[],'near_duplicate_reviews':[],'counts':{'input_candidates':1,"
                "'processed_candidates':1,'exact_clusters':0,'exact_duplicate_candidates':0,"
                "'near_duplicate_reviews':0,'dns_validation_required':0}}\n"
                "material = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()\n"
                "import hashlib\nresult['result_digest_sha256'] = hashlib.sha256(material).hexdigest()\n"
                "print(json.dumps(result))\n",
            )
            plan = self.executable_plan([str(engine)])
            extraction = stage_artifact(
                "extraction",
                source_outcomes=[
                    {
                        "source_id": "source-001",
                        "upstream_job_id": "job-001",
                        "body_sha256": "d" * 64,
                        "content_class": "content",
                        "extractor_id": "html-v1",
                        "candidate_ids": ["fresh-id"],
                        "reason_codes": [],
                    }
                ],
                candidates=[
                    {
                        "candidate_id": "fresh-id",
                        "source_id": "source-001",
                        "platform": "web",
                        "url": "https://example.com/fresh",
                        "title": "Fresh candidate",
                        "author": "Author",
                        "published_at": "2026-08-24",
                        "content_type": "text/html",
                        "excerpt_or_observation": "A sufficiently detailed inspected excerpt for processing.",
                    }
                ],
                counts={
                    "input_sources": 1,
                    "content_sources": 1,
                    "blocked_sources": 0,
                    "candidates": 1,
                },
            )
            gate_path = Path(plan["stages"][0]["gate"]["path"])
            gate_path.write_text(json.dumps(extraction), encoding="utf-8")

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            result["executions"][0]["parsed_output"]["processed_candidates"][0][
                "candidate_id"
            ],
            "fresh-id",
        )

    def test_stale_rust_input_cannot_replace_extraction_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = make_engine(
                root / "rust",
                "input_path = pathlib.Path(sys.argv[sys.argv.index('--input') + 1])\n"
                "payload = json.loads(input_path.read_text())\n"
                "candidate_id = payload['candidates'][0]['candidate_id']\n"
                "candidate = {'candidate_id':candidate_id,'requires_fetch_time_dns_validation':False}\n"
                "result = {'contract_version':'top50-processor-result/v1','engine_id':'rust-processor',"
                "'engine_version':'1.0.0','run_id':'run-execute','processed_candidates':[candidate],"
                "'exact_clusters':[],'near_duplicate_reviews':[],'counts':{'input_candidates':1,"
                "'processed_candidates':1,'exact_clusters':0,'exact_duplicate_candidates':0,"
                "'near_duplicate_reviews':0,'dns_validation_required':0}}\n"
                "import hashlib\nmaterial = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()\n"
                "result['result_digest_sha256'] = hashlib.sha256(material).hexdigest()\n"
                "print(json.dumps(result))\n",
            )
            plan = self.executable_plan([str(engine)])
            stale_input = root / "rust-processor-input.json"
            stale_input.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-processor/v1",
                        "run_id": "run-execute",
                        "candidates": [
                            {
                                "candidate_id": "stale-id",
                                "platform": "web",
                                "url": "https://example.com/stale",
                                "title": "Stale",
                                "author": "Author",
                                "published_at": "2026-08-01",
                                "excerpt": "stale input",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            extraction = stage_artifact(
                "extraction",
                source_outcomes=[
                    {
                        "source_id": "source-001",
                        "upstream_job_id": "job-001",
                        "body_sha256": "d" * 64,
                        "content_class": "content",
                        "extractor_id": "html-v1",
                        "candidate_ids": ["fresh-id"],
                        "reason_codes": [],
                    }
                ],
                candidates=[
                    {
                        "candidate_id": "fresh-id",
                        "source_id": "source-001",
                        "platform": "web",
                        "url": "https://example.com/fresh",
                        "title": "Fresh candidate",
                        "author": "Author",
                        "published_at": "2026-08-24",
                        "content_type": "text/html",
                        "excerpt_or_observation": "A sufficiently detailed inspected excerpt for processing.",
                    }
                ],
                counts={
                    "input_sources": 1,
                    "content_sources": 1,
                    "blocked_sources": 0,
                    "candidates": 1,
                },
            )
            Path(plan["stages"][0]["gate"]["path"]).write_text(
                json.dumps(extraction), encoding="utf-8"
            )

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            result["executions"][0]["parsed_output"]["processed_candidates"][0][
                "candidate_id"
            ],
            "fresh-id",
        )

    def test_rust_rejects_same_id_input_replacement_after_compilation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engine = make_engine(
                root / "rust",
                "input_path = pathlib.Path(sys.argv[sys.argv.index('--input') + 1])\n"
                "authorized = json.loads(input_path.read_text())\n"
                "authorized['candidates'][0]['title'] = 'Attacker replacement'\n"
                "replacement = input_path.with_suffix('.attacker.tmp')\n"
                "replacement.write_text(json.dumps(authorized))\n"
                "replacement.replace(input_path)\n"
                "attacked_bytes = input_path.read_bytes()\n"
                "import hashlib\n"
                "if '--expected-input-sha256' in sys.argv:\n"
                "    expected = sys.argv[sys.argv.index('--expected-input-sha256') + 1]\n"
                "    if hashlib.sha256(attacked_bytes).hexdigest() != expected:\n"
                "        print('input digest mismatch', file=sys.stderr)\n"
                "        raise SystemExit(2)\n"
                "payload = json.loads(attacked_bytes)\n"
                "candidate = {'candidate_id':payload['candidates'][0]['candidate_id'],"
                "'title':payload['candidates'][0]['title'],"
                "'requires_fetch_time_dns_validation':False}\n"
                "result = {'contract_version':'top50-processor-result/v1','engine_id':'rust-processor',"
                "'engine_version':'1.0.0','run_id':'run-execute','processed_candidates':[candidate],"
                "'exact_clusters':[],'near_duplicate_reviews':[],'counts':{'input_candidates':1,"
                "'processed_candidates':1,'exact_clusters':0,'exact_duplicate_candidates':0,"
                "'near_duplicate_reviews':0,'dns_validation_required':0}}\n"
                "material = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()\n"
                "result['result_digest_sha256'] = hashlib.sha256(material).hexdigest()\n"
                "print(json.dumps(result))\n",
            )
            plan = self.executable_plan([str(engine)])
            extraction = stage_artifact(
                "extraction",
                source_outcomes=[
                    {
                        "source_id": "source-001",
                        "upstream_job_id": "job-001",
                        "body_sha256": "d" * 64,
                        "content_class": "content",
                        "extractor_id": "html-v1",
                        "candidate_ids": ["same-id"],
                        "reason_codes": [],
                    }
                ],
                candidates=[
                    {
                        "candidate_id": "same-id",
                        "source_id": "source-001",
                        "platform": "web",
                        "url": "https://example.com/original",
                        "title": "Authorized title",
                        "author": "Author",
                        "published_at": "2026-08-24",
                        "content_type": "text/html",
                        "excerpt_or_observation": "Authorized inspected content for processing.",
                    }
                ],
                counts={
                    "input_sources": 1,
                    "content_sources": 1,
                    "blocked_sources": 0,
                    "candidates": 1,
                },
            )
            Path(plan["stages"][0]["gate"]["path"]).write_text(
                json.dumps(extraction), encoding="utf-8"
            )

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        execution = result["executions"][0]
        self.assertEqual(execution["error_code"], "nonzero_exit")
        digest_index = execution["command"].index("--expected-input-sha256")
        self.assertEqual(
            execution["command"][digest_index + 1],
            execution["input_binding"]["artifact_sha256"],
        )

    def test_json_artifact_is_opened_once_for_parse_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "artifact.json"
            artifact.write_text(json.dumps({"status": "complete"}), encoding="utf-8")
            opens = 0
            real_open = os.open

            def counted_open(path: object, *args: object, **kwargs: object):
                nonlocal opens
                if Path(path) == artifact:
                    opens += 1
                return real_open(path, *args, **kwargs)

            with mock.patch.object(os, "open", counted_open):
                payload, digest = router._read_json_artifact(artifact)

        self.assertEqual(payload, {"status": "complete"})
        expected = hashlib.sha256(json.dumps({"status": "complete"}).encode("utf-8")).hexdigest()
        self.assertEqual(digest, expected)
        self.assertEqual(opens, 1)

    def test_stage_gate_rejects_cross_run_wrong_stage_and_digest_mismatch(self) -> None:
        cases = (
            ("cross_run", {"run_id": "other-run"}, None),
            ("wrong_stage", {"stage": "fetch"}, None),
            ("wrong_digest", {}, "0" * 64),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, overrides, forced_digest in cases:
                payload = {
                    "contract_version": "top50-extraction-result/v1",
                    "status": "complete",
                    "run_id": "run-execute",
                    "stage": "extraction",
                    **overrides,
                }
                engine = make_engine(
                    root / f"engine-{label}",
                    f"print(json.dumps({self.rust_output()!r}))\n",
                )
                plan = self.executable_plan([str(engine)])
                artifact = Path(plan["stages"][0]["gate"]["path"])
                artifact.write_text(json.dumps(payload), encoding="utf-8")
                plan["stages"][0]["gate"]["artifact_sha256"] = forced_digest or hashlib.sha256(artifact.read_bytes()).hexdigest()
                with self.subTest(label=label):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], "stage_artifact_required")

    def test_orchestrated_step_is_pending_until_completion_artifact_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "marker"
            engine = make_engine(
                root / "engine",
                f"pathlib.Path({str(marker)!r}).write_text('ran'); "
                "print(json.dumps({'contract':'top50-engine-result/v1','items':[]}))\n",
            )
            plan = self.executable_plan([str(engine)])
            plan["request"] = request(run_id="run-execute", stage="full")
            plan["stages"].insert(
                0,
                {
                    "id": "discovery-primary",
                    "stage": "discovery",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "orchestrated",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-discovery-result/v1",
                    "fallback_chain": ["python"],
                    "completion_artifact": {
                        "path": str(root / "discovery-result.json"),
                        "contract": "top50-discovery-result/v1",
                        "required_status": "complete",
                        "run_id": "run-execute",
                        "stage": "discovery",
                    },
                },
            )
            plan["stages"].insert(
                1,
                {
                    "id": "fetch-primary",
                    "stage": "fetch",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "covered",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-python-orchestration-result/v1",
                    "fallback_chain": ["python"],
                },
            )
            plan["stages"].insert(
                2,
                {
                    "id": "extraction-primary",
                    "stage": "extraction",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "covered",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-raw-fetch-bundle/v1",
                    "output_contract": "top50-extraction-result/v1",
                    "fallback_chain": ["python"],
                },
            )
            plan["stages"].extend(
                [
                    {
                        "id": "curate-primary",
                        "stage": "curate",
                        "engine": "python",
                        "role": "primary",
                        "execution_mode": "covered",
                        "command": [],
                        "timeout_seconds": 2,
                        "input_contract": "top50-raw-processed-bundle/v1",
                        "output_contract": "top50-curator-accepted-bundle/v1",
                        "fallback_chain": ["python"],
                    },
                    {
                        "id": "rank-primary",
                        "stage": "rank",
                        "engine": "python",
                        "role": "primary",
                        "execution_mode": "covered",
                        "command": [],
                        "timeout_seconds": 2,
                        "input_contract": "top50-research-bundle/v1",
                        "output_contract": "top50-ranking-summary/v1",
                        "fallback_chain": ["python"],
                    },
                ]
            )
            plan["selected_engines"] = ["python", "rust"]

            with self.assertRaises(router.RouterError):
                router.execute_plan(plan)

        self.assertFalse(marker.exists())

    def test_matching_completion_artifact_resumes_same_plan_without_editing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "discovery-result.json"
            artifact.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-discovery-result/v1",
                        "status": "complete",
                        "run_id": "run-execute",
                        "stage": "discovery",
                    }
                ),
                encoding="utf-8",
            )
            engine = make_engine(
                root / "engine",
                f"print(json.dumps({self.rust_output()!r}))\n",
            )
            plan = self.executable_plan([str(engine)])
            self.allow_process(plan, root)
            plan["request"] = request(run_id="run-execute", stage="full")
            plan["stages"].insert(
                0,
                {
                    "id": "discovery-primary",
                    "stage": "discovery",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "orchestrated",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-discovery-result/v1",
                    "fallback_chain": ["python"],
                    "completion_artifact": {
                        "path": str(artifact),
                        "contract": "top50-discovery-result/v1",
                        "required_status": "complete",
                        "run_id": "run-execute",
                        "stage": "discovery",
                    },
                },
            )
            plan["stages"].insert(
                1,
                {
                    "id": "fetch-primary",
                    "stage": "fetch",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "covered",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-python-orchestration-result/v1",
                    "fallback_chain": ["python"],
                },
            )
            plan["stages"].insert(
                2,
                {
                    "id": "extraction-primary",
                    "stage": "extraction",
                    "engine": "python",
                    "role": "primary",
                    "execution_mode": "covered",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-raw-fetch-bundle/v1",
                    "output_contract": "top50-extraction-result/v1",
                    "fallback_chain": ["python"],
                },
            )
            plan["stages"].extend(
                [
                    {
                        "id": "curate-primary",
                        "stage": "curate",
                        "engine": "python",
                        "role": "primary",
                        "execution_mode": "covered",
                        "command": [],
                        "timeout_seconds": 2,
                        "input_contract": "top50-raw-processed-bundle/v1",
                        "output_contract": "top50-curator-accepted-bundle/v1",
                        "fallback_chain": ["python"],
                    },
                    {
                        "id": "rank-primary",
                        "stage": "rank",
                        "engine": "python",
                        "role": "primary",
                        "execution_mode": "covered",
                        "command": [],
                        "timeout_seconds": 2,
                        "input_contract": "top50-research-bundle/v1",
                        "output_contract": "top50-ranking-summary/v1",
                        "fallback_chain": ["python"],
                    },
                ]
            )
            plan["selected_engines"] = ["python", "rust"]

            with self.assertRaises(router.RouterError):
                router.execute_plan(plan)

    def test_completion_artifact_rejects_wrong_run_or_stage_identity(self) -> None:
        cases = (("wrong-run", "discovery"), ("run-execute", "fetch"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (run_id, stage) in enumerate(cases):
                artifact = root / f"artifact-{index}.json"
                artifact.write_text(
                    json.dumps(
                        {
                            "contract_version": "top50-discovery-result/v1",
                            "status": "complete",
                            "run_id": run_id,
                            "stage": stage,
                        }
                    ),
                    encoding="utf-8",
                )
                plan = router.build_plan(
                    request(run_id="run-execute", stage="discovery", run_dir=directory),
                    probes=all_ready(),
                )
                canonical = Path(plan["stages"][0]["completion_artifact"]["path"])
                canonical.write_bytes(artifact.read_bytes())
                with self.subTest(run_id=run_id, stage=stage):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["executions"][0]["error_code"], "completion_artifact_mismatch")

    def test_orchestrated_completion_rejects_empty_shell_and_forged_fetch_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="discovery",
                    source_kind="platform_cli",
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            artifact = Path(plan["stages"][0]["completion_artifact"]["path"])
            artifact.write_text(
                json.dumps(
                    {
                        "contract_version": "top50-discovery-result/v1",
                        "status": "complete",
                        "run_id": "run-execute",
                        "stage": "discovery",
                    }
                ),
                encoding="utf-8",
            )
            result = router.execute_plan(plan)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["executions"][0]["error_code"], "completion_artifact_mismatch")

            fetch_plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="fetch",
                    source_kind="platform_cli",
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            fetch_artifact = Path(fetch_plan["stages"][0]["completion_artifact"]["path"])
            forged = stage_artifact(
                "fetch",
                results=[
                    fetch_result(
                        source_kind="platform_cli",
                        backend_kind="platform_adapter",
                        request_user_agent="OAI-SearchBot",
                        final_url="https://example.com/login",
                        content_class="content",
                        artifact=None,
                    )
                ],
                counts={"jobs": 1, "transport_success": 1, "blocked": 0},
            )
            fetch_artifact.write_text(json.dumps(forged), encoding="utf-8")
            result = router.execute_plan(fetch_plan)
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["executions"][0]["error_code"], "completion_artifact_mismatch")

    def test_fetch_provenance_is_scoped_to_the_actual_access_backend(self) -> None:
        platform_payload = stage_artifact(
            "fetch",
            results=[fetch_result(source_kind="platform_cli", backend_kind="platform_adapter")],
            counts={"jobs": 1, "transport_success": 1, "blocked": 0},
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "fetch", platform_payload, "run-execute", source_kind="platform_cli"
            )
        )

        browser_payload = stage_artifact(
            "fetch",
            results=[
                fetch_result(
                    source_kind="browser_session",
                    backend_kind="browser_session",
                    auth_state="authenticated",
                    http_status=None,
                )
            ],
            counts={"jobs": 1, "transport_success": 1, "blocked": 0},
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "fetch", browser_payload, "run-execute", source_kind="browser_session"
            )
        )

        go_payload = stage_artifact(
            "fetch",
            results=[
                fetch_result(
                    source_kind="public_http",
                    backend_kind="go_collector",
                    request_user_agent=router.TRANSPARENT_USER_AGENT,
                    robots_status="allowed",
                    robots_user_agent=router.ROBOTS_PRODUCT_TOKEN,
                )
            ],
            counts={"jobs": 1, "transport_success": 1, "blocked": 0},
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "fetch", go_payload, "run-execute", source_kind="public_http"
            )
        )

        transparent_payload = stage_artifact(
            "fetch",
            results=[
                fetch_result(
                    source_kind="public_http",
                    backend_kind="transparent_http",
                    request_user_agent=router.TRANSPARENT_USER_AGENT,
                    robots_status="allowed",
                )
            ],
            counts={"jobs": 1, "transport_success": 1, "blocked": 0},
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "fetch", transparent_payload, "run-execute", source_kind="public_http"
            )
        )

        for source_kind, item in (
            (
                "platform_cli",
                fetch_result(
                    source_kind="platform_cli",
                    backend_kind="platform_adapter",
                    request_user_agent="Claude-User",
                ),
            ),
            (
                "browser_session",
                fetch_result(
                    source_kind="browser_session",
                    backend_kind="platform_adapter",
                ),
            ),
            (
                "public_http",
                fetch_result(
                    source_kind="public_http",
                    backend_kind="go_collector",
                    request_user_agent="ordinary-curl",
                    robots_status="allowed",
                    robots_user_agent=router.ROBOTS_PRODUCT_TOKEN,
                ),
            ),
        ):
            payload = stage_artifact(
                "fetch",
                results=[item],
                counts={"jobs": 1, "transport_success": 1, "blocked": 0},
            )
            with self.subTest(source_kind=source_kind):
                self.assertIsNotNone(
                    router._validate_stage_artifact(
                        "fetch", payload, "run-execute", source_kind=source_kind
                    )
                )

    def test_every_fetch_outcome_rejects_caller_selected_or_official_bot_uas(self) -> None:
        direct_bot_names = (
            "OAI-SearchBot",
            "Claude-User",
            "Bytespider",
            "GrokBot",
            "Googlebot",
            "bingbot",
            "PerplexityBot",
            "ordinary-curl",
        )
        outcomes = (
            ("transport_success", ""),
            ("transport_failed", "network_error"),
            ("blocked_by_robots", "robots_disallowed"),
            ("blocked_by_policy", "policy_blocked"),
        )
        for transport_status, error_code in outcomes:
            for user_agent in direct_bot_names:
                artifact = (
                    {"path": "artifacts/job-001.body", "body_sha256": "a" * 64, "bytes": 123}
                    if transport_status == "transport_success"
                    else None
                )
                item = fetch_result(
                    source_kind="public_http",
                    backend_kind="transparent_http",
                    request_user_agent=user_agent,
                    transport_status=transport_status,
                    artifact=artifact,
                    error_code=error_code,
                    robots_status="allowed",
                )
                payload = stage_artifact(
                    "fetch",
                    results=[item],
                    counts={
                        "jobs": 1,
                        "transport_success": int(transport_status == "transport_success"),
                        "blocked": int(transport_status in {"blocked_by_robots", "blocked_by_policy"}),
                    },
                )
                with self.subTest(transport_status=transport_status, user_agent=user_agent):
                    self.assertIsNotNone(
                        router._validate_stage_artifact(
                            "fetch", payload, "run-execute", source_kind="public_http"
                        )
                    )

        for transport_status, error_code in outcomes:
            item = fetch_result(
                source_kind="platform_cli",
                backend_kind="platform_adapter",
                request_user_agent="Claude-User",
                transport_status=transport_status,
                artifact=(
                    {"path": "artifacts/job-001.body", "body_sha256": "a" * 64, "bytes": 123}
                    if transport_status == "transport_success"
                    else None
                ),
                error_code=error_code,
            )
            payload = stage_artifact(
                "fetch",
                results=[item],
                counts={
                    "jobs": 1,
                    "transport_success": int(transport_status == "transport_success"),
                    "blocked": int(transport_status in {"blocked_by_robots", "blocked_by_policy"}),
                },
            )
            with self.subTest(managed_transport_status=transport_status):
                self.assertIsNotNone(
                    router._validate_stage_artifact(
                        "fetch", payload, "run-execute", source_kind="platform_cli"
                    )
                )

    def test_managed_fetch_malformed_user_agent_types_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="fetch",
                    source_kind="platform_cli",
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            completion_path = Path(
                plan["stages"][0]["completion_artifact"]["path"]
            )
            for index, malformed in enumerate(([], {}, ["Claude-User"])):
                item = fetch_result(
                    source_kind="platform_cli",
                    backend_kind="platform_adapter",
                )
                item["request_user_agent"] = malformed
                artifact = stage_artifact(
                    "fetch",
                    results=[item],
                    counts={"jobs": 1, "transport_success": 1, "blocked": 0},
                )
                completion_path.write_text(json.dumps(artifact), encoding="utf-8")

                with self.subTest(index=index, malformed=malformed):
                    result = router.execute_plan(plan)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(
                        result["executions"][0]["error_code"],
                        "completion_artifact_mismatch",
                    )
                    self.assertIn(
                        "caller-selected user agent",
                        result["executions"][0]["validation_error"],
                    )

    def test_direct_http_fixed_identity_applies_to_non_success_outcomes(self) -> None:
        for backend_kind in ("go_collector", "transparent_http"):
            for transport_status in (
                "transport_failed",
                "blocked_by_robots",
                "blocked_by_policy",
            ):
                item = fetch_result(
                    source_kind="public_http",
                    backend_kind=backend_kind,
                    request_user_agent=router.TRANSPARENT_USER_AGENT,
                    robots_user_agent=(
                        router.ROBOTS_PRODUCT_TOKEN if backend_kind == "go_collector" else ""
                    ),
                    transport_status=transport_status,
                    artifact=None,
                    error_code="blocked_or_failed",
                )
                payload = stage_artifact(
                    "fetch",
                    results=[item],
                    counts={
                        "jobs": 1,
                        "transport_success": 0,
                        "blocked": int(transport_status != "transport_failed"),
                    },
                )
                with self.subTest(backend_kind=backend_kind, transport_status=transport_status):
                    self.assertIsNone(
                        router._validate_stage_artifact(
                            "fetch", payload, "run-execute", source_kind="public_http"
                        )
                    )

    def test_python_process_completion_uses_the_canonical_process_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="process",
                    workload="small",
                    source_kind="local_bundle",
                    engine_mode="python",
                    run_dir=directory,
                ),
                probes=all_ready(),
            )
            extraction_path = Path(plan["stages"][0]["completion_artifact"]["path"])
            extraction_path.write_text(json.dumps(stage_artifact("extraction")), encoding="utf-8")
            process_path = Path(plan["stages"][1]["completion_artifact"]["path"])
            process_path.write_text(json.dumps(stage_artifact("process")), encoding="utf-8")

            result = router.execute_plan(plan)

        self.assertEqual(plan["stages"][1]["completion_artifact"]["contract"], "top50-process-result/v1")
        self.assertEqual(result["status"], "complete")
        self.assertEqual([row["status"] for row in result["executions"]], ["covered", "covered"])

    def test_extraction_rejects_candidates_from_login_or_challenge_outcomes(self) -> None:
        candidate = {
            "candidate_id": "candidate-001",
            "source_id": "source-001",
            "platform": "web",
            "url": "https://example.com/login",
            "title": "Please sign in",
            "author": "unknown",
            "published_at": "unknown",
            "content_type": "text/html",
            "excerpt_or_observation": "captcha challenge",
        }
        outcome = {
            "source_id": "source-001",
            "upstream_job_id": "job-001",
            "body_sha256": "d" * 64,
            "content_class": "login_wall",
            "extractor_id": "html-v1",
            "candidate_ids": ["candidate-001"],
            "reason_codes": ["login_form_detected"],
        }
        payload = stage_artifact(
            "extraction",
            source_outcomes=[outcome],
            candidates=[candidate],
            counts={"input_sources": 1, "content_sources": 0, "blocked_sources": 1, "candidates": 1},
        )
        error = router._validate_stage_artifact("extraction", payload, "run-execute")
        self.assertIsNotNone(error)

    def test_go_manifest_replacement_is_rejected_before_engine_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "marker"
            original_jobs = [
                {
                    "job_id": "job-001",
                    "query_id": "query-001",
                    "platform": "web",
                    "url": "https://example.com/allowed",
                    "method": "GET",
                    "headers": {"Accept": "text/html"},
                }
            ]
            manifest = root / "go-collector-input.json"
            manifest_payload = {
                "contract_version": "top50-collector/v1",
                "run_id": "run-execute",
                "concurrency": 1,
                "per_host_interval_ms": 0,
                "timeout_ms": 1000,
                "max_response_bytes": 1024,
                "max_attempts": 1,
                "jobs": original_jobs,
            }
            manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
            engine = make_engine(
                root / "go",
                "if sys.argv[1:] == ['probe', '--json']:\n"
                "    print(json.dumps({'contract_version':'top50-engine/v1',"
                "'engine_id':'go-collector','engine_version':'1.0.0',"
                "'status':'ready','capabilities':['public_http_collect','get','bounded_concurrency']}))\n"
                "else:\n"
                f"    pathlib.Path({str(marker)!r}).write_text('ran')\n",
            )
            binding = public_http_binding(
                str(manifest),
                original_jobs,
                artifact_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            )
            plan = router.build_plan(
                request(
                    run_id="run-execute",
                    stage="fetch",
                    workload="large",
                    engine_mode="go",
                    run_dir=directory,
                    engine_paths={"go": str(engine)},
                    public_http_binding=binding,
                ),
                probes={
                    **all_ready({"go": str(engine)}),
                    "go": probe(
                        "go",
                        capabilities=("public_http_collect", "get", "bounded_concurrency"),
                        version="1.0.0",
                        base_command=[str(engine)],
                    ),
                },
            )
            manifest_payload["jobs"][0]["url"] = "https://attacker.example/"
            manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["executions"][0]["error_code"], "input_binding_mismatch")
        self.assertFalse(marker.exists())

    def test_declared_semantic_digest_is_used_for_dual_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            engines = []
            for name in ("first", "second"):
                payload = self.rust_output(semantic_digest="same-reviewed-result")
                engines.append(
                    make_engine(
                        root / name,
                        f"print(json.dumps({payload!r}))\n",
                    )
                )
            plan = self.dual_rust_plan(engines[0], engines[1], root)
            self.allow_process(plan, root)
            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["validation"]["matched"])

    def test_declared_semantic_digest_cannot_hide_changed_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_payload = self.rust_output(
                semantic_digest="forged-same",
                processed_candidates=[{"candidate_id": "same", "title": "before"}],
                counts={**self.rust_output()["counts"], "input_candidates": 1, "processed_candidates": 1},
            )
            second_payload = self.rust_output(
                semantic_digest="forged-same",
                processed_candidates=[{"candidate_id": "same", "title": "after"}],
                counts={**self.rust_output()["counts"], "input_candidates": 1, "processed_candidates": 1},
            )
            first = make_engine(root / "first", f"print(json.dumps({first_payload!r}))\n")
            second = make_engine(root / "second", f"print(json.dumps({second_payload!r}))\n")
            plan = self.dual_rust_plan(first, second, root)
            self.allow_process(plan, root)
            plan["dual_run"] = True

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "validation_mismatch")
        comparison = result["validation"]["comparisons"][0]
        self.assertFalse(comparison["matched"])
        self.assertEqual(comparison["diff"]["changed"][0]["changed_fields"], ["title"])

    def test_nested_business_identity_and_status_fields_are_not_envelope_noise(self) -> None:
        for field, before, after in (
            ("status", "accepted", "rejected"),
            ("stage", "reviewed", "pending"),
            ("engine_id", "source-engine-a", "source-engine-b"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                first_payload = self.rust_output(
                    processed_candidates=[{"candidate_id": "same", field: before}],
                    counts={**self.rust_output()["counts"], "input_candidates": 1, "processed_candidates": 1},
                )
                second_payload = self.rust_output(
                    processed_candidates=[{"candidate_id": "same", field: after}],
                    counts={**self.rust_output()["counts"], "input_candidates": 1, "processed_candidates": 1},
                )
                first = make_engine(root / "first", f"print(json.dumps({first_payload!r}))\n")
                second = make_engine(root / "second", f"print(json.dumps({second_payload!r}))\n")
                plan = self.dual_rust_plan(first, second, root)
                self.allow_process(plan, root)

                result = router.execute_plan(plan)

                self.assertEqual(result["status"], "validation_mismatch")
                comparison = result["validation"]["comparisons"][0]
                self.assertEqual(comparison["diff"]["changed"][0]["changed_fields"], [field])

    def test_generated_dual_run_can_resume_orchestrated_validator_and_compare(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary_payload = self.rust_output()
            primary = make_engine(
                root / "rust",
                f"print(json.dumps({primary_payload!r}))\n",
            )
            extraction = root / "extraction-result.json"
            extraction.write_text(
                json.dumps(
                    stage_artifact("extraction")
                ),
                encoding="utf-8",
            )
            validator = root / "process-validator-result.json"
            validator.write_text(
                json.dumps(stage_artifact("process", counts=primary_payload["counts"])),
                encoding="utf-8",
            )
            plan = self.executable_plan([str(primary)])
            plan["dual_run"] = True
            plan["stages"][0]["gate"] = {
                "type": "stage_artifact",
                "path": str(extraction),
                "contract": "top50-extraction-result/v1",
                "required_status": "complete",
                "run_id": "run-execute",
                "stage": "extraction",
                "fail_closed": True,
            }
            plan["stages"].append(
                {
                    "id": "process-validator",
                    "stage": "process",
                    "engine": "python",
                    "role": "validator",
                    "execution_mode": "orchestrated",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-python-orchestration-result/v1",
                    "fallback_chain": ["python"],
                    "validates_step": "process-primary",
                    "completion_artifact": {
                        "path": str(validator),
                        "contract": "top50-process-result/v1",
                        "required_status": "complete",
                        "run_id": "run-execute",
                        "stage": "process",
                    },
                }
            )
            plan["selected_engines"] = ["rust", "python"]

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["validation"]["matched"])
        self.assertEqual(result["executions"][1]["status"], "covered")

    def test_generated_dual_run_flags_mismatched_orchestrated_validator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = make_engine(
                root / "rust",
                f"print(json.dumps({self.rust_output(semantic_digest='primary-result')!r}))\n",
            )
            extraction = root / "extraction-result.json"
            extraction.write_text(
                json.dumps(
                    stage_artifact("extraction")
                ),
                encoding="utf-8",
            )
            validator = root / "process-validator-result.json"
            validator_payload = stage_artifact(
                "process",
                processed_candidates=[
                    {
                        "candidate_id": "different",
                        "title": "validator",
                        "requires_fetch_time_dns_validation": False,
                    }
                ],
                counts={
                    "input_candidates": 1,
                    "processed_candidates": 1,
                    "exact_clusters": 0,
                    "exact_duplicate_candidates": 0,
                    "near_duplicate_reviews": 0,
                    "dns_validation_required": 0,
                },
            )
            validator.write_text(json.dumps(validator_payload), encoding="utf-8")
            plan = self.executable_plan([str(primary)])
            plan["dual_run"] = True
            plan["stages"][0]["gate"] = {
                "type": "stage_artifact",
                "path": str(extraction),
                "contract": "top50-extraction-result/v1",
                "required_status": "complete",
                "run_id": "run-execute",
                "stage": "extraction",
                "fail_closed": True,
            }
            plan["stages"].append(
                {
                    "id": "process-validator",
                    "stage": "process",
                    "engine": "python",
                    "role": "validator",
                    "execution_mode": "orchestrated",
                    "command": [],
                    "timeout_seconds": 2,
                    "input_contract": "top50-python-orchestration/v1",
                    "output_contract": "top50-python-orchestration-result/v1",
                    "fallback_chain": ["python"],
                    "validates_step": "process-primary",
                    "completion_artifact": {
                        "path": str(validator),
                        "contract": "top50-process-result/v1",
                        "required_status": "complete",
                        "run_id": "run-execute",
                        "stage": "process",
                    },
                }
            )
            plan["selected_engines"] = ["rust", "python"]

            result = router.execute_plan(plan)

        self.assertEqual(result["status"], "validation_mismatch")
        self.assertFalse(result["validation"]["matched"])

    def test_rejects_invalid_plan_envelope_and_stage_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = make_engine(Path(directory) / "unused", "raise SystemExit(99)\n")
            bad_plan = self.executable_plan([str(engine)])
            bad_plan["schema"] = "top50-router-plan/v0"
            with self.assertRaises(router.RouterError):
                router.execute_plan(bad_plan)

            bad_gate = self.executable_plan([str(engine)])
            process = next(step for step in bad_gate["stages"] if step["stage"] == "process")
            process["gate"] = {
                "type": "stage_artifact",
                "path": "/tmp/value",
                "contract": "wrong",
                "required_status": "complete",
            }
            with self.assertRaises(router.RouterError):
                router.execute_plan(bad_gate)


class CliTests(unittest.TestCase):
    def test_plan_and_execute_cli_write_atomic_json_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "go-collector-input.json"
            input_payload = {
                "contract_version": "top50-collector/v1",
                "run_id": "run-001",
                "concurrency": 1,
                "per_host_interval_ms": 0,
                "timeout_ms": 1000,
                "max_response_bytes": 1024,
                "max_attempts": 1,
                "jobs": [
                    {
                        "job_id": "job-001",
                        "query_id": "query-001",
                        "platform": "web",
                        "url": "https://example.com/",
                        "method": "GET",
                        "headers": {"Accept": "text/plain"},
                    }
                ],
            }
            input_path.write_text(json.dumps(input_payload), encoding="utf-8")
            engine = make_engine(
                root / "python-engine",
                """
                if sys.argv[1:] == ['--help']:
                    print('ranker help')
                elif sys.argv[1:] == ['probe', '--json']:
                    print(json.dumps({'contract_version':'top50-engine/v1',
                        'engine_id':'go-collector','engine_version':'1.0.0',
                        'status':'ready','capabilities':['public_http_collect','get']}))
                else:
                    manifest = json.loads(pathlib.Path(sys.argv[sys.argv.index('--input') + 1]).read_text())
                    artifacts = pathlib.Path(sys.argv[sys.argv.index('--artifacts') + 1])
                    artifacts.mkdir(parents=True, exist_ok=True)
                    artifact = (artifacts / '0000000000000000-e3b0c44298fc1c14.body').resolve()
                    artifact.write_bytes(b'')
                    result = {'contract_version':'top50-collector-result/v1',
                        'engine_id':'go-collector','engine_version':'1.0.0',
                        'run_id':'run-001','status':'complete','results':[
                            {'job_id':job['job_id'],'query_id':job['query_id'],
                             'platform':job['platform'],'url':job['url'],'final_url':job['url'],
                             'status':'transport_success','attempts':1,'http_status':200,'content_type':'text/plain',
                             'bytes':0,'body_sha256':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                             'artifact_path':str(artifact),'robots_url':job['url'].split('/',3)[0]+'//'+job['url'].split('/',3)[2]+'/robots.txt',
                             'robots_status':'allowed','robots_rule':'','robots_user_agent':'TopFiftyCollector',
                             'request_accept':job['headers'].get('Accept',''),'request_accept_language':'','request_accept_encoding':'',
                             'response_content_language':'','response_content_encoding':'','response_vary':''}
                            for job in manifest['jobs']]}
                    pathlib.Path(sys.argv[sys.argv.index('--output') + 1]).write_text(json.dumps(result))
                    print(json.dumps(result))
                """,
            )
            request_path = root / "request.json"
            plan_path = root / "plan.json"
            result_path = root / "result.json"
            payload = request(
                stage="fetch",
                workload="large",
                engine_mode="go",
                run_dir=directory,
                engine_paths={"go": str(engine), "python": str(engine), "rust": str(root / "missing")},
                public_http_binding=public_http_binding(
                    str(input_path),
                    input_payload["jobs"],
                    artifact_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
                ),
            )
            request_path.write_text(json.dumps(payload), encoding="utf-8")

            planned = subprocess.run(
                [sys.executable, str(SCRIPT), "plan", "--input", str(request_path), "--output", str(plan_path)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(planned.returncode, 0, planned.stderr)
            self.assertTrue(plan_path.exists())
            plan_payload = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan_payload["selected_engines"], ["go"])
            planned_input_path = Path(
                plan_payload["stages"][0]["command"][
                    plan_payload["stages"][0]["command"].index("--input") + 1
                ]
            )
            self.assertEqual(planned_input_path, input_path)

            executed = subprocess.run(
                [sys.executable, str(SCRIPT), "execute", "--plan", str(plan_path), "--output", str(result_path)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(
                executed.returncode,
                0,
                executed.stderr
                + (result_path.read_text(encoding="utf-8") if result_path.exists() else ""),
            )
            self.assertEqual(json.loads(result_path.read_text(encoding="utf-8"))["status"], "complete")

    def test_probe_cli_emits_json_even_when_optional_engines_are_missing(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "probe", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema"], "top50-router-probe/v1")
        self.assertEqual(set(payload["engines"]), {"python", "go", "rust"})


if __name__ == "__main__":
    unittest.main()
