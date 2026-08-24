from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import atexit
from unittest import mock
from pathlib import Path

import jsonschema


SKILL_ROOT = Path(__file__).parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "compile_route_bundle.py"
SPEC = importlib.util.spec_from_file_location("compile_route_bundle", SCRIPT)
assert SPEC and SPEC.loader
compiler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compiler
SPEC.loader.exec_module(compiler)

ROUTER_SCRIPT = SKILL_ROOT / "scripts" / "engine_router.py"
ROUTER_SPEC = importlib.util.spec_from_file_location("engine_router_for_route_bundle", ROUTER_SCRIPT)
assert ROUTER_SPEC and ROUTER_SPEC.loader
router = importlib.util.module_from_spec(ROUTER_SPEC)
sys.modules[ROUTER_SPEC.name] = router
ROUTER_SPEC.loader.exec_module(router)

PLANNER_SCRIPT = SKILL_ROOT / "scripts" / "research_planner.py"
PLANNER_SPEC = importlib.util.spec_from_file_location(
    "research_planner_for_route_bundle", PLANNER_SCRIPT
)
assert PLANNER_SPEC and PLANNER_SPEC.loader
planner = importlib.util.module_from_spec(PLANNER_SPEC)
sys.modules[PLANNER_SPEC.name] = planner
PLANNER_SPEC.loader.exec_module(planner)

_QUERY_PLAN_FIXTURE = tempfile.TemporaryDirectory(prefix="top50-route-query-plan-")
atexit.register(_QUERY_PLAN_FIXTURE.cleanup)


CANONICAL_PLATFORMS = (
    "csdn",
    "wechat_official_accounts",
    "zhihu",
    "xiaohongshu",
    "weibo",
    "douyin",
    "x",
    "bilibili",
    "juejin",
    "youtube",
    "linuxdo",
    "github",
    "baidu_search",
    "google_search",
    "bing_search",
    "toutiao",
    "36kr",
    "infoq",
    "segmentfault",
    "oschina",
    "v2ex",
    "reddit",
    "hacker_news",
    "medium",
    "linkedin",
    "kuaishou",
    "wechat_channels",
    "tiktok",
)


def public_http_binding(job_count: int) -> dict[str, object]:
    return {
        "manifest_path": "route-inputs/run-001/public-http-manifest.json",
        "manifest_artifact_sha256": "a" * 64,
        "job_set_sha256": "b" * 64,
        "job_count": job_count,
    }


def write_query_plan(root: Path, *, run_id: str = "run-001") -> tuple[Path, dict[str, object]]:
    plan = planner.compile_query_plan(
        {
            "schema": "top50-research-query-request/v1",
            "run_id": run_id,
            "topic": "Agent 跨平台检索",
            "purpose": "建立可审计 Top 50",
            "platforms": [
                {"platform_id": "github", "required": True},
                {"platform_id": "csdn", "required": False},
            ],
            "aliases": [],
            "languages": ["zh"],
            "intents": ["exact", "failure"],
            "timeframe": {"start": "2026-07-25", "end": "2026-08-24"},
            "tokenizer_mode": "cjk_bigram",
        }
    )
    path = root / "query_plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return path, plan


def scope(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "top50-route-scope/v1",
        "run_id": "run-001",
        "topic": "Agent 跨平台检索",
        "top_n": 50,
        "engine_mode": "auto",
        "dual_run": False,
        "login_mode": "public-only",
        "platform_routes": [
            {"platform_id": "github", "access_kind": "platform_cli", "required": True}
        ],
    }
    value.update(overrides)
    if "query_plan_path" not in overrides:
        fixture_root = Path(_QUERY_PLAN_FIXTURE.name)
        plan_run_id = str(value["run_id"])
        if not plan_run_id or any(
            character
            not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
            for character in plan_run_id
        ):
            plan_run_id = "run-001"
        query_plan_path, _ = write_query_plan(fixture_root, run_id=plan_run_id)
        value["query_plan_path"] = str(query_plan_path)
    return value


def shard(bundle: dict[str, object], shard_id: str) -> dict[str, object]:
    rows = [row for row in bundle["shards"] if row["shard_id"] == shard_id]
    if len(rows) != 1:
        raise AssertionError(f"expected one shard {shard_id}, found {len(rows)}")
    return rows[0]


def redigest(bundle: dict[str, object]) -> dict[str, object]:
    """Refresh only the digest so semantic tamper tests reach the intended gate."""
    bundle["bundle_digest_sha256"] = compiler._digest(bundle)
    return bundle


class CompilationTests(unittest.TestCase):
    def test_freezes_exact_research_query_plan_into_discovery_router_requests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            query_plan_path, query_plan = write_query_plan(Path(directory))
            raw_sha256 = hashlib.sha256(query_plan_path.read_bytes()).hexdigest()
            bundle = compiler.compile_route_bundle(
                scope(query_plan_path=str(query_plan_path))
            )
            query_ids = sorted(str(row["query_id"]) for row in query_plan["queries"])
            expected = {
                "path": str(query_plan_path.resolve()),
                "artifact_sha256": raw_sha256,
                "plan_digest_sha256": query_plan["plan_digest_sha256"],
                "query_count": len(query_ids),
                "query_ids_sha256": compiler._canonical_value_sha256(query_ids),
            }
            self.assertEqual(bundle["query_plan_binding"], expected)
            discovery = shard(bundle, "platform-cli-discovery")
            self.assertEqual(discovery["router_request"]["query_plan_binding"], expected)
            self.assertNotIn(
                "query_plan_binding",
                shard(bundle, "platform-cli-fetch")["router_request"],
            )

    def test_compiles_grouped_replayable_shards_and_shared_handoffs(self) -> None:
        payload = scope(
            engine_mode="hybrid",
            login_mode="user-assisted",
            platform_routes=[
                {"platform_id": "github", "access_kind": "platform_cli", "required": True},
                {"platform_id": "xiaohongshu", "access_kind": "browser_session", "required": True},
                {"platform_id": "csdn", "access_kind": "platform_cli", "required": False},
            ],
            public_url_count=50,
            public_urls_authorized=True,
            public_http_binding=public_http_binding(50),
            local_candidate_count=150,
            extraction_complete=True,
        )

        bundle = compiler.compile_route_bundle(payload)

        self.assertEqual(bundle["schema"], "top50-route-bundle/v1")
        self.assertEqual(bundle["run_id"], "run-001")
        self.assertEqual(bundle["topic"], "Agent 跨平台检索")
        self.assertEqual(bundle["platform_scope_mode"], "required_plus_default")
        self.assertEqual(
            bundle["assumptions"],
            [
                {"field": "platform_scope_mode", "value": "required_plus_default", "reason": "omitted_default"},
                {"field": "risk", "value": "low", "reason": "omitted_default"},
            ],
        )
        self.assertEqual(
            [row["shard_id"] for row in bundle["shards"]],
            [
                "platform-cli-discovery",
                "platform-cli-fetch",
                "browser-session-discovery",
                "browser-session-fetch",
                "public-http-fetch",
                "local-bundle-process",
                "local-bundle-rank",
            ],
        )

        cli_discovery = shard(bundle, "platform-cli-discovery")
        self.assertEqual(cli_discovery["platform_ids"], ["csdn", "github"])
        self.assertEqual(cli_discovery["required_platform_ids"], ["github"])
        self.assertEqual(cli_discovery["status"], "ready_to_plan")
        self.assertEqual(cli_discovery["router_request"]["source_kind"], "platform_cli")
        self.assertEqual(cli_discovery["router_request"]["stage"], "discovery")
        self.assertEqual(cli_discovery["router_request"]["engine_mode"], "python")
        self.assertFalse(cli_discovery["router_request"]["dual_run"])

        browser = shard(bundle, "browser-session-discovery")
        self.assertEqual(browser["status"], "pending_checkpoint")
        self.assertNotIn("router_request", browser)
        self.assertEqual(browser["checkpoint"]["contract"], "top50-login-checkpoint/v1")
        self.assertTrue(browser["checkpoint"]["required_before_plan"])

        public = shard(bundle, "public-http-fetch")
        self.assertEqual(public["input_count"], 50)
        self.assertEqual(public["workload"], "medium")
        self.assertEqual(public["router_request"]["engine_mode"], "hybrid")
        self.assertEqual(public["router_request"]["source_kind"], "public_http")
        self.assertEqual(
            public["router_request"]["public_http_binding"], public_http_binding(50)
        )
        self.assertFalse(public["router_request"]["dual_run"])

        process = shard(bundle, "local-bundle-process")
        rank = shard(bundle, "local-bundle-rank")
        self.assertEqual(process["workload"], "large")
        self.assertEqual(process["router_request"]["engine_mode"], "hybrid")
        self.assertEqual(process["router_request"]["dual_run"], False)
        self.assertEqual(rank["router_request"]["engine_mode"], "python")
        self.assertEqual(rank["router_request"]["stage"], "rank")

        ready = [row for row in bundle["shards"] if row["status"] == "ready_to_plan"]
        self.assertGreater(len(ready), 0)
        for row in ready:
            with self.subTest(shard=row["shard_id"]):
                self.assertTrue(row["run_dir"].startswith("route-runs/run-001/"))
                self.assertTrue(row["plan_filename"].endswith(f"{row['shard_id']}.plan.json"))
                self.assertEqual(row["merge_contract"], "top50-route-shard-result/v1")
                self.assertEqual(row["router_request"]["run_dir"], row["run_dir"])
                self.assertEqual(row["router_request"]["run_id"], "run-001")

        self.assertEqual(
            bundle["plan_filenames"],
            {row["shard_id"]: row["plan_filename"] for row in bundle["shards"]},
        )
        self.assertEqual(
            [row["handoff_id"] for row in bundle["shared_handoffs"]],
            ["shards-to-merge", "merge-to-curate", "curate-to-rank"],
        )
        merge_handoff = bundle["shared_handoffs"][0]
        ready_pre_curator_shard_ids = [
            row["shard_id"]
            for row in bundle["shards"]
            if row["status"] == "ready_to_plan" and row["stage"] != "rank"
        ]
        self.assertEqual(merge_handoff["input_shard_ids"], ready_pre_curator_shard_ids)
        self.assertNotIn("browser-session-discovery", merge_handoff["input_shard_ids"])
        self.assertNotIn("browser-session-fetch", merge_handoff["input_shard_ids"])
        self.assertNotIn("local-bundle-rank", merge_handoff["input_shard_ids"])
        self.assertEqual(
            merge_handoff["input_contract"],
            "top50-route-shard-result-manifest/v1",
        )
        self.assertEqual(bundle["shared_handoffs"][-1]["required_status"], "accepted")
        rank_run_dir = Path(rank["router_request"]["run_dir"])
        self.assertEqual(
            str(rank_run_dir / "curate-result.json"), bundle["artifacts"]["curator_acceptance"]
        )
        self.assertEqual(
            str(rank_run_dir / "ranking-output" / "run_summary.json"),
            bundle["artifacts"]["ranking_result"],
        )
        self.assertEqual(
            process["router_request"]["run_dir"], rank["router_request"]["run_dir"]
        )
        self.assertEqual(
            str(Path(process["router_request"]["run_dir"]) / "extraction-result.json"),
            bundle["artifacts"]["extraction_result"],
        )
        self.assertEqual(len(bundle["bundle_digest_sha256"]), 64)

    def test_semantically_identical_route_order_produces_identical_bundle(self) -> None:
        routes = [
            {"platform_id": "github", "access_kind": "platform_cli", "required": True},
            {"platform_id": "csdn", "access_kind": "platform_cli", "required": False},
        ]
        first = compiler.compile_route_bundle(scope(platform_routes=routes, risk="medium"))
        second = compiler.compile_route_bundle(scope(platform_routes=list(reversed(routes)), risk="medium"))

        self.assertEqual(first, second)

    def test_dual_run_is_only_forwarded_to_compatible_data_stage(self) -> None:
        bundle = compiler.compile_route_bundle(
            scope(
                dual_run=True,
                public_url_count=75,
                public_urls_authorized=True,
                public_http_binding=public_http_binding(75),
                local_candidate_count=75,
                extraction_complete=True,
            )
        )

        self.assertFalse(shard(bundle, "platform-cli-discovery")["router_request"]["dual_run"])
        self.assertTrue(shard(bundle, "public-http-fetch")["router_request"]["dual_run"])
        self.assertTrue(shard(bundle, "local-bundle-process")["router_request"]["dual_run"])
        self.assertFalse(shard(bundle, "local-bundle-rank")["router_request"]["dual_run"])


class ScopeAndAccessTests(unittest.TestCase):
    def test_required_plus_default_expands_coverage_without_inventing_routes(self) -> None:
        bundle = compiler.compile_route_bundle(scope())

        self.assertEqual([row["platform_id"] for row in bundle["coverage_targets"]], list(CANONICAL_PLATFORMS))
        github = next(row for row in bundle["coverage_targets"] if row["platform_id"] == "github")
        zhihu = next(row for row in bundle["coverage_targets"] if row["platform_id"] == "zhihu")
        self.assertEqual(github["route_status"], "planned")
        self.assertEqual(github["access_kind"], "platform_cli")
        self.assertTrue(github["required"])
        self.assertEqual(zhihu["route_status"], "pending_classification")
        self.assertIsNone(zhihu["access_kind"])
        self.assertFalse(zhihu["required"])
        self.assertNotIn("zhihu", shard(bundle, "platform-cli-discovery")["platform_ids"])

    def test_include_only_keeps_only_explicit_routes(self) -> None:
        bundle = compiler.compile_route_bundle(
            scope(
                platform_scope_mode="include_only",
                platform_routes=[
                    {"platform_id": "zhihu", "access_kind": "browser_session", "required": False}
                ],
            )
        )

        self.assertEqual([row["platform_id"] for row in bundle["coverage_targets"]], ["zhihu"])
        self.assertEqual(bundle["assumptions"], [{"field": "risk", "value": "low", "reason": "omitted_default"}])

    def test_public_only_browser_routes_are_blocked_without_login_request(self) -> None:
        bundle = compiler.compile_route_bundle(
            scope(
                platform_scope_mode="include_only",
                platform_routes=[
                    {"platform_id": "xiaohongshu", "access_kind": "browser_session", "required": True}
                ],
            )
        )

        self.assertEqual(len(bundle["shards"]), 2)
        for row in bundle["shards"]:
            self.assertEqual(row["status"], "blocked")
            self.assertEqual(row["reason_code"], "browser_session_disallowed_in_public_only")
            self.assertFalse(row["login_requested"])
            self.assertNotIn("checkpoint", row)
            self.assertNotIn("router_request", row)
        coverage = bundle["coverage_targets"][0]
        self.assertEqual(coverage["route_status"], "blocked")
        self.assertEqual(bundle["shared_handoffs"][0]["input_shard_ids"], [])

    def test_user_assisted_browser_routes_create_one_shared_pending_checkpoint(self) -> None:
        bundle = compiler.compile_route_bundle(
            scope(
                login_mode="user-assisted",
                platform_scope_mode="include_only",
                platform_routes=[
                    {"platform_id": "xiaohongshu", "access_kind": "browser_session", "required": True},
                    {"platform_id": "zhihu", "access_kind": "browser_session", "required": False},
                ],
            )
        )

        checkpoint_paths = {row["checkpoint"]["path"] for row in bundle["shards"]}
        self.assertEqual(checkpoint_paths, {"route-runs/run-001/checkpoints/browser-session.json"})
        self.assertTrue(all(row["status"] == "pending_checkpoint" for row in bundle["shards"]))
        self.assertTrue(all(row["login_requested"] is False for row in bundle["shards"]))
        self.assertEqual(bundle["shared_handoffs"][0]["input_shard_ids"], [])

    def test_ineligible_public_and_local_inputs_are_omitted_not_routed(self) -> None:
        bundle = compiler.compile_route_bundle(
            scope(
                public_url_count=4,
                public_urls_authorized=False,
                local_candidate_count=3,
                extraction_complete=False,
            )
        )

        ids = {row["shard_id"] for row in bundle["shards"]}
        self.assertNotIn("public-http-fetch", ids)
        self.assertNotIn("local-bundle-process", ids)
        self.assertNotIn("local-bundle-rank", ids)
        self.assertEqual(
            bundle["omissions"],
            [
                {"source_kind": "public_http", "reason_code": "public_urls_not_authorized", "input_count": 4},
                {"source_kind": "local_bundle", "reason_code": "extraction_not_complete", "input_count": 3},
            ],
        )


class WorkloadTests(unittest.TestCase):
    def test_thresholds_are_frozen(self) -> None:
        for count, expected in ((0, "small"), (49, "small"), (50, "medium"), (149, "medium"), (150, "large")):
            with self.subTest(count=count):
                self.assertEqual(compiler.workload_for_count(count), expected)

        for count, expected in ((1, "small"), (49, "small"), (50, "medium"), (149, "medium"), (150, "large")):
            with self.subTest(count=count):
                bundle = compiler.compile_route_bundle(
                    scope(
                        platform_routes=[],
                        platform_scope_mode="include_only",
                        public_url_count=count,
                        public_urls_authorized=True,
                        public_http_binding=public_http_binding(count),
                    )
                )
                self.assertEqual(shard(bundle, "public-http-fetch")["workload"], expected)


class FailClosedValidationTests(unittest.TestCase):
    def test_rejects_old_drifted_resigned_and_replaced_query_plans(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, plan = write_query_plan(root)

            old = copy.deepcopy(plan)
            old["schema"] = "top50-scope-query-plan/v1"
            old["plan_digest_sha256"] = compiler._canonical_value_sha256(
                {key: value for key, value in old.items() if key != "plan_digest_sha256"}
            )
            path.write_text(json.dumps(old), encoding="utf-8")
            with self.assertRaisesRegex(compiler.RouteBundleError, "research-query-plan"):
                compiler.compile_route_bundle(scope(query_plan_path=str(path)))

            replaced_path, replaced = write_query_plan(root)
            replaced["run_id"] = "other-run"
            replaced["plan_digest_sha256"] = compiler._canonical_value_sha256(
                {
                    key: value
                    for key, value in replaced.items()
                    if key != "plan_digest_sha256"
                }
            )
            replaced_path.write_text(json.dumps(replaced), encoding="utf-8")
            with self.assertRaisesRegex(compiler.RouteBundleError, "run_id"):
                compiler.compile_route_bundle(scope(query_plan_path=str(replaced_path)))

            drift_path, drift = write_query_plan(root)
            drift["queries"][0]["search_query"] += " drift"
            drift_path.write_text(json.dumps(drift), encoding="utf-8")
            with self.assertRaisesRegex(compiler.RouteBundleError, "digest"):
                compiler.compile_route_bundle(scope(query_plan_path=str(drift_path)))

            resigned_path, resigned = write_query_plan(root)
            resigned["queries"].append(copy.deepcopy(resigned["queries"][0]))
            resigned["counts"]["queries"] += 1
            resigned["plan_digest_sha256"] = compiler._canonical_value_sha256(
                {
                    key: value
                    for key, value in resigned.items()
                    if key != "plan_digest_sha256"
                }
            )
            resigned_path.write_text(json.dumps(resigned), encoding="utf-8")
            with self.assertRaisesRegex(
                compiler.RouteBundleError, "semantic validation|query IDs.*unique"
            ):
                compiler.compile_route_bundle(scope(query_plan_path=str(resigned_path)))

    def test_route_bundle_validation_rejects_query_plan_descriptor_tampering(self) -> None:
        bundle = compiler.compile_route_bundle(scope())
        cases = []
        for field, value in (
            ("artifact_sha256", "0" * 64),
            ("plan_digest_sha256", "1" * 64),
            ("query_count", 99),
            ("query_ids_sha256", "2" * 64),
        ):
            root_drift = copy.deepcopy(bundle)
            root_drift["query_plan_binding"][field] = value
            redigest(root_drift)
            cases.append(root_drift)

            shard_drift = copy.deepcopy(bundle)
            shard(shard_drift, "platform-cli-discovery")["router_request"][
                "query_plan_binding"
            ][field] = value
            redigest(shard_drift)
            cases.append(shard_drift)
        for tampered in cases:
            with self.subTest(tampered=tampered), self.assertRaises(
                compiler.RouteBundleError
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_topic_placeholders_and_punctuation_only_topics(self) -> None:
        for topic in ("", "   ", "《》", "《主题》", "{{TOPIC}}", "<主题>", "请填写主题", "---"):
            with self.subTest(topic=topic), self.assertRaises(compiler.RouteBundleError):
                compiler.compile_route_bundle(scope(topic=topic))

    def test_rejects_duplicate_platform_routes(self) -> None:
        route = {"platform_id": "github", "access_kind": "platform_cli", "required": True}
        with self.assertRaisesRegex(compiler.RouteBundleError, "duplicate platform"):
            compiler.compile_route_bundle(scope(platform_routes=[route, copy.deepcopy(route)]))

    def test_rejects_boolean_negative_and_noninteger_counts(self) -> None:
        for field in ("public_url_count", "local_candidate_count"):
            for value in (True, False, -1, 1.5, "1"):
                with self.subTest(field=field, value=value), self.assertRaises(compiler.RouteBundleError):
                    compiler.compile_route_bundle(scope(**{field: value}))

    def test_rejects_unknown_fields_at_every_input_level(self) -> None:
        invalid = [
            scope(extra=True),
            scope(platform_routes=[{"platform_id": "github", "access_kind": "platform_cli", "required": True, "extra": 1}]),
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(compiler.RouteBundleError, "unknown field"):
                compiler.compile_route_bundle(value)

    def test_public_http_requires_a_strict_manifest_binding(self) -> None:
        with self.assertRaisesRegex(compiler.RouteBundleError, "public_http_binding is required"):
            compiler.compile_route_bundle(
                scope(public_url_count=2, public_urls_authorized=True)
            )

        invalid_bindings = [
            None,
            [],
            {},
            {**public_http_binding(2), "extra": True},
            {**public_http_binding(2), "manifest_path": ""},
            {**public_http_binding(2), "manifest_artifact_sha256": "A" * 64},
            {**public_http_binding(2), "job_set_sha256": "short"},
            {**public_http_binding(2), "job_count": True},
            {**public_http_binding(2), "job_count": 3},
        ]
        for binding in invalid_bindings:
            with self.subTest(binding=binding), self.assertRaises(compiler.RouteBundleError):
                compiler.compile_route_bundle(
                    scope(
                        public_url_count=2,
                        public_urls_authorized=True,
                        public_http_binding=binding,
                    )
                )

    def test_public_http_binding_is_rejected_without_an_eligible_public_batch(self) -> None:
        for overrides in (
            {"public_http_binding": public_http_binding(1)},
            {
                "public_url_count": 1,
                "public_urls_authorized": False,
                "public_http_binding": public_http_binding(1),
            },
        ):
            with self.subTest(overrides=overrides), self.assertRaisesRegex(
                compiler.RouteBundleError, "only allowed"
            ):
                compiler.compile_route_bundle(scope(**overrides))

    def test_rejects_invalid_scalars_enums_and_unknown_platforms(self) -> None:
        invalid = [
            [],
            scope(schema="top50-route-scope/v0"),
            scope(run_id="../escape"),
            scope(top_n=True),
            scope(top_n=0),
            scope(top_n=101),
            scope(engine_mode="fast"),
            scope(dual_run="yes"),
            scope(login_mode="stealth"),
            scope(risk="critical"),
            scope(platform_scope_mode="all"),
            scope(public_urls_authorized="yes"),
            scope(extraction_complete=1),
            scope(platform_routes="github"),
            scope(platform_routes=[{"platform_id": "unknown", "access_kind": "platform_cli", "required": True}]),
            scope(platform_routes=[{"platform_id": "github", "access_kind": "http", "required": True}]),
            scope(platform_routes=[{"platform_id": "github", "access_kind": "platform_cli", "required": 1}]),
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(compiler.RouteBundleError):
                compiler.compile_route_bundle(value)

    def test_rejects_no_shards(self) -> None:
        with self.assertRaisesRegex(compiler.RouteBundleError, "no shards"):
            compiler.compile_route_bundle(
                scope(platform_routes=[], platform_scope_mode="include_only")
            )

    def test_hybrid_requires_eligible_public_or_local_stage(self) -> None:
        invalid = [
            scope(engine_mode="hybrid"),
            scope(engine_mode="hybrid", public_url_count=3, public_urls_authorized=False),
            scope(engine_mode="hybrid", local_candidate_count=3, extraction_complete=False),
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(
                compiler.RouteBundleError, "hybrid.*public_http.*local_bundle"
            ):
                compiler.compile_route_bundle(value)


class RuntimeBundleValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = compiler.compile_route_bundle(
            scope(
                engine_mode="hybrid",
                login_mode="user-assisted",
                platform_routes=[
                    {"platform_id": "github", "access_kind": "platform_cli", "required": True},
                    {"platform_id": "xiaohongshu", "access_kind": "browser_session", "required": True},
                ],
                public_url_count=50,
                public_urls_authorized=True,
                public_http_binding=public_http_binding(50),
                local_candidate_count=150,
                extraction_complete=True,
            )
        )

    def test_accepts_an_untampered_compiled_bundle(self) -> None:
        self.assertIsNone(compiler.validate_route_bundle(self.bundle))

    def test_validation_is_pure_and_does_not_mutate_the_bundle(self) -> None:
        before = copy.deepcopy(self.bundle)

        compiler.validate_route_bundle(self.bundle)

        self.assertEqual(self.bundle, before)

    def test_rejects_redigested_synchronized_canonical_shard_tampering(self) -> None:
        tampered = copy.deepcopy(self.bundle)
        row = shard(tampered, "platform-cli-fetch")
        row.update(
            {
                "source_kind": "browser_session",
                "platform_ids": ["youtube"],
                "required_platform_ids": [],
                "input_count": 999,
                "workload": "large",
            }
        )
        row["router_request"].update(
            {
                "source_kind": "browser_session",
                "workload": "large",
            }
        )
        redigest(tampered)

        with self.assertRaisesRegex(
            compiler.RouteBundleError,
            "shard platform-cli-fetch semantics do not match canonical topology",
        ):
            compiler.validate_route_bundle(tampered)

    def test_rejects_unknown_fields_at_every_bundle_object_level(self) -> None:
        cases = []

        root = copy.deepcopy(self.bundle)
        root["unexpected"] = True
        cases.append(root)

        assumption = copy.deepcopy(self.bundle)
        assumption["assumptions"][0]["unexpected"] = True
        cases.append(assumption)

        coverage = copy.deepcopy(self.bundle)
        coverage["coverage_targets"][0]["unexpected"] = True
        cases.append(coverage)

        shard_row = copy.deepcopy(self.bundle)
        shard(shard_row, "platform-cli-discovery")["unexpected"] = True
        cases.append(shard_row)

        router_request = copy.deepcopy(self.bundle)
        shard(router_request, "platform-cli-discovery")["router_request"]["unexpected"] = True
        cases.append(router_request)

        checkpoint = copy.deepcopy(self.bundle)
        shard(checkpoint, "browser-session-discovery")["checkpoint"]["unexpected"] = True
        cases.append(checkpoint)

        handoff = copy.deepcopy(self.bundle)
        handoff["shared_handoffs"][0]["unexpected"] = True
        cases.append(handoff)

        artifacts = copy.deepcopy(self.bundle)
        artifacts["artifacts"]["unexpected"] = "wrong.json"
        cases.append(artifacts)

        public_binding = copy.deepcopy(self.bundle)
        shard(public_binding, "public-http-fetch")["router_request"][
            "public_http_binding"
        ]["unexpected"] = True
        cases.append(public_binding)

        omitted = compiler.compile_route_bundle(
            scope(public_url_count=2, public_urls_authorized=False)
        )
        omitted["omissions"][0]["unexpected"] = True
        cases.append(omitted)

        for tampered in cases:
            redigest(tampered)
            with self.subTest(tampered=tampered), self.assertRaisesRegex(
                compiler.RouteBundleError, "unknown fields"
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_invalid_root_and_coverage_semantics_after_redigest(self) -> None:
        cases = []

        top_n = copy.deepcopy(self.bundle)
        top_n["top_n"] = 101
        for row in top_n["shards"]:
            if "router_request" in row:
                row["router_request"]["top_n"] = 101
        cases.append((top_n, "top_n"))

        invalid_engine = copy.deepcopy(self.bundle)
        invalid_engine["engine_mode"] = "rust"
        shard(invalid_engine, "public-http-fetch")["router_request"]["engine_mode"] = "rust"
        shard(invalid_engine, "local-bundle-process")["router_request"]["engine_mode"] = "rust"
        cases.append((invalid_engine, "rust.*public_http"))

        login_mode = copy.deepcopy(self.bundle)
        login_mode["login_mode"] = "public-only"
        cases.append((login_mode, "coverage_targets"))

        invalid_coverage = copy.deepcopy(self.bundle)
        pending = next(
            row
            for row in invalid_coverage["coverage_targets"]
            if row["route_status"] == "pending_classification"
        )
        pending["required"] = True
        cases.append((invalid_coverage, "coverage_targets"))

        reordered_coverage = copy.deepcopy(self.bundle)
        reordered_coverage["coverage_targets"][0:2] = reversed(
            reordered_coverage["coverage_targets"][0:2]
        )
        cases.append((reordered_coverage, "canonical order"))

        for tampered, message in cases:
            redigest(tampered)
            with self.subTest(message=message), self.assertRaisesRegex(
                compiler.RouteBundleError, message
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_shard_checkpoint_and_router_semantic_tampering(self) -> None:
        cases = []

        dependency = copy.deepcopy(self.bundle)
        shard(dependency, "platform-cli-fetch")["depends_on"] = []
        cases.append((dependency, "platform-cli-fetch.*canonical topology"))

        merge_contract = copy.deepcopy(self.bundle)
        shard(merge_contract, "platform-cli-fetch")["merge_contract"] = "wrong/v1"
        cases.append((merge_contract, "platform-cli-fetch.*canonical topology"))

        login_requested = copy.deepcopy(self.bundle)
        shard(login_requested, "platform-cli-fetch")["login_requested"] = True
        cases.append((login_requested, "platform-cli-fetch.*canonical topology"))

        checkpoint = copy.deepcopy(self.bundle)
        shard(checkpoint, "browser-session-discovery")["checkpoint"]["platform_ids"] = [
            "zhihu"
        ]
        cases.append((checkpoint, "browser-session-discovery.*canonical topology"))

        router_run = copy.deepcopy(self.bundle)
        shard(router_run, "platform-cli-fetch")["router_request"]["run_id"] = "other-run"
        cases.append((router_run, "platform-cli-fetch.*canonical topology"))

        router_stage = copy.deepcopy(self.bundle)
        shard(router_stage, "platform-cli-fetch")["router_request"]["stage"] = "discovery"
        cases.append((router_stage, "platform-cli-fetch.*canonical topology"))

        router_bundle = copy.deepcopy(self.bundle)
        shard(router_bundle, "platform-cli-fetch")["router_request"].update(
            {"risk": "high", "top_n": 49, "dual_run": True}
        )
        cases.append((router_bundle, "platform-cli-fetch.*canonical topology"))

        for tampered, message in cases:
            redigest(tampered)
            with self.subTest(message=message), self.assertRaisesRegex(
                compiler.RouteBundleError, message
            ):
                compiler.validate_route_bundle(tampered)

    def test_validation_rejects_nonobjects_and_malformed_digest_serialization(self) -> None:
        with self.assertRaisesRegex(compiler.RouteBundleError, "route bundle must be an object"):
            compiler.validate_route_bundle([])

        malformed = copy.deepcopy(self.bundle)
        malformed["assumptions"] = {"not-json-serializable"}
        with self.assertRaisesRegex(compiler.RouteBundleError, "canonically serializable"):
            compiler.validate_route_bundle(malformed)

    def test_rejects_duplicate_shard_ids(self) -> None:
        tampered = copy.deepcopy(self.bundle)
        tampered["shards"][1]["shard_id"] = tampered["shards"][0]["shard_id"]
        redigest(tampered)

        with self.assertRaisesRegex(compiler.RouteBundleError, "duplicate shard_id"):
            compiler.validate_route_bundle(tampered)

    def test_rejects_malformed_shard_graph_fields(self) -> None:
        cases = []

        invalid_status = copy.deepcopy(self.bundle)
        invalid_status["shards"][0]["status"] = "complete"
        cases.append((invalid_status, "invalid status"))

        invalid_stage = copy.deepcopy(self.bundle)
        invalid_stage["shards"][0]["stage"] = "curate"
        cases.append((invalid_stage, "invalid stage"))

        nonarray_dependencies = copy.deepcopy(self.bundle)
        nonarray_dependencies["shards"][0]["depends_on"] = "public-http-fetch"
        cases.append((nonarray_dependencies, "must be an array"))

        duplicate_dependencies = copy.deepcopy(self.bundle)
        duplicate_dependencies["shards"][1]["depends_on"] = [
            "platform-cli-discovery",
            "platform-cli-discovery",
        ]
        cases.append((duplicate_dependencies, "contains duplicates"))

        for tampered, message in cases:
            redigest(tampered)
            with self.subTest(message=message), self.assertRaisesRegex(
                compiler.RouteBundleError, message
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_dangling_dependencies_and_cycles(self) -> None:
        dangling = copy.deepcopy(self.bundle)
        dangling["shards"][0]["depends_on"] = ["missing-shard"]
        redigest(dangling)
        with self.assertRaisesRegex(compiler.RouteBundleError, "unknown shard"):
            compiler.validate_route_bundle(dangling)

        cyclic = copy.deepcopy(self.bundle)
        shard(cyclic, "platform-cli-discovery")["depends_on"] = ["platform-cli-fetch"]
        redigest(cyclic)
        with self.assertRaisesRegex(compiler.RouteBundleError, "cycle"):
            compiler.validate_route_bundle(cyclic)

    def test_rejects_dependency_order_that_is_a_dag_but_not_replayable(self) -> None:
        tampered = copy.deepcopy(self.bundle)
        shard(tampered, "platform-cli-discovery")["depends_on"] = [
            "public-http-fetch"
        ]
        redigest(tampered)

        with self.assertRaisesRegex(compiler.RouteBundleError, "earlier shard"):
            compiler.validate_route_bundle(tampered)

    def test_rejects_merge_inputs_that_omit_ready_or_include_pending_or_rank(self) -> None:
        cases = []

        omitted = copy.deepcopy(self.bundle)
        omitted["shared_handoffs"][0]["input_shard_ids"].remove("public-http-fetch")
        cases.append(omitted)

        pending = copy.deepcopy(self.bundle)
        pending["shared_handoffs"][0]["input_shard_ids"].append(
            "browser-session-discovery"
        )
        cases.append(pending)

        rank_input = copy.deepcopy(self.bundle)
        rank_input["shared_handoffs"][0]["input_shard_ids"].append(
            "local-bundle-rank"
        )
        cases.append(rank_input)

        reordered = copy.deepcopy(self.bundle)
        reordered["shared_handoffs"][0]["input_shard_ids"].reverse()
        cases.append(reordered)

        for tampered in cases:
            with self.subTest(input_shard_ids=tampered["shared_handoffs"][0]["input_shard_ids"]):
                redigest(tampered)
                with self.assertRaisesRegex(compiler.RouteBundleError, "input_shard_ids"):
                    compiler.validate_route_bundle(tampered)

    def test_rejects_plan_filename_key_and_value_tampering(self) -> None:
        wrong_key = copy.deepcopy(self.bundle)
        wrong_key["plan_filenames"]["unknown-shard"] = wrong_key["plan_filenames"].pop(
            "platform-cli-discovery"
        )

        wrong_value = copy.deepcopy(self.bundle)
        wrong_value["plan_filenames"]["platform-cli-discovery"] = "wrong.plan.json"

        for tampered in (wrong_key, wrong_value):
            redigest(tampered)
            with self.assertRaisesRegex(compiler.RouteBundleError, "plan_filenames"):
                compiler.validate_route_bundle(tampered)

    def test_rejects_public_http_binding_tampering(self) -> None:
        cases = []

        missing = copy.deepcopy(self.bundle)
        del shard(missing, "public-http-fetch")["router_request"]["public_http_binding"]
        cases.append(missing)

        wrong_count = copy.deepcopy(self.bundle)
        shard(wrong_count, "public-http-fetch")["router_request"]["public_http_binding"][
            "job_count"
        ] = 49
        cases.append(wrong_count)

        wrong_digest = copy.deepcopy(self.bundle)
        shard(wrong_digest, "public-http-fetch")["router_request"]["public_http_binding"][
            "job_set_sha256"
        ] = "A" * 64
        cases.append(wrong_digest)

        misplaced = copy.deepcopy(self.bundle)
        shard(misplaced, "platform-cli-discovery")["router_request"][
            "public_http_binding"
        ] = public_http_binding(50)
        cases.append(misplaced)

        for tampered in cases:
            redigest(tampered)
            with self.subTest(tampered=tampered), self.assertRaisesRegex(
                compiler.RouteBundleError, "public_http_binding"
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_broken_artifact_handoff_path_chain(self) -> None:
        tampered = copy.deepcopy(self.bundle)
        tampered["shared_handoffs"][1]["input_artifact"] = (
            "route-runs/run-001/merge/wrong.json"
        )
        redigest(tampered)

        with self.assertRaisesRegex(compiler.RouteBundleError, "artifact path chain"):
            compiler.validate_route_bundle(tampered)

    def test_rejects_handoff_and_artifact_contract_tampering(self) -> None:
        cases = []

        missing_handoff = copy.deepcopy(self.bundle)
        missing_handoff["shared_handoffs"].pop()
        cases.append((missing_handoff, "exactly three"))

        wrong_contract = copy.deepcopy(self.bundle)
        wrong_contract["shared_handoffs"][0]["input_contract"] = (
            "top50-route-shard-result/v1"
        )
        cases.append((wrong_contract, "input_contract"))

        misplaced_inputs = copy.deepcopy(self.bundle)
        misplaced_inputs["shared_handoffs"][1]["input_shard_ids"] = []
        cases.append((misplaced_inputs, "only shards-to-merge"))

        wrong_artifact = copy.deepcopy(self.bundle)
        wrong_artifact["artifacts"]["merge_result"] = "wrong.json"
        cases.append((wrong_artifact, "artifacts paths"))

        for tampered, message in cases:
            redigest(tampered)
            with self.subTest(message=message), self.assertRaisesRegex(
                compiler.RouteBundleError, message
            ):
                compiler.validate_route_bundle(tampered)

    def test_rejects_a_forged_bundle_digest(self) -> None:
        tampered = copy.deepcopy(self.bundle)
        tampered["topic"] = "篡改后的主题"

        with self.assertRaisesRegex(compiler.RouteBundleError, "bundle_digest_sha256"):
            compiler.validate_route_bundle(tampered)

        malformed_digest = copy.deepcopy(self.bundle)
        malformed_digest["bundle_digest_sha256"] = "A" * 64
        with self.assertRaisesRegex(compiler.RouteBundleError, "64 lowercase"):
            compiler.validate_route_bundle(malformed_digest)

    def test_compile_fails_if_internal_bundle_construction_breaks_validation(self) -> None:
        original = compiler._shared_handoffs

        def malformed_handoffs(*args: object, **kwargs: object) -> list[dict[str, object]]:
            handoffs = original(*args, **kwargs)
            handoffs[1]["input_artifact"] = "wrong.json"
            return handoffs

        with mock.patch.object(compiler, "_shared_handoffs", malformed_handoffs):
            with self.assertRaisesRegex(compiler.RouteBundleError, "artifact path chain"):
                compiler.compile_route_bundle(scope())


class ContractAndCliTests(unittest.TestCase):
    def test_schema_assets_are_strict_and_version_aligned(self) -> None:
        request_schema = json.loads(
            (SKILL_ROOT / "assets" / "engine-contracts" / "route-bundle-request.schema.json").read_text(
                encoding="utf-8"
            )
        )
        result_schema = json.loads(
            (SKILL_ROOT / "assets" / "engine-contracts" / "route-bundle.schema.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_schema = json.loads(
            (
                SKILL_ROOT
                / "assets"
                / "engine-contracts"
                / "route-shard-result-manifest.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(request_schema["$id"], "top50-route-scope/v1")
        self.assertEqual(result_schema["$id"], "top50-route-bundle/v1")
        self.assertEqual(
            manifest_schema["$id"], "top50-route-shard-result-manifest/v1"
        )
        self.assertFalse(request_schema["additionalProperties"])
        self.assertFalse(request_schema["properties"]["platform_routes"]["items"]["additionalProperties"])
        self.assertFalse(request_schema["$defs"]["publicHttpBinding"]["additionalProperties"])
        self.assertFalse(result_schema["additionalProperties"])
        self.assertFalse(result_schema["$defs"]["queryPlanBinding"]["additionalProperties"])
        self.assertFalse(result_schema["properties"]["shards"]["items"]["additionalProperties"])
        self.assertFalse(result_schema["$defs"]["publicHttpBinding"]["additionalProperties"])
        self.assertFalse(manifest_schema["additionalProperties"])
        self.assertFalse(
            manifest_schema["properties"]["results"]["items"]["additionalProperties"]
        )

        jsonschema.Draft202012Validator.check_schema(request_schema)
        jsonschema.Draft202012Validator.check_schema(result_schema)
        jsonschema.Draft202012Validator.check_schema(manifest_schema)
        payload = scope(
            login_mode="user-assisted",
            platform_routes=[
                {"platform_id": "github", "access_kind": "platform_cli", "required": True},
                {"platform_id": "zhihu", "access_kind": "browser_session", "required": False},
            ],
            public_url_count=50,
            public_urls_authorized=True,
            public_http_binding=public_http_binding(50),
            local_candidate_count=150,
            extraction_complete=True,
        )
        jsonschema.Draft202012Validator(request_schema).validate(payload)
        missing_binding = copy.deepcopy(payload)
        del missing_binding["public_http_binding"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(request_schema).validate(missing_binding)
        ineligible_binding = scope(public_http_binding=public_http_binding(1))
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(request_schema).validate(ineligible_binding)
        result = compiler.compile_route_bundle(payload)
        jsonschema.Draft202012Validator(result_schema).validate(result)
        missing_query_binding = copy.deepcopy(result)
        del missing_query_binding["query_plan_binding"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(
                missing_query_binding
            )
        discovery_without_query_binding = copy.deepcopy(result)
        del shard(discovery_without_query_binding, "platform-cli-discovery")[
            "router_request"
        ]["query_plan_binding"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(
                discovery_without_query_binding
            )
        manifest = {
            "schema": "top50-route-shard-result-manifest/v1",
            "run_id": result["run_id"],
            "route_bundle_digest_sha256": result["bundle_digest_sha256"],
            "status": "complete",
            "results": [
                {
                    "shard_id": result["shared_handoffs"][0]["input_shard_ids"][0],
                    "result_contract": "top50-route-shard-result/v1",
                    "status": "complete",
                    "artifact_path": "route-runs/run-001/results/shard-result.json",
                    "artifact_digest_sha256": "0" * 64,
                    "error_summary": None,
                }
            ],
        }
        jsonschema.Draft202012Validator(manifest_schema).validate(manifest)
        invalid_manifest = copy.deepcopy(manifest)
        invalid_manifest["results"][0]["unexpected"] = True
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(manifest_schema).validate(invalid_manifest)
        inconsistent_manifest_status = copy.deepcopy(manifest)
        inconsistent_manifest_status["results"][0].update(
            {
                "status": "failed",
                "artifact_path": None,
                "artifact_digest_sha256": None,
                "error_summary": "shard failed",
            }
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(manifest_schema).validate(
                inconsistent_manifest_status
            )
        duplicate_manifest_result = copy.deepcopy(manifest)
        duplicate_manifest_result["results"].append(
            copy.deepcopy(duplicate_manifest_result["results"][0])
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(manifest_schema).validate(
                duplicate_manifest_result
            )
        merge_handoff, merge_to_curate, curate_to_rank = result["shared_handoffs"]
        self.assertIn("input_shard_ids", merge_handoff)
        self.assertNotIn("input_shard_ids", merge_to_curate)
        self.assertNotIn("input_shard_ids", curate_to_rank)

        missing_merge_inputs = copy.deepcopy(result)
        del missing_merge_inputs["shared_handoffs"][0]["input_shard_ids"]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(missing_merge_inputs)

        misplaced_merge_inputs = copy.deepcopy(result)
        misplaced_merge_inputs["shared_handoffs"][1]["input_shard_ids"] = [
            "platform-cli-discovery"
        ]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(misplaced_merge_inputs)

        unknown_handoff = copy.deepcopy(result)
        unknown_handoff["shared_handoffs"][1]["handoff_id"] = "unknown-handoff"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(unknown_handoff)

        duplicate_handoffs = copy.deepcopy(result)
        duplicate_handoffs["shared_handoffs"] = [
            copy.deepcopy(result["shared_handoffs"][0]) for _ in range(3)
        ]
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(duplicate_handoffs)

        cyclic_handoff = copy.deepcopy(result)
        cyclic_handoff["shared_handoffs"][1].update(
            {"from_stage": "curate", "to_stage": "merge"}
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(cyclic_handoff)

        wrong_handoff_contract = copy.deepcopy(result)
        wrong_handoff_contract["shared_handoffs"][2]["input_contract"] = (
            "top50-route-merge-result/v1"
        )
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(result_schema).validate(wrong_handoff_contract)
        for row in result["shards"]:
            if row["status"] == "ready_to_plan":
                normalized = router.validate_request(row["router_request"])
                self.assertEqual(
                    {key: normalized[key] for key in row["router_request"]}, row["router_request"]
                )

    def test_cli_writes_deterministic_json_and_fails_without_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "scope.json"
            output_path = root / "bundle.json"
            input_path.write_text(json.dumps(scope(), ensure_ascii=False), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            first = output_path.read_bytes()
            self.assertEqual(json.loads(first), compiler.compile_route_bundle(scope()))

            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--output", str(output_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(output_path.read_bytes(), first)

            invalid_path = root / "invalid.json"
            invalid_output = root / "invalid-output.json"
            invalid_path.write_text(json.dumps(scope(topic="《主题》"), ensure_ascii=False), encoding="utf-8")
            failed = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(invalid_path), "--output", str(invalid_output)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(failed.returncode, 2)
            self.assertIn("topic", failed.stderr)
            self.assertFalse(invalid_output.exists())


if __name__ == "__main__":
    unittest.main()
