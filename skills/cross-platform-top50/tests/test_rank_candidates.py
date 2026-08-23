from __future__ import annotations

import importlib.util
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "rank_candidates.py"
SPEC = importlib.util.spec_from_file_location("rank_candidates", SCRIPT)
assert SPEC and SPEC.loader
ranking = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ranking
SPEC.loader.exec_module(ranking)

LINEAGE_SCRIPT = SCRIPT.with_name("lineage_contract.py")
LINEAGE_SPEC = importlib.util.spec_from_file_location("lineage_contract_test", LINEAGE_SCRIPT)
assert LINEAGE_SPEC and LINEAGE_SPEC.loader
lineage = importlib.util.module_from_spec(LINEAGE_SPEC)
LINEAGE_SPEC.loader.exec_module(lineage)


def candidate(identifier: str, *, url: str | None = None) -> dict[str, object]:
    return {
        "id": identifier,
        "platform": "github",
        "author": "Example Author",
        "content_type": "article",
        "url": url or f"https://example.com/articles/{identifier}",
        "title": f"Reliable research item {identifier}",
        "excerpt": (
            f"A directly inspected, sufficiently detailed observation for {identifier} "
            "that a third-party curator can audit against the public source page."
        ),
        "accessed_at": "2026-08-23T09:00:00+08:00",
        "published_at": "2026-07-01",
        "reviewer_status": "accepted",
        "evidence_grade": "strong",
        "evidence_ids": [f"ev-{identifier}"],
        "worker_id": "worker-1",
        "relevance": 90,
        "source_quality": 85,
        "freshness": 80,
    }


def bundle(rows: list[dict[str, object]]) -> dict[str, object]:
    platforms: dict[str, int] = {}
    for row in rows:
        platform = str(row["platform"])
        platforms[platform] = platforms.get(platform, 0) + 1

    sources = [
        {
            "source_id": f"src-{row['id']}",
            "url": row["url"],
            "status": "verified",
            "source_type": "primary",
            "platform": row["platform"],
        }
        for row in rows
    ]
    cards = [
        {
            "evidence_id": f"ev-{row['id']}",
            "source_id": f"src-{row['id']}",
            "source_url": row["url"],
            "claim": f"The inspected item {row['id']} is relevant to the research topic.",
            "supports": "fact",
            "access_date": "2026-08-23",
            "excerpt_or_observation": row["excerpt"],
            "evidence_grade": "strong",
            "reviewer_status": "accepted",
            "reviewer_id": "curator-1",
        }
        for row in rows
    ]
    queries = []
    for platform in platforms:
        queries.extend(
            [
                {
                    "platform": platform,
                    "query": "topic exact",
                    "backend": "public_search",
                    "executed_at": "2026-08-23T08:00:00+08:00",
                    "status": "complete",
                    "candidate_count": platforms[platform],
                },
                {
                    "platform": platform,
                    "query": "topic practical guide",
                    "backend": "public_search",
                    "executed_at": "2026-08-23T08:05:00+08:00",
                    "status": "complete",
                    "candidate_count": 0,
                },
            ]
        )
    coverage = [
        {
            "platform": platform,
            "coverage_status": "complete",
            "discovered_count": count,
            "fetched_count": count,
            "eligible_count": count,
            "blocked_count": 0,
            "rejected_count": 0,
        }
        for platform, count in platforms.items()
    ]
    manifest = {
        "schema_version": "1.0",
        "run_id": "run-test",
        "topic": "test topic",
        "scope": {
            "topic": "test topic",
            "required_platforms": sorted(platforms),
            "claim_20_plus_platforms": False,
        },
        "phases": {
            "scope": "complete",
            "discovery": "complete",
            "fetch": "complete",
            "extraction": "complete",
            "worker_check": "complete",
            "curator_acceptance": "complete",
            "ranking": "pending",
        },
        "curator": {"id": "curator-1"},
        "workers": [{"id": "worker-1"}],
        "coverage": coverage,
        "errors": [],
        "counts": {
            "candidates": len(rows),
            "queries": len(queries),
            "sources": len(sources),
            "evidence_cards": len(cards),
            "platforms": len(coverage),
            "discovered": len(rows),
        },
    }
    return {
        "topic": "test topic",
        "candidates": rows,
        "run_manifest": manifest,
        "queries": queries,
        "sources": sources,
        "evidence_cards": cards,
        "platform_coverage": coverage,
    }


def context_from(payload: dict[str, object]):
    return ranking.ResearchContext(
        manifest=payload["run_manifest"],
        queries=payload["queries"],
        sources=payload["sources"],
        evidence_cards=payload["evidence_cards"],
        platform_coverage=payload["platform_coverage"],
    )


def write_frozen_rank_inputs(root: Path, payload: dict[str, object]) -> dict[str, Path]:
    paths = {
        "candidates": root / "candidates.json",
        "run_manifest": root / "run_manifest.json",
        "queries": root / "queries.tsv",
        "sources": root / "sources.tsv",
        "evidence_cards": root / "evidence_cards.tsv",
        "platform_coverage": root / "platform_coverage.tsv",
    }
    paths["candidates"].write_text(
        json.dumps({"topic": payload["topic"], "candidates": payload["candidates"]}),
        encoding="utf-8",
    )
    paths["run_manifest"].write_text(json.dumps(payload["run_manifest"]), encoding="utf-8")

    def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    write_tsv(paths["queries"], payload["queries"])
    write_tsv(paths["sources"], payload["sources"])
    write_tsv(paths["evidence_cards"], payload["evidence_cards"])
    write_tsv(paths["platform_coverage"], payload["platform_coverage"])
    manifest = lineage.build_rank_input_manifest(root, "run-test")
    lineage_path = root / "rank-input-manifest.json"
    lineage_path.write_text(json.dumps(manifest), encoding="utf-8")
    process = {
        "contract_version": "top50-process-result/v1",
        "run_id": "run-test",
        "stage": "process",
        "status": "complete",
        "producer": {"engine_id": "python-control-plane", "engine_version": "0.1.0"},
        "input_bindings": [],
        "processed_candidates": [
            {"candidate_id": row["id"], "requires_fetch_time_dns_validation": False}
            for row in payload["candidates"]
        ],
        "exact_clusters": [],
        "near_duplicate_reviews": [],
        "counts": {
            "input_candidates": len(payload["candidates"]),
            "processed_candidates": len(payload["candidates"]),
            "exact_clusters": 0,
            "exact_duplicate_candidates": 0,
            "near_duplicate_reviews": 0,
            "dns_validation_required": 0,
        },
    }
    process["result_digest_sha256"] = lineage.canonical_json_sha256(process)
    process_path = root / "process-result.json"
    process_path.write_text(json.dumps(process), encoding="utf-8")

    def stage_binding(relation: str, path: Path, artifact: dict[str, object], record_ids: list[str], record_kind: str) -> dict[str, object]:
        return {
            "relation": relation,
            "path": str(path),
            "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
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
        "run_id": "run-test",
        "stage": "curate",
        "status": "accepted",
        "producer": {"engine_id": "python-control-plane", "engine_version": "0.1.0"},
        "input_bindings": [
            stage_binding("process_result", process_path, process, [row["id"] for row in payload["candidates"]], "candidate"),
            stage_binding("rank_input_manifest", lineage_path, manifest, [row["input_id"] for row in manifest["files"]], "file"),
        ],
        "curator": {"id": "curator-1"},
        "worker_ids": ["worker-1"],
        "decisions": [
            {
                "candidate_id": row["id"],
                "decision": "accepted",
                "evidence_ids": row["evidence_ids"],
                "reason_codes": [],
            }
            for row in payload["candidates"]
        ],
        "accepted_candidate_ids": [row["id"] for row in payload["candidates"]],
        "evidence_ledger_binding": {
            "artifact_sha256": next(row["artifact_sha256"] for row in manifest["files"] if row["input_id"] == "evidence_cards")
        },
        "source_ledger_binding": {
            "artifact_sha256": next(row["artifact_sha256"] for row in manifest["files"] if row["input_id"] == "sources")
        },
        "counts": {
            "input_candidates": len(payload["candidates"]),
            "accepted": len(payload["candidates"]),
            "rejected": 0,
            "blocked": 0,
        },
    }
    curator["result_digest_sha256"] = lineage.canonical_json_sha256(curator)
    curator_path = root / "curate-result.json"
    curator_path.write_text(json.dumps(curator), encoding="utf-8")
    return {**paths, "lineage": lineage_path, "curator": curator_path}


def frozen_rank_cli_command(
    paths: dict[str, Path], output: Path, *, top: int = 1
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--input",
        str(paths["candidates"]),
        "--manifest",
        str(paths["run_manifest"]),
        "--queries",
        str(paths["queries"]),
        "--sources",
        str(paths["sources"]),
        "--evidence-cards",
        str(paths["evidence_cards"]),
        "--platform-coverage",
        str(paths["platform_coverage"]),
        "--lineage-manifest",
        str(paths["lineage"]),
        "--curator-acceptance",
        str(paths["curator"]),
        "--output-dir",
        str(output),
        "--top",
        str(top),
    ]


class RankingGateTests(unittest.TestCase):
    def test_candidate_self_report_cannot_replace_run_and_evidence_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "research context"):
            ranking.rank_candidates([candidate("one")], top_n=1)

    def test_top_n_contract_accepts_100_and_rejects_out_of_range_or_boolean(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        result = ranking.rank_candidates(
            rows, top_n=100, context=context_from(payload), topic="test topic"
        )
        self.assertEqual(result.summary["requested_top_n"], 100)
        for invalid in (0, 101, True):
            with self.subTest(top_n=invalid), self.assertRaisesRegex(
                ValueError, "1 to 100"
            ):
                ranking.rank_candidates(
                    rows,
                    top_n=invalid,
                    context=context_from(payload),
                    topic="test topic",
                )

    def test_complete_independently_curated_context_passes(self) -> None:
        rows = [candidate("one"), candidate("two")]
        payload = bundle(rows)

        result = ranking.rank_candidates(
            rows, top_n=2, context=context_from(payload), topic="test topic"
        )

        self.assertEqual([row["id"] for row in result.selected], ["one", "two"])
        self.assertTrue(result.summary["top_n_filled"])
        self.assertTrue(result.summary["count_conservation_passed"])
        self.assertEqual(result.summary["input_count"], 2)
        self.assertEqual(result.summary["selected_count"] + result.summary["rejected_count"], 2)

    def test_contract_field_aliases_are_normalized_bidirectionally(self) -> None:
        row = candidate("one")
        payload = bundle([row])
        row["platform_id"] = row.pop("platform")
        row["creator_name"] = row.pop("author")
        row["summary"] = row.pop("excerpt")

        result = ranking.rank_candidates(
            [row], top_n=1, context=context_from(payload), topic="test topic"
        )

        selected = result.selected[0]
        self.assertEqual(selected["platform"], selected["platform_id"])
        self.assertEqual(selected["author"], selected["creator_name"])
        self.assertEqual(selected["excerpt"], selected["summary"])

    def test_curator_must_be_independent_from_worker(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["run_manifest"]["curator"] = {"id": "worker-1"}

        with self.assertRaisesRegex(ValueError, "curator.*independent"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_manifest_artifact_count_mismatch_fails_closed(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["run_manifest"]["counts"]["sources"] = 99

        with self.assertRaisesRegex(ValueError, "source.*count"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_platform_ledgers_cannot_be_relabeled_to_fake_required_coverage(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        for row in payload["queries"]:
            row["platform"] = "youtube"
        for row in payload["platform_coverage"]:
            row["platform"] = "youtube"
        for row in payload["run_manifest"]["coverage"]:
            row["platform"] = "youtube"
        payload["run_manifest"]["scope"]["required_platforms"] = ["youtube"]

        with self.assertRaisesRegex(ValueError, "candidate platform counts"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_source_and_query_platforms_must_exist_in_coverage(self) -> None:
        mutations = (
            (
                lambda payload: payload["sources"][0].__setitem__("platform", "youtube"),
                "source platform lacks coverage",
            ),
            (
                lambda payload: payload["queries"][0].__setitem__("platform", "youtube"),
                "query platform lacks coverage",
            ),
        )
        for mutate, message in mutations:
            rows = [candidate("one")]
            payload = bundle(rows)
            mutate(payload)

            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                ranking.rank_candidates(
                    rows, top_n=1, context=context_from(payload), topic="test topic"
                )

    def test_fetched_platform_count_requires_enough_successful_source_rows(self) -> None:
        rows = [candidate("one"), candidate("two")]
        payload = bundle(rows)
        payload["sources"] = payload["sources"][:1]
        payload["evidence_cards"] = payload["evidence_cards"][:1]
        payload["run_manifest"]["counts"]["sources"] = 1
        payload["run_manifest"]["counts"]["evidence_cards"] = 1

        with self.assertRaisesRegex(ValueError, "source counts.*fetched"):
            ranking.rank_candidates(
                rows, top_n=2, context=context_from(payload), topic="test topic"
            )

    def test_candidate_direct_source_cannot_claim_another_platform(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["sources"][0]["platform"] = "youtube"
        youtube_coverage = {
            "platform": "youtube",
            "coverage_status": "complete",
            "discovered_count": 0,
            "fetched_count": 0,
            "eligible_count": 0,
            "blocked_count": 0,
            "rejected_count": 0,
        }
        payload["platform_coverage"].append(youtube_coverage)
        payload["run_manifest"]["counts"]["platforms"] = 2
        payload["queries"].extend(
            [
                {
                    "platform": "youtube",
                    "query": "topic exact",
                    "backend": "public_search",
                    "executed_at": "2026-08-23T08:10:00+08:00",
                    "status": "complete",
                    "candidate_count": 0,
                },
                {
                    "platform": "youtube",
                    "query": "topic practical guide",
                    "backend": "public_search",
                    "executed_at": "2026-08-23T08:15:00+08:00",
                    "status": "complete",
                    "candidate_count": 0,
                },
            ]
        )
        payload["run_manifest"]["counts"]["queries"] = 4

        with self.assertRaisesRegex(ValueError, "direct source platform"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_per_platform_candidate_counts_must_match_coverage(self) -> None:
        first = candidate("github-one")
        second = candidate("youtube-one")
        second["platform"] = "youtube"
        payload = bundle([first, second])
        coverage = {
            row["platform"]: row for row in payload["platform_coverage"]
        }
        manifest_coverage = {
            row["platform"]: row for row in payload["run_manifest"]["coverage"]
        }
        for ledger in (coverage, manifest_coverage):
            for key in ("discovered_count", "fetched_count", "eligible_count"):
                ledger["github"][key] = 0
                ledger["youtube"][key] = 2

        with self.assertRaisesRegex(ValueError, "candidate platform counts"):
            ranking.rank_candidates(
                [first, second],
                top_n=2,
                context=context_from(payload),
                topic="test topic",
            )

    def test_query_candidate_counts_must_cover_platform_discoveries(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        for query in payload["queries"]:
            query["candidate_count"] = 0

        with self.assertRaisesRegex(ValueError, "query candidate counts"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_platform_aliases_cannot_disagree_inside_one_ledger_row(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["sources"][0]["platform_id"] = "youtube"

        with self.assertRaisesRegex(ValueError, "conflicting platform aliases"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_candidate_requires_linked_accepted_evidence_card(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["evidence_cards"][0]["reviewer_status"] = "pending"

        result = ranking.rank_candidates(
            rows, top_n=1, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(result.selected, [])
        self.assertIn("evidence_card_not_accepted:ev-one", result.rejected[0]["rejection_reasons"])

    def test_primary_only_policy_rejects_secondary_or_medium_evidence(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["run_manifest"]["scope"]["source_policy"] = "primary_only"
        payload["sources"][0]["source_type"] = "secondary"
        payload["evidence_cards"][0]["evidence_grade"] = "medium"
        rows[0]["evidence_grade"] = "medium"

        result = ranking.rank_candidates(
            rows, top_n=1, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(result.selected, [])
        reasons = result.rejected[0]["rejection_reasons"]
        self.assertIn("evidence_source_not_primary:ev-one", reasons)
        self.assertEqual(result.summary["actual_count"], 0)

        payload["sources"][0]["source_type"] = "official"
        payload["evidence_cards"][0]["evidence_grade"] = "strong"
        rows[0]["evidence_grade"] = "strong"
        accepted = ranking.rank_candidates(
            rows, top_n=1, context=context_from(payload), topic="test topic"
        )
        self.assertEqual([row["id"] for row in accepted.selected], ["one"])


class UrlAndDedupeTests(unittest.TestCase):
    def test_canonical_url_matches_shared_cross_language_fixture(self) -> None:
        fixture_path = (
            Path(__file__).parents[1]
            / "engines"
            / "rust-processor"
            / "tests"
            / "fixtures"
            / "canonical-url-v1.json"
        )
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

        self.assertEqual(fixture["contract_version"], "top50-canonical-url-fixture/v1")
        for case in fixture["accepted"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(ranking.canonical_url(case["input"]), case["canonical_url"])

    def test_http_and_https_are_one_canonical_public_url(self) -> None:
        self.assertEqual(
            ranking.canonical_url("http://www.example.com/a/?utm_source=x#part"),
            "https://example.com/a",
        )
        self.assertEqual(
            ranking.canonical_url("https://example.com/a"),
            "https://example.com/a",
        )

    def test_local_private_and_credential_urls_are_rejected(self) -> None:
        for unsafe in (
            "http://127.0.0.1/admin",
            "http://10.0.0.2/data",
            "https://user:password@example.com/post",
            "file:///etc/passwd",
        ):
            with self.subTest(url=unsafe):
                self.assertFalse(ranking.is_safe_public_url(unsafe))

    def test_nonstandard_ipv4_and_private_dns_answers_are_rejected(self) -> None:
        for unsafe in (
            "http://2130706433/admin",
            "http://0x7f000001/admin",
            "http://127.1/admin",
        ):
            with self.subTest(url=unsafe):
                self.assertFalse(ranking.is_safe_public_url(unsafe))

        private_answer = [
            (
                ranking.socket.AF_INET,
                ranking.socket.SOCK_STREAM,
                ranking.socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 443),
            )
        ]
        with patch.object(ranking.socket, "getaddrinfo", return_value=private_answer):
            self.assertFalse(
                ranking.is_safe_public_url(
                    "https://public-looking-but-private.invalid/source"
                )
            )

    def test_dns_is_rechecked_instead_of_reusing_a_stale_public_answer(self) -> None:
        public_answer = [
            (
                ranking.socket.AF_INET,
                ranking.socket.SOCK_STREAM,
                ranking.socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", 443),
            )
        ]
        private_answer = [
            (
                ranking.socket.AF_INET,
                ranking.socket.SOCK_STREAM,
                ranking.socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 443),
            )
        ]
        with patch.object(
            ranking.socket,
            "getaddrinfo",
            side_effect=[public_answer, private_answer],
        ) as resolver:
            self.assertTrue(ranking.is_safe_public_url("https://rebind.invalid/one"))
            self.assertFalse(ranking.is_safe_public_url("https://rebind.invalid/two"))
            self.assertEqual(resolver.call_count, 2)

    def test_exact_url_duplicate_is_removed_with_count_conservation(self) -> None:
        first = candidate("one", url="http://www.example.com/item/?utm_campaign=test")
        second = candidate("two", url="https://example.com/item")
        second["title"] = "A distinct mirror title"
        payload = bundle([first, second])

        result = ranking.rank_candidates(
            [first, second], top_n=2, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(len(result.selected), 1)
        self.assertEqual(result.summary["exact_duplicate_count"], 1)
        self.assertEqual(result.summary["input_count"], len(result.selected) + len(result.rejected))
        duplicate = next(row for row in result.rejected if row["id"] != result.selected[0]["id"])
        self.assertIn("duplicate_canonical_url", duplicate["rejection_reasons"])

    def test_near_duplicate_content_is_flagged_not_auto_removed(self) -> None:
        first = candidate("one")
        second = candidate("two")
        first["title"] = "A practical guide to auditable cross platform research"
        second["title"] = "A practical guide to auditable cross-platform research"
        first["excerpt"] = "This detailed workflow collects public sources, verifies evidence cards, and preserves every research decision for later audit."
        second["excerpt"] = "This detailed workflow collects public sources, verifies evidence cards, and preserves each research decision for later audit."
        payload = bundle([first, second])

        result = ranking.rank_candidates(
            [first, second], top_n=2, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(len(result.selected), 2)
        self.assertEqual(len(result.near_duplicate_reviews), 1)
        self.assertTrue(all(row["dedupe_review_required"] for row in result.selected))

    def test_matching_title_and_excerpt_from_distinct_authors_are_not_exact_duplicates(self) -> None:
        first = candidate("one", url="https://example.com/one")
        second = candidate("two", url="https://example.org/two")
        second["title"] = first["title"]
        second["excerpt"] = first["excerpt"]
        second["author"] = "Independent Author"
        second["published_at"] = "2026-08-01"
        payload = bundle([first, second])

        result = ranking.rank_candidates(
            [first, second], top_n=2, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(len(result.selected), 2)
        self.assertEqual(result.summary["exact_duplicate_count"], 0)


class EngagementAndCliTests(unittest.TestCase):
    def test_missing_engagement_never_receives_relative_or_absolute_points(self) -> None:
        rows = [candidate("one"), candidate("two"), candidate("three")]
        payload = bundle(rows)

        result = ranking.rank_candidates(
            rows, top_n=3, context=context_from(payload), topic="test topic"
        )

        for row in result.selected:
            self.assertEqual(row["score_components"]["engagement"], 0.0)
            self.assertEqual(row["engagement_normalization"]["method"], "unobserved")
            self.assertIsNone(row["engagement_normalization"]["normalized_signal"])

    def test_shortfall_is_reported_without_padding(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)

        result = ranking.rank_candidates(
            rows, top_n=3, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(result.summary["selected_count"], 1)
        self.assertEqual(result.summary["shortfall"], 2)
        self.assertFalse(result.summary["top_n_filled"])
        self.assertNotIn("Top 3", result.summary["completion_label"])

    def test_cli_validates_bundle_and_writes_complete_atomic_ranking_package(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output_path = root / "out"

            completed = subprocess.run(
                frozen_rank_cli_command(paths, output_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            expected = {
                "ranking.json",
                "top.json",
                "rejected.json",
                "run_summary.json",
                "report.md",
                "package_validation.json",
                "run_manifest.json",
                "candidates.json",
                "queries.tsv",
                "sources.tsv",
                "evidence_cards.tsv",
                "platform_coverage.tsv",
                "source_gap_backlog.md",
            }
            self.assertTrue(expected.issubset({path.name for path in output_path.iterdir()}))
            validation = json.loads((output_path / "package_validation.json").read_text())
            self.assertEqual(validation["status"], "pass")
            self.assertTrue(validation["count_conservation_passed"])

    def test_cli_requires_both_lineage_artifacts_before_creating_output(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            base_command = [
                sys.executable,
                str(SCRIPT),
                "--input",
                str(paths["candidates"]),
                "--manifest",
                str(paths["run_manifest"]),
                "--queries",
                str(paths["queries"]),
                "--sources",
                str(paths["sources"]),
                "--evidence-cards",
                str(paths["evidence_cards"]),
                "--platform-coverage",
                str(paths["platform_coverage"]),
                "--top",
                "1",
            ]
            missing_cases = {
                "both": [],
                "lineage_manifest": [
                    "--curator-acceptance",
                    str(paths["curator"]),
                ],
                "curator_acceptance": [
                    "--lineage-manifest",
                    str(paths["lineage"]),
                ],
            }

            for label, lineage_args in missing_cases.items():
                output = root / f"ranking-output-{label}"
                completed = subprocess.run(
                    [
                        *base_command,
                        *lineage_args,
                        "--output-dir",
                        str(output),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                with self.subTest(missing=label):
                    self.assertEqual(completed.returncode, 2, completed.stderr)
                    self.assertIn("lineage-manifest", completed.stderr)
                    self.assertIn("curator-acceptance", completed.stderr)
                    self.assertFalse(output.exists())

    def test_cli_failure_does_not_leave_a_partial_output_directory(self) -> None:
        payload = bundle([candidate("one")])
        payload["run_manifest"]["counts"]["queries"] = 999
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output_path = root / "out"

            completed = subprocess.run(
                frozen_rank_cli_command(paths, output_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("query", completed.stderr.lower())
            self.assertFalse(output_path.exists())

    def test_cli_refuses_to_replace_an_existing_empty_output_directory(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output_path = root / "out"
            output_path.mkdir()

            completed = subprocess.run(
                frozen_rank_cli_command(paths, output_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("must not already exist", completed.stderr)
            self.assertEqual(list(output_path.iterdir()), [])


class ExtendedBehaviorTests(unittest.TestCase):
    def test_placeholder_topic_is_rejected(self) -> None:
        for value in (
            "《》", "《主题》", "【主题】", "{{TOPIC}}", "{{ TOPIC }}",
            "{{PURPOSE}}", "<TOPIC>", "请填写主题", "待填写", "TBD", "---",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "topic"):
                ranking.normalized_topic(value)
        self.assertEqual(ranking.normalized_topic("topic modeling"), "topic modeling")

    def test_direct_api_rejects_candidate_without_a_stable_id(self) -> None:
        row = candidate("missing-id")
        payload = bundle([row])
        row.pop("id")

        with self.assertRaisesRegex(ValueError, "stable ID"):
            ranking.rank_candidates(
                [row], top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_cli_rejects_candidate_id_removal_after_lineage_freeze(self) -> None:
        payload = bundle([candidate("missing-id")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output_path = root / "out"
            rewritten = json.loads(paths["candidates"].read_text(encoding="utf-8"))
            rewritten["candidates"][0].pop("id")
            paths["candidates"].write_text(json.dumps(rewritten), encoding="utf-8")

            completed = subprocess.run(
                frozen_rank_cli_command(paths, output_path),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("lineage", completed.stderr)
            self.assertFalse(output_path.exists())

    def test_observed_engagement_is_scored_and_normalized(self) -> None:
        rows = [candidate(f"item-{index}") for index in range(3)]
        for index, row in enumerate(rows, 1):
            row["engagement"] = {"likes": index * 10, "comments": index}
        payload = bundle(rows)

        result = ranking.rank_candidates(
            rows, top_n=3, context=context_from(payload), topic="test topic"
        )

        points = [row["score_components"]["engagement"] for row in result.selected]
        self.assertGreater(max(points), min(points))
        self.assertTrue(
            all(
                row["engagement_normalization"]["method"]
                == "platform_minmax_log_signal"
                for row in result.selected
            )
        )

    def test_exact_crosspost_content_is_deduplicated_across_urls(self) -> None:
        first = candidate("first", url="https://example.com/original")
        second = candidate("second", url="https://example.org/crosspost")
        second["title"] = first["title"]
        second["excerpt"] = first["excerpt"]
        second["author"] = first["author"]
        second["published_at"] = first["published_at"]
        payload = bundle([first, second])

        result = ranking.rank_candidates(
            [first, second], top_n=2, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(len(result.selected), 1)
        self.assertIn("content_fingerprint", result.dedup_clusters[0]["dedup_reason"])
        self.assertTrue(any("duplicate_content_fingerprint" in row["rejection_reasons"] for row in result.rejected))

    def test_publication_rejects_missing_fields_bad_scores_dates_and_evidence(self) -> None:
        row = candidate("broken")
        payload = bundle([row])
        row.update({
            "title": "", "accessed_at": "not-a-date", "published_at": 123,
            "reviewer_status": "pending", "evidence_grade": "weak",
            "relevance": 101, "source_quality": True, "freshness": None,
            "engagement": {"likes": -1}, "evidence_ids": ["missing-card"],
        })

        result = ranking.rank_candidates(
            [row], top_n=1, context=context_from(payload), topic="test topic"
        )

        reasons = result.rejected[0]["rejection_reasons"]
        for expected in (
            "missing_title", "reviewer_not_accepted", "evidence_grade_not_publishable",
            "invalid_relevance", "invalid_source_quality", "invalid_freshness",
            "invalid_accessed_at", "invalid_published_at", "invalid_engagement_likes",
            "evidence_card_missing:missing-card",
        ):
            self.assertIn(expected, reasons)

    def test_context_rejects_incomplete_phase_pending_coverage_and_nonindependent_card(self) -> None:
        mutations = (
            (lambda payload: payload["run_manifest"]["phases"].__setitem__("fetch", "pending"), "phase"),
            (lambda payload: payload["platform_coverage"][0].__setitem__("coverage_status", "pending"), "coverage"),
            (lambda payload: payload["evidence_cards"][0].__setitem__("reviewer_id", "worker-1"), "reviewer"),
            (lambda payload: payload["sources"][0].__setitem__("url", "http://127.0.0.1/a"), "safe public URL"),
        )
        for mutate, message in mutations:
            rows = [candidate("one")]
            payload = bundle(rows)
            mutate(payload)
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                ranking.rank_candidates(rows, top_n=1, context=context_from(payload), topic="test topic")

    def test_twenty_plus_claim_fails_without_real_coverage(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["run_manifest"]["scope"]["claim_20_plus_platforms"] = True

        with self.assertRaisesRegex(ValueError, "20\+"):
            ranking.rank_candidates(rows, top_n=1, context=context_from(payload), topic="test topic")

    def test_safe_markdown_serialization_blocks_structure_injection(self) -> None:
        value = "# heading\n<img token='secret'> [x](javascript:alert(1)) | cell"
        rendered = ranking.markdown_text(value, single_line=True)

        self.assertNotIn("\n", rendered)
        self.assertNotRegex(rendered, r"(?<!\\)<img")
        self.assertIn("\\#", rendered)
        self.assertIn("\\<img", rendered)
        self.assertIn("\\|", rendered)

    def test_report_escapes_topic_rejected_id_and_markdown_url_boundaries(self) -> None:
        good = candidate("good", url="https://example.com/a_(b)")
        bad = candidate("bad`\n# injected", url="https://example.com/rejected")
        bad["title"] = ""
        payload = bundle([good, bad])
        payload["topic"] = "# topic\n1. injected"
        payload["run_manifest"]["topic"] = payload["topic"]
        payload["run_manifest"]["scope"]["topic"] = payload["topic"]
        result = ranking.rank_candidates(
            [good, bad], top_n=1, context=context_from(payload), topic=payload["topic"]
        )

        report = ranking.report_markdown(payload["topic"], result)

        self.assertTrue(report.startswith("# \\# topic 1. injected"))
        self.assertIn("https://example.com/a_%28b%29", report)
        self.assertNotIn("`bad`\n# injected`", report)
        self.assertIn("bad\\` \\# injected", report)

    def test_public_url_rejects_whitespace_and_invalid_ports(self) -> None:
        for unsafe in (
            "https://exa mple.com/post",
            "https://example.com/a b",
            "https://example.com:invalid/post",
        ):
            with self.subTest(url=unsafe):
                self.assertFalse(ranking.is_safe_public_url(unsafe))

    def test_explicit_unknown_author_and_publication_date_are_publishable(self) -> None:
        row = candidate("unknown-metadata")
        row["author"] = "未知"
        row["published_at"] = "N/A"
        payload = bundle([row])

        result = ranking.rank_candidates(
            [row], top_n=1, context=context_from(payload), topic="test topic"
        )

        self.assertEqual(result.selected[0]["author"], "unknown")
        self.assertEqual(result.selected[0]["published_at"], "unknown")
        report = ranking.report_markdown("test topic", result)
        self.assertIn("作者：unknown", report)
        self.assertIn("发布：unknown", report)

    def test_missing_author_content_type_or_publication_marker_is_rejected(self) -> None:
        mutations = (
            (lambda row: row.pop("author"), "missing_author"),
            (lambda row: row.__setitem__("content_type", ""), "missing_content_type"),
            (lambda row: row.pop("published_at"), "missing_published_at"),
        )
        for mutate, reason in mutations:
            row = candidate(reason)
            payload = bundle([row])
            mutate(row)

            result = ranking.rank_candidates(
                [row], top_n=1, context=context_from(payload), topic="test topic"
            )

            with self.subTest(reason=reason):
                self.assertEqual(result.selected, [])
                self.assertIn(reason, result.rejected[0]["rejection_reasons"])

    def test_evidence_card_requires_nonempty_claim_and_valid_support_type(self) -> None:
        mutations = (
            (lambda card: card.__setitem__("claim", ""), "claim"),
            (lambda card: card.pop("supports"), "supports"),
            (lambda card: card.__setitem__("supports", "opinion"), "supports"),
        )
        for mutate, field in mutations:
            rows = [candidate(f"bad-{field}")]
            payload = bundle(rows)
            mutate(payload["evidence_cards"][0])

            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                ranking.rank_candidates(
                    rows, top_n=1, context=context_from(payload), topic="test topic"
                )

    def test_cli_accepts_separate_frozen_tsv_context_files(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output = root / "out"
            completed = subprocess.run(
                frozen_rank_cli_command(paths, output),
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "package_validation.json").exists())

    def test_direct_unbound_bundle_loader_is_rejected(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "bundle.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            args = SimpleNamespace(
                input=input_path,
                manifest=None,
                queries=None,
                sources=None,
                evidence_cards=None,
                platform_coverage=None,
            )

            with self.assertRaisesRegex(ValueError, "lineage-manifest"):
                ranking.load_bundle(args)

    def test_gap_backlog_reports_shortfall_coverage_and_rejection_counts(self) -> None:
        good = candidate("good")
        bad = candidate("bad")
        bad["title"] = ""
        payload = bundle([good, bad])
        payload["platform_coverage"][0]["coverage_status"] = "partial"
        payload["run_manifest"]["coverage"][0]["coverage_status"] = "partial"
        payload["platform_coverage"][0]["next_verification_step"] = "review one more result page"
        payload["run_manifest"]["coverage"][0]["next_verification_step"] = "review one more result page"
        result = ranking.rank_candidates(
            [good, bad], top_n=3, context=context_from(payload), topic="test topic"
        )

        gaps = ranking.gap_backlog_markdown(context_from(payload), result)

        self.assertIn("短缺：2 条", gaps)
        self.assertIn("github：partial", gaps)
        self.assertIn("review one more result page", gaps)
        self.assertIn("missing\_title：1", gaps)

    def test_evidence_url_must_match_candidate_and_access_date_must_parse(self) -> None:
        rows = [candidate("one")]
        payload = bundle(rows)
        payload["evidence_cards"][0]["source_url"] = "https://example.com/other"

        with self.assertRaisesRegex(ValueError, "source URL mismatch"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

        payload = bundle(rows)
        payload["evidence_cards"][0]["access_date"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "access_date"):
            ranking.rank_candidates(
                rows, top_n=1, context=context_from(payload), topic="test topic"
            )

    def test_cli_frozen_lineage_succeeds_before_writing_package(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            output = root / "ranking-output"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(paths["candidates"]),
                    "--manifest",
                    str(paths["run_manifest"]),
                    "--queries",
                    str(paths["queries"]),
                    "--sources",
                    str(paths["sources"]),
                    "--evidence-cards",
                    str(paths["evidence_cards"]),
                    "--platform-coverage",
                    str(paths["platform_coverage"]),
                    "--lineage-manifest",
                    str(paths["lineage"]),
                    "--curator-acceptance",
                    str(paths["curator"]),
                    "--output-dir",
                    str(output),
                    "--top",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "package_validation.json").is_file())

    def test_cli_rejects_curator_a_rank_b_without_creating_output(self) -> None:
        payload = bundle([candidate("accepted-a")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            replacement = candidate("replacement-b")
            paths["candidates"].write_text(
                json.dumps({"topic": "test topic", "candidates": [replacement]}),
                encoding="utf-8",
            )
            output = root / "ranking-output"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(paths["candidates"]),
                    "--manifest",
                    str(paths["run_manifest"]),
                    "--queries",
                    str(paths["queries"]),
                    "--sources",
                    str(paths["sources"]),
                    "--evidence-cards",
                    str(paths["evidence_cards"]),
                    "--platform-coverage",
                    str(paths["platform_coverage"]),
                    "--lineage-manifest",
                    str(paths["lineage"]),
                    "--curator-acceptance",
                    str(paths["curator"]),
                    "--output-dir",
                    str(output),
                    "--top",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("lineage", completed.stderr)
            self.assertFalse(output.exists())

    def test_cli_rejects_curator_set_drift_without_creating_output(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = write_frozen_rank_inputs(root, payload)
            curator_payload = json.loads(paths["curator"].read_text(encoding="utf-8"))
            curator_payload["accepted_candidate_ids"] = []
            curator_payload["result_digest_sha256"] = lineage.canonical_json_sha256(
                {
                    key: value
                    for key, value in curator_payload.items()
                    if key != "result_digest_sha256"
                }
            )
            paths["curator"].write_text(json.dumps(curator_payload), encoding="utf-8")
            output = root / "ranking-output"
            args = SimpleNamespace(
                input=paths["candidates"],
                manifest=paths["run_manifest"],
                queries=paths["queries"],
                sources=paths["sources"],
                evidence_cards=paths["evidence_cards"],
                platform_coverage=paths["platform_coverage"],
                lineage_manifest=paths["lineage"],
                curator_acceptance=paths["curator"],
            )

            with self.assertRaisesRegex(ValueError, "accepted candidate IDs"):
                ranking.load_bundle(args)
            self.assertFalse(output.exists())

if __name__ == "__main__":
    unittest.main()
