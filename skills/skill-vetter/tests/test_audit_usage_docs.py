from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_usage_docs.py"
SPEC = importlib.util.spec_from_file_location("audit_usage_docs", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class UsageDocsAuditTests(unittest.TestCase):
    def fixture(self, mutate=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        skill = root / "skills" / "sample"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: Use for a sample workflow request.\n---\n"
            "# Sample\n\nRead [references/examples.md](references/examples.md).\n\n"
            "## Inputs and scope\n\nResolve the request, input, context, permission, and boundary. "
            "## Workflow\n\nProcess the work in an explicit sequence. "
            "## Failure recovery\n\nStop on failure and recover without blind retry. "
            "## Verification\n\nVerify completion with observable evidence. " + "detail " * 100,
            encoding="utf-8",
        )
        positive = (
            "**用户请求：** 完成一个具体任务。\n\n**准备信息：** 输入、前提和目标路径已确认。\n\n"
            "**处理：** 按明确步骤处理对象并保留权限边界。\n\n**预期输出：** 产生可打开的目标制品。\n\n"
            "**验收证据：** 回读结果、检查字段和命令输出均一致。\n\n" + "具体细节。" * 40
        )
        boundary = (
            "**场景：** 请求包含超出范围的动作。\n\n**边界判断：** 该动作没有获得授权。\n\n"
            "**处理：** 停止外部写入并给出范围内方案。\n\n**验收证据：** 精确对象状态保持不变。\n\n" + "边界细节。" * 40
        )
        recovery = (
            "**失败场景：** 执行返回未知状态。\n\n**处理与恢复：** 先只读查询，再根据真实状态恢复。\n\n"
            "**验收证据：** 状态、已完成范围和下一步均可复核。\n\n" + "恢复细节。" * 40
        )
        (skill / "references" / "examples.md").write_text(
            f"# 使用说明与案例\n\n## 使用说明\n\n"
            f"适用于需要完成示例工作流并保留可观察证据的请求。开始前确认目标对象、输入、"
            f"输出位置、权限范围和停止条件；执行时依次读取现状、处理输入、写入目标并回读验证。"
            f"如果对象不明确、授权不足或外部状态未知，停止有副作用的动作，保存当前证据并给出"
            f"下一次安全继续所需条件。只有目标制品可打开、关键字段一致且边界未被突破时才报告完成。"
            f"具体命令和字段必须替换为本次任务的真实值。" + "使用细节。" * 20 + "\n\n"
            f"## 正向案例\n\n{positive}\n\n## 边界案例\n\n{boundary}\n\n## 失败与恢复\n\n{recovery}\n",
            encoding="utf-8",
        )
        (root / "USAGE_GUIDE.md").write_text(
            "[入口](skills/sample/SKILL.md) [案例](skills/sample/references/examples.md)",
            encoding="utf-8",
        )
        if mutate:
            mutate(skill)
        return root

    def codes(self, root):
        findings, _summary = MODULE.audit(root, expected_count=1, min_case_chars=220)
        return {finding.code for finding in findings}

    def test_complete_usage_docs_pass(self):
        self.assertEqual(self.codes(self.fixture()), set())

    def test_missing_preparation_is_reported(self):
        def mutate(skill):
            path = skill / "references" / "examples.md"
            text = path.read_text(encoding="utf-8").replace("**准备信息：** 输入、前提和目标路径已确认。", "")
            path.write_text(text, encoding="utf-8")

        self.assertIn("case-signal", self.codes(self.fixture(mutate)))

    def test_missing_usage_section_is_reported(self):
        def mutate(skill):
            path = skill / "references" / "examples.md"
            text = path.read_text(encoding="utf-8").replace("## 使用说明", "## 使用方式", 1)
            path.write_text(text, encoding="utf-8")

        self.assertIn("usage-section-missing", self.codes(self.fixture(mutate)))

    def test_thin_usage_section_is_reported(self):
        def mutate(skill):
            path = skill / "references" / "examples.md"
            text = path.read_text(encoding="utf-8")
            start = text.index("## 使用说明")
            end = text.index("## 正向案例")
            replacement = "## 使用说明\n\n准备输入后执行并验收。\n\n"
            path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

        self.assertIn("usage-section-thin", self.codes(self.fixture(mutate)))

    def test_thin_case_is_reported(self):
        def mutate(skill):
            path = skill / "references" / "examples.md"
            text = path.read_text(encoding="utf-8")
            start = text.index("## 边界案例")
            end = text.index("## 失败与恢复")
            replacement = "## 边界案例\n\n**场景：** X。**边界判断：** Y。**处理：** Z。**验收证据：** N。\n\n"
            path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

        self.assertIn("case-thin", self.codes(self.fixture(mutate)))

    def test_generic_evidence_is_reported(self):
        def mutate(skill):
            path = skill / "references" / "examples.md"
            with path.open("a", encoding="utf-8") as handle:
                handle.write("\n- **验收证据：** 失败状态、已完成范围和下一次安全重试条件均可复核。\n")

        self.assertIn("generic-case-evidence", self.codes(self.fixture(mutate)))

    def test_usage_guide_gap_is_reported(self):
        def mutate(skill):
            (skill.parents[1] / "USAGE_GUIDE.md").write_text("# Empty guide", encoding="utf-8")

        self.assertIn("usage-guide-coverage", self.codes(self.fixture(mutate)))


if __name__ == "__main__":
    unittest.main()
