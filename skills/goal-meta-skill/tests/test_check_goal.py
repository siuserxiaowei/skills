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
            "/goal 修复静态站点导航中的重复页面标识，并保持合法嵌套页面的排序和输出字段不变。"
            "用先失败后通过的回归测试、导航测试套件和构建日志作为验证证据。"
            "只允许修改导航生成器及其测试；涉及公开数据结构或现有内容标识时暂停并请求用户确认。"
            "仅当所有命名行为都被证明、检查全部通过且无剩余要求时完成。"
        )
        self.assertEqual([], MODULE.analyze(text))

    def test_strong_english_goal_has_no_findings(self):
        text = (
            "/goal Reject duplicate page identifiers while preserving nested navigation order and the public schema. "
            "Verify with a failing-then-passing regression fixture, the navigation suite, and build logs. Only write "
            "the navigation builder and tests; pause for approval before changing existing content identifiers. Finish only when all required behavior is "
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
