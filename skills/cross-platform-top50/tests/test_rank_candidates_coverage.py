from __future__ import annotations

import io
import ipaddress
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_rank_candidates as base


ranking = base.ranking


def frozen_args(paths: dict[str, Path], **overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "input": paths["candidates"],
        "manifest": paths["run_manifest"],
        "queries": paths["queries"],
        "sources": paths["sources"],
        "evidence_cards": paths["evidence_cards"],
        "platform_coverage": paths["platform_coverage"],
        "lineage_manifest": paths["lineage"],
        "curator_acceptance": paths["curator"],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class RankCandidatesCoverageTests(unittest.TestCase):
    public_ip = ipaddress.ip_address("93.184.216.34")

    def rank_one(self, *, top_n: int = 1):
        rows = [base.candidate("one")]
        payload = base.bundle(rows)
        with patch.object(
            ranking, "_resolved_ip_addresses", return_value=(self.public_ip,)
        ):
            result = ranking.rank_candidates(
                rows,
                top_n=top_n,
                context=base.context_from(payload),
                topic="test topic",
            )
        return rows, payload, result

    def test_in_process_cli_loads_frozen_lineage_and_writes_shortfall_package(self) -> None:
        payload = base.bundle([base.candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = base.write_frozen_rank_inputs(root, payload)
            output = root / "ranking-output"
            command = base.frozen_rank_cli_command(paths, output, top=2)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                patch.object(sys, "argv", command[1:]),
                patch.object(
                    ranking,
                    "_resolved_ip_addresses",
                    return_value=(self.public_ip,),
                ),
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = ranking.main()

            self.assertEqual(exit_code, 0, stderr.getvalue())
            self.assertEqual(stderr.getvalue(), "")
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["selected_count"], 1)
            self.assertEqual(summary["shortfall"], 1)
            self.assertEqual(
                {item.name for item in output.iterdir() if item.is_file()},
                ranking.PACKAGE_FILES,
            )
            self.assertEqual(
                json.loads((output / "ranking.json").read_text(encoding="utf-8"))[
                    "completion_gate"
                ]["status"],
                "shortfall",
            )
            self.assertIn(
                "只能发布为阶段性 Top K",
                (output / "report.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                json.loads(
                    (output / "package_validation.json").read_text(encoding="utf-8")
                )["status"],
                "pass",
            )

    def test_in_process_cli_validation_error_does_not_create_output(self) -> None:
        payload = base.bundle([base.candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = base.write_frozen_rank_inputs(root, payload)
            output = root / "ranking-output"
            command = base.frozen_rank_cli_command(paths, output, top=0)
            stderr = io.StringIO()

            with (
                patch.object(sys, "argv", command[1:]),
                redirect_stdout(io.StringIO()),
                redirect_stderr(stderr),
            ):
                exit_code = ranking.main()

            self.assertEqual(exit_code, 2)
            self.assertIn("top_n must be an integer from 1 to 100", stderr.getvalue())
            self.assertFalse(output.exists())

    def test_standalone_cli_rejects_semantically_forged_curator_artifact(self) -> None:
        """A valid digest cannot bless a non-independent, malformed review."""
        payload = base.bundle([base.candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = base.write_frozen_rank_inputs(root, payload)
            curator = json.loads(paths["curator"].read_text(encoding="utf-8"))
            curator["curator"] = {"id": "worker-1"}
            curator["worker_ids"] = ["worker-1"]
            curator["decisions"][0]["evidence_ids"] = ["ev-one", "ev-one"]
            curator["decisions"][0]["reason_codes"] = "not-an-array"
            curator["counts"] = {"garbage": -1}
            curator["result_digest_sha256"] = base.lineage.canonical_json_sha256(
                {
                    key: value
                    for key, value in curator.items()
                    if key != "result_digest_sha256"
                }
            )
            paths["curator"].write_text(json.dumps(curator), encoding="utf-8")
            output = root / "ranking-output"
            command = base.frozen_rank_cli_command(paths, output)
            stderr = io.StringIO()

            with (
                patch.object(sys, "argv", command[1:]),
                redirect_stdout(io.StringIO()),
                redirect_stderr(stderr),
            ):
                exit_code = ranking.main()

            self.assertEqual(exit_code, 2)
            self.assertIn("curator", stderr.getvalue())
            self.assertFalse(output.exists())

    def test_lineage_loader_returns_only_the_frozen_inputs(self) -> None:
        payload = base.bundle([base.candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = base.write_frozen_rank_inputs(root, payload)

            topic, rows, context = ranking.load_bundle(frozen_args(paths))

            self.assertEqual(topic, "test topic")
            self.assertEqual([row["id"] for row in rows], ["one"])
            self.assertEqual(context.manifest["run_id"], "run-test")
            self.assertEqual(context.queries, payload["queries"])
            self.assertEqual(context.sources, payload["sources"])
            self.assertEqual(context.evidence_cards, payload["evidence_cards"])
            self.assertEqual(context.platform_coverage, payload["platform_coverage"])

    def test_lineage_loader_rejects_bad_curator_identity_and_cli_path_drift(self) -> None:
        payload = base.bundle([base.candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = base.write_frozen_rank_inputs(root, payload)
            valid_curator = paths["curator"].read_bytes()

            malformed_cases = (
                (b"[]", "root must be an object"),
                (b"{}", "run_id is required"),
                (b"{", "rank input lineage validation failed"),
            )
            for raw, message in malformed_cases:
                paths["curator"].write_bytes(raw)
                with self.subTest(curator=raw), self.assertRaisesRegex(
                    ValueError, message
                ):
                    ranking.load_bundle(frozen_args(paths))

            paths["curator"].write_bytes(valid_curator)
            unfrozen_sources = root / "unfrozen-sources.tsv"
            unfrozen_sources.write_bytes(paths["sources"].read_bytes())
            with self.assertRaisesRegex(ValueError, "CLI paths do not match"):
                ranking.load_bundle(
                    frozen_args(paths, sources=unfrozen_sources)
                )

    def test_json_and_tsv_readers_fail_closed_on_unreadable_or_invalid_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_json = root / "valid.json"
            valid_json.write_text('{"status": "ok"}', encoding="utf-8")
            self.assertEqual(ranking._read_json(valid_json, "fixture"), {"status": "ok"})

            invalid_json = root / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot read fixture JSON"):
                ranking._read_json(invalid_json, "fixture")

            valid_tsv = root / "valid.tsv"
            valid_tsv.write_text(
                "platform\tcandidate_count\tdiscovered_count\n"
                "github\t2\t3\n",
                encoding="utf-8",
            )
            self.assertEqual(
                ranking._read_tsv(valid_tsv, "fixture")[0]["candidate_count"], 2
            )

            empty_tsv = root / "empty.tsv"
            empty_tsv.write_text("platform\tcandidate_count\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "TSV is empty"):
                ranking._read_tsv(empty_tsv, "fixture")

            invalid_tsv = root / "invalid.tsv"
            invalid_tsv.write_text(
                "platform\tcandidate_count\n"
                "github\tnot-an-integer\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid integer candidate_count"):
                ranking._read_tsv(invalid_tsv, "fixture")

            with self.assertRaisesRegex(ValueError, "cannot read fixture TSV"):
                ranking._read_tsv(root / "missing.tsv", "fixture")

    def test_package_readback_rejects_tampered_top_shape(self) -> None:
        rows, payload, result = self.rank_one()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "ranking-output"
            ranking.write_package(
                output, "test topic", rows, base.context_from(payload), result
            )
            (output / "package_validation.json").unlink()
            (output / "top.json").write_text(
                json.dumps({"topic": "test topic", "items": {"one": {}}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "items must be arrays"):
                ranking.validate_package(output, result)

    def test_package_validation_failure_removes_temporary_tree_atomically(self) -> None:
        rows, payload, result = self.rank_one()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "ranking-output"

            with (
                patch.object(
                    ranking,
                    "validate_package",
                    side_effect=ValueError("injected readback failure"),
                ),
                self.assertRaisesRegex(ValueError, "injected readback failure"),
            ):
                ranking.write_package(
                    output, "test topic", rows, base.context_from(payload), result
                )

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".ranking-output.*")), [])


if __name__ == "__main__":
    unittest.main()
