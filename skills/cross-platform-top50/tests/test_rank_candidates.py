from __future__ import annotations

import importlib.util
import csv
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
            input_path = root / "candidates.json"
            output_path = root / "out"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_path),
                    "--top",
                    "1",
                ],
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

    def test_cli_failure_does_not_leave_a_partial_output_directory(self) -> None:
        payload = bundle([candidate("one")])
        payload["run_manifest"]["counts"]["queries"] = 999
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "candidates.json"
            output_path = root / "out"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_path),
                    "--top",
                    "1",
                ],
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
            input_path = root / "candidates.json"
            output_path = root / "out"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            output_path.mkdir()

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_path),
                    "--top",
                    "1",
                ],
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

    def test_cli_rejects_candidate_without_a_stable_id(self) -> None:
        row = candidate("missing-id")
        payload = bundle([row])
        row.pop("id")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "candidates.json"
            output_path = root / "out"
            input_path.write_text(json.dumps(payload), encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_path),
                    "--top",
                    "1",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("stable ID", completed.stderr)
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

    def test_cli_accepts_separate_tsv_context_files(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_path = root / "candidates.json"
            manifest_path = root / "run_manifest.json"
            candidate_path.write_text(json.dumps({"topic": payload["topic"], "candidates": payload["candidates"]}), encoding="utf-8")
            manifest_path.write_text(json.dumps(payload["run_manifest"]), encoding="utf-8")

            def write_tsv(name: str, rows: list[dict[str, object]]) -> Path:
                path = root / name
                fields = list(dict.fromkeys(key for row in rows for key in row))
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
                    writer.writeheader()
                    writer.writerows(rows)
                return path

            queries = write_tsv("queries.tsv", payload["queries"])
            sources = write_tsv("sources.tsv", payload["sources"])
            evidence = write_tsv("evidence_cards.tsv", payload["evidence_cards"])
            coverage = write_tsv("platform_coverage.tsv", payload["platform_coverage"])
            output = root / "out"
            completed = subprocess.run([
                sys.executable, str(SCRIPT), "--input", str(candidate_path),
                "--manifest", str(manifest_path), "--queries", str(queries),
                "--sources", str(sources), "--evidence-cards", str(evidence),
                "--platform-coverage", str(coverage), "--output-dir", str(output),
                "--top", "1",
            ], capture_output=True, text=True, check=False)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output / "package_validation.json").exists())

    def test_direct_bundle_roundtrip_exposes_contract_fields_and_validates_files(self) -> None:
        payload = bundle([candidate("one")])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "bundle.json"
            output_path = root / "out"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            args = SimpleNamespace(
                input=input_path,
                manifest=None,
                queries=None,
                sources=None,
                evidence_cards=None,
                platform_coverage=None,
            )

            topic, rows, context = ranking.load_bundle(args)
            result = ranking.rank_candidates(
                rows, top_n=1, context=context, topic=topic
            )
            ranking.write_package(output_path, topic, rows, context, result)

            self.assertEqual(
                {path.name for path in output_path.iterdir()}, ranking.PACKAGE_FILES
            )
            output = json.loads((output_path / "ranking.json").read_text())
            gaps = (output_path / "source_gap_backlog.md").read_text()
            selected = output["ranked_candidates"][0]
            self.assertEqual(output["ranking_version"], "deterministic-v2")
            self.assertEqual(output["score_model"]["name"], "deterministic-v2")
            self.assertEqual(output["requested_top_n"], 1)
            self.assertEqual(output["actual_count"], 1)
            self.assertEqual(selected["platform_id"], "github")
            self.assertEqual(selected["creator_name"], "Example Author")
            self.assertEqual(
                selected["total_score"],
                sum(selected[f"{name}_score"] for name in ranking.SCORE_WEIGHTS),
            )
            self.assertIn("短缺：0 条", gaps)
            self.assertIn("未入选原因摘要", gaps)

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


if __name__ == "__main__":
    unittest.main()
