from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema


SKILL_ROOT = Path(__file__).parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "source_contract.py"
OUTCOME_SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "source-outcome.schema.json"
CHECKPOINT_SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "checkpoint.schema.json"
QUERY_PLAN_SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "research-query-plan.schema.json"
SPEC = importlib.util.spec_from_file_location("source_contract", SCRIPT)
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contract
SPEC.loader.exec_module(contract)


NOW = datetime(2026, 8, 24, 8, 30, tzinfo=timezone.utc)


def raw_outcome(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "top50-source-observation/v1",
        "run_id": "run-source-001",
        "query_id": "q-001",
        "route_id": "route-xhs-browser",
        "platform_id": "xiaohongshu",
        "adapter_id": "xhs-browser-v1",
        "access_kind": "browser_session",
        "acquisition_method": "platform_native",
        "evidence_tier": "full_content",
        "url": "https://www.xiaohongshu.com/explore/example",
        "observed_at": "2026-08-24T08:00:00Z",
        "http_status": 200,
        "result_state": "success",
        "attempt": 1,
        "max_attempts": 3,
        "breaker_failure_count": 0,
        "breaker_threshold": 3,
        "breaker_cooldown_seconds": 300,
        "timeframe": {"start": "2026-07-25", "end": "2026-08-24"},
        "window_timezone": "Asia/Shanghai",
        "published_at": "2026-08-20T12:00:00Z",
        "published_at_confidence": "observed",
        "date_basis": "platform_timestamp",
        "content_sha256": "a" * 64,
        "response_endpoint": "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
        "payload_shape": "content_cards",
        "content_card_count": 12,
        "backend_id": "browser-bridge",
        "probe_id": "probe-001",
        "authorization": "granted_for_current_task",
        "error_code": None,
        "error_summary": None,
        "retry_after_seconds": None,
    }
    value.update(overrides)
    if overrides.get("result_state", "success") != "success":
        if "payload_shape" not in overrides:
            value["payload_shape"] = "unknown"
        if "content_card_count" not in overrides:
            value["content_card_count"] = 0
    return value


class OutcomeContractTests(unittest.TestCase):
    def test_runtime_and_all_source_platform_schemas_share_canonical_28(self) -> None:
        expected = set(contract.CANONICAL_PLATFORMS)
        self.assertEqual(len(expected), 28)
        for schema_path in (OUTCOME_SCHEMA, CHECKPOINT_SCHEMA, QUERY_PLAN_SCHEMA):
            with self.subTest(schema=schema_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertEqual(set(schema["$defs"]["platform"]["enum"]), expected)

    def test_normalizes_success_with_acquisition_provenance_and_known_date(self) -> None:
        outcome = contract.normalize_source_outcome(raw_outcome(), now=NOW)

        self.assertEqual(outcome["schema"], "top50-source-outcome/v1")
        self.assertEqual(outcome["source_status"], "fetched")
        self.assertEqual(outcome["eligibility"], "eligible_for_review")
        self.assertEqual(outcome["published_at_confidence"], "observed")
        self.assertEqual(outcome["date_qualification"], "within_window")
        self.assertEqual(outcome["timeframe"], raw_outcome()["timeframe"])
        self.assertEqual(outcome["window_timezone"], "Asia/Shanghai")
        self.assertEqual(outcome["acquisition"]["method"], "platform_native")
        self.assertEqual(outcome["acquisition"]["access_kind"], "browser_session")
        self.assertEqual(outcome["acquisition"]["evidence_tier"], "full_content")
        self.assertEqual(outcome["acquisition"]["payload_shape"], "content_cards")
        self.assertEqual(outcome["acquisition"]["content_card_count"], 12)
        self.assertEqual(outcome["discovery_count"], 12)
        self.assertTrue(outcome["discoveries_allowed"])
        self.assertEqual(outcome["retry"]["decision"], "do_not_retry")
        self.assertEqual(outcome["breaker"]["action"], "record_success")
        self.assertEqual(outcome["breaker"]["threshold"], 3)
        self.assertEqual(len(outcome["outcome_digest_sha256"]), 64)

    def test_unknown_date_is_isolated_even_when_fetch_succeeds(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(
                published_at=None,
                published_at_confidence="unknown",
                date_basis="unavailable",
            ),
            now=NOW,
        )

        self.assertEqual(outcome["source_status"], "fetched")
        self.assertEqual(outcome["date_qualification"], "unknown_isolated")
        self.assertEqual(outcome["eligibility"], "isolated_unknown_date")
        self.assertFalse(outcome["may_enter_time_bounded_ranking"])

    def test_search_snippet_can_discover_but_cannot_enter_review(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(
                acquisition_method="search_index",
                evidence_tier="search_snippet",
                content_sha256=None,
            ),
            now=NOW,
        )

        self.assertEqual(outcome["source_status"], "discovered_only")
        self.assertEqual(outcome["eligibility"], "discovery_only")
        self.assertFalse(outcome["may_enter_time_bounded_ranking"])

    def test_suggestion_payload_is_rejected_as_content_discovery(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(
                payload_shape="suggestions",
                content_card_count=0,
                evidence_tier="metadata_only",
                content_sha256=None,
            ),
            now=NOW,
        )

        self.assertEqual(outcome["source_status"], "rejected_payload_shape")
        self.assertEqual(outcome["eligibility"], "not_eligible")
        self.assertEqual(outcome["discovery_count"], 0)
        self.assertFalse(outcome["discoveries_allowed"])

    def test_endpoint_change_is_accepted_when_payload_shape_is_content_cards(self) -> None:
        old = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        changed = contract.normalize_source_outcome(
            raw_outcome(
                response_endpoint="https://edith.xiaohongshu.com/api/sns/web/v9/search/items"
            ),
            now=NOW,
        )

        self.assertEqual(old["source_status"], "fetched")
        self.assertEqual(changed["source_status"], "fetched")
        self.assertEqual(changed["discovery_count"], 12)
        self.assertNotEqual(
            old["acquisition"]["response_endpoint"],
            changed["acquisition"]["response_endpoint"],
        )

    def test_known_date_outside_window_is_not_eligible(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(published_at="2026-06-01T12:00:00Z"), now=NOW
        )

        self.assertEqual(outcome["date_qualification"], "before_window")
        self.assertEqual(outcome["eligibility"], "outside_timeframe")
        self.assertFalse(outcome["may_enter_time_bounded_ranking"])

    def test_window_boundary_uses_declared_local_timezone_not_utc_date(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(published_at="2026-07-25T00:30:00+08:00"), now=NOW
        )

        self.assertEqual(outcome["published_at"], "2026-07-24T16:30:00Z")
        self.assertEqual(outcome["window_timezone"], "Asia/Shanghai")
        self.assertEqual(outcome["date_qualification"], "within_window")
        self.assertEqual(outcome["eligibility"], "eligible_for_review")

    def test_inferred_date_is_isolated_from_strict_time_ranking(self) -> None:
        outcome = contract.normalize_source_outcome(
            raw_outcome(
                published_at_confidence="inferred",
                date_basis="content_text",
            ),
            now=NOW,
        )

        self.assertEqual(outcome["date_qualification"], "within_window_inferred")
        self.assertEqual(outcome["eligibility"], "inferred_date_review_only")
        self.assertFalse(outcome["may_enter_time_bounded_ranking"])
        self.assertTrue(outcome["may_enter_general_review"])

    def test_rate_limit_uses_bounded_retry_and_opens_breaker_at_threshold(self) -> None:
        retrying = contract.normalize_source_outcome(
            raw_outcome(
                result_state="rate_limited",
                http_status=429,
                attempt=1,
                max_attempts=3,
                error_code="http_429",
                error_summary="rate limit",
                retry_after_seconds=90,
                breaker_failure_count=1,
                content_sha256=None,
                published_at=None,
                published_at_confidence="unknown",
                date_basis="unavailable",
            ),
            now=NOW,
        )
        exhausted = contract.normalize_source_outcome(
            raw_outcome(
                result_state="rate_limited",
                http_status=429,
                attempt=3,
                max_attempts=3,
                error_code="http_429",
                error_summary="rate limit",
                retry_after_seconds=90,
                breaker_failure_count=3,
                content_sha256=None,
                published_at=None,
                published_at_confidence="unknown",
                date_basis="unavailable",
            ),
            now=NOW,
        )

        self.assertEqual(retrying["source_status"], "rate_limited")
        self.assertFalse(retrying["discoveries_allowed"])
        self.assertEqual(retrying["discovery_count"], 0)
        self.assertEqual(retrying["retry"]["decision"], "retry_after")
        self.assertEqual(retrying["retry"]["delay_seconds"], 90)
        self.assertEqual(retrying["breaker"]["action"], "count_failure")
        self.assertEqual(retrying["breaker"]["failure_count"], 2)
        self.assertEqual(exhausted["retry"]["decision"], "exhausted")
        self.assertEqual(exhausted["breaker"]["action"], "open")
        self.assertEqual(exhausted["breaker"]["cooldown_seconds"], 300)
        self.assertEqual(exhausted["breaker"]["scope"], "xiaohongshu:xhs-browser-v1")

    def test_terminal_access_failures_are_never_retried(self) -> None:
        for state in ("authentication_required", "challenge", "robots_blocked", "unauthorized"):
            with self.subTest(state=state):
                outcome = contract.normalize_source_outcome(
                    raw_outcome(
                        result_state=state,
                        http_status=403,
                        attempt=1,
                        error_code=state,
                        error_summary=state,
                        content_sha256=None,
                        published_at=None,
                        published_at_confidence="unknown",
                        date_basis="unavailable",
                    ),
                    now=NOW,
                )

                self.assertEqual(outcome["retry"]["decision"], "terminal")
                self.assertEqual(outcome["breaker"]["action"], "do_not_count")
                self.assertEqual(outcome["eligibility"], "blocked")

    def test_schema_validation_and_digest_reject_tampering(self) -> None:
        outcome = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        schema = json.loads(OUTCOME_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(outcome)

        outcome["eligibility"] = "blocked"
        with self.assertRaisesRegex(contract.SourceContractError, "digest"):
            contract.validate_source_outcome(outcome)

    def test_semantic_tampering_fails_even_after_redigest(self) -> None:
        outcome = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        outcome["eligibility"] = "blocked"
        outcome["outcome_digest_sha256"] = contract._digest(
            outcome, omit=("outcome_digest_sha256",)
        )

        with self.assertRaisesRegex(contract.SourceContractError, "semantic"):
            contract.validate_source_outcome(outcome)

        qualification = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        qualification["date_qualification"] = "after_window"
        qualification["eligibility"] = "outside_timeframe"
        qualification["may_enter_time_bounded_ranking"] = False
        qualification["outcome_digest_sha256"] = contract._digest(
            qualification, omit=("outcome_digest_sha256",)
        )
        with self.assertRaisesRegex(contract.SourceContractError, "date qualification"):
            contract.validate_source_outcome(qualification)

    def test_resigned_outcome_rejects_unknown_fields_and_derived_recovery_tampering(
        self,
    ) -> None:
        cases: list[dict[str, object]] = []

        unknown_root = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        unknown_root["unexpected"] = "smuggled"
        cases.append(unknown_root)

        unknown_nested = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        unknown_nested["acquisition"]["cookie"] = "smuggled"
        cases.append(unknown_nested)

        retry_tamper = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        retry_tamper["retry"]["decision"] = "retry_after"
        retry_tamper["retry"]["delay_seconds"] = 1
        cases.append(retry_tamper)

        breaker_tamper = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        breaker_tamper["breaker"]["action"] = "open"
        cases.append(breaker_tamper)

        for outcome in cases:
            outcome["outcome_digest_sha256"] = contract._digest(
                outcome, omit=("outcome_digest_sha256",)
            )
            with self.subTest(keys=sorted(outcome)):
                with self.assertRaisesRegex(
                    contract.SourceContractError, "fields|deterministic"
                ):
                    contract.validate_source_outcome(outcome)

    def test_resigned_outcome_cannot_bypass_observation_semantics(self) -> None:
        cases: list[tuple[str, dict[str, object]]] = []

        not_authorized = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        not_authorized["acquisition"]["authorization"] = "not_granted"
        cases.append(("authorization", not_authorized))

        unauthorized_http = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        unauthorized_http["acquisition"]["http_status"] = 401
        cases.append(("http_status", unauthorized_http))

        missing_content = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        missing_content["acquisition"]["content_sha256"] = None
        cases.append(("content_sha256", missing_content))

        success_with_error = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        success_with_error["error"] = {
            "code": "login_required",
            "summary": "login required",
        }
        cases.append(("error", success_with_error))

        invalid_observed = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        invalid_observed["observed_at"] = "not-a-date"
        cases.append(("observed_at", invalid_observed))

        invalid_normalized = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        invalid_normalized["normalized_at"] = "not-a-date"
        cases.append(("normalized_at", invalid_normalized))

        reversed_times = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        reversed_times["normalized_at"] = "2026-08-24T07:59:59Z"
        cases.append(("normalized_at", reversed_times))

        invalid_backend = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        invalid_backend["acquisition"]["backend_id"] = "../other-backend"
        cases.append(("backend_id", invalid_backend))

        invalid_endpoint = contract.normalize_source_outcome(raw_outcome(), now=NOW)
        invalid_endpoint["acquisition"]["response_endpoint"] = "file:///etc/passwd"
        cases.append(("url", invalid_endpoint))

        for field, outcome in cases:
            outcome["outcome_digest_sha256"] = contract._digest(
                outcome, omit=("outcome_digest_sha256",)
            )
            with self.subTest(field=field):
                with self.assertRaises(contract.SourceContractError):
                    contract.validate_source_outcome(outcome)


class SourceObservationValidationTests(unittest.TestCase):
    def test_rejects_impossible_success_and_secret_bearing_fields(self) -> None:
        with self.assertRaisesRegex(contract.SourceContractError, "content_sha256"):
            contract.normalize_source_outcome(raw_outcome(content_sha256=None), now=NOW)
        with self.assertRaisesRegex(contract.SourceContractError, "unexpected"):
            contract.normalize_source_outcome(raw_outcome(cookie="secret"), now=NOW)
        with self.assertRaisesRegex(contract.SourceContractError, "authorization"):
            contract.normalize_source_outcome(
                raw_outcome(authorization="not_granted"), now=NOW
            )

    def test_rejects_inconsistent_date_confidence(self) -> None:
        cases = [
            raw_outcome(published_at=None, published_at_confidence="observed"),
            raw_outcome(published_at="2026-08-20T12:00:00Z", published_at_confidence="unknown"),
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(contract.SourceContractError, "published_at"):
                    contract.normalize_source_outcome(payload, now=NOW)

    def test_retry_metadata_is_bounded(self) -> None:
        for attempt, maximum in ((0, 3), (4, 3), (1, 0), (1, 6)):
            with self.subTest(attempt=attempt, maximum=maximum):
                with self.assertRaisesRegex(contract.SourceContractError, "attempt"):
                    contract.normalize_source_outcome(
                        raw_outcome(attempt=attempt, max_attempts=maximum), now=NOW
                    )

    def test_rejects_inconsistent_rate_limit_and_breaker_metadata(self) -> None:
        cases = [
            raw_outcome(result_state="rate_limited", http_status=503),
            raw_outcome(breaker_failure_count=4, breaker_threshold=3),
            raw_outcome(breaker_threshold=0),
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(contract.SourceContractError):
                    contract.normalize_source_outcome(payload, now=NOW)

    def test_rejects_payload_shape_and_card_count_inconsistency(self) -> None:
        cases = [
            raw_outcome(payload_shape="content_cards", content_card_count=0),
            raw_outcome(payload_shape="suggestions", content_card_count=1),
            raw_outcome(payload_shape="made_up"),
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(contract.SourceContractError, "payload"):
                    contract.normalize_source_outcome(payload, now=NOW)

    def test_rejects_malformed_observation_envelope(self) -> None:
        cases = [
            (None, "JSON object"),
            ({"schema": "wrong"}, "missing"),
            (raw_outcome(schema="wrong"), "schema"),
            (raw_outcome(run_id="bad/path"), "identifier"),
            (raw_outcome(url="ftp://example.com"), "HTTP"),
            (raw_outcome(url="https://user:pass@example.com"), "credentials"),
            (raw_outcome(observed_at="not-a-date"), "ISO-8601"),
            (raw_outcome(observed_at="2026-08-24T08:00:00"), "timezone"),
            (raw_outcome(timeframe={"start": "bad", "end": "2026-08-24"}), "YYYY-MM-DD"),
            (raw_outcome(timeframe={"start": "2026-08-25", "end": "2026-08-24"}), "after"),
            (raw_outcome(content_sha256="bad"), "SHA-256"),
            (raw_outcome(window_timezone="Mars/Olympus"), "window_timezone"),
            (raw_outcome(platform_id="made_up"), "platform_id"),
        ]
        for payload, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(contract.SourceContractError, message):
                    contract.normalize_source_outcome(payload, now=NOW)

    def test_rejects_error_contract_inconsistency(self) -> None:
        cases = [
            raw_outcome(error_code="unexpected", error_summary="unexpected"),
            raw_outcome(http_status=401),
            raw_outcome(
                result_state="parse_error",
                http_status=200,
                content_sha256=None,
                error_code=None,
                error_summary=None,
            ),
            raw_outcome(retry_after_seconds=10),
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(contract.SourceContractError):
                    contract.normalize_source_outcome(payload, now=NOW)


def checkpoint_input(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "run_id": "run-source-001",
        "topic": "AI Agent 搜索",
        "platform_id": "xiaohongshu",
        "stage": "discovery",
        "exact_probe_or_command": ["agent-reach", "search", "AI Agent"],
        "tool_readiness": "configured",
        "bridge_state": "connected",
        "auth_state": "required",
        "quota_state": "available",
        "authorization": "granted_for_current_task",
        "probe_result": "blocked",
        "error_summary": "login required",
        "completed_query_ids": ["q-001"],
        "pending_query_ids": ["q-002", "q-003"],
        "candidate_ids": ["candidate-001"],
        "artifact_paths": {
            "manifest": "runs/run-source-001/run_manifest.json",
            "queries": "runs/run-source-001/queries.tsv",
            "sources": "runs/run-source-001/sources.tsv",
            "candidates": "runs/run-source-001/candidates.json",
        },
        "next_safe_command": ["agent-reach", "probe", "xiaohongshu"],
        "ttl_seconds": 3600,
    }
    value.update(overrides)
    return value


class CheckpointTests(unittest.TestCase):
    def test_checkpoint_has_ttl_stable_idempotency_and_schema(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)

        self.assertEqual(checkpoint["schema"], "top50-research-checkpoint/v1")
        self.assertEqual(checkpoint["created_at"], "2026-08-24T08:30:00Z")
        self.assertEqual(checkpoint["updated_at"], checkpoint["created_at"])
        self.assertEqual(checkpoint["expires_at"], "2026-08-24T09:30:00Z")
        self.assertEqual(checkpoint["status"], "paused")
        self.assertEqual(checkpoint["resume_count"], 0)
        self.assertEqual(len(checkpoint["checkpoint_id"]), 64)
        self.assertEqual(len(checkpoint["idempotency_key"]), 64)
        self.assertEqual(len(checkpoint["checkpoint_digest_sha256"]), 64)
        self.assertEqual(checkpoint["completed_query_ids"], ["q-001"])
        self.assertEqual(checkpoint["pending_query_ids"], ["q-002", "q-003"])

        schema = json.loads(CHECKPOINT_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(checkpoint)

    def test_identical_pause_state_gets_same_idempotency_key(self) -> None:
        first = contract.create_checkpoint(checkpoint_input(), now=NOW)
        second = contract.create_checkpoint(
            checkpoint_input(
                completed_query_ids=["q-001", "q-001"],
                pending_query_ids=["q-003", "q-002"],
                candidate_ids=["candidate-001", "candidate-001"],
            ),
            now=NOW,
        )

        self.assertEqual(first["idempotency_key"], second["idempotency_key"])
        self.assertEqual(first, second)

    def test_resume_requires_fresh_probe_and_returns_only_pending_work(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)

        with self.assertRaisesRegex(contract.SourceContractError, "fresh probe"):
            contract.resume_checkpoint(
                checkpoint,
                probe={"observed_at": "2026-08-24T08:40:00Z", "result": "blocked"},
                now=datetime(2026, 8, 24, 8, 40, tzinfo=timezone.utc),
            )

        resume = contract.resume_checkpoint(
            checkpoint,
            probe={
                "observed_at": "2026-08-24T08:40:00Z",
                "result": "success",
                "equivalent_command": ["agent-reach", "probe", "xiaohongshu"],
            },
            now=datetime(2026, 8, 24, 8, 40, tzinfo=timezone.utc),
        )

        self.assertEqual(resume["query_ids_to_execute"], ["q-002", "q-003"])
        self.assertEqual(resume["completed_query_ids"], ["q-001"])
        self.assertEqual(resume["resume_count"], 1)
        self.assertEqual(resume["status"], "resuming")

    def test_completed_checkpoint_cannot_resume(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        complete = contract.advance_checkpoint(
            checkpoint,
            completed_query_ids=["q-002", "q-003"],
            now=datetime(2026, 8, 24, 8, 45, tzinfo=timezone.utc),
        )

        with self.assertRaisesRegex(contract.SourceContractError, "complete"):
            contract.resume_checkpoint(
                complete,
                probe={
                    "observed_at": "2026-08-24T08:50:00Z",
                    "result": "success",
                    "equivalent_command": ["agent-reach", "probe", "xiaohongshu"],
                },
                now=datetime(2026, 8, 24, 8, 50, tzinfo=timezone.utc),
            )

    def test_expired_checkpoint_fails_closed(self) -> None:
        checkpoint = contract.create_checkpoint(
            checkpoint_input(ttl_seconds=60), now=NOW
        )

        with self.assertRaisesRegex(contract.SourceContractError, "expired"):
            contract.resume_checkpoint(
                checkpoint,
                probe={
                    "observed_at": "2026-08-24T08:32:00Z",
                    "result": "success",
                    "equivalent_command": ["agent-reach", "probe", "xiaohongshu"],
                },
                now=datetime(2026, 8, 24, 8, 32, tzinfo=timezone.utc),
            )

    def test_advancing_checkpoint_is_monotonic_and_preserves_error_history(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        advanced = contract.advance_checkpoint(
            checkpoint,
            completed_query_ids=["q-002"],
            candidate_ids=["candidate-002"],
            error_summary="one result page was empty",
            now=datetime(2026, 8, 24, 8, 45, tzinfo=timezone.utc),
        )

        self.assertEqual(advanced["completed_query_ids"], ["q-001", "q-002"])
        self.assertEqual(advanced["pending_query_ids"], ["q-003"])
        self.assertEqual(
            advanced["candidate_ids"], ["candidate-001", "candidate-002"]
        )
        self.assertEqual(
            advanced["error_history"],
            ["login required", "one result page was empty"],
        )
        self.assertEqual(advanced["created_at"], checkpoint["created_at"])
        self.assertEqual(advanced["idempotency_key"], checkpoint["idempotency_key"])
        contract.validate_checkpoint(advanced)

        resume = contract.resume_checkpoint(
            advanced,
            probe={
                "observed_at": "2026-08-24T08:50:00Z",
                "result": "success",
                "equivalent_command": ["agent-reach", "probe", "xiaohongshu"],
            },
            now=datetime(2026, 8, 24, 8, 50, tzinfo=timezone.utc),
        )
        self.assertEqual(resume["query_ids_to_execute"], ["q-003"])

        with self.assertRaisesRegex(contract.SourceContractError, "pending"):
            contract.advance_checkpoint(
                checkpoint,
                completed_query_ids=["q-not-pending"],
                now=datetime(2026, 8, 24, 8, 45, tzinfo=timezone.utc),
            )

    def test_checkpoint_digest_rejects_tampering(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        checkpoint["pending_query_ids"].append("q-injected")

        with self.assertRaisesRegex(contract.SourceContractError, "digest"):
            contract.validate_checkpoint(checkpoint)

    def test_checkpoint_semantic_tampering_fails_after_redigest(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        checkpoint["completed_query_ids"] = ["q-001", "q-002"]
        checkpoint["checkpoint_digest_sha256"] = contract._digest(
            checkpoint, omit=("checkpoint_digest_sha256",)
        )

        with self.assertRaisesRegex(contract.SourceContractError, "overlap"):
            contract.validate_checkpoint(checkpoint)

    def test_rejects_malformed_checkpoint_input(self) -> None:
        cases = [
            (None, "JSON object"),
            ({}, "missing"),
            (checkpoint_input(extra=True), "unexpected"),
            (checkpoint_input(pending_query_ids=[]), "pending"),
            (checkpoint_input(completed_query_ids=["q-002"], pending_query_ids=["q-002"]), "disjoint"),
            (checkpoint_input(artifact_paths={}), "artifact_paths"),
            (
                checkpoint_input(
                    artifact_paths={
                        "manifest": "runs/other/run_manifest.json",
                        "queries": "runs/other/queries.tsv",
                        "sources": "runs/other/sources.tsv",
                        "candidates": "runs/other/candidates.json",
                    }
                ),
                "run_id",
            ),
            (checkpoint_input(ttl_seconds=1), "ttl_seconds"),
            (checkpoint_input(platform_id="made_up"), "platform_id"),
        ]
        for payload, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(contract.SourceContractError, message):
                    contract.create_checkpoint(payload, now=NOW)

    def test_rejects_bad_checkpoint_schema_and_timestamps(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        with self.assertRaisesRegex(contract.SourceContractError, "schema"):
            contract.validate_checkpoint(None)

        bad = copy.deepcopy(checkpoint)
        bad["updated_at"] = bad["expires_at"]
        bad["checkpoint_digest_sha256"] = contract._digest(
            bad, omit=("checkpoint_digest_sha256",)
        )
        with self.assertRaisesRegex(contract.SourceContractError, "timestamps"):
            contract.validate_checkpoint(bad)

    def test_resume_rejects_stale_future_and_wrong_command_probe(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        cases = [
            (
                {"observed_at": "2026-08-24T08:30:00Z", "result": "success", "equivalent_command": ["agent-reach", "probe", "xiaohongshu"]},
                "fresh",
            ),
            (
                {"observed_at": "2026-08-24T09:00:00Z", "result": "success", "equivalent_command": ["agent-reach", "probe", "xiaohongshu"]},
                "future",
            ),
            (
                {"observed_at": "2026-08-24T08:40:00Z", "result": "success", "equivalent_command": ["different", "probe"]},
                "equivalent",
            ),
        ]
        for probe, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(contract.SourceContractError, message):
                    contract.resume_checkpoint(
                        checkpoint,
                        probe=probe,
                        now=datetime(2026, 8, 24, 8, 40, tzinfo=timezone.utc),
                    )

    def test_atomic_write_preserves_existing_file_unless_same_idempotent_payload(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        different = contract.create_checkpoint(
            checkpoint_input(pending_query_ids=["q-009"]), now=NOW
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "checkpoint.json"
            contract.write_checkpoint_atomic(path, checkpoint)
            contract.write_checkpoint_atomic(path, copy.deepcopy(checkpoint))
            original = path.read_text(encoding="utf-8")

            with self.assertRaisesRegex(contract.SourceContractError, "different checkpoint"):
                contract.write_checkpoint_atomic(path, different)

            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_atomic_write_accepts_monotonic_progress_and_rejects_rollback(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        advanced = contract.advance_checkpoint(
            checkpoint,
            completed_query_ids=["q-002"],
            now=datetime(2026, 8, 24, 8, 45, tzinfo=timezone.utc),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "checkpoint.json"
            contract.write_checkpoint_atomic(path, checkpoint)
            contract.write_checkpoint_atomic(path, advanced)

            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored, advanced)
            with self.assertRaisesRegex(contract.SourceContractError, "rollback"):
                contract.write_checkpoint_atomic(path, checkpoint)

    def test_checkpoint_commands_reject_secret_bearing_arguments(self) -> None:
        for command in (
            ["curl", "--cookie", "session=secret"],
            ["tool", "--authorization=Bearer secret"],
            ["tool", "--api-key", "secret"],
        ):
            with self.subTest(command=command):
                with self.assertRaisesRegex(contract.SourceContractError, "secret"):
                    contract.create_checkpoint(
                        checkpoint_input(exact_probe_or_command=command), now=NOW
                    )

    def test_cli_normalizes_outcome_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "raw.json"
            output_path = root / "outcome.json"
            input_path.write_text(json.dumps(raw_outcome()), encoding="utf-8")
            command = [
                sys.executable,
                str(SCRIPT),
                "normalize-outcome",
                "--input",
                str(input_path),
                "--output",
                str(output_path),
            ]

            first = subprocess.run(command, capture_output=True, text=True, check=False)
            second = subprocess.run(command, capture_output=True, text=True, check=False)

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)
            contract.validate_source_outcome(
                json.loads(output_path.read_text(encoding="utf-8"))
            )

    def test_cli_resume_and_advance_replace_checkpoint_monotonically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            checkpoint_path = root / "checkpoint.json"
            checkpoint = contract.create_checkpoint(
                checkpoint_input(), now=datetime.now(timezone.utc)
            )
            contract.write_checkpoint_atomic(checkpoint_path, checkpoint)

            probe_path = root / "probe.json"
            probe_path.write_text(
                json.dumps(
                    {
                        "observed_at": (
                            datetime.now(timezone.utc) + timedelta(seconds=2)
                        ).isoformat(),
                        "result": "success",
                        "equivalent_command": [
                            "agent-reach",
                            "probe",
                            "xiaohongshu",
                        ],
                    }
                ),
                encoding="utf-8",
            )
            resumed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "resume-checkpoint",
                    "--checkpoint",
                    str(checkpoint_path),
                    "--probe",
                    str(probe_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            resume_receipt = json.loads(resumed.stdout)
            self.assertEqual(resume_receipt["status"], "resuming")
            stored = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["status"], "resuming")
            self.assertEqual(stored["resume_count"], 1)
            self.assertEqual(stored["error_history"], ["login required"])

            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "completed_query_ids": ["q-002"],
                        "candidate_ids": ["candidate-002"],
                        "error_summary": "one result page was empty",
                    }
                ),
                encoding="utf-8",
            )
            advanced = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "advance-checkpoint",
                    "--checkpoint",
                    str(checkpoint_path),
                    "--progress",
                    str(progress_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(advanced.returncode, 0, advanced.stderr)
            stored = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            self.assertEqual(stored["completed_query_ids"], ["q-001", "q-002"])
            self.assertEqual(stored["pending_query_ids"], ["q-003"])
            self.assertEqual(stored["candidate_ids"], ["candidate-001", "candidate-002"])
            self.assertEqual(
                stored["error_history"],
                ["login required", "one result page was empty"],
            )

            before_reentry = checkpoint_path.read_bytes()
            reentry = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "advance-checkpoint",
                    "--checkpoint",
                    str(checkpoint_path),
                    "--progress",
                    str(progress_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(reentry.returncode, 0)
            self.assertIn("pending", reentry.stderr)
            self.assertEqual(checkpoint_path.read_bytes(), before_reentry)

    def test_atomic_checkpoint_replacement_rejects_error_history_loss(self) -> None:
        checkpoint = contract.create_checkpoint(checkpoint_input(), now=NOW)
        advanced = contract.advance_checkpoint(
            checkpoint,
            completed_query_ids=["q-002"],
            error_summary="new error",
            now=datetime(2026, 8, 24, 8, 45, tzinfo=timezone.utc),
        )
        lost_history = copy.deepcopy(advanced)
        lost_history["error_history"] = ["new error"]
        lost_history["checkpoint_digest_sha256"] = contract._digest(
            lost_history, omit=("checkpoint_digest_sha256",)
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "checkpoint.json"
            contract.write_checkpoint_atomic(path, checkpoint)
            with self.assertRaisesRegex(contract.SourceContractError, "error history"):
                contract.write_checkpoint_atomic(path, lost_history)


if __name__ == "__main__":
    unittest.main()
