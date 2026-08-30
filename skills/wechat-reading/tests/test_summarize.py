import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "summarize.py"
SPEC = importlib.util.spec_from_file_location("summarize", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SummarizeTests(unittest.TestCase):
    def test_shelf_components_and_unknown_privacy(self):
        result = MODULE.shelf_summary(
            {
                "books": [{"secret": 0}, {"secret": 1}, {}],
                "albums": [{"albumInfoExtra": {"secret": 0}}, {"albumInfoExtra": {}}],
                "mp": {"name": "articles"},
            }
        )
        self.assertEqual(6, result["visible_entries"])
        self.assertEqual({"public": 2, "private": 1, "unknown": 3}, result["privacy"])

    def test_article_collection_is_not_called_a_book(self):
        result = MODULE.shelf_summary({"books": [], "albums": [], "mp": {"x": 1}})
        self.assertEqual(0, result["electronic_book_entries"])
        self.assertEqual(1, result["article_collection_entries"])

    def test_notebook_total_reconciles(self):
        result = MODULE.notebooks_summary(
            {
                "totalBookCount": 1,
                "totalNoteCount": 6,
                "hasMore": 0,
                "books": [
                    {
                        "bookId": "b1",
                        "book": {"title": "Demo"},
                        "reviewCount": 1,
                        "noteCount": 2,
                        "bookmarkCount": 3,
                    }
                ],
            }
        )
        self.assertEqual(6, result["computed_total_note_count"])
        self.assertTrue(result["reconciles"])

    def test_missing_notebook_count_stays_unknown(self):
        result = MODULE.notebooks_summary(
            {"totalNoteCount": 4, "books": [{"reviewCount": 1, "noteCount": 2}]}
        )
        self.assertIsNone(result["computed_total_note_count"])
        self.assertIsNone(result["reconciles"])

    def test_reading_time_uses_returned_seconds(self):
        result = MODULE.reading_summary(
            {"baseTime": 123, "totalReadTime": 3661, "readDays": 2, "dayAverageReadTime": 1830}
        )
        self.assertEqual("1h 1m 1s", result["total_read_time_human"])
        self.assertEqual("30m 30s", result["natural_day_average_human"])

    def test_negative_time_stays_unknown(self):
        result = MODULE.reading_summary({"totalReadTime": -1})
        self.assertIsNone(result["total_read_time_seconds"])


if __name__ == "__main__":
    unittest.main()
