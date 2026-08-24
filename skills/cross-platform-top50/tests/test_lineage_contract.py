from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "lineage_contract.py"
SPEC = importlib.util.spec_from_file_location("lineage_contract", SCRIPT)
assert SPEC and SPEC.loader
lineage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lineage)

SOURCE_SCRIPT = SCRIPT.with_name("source_contract.py")
SOURCE_SPEC = importlib.util.spec_from_file_location(
    "lineage_source_contract_test", SOURCE_SCRIPT
)
assert SOURCE_SPEC and SOURCE_SPEC.loader
source_contract = importlib.util.module_from_spec(SOURCE_SPEC)
SOURCE_SPEC.loader.exec_module(source_contract)


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def make_run(root: Path, *, include_source_outcomes: bool = True) -> None:
    candidates = [
        {
            "id": "candidate-001",
            "reviewer_status": "accepted",
            "evidence_ids": ["evidence-001"],
        }
    ]
    (root / "candidates.json").write_text(
        json.dumps({"topic": "test", "candidates": candidates}), encoding="utf-8"
    )
    (root / "run_manifest.json").write_text(
        json.dumps({"run_id": "run-001", "topic": "test"}), encoding="utf-8"
    )
    write_tsv(
        root / "queries.tsv",
        [
            {
                "query_id": "query-001",
                "platform": "github",
                "query": "test",
                "backend": "search",
                "executed_at": "2026-08-24T00:00:00Z",
            }
        ],
    )
    write_tsv(
        root / "sources.tsv",
        [
            {
                "source_id": "source-001",
                "url": "https://example.com/",
                "platform": "github",
                "query_id": "query-001",
                "status": "verified",
                "source_outcome_digest_sha256": "a" * 64,
            }
        ],
    )
    write_tsv(
        root / "evidence_cards.tsv",
        [{"evidence_id": "evidence-001", "source_id": "source-001"}],
    )
    write_tsv(
        root / "platform_coverage.tsv",
        [{"platform": "web", "coverage_status": "complete"}],
    )
    if include_source_outcomes:
        outcome = source_contract.normalize_source_outcome(
            {
                "schema": "top50-source-observation/v1",
                "run_id": "run-001",
                "query_id": "query-001",
                "route_id": "github:public_http",
                "platform_id": "github",
                "adapter_id": "lineage-fixture",
                "access_kind": "public_http",
                "acquisition_method": "direct_http",
                "evidence_tier": "full_content",
                "url": "https://example.com/",
                "observed_at": "2026-08-24T00:00:00Z",
                "http_status": 200,
                "result_state": "success",
                "attempt": 1,
                "max_attempts": 1,
                "breaker_failure_count": 0,
                "breaker_threshold": 3,
                "breaker_cooldown_seconds": 300,
                "timeframe": {"start": "2026-01-01", "end": "2026-08-24"},
                "window_timezone": "UTC",
                "published_at": "2026-08-01T00:00:00Z",
                "published_at_confidence": "observed",
                "date_basis": "document_metadata",
                "content_sha256": "b" * 64,
                "response_endpoint": "https://example.com/",
                "payload_shape": "content_cards",
                "content_card_count": 1,
                "backend_id": "lineage-fixture",
                "probe_id": "probe-001",
                "authorization": "not_required",
                "error_code": None,
                "error_summary": None,
                "retry_after_seconds": None,
            },
            now=datetime(2026, 8, 24, tzinfo=timezone.utc),
        )
        with (root / "sources.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        rows[0]["source_outcome_digest_sha256"] = outcome[
            "outcome_digest_sha256"
        ]
        write_tsv(root / "sources.tsv", rows)
        (root / "source_outcomes.jsonl").write_text(
            json.dumps(outcome, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def write_manifest(root: Path) -> tuple[dict[str, object], Path]:
    manifest = lineage.build_rank_input_manifest(root, "run-001")
    path = root / "rank-input-manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest, path


def rewrite_source_outcomes(
    root: Path, outcomes: list[dict[str, object]]
) -> None:
    (root / "source_outcomes.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in outcomes
        ),
        encoding="utf-8",
    )


def make_curator(
    root: Path,
    manifest: dict[str, object],
    manifest_path: Path,
) -> dict[str, object]:
    descriptors = {row["input_id"]: row for row in manifest["files"]}
    process = {
        "contract_version": "top50-process-result/v1",
        "run_id": "run-001",
        "stage": "process",
        "status": "complete",
        "producer": {
            "engine_id": "python-control-plane",
            "engine_version": "0.1.0",
        },
        "input_bindings": [],
        "processed_candidates": [
            {
                "candidate_id": "candidate-001",
                "requires_fetch_time_dns_validation": False,
            }
        ],
        "exact_clusters": [],
        "near_duplicate_reviews": [],
        "counts": {
            "input_candidates": 1,
            "processed_candidates": 1,
            "exact_clusters": 0,
            "exact_duplicate_candidates": 0,
            "near_duplicate_reviews": 0,
            "dns_validation_required": 0,
        },
    }
    process["result_digest_sha256"] = lineage.canonical_json_sha256(process)
    process_path = root / "process-result.json"
    process_path.write_text(json.dumps(process), encoding="utf-8")

    def binding(
        relation: str,
        path: Path,
        artifact: dict[str, object],
        record_ids: list[str],
        record_kind: str,
    ) -> dict[str, object]:
        return {
            "relation": relation,
            "path": str(path),
            "artifact_sha256": lineage.hashlib.sha256(path.read_bytes()).hexdigest(),
            "contract": artifact["contract_version"],
            "run_id": artifact["run_id"],
            "stage": artifact["stage"],
            "required_status": artifact["status"],
            "producer_engine_id": artifact["producer"]["engine_id"],
            "result_digest_sha256": artifact["result_digest_sha256"],
            "record_kind": record_kind,
            "record_count": len(record_ids),
            "record_ids_sha256": lineage.canonical_json_sha256(sorted(record_ids)),
        }

    curator = {
        "contract_version": "top50-curator-acceptance/v1",
        "run_id": "run-001",
        "stage": "curate",
        "status": "accepted",
        "producer": {
            "engine_id": "python-control-plane",
            "engine_version": "0.1.0",
        },
        "input_bindings": [
            binding(
                "process_result",
                process_path,
                process,
                ["candidate-001"],
                "candidate",
            ),
            binding(
                "rank_input_manifest",
                manifest_path,
                manifest,
                [row["input_id"] for row in manifest["files"]],
                "file",
            ),
        ],
        "curator": {"id": "curator-001"},
        "worker_ids": ["worker-001"],
        "decisions": [
            {
                "candidate_id": "candidate-001",
                "decision": "accepted",
                "evidence_ids": ["evidence-001"],
                "reason_codes": [],
            }
        ],
        "accepted_candidate_ids": ["candidate-001"],
        "evidence_ledger_binding": {
            "artifact_sha256": descriptors["evidence_cards"]["artifact_sha256"]
        },
        "source_ledger_binding": {
            "artifact_sha256": descriptors["sources"]["artifact_sha256"]
        },
        "counts": {
            "input_candidates": 1,
            "accepted": 1,
            "rejected": 0,
            "blocked": 0,
        },
    }
    curator["result_digest_sha256"] = lineage.canonical_json_sha256(curator)
    return curator


class RankInputManifestTests(unittest.TestCase):
    def test_freeze_requires_authoritative_source_outcomes_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root, include_source_outcomes=False)

            with self.assertRaisesRegex(
                lineage.LineageError, "source_outcomes.jsonl"
            ):
                lineage.build_rank_input_manifest(root, "run-001")

    def test_build_and_validate_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest = lineage.build_rank_input_manifest(root, "run-001")
            manifest_path = root / "rank-input-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            validated = lineage.validate_rank_input_manifest(
                manifest_path, "run-001"
            )

        self.assertEqual(
            set(validated["paths"]), set(lineage.RANK_INPUT_SPECS)
        )
        self.assertEqual(validated["record_ids"]["candidates"], ["candidate-001"])

    def test_source_outcomes_reject_digest_tampering_and_blank_jsonl_records(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            outcome = json.loads(
                (root / "source_outcomes.jsonl").read_text(encoding="utf-8")
            )
            outcome["outcome_digest_sha256"] = "0" * 64
            rewrite_source_outcomes(root, [outcome])
            with self.assertRaisesRegex(lineage.LineageError, "digest"):
                lineage.build_rank_input_manifest(root, "run-001")

            make_run(root)
            (root / "source_outcomes.jsonl").write_text(
                json.dumps(outcome) + "\n\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(lineage.LineageError, "blank JSONL"):
                lineage.build_rank_input_manifest(root, "run-001")

    def test_source_outcomes_preserve_unreferenced_routes_and_reject_source_binding_drift(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            outcome = json.loads(
                (root / "source_outcomes.jsonl").read_text(encoding="utf-8")
            )
            extra = source_contract.normalize_source_outcome(
                {
                    "schema": "top50-source-observation/v1",
                    "run_id": "run-001",
                    "query_id": "query-001",
                    "route_id": "github:blocked-route",
                    "platform_id": "github",
                    "adapter_id": "blocked-fixture",
                    "access_kind": "public_http",
                    "acquisition_method": "direct_http",
                    "evidence_tier": "metadata_only",
                    "url": "https://example.com/blocked",
                    "observed_at": "2026-08-24T00:00:00Z",
                    "http_status": 403,
                    "result_state": "robots_blocked",
                    "attempt": 1,
                    "max_attempts": 1,
                    "breaker_failure_count": 0,
                    "breaker_threshold": 3,
                    "breaker_cooldown_seconds": 300,
                    "timeframe": {
                        "start": "2026-01-01",
                        "end": "2026-08-24",
                    },
                    "window_timezone": "UTC",
                    "published_at": None,
                    "published_at_confidence": "unknown",
                    "date_basis": "unavailable",
                    "content_sha256": None,
                    "response_endpoint": "https://example.com/blocked",
                    "payload_shape": "unknown",
                    "content_card_count": 0,
                    "backend_id": "blocked-fixture",
                    "probe_id": "probe-blocked",
                    "authorization": "not_required",
                    "error_code": "robots_blocked",
                    "error_summary": "robots disallow",
                    "retry_after_seconds": None,
                },
                now=datetime(2026, 8, 24, tzinfo=timezone.utc),
            )
            rewrite_source_outcomes(root, [outcome, extra])
            manifest = lineage.build_rank_input_manifest(root, "run-001")
            outcome_descriptor = next(
                row
                for row in manifest["files"]
                if row["input_id"] == "source_outcomes"
            )
            self.assertEqual(outcome_descriptor["record_count"], 2)
            self.assertEqual(manifest["counts"]["source_outcomes"], 2)

            for field, value, message in (
                ("query_id", "query-other", "query, platform, or URL"),
                ("platform", "youtube", "query, platform, or URL"),
                ("url", "https://example.com/other", "query, platform, or URL"),
                (
                    "source_outcome_digest_sha256",
                    "f" * 64,
                    "does not resolve",
                ),
            ):
                make_run(root)
                with (root / "sources.tsv").open(
                    encoding="utf-8", newline=""
                ) as handle:
                    rows = list(csv.DictReader(handle, delimiter="\t"))
                rows[0][field] = value
                write_tsv(root / "sources.tsv", rows)
                with self.subTest(field=field), self.assertRaisesRegex(
                    lineage.LineageError, message
                ):
                    lineage.build_rank_input_manifest(root, "run-001")

    def test_source_summary_rejects_accepted_and_complete_statuses(self) -> None:
        for status in ("accepted", "complete"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                make_run(root)
                with (root / "sources.tsv").open(
                    encoding="utf-8", newline=""
                ) as handle:
                    rows = list(csv.DictReader(handle, delimiter="\t"))
                rows[0]["status"] = status
                write_tsv(root / "sources.tsv", rows)

                with self.subTest(status=status), self.assertRaisesRegex(
                    lineage.LineageError, "summary status"
                ):
                    lineage.build_rank_input_manifest(root, "run-001")

    def test_curator_rejects_discovery_only_as_accepted_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            outcome = json.loads(
                (root / "source_outcomes.jsonl").read_text(encoding="utf-8")
            )
            outcome["acquisition"]["evidence_tier"] = "search_snippet"
            outcome["acquisition"]["content_sha256"] = None
            outcome["source_status"] = "discovered_only"
            outcome["eligibility"] = "discovery_only"
            outcome["may_enter_time_bounded_ranking"] = False
            outcome["may_enter_general_review"] = False
            outcome["outcome_digest_sha256"] = source_contract._digest(
                outcome, omit=("outcome_digest_sha256",)
            )
            source_contract.validate_source_outcome(outcome)
            rewrite_source_outcomes(root, [outcome])
            with (root / "sources.tsv").open(
                encoding="utf-8", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[0]["source_outcome_digest_sha256"] = outcome[
                "outcome_digest_sha256"
            ]
            write_tsv(root / "sources.tsv", rows)
            manifest, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(
                manifest_path, "run-001"
            )
            curator = make_curator(root, manifest, manifest_path)

            with self.assertRaisesRegex(
                lineage.LineageError, "reviewable fetched source outcome"
            ):
                lineage.validate_curator_against_rank_bundle(
                    curator, bundle, "run-001"
                )

    def test_rejects_replaced_file_same_id_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest = lineage.build_rank_input_manifest(root, "run-001")
            manifest_path = root / "rank-input-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            (root / "candidates.json").write_text(
                json.dumps(
                    {
                        "topic": "changed",
                        "candidates": [
                            {
                                "id": "candidate-001",
                                "reviewer_status": "accepted",
                                "evidence_ids": ["evidence-001"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(lineage.LineageError, "no longer matches"):
                lineage.validate_rank_input_manifest(manifest_path, "run-001")

    def test_rejects_descriptor_escape_and_duplicate_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest = lineage.build_rank_input_manifest(root, "run-001")
            manifest["files"][0]["path"] = str(root.parent / "outside.json")
            manifest["result_digest_sha256"] = lineage.canonical_json_sha256(
                {
                    key: value
                    for key, value in manifest.items()
                    if key != "result_digest_sha256"
                }
            )
            manifest_path = root / "rank-input-manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(lineage.LineageError, "escapes"):
                lineage.validate_rank_input_manifest(manifest_path, "run-001")

            (root / "candidates.json").write_text(
                json.dumps(
                    {
                        "candidates": [
                            {"id": "duplicate"},
                            {"candidate_id": "duplicate"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(lineage.LineageError, "unique"):
                lineage.build_rank_input_manifest(root, "run-001")

    def test_manifest_rejects_identity_producer_digest_counts_and_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            original = lineage.build_rank_input_manifest(root, "run-001")

            mutations = (
                ("fields", lambda value: value.__setitem__("unexpected", True)),
                ("contract", lambda value: value.__setitem__("contract_version", "wrong")),
                ("producer-type", lambda value: value.__setitem__("producer", [])),
                (
                    "producer-fields",
                    lambda value: value.__setitem__(
                        "producer", {"engine_id": "python-control-plane"}
                    ),
                ),
                (
                    "digest",
                    lambda value: value.__setitem__("result_digest_sha256", "0" * 64),
                ),
                ("files", lambda value: value.__setitem__("files", [])),
                (
                    "descriptor-fields",
                    lambda value: value["files"][0].__setitem__("unexpected", True),
                ),
                (
                    "descriptor-id",
                    lambda value: value["files"][0].__setitem__("input_id", "unknown"),
                ),
                (
                    "descriptor-media",
                    lambda value: value["files"][0].__setitem__("media_type", "text/plain"),
                ),
                (
                    "counts",
                    lambda value: value["counts"].__setitem__("candidates", 99),
                ),
            )
            for label, mutate in mutations:
                changed = json.loads(json.dumps(original))
                mutate(changed)
                if label not in {"fields", "contract", "digest"}:
                    changed["result_digest_sha256"] = lineage.canonical_json_sha256(
                        {
                            key: value
                            for key, value in changed.items()
                            if key != "result_digest_sha256"
                        }
                    )
                path = root / "rank-input-manifest.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.subTest(label=label), self.assertRaises(lineage.LineageError):
                    lineage.validate_rank_input_manifest(path, "run-001")

    def test_build_rejects_bad_run_ids_and_unreadable_input_types(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            with self.assertRaisesRegex(lineage.LineageError, "non-empty"):
                lineage.build_rank_input_manifest(root, " ")
            with self.assertRaisesRegex(lineage.LineageError, "does not match"):
                lineage.build_rank_input_manifest(root, "other-run")

            candidate_path = root / "candidates.json"
            candidate_path.unlink()
            candidate_path.mkdir()
            with self.assertRaisesRegex(lineage.LineageError, "cannot read immutable input"):
                lineage.build_rank_input_manifest(root, "run-001")

    def test_atomic_writer_replaces_file_and_cleans_failed_temporary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "manifest.json"
            output.write_text("old", encoding="utf-8")
            lineage.write_json_atomic(output, {"status": "new"})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {"status": "new"})
            self.assertFalse(list(root.glob(".manifest.json.*.tmp")))

            output.unlink()
            output.mkdir()
            with self.assertRaises(OSError):
                lineage.write_json_atomic(output, {"status": "blocked"})
            self.assertFalse(list(root.glob(".manifest.json.*.tmp")))

    def test_query_id_derivation_is_deterministic_and_unique(self) -> None:
        row = {
            "platform": "web",
            "query": "test",
            "backend": "search",
            "executed_at": "2026-08-24T00:00:00Z",
        }
        first = lineage.record_ids("queries", [row])
        second = lineage.record_ids("queries", [dict(reversed(list(row.items())))])
        self.assertEqual(first, second)
        with self.assertRaisesRegex(lineage.LineageError, "unique"):
            lineage.record_ids("queries", [row, row])

    def test_curator_round_trip_and_every_set_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(manifest_path, "run-001")
            curator = make_curator(root, manifest, manifest_path)
            lineage.validate_curator_against_rank_bundle(curator, bundle, "run-001")

            mutations = (
                ("identity", lambda value: value.__setitem__("status", "pending")),
                ("digest", lambda value: value.__setitem__("result_digest_sha256", "0" * 64)),
                ("decisions", lambda value: value.__setitem__("decisions", [])),
                ("accepted", lambda value: value.__setitem__("accepted_candidate_ids", [])),
                (
                    "evidence",
                    lambda value: value["decisions"][0].__setitem__(
                        "evidence_ids", ["missing"]
                    ),
                ),
                (
                    "source-ledger",
                    lambda value: value["source_ledger_binding"].__setitem__(
                        "artifact_sha256", "1" * 64
                    ),
                ),
                (
                    "manifest-binding",
                    lambda value: next(
                        binding
                        for binding in value["input_bindings"]
                        if binding["relation"] == "rank_input_manifest"
                    ).__setitem__("artifact_sha256", "2" * 64),
                ),
            )
            for label, mutate in mutations:
                changed = json.loads(json.dumps(curator))
                mutate(changed)
                if label not in {"identity", "digest"}:
                    changed["result_digest_sha256"] = lineage.canonical_json_sha256(
                        {
                            key: value
                            for key, value in changed.items()
                            if key != "result_digest_sha256"
                        }
                    )
                with self.subTest(label=label), self.assertRaises(lineage.LineageError):
                    lineage.validate_curator_against_rank_bundle(
                        changed, bundle, "run-001"
                    )

    def test_curator_rejects_incomplete_bundle_and_invalid_decision_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(manifest_path, "run-001")
            curator = make_curator(root, manifest, manifest_path)

            with self.assertRaisesRegex(lineage.LineageError, "incomplete"):
                lineage.validate_curator_against_rank_bundle(curator, {}, "run-001")

            mutations = (
                ("not-list", lambda value: value.__setitem__("decisions", {})),
                (
                    "bad-evidence",
                    lambda value: value["decisions"][0].__setitem__("evidence_ids", [""]),
                ),
                (
                    "accepted-without-evidence",
                    lambda value: value["decisions"][0].__setitem__("evidence_ids", []),
                ),
                ("bindings", lambda value: value.__setitem__("input_bindings", None)),
            )
            for label, mutate in mutations:
                changed = json.loads(json.dumps(curator))
                mutate(changed)
                changed["result_digest_sha256"] = lineage.canonical_json_sha256(
                    {
                        key: value
                        for key, value in changed.items()
                        if key != "result_digest_sha256"
                    }
                )
                with self.subTest(label=label), self.assertRaises(lineage.LineageError):
                    lineage.validate_curator_against_rank_bundle(
                        changed, bundle, "run-001"
                    )

    def test_curator_rejects_forged_semantics_and_incomplete_fixed_dag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(manifest_path, "run-001")
            curator = make_curator(root, manifest, manifest_path)

            mutations = (
                (
                    "non-independent",
                    lambda value: value.update(
                        {"curator": {"id": "worker-001"}, "worker_ids": ["worker-001"]}
                    ),
                    "independent",
                ),
                (
                    "duplicate-evidence",
                    lambda value: value["decisions"][0].__setitem__(
                        "evidence_ids", ["evidence-001", "evidence-001"]
                    ),
                    "unique",
                ),
                (
                    "reason-shape",
                    lambda value: value["decisions"][0].__setitem__(
                        "reason_codes", "not-an-array"
                    ),
                    "reason codes",
                ),
                (
                    "decision-enum",
                    lambda value: value["decisions"][0].__setitem__(
                        "decision", "approved"
                    ),
                    "curator",
                ),
                (
                    "counts",
                    lambda value: value.__setitem__("counts", {"garbage": -1}),
                    "counts",
                ),
                (
                    "missing-process-binding",
                    lambda value: value.__setitem__(
                        "input_bindings",
                        [
                            binding
                            for binding in value["input_bindings"]
                            if binding["relation"] != "process_result"
                        ],
                    ),
                    "fixed DAG",
                ),
            )
            for label, mutate, message in mutations:
                changed = json.loads(json.dumps(curator))
                mutate(changed)
                changed["result_digest_sha256"] = lineage.canonical_json_sha256(
                    {
                        key: value
                        for key, value in changed.items()
                        if key != "result_digest_sha256"
                    }
                )
                with self.subTest(label=label), self.assertRaisesRegex(
                    lineage.LineageError, message
                ):
                    lineage.validate_curator_against_rank_bundle(
                        changed, bundle, "run-001"
                    )

    def test_curator_rejects_redigested_semantically_invalid_process_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            manifest, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(manifest_path, "run-001")
            curator = make_curator(root, manifest, manifest_path)
            process_binding = next(
                binding
                for binding in curator["input_bindings"]
                if binding["relation"] == "process_result"
            )
            process_path = Path(process_binding["path"])
            process = json.loads(process_path.read_text(encoding="utf-8"))
            process["counts"]["dns_validation_required"] = 99
            process["result_digest_sha256"] = lineage.canonical_json_sha256(
                {
                    key: value
                    for key, value in process.items()
                    if key != "result_digest_sha256"
                }
            )
            process_path.write_text(json.dumps(process), encoding="utf-8")
            process_binding["artifact_sha256"] = lineage.hashlib.sha256(
                process_path.read_bytes()
            ).hexdigest()
            process_binding["result_digest_sha256"] = process[
                "result_digest_sha256"
            ]
            curator["result_digest_sha256"] = lineage.canonical_json_sha256(
                {
                    key: value
                    for key, value in curator.items()
                    if key != "result_digest_sha256"
                }
            )

            with self.assertRaisesRegex(
                lineage.LineageError, "DNS validation count"
            ):
                lineage.validate_curator_against_rank_bundle(
                    curator, bundle, "run-001"
                )

    def test_command_paths_match_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            _, manifest_path = write_manifest(root)
            bundle = lineage.validate_rank_input_manifest(manifest_path, "run-001")
            self.assertTrue(lineage.command_paths_match_bundle(bundle["paths"], bundle))
            wrong = dict(bundle["paths"])
            wrong["candidates"] = root / "other.json"
            self.assertFalse(lineage.command_paths_match_bundle(wrong, bundle))
            self.assertFalse(lineage.command_paths_match_bundle({}, bundle))

    def test_cli_freezes_validates_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            frozen = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "freeze-rank-inputs",
                    "--run-dir",
                    str(root),
                    "--run-id",
                    "run-001",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            manifest_path = root / "rank-input-manifest.json"
            checked = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "validate-rank-inputs",
                    "--manifest",
                    str(manifest_path),
                    "--run-id",
                    "run-001",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "validate-rank-inputs",
                    "--manifest",
                    str(manifest_path),
                    "--run-id",
                    "other-run",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("ERROR", rejected.stderr)

    def test_cli_freezes_to_explicit_output_and_rejects_missing_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_run(root)
            output = root / "custom-rank-manifest.json"
            frozen = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "freeze-rank-inputs",
                    "--run-dir",
                    str(root),
                    "--run-id",
                    "run-001",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(frozen.returncode, 0, frozen.stderr)
            self.assertTrue(output.is_file())
            self.assertEqual(json.loads(frozen.stdout)["output"], str(output))

            (root / "sources.tsv").unlink()
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "freeze-rank-inputs",
                    "--run-dir",
                    str(root),
                    "--run-id",
                    "run-001",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("ERROR", rejected.stderr)

    def test_parsers_reject_malformed_inputs(self) -> None:
        with self.assertRaisesRegex(lineage.LineageError, "JSON"):
            lineage.parse_json_bytes(b"{", "broken")
        with self.assertRaisesRegex(lineage.LineageError, "empty"):
            lineage.parse_tsv_bytes(b"header\n", "empty")
        with self.assertRaisesRegex(lineage.LineageError, "overflow"):
            lineage.parse_tsv_bytes(b"a\tb\n1\t2\t3\n", "overflow")
        with self.assertRaisesRegex(lineage.LineageError, "invalid integer"):
            lineage.parse_tsv_bytes(
                b"platform\tdiscovered_count\nweb\tbad\n", "bad"
            )
        with self.assertRaisesRegex(lineage.LineageError, "require"):
            lineage.record_ids("queries", [{"platform": "web"}])
        with self.assertRaisesRegex(lineage.LineageError, "candidate objects"):
            lineage.record_ids("candidates", "wrong")
        with self.assertRaisesRegex(lineage.LineageError, "JSON object"):
            lineage.record_ids("run_manifest", [])
        with self.assertRaisesRegex(lineage.LineageError, "record objects"):
            lineage.record_ids("sources", "wrong")
        with self.assertRaisesRegex(lineage.LineageError, "non-empty"):
            lineage.record_ids("sources", [{"source_id": ""}])
        self.assertTrue(lineage.is_sha256("a" * 64))
        self.assertFalse(lineage.is_sha256("A" * 64))


if __name__ == "__main__":
    unittest.main()
