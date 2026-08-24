from __future__ import annotations

import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "hengzong_contract.py"
SPEC = importlib.util.spec_from_file_location("hengzong_contract", SCRIPT)
assert SPEC and SPEC.loader
hengzong = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hengzong
SPEC.loader.exec_module(hengzong)


def request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": "top50-hengzong-request/v1",
        "run_id": "run-hz-001",
        "brief_date": "2026-08-24",
        "as_of": "2026-08-24T12:00:00Z",
        "goal": {
            "type": "opportunity",
            "objective": "判断 AI 搜索工具未来三年的行业机会",
            "audience": "产品与投资决策者",
            "decision": "选择优先进入的行业",
        },
        "scope": {
            "start_date": "2026-07-25",
            "end_date": "2026-08-24",
            "geographies": ["CN", "US"],
            "languages": ["zh-CN", "en"],
        },
        "query_bounds": {
            "max_geo_language_cells": 4,
            "max_queries_per_group": 3,
            "max_total_queries": 12,
        },
        "producer": {
            "engine_id": "python-control-plane",
            "engine_version": "0.2.0",
            "worker_ids": ["worker-research-01"],
        },
    }
    value.update(overrides)
    return value


def refresh_digest(value: dict[str, object]) -> None:
    value["result_digest_sha256"] = hengzong.artifact_digest(value)


def make_brief(plan: dict[str, object]) -> dict[str, object]:
    as_of = plan["as_of"]
    workstreams = plan["canonical_workstreams"]
    claims = [
        {
            "claim_id": "claim-past",
            "text": "一次关键的开放协议发布降低了行业接入门槛。",
            "temporal_role": "past_event",
            "event_date": "2026-07-10",
            "as_of": as_of,
            "pre_scope_context": True,
            "scope": "公开协议及其直接生态",
            "evidence_links": [
                {
                    "source_id": "source-primary",
                    "stance": "support",
                    "locator": "release notes, section 2",
                    "evidence_date": "2026-07-11",
                    "scope": "协议发布内容",
                },
                {
                    "source_id": "source-review",
                    "stance": "support",
                    "locator": "paragraphs 4-6",
                    "evidence_date": "2026-07-14",
                    "scope": "独立复核的兼容性测试",
                },
            ],
        },
        {
            "claim_id": "claim-present",
            "text": "当前采用速度主要受数据授权和中文检索质量约束。",
            "temporal_role": "present_effect",
            "event_date": "2026-08-18",
            "as_of": as_of,
            "pre_scope_context": False,
            "scope": "中国与美国的公开搜索产品",
            "evidence_links": [
                {
                    "source_id": "source-review",
                    "stance": "support",
                    "locator": "benchmark table 3",
                    "evidence_date": "2026-08-19",
                    "scope": "中英文检索质量",
                },
                {
                    "source_id": "source-challenge",
                    "stance": "refute",
                    "locator": "results, rows 12-18",
                    "evidence_date": "2026-08-20",
                    "scope": "无需授权的公开数据子集",
                },
            ],
        },
        {
            "claim_id": "claim-future",
            "text": "可审计的行业专用检索层可能形成新的付费价值。",
            "temporal_role": "implication",
            "event_date": None,
            "as_of": as_of,
            "pre_scope_context": False,
            "scope": "未来三年的企业研究工作流",
            "evidence_links": [
                {
                    "source_id": "source-review",
                    "stance": "support",
                    "locator": "discussion, paragraphs 8-10",
                    "evidence_date": "2026-08-21",
                    "scope": "采购意愿与审计需求",
                }
            ],
        },
    ]
    brief: dict[str, object] = {
        "contract_version": "top50-hengzong-brief/v1",
        "run_id": plan["run_id"],
        "stage": "hengzong_synthesis",
        "status": "ready_for_curator",
        "brief_date": plan["brief_date"],
        "as_of": as_of,
        "goal": copy.deepcopy(plan["goal"]),
        "scope": copy.deepcopy(plan["scope"]),
        "producer": {
            "engine_id": "python-control-plane",
            "engine_version": "0.2.0",
            "worker_ids": ["worker-research-01"],
        },
        "plan_binding": {
            "contract_version": plan["contract_version"],
            "plan_id": plan["plan_id"],
            "result_digest_sha256": plan["result_digest_sha256"],
        },
        "workstream_results": [
            {
                "workstream_id": row["workstream_id"],
                "status": "complete",
                "finding": f"已完成 {row['workstream_id']} 的研究。",
                "claim_ids": [claims[index % len(claims)]["claim_id"]],
            }
            for index, row in enumerate(workstreams)
        ],
        "sources": [
            {
                "source_id": "source-primary",
                "url": "https://example.com/release",
                "title": "Protocol release",
                "publisher": "Protocol maintainer",
                "independence_group": "protocol-maintainer",
                "published_at": "2026-07-11T08:00:00Z",
                "as_of": as_of,
                "pre_scope_context": True,
            },
            {
                "source_id": "source-review",
                "url": "https://review.example.org/benchmark",
                "title": "Independent benchmark",
                "publisher": "Research lab",
                "independence_group": "research-lab",
                "published_at": "2026-08-19T08:00:00Z",
                "as_of": as_of,
                "pre_scope_context": False,
            },
            {
                "source_id": "source-challenge",
                "url": "https://challenge.example.net/results",
                "title": "Counter-test",
                "publisher": "Independent tester",
                "independence_group": "independent-tester",
                "published_at": "2026-08-20T08:00:00Z",
                "as_of": as_of,
                "pre_scope_context": False,
            },
        ],
        "claims": claims,
        "causal_chains": [
            {
                "chain_id": "chain-001",
                "past_event_claim_id": "claim-past",
                "present_effect_claim_id": "claim-present",
                "implication_claim_id": "claim-future",
                "mechanism": "开放接口扩大供给，同时把竞争焦点推向授权与质量。",
                "caveat": "链条表示有证据约束的解释，不表示唯一因果。",
            }
        ],
        "scenarios": [
            {
                "scenario_id": "constrained",
                "summary": "授权收紧使行业采用保持局部化。",
                "triggers": [
                    {
                        "signal": "两类关键数据源停止公开访问",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-present"],
                    }
                ],
                "invalidators": [
                    {
                        "signal": "形成可执行的跨平台授权标准",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-future"],
                    }
                ],
            },
            {
                "scenario_id": "continuity",
                "summary": "采用稳步增长但保持多后端共存。",
                "triggers": [
                    {
                        "signal": "企业采购连续两个季度增长",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-future"],
                    }
                ],
                "invalidators": [
                    {
                        "signal": "部署后留存率连续两个季度下降",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-present"],
                    }
                ],
            },
            {
                "scenario_id": "acceleration",
                "summary": "标准化和高质量中文检索推动跨行业扩张。",
                "triggers": [
                    {
                        "signal": "中文基准达到约定质量门槛",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-present", "claim-future"],
                    }
                ],
                "invalidators": [
                    {
                        "signal": "行业采购仍只集中在试点预算",
                        "check_by": "2027-06-30",
                        "claim_ids": ["claim-future"],
                    }
                ],
            },
        ],
        "opportunity_map": [
            {
                "opportunity_id": "opp-compliance-research",
                "industry": "受监管企业研究",
                "horizon": "1-3y",
                "unmet_need": "需要可复核来源和授权边界的研究结果",
                "enabling_change": "可审计证据账本与多后端检索成熟",
                "offer": "行业专用的检索、证据与复核控制面",
                "beneficiaries": ["合规团队", "研究团队"],
                "constraints": ["平台授权", "数据驻留"],
                "leading_indicators": ["付费试点数", "复核通过率"],
                "claim_ids": ["claim-present", "claim-future"],
            }
        ],
        "retained_gaps": [
            {
                "gap_id": "gap-private-adoption",
                "statement": "无法确认非公开部署的真实采用规模。",
                "status": "retained",
                "attempts": [
                    {
                        "attempt_id": "attempt-native",
                        "query": "行业 AI 搜索 私有化 部署 采用率",
                        "query_path": "platform_native",
                        "route": "authorized-platform-search",
                        "executed_at": "2026-08-23T09:00:00Z",
                        "outcome": "insufficient_independence",
                    },
                    {
                        "attempt_id": "attempt-primary",
                        "query": "enterprise AI search private deployment adoption filing",
                        "query_path": "primary_source_registry",
                        "route": "public-web-index",
                        "executed_at": "2026-08-23T10:00:00Z",
                        "outcome": "no_eligible_evidence",
                    },
                ],
            }
        ],
        "blocking_reasons": [],
    }
    refresh_digest(brief)
    return brief


def write_json(path: Path, value: dict[str, object]) -> str:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PlanContractTests(unittest.TestCase):
    def test_builds_dated_goal_sensitive_hv_plan_with_bounded_geo_language_cells(
        self,
    ) -> None:
        plan = hengzong.build_plan(request())

        self.assertEqual(plan["brief_date"], "2026-08-24")
        self.assertEqual(plan["as_of"], "2026-08-24T12:00:00Z")
        self.assertEqual(
            {row["axis"] for row in plan["canonical_workstreams"]},
            {"horizontal", "vertical"},
        )
        self.assertTrue(
            all(
                "AI 搜索工具" in row["question"]
                for row in plan["canonical_workstreams"]
            )
        )
        cells = {
            (row["geography"], row["language"])
            for row in plan["query_groups"]
        }
        self.assertEqual(
            cells,
            {("CN", "zh-CN"), ("CN", "en"), ("US", "zh-CN"), ("US", "en")},
        )
        self.assertTrue(
            all(len(row["queries"]) <= 3 for row in plan["query_groups"])
        )
        self.assertLessEqual(plan["counts"]["total_queries"], 12)
        self.assertEqual(hengzong.validate_plan(plan)["status"], "complete")

        decision_request = request()
        decision_request["goal"] = {
            "type": "decision",
            "objective": "选择是否建设自有搜索基础设施",
            "audience": "技术委员会",
            "decision": "批准或否决建设预算",
        }
        decision_plan = hengzong.build_plan(decision_request)
        self.assertNotEqual(
            [row["workstream_id"] for row in plan["canonical_workstreams"]],
            [
                row["workstream_id"]
                for row in decision_plan["canonical_workstreams"]
            ],
        )

    def test_rejects_geo_language_cross_product_over_declared_or_hard_bound(self) -> None:
        too_small = request()
        too_small["query_bounds"] = {
            "max_geo_language_cells": 3,
            "max_queries_per_group": 3,
            "max_total_queries": 12,
        }
        with self.assertRaisesRegex(hengzong.BlockingError, "geo.*language"):
            hengzong.build_plan(too_small)

        too_large = request()
        too_large["scope"] = {
            "start_date": "2026-07-25",
            "end_date": "2026-08-24",
            "geographies": [f"G{index}" for index in range(9)],
            "languages": [f"l{index}" for index in range(3)],
        }
        too_large["query_bounds"] = {
            "max_geo_language_cells": 27,
            "max_queries_per_group": 3,
            "max_total_queries": 81,
        }
        with self.assertRaisesRegex(hengzong.BlockingError, "hard limit"):
            hengzong.build_plan(too_large)

    def test_deleting_canonical_workstream_still_fails_after_recomputed_hashes(
        self,
    ) -> None:
        plan = hengzong.build_plan(request())
        plan["canonical_workstreams"] = plan["canonical_workstreams"][:-1]
        missing_id = "V3-future-value-paths"
        for group in plan["query_groups"]:
            for query in group["queries"]:
                query["workstream_ids"] = [
                    item for item in query["workstream_ids"] if item != missing_id
                ]
        plan["counts"]["workstreams"] -= 1
        plan["plan_id"] = hengzong.plan_id_for(plan)
        refresh_digest(plan)

        with self.assertRaisesRegex(
            hengzong.ContractError, "canonical workstreams"
        ):
            hengzong.validate_plan(plan)


class RequestAndPlanFailureTests(unittest.TestCase):
    def assert_request_rejected(
        self, value: object, message: str
    ) -> None:
        with self.subTest(message=message):
            with self.assertRaisesRegex(hengzong.ContractError, message):
                hengzong.build_plan(value)

    def test_rejects_malformed_request_identity_fields_and_dates(self) -> None:
        self.assert_request_rejected([], "request must be an object")

        missing = request()
        del missing["run_id"]
        self.assert_request_rejected(missing, "missing run_id")

        extra = request(extra=True)
        self.assert_request_rejected(extra, "unexpected extra")

        wrong_contract = request(contract_version="wrong")
        self.assert_request_rejected(wrong_contract, "contract_version")

        blank_run = request(run_id=" \x00")
        self.assert_request_rejected(blank_run, "run_id")

        for field, value, message in (
            ("brief_date", "", "ISO date"),
            ("brief_date", "2026-02-30", "ISO date"),
            ("as_of", "", "ISO timestamp"),
            ("as_of", "not-a-timestamp", "ISO timestamp"),
            ("as_of", "2026-08-24T12:00:00", "timezone"),
            ("brief_date", "2026-08-23", "UTC date"),
        ):
            mutated = request(**{field: value})
            self.assert_request_rejected(mutated, message)

    def test_rejects_invalid_goal_scope_bounds_and_producer(self) -> None:
        cases: list[tuple[dict[str, object], str]] = []

        cases.append((request(goal=[]), "goal must be an object"))
        bad_goal = copy.deepcopy(request()["goal"])
        bad_goal["type"] = "prediction"
        cases.append((request(goal=bad_goal), "goal.type"))
        bad_goal = copy.deepcopy(request()["goal"])
        bad_goal["objective"] = "  "
        cases.append((request(goal=bad_goal), "goal.objective"))

        cases.append((request(scope=[]), "scope must be an object"))
        reversed_scope = copy.deepcopy(request()["scope"])
        reversed_scope["start_date"] = "2026-08-25"
        cases.append((request(scope=reversed_scope), "start_date"))
        future_scope = copy.deepcopy(request()["scope"])
        future_scope["end_date"] = "2026-08-25"
        cases.append((request(scope=future_scope), "after as_of"))
        empty_geo = copy.deepcopy(request()["scope"])
        empty_geo["geographies"] = []
        cases.append((request(scope=empty_geo), "must not be empty"))
        duplicate_language = copy.deepcopy(request()["scope"])
        duplicate_language["languages"] = ["zh-CN", "zh-CN"]
        cases.append((request(scope=duplicate_language), "must be unique"))
        bad_language = copy.deepcopy(request()["scope"])
        bad_language["languages"] = [1]
        cases.append((request(scope=bad_language), "non-empty strings"))

        cases.append((request(query_bounds=[]), "query_bounds must be an object"))
        boolean_bound = copy.deepcopy(request()["query_bounds"])
        boolean_bound["max_total_queries"] = True
        cases.append((request(query_bounds=boolean_bound), "must be an integer"))
        zero_bound = copy.deepcopy(request()["query_bounds"])
        zero_bound["max_total_queries"] = 0
        cases.append((request(query_bounds=zero_bound), ">= 1"))

        cases.append((request(producer=[]), "producer must be an object"))
        blank_engine = copy.deepcopy(request()["producer"])
        blank_engine["engine_id"] = ""
        cases.append((request(producer=blank_engine), "producer.engine_id"))
        empty_workers = copy.deepcopy(request()["producer"])
        empty_workers["worker_ids"] = []
        cases.append((request(producer=empty_workers), "must not be empty"))

        for value, message in cases:
            self.assert_request_rejected(value, message)

    def test_covers_all_goal_specific_workstreams_and_query_budget_failures(self) -> None:
        expected = {
            "opportunity": "V3-future-value-paths",
            "decision": "V3-decision-and-reversal-tests",
            "landscape": "V3-structure-and-transition-paths",
            "diagnosis": "V3-remedies-and-disconfirmation",
        }
        for goal_type, workstream_id in expected.items():
            value = request()
            value["goal"] = {
                "type": goal_type,
                "objective": "评估 AI 搜索工具",
                "audience": "决策团队",
                "decision": "选择行动路径",
            }
            plan = hengzong.build_plan(value)
            self.assertEqual(
                plan["canonical_workstreams"][-1]["workstream_id"], workstream_id
            )

        per_group = request()
        per_group["query_bounds"] = {
            "max_geo_language_cells": 4,
            "max_queries_per_group": hengzong.HARD_MAX_QUERIES_PER_GROUP + 1,
            "max_total_queries": 12,
        }
        with self.assertRaisesRegex(hengzong.BlockingError, "max_queries_per_group"):
            hengzong.build_plan(per_group)

        total_hard = request()
        total_hard["query_bounds"] = {
            "max_geo_language_cells": 4,
            "max_queries_per_group": 3,
            "max_total_queries": hengzong.HARD_MAX_TOTAL_QUERIES + 1,
        }
        with self.assertRaisesRegex(hengzong.BlockingError, "max_total_queries"):
            hengzong.build_plan(total_hard)

        insufficient = request()
        insufficient["query_bounds"] = {
            "max_geo_language_cells": 4,
            "max_queries_per_group": 3,
            "max_total_queries": 3,
        }
        with self.assertRaisesRegex(hengzong.BlockingError, "one query"):
            hengzong.build_plan(insufficient)

    def test_plan_validation_rejects_semantic_and_digest_drift(self) -> None:
        mutations = []

        wrong_contract = hengzong.build_plan(request())
        wrong_contract["contract_version"] = "wrong"
        mutations.append((wrong_contract, "contract_version"))

        wrong_stage = hengzong.build_plan(request())
        wrong_stage["stage"] = "discovery"
        mutations.append((wrong_stage, "stage=hengzong_plan"))

        wrong_queries = hengzong.build_plan(request())
        wrong_queries["query_groups"][0]["queries"][0]["query"] = "替换查询"
        wrong_queries["plan_id"] = hengzong.plan_id_for(wrong_queries)
        refresh_digest(wrong_queries)
        mutations.append((wrong_queries, "query_groups"))

        wrong_counts = hengzong.build_plan(request())
        wrong_counts["counts"]["total_queries"] += 1
        wrong_counts["plan_id"] = hengzong.plan_id_for(wrong_counts)
        refresh_digest(wrong_counts)
        mutations.append((wrong_counts, "counts"))

        wrong_id = hengzong.build_plan(request())
        wrong_id["plan_id"] = "hzplan-" + "0" * 24
        refresh_digest(wrong_id)
        mutations.append((wrong_id, "plan_id"))

        wrong_digest = hengzong.build_plan(request())
        wrong_digest["result_digest_sha256"] = "0" * 64
        mutations.append((wrong_digest, "result digest"))

        with self.assertRaisesRegex(hengzong.ContractError, "plan must be an object"):
            hengzong.validate_plan([])
        for value, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(hengzong.ContractError, message):
                    hengzong.validate_plan(value)


class BriefContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = hengzong.build_plan(request())
        self.brief = make_brief(self.plan)

    def acceptance(self, artifact_sha256: str = "a" * 64) -> dict[str, object]:
        return hengzong.build_curator_acceptance(
            self.brief,
            brief_artifact_sha256=artifact_sha256,
            curator_id="curator-independent-01",
            reviewed_workstream_ids=[
                row["workstream_id"] for row in self.plan["canonical_workstreams"]
            ],
            accepted_claim_ids=[row["claim_id"] for row in self.brief["claims"]],
        )

    def test_validates_claim_source_temporal_chain_scenarios_and_opportunity_map(
        self,
    ) -> None:
        acceptance = self.acceptance()
        result = hengzong.validate_brief(
            self.brief,
            self.plan,
            acceptance=acceptance,
            brief_artifact_sha256="a" * 64,
        )

        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["counts"]["scenarios"], 3)
        self.assertEqual(result["counts"]["causal_chains"], 1)
        self.assertEqual(result["counts"]["opportunities"], 1)
        self.assertEqual(result["counts"]["independence_groups"], 3)

    def test_rejects_temporal_label_or_locator_drift(self) -> None:
        wrong_context = copy.deepcopy(self.brief)
        wrong_context["sources"][0]["pre_scope_context"] = False
        refresh_digest(wrong_context)
        with self.assertRaisesRegex(hengzong.ContractError, "pre_scope_context"):
            hengzong.validate_brief_structure(wrong_context, self.plan)

        missing_locator = copy.deepcopy(self.brief)
        del missing_locator["claims"][0]["evidence_links"][0]["locator"]
        refresh_digest(missing_locator)
        with self.assertRaisesRegex(hengzong.ContractError, "locator"):
            hengzong.validate_brief_structure(missing_locator, self.plan)

    def test_rejects_broken_causal_role_and_incomplete_scenario_set(self) -> None:
        broken_chain = copy.deepcopy(self.brief)
        broken_chain["causal_chains"][0]["past_event_claim_id"] = "claim-present"
        refresh_digest(broken_chain)
        with self.assertRaisesRegex(hengzong.ContractError, "past_event"):
            hengzong.validate_brief_structure(broken_chain, self.plan)

        missing_scenario = copy.deepcopy(self.brief)
        missing_scenario["scenarios"] = missing_scenario["scenarios"][:-1]
        refresh_digest(missing_scenario)
        with self.assertRaisesRegex(hengzong.ContractError, "three canonical"):
            hengzong.validate_brief_structure(missing_scenario, self.plan)

    def test_retained_gap_requires_two_distinct_queries_paths_and_routes(self) -> None:
        for field in ("query", "query_path", "route"):
            with self.subTest(field=field):
                mutated = copy.deepcopy(self.brief)
                attempts = mutated["retained_gaps"][0]["attempts"]
                attempts[1][field] = attempts[0][field]
                refresh_digest(mutated)
                with self.assertRaisesRegex(hengzong.ContractError, field):
                    hengzong.validate_brief_structure(mutated, self.plan)

        one_attempt = copy.deepcopy(self.brief)
        one_attempt["retained_gaps"][0]["attempts"] = one_attempt[
            "retained_gaps"
        ][0]["attempts"][:1]
        refresh_digest(one_attempt)
        with self.assertRaisesRegex(hengzong.ContractError, "at least two"):
            hengzong.validate_brief_structure(one_attempt, self.plan)

    def test_self_reported_verified_or_non_independent_curator_fails(self) -> None:
        self_report = copy.deepcopy(self.brief)
        self_report["status"] = "verified"
        refresh_digest(self_report)
        with self.assertRaisesRegex(hengzong.ContractError, "cannot self-verify"):
            hengzong.validate_brief_structure(self_report, self.plan)

        with self.assertRaisesRegex(
            hengzong.BlockingError, "independent curator acceptance"
        ):
            hengzong.validate_brief(self.brief, self.plan)

        acceptance = hengzong.build_curator_acceptance(
            self.brief,
            brief_artifact_sha256="a" * 64,
            curator_id="worker-research-01",
            reviewed_workstream_ids=[
                row["workstream_id"] for row in self.plan["canonical_workstreams"]
            ],
            accepted_claim_ids=[row["claim_id"] for row in self.brief["claims"]],
        )
        with self.assertRaisesRegex(hengzong.ContractError, "independent"):
            hengzong.validate_brief(
                self.brief,
                self.plan,
                acceptance=acceptance,
                brief_artifact_sha256="a" * 64,
            )

    def test_acceptance_binds_exact_brief_and_full_review_sets(self) -> None:
        acceptance = self.acceptance()
        acceptance["brief_binding"]["artifact_sha256"] = "b" * 64
        refresh_digest(acceptance)
        with self.assertRaisesRegex(hengzong.ContractError, "artifact"):
            hengzong.validate_brief(
                self.brief,
                self.plan,
                acceptance=acceptance,
                brief_artifact_sha256="a" * 64,
            )

    def assert_brief_rejected(
        self, value: dict[str, object], message: str
    ) -> None:
        refresh_digest(value)
        with self.assertRaisesRegex(hengzong.ContractError, message):
            hengzong.validate_brief_structure(value, self.plan)

    def test_rejects_brief_identity_binding_and_source_failures(self) -> None:
        cases: list[tuple[dict[str, object], str]] = []

        wrong_contract = copy.deepcopy(self.brief)
        wrong_contract["contract_version"] = "wrong"
        cases.append((wrong_contract, "contract_version"))
        wrong_stage = copy.deepcopy(self.brief)
        wrong_stage["stage"] = "research"
        cases.append((wrong_stage, "brief.stage"))
        wrong_status = copy.deepcopy(self.brief)
        wrong_status["status"] = "complete"
        cases.append((wrong_status, "brief.status"))
        unexpected_block = copy.deepcopy(self.brief)
        unexpected_block["blocking_reasons"] = [
            {"code": "not-blocking", "message": "不应出现在 ready 状态"}
        ]
        cases.append((unexpected_block, "no blocking_reasons"))
        wrong_run = copy.deepcopy(self.brief)
        wrong_run["run_id"] = "other-run"
        cases.append((wrong_run, "brief.run_id"))
        wrong_binding = copy.deepcopy(self.brief)
        wrong_binding["plan_binding"]["plan_id"] = "hzplan-" + "0" * 24
        cases.append((wrong_binding, "plan_binding"))

        credential_url = copy.deepcopy(self.brief)
        credential_url["sources"][0]["url"] = "https://user:secret@example.com/release"
        cases.append((credential_url, "credentials"))
        invalid_url = copy.deepcopy(self.brief)
        invalid_url["sources"][0]["url"] = "ftp://example.com/release"
        cases.append((invalid_url, "http\\(s\\) URL"))
        blank_title = copy.deepcopy(self.brief)
        blank_title["sources"][0]["title"] = ""
        cases.append((blank_title, "title"))
        wrong_as_of = copy.deepcopy(self.brief)
        wrong_as_of["sources"][0]["as_of"] = "2026-08-23T12:00:00Z"
        cases.append((wrong_as_of, "as_of must match"))
        future_source = copy.deepcopy(self.brief)
        future_source["sources"][0]["published_at"] = "2026-08-25T00:00:00Z"
        cases.append((future_source, "published_at must not be after"))
        duplicate_source = copy.deepcopy(self.brief)
        duplicate_source["sources"][1]["source_id"] = "source-primary"
        cases.append((duplicate_source, "values must be unique"))

        for value, message in cases:
            with self.subTest(message=message):
                self.assert_brief_rejected(value, message)

        bad_digest = copy.deepcopy(self.brief)
        bad_digest["result_digest_sha256"] = "0" * 64
        with self.assertRaisesRegex(hengzong.ContractError, "result digest"):
            hengzong.validate_brief_structure(bad_digest, self.plan)

    def test_rejects_claim_ledger_semantic_failures(self) -> None:
        cases: list[tuple[dict[str, object], str]] = []

        blank_text = copy.deepcopy(self.brief)
        blank_text["claims"][0]["text"] = ""
        cases.append((blank_text, "text"))
        bad_role = copy.deepcopy(self.brief)
        bad_role["claims"][0]["temporal_role"] = "forecast"
        cases.append((bad_role, "temporal_role"))
        wrong_as_of = copy.deepcopy(self.brief)
        wrong_as_of["claims"][0]["as_of"] = "2026-08-23T12:00:00Z"
        cases.append((wrong_as_of, "as_of must match"))
        missing_event = copy.deepcopy(self.brief)
        missing_event["claims"][0]["event_date"] = None
        cases.append((missing_event, "event_date is required"))
        future_event = copy.deepcopy(self.brief)
        future_event["claims"][1]["event_date"] = "2026-08-25"
        cases.append((future_event, "event_date must not be after"))
        wrong_context = copy.deepcopy(self.brief)
        wrong_context["claims"][1]["pre_scope_context"] = True
        cases.append((wrong_context, "pre_scope_context"))
        unknown_source = copy.deepcopy(self.brief)
        unknown_source["claims"][0]["evidence_links"][0]["source_id"] = "missing"
        cases.append((unknown_source, "not present in sources"))
        bad_stance = copy.deepcopy(self.brief)
        bad_stance["claims"][0]["evidence_links"][0]["stance"] = "neutral"
        cases.append((bad_stance, "support or refute"))
        blank_scope = copy.deepcopy(self.brief)
        blank_scope["claims"][0]["evidence_links"][0]["scope"] = ""
        cases.append((blank_scope, "scope"))
        future_evidence = copy.deepcopy(self.brief)
        future_evidence["claims"][0]["evidence_links"][0]["evidence_date"] = "2026-08-25"
        cases.append((future_evidence, "evidence_date must not be after"))

        no_support = copy.deepcopy(self.brief)
        for link in no_support["claims"][0]["evidence_links"]:
            link["stance"] = "refute"
        cases.append((no_support, "supporting source"))

        one_group = copy.deepcopy(self.brief)
        one_group["claims"][0]["evidence_links"] = one_group["claims"][0][
            "evidence_links"
        ][:1]
        cases.append((one_group, "two independent"))

        missing_role = copy.deepcopy(self.brief)
        missing_role["claims"][2]["temporal_role"] = "present_effect"
        missing_role["claims"][2]["event_date"] = "2026-08-21"
        missing_role["claims"][2]["evidence_links"].append(
            {
                "source_id": "source-challenge",
                "stance": "support",
                "locator": "results, rows 12-18",
                "evidence_date": "2026-08-20",
                "scope": "独立测试结果",
            }
        )
        cases.append((missing_role, "must cover"))

        no_refute = copy.deepcopy(self.brief)
        no_refute["claims"][1]["evidence_links"][1]["stance"] = "support"
        cases.append((no_refute, "retain at least one refute"))

        for value, message in cases:
            with self.subTest(message=message):
                self.assert_brief_rejected(value, message)

    def test_rejects_workstream_chain_scenario_and_opportunity_failures(self) -> None:
        cases: list[tuple[dict[str, object], str]] = []

        missing_workstream = copy.deepcopy(self.brief)
        missing_workstream["workstream_results"] = missing_workstream[
            "workstream_results"
        ][:-1]
        cases.append((missing_workstream, "every canonical workstream"))
        incomplete_workstream = copy.deepcopy(self.brief)
        incomplete_workstream["workstream_results"][0]["status"] = "partial"
        cases.append((incomplete_workstream, "status must be complete"))
        blank_finding = copy.deepcopy(self.brief)
        blank_finding["workstream_results"][0]["finding"] = ""
        cases.append((blank_finding, "finding"))
        unknown_claim = copy.deepcopy(self.brief)
        unknown_claim["workstream_results"][0]["claim_ids"] = ["claim-missing"]
        cases.append((unknown_claim, "unknown claim"))
        unassigned_claim = copy.deepcopy(self.brief)
        for row in unassigned_claim["workstream_results"]:
            row["claim_ids"] = [
                claim for claim in row["claim_ids"] if claim != "claim-future"
            ] or ["claim-past"]
        cases.append((unassigned_claim, "every claim"))

        blank_mechanism = copy.deepcopy(self.brief)
        blank_mechanism["causal_chains"][0]["mechanism"] = ""
        cases.append((blank_mechanism, "mechanism"))
        unknown_chain_claim = copy.deepcopy(self.brief)
        unknown_chain_claim["causal_chains"][0]["implication_claim_id"] = "missing"
        cases.append((unknown_chain_claim, "unknown claim"))

        blank_scenario = copy.deepcopy(self.brief)
        blank_scenario["scenarios"][0]["summary"] = ""
        cases.append((blank_scenario, "summary"))
        blank_signal = copy.deepcopy(self.brief)
        blank_signal["scenarios"][0]["triggers"][0]["signal"] = ""
        cases.append((blank_signal, "signal"))
        stale_check = copy.deepcopy(self.brief)
        stale_check["scenarios"][0]["triggers"][0]["check_by"] = "2026-08-23"
        cases.append((stale_check, "must not predate"))
        unknown_scenario_claim = copy.deepcopy(self.brief)
        unknown_scenario_claim["scenarios"][0]["triggers"][0]["claim_ids"] = [
            "missing"
        ]
        cases.append((unknown_scenario_claim, "unknown claim"))

        no_opportunity = copy.deepcopy(self.brief)
        no_opportunity["opportunity_map"] = []
        cases.append((no_opportunity, "must not be empty"))
        blank_industry = copy.deepcopy(self.brief)
        blank_industry["opportunity_map"][0]["industry"] = ""
        cases.append((blank_industry, "industry"))
        empty_beneficiary = copy.deepcopy(self.brief)
        empty_beneficiary["opportunity_map"][0]["beneficiaries"] = []
        cases.append((empty_beneficiary, "must not be empty"))
        unknown_opportunity_claim = copy.deepcopy(self.brief)
        unknown_opportunity_claim["opportunity_map"][0]["claim_ids"] = ["missing"]
        cases.append((unknown_opportunity_claim, "unknown claim"))
        no_implication = copy.deepcopy(self.brief)
        no_implication["opportunity_map"][0]["claim_ids"] = ["claim-present"]
        cases.append((no_implication, "implication claim"))

        for value, message in cases:
            with self.subTest(message=message):
                self.assert_brief_rejected(value, message)

        non_opportunity_request = request()
        non_opportunity_request["goal"] = {
            "type": "decision",
            "objective": "决定是否建设自有检索",
            "audience": "技术委员会",
            "decision": "批准或否决预算",
        }
        plan = hengzong.build_plan(non_opportunity_request)
        brief = make_brief(plan)
        brief["opportunity_map"] = []
        refresh_digest(brief)
        result = hengzong.validate_brief_structure(brief, plan)
        self.assertEqual(result["counts"]["opportunities"], 0)

    def test_rejects_retained_gap_and_blocking_reason_semantic_failures(self) -> None:
        cases: list[tuple[dict[str, object], str]] = []
        blank_gap = copy.deepcopy(self.brief)
        blank_gap["retained_gaps"][0]["statement"] = ""
        cases.append((blank_gap, "statement"))
        wrong_status = copy.deepcopy(self.brief)
        wrong_status["retained_gaps"][0]["status"] = "resolved"
        cases.append((wrong_status, "status must be retained"))
        blank_attempt = copy.deepcopy(self.brief)
        blank_attempt["retained_gaps"][0]["attempts"][0]["query"] = ""
        cases.append((blank_attempt, "query"))
        future_attempt = copy.deepcopy(self.brief)
        future_attempt["retained_gaps"][0]["attempts"][0][
            "executed_at"
        ] = "2026-08-25T00:00:00Z"
        cases.append((future_attempt, "executed_at must not be after"))
        bad_outcome = copy.deepcopy(self.brief)
        bad_outcome["retained_gaps"][0]["attempts"][0]["outcome"] = "success"
        cases.append((bad_outcome, "outcome is invalid"))
        duplicate_attempt = copy.deepcopy(self.brief)
        duplicate_attempt["retained_gaps"][0]["attempts"][1][
            "attempt_id"
        ] = "attempt-native"
        cases.append((duplicate_attempt, "values must be unique"))
        for value, message in cases:
            with self.subTest(message=message):
                self.assert_brief_rejected(value, message)

        blocking = copy.deepcopy(self.brief)
        blocking["status"] = "blocking"
        blocking["blocking_reasons"] = []
        refresh_digest(blocking)
        with self.assertRaisesRegex(hengzong.ContractError, "must not be empty"):
            hengzong.validate_brief_structure(blocking, self.plan)

        blocking["blocking_reasons"] = [{"code": "", "message": "blocked"}]
        refresh_digest(blocking)
        with self.assertRaisesRegex(hengzong.ContractError, "code and message"):
            hengzong.validate_brief_structure(blocking, self.plan)

    def test_acceptance_builder_and_validator_reject_malformed_decisions(self) -> None:
        workstream_ids = [
            row["workstream_id"] for row in self.plan["canonical_workstreams"]
        ]
        claim_ids = [row["claim_id"] for row in self.brief["claims"]]
        for kwargs, message in (
            ({"brief_artifact_sha256": "bad"}, "SHA-256"),
            ({"curator_id": ""}, "curator_id"),
            ({"reviewed_workstream_ids": []}, "must not be empty"),
        ):
            supplied = {
                "brief_artifact_sha256": "a" * 64,
                "curator_id": "curator",
                "reviewed_workstream_ids": workstream_ids,
                "accepted_claim_ids": claim_ids,
            }
            supplied.update(kwargs)
            with self.subTest(message=message):
                with self.assertRaisesRegex(hengzong.ContractError, message):
                    hengzong.build_curator_acceptance(self.brief, **supplied)

        bad_brief = copy.deepcopy(self.brief)
        bad_brief["contract_version"] = "wrong"
        with self.assertRaisesRegex(hengzong.ContractError, "hengzong brief"):
            hengzong.build_curator_acceptance(
                bad_brief,
                brief_artifact_sha256="a" * 64,
                curator_id="curator",
                reviewed_workstream_ids=workstream_ids,
                accepted_claim_ids=claim_ids,
            )

        bad_digest_brief = copy.deepcopy(self.brief)
        bad_digest_brief["result_digest_sha256"] = "bad"
        with self.assertRaisesRegex(hengzong.ContractError, "result digest"):
            hengzong.build_curator_acceptance(
                bad_digest_brief,
                brief_artifact_sha256="a" * 64,
                curator_id="curator",
                reviewed_workstream_ids=workstream_ids,
                accepted_claim_ids=claim_ids,
            )

        base = self.acceptance()
        mutations = []
        for field, value, message in (
            ("contract_version", "wrong", "contract_version"),
            ("run_id", "other", "run_id"),
            ("stage", "curate", "stage"),
            ("status", "rejected", "status and decision"),
        ):
            mutated = copy.deepcopy(base)
            mutated[field] = value
            refresh_digest(mutated)
            mutations.append((mutated, message))
        blank_curator = copy.deepcopy(base)
        blank_curator["curator"]["curator_id"] = ""
        refresh_digest(blank_curator)
        mutations.append((blank_curator, "curator_id"))
        missing_workstream = copy.deepcopy(base)
        missing_workstream["reviewed_workstream_ids"] = missing_workstream[
            "reviewed_workstream_ids"
        ][:-1]
        missing_workstream["counts"]["reviewed_workstreams"] -= 1
        refresh_digest(missing_workstream)
        mutations.append((missing_workstream, "workstream set"))
        wrong_counts = copy.deepcopy(base)
        wrong_counts["counts"]["accepted_claims"] += 1
        refresh_digest(wrong_counts)
        mutations.append((wrong_counts, "counts"))

        for acceptance, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(hengzong.ContractError, message):
                    hengzong.validate_brief(
                        self.brief,
                        self.plan,
                        acceptance=acceptance,
                        brief_artifact_sha256="a" * 64,
                    )

        with self.assertRaisesRegex(hengzong.ContractError, "artifact SHA-256"):
            hengzong.validate_brief(
                self.brief,
                self.plan,
                acceptance=base,
                brief_artifact_sha256="bad",
            )

        acceptance = self.acceptance()
        acceptance["accepted_claim_ids"] = acceptance["accepted_claim_ids"][:-1]
        acceptance["counts"]["accepted_claims"] -= 1
        refresh_digest(acceptance)
        with self.assertRaisesRegex(hengzong.ContractError, "claim set"):
            hengzong.validate_brief(
                self.brief,
                self.plan,
                acceptance=acceptance,
                brief_artifact_sha256="a" * 64,
            )


class CliAndSchemaTests(unittest.TestCase):
    def test_cli_builds_and_validates_plan_and_acceptance_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path = root / "request.json"
            plan_path = root / "plan.json"
            brief_path = root / "brief.json"
            acceptance_path = root / "acceptance.json"
            write_json(request_path, request())

            built = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build-plan",
                    "--request",
                    str(request_path),
                    "--output",
                    str(plan_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(built.returncode, 0, built.stdout or built.stderr)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            validated = subprocess.run(
                [sys.executable, str(SCRIPT), "validate-plan", "--plan", str(plan_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout or validated.stderr)

            brief = make_brief(plan)
            write_json(brief_path, brief)
            acceptance = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build-acceptance",
                    "--brief",
                    str(brief_path),
                    "--curator-id",
                    "curator-independent-01",
                    *[
                        argument
                        for row in plan["canonical_workstreams"]
                        for argument in ("--workstream-id", row["workstream_id"])
                    ],
                    *[
                        argument
                        for row in brief["claims"]
                        for argument in ("--claim-id", row["claim_id"])
                    ],
                    "--output",
                    str(acceptance_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(acceptance.returncode, 0, acceptance.stdout or acceptance.stderr)
        self.assertEqual(json.loads(acceptance.stdout)["status"], "accepted")

    def test_cli_rejects_unreadable_json_with_machine_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("[]", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "validate-plan", "--plan", str(path)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "invalid")
        self.assertIn("object", payload["message"])

    def test_cli_build_plan_without_output_and_contract_failure_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid_path = root / "valid.json"
            invalid_path = root / "invalid.json"
            write_json(valid_path, request())
            invalid = request()
            invalid["goal"]["type"] = "prediction"
            write_json(invalid_path, invalid)

            success_stdout = io.StringIO()
            with contextlib.redirect_stdout(success_stdout):
                returncode = hengzong.main(
                    ["build-plan", "--request", str(valid_path)]
                )
            failure_stdout = io.StringIO()
            with contextlib.redirect_stdout(failure_stdout):
                failure_code = hengzong.main(
                    ["build-plan", "--request", str(invalid_path)]
                )

        self.assertEqual(returncode, 0)
        self.assertEqual(json.loads(success_stdout.getvalue())["status"], "complete")
        self.assertEqual(failure_code, 2)
        self.assertEqual(json.loads(failure_stdout.getvalue())["status"], "invalid")

    def test_read_json_rejects_missing_invalid_utf8_non_object_and_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = root / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            invalid_utf8 = root / "invalid-utf8.json"
            invalid_utf8.write_bytes(b"\xff")
            scalar = root / "scalar.json"
            scalar.write_text('"text"', encoding="utf-8")
            missing = root / "missing.json"

            for path, message in (
                (malformed, "cannot read JSON"),
                (invalid_utf8, "cannot read JSON"),
                (scalar, "must contain an object"),
                (missing, "cannot read JSON"),
                (root, "cannot read JSON"),
            ):
                with self.subTest(path=path.name):
                    with self.assertRaisesRegex(hengzong.ContractError, message):
                        hengzong._read_json(path)

    def test_read_json_detects_changed_snapshot_and_write_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            source.write_text('{"value": 1}', encoding="utf-8")
            real_fstat = os.fstat
            calls = 0

            def changed_fstat(fd: int):
                nonlocal calls
                calls += 1
                result = real_fstat(fd)
                if calls == 2:
                    values = list(result)
                    values[1] = result.st_ino + 1
                    return os.stat_result(values)
                return result

            with mock.patch.object(hengzong.os, "fstat", side_effect=changed_fstat):
                with self.assertRaisesRegex(hengzong.ContractError, "changed while"):
                    hengzong._read_json(source)

            output = root / "nested" / "result.json"
            legacy_temporary = output.with_name(output.name + ".tmp")
            legacy_temporary.parent.mkdir(parents=True)
            legacy_temporary.write_text("unrelated user data", encoding="utf-8")
            hengzong._write_json(output, {"状态": "完成"})
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")), {"状态": "完成"}
            )
            self.assertEqual(
                legacy_temporary.read_text(encoding="utf-8"),
                "unrelated user data",
            )
            self.assertEqual(
                list(output.parent.glob(f".{output.name}.*.tmp")), []
            )

    def test_main_exercises_all_cli_routes_and_blocking_without_subprocess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path = root / "request.json"
            plan_path = root / "plan.json"
            brief_path = root / "brief.json"
            acceptance_path = root / "acceptance.json"
            write_json(request_path, request())

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    hengzong.main(
                        [
                            "build-plan",
                            "--request",
                            str(request_path),
                            "--output",
                            str(plan_path),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    hengzong.main(["validate-plan", "--plan", str(plan_path)]),
                    0,
                )

            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            brief = make_brief(plan)
            write_json(brief_path, brief)
            workstream_args = [
                argument
                for row in plan["canonical_workstreams"]
                for argument in ("--workstream-id", row["workstream_id"])
            ]
            claim_args = [
                argument
                for row in brief["claims"]
                for argument in ("--claim-id", row["claim_id"])
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    hengzong.main(
                        [
                            "build-acceptance",
                            "--brief",
                            str(brief_path),
                            "--curator-id",
                            "curator-independent-01",
                            *workstream_args,
                            *claim_args,
                            "--output",
                            str(acceptance_path),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    hengzong.main(
                        [
                            "validate-brief",
                            "--brief",
                            str(brief_path),
                            "--plan",
                            str(plan_path),
                            "--acceptance",
                            str(acceptance_path),
                        ]
                    ),
                    0,
                )

            blocked_stdout = io.StringIO()
            with contextlib.redirect_stdout(blocked_stdout):
                blocked_code = hengzong.main(
                    [
                        "validate-brief",
                        "--brief",
                        str(brief_path),
                        "--plan",
                        str(plan_path),
                    ]
                )
            self.assertEqual(blocked_code, 3)
            self.assertEqual(json.loads(blocked_stdout.getvalue())["status"], "blocking")

    def test_blocking_brief_exits_nonzero_with_machine_readable_status(self) -> None:
        plan = hengzong.build_plan(request())
        brief = make_brief(plan)
        brief["status"] = "blocking"
        brief["blocking_reasons"] = [
            {
                "code": "source_access_blocked",
                "message": "关键来源需要用户授权后才能继续。",
            }
        ]
        refresh_digest(brief)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "plan.json"
            brief_path = root / "brief.json"
            write_json(plan_path, plan)
            write_json(brief_path, brief)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "validate-brief",
                    "--brief",
                    str(brief_path),
                    "--plan",
                    str(plan_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "blocking")
        self.assertEqual(payload["code"], "source_access_blocked")
        self.assertIn("用户授权", payload["message"])

    def test_cli_validates_bound_acceptance(self) -> None:
        plan = hengzong.build_plan(request())
        brief = make_brief(plan)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "plan.json"
            brief_path = root / "brief.json"
            acceptance_path = root / "acceptance.json"
            write_json(plan_path, plan)
            artifact_sha256 = write_json(brief_path, brief)
            acceptance = hengzong.build_curator_acceptance(
                brief,
                brief_artifact_sha256=artifact_sha256,
                curator_id="curator-independent-01",
                reviewed_workstream_ids=[
                    row["workstream_id"]
                    for row in plan["canonical_workstreams"]
                ],
                accepted_claim_ids=[row["claim_id"] for row in brief["claims"]],
            )
            write_json(acceptance_path, acceptance)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "validate-brief",
                    "--brief",
                    str(brief_path),
                    "--plan",
                    str(plan_path),
                    "--acceptance",
                    str(acceptance_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertEqual(json.loads(completed.stdout)["status"], "verified")

    def test_json_schemas_are_strict_and_match_runtime_contract_ids(self) -> None:
        schema_root = SCRIPT.parents[1] / "assets" / "engine-contracts"
        expected = {
            "hengzong-request.schema.json": (
                hengzong.REQUEST_CONTRACT,
                hengzong.REQUEST_FIELDS,
            ),
            "hengzong-plan.schema.json": (
                hengzong.PLAN_CONTRACT,
                hengzong.PLAN_FIELDS,
            ),
            "hengzong-brief.schema.json": (
                hengzong.BRIEF_CONTRACT,
                hengzong.BRIEF_FIELDS,
            ),
            "hengzong-curator-acceptance.schema.json": (
                hengzong.ACCEPTANCE_CONTRACT,
                hengzong.ACCEPTANCE_FIELDS,
            ),
        }
        schemas: dict[str, dict[str, object]] = {}
        for filename, (contract, runtime_fields) in expected.items():
            with self.subTest(filename=filename):
                schema = json.loads((schema_root / filename).read_text(encoding="utf-8"))
                schemas[filename] = schema
                self.assertEqual(schema["$id"], contract)
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), runtime_fields)
                self.assertEqual(set(schema["properties"]), runtime_fields)

        request_schema = schemas["hengzong-request.schema.json"]
        plan_schema = schemas["hengzong-plan.schema.json"]
        brief_schema = schemas["hengzong-brief.schema.json"]
        self.assertEqual(
            set(request_schema["$defs"]["goal"]["properties"]["type"]["enum"]),
            hengzong.GOAL_TYPES,
        )
        self.assertEqual(
            request_schema["$defs"]["queryBounds"]["properties"][
                "max_geo_language_cells"
            ]["maximum"],
            hengzong.HARD_MAX_GEO_LANGUAGE_CELLS,
        )
        self.assertEqual(
            request_schema["$defs"]["queryBounds"]["properties"][
                "max_queries_per_group"
            ]["maximum"],
            hengzong.HARD_MAX_QUERIES_PER_GROUP,
        )
        self.assertEqual(
            request_schema["$defs"]["queryBounds"]["properties"][
                "max_total_queries"
            ]["maximum"],
            hengzong.HARD_MAX_TOTAL_QUERIES,
        )
        self.assertEqual(
            set(brief_schema["properties"]["status"]["enum"]),
            {"ready_for_curator", "blocking"},
        )
        self.assertEqual(
            set(brief_schema["$defs"]["claim"]["properties"]["temporal_role"]["enum"]),
            hengzong.TEMPORAL_ROLES,
        )
        self.assertEqual(
            set(brief_schema["$defs"]["evidenceLink"]["properties"]["stance"]["enum"]),
            hengzong.STANCES,
        )
        self.assertEqual(
            set(brief_schema["$defs"]["scenario"]["properties"]["scenario_id"]["enum"]),
            hengzong.SCENARIO_IDS,
        )
        self.assertEqual(
            plan_schema["properties"]["canonical_workstreams"]["minItems"], 6
        )
        self.assertEqual(
            plan_schema["properties"]["canonical_workstreams"]["maxItems"], 6
        )


if __name__ == "__main__":
    unittest.main()
