from __future__ import annotations

import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import test_rank_candidates as rank_fixtures


TEST_ROOT = Path(__file__).parent
ROUTER_TEST = TEST_ROOT / "test_engine_router.py"
FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "engine_router_test_fixtures", ROUTER_TEST
)
assert FIXTURE_SPEC and FIXTURE_SPEC.loader
fixtures = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(fixtures)
router = fixtures.router

LINEAGE_SCRIPT = TEST_ROOT.parents[0] / "scripts" / "lineage_contract.py"
LINEAGE_SPEC = importlib.util.spec_from_file_location(
    "engine_router_coverage_lineage", LINEAGE_SCRIPT
)
assert LINEAGE_SPEC and LINEAGE_SPEC.loader
lineage = importlib.util.module_from_spec(LINEAGE_SPEC)
LINEAGE_SPEC.loader.exec_module(lineage)


def _refresh_digest(payload: dict[str, object]) -> None:
    payload["result_digest_sha256"] = fixtures.canonical_digest(
        {
            key: value
            for key, value in payload.items()
            if key != "result_digest_sha256"
        }
    )


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _make_rank_bundle(root: Path) -> tuple[dict[str, object], Path, dict[str, object]]:
    payload = rank_fixtures.bundle([rank_fixtures.candidate("candidate-001")])
    paths = rank_fixtures.write_frozen_rank_inputs(root, payload)
    manifest_path = paths["lineage"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    curator = json.loads(paths["curator"].read_text(encoding="utf-8"))
    return manifest, manifest_path, curator


def _remove_flag(command: list[str], flag: str) -> list[str]:
    changed = list(command)
    index = changed.index(flag)
    del changed[index : index + 2]
    return changed


class RankRuntimeBindingCoverageTests(unittest.TestCase):
    def test_rank_transport_normalizes_stdout_and_run_summary_to_one_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output_path = root / "run_summary.json"
            summary = {
                "requested_top_n": 1,
                "selected_count": 1,
                "rejected_count": 0,
                "shortfall": 0,
            }
            output_path.write_text(
                json.dumps({"topic": "test topic", **summary}), encoding="utf-8"
            )
            step = {
                "output_contract": "top50-ranking-summary/v1",
                "output_path": str(output_path),
                "run_id": "run-test",
            }

            parsed = router._load_execution_output(step, json.dumps(summary))

            self.assertEqual(parsed["contract_version"], "top50-ranking-summary/v1")
            self.assertEqual(parsed["run_id"], "run-test")
            self.assertEqual(parsed["summary"], summary)

    def test_real_ranker_subprocess_completes_through_router_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, curator = _make_rank_bundle(root)
            (root / "curate-result.json").write_text(
                json.dumps(curator), encoding="utf-8"
            )
            plan = router.build_plan(
                fixtures.request(
                    run_id="run-test",
                    stage="rank",
                    source_kind="local_bundle",
                    run_dir=str(root),
                    top_n=1,
                ),
                probes=fixtures.all_ready(),
            )
            rank_step = next(
                step for step in plan["stages"] if step["stage"] == "rank"
            )
            runtime_step = dict(rank_step)
            runtime_step["run_id"] = "run-test"

            execution = router._execute_step(runtime_step, "run-test")

            self.assertEqual(execution["status"], "complete", execution)
            self.assertEqual(execution["parsed_output"]["stage"], "rank")
            self.assertEqual(
                execution["parsed_output"]["summary"]["selected_count"], 1
            )
            self.assertEqual(curator["status"], "accepted")

    def test_rank_runtime_binding_accepts_one_frozen_bundle_and_rejects_swaps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, curator = _make_rank_bundle(root)
            plan = router.build_plan(
                fixtures.request(
                    run_id="run-test",
                    stage="rank",
                    source_kind="local_bundle",
                    run_dir=str(root),
                ),
                probes=fixtures.all_ready(),
            )
            rank_step = next(
                step for step in plan["stages"] if step["stage"] == "rank"
            )

            frozen, error = router._validate_rank_runtime_binding(
                rank_step, curator, "run-test"
            )
            self.assertIsNone(error)
            self.assertEqual(frozen["record_ids"]["candidates"], ["candidate-001"])

            missing_lineage = copy.deepcopy(rank_step)
            missing_lineage["command"] = _remove_flag(
                missing_lineage["command"], "--lineage-manifest"
            )
            self.assertIn(
                "missing lineage or curator",
                router._validate_rank_runtime_binding(
                    missing_lineage, curator, "run-test"
                )[1]
                or "",
            )

            wrong_gate = copy.deepcopy(rank_step)
            curator_index = wrong_gate["command"].index("--curator-acceptance") + 1
            wrong_gate["command"][curator_index] = str(root / "other-curator.json")
            self.assertIn(
                "does not match its gate",
                router._validate_rank_runtime_binding(
                    wrong_gate, curator, "run-test"
                )[1]
                or "",
            )

            missing_source = copy.deepcopy(rank_step)
            missing_source["command"] = _remove_flag(
                missing_source["command"], "--sources"
            )
            self.assertIn(
                "missing --sources",
                router._validate_rank_runtime_binding(
                    missing_source, curator, "run-test"
                )[1]
                or "",
            )

            missing_outcomes = copy.deepcopy(rank_step)
            missing_outcomes["command"] = _remove_flag(
                missing_outcomes["command"], "--source-outcomes"
            )
            self.assertIn(
                "missing --source-outcomes",
                router._validate_rank_runtime_binding(
                    missing_outcomes, curator, "run-test"
                )[1]
                or "",
            )

            swapped_candidates = copy.deepcopy(rank_step)
            candidate_index = swapped_candidates["command"].index("--input") + 1
            swapped_candidates["command"][candidate_index] = str(
                root / "candidate-set-b.json"
            )
            self.assertIn(
                "paths do not match",
                router._validate_rank_runtime_binding(
                    swapped_candidates, curator, "run-test"
                )[1]
                or "",
            )

            (root / "candidates.json").write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "id": "candidate-001",
                                "reviewer_status": "accepted",
                                "evidence_ids": ["evidence-001"],
                                "title": "replacement with the same ID",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "no longer matches",
                router._validate_rank_runtime_binding(
                    rank_step, curator, "run-test"
                )[1]
                or "",
            )

    def test_execute_fails_rank_before_subprocess_or_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = router.build_plan(
                fixtures.request(
                    run_id="run-execute-rank",
                    stage="rank",
                    source_kind="local_bundle",
                    run_dir=str(root),
                ),
                probes=fixtures.all_ready(),
            )
            curator = fixtures.stage_artifact(
                "curate", run_id="run-execute-rank"
            )
            curator_path = root / "curate-result.json"
            curator_path.write_text(json.dumps(curator), encoding="utf-8")
            python_probe = plan["probe_evidence"]["python"]

            with mock.patch.object(
                router, "probe_python_engine", return_value=python_probe
            ), mock.patch.object(router, "_execute_step") as execute_step:
                result = router.execute_plan(plan)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(
                result["executions"][-1]["error_code"],
                "rank_input_binding_mismatch",
            )
            self.assertIn(
                "rank-input-manifest.json",
                result["executions"][-1]["validation_error"],
            )
            execute_step.assert_not_called()
            self.assertFalse((root / "ranking-output").exists())


class NonEmptyStageContractCoverageTests(unittest.TestCase):
    def test_curator_revalidates_bound_process_business_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, curator = _make_rank_bundle(root)
            process_binding = next(
                binding
                for binding in curator["input_bindings"]
                if binding["relation"] == "process_result"
            )
            process_path = Path(process_binding["path"])
            process = json.loads(process_path.read_text(encoding="utf-8"))
            process["counts"]["dns_validation_required"] = 99
            process["result_digest_sha256"] = router._canonical_json_sha256(
                process, omit={"result_digest_sha256"}
            )
            process_path.write_text(json.dumps(process), encoding="utf-8")
            process_binding["artifact_sha256"] = router._sha256_file(process_path)[1]
            process_binding["result_digest_sha256"] = process["result_digest_sha256"]
            curator["result_digest_sha256"] = router._canonical_json_sha256(
                curator, omit={"result_digest_sha256"}
            )

            error = router._validate_stage_artifact(
                "curate", curator, "run-test", source_kind="local_bundle"
            )

            self.assertIsNotNone(error)
            self.assertIn("DNS validation count", str(error))

    def test_discovery_nonempty_ledger_conserves_ids_and_authorization(self) -> None:
        query_plan_binding = fixtures.query_plan_binding("run-execute")
        query_plan = json.loads(
            Path(str(query_plan_binding["path"])).read_text(encoding="utf-8")
        )
        frozen_query_id = str(query_plan["queries"][0]["query_id"])
        frozen_platform = str(query_plan["queries"][0]["platform_id"])
        payload = fixtures.stage_artifact(
            "discovery",
            queries=[
                {
                    "query_id": frozen_query_id,
                    "platform": frozen_platform,
                    "backend_id": "search-backend",
                    "probe_id": "probe-001",
                    "authorization": "granted",
                    "status": "complete",
                    "discovered_ids": ["discovery-001"],
                }
            ],
            discoveries=[
                {
                    "discovery_id": "discovery-001",
                    "query_id": frozen_query_id,
                    "platform": frozen_platform,
                    "url": "https://example.com/article",
                    "canonical_url": "https://example.com/article",
                    "access_kind": "public_http",
                }
            ],
            counts={"queries": 1, "discoveries": 1},
        )
        payload["input_bindings"] = [
            fixtures.discovery_binding_from_plan(query_plan_binding)
        ]
        _refresh_digest(payload)
        self.assertIsNone(
            router._validate_stage_artifact(
                "discovery",
                payload,
                "run-execute",
                query_plan_binding=query_plan_binding,
            )
        )

        unauthorized = copy.deepcopy(payload)
        unauthorized["queries"][0]["authorization"] = "not_granted"
        _refresh_digest(unauthorized)
        self.assertIn(
            "unauthorized",
            router._validate_stage_artifact(
                "discovery",
                unauthorized,
                "run-execute",
                query_plan_binding=query_plan_binding,
            )
            or "",
        )

        wrong_count = copy.deepcopy(payload)
        wrong_count["counts"]["discoveries"] = 2
        _refresh_digest(wrong_count)
        self.assertIn(
            "counts",
            router._validate_stage_artifact(
                "discovery",
                wrong_count,
                "run-execute",
                query_plan_binding=query_plan_binding,
            )
            or "",
        )

    def test_fetch_blocked_result_is_counted_and_requires_a_reason(self) -> None:
        blocked = fixtures.fetch_result(
            source_kind="platform_cli",
            backend_kind="platform_adapter",
            transport_status="blocked_by_policy",
            error_code="login_required",
        )
        payload = fixtures.stage_artifact(
            "fetch",
            results=[blocked],
            counts={"jobs": 1, "transport_success": 0, "blocked": 1},
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "fetch", payload, "run-execute", source_kind="platform_cli"
            )
        )

        unexplained = copy.deepcopy(payload)
        unexplained["results"][0]["error_code"] = ""
        _refresh_digest(unexplained)
        self.assertIn(
            "error_code",
            router._validate_stage_artifact(
                "fetch", unexplained, "run-execute", source_kind="platform_cli"
            )
            or "",
        )

    def test_extraction_nonempty_content_conserves_fetch_and_candidate_ids(self) -> None:
        outcome = {
            "source_id": "source-001",
            "upstream_job_id": "job-001",
            "body_sha256": "d" * 64,
            "content_class": "content",
            "extractor_id": "html-v1",
            "candidate_ids": ["candidate-001"],
            "reason_codes": [],
        }
        candidate = {
            "candidate_id": "candidate-001",
            "source_id": "source-001",
            "platform": "web",
            "url": "https://example.com/article",
            "title": "Inspected article",
            "author": "Author",
            "published_at": "2026-08-24",
            "content_type": "text/html",
            "excerpt_or_observation": "A directly inspected, auditable excerpt.",
        }
        payload = fixtures.stage_artifact(
            "extraction",
            source_outcomes=[outcome],
            candidates=[candidate],
            counts={
                "input_sources": 1,
                "content_sources": 1,
                "blocked_sources": 0,
                "candidates": 1,
            },
        )
        self.assertIsNone(
            router._validate_stage_artifact(
                "extraction", payload, "run-execute"
            )
        )

        login_wall = copy.deepcopy(payload)
        login_wall["source_outcomes"][0]["content_class"] = "login_wall"
        _refresh_digest(login_wall)
        self.assertIn(
            "non-content",
            router._validate_stage_artifact(
                "extraction", login_wall, "run-execute"
            )
            or "",
        )

    def test_curator_nonempty_decisions_cover_processed_set_and_ledgers(self) -> None:
        payload = fixtures.stage_artifact(
            "curate",
            curator={"id": "curator-001"},
            worker_ids=["worker-001"],
            decisions=[
                {
                    "candidate_id": "candidate-accepted",
                    "decision": "accepted",
                    "evidence_ids": ["evidence-001"],
                    "reason_codes": [],
                },
                {
                    "candidate_id": "candidate-rejected",
                    "decision": "rejected",
                    "evidence_ids": [],
                    "reason_codes": ["insufficient_evidence"],
                },
            ],
            accepted_candidate_ids=["candidate-accepted"],
            counts={
                "input_candidates": 2,
                "accepted": 1,
                "rejected": 1,
                "blocked": 0,
            },
        )
        self.assertIsNone(
            router._validate_stage_artifact("curate", payload, "run-execute")
        )

        mismatched = copy.deepcopy(payload)
        mismatched["accepted_candidate_ids"] = []
        _refresh_digest(mismatched)
        self.assertIn(
            "accepted candidate IDs",
            router._validate_stage_artifact(
                "curate", mismatched, "run-execute"
            )
            or "",
        )

        extra_root = copy.deepcopy(payload)
        extra_root["unexpected"] = True
        _refresh_digest(extra_root)
        self.assertIn(
            "fields",
            router._validate_stage_artifact(
                "curate", extra_root, "run-execute"
            )
            or "",
        )

        extra_decision = copy.deepcopy(payload)
        extra_decision["decisions"][0]["unexpected"] = True
        _refresh_digest(extra_decision)
        self.assertIn(
            "canonical objects",
            router._validate_stage_artifact(
                "curate", extra_decision, "run-execute"
            )
            or "",
        )


class RouterCliAndDefaultPathCoverageTests(unittest.TestCase):
    def test_probe_all_and_implicit_build_plan_use_default_routing_paths(self) -> None:
        python_evidence = fixtures.all_ready()["python"]
        go_evidence = fixtures.all_ready()["go"]
        rust_evidence = fixtures.all_ready()["rust"]
        with mock.patch.object(
            router, "probe_python_engine", return_value=python_evidence
        ) as python_probe, mock.patch.object(
            router,
            "probe_external_engine",
            side_effect=[go_evidence, rust_evidence],
        ) as external_probe:
            bundle = router.probe_all(timeout=1.5)

        self.assertEqual(set(bundle["engines"]), {"python", "go", "rust"})
        python_probe.assert_called_once()
        self.assertEqual(
            [call.args[0] for call in external_probe.call_args_list],
            ["go", "rust"],
        )

        request_payload = fixtures.request(
            stage="discovery", source_kind="local_bundle"
        )
        with mock.patch.object(
            router,
            "probe_all",
            return_value={"engines": fixtures.all_ready()},
        ) as probe_all:
            plan = router.build_plan(request_payload)
        probe_all.assert_called_once_with({})
        self.assertEqual(plan["stages"][0]["stage"], "discovery")

    def test_main_probe_plan_execute_and_error_return_stable_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            probe_bundle = {
                "schema": router.PROBE_SCHEMA,
                "probed_at": "2026-08-24T00:00:00Z",
                "engines": fixtures.all_ready(),
            }
            stdout = io.StringIO()
            with mock.patch.object(
                sys, "argv", [str(fixtures.SCRIPT), "probe", "--json"]
            ), mock.patch.object(
                router, "probe_all", return_value=probe_bundle
            ) as probe_all, contextlib.redirect_stdout(stdout):
                self.assertEqual(router.main(), 0)
            self.assertEqual(json.loads(stdout.getvalue())["schema"], router.PROBE_SCHEMA)
            probe_all.assert_called_once_with({}, timeout=router.DEFAULT_PROBE_TIMEOUT)

            request_path = root / "request.json"
            plan_path = root / "plan.json"
            request_payload = fixtures.request(
                run_id="run-cli-coverage",
                stage="discovery",
                source_kind="local_bundle",
                run_dir=str(root),
            )
            request_path.write_text(json.dumps(request_payload), encoding="utf-8")
            stdout = io.StringIO()
            with mock.patch.object(
                sys,
                "argv",
                [
                    str(fixtures.SCRIPT),
                    "plan",
                    "--input",
                    str(request_path),
                    "--output",
                    str(plan_path),
                ],
            ), mock.patch.object(
                router,
                "probe_all",
                return_value=probe_bundle,
            ), contextlib.redirect_stdout(stdout):
                self.assertEqual(router.main(), 0)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["run_id"], "run-cli-coverage")

            result_path = root / "result.json"
            stdout = io.StringIO()
            with mock.patch.object(
                sys,
                "argv",
                [
                    str(fixtures.SCRIPT),
                    "execute",
                    "--plan",
                    str(plan_path),
                    "--output",
                    str(result_path),
                ],
            ), mock.patch.object(
                router,
                "probe_python_engine",
                return_value=plan["probe_evidence"]["python"],
            ), contextlib.redirect_stdout(stdout):
                self.assertEqual(router.main(), 3)
            self.assertEqual(
                json.loads(result_path.read_text(encoding="utf-8"))["status"],
                "pending_orchestrator",
            )

            malformed = root / "malformed-request.json"
            malformed.write_text("{", encoding="utf-8")
            refused_output = root / "must-not-exist.json"
            stderr = io.StringIO()
            with mock.patch.object(
                sys,
                "argv",
                [
                    str(fixtures.SCRIPT),
                    "plan",
                    "--input",
                    str(malformed),
                    "--output",
                    str(refused_output),
                ],
            ), contextlib.redirect_stderr(stderr):
                self.assertEqual(router.main(), 2)
            self.assertIn("cannot read JSON", stderr.getvalue())
            self.assertFalse(refused_output.exists())


if __name__ == "__main__":
    unittest.main()
