from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


SKILL_ROOT = Path(__file__).parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "fuse_candidates.py"
INPUT_SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "fusion-input.schema.json"
RESULT_SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "fusion-result.schema.json"
SPEC = importlib.util.spec_from_file_location("top50_fuse_candidates", SCRIPT)
assert SPEC and SPEC.loader
fusion = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = fusion
SPEC.loader.exec_module(fusion)


def item(
    candidate_id: str,
    *,
    url: str | None = None,
    author_id: str = "author-a",
    published_at: str = "2026-08-20",
    date_confidence: str = "verified",
    source_role: str = "community",
    engagement: int = 0,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "url": url or f"https://example.com/{candidate_id}",
        "title": f"Title {candidate_id}",
        "author_id": author_id,
        "published_at": published_at,
        "date_confidence": date_confidence,
        "source_role": source_role,
        "engagement": {"likes": engagement},
        "acquisition_method": "platform_native",
        "evidence_status": "discovery_only",
    }


def ranked_list(
    list_id: str,
    platform: str,
    items: list[dict[str, object]],
    *,
    weight: float = 1.0,
    query_id: str = "q-main",
) -> dict[str, object]:
    return {
        "list_id": list_id,
        "platform": platform,
        "query_id": query_id,
        "weight": weight,
        "items": items,
    }


def payload(lists: list[dict[str, object]], **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": "top50-fusion-input/v1",
        "run_id": "run-fusion-001",
        "topic": "Agent research",
        "lists": lists,
        "selection": {
            "max_results": 50,
            "max_per_author": 3,
            "max_first_party_per_author": 5,
            "min_per_platform": 0,
        },
        "time_policy": {
            "mode": "strict",
            "from_date": "2026-07-26",
            "to_date": "2026-08-24",
        },
        "subject_author_ids": ["official-account"],
    }
    value.update(overrides)
    return value


class WeightedFusionTests(unittest.TestCase):
    def test_weighted_rrf_merges_only_stable_candidate_ids_and_preserves_provenance(self) -> None:
        request = payload(
            [
                ranked_list("x-exact", "x", [item("c1"), item("c2")], weight=1.0),
                ranked_list(
                    "web-review",
                    "web",
                    [item("c2"), item("c3")],
                    weight=0.5,
                    query_id="q-review",
                ),
            ]
        )

        result = fusion.fuse(request)

        self.assertEqual(result["contract_version"], "top50-fusion-result/v1")
        self.assertEqual([row["candidate_id"] for row in result["selected"]], ["c2", "c1", "c3"])
        merged = result["selected"][0]
        self.assertEqual(merged["consensus_count"], 2)
        self.assertEqual(merged["platforms"], ["web", "x"])
        self.assertEqual(merged["query_ids"], ["q-main", "q-review"])
        self.assertEqual(
            merged["rank_provenance"],
            [
                {"list_id": "web-review", "platform": "web", "query_id": "q-review", "rank": 1, "weight": 0.5},
                {"list_id": "x-exact", "platform": "x", "query_id": "q-main", "rank": 2, "weight": 1.0},
            ],
        )
        self.assertAlmostEqual(merged["weighted_rrf_score"], 0.5 / 61 + 1.0 / 62, places=12)
        self.assertEqual(merged["evidence_status"], "discovery_only")
        self.assertFalse(merged["curator_accepted"])

    def test_high_engagement_cannot_override_rrf_or_upgrade_evidence(self) -> None:
        low_rank_viral = item("viral", engagement=10_000_000)
        request = payload(
            [ranked_list("native", "x", [item("relevant"), low_rank_viral])]
        )

        result = fusion.fuse(request)

        self.assertEqual([row["candidate_id"] for row in result["selected"]], ["relevant", "viral"])
        viral = result["selected"][1]
        self.assertEqual(viral["evidence_status"], "discovery_only")
        self.assertNotIn("engagement", viral["fusion_signals"])
        self.assertFalse(viral["curator_accepted"])

    def test_result_is_byte_deterministic_for_equivalent_list_order(self) -> None:
        first_list = ranked_list("a", "x", [item("c1"), item("c2")])
        second_list = ranked_list("b", "web", [item("c2"), item("c3")])

        first = fusion.fuse(payload([first_list, second_list]))
        second = fusion.fuse(payload([second_list, first_list]))

        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )


class EligibilityAndDiversityTests(unittest.TestCase):
    def test_strict_window_quarantines_unknown_inferred_and_out_of_window_dates(self) -> None:
        request = payload(
            [
                ranked_list(
                    "native",
                    "x",
                    [
                        item("verified"),
                        item("unknown", published_at="unknown", date_confidence="unknown"),
                        item("inferred", date_confidence="inferred"),
                        item("old", published_at="2026-06-01"),
                    ],
                )
            ]
        )

        result = fusion.fuse(request)

        self.assertEqual([row["candidate_id"] for row in result["selected"]], ["verified"])
        self.assertEqual(
            [(row["candidate_id"], row["reason_code"]) for row in result["quarantined"]],
            [
                ("inferred", "date_not_verified"),
                ("old", "outside_time_window"),
                ("unknown", "date_unknown"),
            ],
        )

    def test_author_cap_has_bounded_first_party_exception_and_never_forces_platform_quota(self) -> None:
        rows = [item(f"ordinary-{i}", author_id="same") for i in range(1, 6)]
        rows += [
            item(f"official-{i}", author_id="official-account", source_role="first_party")
            for i in range(1, 7)
        ]
        request = payload([ranked_list("x-main", "x", rows)])

        result = fusion.fuse(request)

        selected_ids = [row["candidate_id"] for row in result["selected"]]
        self.assertEqual(selected_ids[:3], ["ordinary-1", "ordinary-2", "ordinary-3"])
        self.assertNotIn("ordinary-4", selected_ids)
        self.assertEqual(len([value for value in selected_ids if value.startswith("official-")]), 5)
        self.assertTrue(all(row["first_party_signal"] for row in result["selected"] if row["candidate_id"].startswith("official-")))
        self.assertEqual(result["selection_policy"]["min_per_platform"], 0)
        self.assertEqual(result["summary"]["platform_quota_forced"], 0)

    def test_optional_discovery_floor_uses_only_eligible_candidates_and_is_disclosed(self) -> None:
        request = payload(
            [
                ranked_list("x", "x", [item("x1"), item("x2"), item("x3")]),
                ranked_list("web", "web", [item("w1")], weight=0.1),
            ],
            selection={
                "max_results": 2,
                "max_per_author": 3,
                "max_first_party_per_author": 5,
                "min_per_platform": 1,
            },
        )

        result = fusion.fuse(request)

        self.assertEqual({row["candidate_id"] for row in result["selected"]}, {"x1", "w1"})
        self.assertEqual(result["summary"]["platform_quota_forced"], 1)
        self.assertEqual(result["selection_policy"]["scope"], "discovery_breadth_only")

    def test_author_cap_backfill_is_not_mislabeled_as_platform_quota(self) -> None:
        request = payload(
            [
                ranked_list(
                    "native",
                    "x",
                    [
                        item("same-1", author_id="same"),
                        item("same-2", author_id="same"),
                        item("other", author_id="other"),
                    ],
                )
            ],
            selection={
                "max_results": 2,
                "max_per_author": 1,
                "max_first_party_per_author": 2,
                "min_per_platform": 0,
            },
        )

        result = fusion.fuse(request)

        self.assertEqual(
            [row["candidate_id"] for row in result["selected"]],
            ["same-1", "other"],
        )
        self.assertEqual(result["summary"]["platform_quota_forced"], 0)

    def test_impossible_platform_floor_fails_closed(self) -> None:
        request = payload(
            [
                ranked_list("a", "a", [item("a1", author_id="a")]),
                ranked_list("b", "b", [item("b1", author_id="b")]),
                ranked_list("c", "c", [item("c1", author_id="c")]),
            ],
            selection={
                "max_results": 2,
                "max_per_author": 2,
                "max_first_party_per_author": 2,
                "min_per_platform": 1,
            },
        )

        with self.assertRaisesRegex(fusion.FusionError, "platform floor is infeasible"):
            fusion.fuse(request)


class ValidationAndCliTests(unittest.TestCase):
    def test_rejects_same_candidate_id_with_conflicting_identity(self) -> None:
        request = payload(
            [
                ranked_list("a", "x", [item("c1", url="https://example.com/a")]),
                ranked_list("b", "web", [item("c1", url="https://example.com/b")]),
            ]
        )

        with self.assertRaisesRegex(fusion.FusionError, "conflicting identity"):
            fusion.fuse(request)

    def test_rejects_conflicting_candidate_metadata_and_invalid_engagement(self) -> None:
        first = item("c1", author_id="author-a")
        second = item("c1", author_id="author-b")
        conflict = payload(
            [ranked_list("a", "x", [first]), ranked_list("b", "web", [second])]
        )
        with self.assertRaisesRegex(fusion.FusionError, "conflicting identity"):
            fusion.fuse(conflict)

        invalid = item("c2")
        invalid["engagement"] = {"likes": True}
        with self.assertRaisesRegex(fusion.FusionError, "engagement.likes"):
            fusion.fuse(payload([ranked_list("a", "x", [invalid])]))

    def test_rejects_unknown_fields_boolean_numbers_and_non_discovery_evidence(self) -> None:
        cases = []
        unknown = payload([ranked_list("a", "x", [item("c1")])])
        unknown["unexpected"] = True
        cases.append(unknown)
        boolean_weight = payload([ranked_list("a", "x", [item("c1")], weight=True)])
        cases.append(boolean_weight)
        accepted = item("c1")
        accepted["evidence_status"] = "accepted"
        cases.append(payload([ranked_list("a", "x", [accepted])]))
        unknown_item = item("c1")
        unknown_item["worker_accepted"] = True
        cases.append(payload([ranked_list("a", "x", [unknown_item])]))

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(fusion.FusionError):
                    fusion.fuse(case)

    def test_cli_writes_nothing_on_failure_and_probe_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bad_input = root / "bad.json"
            bad_input.write_text("{}", encoding="utf-8")
            output = root / "result.json"
            run = subprocess.run(
                [sys.executable, str(SCRIPT), "fuse", "--input", str(bad_input), "--output", str(output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(output.exists())
            error = json.loads(run.stderr)
            self.assertEqual(error["status"], "error")

            probe = subprocess.run(
                [sys.executable, str(SCRIPT), "probe", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            payload_out = json.loads(probe.stdout)
            self.assertEqual(payload_out["engine_id"], "python-fusion")
            self.assertIn("weighted_rrf", payload_out["capabilities"])


class SchemaParityTests(unittest.TestCase):
    def test_runtime_request_and_result_validate_against_published_schemas(self) -> None:
        request = payload(
            [
                ranked_list("native", "x", [item("c1"), item("c2")]),
                ranked_list("web", "web", [item("c2")], weight=0.25),
            ]
        )
        result = fusion.fuse(request)

        input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(input_schema).validate(request)
        jsonschema.Draft202012Validator(result_schema).validate(result)

    def test_schemas_reject_boolean_numbers_and_evidence_upgrades(self) -> None:
        input_schema = json.loads(INPUT_SCHEMA.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(input_schema)
        bad_weight = payload([ranked_list("native", "x", [item("c1")], weight=True)])
        upgraded = payload([ranked_list("native", "x", [item("c1")])])
        upgraded["lists"][0]["items"][0]["evidence_status"] = "accepted"

        self.assertTrue(list(validator.iter_errors(bad_weight)))
        self.assertTrue(list(validator.iter_errors(upgraded)))


if __name__ == "__main__":
    unittest.main()
