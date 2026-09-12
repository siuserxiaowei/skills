"""REGRESSION_FIXTURE: blank CSV rows must not crash parsing."""

import csv
import io
import unittest


def parse_rows(raw: str) -> list[list[str]]:
    return [row for row in csv.reader(io.StringIO(raw)) if any(cell.strip() for cell in row)]


class EmptyLineRegressionTest(unittest.TestCase):
    def test_blank_lines_are_ignored(self) -> None:
        self.assertEqual(parse_rows("name,value\n\nalpha,1\n"), [["name", "value"], ["alpha", "1"]])


if __name__ == "__main__":
    unittest.main()
