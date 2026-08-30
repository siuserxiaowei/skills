from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


history = load("analyze_history")
downloads = load("download_urls")
doctor = load("doctor")
service = load("start_wxdown_service")


class HistoryTests(unittest.TestCase):
    def test_normalization_deduplicates_and_marks_original(self):
        rows = [
            {"url": "https://mp.weixin.qq.com/s/a", "title": "A", "create_time": 10, "itemidx": 1, "msgid": "m1", "raw": {"copyright_type": 1, "copyright_stat": 1}},
            {"url": "https://mp.weixin.qq.com/s/a", "title": "duplicate", "create_time": 9},
            {"url": "https://mp.weixin.qq.com/s/b", "title": "B", "create_time": 8, "itemidx": 2, "msgid": "m1", "raw": {}},
        ]
        normalized, duplicates = history.normalize(rows)
        self.assertEqual(2, len(normalized))
        self.assertEqual(1, len(duplicates))
        self.assertTrue(normalized[0]["is_original"])
        report = history.summary(3, normalized, duplicates)
        self.assertEqual(1, report["publish_groups"])
        self.assertEqual(2, report["expanded_articles"])


class DownloadTests(unittest.TestCase):
    def test_collect_urls_is_ordered_and_deduplicated(self):
        values = ["first https://mp.weixin.qq.com/s/a", "again https://mp.weixin.qq.com/s/a and https://mp.weixin.qq.com/s/b"]
        self.assertEqual(
            ["https://mp.weixin.qq.com/s/a", "https://mp.weixin.qq.com/s/b"],
            downloads.collect_urls(values, []),
        )

    def test_safe_stem_removes_path_characters(self):
        self.assertEqual("one_two", downloads.safe_stem("one/two"))


class DoctorTests(unittest.TestCase):
    def test_report_does_not_claim_private_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = doctor.build_report(root / "exporter", root / "service", "https://example.invalid", False)
        self.assertFalse(report["privacy"]["wechat_launched"])
        self.assertFalse(report["privacy"]["credentials_read"])
        self.assertFalse(report["privacy"]["proxy_settings_changed"])


class ServiceTests(unittest.TestCase):
    def test_proxy_environment_is_removed_by_default(self):
        previous = os.environ.get("HTTP_PROXY")
        os.environ["HTTP_PROXY"] = "http://example.invalid"
        try:
            self.assertNotIn("HTTP_PROXY", service.sanitized_environment(False))
            self.assertEqual("http://example.invalid", service.sanitized_environment(True)["HTTP_PROXY"])
        finally:
            if previous is None:
                os.environ.pop("HTTP_PROXY", None)
            else:
                os.environ["HTTP_PROXY"] = previous

    def test_ports_are_bounded(self):
        self.assertEqual(65000, service.valid_port("65000"))
        with self.assertRaises(Exception):
            service.valid_port("80")


if __name__ == "__main__":
    unittest.main()
