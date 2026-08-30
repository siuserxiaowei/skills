import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "build_deck.py"
EXAMPLE = Path(__file__).parents[1] / "assets" / "deck.example.json"
SPEC = importlib.util.spec_from_file_location("build_deck", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

PNG = b"\x89PNG\r\n\x1a\n" + b"illustration"


class DeckBuilderTests(unittest.TestCase):
    def make_tree(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        return temp, root

    def base_spec(self):
        return {
            "version": 1,
            "title": "A bounded decision",
            "language": "en-US",
            "meta": {"audience": "Leadership", "occasion": "Review", "outcome": "Choose one experiment"},
            "theme": {
                "font_pair": "modern",
                "background": "#f5f6f8",
                "panel": "#ffffff",
                "text": "#16191f",
                "muted": "#505966",
                "accent": "#174f91",
                "line": "#b9c2cc",
            },
            "slides": [
                {"layout": "cover", "title": "A bounded decision", "subtitle": "Evidence before scale", "notes": "Pause here."},
                {"layout": "bullets", "title": "What we know", "items": ["The need is real", "The mechanism is uncertain"]},
                {"layout": "closing", "title": "Run the smallest test", "body": "Review after two weeks."},
            ],
        }

    def write_spec(self, root, data):
        path = root / "deck.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def codes(self, report):
        return {item["rule_id"] for item in report["findings"]}

    def test_shipped_example_is_valid(self):
        report = MODULE.validate_spec(EXAMPLE)
        self.assertTrue(report["ok"], report["findings"])
        self.assertEqual(report["summary"], {"error": 0, "warning": 0})

    def test_generated_deck_escapes_content_and_has_no_remote_runtime(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["slides"][0]["subtitle"] = "</script><script>alert(1)</script>"
        path = self.write_spec(root, data)
        report = MODULE.validate_spec(path)
        html = MODULE.build_html(path, report["spec"], report["theme"])
        self.assertNotIn("</script><script>alert(1)</script>", html)
        self.assertIn("&lt;/script&gt;", html)
        self.assertNotIn("fonts.googleapis", html)
        self.assertNotRegex(html, r'<(?:script|link)[^>]+src=["\']https?://')

    def test_generated_runtime_has_accessible_controls_and_progressive_slides(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        path = self.write_spec(root, self.base_spec())
        report = MODULE.validate_spec(path)
        html = MODULE.build_html(path, report["spec"], report["theme"])
        self.assertIn('aria-roledescription="carousel"', html)
        self.assertEqual(html.count('aria-roledescription="slide"'), 3)
        self.assertIn('aria-label="Previous slide"', html)
        self.assertIn("prefers-reduced-motion", html)
        section_tags = re.findall(r"<section class=\"slide[^>]+>", html)
        self.assertTrue(section_tags)
        self.assertTrue(all(" hidden" not in tag for tag in section_tags))

    def test_unsupported_layout_and_invalid_language_fail(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["language"] = "english!"
        data["slides"][1]["layout"] = "timeline"
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertTrue({"deck-language", "slide-layout"}.issubset(self.codes(report)))

    def test_theme_contrast_and_unknown_token_fail(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["theme"]["text"] = "#eeeeee"
        data["theme"]["shadow"] = "#000000"
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertTrue({"theme-contrast", "theme-key"}.issubset(self.codes(report)))

    def test_bullet_and_metric_density_are_bounded(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["slides"][1]["items"] = [str(index) for index in range(7)]
        data["slides"].append({"layout": "metrics", "title": "Too many", "metrics": [{"value": str(i), "label": "Metric"} for i in range(5)]})
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertTrue({"bullet-items", "metrics"}.issubset(self.codes(report)))

    def test_long_copy_warns_without_failing_preflight(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["slides"][1]["items"][0] = "evidence " * 30
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertTrue(report["ok"])
        self.assertIn("bullet-length", self.codes(report))

    def test_image_needs_safe_path_alt_rights_and_description(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["slides"][1] = {"layout": "image", "title": "Figure", "image": {"path": "../outside.png", "rights": "unknown"}}
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertTrue({"image-path", "image-alt", "image-rights", "image-description"}.issubset(self.codes(report)))

    def test_symlink_image_is_rejected(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "real.png").write_bytes(PNG)
        (root / "linked.png").symlink_to(root / "real.png")
        data = self.base_spec()
        data["slides"][1] = {"layout": "image", "title": "Figure", "image": {"path": "linked.png", "alt": "Chart", "description": "Two bars.", "rights": "user-provided"}}
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertIn("image-symlink", self.codes(report))

    def test_valid_image_is_embedded_with_hash_inventory(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "figure.png").write_bytes(PNG)
        data = self.base_spec()
        data["slides"][1] = {"layout": "image", "title": "Figure", "image": {"path": "figure.png", "alt": "Two bars compare A and B", "description": "A is twice the height of B.", "rights": "user-provided"}}
        path = self.write_spec(root, data)
        report = MODULE.validate_spec(path)
        self.assertTrue(report["ok"], report["findings"])
        self.assertEqual(len(report["inventory"][0]["sha256"]), 64)
        html = MODULE.build_html(path, report["spec"], report["theme"])
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("Figure description", html)

    def test_current_source_needs_as_of_date(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["slides"][1]["sources"] = [{"label": "Official dashboard", "url": "https://example.com", "current": True}]
        report = MODULE.validate_spec(self.write_spec(root, data))
        self.assertIn("source-date", self.codes(report))

    def test_rtl_language_sets_rtl_direction(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.base_spec()
        data["language"] = "ar"
        path = self.write_spec(root, data)
        report = MODULE.validate_spec(path)
        html = MODULE.build_html(path, report["spec"], report["theme"])
        self.assertIn('dir="rtl"', html)

    def test_existing_output_requires_force(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        output = root / "deck.html"
        output.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            MODULE.write_output(output, "new", False)
        self.assertEqual(output.read_text(encoding="utf-8"), "keep")
        MODULE.write_output(output, "new", True)
        self.assertEqual(output.read_text(encoding="utf-8"), "new")

    def test_cli_json_build_reports_output_hash(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        spec = self.write_spec(root, self.base_spec())
        output = root / "deck.html"
        result = subprocess.run([sys.executable, str(SCRIPT), str(spec), "--out", str(output), "--format", "json"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["output"], str(output.resolve()))
        self.assertEqual(len(report["output_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
