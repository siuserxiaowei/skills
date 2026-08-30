from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_worker_ledgers.py"
SPEC = importlib.util.spec_from_file_location("build_worker_ledgers", SCRIPT)
assert SPEC and SPEC.loader
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


def candidate(candidate_id: str, query_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "platform_id": "github",
        "query_id": query_id,
        "title": f"Title {candidate_id}",
        "summary": f"Summary for {candidate_id}",
        "canonical_url": f"https://example.test/{candidate_id}",
        "discovery_backend": "github_search",
        "readback_backend": "original_page",
        "accessed_at": "2026-08-26",
        "evidence_status": "accepted",
        "limitations": "",
    }


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class WorkerLedgerContentClusterTests(unittest.TestCase):
    def test_probe_status_does_not_hide_partial_success_with_blocked_mentions(self) -> None:
        self.assertTrue(
            build.probe_was_executed(
                "Ten repositories were probed; four descriptionless aliases "
                "remain provenance-blocked."
            )
        )
        self.assertTrue(build.probe_was_executed("partial_success"))
        self.assertFalse(build.probe_was_executed("blocked"))
        self.assertFalse(build.probe_was_executed("blocked: login required"))
        self.assertFalse(build.probe_was_executed("not executed"))
        self.assertFalse(build.probe_was_executed(""))

    def make_run(self, run_dir: Path) -> tuple[dict, dict]:
        excluded = candidate("duplicate-copy", "github-query-a")
        kept = candidate("canonical-copy", "github-query-b")
        (run_dir / "run_manifest.json").write_text(
            json.dumps({
                "required_platforms": ["github"],
                "per_platform_minimum_accepted": 2,
                "per_platform_discovery_target": 2,
            }),
            encoding="utf-8",
        )
        (run_dir / "candidates.json").write_text(
            json.dumps({"items": [excluded, kept]}),
            encoding="utf-8",
        )
        worker_excluded = {**excluded, "evidence_status": "worker_checked"}
        worker_kept = {**kept, "evidence_status": "worker_checked"}
        (run_dir / "review_queue.json").write_text(
            json.dumps({"items": [worker_excluded, worker_kept]}),
            encoding="utf-8",
        )
        write_tsv(
            run_dir / "platform_rules.tsv",
            [
                "platform_id", "platform_name", "query_intents", "probe_result",
                "discovery_route", "last_checked_at", "fetched_count",
                "reviewer_status", "coverage_state", "login_requirement",
                "notes", "next_step",
            ],
            [{
                "platform_id": "github",
                "platform_name": "GitHub",
                "query_intents": "github-query-a;github-query-b",
                "probe_result": "success",
                "discovery_route": "github_search",
                "last_checked_at": "2026-08-26",
                "fetched_count": "2",
                "reviewer_status": "curator_accepted",
                "coverage_state": "complete",
                "login_requirement": "none",
                "notes": "",
                "next_step": "find a replacement",
            }],
        )
        return excluded, kept

    def write_exclusions(self, run_dir: Path, rows: list[dict]) -> None:
        write_tsv(
            run_dir / build.CONTENT_CLUSTER_EXCLUSIONS,
            list(build.CONTENT_CLUSTER_EXCLUSION_FIELDS),
            rows,
        )

    def valid_exclusion(self) -> dict[str, str]:
        return {
            "candidate_id": "duplicate-copy",
            "kept_candidate_id": "canonical-copy",
            "cluster_basis": "same original body",
            "curator_reviewer": "curator",
            "reviewed_at": "2026-08-26",
        }

    def run_build(self, run_dir: Path) -> int:
        with mock.patch(
            "sys.argv",
            [str(SCRIPT), "--run-dir", str(run_dir)],
        ):
            return build.main()

    def test_valid_overlay_filters_every_rebuilt_ledger_and_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.make_run(run_dir)
            self.write_exclusions(run_dir, [self.valid_exclusion()])

            self.assertEqual(self.run_build(run_dir), 0)

            queries = {row["query_id"]: row for row in read_tsv(run_dir / "queries.tsv")}
            sources = read_tsv(run_dir / "sources.tsv")
            evidence = read_tsv(run_dir / "evidence_cards.tsv")
            coverage = read_tsv(run_dir / "platform_coverage.tsv")

            self.assertEqual(queries["github-query-a"]["result_count"], "0")
            self.assertEqual(queries["github-query-b"]["result_count"], "1")
            self.assertEqual(
                [row["candidate_id"] for row in sources],
                ["canonical-copy"],
            )
            self.assertEqual(sources[0]["source_status"], "accepted_readback")
            self.assertEqual(
                [row["candidate_id"] for row in evidence],
                ["canonical-copy"],
            )
            self.assertEqual(evidence[0]["verification_status"], "accepted")
            self.assertEqual(coverage[0]["discovered_count"], "1")
            self.assertEqual(coverage[0]["fetched_count"], "1")
            self.assertEqual(coverage[0]["accepted_count"], "1")
            self.assertEqual(coverage[0]["coverage_status"], "partial")

    def test_overlay_requires_exact_complete_unique_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            path = run_dir / build.CONTENT_CLUSTER_EXCLUSIONS
            path.write_text(
                "excluded_candidate_id\tkept_candidate_id\tcluster_basis\t"
                "curator_reviewer\treviewed_at\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "expected exact columns"):
                build.load_content_cluster_exclusions(run_dir)

            self.write_exclusions(
                run_dir,
                [self.valid_exclusion(), self.valid_exclusion()],
            )
            with self.assertRaisesRegex(
                ValueError,
                "duplicate content-cluster exclusion: duplicate-copy",
            ):
                build.load_content_cluster_exclusions(run_dir)

            invalid = {**self.valid_exclusion(), "cluster_basis": ""}
            self.write_exclusions(run_dir, [invalid])
            with self.assertRaisesRegex(ValueError, "empty.*cluster_basis"):
                build.load_content_cluster_exclusions(run_dir)

            path.write_text(
                "candidate_id\tkept_candidate_id\tcluster_basis\tcurator_reviewer\t"
                "reviewed_at\n"
                "duplicate-copy\tcanonical-copy\tsame body\tcurator\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "empty.*reviewed_at"):
                build.load_content_cluster_exclusions(run_dir)

    def test_overlay_rejects_unknown_or_nonaccepted_references(self) -> None:
        excluded = candidate("duplicate-copy", "q-a")
        kept = candidate("canonical-copy", "q-b")
        overlay = self.valid_exclusion()

        cases = [
            (
                {**overlay, "candidate_id": "does-not-exist"},
                [excluded, kept],
                "unknown_excluded=does-not-exist",
            ),
            (
                {**overlay, "kept_candidate_id": "does-not-exist"},
                [excluded, kept],
                "missing_kept=does-not-exist",
            ),
            (
                overlay,
                [{**excluded, "evidence_status": "worker_checked"}, kept],
                "unknown_excluded=duplicate-copy",
            ),
            (
                overlay,
                [{**excluded, "evidence_status": "ACCEPTED"}, kept],
                "unknown_excluded=duplicate-copy",
            ),
            (
                overlay,
                [excluded, {**kept, "evidence_status": "worker_checked"}],
                "missing_kept=canonical-copy",
            ),
        ]
        for candidate_overlay, accepted, expected in cases:
            with self.subTest(expected=expected):
                exclusions = {candidate_overlay["candidate_id"]: candidate_overlay}
                with self.assertRaisesRegex(ValueError, expected):
                    build.validate_content_cluster_exclusions(exclusions, accepted)

    def test_overlay_rejects_self_reference_or_excluded_retained_item(self) -> None:
        first = candidate("first-copy", "q-a")
        second = candidate("second-copy", "q-b")
        third = candidate("canonical-copy", "q-c")
        base = {
            "cluster_basis": "same original body",
            "curator_reviewer": "curator",
            "reviewed_at": "2026-08-26",
        }

        self_reference = {
            "first-copy": {
                **base,
                "candidate_id": "first-copy",
                "kept_candidate_id": "first-copy",
            }
        }
        with self.assertRaisesRegex(ValueError, "self_reference=first-copy"):
            build.validate_content_cluster_exclusions(
                self_reference,
                [first, second, third],
            )

        chained = {
            "first-copy": {
                **base,
                "candidate_id": "first-copy",
                "kept_candidate_id": "second-copy",
            },
            "second-copy": {
                **base,
                "candidate_id": "second-copy",
                "kept_candidate_id": "canonical-copy",
            },
        }
        with self.assertRaisesRegex(ValueError, "kept_is_excluded=second-copy"):
            build.validate_content_cluster_exclusions(
                chained,
                [first, second, third],
            )

    def test_duplicate_accepted_candidate_id_fails_closed(self) -> None:
        duplicate = candidate("duplicate-copy", "q-a")
        exclusions = {"duplicate-copy": self.valid_exclusion()}
        with self.assertRaisesRegex(
            ValueError,
            "duplicate candidate_id in candidates.json: duplicate-copy",
        ):
            build.validate_content_cluster_exclusions(
                exclusions,
                [duplicate, dict(duplicate), candidate("canonical-copy", "q-b")],
            )


if __name__ == "__main__":
    unittest.main()
