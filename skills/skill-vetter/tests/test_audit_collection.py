from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_collection.py"
SPEC = importlib.util.spec_from_file_location("audit_collection", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CollectionAuditTests(unittest.TestCase):
    def fixture(self, mutate=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        skill = root / "skills" / "sample"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: sample\ndescription: A sufficiently specific sample description for testing.\n---\n"
            "# Sample\n\n## 案例入口\n\n先读 [references/examples.md](references/examples.md)。\n\n"
            "## 范围\n\n说明边界。\n\n## 流程\n\n" + "执行与验收。" * 100,
            encoding="utf-8",
        )
        (skill / "references" / "examples.md").write_text(
            "# 案例与详细说明\n\n## 正向案例\n\n用户请求。处理。验收证据。" + "细节。" * 160
            + "\n\n## 边界案例\n\n场景。边界。验收证据。"
            + "\n\n## 失败与恢复\n\n场景。处理。失败。验收证据。",
            encoding="utf-8",
        )
        (root / "SKILL_PROVENANCE.json").write_text(
            json.dumps({"bundled_third_party_artifacts": [], "origin_groups": {"new_original": ["sample"]}}),
            encoding="utf-8",
        )
        if mutate:
            mutate(root, skill)
        return root

    def codes(self, root):
        findings, _ = MODULE.audit(root, 1)
        return {finding.code for finding in findings}

    def test_clean_collection(self):
        self.assertEqual(self.codes(self.fixture()), set())

    def test_missing_example_is_reported(self):
        root = self.fixture(lambda _root, skill: (skill / "references" / "examples.md").unlink())
        self.assertIn("example-missing", self.codes(root))

    def test_provenance_gap_is_reported(self):
        def mutate(root, _skill):
            (root / "SKILL_PROVENANCE.json").write_text(
                json.dumps({"bundled_third_party_artifacts": [], "origin_groups": {"new_original": []}}),
                encoding="utf-8",
            )
        self.assertIn("provenance-coverage", self.codes(self.fixture(mutate)))

    def test_embedded_notice_and_binary_are_reported(self):
        def mutate(_root, skill):
            (skill / "LICENSE.third-party").write_text("external", encoding="utf-8")
            (skill / "asset.png").write_bytes(b"not really a png")
        codes = self.codes(self.fixture(mutate))
        self.assertIn("embedded-notice", codes)
        self.assertIn("unmanifested-binary", codes)


if __name__ == "__main__":
    unittest.main()
