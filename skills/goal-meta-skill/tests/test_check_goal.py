import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_goal.py"
SPEC = importlib.util.spec_from_file_location("check_goal", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GoalCheckerTests(unittest.TestCase):
    def codes(self, text):
        return {finding.code for finding in MODULE.analyze(text)}

    def test_strong_chinese_goal_has_no_findings(self):
        text = (
            "/goal 修复结账优惠券重复计算问题，并保持固定金额优惠和礼品卡行为不变。"
            "用先失败后通过的回归测试、相关测试套件和运行日志作为验证证据。"
            "只允许修改结账定价逻辑及其测试；涉及生产支付凭证或规则不明确时暂停并请求用户确认。"
            "仅当所有命名行为都被证明、检查全部通过且无剩余要求时完成。"
        )
        self.assertEqual([], MODULE.analyze(text))

    def test_strong_english_goal_has_no_findings(self):
        text = (
            "/goal Fix coupon calculation while preserving the public API. Verify with a failing-then-passing "
            "regression test, the checkout test suite, and runtime logs. Only write checkout code and tests; "
            "pause for approval before production or credential use. Finish only when all required behavior is "
            "proved and no required work remains."
        )
        self.assertEqual([], MODULE.analyze(text))

    def test_placeholder_is_error(self):
        self.assertIn("placeholder", self.codes("/goal 完成[目标]并用测试验证，完成条件是测试全部通过。"))

    def test_high_risk_work_requires_authority_boundary(self):
        text = "/goal 发布到生产并推送代码。用运行日志验证；完成条件是线上可用。"
        self.assertIn("missing-authority-boundary", self.codes(text))

    def test_unbounded_retry_is_error(self):
        text = "/goal 一直重试直到成功。用测试验证；完成条件是全部通过。"
        self.assertIn("unbounded-persistence", self.codes(text))

    def test_vague_goal_warns_about_evidence_and_completion(self):
        codes = self.codes("/goal 优化一下")
        self.assertTrue({"weak-outcome", "missing-evidence", "missing-completion"}.issubset(codes))

    def test_json_cli_reports_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "goal.txt"
            path.write_text("/goal 完成[目标]", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--format", "json"],
                text=True,
                capture_output=True,
                check=False,
            )
        payload = json.loads(result.stdout)
        self.assertEqual(1, result.returncode)
        self.assertGreaterEqual(payload["counts"]["error"], 1)


if __name__ == "__main__":
    unittest.main()
