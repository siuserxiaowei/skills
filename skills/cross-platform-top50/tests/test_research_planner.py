from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import jsonschema


SKILL_ROOT = Path(__file__).parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "research_planner.py"
SCHEMA = SKILL_ROOT / "assets" / "engine-contracts" / "research-query-plan.schema.json"
SPEC = importlib.util.spec_from_file_location("research_planner", SCRIPT)
assert SPEC and SPEC.loader
planner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = planner
SPEC.loader.exec_module(planner)


def request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": "top50-research-query-request/v1",
        "run_id": "run-query-001",
        "topic": "AI Agent 搜索",
        "purpose": "建立近期工具研究榜单",
        "platforms": [
            {"platform_id": "github", "required": True},
            {"platform_id": "xiaohongshu", "required": True},
        ],
        "aliases": ["智能体搜索"],
        "languages": ["zh", "en"],
        "intents": ["exact", "tutorial", "failure"],
        "timeframe": {"start": "2026-07-25", "end": "2026-08-24"},
        "tokenizer_mode": "cjk_bigram",
    }
    value.update(overrides)
    return value


class QueryPlanTests(unittest.TestCase):
    def test_compiles_platform_specific_search_queries_but_shared_ranking_queries(self) -> None:
        plan = planner.compile_query_plan(request())

        self.assertEqual(plan["schema"], "top50-research-query-plan/v1")
        self.assertEqual(plan["run_id"], "run-query-001")
        self.assertEqual(plan["topic"], "AI Agent 搜索")
        self.assertEqual(plan["date_policy"], "isolate_unknown")
        self.assertEqual(plan["recent_social_mode"], "auto")
        self.assertEqual(
            plan["fusion_time_policy"],
            {
                "mode": "advisory",
                "from_date": "2026-07-25",
                "to_date": "2026-08-24",
            },
        )
        self.assertEqual(plan["counts"], {"platforms": 2, "queries": 12})
        self.assertEqual(len(plan["plan_digest_sha256"]), 64)
        self.assertEqual(len(plan["idempotency_key"]), 64)

        github = next(
            row
            for row in plan["queries"]
            if row["platform_id"] == "github"
            and row["intent"] == "tutorial"
            and row["language"] == "zh"
        )
        xhs = next(
            row
            for row in plan["queries"]
            if row["platform_id"] == "xiaohongshu"
            and row["intent"] == "tutorial"
            and row["language"] == "zh"
        )
        self.assertNotEqual(github["search_query"], xhs["search_query"])
        self.assertIn("site:github.com", github["search_query"])
        self.assertIn("小红书", xhs["search_query"])
        self.assertEqual(github["ranking_query"], xhs["ranking_query"])
        self.assertNotIn("site:", github["ranking_query"])
        self.assertNotIn("github", github["ranking_query"].casefold())
        self.assertEqual(github["status"], "pending")
        self.assertEqual(github["date_filter"], request()["timeframe"])
        self.assertEqual(github["window_timezone"], "UTC")
        self.assertEqual(xhs["window_timezone"], "Asia/Shanghai")
        self.assertEqual(github["ranking_tokenizer"], "cjk_bigram")
        self.assertIn("搜索", github["ranking_tokens"])
        self.assertIn("教程", github["intent_expansion"])
        self.assertEqual(github["platform_expansion"], ["site:github.com"])
        xhs_platform = next(
            row for row in plan["platforms"] if row["platform_id"] == "xiaohongshu"
        )
        github_platform = next(
            row for row in plan["platforms"] if row["platform_id"] == "github"
        )
        self.assertEqual(xhs_platform["window_timezone"], "Asia/Shanghai")
        self.assertEqual(github_platform["window_timezone"], "UTC")
        self.assertEqual(
            [route["route_kind"] for route in xhs_platform["adapter_chain"]],
            ["platform_api", "authorized_browser", "public_discovery"],
        )
        self.assertEqual(
            [route["order"] for route in xhs_platform["adapter_chain"]], [1, 2, 3]
        )
        self.assertTrue(
            all(
                route["status"] == "planned" and route["requires_probe"]
                for route in xhs_platform["adapter_chain"]
            )
        )
        self.assertEqual(
            xhs["route_plan"],
            [route["route_id"] for route in xhs_platform["adapter_chain"]],
        )
        self.assertEqual(xhs["route_plan_status"], "not_started")

    def test_platform_and_input_order_do_not_change_the_plan(self) -> None:
        original = request()
        reordered = request(
            platforms=list(reversed(copy.deepcopy(original["platforms"]))),
            aliases=["智能体搜索", "AI Agent 搜索", "智能体搜索"],
            languages=["en", "zh"],
            intents=["failure", "tutorial", "exact"],
        )

        first = planner.compile_query_plan(original)
        second = planner.compile_query_plan(reordered)

        self.assertEqual(first, second)
        self.assertEqual(
            [row["platform_id"] for row in first["platforms"]],
            ["xiaohongshu", "github"],
        )
        self.assertEqual(len({row["query_id"] for row in first["queries"]}), 12)

    def test_explicit_default_route_kinds_equal_omitted_defaults(self) -> None:
        implicit = planner.compile_query_plan(request())
        explicit_payload = request()
        explicit_payload["platforms"] = [
            {
                **platform,
                "route_kinds": list(
                    planner.DEFAULT_ROUTE_KINDS[str(platform["platform_id"])]
                ),
            }
            for platform in explicit_payload["platforms"]
        ]

        self.assertEqual(implicit, planner.compile_query_plan(explicit_payload))

    def test_platform_timezone_override_is_explicit_and_part_of_query_identity(self) -> None:
        baseline = planner.compile_query_plan(
            request(
                platforms=[{"platform_id": "github", "required": True}],
                languages=["en"],
                intents=["exact"],
            )
        )
        overridden = planner.compile_query_plan(
            request(
                platforms=[
                    {
                        "platform_id": "github",
                        "required": True,
                        "window_timezone": "America/New_York",
                    }
                ],
                languages=["en"],
                intents=["exact"],
            )
        )

        self.assertEqual(
            overridden["platforms"][0]["window_timezone"], "America/New_York"
        )
        self.assertEqual(
            overridden["queries"][0]["window_timezone"], "America/New_York"
        )
        self.assertNotEqual(
            baseline["queries"][0]["query_id"], overridden["queries"][0]["query_id"]
        )

    def test_platform_expansion_covers_native_and_web_index_routes(self) -> None:
        plan = planner.compile_query_plan(
            request(
                platforms=[
                    {"platform_id": "wechat_official_accounts", "required": True},
                    {"platform_id": "bilibili", "required": False},
                    {"platform_id": "linuxdo", "required": False},
                ],
                aliases=[],
                languages=["zh"],
                intents=["exact"],
            )
        )

        by_platform = {row["platform_id"]: row for row in plan["queries"]}
        self.assertIn("site:mp.weixin.qq.com", by_platform["wechat_official_accounts"]["search_query"])
        self.assertIn("公众号", by_platform["wechat_official_accounts"]["search_query"])
        self.assertIn("site:bilibili.com", by_platform["bilibili"]["search_query"])
        self.assertIn("site:linux.do", by_platform["linuxdo"]["search_query"])
        self.assertTrue(by_platform["wechat_official_accounts"]["required"])
        self.assertFalse(by_platform["bilibili"]["required"])

    def test_plan_validates_against_the_shipped_json_schema(self) -> None:
        plan = planner.compile_query_plan(request())
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        jsonschema.Draft202012Validator(schema).validate(plan)

    def test_plan_digest_detects_semantic_tampering(self) -> None:
        plan = planner.compile_query_plan(request())
        plan["queries"][0]["ranking_query"] = "unrelated"

        with self.assertRaisesRegex(planner.QueryPlanError, "digest"):
            planner.validate_query_plan(plan)

    def test_adapter_chain_tampering_fails_even_after_redigest(self) -> None:
        plan = planner.compile_query_plan(request())
        platform = next(
            row for row in plan["platforms"] if row["platform_id"] == "xiaohongshu"
        )
        platform["adapter_chain"][0]["route_kind"] = "public_discovery"
        plan["plan_digest_sha256"] = planner._digest(
            plan, omit=("plan_digest_sha256",)
        )

        with self.assertRaisesRegex(planner.QueryPlanError, "route|deterministic"):
            planner.validate_query_plan(plan)


class TokenizationTests(unittest.TestCase):
    def test_cjk_bigram_tokenizer_handles_mixed_language_text(self) -> None:
        tokens, tokenizer = planner.tokenize_for_ranking(
            "人工智能 Agent 2.0", mode="cjk_bigram"
        )

        self.assertEqual(tokenizer, "cjk_bigram")
        self.assertEqual(tokens, ["人工", "工智", "智能", "agent", "2.0"])

    def test_jieba_mode_falls_back_to_cjk_bigrams_when_dependency_is_absent(self) -> None:
        with mock.patch.object(planner, "_load_jieba", return_value=None):
            tokens, tokenizer = planner.tokenize_for_ranking(
                "人工智能 Agent", mode="jieba"
            )

        self.assertEqual(tokenizer, "cjk_bigram_fallback")
        self.assertEqual(tokens, ["人工", "工智", "智能", "agent"])

    def test_jieba_mode_records_actual_jieba_usage(self) -> None:
        fake_jieba = mock.Mock()
        fake_jieba.lcut.return_value = ["人工智能", " ", "Agent"]

        with mock.patch.object(planner, "_load_jieba", return_value=fake_jieba):
            tokens, tokenizer = planner.tokenize_for_ranking(
                "人工智能 Agent", mode="jieba"
            )

        self.assertEqual(tokenizer, "jieba")
        self.assertEqual(tokens, ["人工智能", "agent"])


class QueryPlanValidationTests(unittest.TestCase):
    def test_recent_social_mode_compiles_to_exact_fusion_time_policy(self) -> None:
        mappings = {
            "auto": "advisory",
            "strict": "strict",
            "off": "unbounded",
        }
        for external_mode, fusion_mode in mappings.items():
            with self.subTest(external_mode=external_mode):
                plan = planner.compile_query_plan(
                    request(recent_social_mode=external_mode)
                )
                self.assertEqual(plan["recent_social_mode"], external_mode)
                self.assertEqual(plan["fusion_time_policy"]["mode"], fusion_mode)
                self.assertEqual(
                    plan["fusion_time_policy"]["from_date"],
                    plan["timeframe"]["start"],
                )
                self.assertEqual(
                    plan["fusion_time_policy"]["to_date"],
                    plan["timeframe"]["end"],
                )

    def test_unknown_recent_social_mode_fails_closed(self) -> None:
        with self.assertRaisesRegex(planner.QueryPlanError, "recent_social_mode"):
            planner.compile_query_plan(request(recent_social_mode="sometimes"))

    def test_rejects_placeholders_unknown_platforms_and_unknown_intents(self) -> None:
        cases = [
            (request(topic="《主题》"), "placeholder"),
            (
                request(platforms=[{"platform_id": "made_up", "required": True}]),
                "platform",
            ),
            (request(intents=["clickbait"]), "intent"),
            (request(languages=[]), "languages"),
        ]

        for payload, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(planner.QueryPlanError, message):
                    planner.compile_query_plan(payload)

    def test_rejects_reversed_timeframe_and_unrecognized_input_fields(self) -> None:
        with self.assertRaisesRegex(planner.QueryPlanError, "timeframe"):
            planner.compile_query_plan(
                request(timeframe={"start": "2026-08-24", "end": "2026-07-25"})
            )
        with self.assertRaisesRegex(planner.QueryPlanError, "unexpected"):
            planner.compile_query_plan(request(cookie="secret"))

    def test_rejects_malformed_request_shape_and_text(self) -> None:
        cases = [
            (None, "JSON object"),
            ({"schema": "wrong"}, "missing"),
            (request(schema="wrong"), "schema"),
            (request(run_id="../unsafe"), "run_id"),
            (request(purpose=" "), "purpose"),
            (request(topic="bad\ncontrol"), "control"),
            (request(timeframe={"start": "bad", "end": "2026-08-24"}), "YYYY-MM-DD"),
            (request(tokenizer_mode="unknown"), "tokenizer_mode"),
            (request(max_queries=True), "max_queries"),
        ]
        for payload, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(planner.QueryPlanError, message):
                    planner.compile_query_plan(payload)

    def test_rejects_malformed_platform_declarations(self) -> None:
        cases = [
            ([], "non-empty"),
            ([{"platform_id": "github"}], "fields"),
            ([{"platform_id": "github", "required": "yes"}], "boolean"),
            ([{"platform_id": "github", "required": True, "route_kinds": []}], "route_kinds"),
            (
                [
                    {
                        "platform_id": "github",
                        "required": True,
                        "window_timezone": "Mars/Olympus",
                    }
                ],
                "window_timezone",
            ),
        ]
        for platforms, message in cases:
            with self.subTest(platforms=platforms):
                with self.assertRaisesRegex(planner.QueryPlanError, message):
                    planner.compile_query_plan(request(platforms=platforms))

    def test_rejects_malformed_plan_even_if_digest_is_recomputed(self) -> None:
        plan = planner.compile_query_plan(request())
        plan["schema"] = "wrong"
        plan["plan_digest_sha256"] = planner._digest(
            plan, omit=("plan_digest_sha256",)
        )
        with self.assertRaisesRegex(planner.QueryPlanError, "schema"):
            planner.validate_query_plan(plan)

        with self.assertRaisesRegex(planner.QueryPlanError, "JSON object"):
            planner.validate_query_plan(None)

    def test_alias_and_query_limits_are_bounded(self) -> None:
        with self.assertRaisesRegex(planner.QueryPlanError, "aliases"):
            planner.compile_query_plan(request(aliases=[f"alias-{index}" for index in range(21)]))
        with self.assertRaisesRegex(planner.QueryPlanError, "query count"):
            planner.compile_query_plan(
                request(
                    platforms=[
                        {"platform_id": platform, "required": False}
                        for platform in planner.CANONICAL_PLATFORMS
                    ],
                    languages=["zh", "en"],
                    intents=list(planner.INTENT_ORDER),
                    max_queries=10,
                )
            )

    def test_rejects_unknown_duplicate_or_reversed_route_kinds(self) -> None:
        route_cases = [
            ["platform_api", "unknown_route"],
            ["platform_api", "platform_api", "public_discovery"],
            ["public_discovery", "authorized_browser"],
        ]
        for route_kinds in route_cases:
            with self.subTest(route_kinds=route_kinds):
                with self.assertRaisesRegex(planner.QueryPlanError, "route"):
                    planner.compile_query_plan(
                        request(
                            platforms=[
                                {
                                    "platform_id": "xiaohongshu",
                                    "required": True,
                                    "route_kinds": route_kinds,
                                }
                            ]
                        )
                    )

    def test_conflicting_duplicate_platform_declarations_fail_closed(self) -> None:
        with self.assertRaisesRegex(planner.QueryPlanError, "conflicting"):
            planner.compile_query_plan(
                request(
                    platforms=[
                        {
                            "platform_id": "xiaohongshu",
                            "required": True,
                            "route_kinds": ["platform_api", "public_discovery"],
                        },
                        {
                            "platform_id": "xiaohongshu",
                            "required": True,
                            "route_kinds": ["authorized_browser", "public_discovery"],
                        },
                    ]
                )
            )

    def test_custom_adapter_chain_is_only_a_planned_probe_order(self) -> None:
        plan = planner.compile_query_plan(
            request(
                platforms=[
                    {
                        "platform_id": "wechat_official_accounts",
                        "required": True,
                        "route_kinds": ["authorized_browser", "public_discovery"],
                    }
                ],
                languages=["zh"],
                intents=["exact"],
            )
        )

        chain = plan["platforms"][0]["adapter_chain"]
        self.assertEqual(
            [route["activation"] for route in chain],
            ["probe_then_execute", "fallback_after_recorded_outcome"],
        )
        self.assertTrue(all(route["status"] == "planned" for route in chain))
        self.assertEqual(plan["queries"][0]["route_plan_status"], "not_started")

    def test_cli_writes_valid_plan_and_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "request.json"
            output_path = root / "plan.json"
            input_path.write_text(json.dumps(request(), ensure_ascii=False), encoding="utf-8")

            first = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compile",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            second = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compile",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)
            planner.validate_query_plan(json.loads(output_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
