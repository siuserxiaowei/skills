import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_delivery.py"
STARTER = Path(__file__).parents[1] / "assets" / "editorial-starter.html"
SPEC = importlib.util.spec_from_file_location("validate_delivery", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

HTML = """<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Review</title></head><body><main><h1>Review</h1><img src="x.png" alt="" width="20" height="20"></main></body></html>"""
PNG = b"\x89PNG\r\n\x1a\n" + b"evidence"
PDF = b"%PDF-1.7\n% test artifact"


class DeliveryValidationTests(unittest.TestCase):
    def make_tree(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "review.html").write_text(HTML, encoding="utf-8")
        (root / "review.pdf").write_bytes(PDF)
        evidence = root / "evidence"
        evidence.mkdir()
        (evidence / "page-1.png").write_bytes(PNG)
        (root / "notes.md").write_text("source", encoding="utf-8")
        return temp, root

    def manifest(self):
        return {
            "version": 1,
            "status": "verified",
            "artifact": {
                "kind": "report",
                "title": "Review",
                "language": "en-US",
                "audience": "Leadership",
                "purpose": "Choose priorities",
            },
            "outputs": [
                {"path": "review.html", "format": "html", "editable": True},
                {"path": "review.pdf", "format": "pdf", "editable": False},
            ],
            "sources": [{"kind": "user-file", "locator": "notes.md", "as_of": "2026-08-30"}],
            "assets": [],
            "verification": {
                "gaps": [],
                "content_reviewed": True,
                "renders": [{
                    "output": "review.pdf",
                    "tool": "browser print",
                    "pages": 1,
                    "reviewed_pages": [1],
                    "evidence": ["evidence/page-1.png"],
                }],
                "accessibility": {
                    "html_keyboard": "not-applicable",
                    "html_structure": "tested",
                    "pdf": "unknown",
                    "notes": "No PDF/UA claim.",
                },
            },
        }

    def write_manifest(self, root, data):
        path = root / "delivery.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def codes(self, report):
        return {item["rule_id"] for item in report["findings"]}

    def test_valid_verified_report_has_hash_inventory(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        report = MODULE.validate(self.write_manifest(root, self.manifest()))
        self.assertTrue(report["ok"], report["findings"])
        self.assertEqual(len(report["inventory"]), 3)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in report["inventory"]))

    def test_filled_neutral_starter_passes_html_checks(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        filled = re.sub(r"\[\[REPLACE:[^\]]+\]\]", "Published content", STARTER.read_text(encoding="utf-8"))
        (root / "review.html").write_text(filled, encoding="utf-8")
        report = MODULE.validate(self.write_manifest(root, self.manifest()))
        html_rules = {item["rule_id"] for item in report["findings"] if item["rule_id"].startswith("html-")}
        self.assertEqual(html_rules, set(), report["findings"])

    def test_manifest_root_must_be_object(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        report = MODULE.validate(self.write_manifest(root, []))
        self.assertIn("manifest-shape", self.codes(report))

    def test_unsafe_and_missing_paths_fail(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["outputs"][0]["path"] = "../review.html"
        data["outputs"][1]["path"] = "missing.pdf"
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertIn("output-path", self.codes(report))

    def test_missing_user_file_source_fails(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["sources"][0]["locator"] = "missing-notes.md"
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertIn("source-path", self.codes(report))

    def test_symlink_asset_is_rejected(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "logo.svg").write_text("<svg/>", encoding="utf-8")
        (root / "linked.svg").symlink_to(root / "logo.svg")
        data = self.manifest()
        data["assets"] = [{"path": "linked.svg", "role": "logo", "rights": "user-provided", "alt": "Logo"}]
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertIn("asset-path", self.codes(report))

    def test_duplicate_output_and_suffix_mismatch_fail(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["outputs"].append({"path": "review.pdf", "format": "html", "editable": True})
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue({"output-duplicate", "output-suffix"}.issubset(self.codes(report)))

    def test_file_signature_must_match_declared_format(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "review.pdf").write_text("not a PDF", encoding="utf-8")
        report = MODULE.validate(self.write_manifest(root, self.manifest()))
        self.assertIn("file-signature", self.codes(report))

    def test_html_structure_markers_and_images_are_checked(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "review.html").write_text("<html><head><title></title></head><body><img src='x'>[[TODO: copy]]</body></html>", encoding="utf-8")
        report = MODULE.validate(self.write_manifest(root, self.manifest()))
        self.assertTrue({"html-language", "html-charset", "html-title", "html-main", "html-h1", "html-marker", "html-image-alt", "html-image-size"}.issubset(self.codes(report)))

    def test_verified_landing_page_needs_narrow_and_wide_evidence(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["artifact"]["kind"] = "landing-page"
        data["outputs"] = [{"path": "review.html", "format": "html", "editable": True}]
        data["verification"]["renders"] = [{"output": "review.html", "tool": "Chromium", "viewports": [{"width": 800, "height": 600, "screenshot": "evidence/page-1.png"}]}]
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue({"render-narrow", "render-wide"}.issubset(self.codes(report)))

    def test_verified_landing_page_accepts_two_viewports(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "evidence" / "wide.png").write_bytes(PNG)
        data = self.manifest()
        data["artifact"]["kind"] = "landing-page"
        data["outputs"] = [{"path": "review.html", "format": "html", "editable": True}]
        data["verification"]["renders"] = [{
            "output": "review.html", "tool": "Chromium",
            "viewports": [
                {"width": 375, "height": 812, "screenshot": "evidence/page-1.png"},
                {"width": 1280, "height": 900, "screenshot": "evidence/wide.png"},
            ],
        }]
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue(report["ok"], report["findings"])

    def test_pdf_review_must_cover_each_page_and_real_image_evidence(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        render = data["verification"]["renders"][0]
        render.update({"pages": 2, "reviewed_pages": [1], "evidence": ["notes.md", "evidence/page-1.png"]})
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue({"render-page-review", "evidence-image"}.issubset(self.codes(report)))

    def test_font_asset_needs_rights_license_source_and_fallback(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        (root / "font.woff2").write_bytes(b"font")
        data = self.manifest()
        data["assets"] = [{"path": "font.woff2", "role": "font", "rights": "unknown"}]
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue({"asset-rights", "font-license", "font-source", "font-offline_fallback"}.issubset(self.codes(report)))

    def test_verified_gaps_and_unreviewed_content_fail(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["verification"]["gaps"] = ["missing source"]
        data["verification"]["content_reviewed"] = False
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue({"verified-gaps", "content-review"}.issubset(self.codes(report)))

    def test_draft_can_record_gaps_without_render_evidence(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["status"] = "draft"
        data["outputs"] = [{"path": "review.html", "format": "html", "editable": True}]
        data["verification"].update({"gaps": ["awaiting approval"], "content_reviewed": False, "renders": []})
        report = MODULE.validate(self.write_manifest(root, data))
        self.assertTrue(report["ok"], report["findings"])

    def test_external_source_without_date_warns_and_cli_threshold_works(self):
        temp, root = self.make_tree()
        self.addCleanup(temp.cleanup)
        data = self.manifest()
        data["sources"] = [{"kind": "primary-url", "locator": "https://example.com"}]
        path = self.write_manifest(root, data)
        report = MODULE.validate(path)
        self.assertIn("source-date", self.codes(report))
        result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--format", "json", "--fail-on", "warning"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["summary"]["warning"], 1)


if __name__ == "__main__":
    unittest.main()
