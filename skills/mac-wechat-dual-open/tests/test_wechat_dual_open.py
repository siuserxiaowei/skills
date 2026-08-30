import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "wechat_dual_open.py"
SPEC = importlib.util.spec_from_file_location("wechat_dual_open", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class DualOpenTests(unittest.TestCase):
    def test_hex_color(self):
        self.assertEqual((40, 120, 208), MODULE.parse_hex_color("#2878d0"))

    def test_invalid_color(self):
        with self.assertRaises(Exception):
            MODULE.parse_hex_color("blue")

    def test_source_and_target_must_differ(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "WeChat.app"
            with self.assertRaises(MODULE.OperationError):
                MODULE.validate_paths(app, app)

    def test_target_requires_app_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "WeChat.app"
            target = Path(directory) / "copy"
            with self.assertRaises(MODULE.OperationError):
                MODULE.validate_paths(source, target)

    def test_plan_does_not_mutate_missing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "WeChat.app"
            target = Path(directory) / "Second.app"
            result = MODULE.plan(source, target, "com.example.second", ["zh-Hans"])
            self.assertFalse(result["source"]["exists"])
            self.assertFalse(result["target"]["exists"])
            self.assertFalse(result["original_bundle_modified"])
            self.assertFalse(source.exists())
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
