from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_family.py"
SPEC = importlib.util.spec_from_file_location("audit_family", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
REAL_ROOT = Path(__file__).resolve().parents[2]


class AuditFamilyTests(unittest.TestCase):
    def codes(self, report: dict) -> set[str]:
        return {item["code"] for item in report["findings"]}

    def test_repository_family_is_clean(self):
        report = MODULE.audit_family(REAL_ROOT)
        self.assertTrue(report["ok"], report["findings"])
        self.assertEqual(27, report["skill_count"])

    def mutate_copy(self, callback):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            root.mkdir()
            for name in MODULE.EXPECTED:
                shutil.copytree(REAL_ROOT / name, root / name)
            callback(root)
            return MODULE.audit_family(root)

    def test_missing_skill_is_reported(self):
        report = self.mutate_copy(lambda root: shutil.rmtree(root / "lark-note"))
        self.assertIn("missing_skill", self.codes(report))

    def test_embedded_license_is_reported(self):
        def mutate(root):
            (root / "lark-note" / "LICENSE").write_text("copied", encoding="utf-8")
        self.assertIn("embedded_license", self.codes(self.mutate_copy(mutate)))

    def test_name_mismatch_is_reported(self):
        def mutate(root):
            path = root / "lark-note" / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("name: lark-note", "name: lark-vc", 1), encoding="utf-8")
        self.assertIn("name_mismatch", self.codes(self.mutate_copy(mutate)))

    def test_broken_relative_link_is_reported(self):
        def mutate(root):
            path = root / "lark-note" / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n[broken](missing.md)\n", encoding="utf-8")
        self.assertIn("broken_link", self.codes(self.mutate_copy(mutate)))

    def test_missing_prompt_token_is_reported(self):
        def mutate(root):
            path = root / "lark-note" / "agents" / "openai.yaml"
            path.write_text(path.read_text(encoding="utf-8").replace("$lark-note", "$other"), encoding="utf-8")
        self.assertIn("missing_default_prompt_token", self.codes(self.mutate_copy(mutate)))

    def test_missing_runtime_discovery_is_reported(self):
        def mutate(root):
            path = root / "lark-note" / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8").replace("lark-cli --version", "version command"), encoding="utf-8")
        self.assertIn("missing_runtime_discovery", self.codes(self.mutate_copy(mutate)))


if __name__ == "__main__":
    unittest.main()
