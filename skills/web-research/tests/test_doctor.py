from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "doctor.py"
SPEC = importlib.util.spec_from_file_location("web_research_doctor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DoctorTests(unittest.TestCase):
    def write_skill(self, root: Path, name: str, declared: str | None = None):
        folder = root / name
        folder.mkdir()
        value = declared or name
        (folder / "SKILL.md").write_text(f"---\nname: {value}\ndescription: test fixture\n---\n", encoding="utf-8")

    def test_missing_children_are_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            report = MODULE.build_report(Path(directory), False)
        self.assertEqual(0, report["counts"]["error"])
        self.assertEqual(len(MODULE.CHILDREN), report["counts"]["warning"])

    def test_complete_fixture_has_matching_children(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, _ in MODULE.CHILDREN.values():
                self.write_skill(root, name)
            report = MODULE.build_report(root, False)
        self.assertTrue(all(child["name_matches"] for child in report["children"]))
        self.assertEqual(0, report["counts"]["error"])

    def test_name_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_skill(root, "unified-search", "wrong-name")
            report = MODULE.build_report(root, False)
        codes = {finding["code"] for finding in report["findings"]}
        self.assertIn("child-name-mismatch", codes)

    def test_no_private_state_probes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = MODULE.build_report(Path(directory), False)
        self.assertFalse(report["privacy"]["credentials_read"])
        self.assertFalse(report["privacy"]["browser_state_read"])
        self.assertFalse(report["privacy"]["private_collections_read"])
        self.assertFalse(report["privacy"]["network_requests_made"])


if __name__ == "__main__":
    unittest.main()
