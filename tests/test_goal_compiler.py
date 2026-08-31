#!/usr/bin/env python3
"""Behavior and security regressions for the Goal Compiler boundary."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"
DEMO_FIXTURES = ROOT / "contest" / "demo-fixtures"
sys.path.insert(0, str(SCRIPTS))

import goal_compiler  # noqa: E402


WEBSITE_REQUEST = "给我做个 AI 网站，越快越好"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_semantic(name: str) -> dict:
    return goal_compiler.load_semantic_input(FIXTURES / name)


def synthetic_review(metric_id: str) -> dict:
    review = load_fixture("synthetic-approved-review.json")
    review["metric_id"] = metric_id
    return review


class GoalCompilerBoundaryTests(unittest.TestCase):
    def test_compile_requires_complete_semantic_input(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "goal_compiler.py"), "compile", "--request", WEBSITE_REQUEST, "--output", "/tmp/not-created"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--semantic-input", result.stderr)

    def test_compile_is_deterministic_for_same_agent_payload(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        first = goal_compiler.build_contract(WEBSITE_REQUEST, semantic)
        second = goal_compiler.build_contract(WEBSITE_REQUEST, semantic)
        self.assertEqual(first, second)
        self.assertEqual(first["smart_router"]["task_type"], "website")
        self.assertEqual(first["compiler"]["kind"], "deterministic-cli")
        self.assertFalse(first["semantic_compilation"]["live_ai_claimed"])

    def test_coding_request_rejects_website_semantics(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        coding_request = "修复 CSV parser 忽略空行时崩溃的问题，并增加回归测试"
        semantic["request"] = coding_request
        with self.assertRaisesRegex(goal_compiler.CompilerError, "domain mismatch"):
            goal_compiler.build_contract(coding_request, semantic)

    def test_generic_programming_language_request_routes_as_coding(self) -> None:
        self.assertEqual(
            goal_compiler.infer_request_task_type("写一个 Python 脚本，并为函数增加单元测试"),
            "coding",
        )

    def test_unknown_domain_is_rejected(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        request = "帮我整理这个未定义的事情"
        semantic["request"] = request
        semantic["smart_router"]["task_type"] = "unknown"
        with self.assertRaisesRegex(goal_compiler.CompilerError, "unsupported task type"):
            goal_compiler.build_contract(request, semantic)

    def test_coding_goal_has_no_website_leak_and_dispatches_python(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        rendered = goal_compiler.render_goal(contract)
        for forbidden in ("CTA", "15-25 个候选来源", "IdeaSignal", "网站/落地页改版包"):
            self.assertNotIn(forbidden, rendered)

        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "coding-first-output"
            report = goal_compiler.execute_first_step(approved, output)
            artifact = output / "test_csv_empty_lines.py"
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["dispatch"]["action"], "write_python_regression_fixture")
            self.assertTrue(artifact.is_file())
            self.assertIn("REGRESSION_FIXTURE", artifact.read_text(encoding="utf-8"))
            self.assertTrue(report["checks"]["python_syntax"])

    def test_seo_requires_sources_before_human_approval(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        errors = goal_compiler.validate_contract(contract, require_human_approval=False, require_evidence=True)
        self.assertTrue(any("evidence_bundle.sources" in error for error in errors))
        with self.assertRaisesRegex(goal_compiler.CompilerError, "evidence-incomplete"):
            goal_compiler.apply_human_review(contract, synthetic_review("seo-source-brief"))

        evidence = load_fixture("seo-evidence.json")
        approved = goal_compiler.apply_human_review(
            contract,
            synthetic_review("seo-source-brief"),
            evidence_bundle=evidence,
        )
        self.assertEqual([], goal_compiler.validate_contract(approved))

    def test_subjective_metric_statement_and_method_fail(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        semantic["strategy_gate"]["success_metrics"][0]["statement"] = "这个修复看起来更专业且令人满意"
        semantic["strategy_gate"]["success_metrics"][0]["measurement"] = {
            "method": "人工主观感受",
            "target": {"reviewers": 1},
        }
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        joined = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("vague wording", joined)
        self.assertIn("subjective method", joined)
        self.assertIn("does not correspond to action", joined)

    def test_pending_review_fixture_cannot_be_applied(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        pending = json.loads((DEMO_FIXTURES / "human-review.pending.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(goal_compiler.CompilerError, "pending"):
            goal_compiler.apply_human_review(contract, pending)

    def test_synthetic_approval_cannot_bypass_non_test_contract(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        contract = goal_compiler.build_contract(WEBSITE_REQUEST, semantic)
        review = synthetic_review("first-validation-page")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "test_fixture"):
            goal_compiler.apply_human_review(contract, review)

    def test_review_must_name_exact_metric(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        review = synthetic_review("wrong-metric")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "metric_id"):
            goal_compiler.apply_human_review(contract, review)

    def test_evidence_sources_must_have_distinct_urls(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        evidence = load_fixture("seo-evidence.json")
        evidence["sources"][1]["url"] = evidence["sources"][0]["url"]
        contract = goal_compiler.build_contract(semantic["request"], semantic, evidence_bundle=evidence)
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("duplicate URL", errors)

    def test_request_hash_and_contract_id_are_verified(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        request_tamper = copy.deepcopy(contract)
        request_tamper["request"]["raw"] += " tampered"
        request_errors = "\n".join(goal_compiler.validate_contract(request_tamper, require_human_approval=False))
        self.assertIn("request.request_sha256", request_errors)

        id_tamper = copy.deepcopy(contract)
        id_tamper["contract_id"] = "goal-tampered"
        id_errors = "\n".join(goal_compiler.validate_contract(id_tamper, require_human_approval=False))
        self.assertIn("contract_id", id_errors)

    def test_every_execution_field_is_bound_after_approval(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))

        mutations = {
            "request": lambda value: value["request"].__setitem__("raw", value["request"]["raw"] + " changed"),
            "router": lambda value: value["smart_router"].__setitem__("risk_level", "high"),
            "strategy": lambda value: value["strategy_gate"]["success_metrics"][0].__setitem__("statement", "生成 2 个 Python 文件"),
            "evidence": lambda value: value["evidence_bundle"].__setitem__("claims", [{"changed": True}]),
            "action": lambda value: value["first_step"].__setitem__("action", "shell_anything"),
            "artifact": lambda value: value["first_step"].__setitem__("primary_artifact", "first-output/other.py"),
            "checks": lambda value: value["first_step"].__setitem__("validators", ["nonempty"]),
            "content": lambda value: value["first_step"].__setitem__("content_template", "# changed"),
        }
        for name, mutate in mutations.items():
            with self.subTest(field=name):
                tampered = copy.deepcopy(approved)
                mutate(tampered)
                errors = goal_compiler.validate_contract(tampered)
                self.assertTrue(
                    any("approved_payload_sha256" in error for error in errors),
                    f"{name} did not invalidate approval: {errors}",
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    output = Path(temp_dir) / "blocked"
                    with self.assertRaises(goal_compiler.CompilerError):
                        goal_compiler.execute_first_step(tampered, output)
                    self.assertFalse(output.exists())

    def test_approval_digest_covers_declared_execution_bound_fields(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        for field in goal_compiler.EXECUTION_BOUND_FIELDS:
            with self.subTest(field=field):
                tampered = copy.deepcopy(approved)
                current = tampered[field]
                if isinstance(current, dict):
                    current["_post_approval_tamper"] = True
                elif isinstance(current, list):
                    current.append("post approval tamper")
                else:
                    tampered[field] = f"{current}-tampered"
                errors = goal_compiler.validate_contract(tampered)
                self.assertTrue(any("approved_payload_sha256" in error for error in errors), errors)

    def test_unknown_action_and_action_specific_checks_are_rejected(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        contract["first_step"]["action"] = "run_shell"
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("unsupported action", errors)

        contract = goal_compiler.build_contract(semantic["request"], semantic)
        contract["first_step"]["validators"] = ["nonempty"]
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("must exactly match action whitelist", errors)

    def test_file_and_directory_outputs_refuse_existing_targets(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing_dir = root / "existing-output"
            existing_dir.mkdir()
            with self.assertRaisesRegex(goal_compiler.CompilerError, "already exists"):
                goal_compiler.execute_first_step(approved, existing_dir)

            existing_file = root / "existing.json"
            existing_file.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(goal_compiler.CompilerError, "overwrite"):
                goal_compiler.write_json(existing_file, contract, refuse_existing=True)

    def test_demo_writes_only_fail_logs_and_stops_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            report = goal_compiler.run_demo(
                output,
                DEMO_FIXTURES / "request.txt",
                DEMO_FIXTURES / "semantic-input.demo.json",
            )
            self.assertEqual(report["status"], "HUMAN_PENDING")
            self.assertFalse(report["liveAiClaimed"])
            self.assertFalse(report["execution"]["attempted"])
            self.assertEqual([], list(output.rglob("validator.PASS.log")))
            self.assertEqual(2, len(list(output.rglob("validator.FAIL.log"))))
            self.assertFalse((output / "03-first-output").exists())
            self.assertTrue((output / "03-human-pending" / "human-review.pending.json").is_file())

    def test_cli_validate_nonzero_for_pending_and_zero_for_synthetic_test_approval(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = goal_compiler.build_contract(semantic["request"], semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending.json"
            approved_path = root / "approved.json"
            goal_compiler.write_json(pending_path, contract)
            goal_compiler.write_json(approved_path, approved)
            pending = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(pending_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            passed = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(approved_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(pending.returncode, 1)
            self.assertEqual(passed.returncode, 0, passed.stderr)


if __name__ == "__main__":
    unittest.main()
