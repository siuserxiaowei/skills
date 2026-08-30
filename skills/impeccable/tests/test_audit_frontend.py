import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit_frontend.py"
SPEC = importlib.util.spec_from_file_location("audit_frontend", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


CLEAN_HTML = """<!doctype html>
<html lang="en"><head><meta name="viewport" content="width=device-width"><title>Account</title></head>
<body><main><h1>Account</h1><img src="avatar.webp" alt="" width="80" height="80">
<label for="name">Name</label><input id="name"><button type="submit">Save</button></main></body></html>
"""


class FrontendAuditTests(unittest.TestCase):
    def make_tree(self, files):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return temp, root

    def codes(self, report):
        return {item["rule_id"] for item in report["findings"]}

    def test_clean_document_has_no_findings(self):
        temp, root = self.make_tree({"index.html": CLEAN_HTML})
        self.addCleanup(temp.cleanup)
        report = MODULE.audit(root)
        self.assertEqual(report["summary"]["findings"], {"high": 0, "medium": 0, "low": 0})

    def test_document_metadata_image_and_control_findings(self):
        source = "<html><head></head><body><img src='x.png'><button><svg></svg></button><input></body></html>"
        temp, root = self.make_tree({"index.html": source})
        self.addCleanup(temp.cleanup)
        codes = self.codes(MODULE.audit(root))
        self.assertTrue({"document-language", "document-title", "document-viewport", "image-alt", "image-dimensions", "button-name", "form-control-label"}.issubset(codes))

    def test_jsx_clickable_div_and_positive_tabindex(self):
        source = "export const X=()=> <><div onClick={go}>Go</div><span tabIndex={3}>Later</span><img src={url} /></>"
        temp, root = self.make_tree({"View.tsx": source})
        self.addCleanup(temp.cleanup)
        codes = self.codes(MODULE.audit(root))
        self.assertIn("clickable-noncontrol", codes)
        self.assertIn("positive-tabindex", codes)
        self.assertIn("image-alt", codes)

    def test_accessible_names_and_wrapped_label_pass(self):
        source = "<label>Query <input type='search'></label><button aria-label='Close'><svg></svg></button><a href='/'><img alt='Home' src='h.png' width='1' height='1'></a>"
        temp, root = self.make_tree({"View.jsx": source})
        self.addCleanup(temp.cleanup)
        codes = self.codes(MODULE.audit(root))
        self.assertNotIn("form-control-label", codes)
        self.assertNotIn("button-name", codes)
        self.assertNotIn("a-name", codes)

    def test_dynamic_control_name_is_left_for_rendered_verification(self):
        source = "export const Nav=({item}) => <a href={item.href}><span>{item.icon}</span><span>{item.label}</span></a>"
        temp, root = self.make_tree({"Nav.tsx": source})
        self.addCleanup(temp.cleanup)
        self.assertNotIn("a-name", self.codes(MODULE.audit(root)))

    def test_css_focus_transition_motion_and_width_findings(self):
        source = ".hero{outline:none;transition:all .2s;animation:fade 1s;width:1800px;font-size:10px;overflow-x:hidden;z-index:20000}"
        temp, root = self.make_tree({"app.css": source})
        self.addCleanup(temp.cleanup)
        codes = self.codes(MODULE.audit(root))
        self.assertTrue({"focus-outline", "transition-all", "reduced-motion", "fixed-wide", "tiny-text", "overflow-mask", "z-index-scale"}.issubset(codes))

    def test_reduced_motion_branch_suppresses_file_level_warning(self):
        source = ".item{transition:transform .2s}@media (prefers-reduced-motion:reduce){.item{transition:none}}"
        temp, root = self.make_tree({"app.css": source})
        self.addCleanup(temp.cleanup)
        self.assertNotIn("reduced-motion", self.codes(MODULE.audit(root)))

    def test_duplicate_id_and_hidden_focusable(self):
        source = CLEAN_HTML.replace("</main>", "<div id='x'></div><div id='x'></div><button aria-hidden='true'>Hidden</button></main>")
        temp, root = self.make_tree({"index.html": source})
        self.addCleanup(temp.cleanup)
        codes = self.codes(MODULE.audit(root))
        self.assertIn("duplicate-id", codes)
        self.assertIn("hidden-focusable", codes)

    def test_color_drift_is_low_confidence(self):
        colors = "".join(f".c{i}{{color:#{i:06x}}}" for i in range(1, 15))
        temp, root = self.make_tree({"tokens.css": colors})
        self.addCleanup(temp.cleanup)
        item = next(item for item in MODULE.audit(root)["findings"] if item["rule_id"] == "color-token-drift")
        self.assertEqual(item["severity"], "low")
        self.assertEqual(item["confidence"], "low")

    def test_symlink_and_large_file_are_skipped(self):
        temp, root = self.make_tree({"real.html": CLEAN_HTML, "large.css": "x" * 100})
        self.addCleanup(temp.cleanup)
        (root / "link.html").symlink_to(root / "real.html")
        report = MODULE.audit(root, max_bytes=50)
        reasons = {item["reason"] for item in report["skipped"]}
        self.assertIn("symlink not followed", reasons)
        self.assertIn("file exceeds 50 bytes", reasons)

    def test_fail_threshold(self):
        source = "<html><head></head><body></body></html>"
        temp, root = self.make_tree({"index.html": source})
        self.addCleanup(temp.cleanup)
        report = MODULE.audit(root)
        self.assertTrue(MODULE.should_fail(report, "high"))
        self.assertFalse(MODULE.should_fail(report, "never"))

    def test_cli_json_output(self):
        temp, root = self.make_tree({"index.html": CLEAN_HTML})
        self.addCleanup(temp.cleanup)
        result = subprocess.run([sys.executable, str(SCRIPT), str(root), "--format", "json", "--fail-on", "high"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["summary"]["files_scanned"], 1)


if __name__ == "__main__":
    unittest.main()
