import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_reference_pack.py"
SPEC = importlib.util.spec_from_file_location("validate_reference_pack", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
image_dimensions = MODULE.image_dimensions
validate = MODULE.validate


def write_png(path: Path, width: int = 1440, height: int = 900) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00")


def write_jpeg(path: Path, width: int, height: int) -> None:
    component_data = b"\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    path.write_bytes(b"\xff\xd8\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", height, width) + b"\x03" + component_data + b"\xff\xd9")


def write_webp(path: Path, width: int, height: int) -> None:
    payload = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    path.write_bytes(b"RIFF" + struct.pack("<I", 4 + 8 + len(payload)) + b"WEBPVP8X" + struct.pack("<I", len(payload)) + payload)


def valid_manifest() -> dict:
    return {
        "version": 1,
        "deliverable": "single-concept",
        "brief": {
            "page_kind": "product landing page",
            "audience": "operations teams",
            "goal": "explain the workflow",
            "primary_action": "request a demo",
        },
        "design_system": {
            "colors": "ink, paper, orange accent",
            "typography": "live sans text with a compact display role",
            "grid": "12 columns",
            "shape": "8px controls and square media",
        },
        "viewports": [{"id": "desktop", "width": 1440, "height": 900}],
        "frames": [
            {
                "id": "home-desktop",
                "file": "frames/home.png",
                "viewport": "desktop",
                "scope": "page",
                "job": "resolve hierarchy and hero crop",
                "purpose": "reference",
                "text_strategy": "live-overlay",
                "alt_mode": "descriptive",
                "alt_text": "Desktop homepage reference.",
                "focal_point": [0.7, 0.4],
                "implementation_notes": ["Keep text and controls live."],
                "provenance": "generated from the approved brief",
            }
        ],
    }


class ReferencePackTests(unittest.TestCase):
    def make_pack(self, manifest: dict, width: int = 1440, height: int = 900):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write_png(root / "frames/home.png", width, height)
        path = root / "reference-pack.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return temp, root, path

    def test_valid_pack_has_dimensions_and_hash(self):
        temp, _, path = self.make_pack(valid_manifest())
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertTrue(result["valid"])
        self.assertEqual(result["warnings"], 0)
        self.assertEqual(result["files"][0]["width"], 1440)
        self.assertEqual(len(result["files"][0]["sha256"]), 64)

    def test_jpeg_and_webp_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_jpeg(root / "sample.jpg", 1200, 630)
            write_webp(root / "sample.webp", 390, 844)
            self.assertEqual(image_dimensions(root / "sample.jpg"), (1200, 630))
            self.assertEqual(image_dimensions(root / "sample.webp"), (390, 844))

    def test_missing_file_is_an_error(self):
        manifest = valid_manifest()
        manifest["frames"][0]["file"] = "frames/missing.png"
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertIn("frame.file", {message["code"] for message in result["messages"]})

    def test_parent_traversal_is_rejected(self):
        manifest = valid_manifest()
        manifest["frames"][0]["file"] = "../outside.png"
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertFalse(result["valid"])
        self.assertIn("inside", next(message["message"] for message in result["messages"] if message["code"] == "frame.file"))

    def test_symlink_is_rejected(self):
        manifest = valid_manifest()
        manifest["frames"][0]["file"] = "frames/link.png"
        temp, root, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        (root / "frames/link.png").symlink_to(root / "frames/home.png")
        result = validate(path)
        self.assertFalse(result["valid"])
        self.assertIn("symlink", next(message["message"] for message in result["messages"] if message["code"] == "frame.file"))

    def test_descriptive_media_requires_alt_text(self):
        manifest = valid_manifest()
        manifest["frames"][0]["alt_text"] = ""
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertIn("frame.alt_text", {message["code"] for message in result["messages"]})

    def test_production_asset_requires_rights(self):
        manifest = valid_manifest()
        manifest["frames"][0]["purpose"] = "production-asset"
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertIn("frame.rights", {message["code"] for message in result["messages"]})

    def test_essential_raster_requires_reason_and_warns(self):
        manifest = valid_manifest()
        manifest["frames"][0]["text_strategy"] = "essential-raster"
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        codes = {message["code"] for message in result["messages"]}
        self.assertIn("frame.raster_reason", codes)
        self.assertIn("frame.raster_accessibility", codes)

    def test_responsive_set_requires_narrow_and_desktop_frames(self):
        manifest = valid_manifest()
        manifest["deliverable"] = "responsive-set"
        temp, _, path = self.make_pack(manifest)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertIn("responsive.coverage", {message["code"] for message in result["messages"]})

    def test_aspect_ratio_drift_warns(self):
        temp, _, path = self.make_pack(valid_manifest(), 1024, 1024)
        self.addCleanup(temp.cleanup)
        result = validate(path)
        self.assertTrue(result["valid"])
        self.assertIn("frame.aspect_ratio", {message["code"] for message in result["messages"]})


if __name__ == "__main__":
    unittest.main()
