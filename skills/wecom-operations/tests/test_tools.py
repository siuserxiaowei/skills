from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


smartpage = load("create_smartpage")
doctor = load("doctor")


class SmartPageTests(unittest.TestCase):
    def test_image_inventory_classifies_remote_and_local(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "diagram.png"
            image.write_bytes(b"fixture")
            source = root / "report.md"
            text = "![local](diagram.png)\n![remote](https://example.com/a.png)"
            refs = smartpage.inspect_images(text, source)
        self.assertEqual(["local", "remote"], [item.kind for item in refs])

    def test_replacement_uses_uploaded_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "diagram.png"
            image.write_bytes(b"fixture")
            source = root / "report.md"
            replaced = smartpage.replace_local_images("![alt](diagram.png)", source, {str(image.resolve()): "https://example.com/cdn.png"})
        self.assertEqual("![alt](https://example.com/cdn.png)", replaced)

    def test_business_error_is_rejected(self):
        with self.assertRaises(smartpage.CliError):
            smartpage.unwrap_response('{"errcode": 1, "errmsg": "denied"}')


class DoctorTests(unittest.TestCase):
    def test_metadata_does_not_read_secret_contents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".encryption_key"
            path.write_text("secret-value", encoding="utf-8")
            path.chmod(0o600)
            rows = doctor.configuration_metadata(root)
        self.assertTrue(rows[0]["exists"])
        self.assertTrue(rows[0]["owner_only"])
        self.assertNotIn("secret", str(rows))


if __name__ == "__main__":
    unittest.main()
