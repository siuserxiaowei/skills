#!/usr/bin/env python3
"""Behavior tests for the deterministic Goal Compiler CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import goal_compiler  # noqa: E402


REQUEST = "给我做个 AI 网站，越快越好"
REVIEW = ROOT / "contest" / "demo-fixtures" / "human-review.json"


class GoalCompilerTests(unittest.TestCase):
    def test_compile_is_deterministic_and_routes_vague_website(self) -> None:
        first = goal_compiler.compile_contract(REQUEST)
        second = goal_compiler.compile_contract(REQUEST)

        self.assertEqual(first, second)
        self.assertEqual(first["smart_router"]["task_type"], "website")
        self.assertEqual(first["smart_router"]["maturity"], "模糊想法")
        self.assertEqual(first["smart_router"]["risk_level"], "中")
        self.assertEqual(first["smart_router"]["external_information_need"], "标准")

    def test_vague_human_metric_fails_for_specific_reasons(self) -> None:
        contract = goal_compiler.compile_contract(REQUEST, proposed_metric="好看")
        errors = goal_compiler.validate_contract(contract, require_human_approval=True)
        joined = "\n".join(errors)

        self.assertIn("vague metric", joined)
        self.assertIn("explicit thresholds", joined)
        self.assertIn("human_review.decision", joined)

    def test_human_review_makes_contract_strictly_valid(self) -> None:
        contract = goal_compiler.compile_contract(REQUEST, proposed_metric="好看")
        review = json.loads(REVIEW.read_text(encoding="utf-8"))
        reviewed = goal_compiler.apply_human_review(contract, review)

        self.assertEqual([], goal_compiler.validate_contract(reviewed, require_human_approval=True))
        self.assertEqual(reviewed["human_review"]["previous_metric_statement"], "好看")
        self.assertEqual(reviewed["human_review"]["sign_off"], "APPROVED BY HUMAN")

    def test_execution_blocks_pending_contract(self) -> None:
        contract = goal_compiler.compile_contract(REQUEST)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "first-output"
            with self.assertRaises(goal_compiler.CompilerError):
                goal_compiler.execute_first_step(contract, output)
            self.assertFalse(output.exists())

    def test_demo_proves_fail_review_pass_and_real_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            report = goal_compiler.run_demo(
                output,
                ROOT / "contest" / "demo-fixtures" / "request.txt",
                REVIEW,
            )

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["negative_gate"]["status"], "FAIL")
            self.assertEqual(report["positive_gate"]["status"], "PASS")
            self.assertEqual(report["first_step_execution"]["status"], "PASS")
            self.assertTrue((output / "03-first-output" / "index.html").is_file())
            self.assertTrue((output / "03-first-output" / "execution-report.json").is_file())

    def test_cli_validate_returns_nonzero_then_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            invalid_path = root / "invalid.json"
            reviewed_path = root / "reviewed.json"
            contract = goal_compiler.compile_contract(REQUEST, proposed_metric="好看")
            goal_compiler.write_json(invalid_path, contract)

            invalid = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(invalid_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(invalid.returncode, 1)

            review = json.loads(REVIEW.read_text(encoding="utf-8"))
            reviewed = goal_compiler.apply_human_review(contract, review)
            goal_compiler.write_json(reviewed_path, reviewed)
            valid = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(reviewed_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)


if __name__ == "__main__":
    unittest.main()
