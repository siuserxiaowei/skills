from __future__ import annotations

import importlib.util
import csv
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_platform_library.py"
SPEC = importlib.util.spec_from_file_location("build_platform_library", SCRIPT)
assert SPEC and SPEC.loader
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


def accepted_item(platform_id: str, index: int = 0, backend: str | None = None) -> dict:
    return {
        "candidate_id": f"{platform_id}-{index}",
        "canonical_url": f"https://example.test/{platform_id}/{index}",
        "discovery_backend": backend or platform_id,
        "title": f"{platform_id} item {index}",
        "creator_name": f"creator {platform_id}",
        "published_at": f"2026-08-{index + 1:02d}",
    }


class StrictGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.required = list(build.DISPLAY_NAMES)
        self.assertEqual(len(self.required), 47)
        self.rules = {
            platform_id: {
                **{field: "verified" for field in build.REQUIRED_RULE_FIELDS},
                "platform_id": platform_id,
                "reviewer_status": "curator_accepted",
            }
            for platform_id in self.required
        }
        self.coverage = {
            platform_id: {"platform_id": platform_id, "coverage_status": "partial"}
            for platform_id in self.required
        }
        self.items = {
            platform_id: [accepted_item(platform_id, index) for index in range(10)]
            for platform_id in self.required
        }
        self.sources = [
            {
                "candidate_id": item["candidate_id"],
                "canonical_url": item["canonical_url"],
                "source_status": "accepted_readback",
                "readback_backend": "original_page",
            }
            for items in self.items.values()
            for item in items
        ]
        self.evidence = [
            {
                "candidate_id": item["candidate_id"],
                "source_url": item["canonical_url"],
                "verification_status": "accepted",
                "reviewer_status": "curator_accepted",
            }
            for items in self.items.values()
            for item in items
        ]

    def errors(self, queries: list[dict[str, str]] | None = None) -> list[str]:
        return build.strict_gate_errors(
            self.required,
            self.rules,
            self.coverage,
            queries or [],
            self.items,
            {},
            self.sources,
            self.evidence,
        )

    def test_valid_strict_metadata_has_no_errors(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_requires_all_rules_and_curator_acceptance(self) -> None:
        self.rules.pop("csdn")
        self.rules["github"]["reviewer_status"] = "worker_checked"
        errors = "\n".join(self.errors())
        self.assertIn("rules must contain exactly the 47 required platforms", errors)
        self.assertIn("missing=csdn", errors)
        self.assertIn("github=worker_checked", errors)

    def test_requires_complete_nonempty_rule_fields(self) -> None:
        self.rules["github"]["official_rule_sources"] = ""
        errors = "\n".join(self.errors())
        self.assertIn("rules have empty required fields", errors)
        self.assertIn("github[official_rule_sources]", errors)

    def test_requires_all_coverage_rows_and_terminal_statuses(self) -> None:
        self.coverage.pop("csdn")
        self.coverage["github"]["coverage_status"] = "pending"
        errors = "\n".join(self.errors())
        self.assertIn("coverage must contain exactly the 47 required platforms", errors)
        self.assertIn("missing=csdn", errors)
        self.assertIn("github=pending", errors)

    def test_complete_requires_two_distinct_executed_query_intents(self) -> None:
        self.coverage["github"]["coverage_status"] = "complete"
        one_executed_and_one_pending = [
            {"platform_id": "github", "intent": "tutorial", "executed_at": "2026-08-26T10:00:00+08:00"},
            {"platform_id": "github", "intent": "TUTORIAL", "executed_at": "2026-08-26T10:01:00+08:00"},
            {"platform_id": "github", "intent": "architecture", "executed_at": "pending"},
        ]
        errors = "\n".join(self.errors(one_executed_and_one_pending))
        self.assertIn("github=1", errors)

        two_executed = one_executed_and_one_pending + [
            {"platform_id": "github", "intent": "architecture", "executed_at": "2026-08-26T10:05:00+08:00"},
        ]
        self.assertEqual(self.errors(two_executed), [])

    def test_named_search_rows_reject_fallback_discovery_backends(self) -> None:
        self.items["google_search"][0]["discovery_backend"] = "exa:google_search"
        self.items["baidu_search"][0]["discovery_backend"] = "previous_run:baidu_search"
        self.items["bing_search"][0]["discovery_backend"] = "Bing Search"
        errors = "\n".join(self.errors())
        self.assertIn("google_search items must declare that named engine", errors)
        self.assertIn("google_search-0=exa:google_search", errors)
        self.assertNotIn("baidu_search items must declare", errors)

    def test_named_search_queries_reject_substitute_actual_backends(self) -> None:
        queries = [
            {
                "query_id": "google-1",
                "platform_id": "google_search",
                "intent": "exact",
                "executed_at": "2026-08-26T10:00:00+08:00",
                "actual_backend": "exa",
            },
            {
                "query_id": "bing-1",
                "platform_id": "bing_search",
                "intent": "exact",
                "executed_at": "2026-08-26T10:00:00+08:00",
                "actual_backend": "bing_search",
            },
            {
                "query_id": "baidu-1",
                "platform_id": "baidu_search",
                "intent": "exact",
                "executed_at": "2026-08-26T10:00:00+08:00",
                "actual_backend": "ddg:baidu_search",
            },
        ]
        errors = "\n".join(self.errors(queries))
        self.assertIn("google_search executed queries must use that named engine", errors)
        self.assertIn("google-1=exa", errors)
        self.assertIn("baidu_search executed queries must use that named engine", errors)
        self.assertIn("baidu-1=ddg:baidu_search", errors)
        self.assertNotIn("bing_search executed queries must use", errors)

    def test_named_search_accepts_descriptive_native_backend(self) -> None:
        self.items["google_search"][0]["discovery_backend"] = (
            "google_search native web results in in-app browser"
        )
        self.items["baidu_search"][0]["discovery_backend"] = (
            "baidu_search native web results for Pi extensions in in-app browser"
        )
        queries = [
            {
                "query_id": "google-native",
                "platform_id": "google_search",
                "intent": "exact",
                "executed_at": "2026-08-26T10:00:00+08:00",
                "actual_backend": "google_search native web results in in-app browser",
            },
            {
                "query_id": "baidu-native",
                "platform_id": "baidu_search",
                "intent": "extensions",
                "executed_at": "2026-08-26T10:00:00+08:00",
                "actual_backend": "baidu_search native web results in in-app browser",
            },
        ]
        errors = "\n".join(self.errors(queries))
        self.assertNotIn("google_search executed queries must use", errors)
        self.assertNotIn("google_search items must declare", errors)
        self.assertNotIn("baidu_search executed queries must use", errors)
        self.assertNotIn("baidu_search items must declare", errors)

    def test_named_search_descriptions_still_reject_fallback_tokens(self) -> None:
        self.items["bing_search"][0]["discovery_backend"] = (
            "DDG discovery then bing_search-labeled readback"
        )
        errors = "\n".join(self.errors())
        self.assertIn("bing_search items must declare that named engine", errors)

    def test_quota_shortages_fail(self) -> None:
        errors = "\n".join(
            build.strict_gate_errors(
                self.required,
                self.rules,
                self.coverage,
                [],
                self.items,
                {"csdn": 3},
                self.sources,
                self.evidence,
            )
        )
        self.assertIn("accepted quota shortages: csdn(-3)", errors)

    def test_exact_cross_platform_content_identity_fails(self) -> None:
        self.items["github"][0].update({
            "title": "A shared Pi article",
            "creator_name": "Same Author",
            "published_at": "2026-08-20",
        })
        self.items["juejin"][0].update({
            "title": "A shared Pi: article",
            "creator_name": "Same Author",
            "published_at": "2026-08-20",
        })
        errors = "\n".join(self.errors())
        self.assertIn("duplicate exact title+creator+date identity", errors)
        self.assertIn("github-0,juejin-0", errors)

    def test_every_accepted_item_requires_curator_source_and_evidence(self) -> None:
        self.sources = [
            source for source in self.sources if source["candidate_id"] != "github-0"
        ]
        self.evidence = [
            card for card in self.evidence if card["candidate_id"] != "github-1"
        ]
        errors = "\n".join(self.errors())
        self.assertIn("github-0[source]", errors)
        self.assertIn("github-1[evidence]", errors)

    def test_worker_only_ledger_rows_do_not_satisfy_accepted_evidence(self) -> None:
        for source in self.sources:
            if source["candidate_id"] == "youtube-0":
                source["source_status"] = "worker_readback_noted"
        for card in self.evidence:
            if card["candidate_id"] == "youtube-0":
                card["reviewer_status"] = "worker_checked"
        errors = "\n".join(self.errors())
        self.assertIn("youtube-0[source=invalid,evidence=invalid]", errors)


class ContentClusterExclusionTests(unittest.TestCase):
    @staticmethod
    def exclusion(
        candidate_id: str = "duplicate-copy",
        kept_candidate_id: str = "canonical-copy",
    ) -> dict[str, str]:
        return {
            "candidate_id": candidate_id,
            "kept_candidate_id": kept_candidate_id,
            "cluster_basis": "same original body",
            "curator_reviewer": "curator",
            "reviewed_at": "2026-08-26",
        }

    @staticmethod
    def accepted_ref(candidate_id: str, status: str = "accepted") -> dict[str, str]:
        return {
            "candidate_id": candidate_id,
            "evidence_status": status,
        }

    def write_exclusions(self, run_dir: Path, rows: list[dict[str, str]]) -> None:
        path = run_dir / build.CONTENT_CLUSTER_EXCLUSIONS
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(build.CONTENT_CLUSTER_EXCLUSION_FIELDS),
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    def test_exclusion_ledger_requires_complete_unique_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            self.write_exclusions(run_dir, [self.exclusion()])
            rows = build.load_content_cluster_exclusions(run_dir)
            self.assertEqual(rows["duplicate-copy"]["kept_candidate_id"], "canonical-copy")

    def test_exclusion_ledger_requires_exact_schema_and_nonempty_cells(self) -> None:
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

            path.write_text(
                "candidate_id\tkept_candidate_id\tcluster_basis\tcurator_reviewer\t"
                "reviewed_at\textra\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "expected exact columns"):
                build.load_content_cluster_exclusions(run_dir)

            invalid = {**self.exclusion(), "cluster_basis": ""}
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

    def test_exclusion_ledger_rejects_duplicate_extra_or_malformed_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            path = run_dir / build.CONTENT_CLUSTER_EXCLUSIONS
            self.write_exclusions(run_dir, [self.exclusion(), self.exclusion()])
            with self.assertRaisesRegex(
                ValueError,
                "duplicate content-cluster exclusion: duplicate-copy",
            ):
                build.load_content_cluster_exclusions(run_dir)

            path.write_text(
                "candidate_id\tkept_candidate_id\tcluster_basis\tcurator_reviewer\t"
                "reviewed_at\n"
                "duplicate-copy\tcanonical-copy\tsame body\tcurator\t2026-08-26\textra\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unexpected extra column data"):
                build.load_content_cluster_exclusions(run_dir)

            path.write_text(
                "candidate_id\tkept_candidate_id\tcluster_basis\tcurator_reviewer\t"
                "reviewed_at\n"
                '"duplicate-copy\tcanonical-copy\tsame body\tcurator\t2026-08-26\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "malformed TSV"):
                build.load_content_cluster_exclusions(run_dir)

    def test_valid_exclusion_references_are_accepted(self) -> None:
        overlay = self.exclusion()
        excluded_ids = build.validate_content_cluster_exclusions(
            {overlay["candidate_id"]: overlay},
            [
                self.accepted_ref("duplicate-copy"),
                self.accepted_ref("canonical-copy"),
            ],
        )
        self.assertEqual(excluded_ids, {"duplicate-copy"})

    def test_exclusion_references_must_resolve_to_accepted_candidates(self) -> None:
        overlay = self.exclusion()
        excluded = self.accepted_ref("duplicate-copy")
        kept = self.accepted_ref("canonical-copy")
        cases = [
            (
                self.exclusion(candidate_id="does-not-exist"),
                [excluded, kept],
                "unknown_excluded=does-not-exist",
            ),
            (
                self.exclusion(kept_candidate_id="does-not-exist"),
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
                [excluded, {**kept, "evidence_status": "worker_checked"}],
                "missing_kept=canonical-copy",
            ),
        ]
        for candidate_overlay, candidates, expected in cases:
            with self.subTest(expected=expected):
                exclusions = {candidate_overlay["candidate_id"]: candidate_overlay}
                with self.assertRaisesRegex(ValueError, expected):
                    build.validate_content_cluster_exclusions(exclusions, candidates)

    def test_exclusion_rejects_self_reference_or_excluded_kept_candidate(self) -> None:
        accepted = [
            self.accepted_ref("first-copy"),
            self.accepted_ref("second-copy"),
            self.accepted_ref("canonical-copy"),
        ]
        self_reference = self.exclusion("first-copy", "first-copy")
        with self.assertRaisesRegex(ValueError, "self_reference=first-copy"):
            build.validate_content_cluster_exclusions(
                {"first-copy": self_reference},
                accepted,
            )

        first = self.exclusion("first-copy", "second-copy")
        second = self.exclusion("second-copy", "canonical-copy")
        with self.assertRaisesRegex(ValueError, "kept_is_excluded=second-copy"):
            build.validate_content_cluster_exclusions(
                {"first-copy": first, "second-copy": second},
                accepted,
            )

    def test_duplicate_candidate_id_fails_before_exclusion_filtering(self) -> None:
        duplicate = self.accepted_ref("duplicate-copy")
        overlay = self.exclusion()
        with self.assertRaisesRegex(
            ValueError,
            "duplicate candidate_id in candidates.json: duplicate-copy",
        ):
            build.validate_content_cluster_exclusions(
                {"duplicate-copy": overlay},
                [
                    duplicate,
                    dict(duplicate),
                    self.accepted_ref("canonical-copy"),
                ],
            )

if __name__ == "__main__":
    unittest.main()
