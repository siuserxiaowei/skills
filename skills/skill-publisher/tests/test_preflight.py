import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "preflight.py"
SPEC = importlib.util.spec_from_file_location("preflight", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_skill(root: Path, directory="demo-skill", name="demo-skill") -> Path:
    skill = root / directory
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Use when the user asks for a deterministic demo.\n---\n\n# Demo\n\nDo the demo.\n",
        encoding="utf-8",
    )
    return skill


class PreflightTests(unittest.TestCase):
    def codes(self, report):
        return {item["code"] for item in report["findings"]}

    def test_clean_private_standalone_has_no_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            report = MODULE.preflight(skill, "private", None)
        self.assertEqual(0, report["counts"]["blocker"])
        self.assertEqual(1, report["summary"]["skill_count"])

    def test_name_must_match_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory), name="other-skill")
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("name-directory-mismatch", self.codes(report))

    def test_invalid_name_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory), name="Bad_Name")
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("name-invalid", self.codes(report))

    def test_public_release_does_not_invent_license(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            report = MODULE.preflight(skill, "public", None)
            self.assertFalse((skill / "LICENSE").exists())
        self.assertIn("public-license-unresolved", self.codes(report))

    def test_secret_filename_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            (skill / ".env").write_text("API_TOKEN=real-value\n", encoding="utf-8")
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("secret-file", self.codes(report))

    def test_private_key_content_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            marker = "-----BEGIN " + "PRIVATE KEY-----"
            (skill / "notes.txt").write_text(marker + "\nnot-a-real-key\n", encoding="utf-8")
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("private-key", self.codes(report))

    @unittest.skipIf(os.name == "nt", "symlink semantics differ on Windows")
    def test_symlink_is_blocked_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            outside = Path(directory) / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            (skill / "linked.txt").symlink_to(outside)
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("symlink", self.codes(report))
        self.assertFalse(any(item["path"] == "linked.txt" for item in report["files"]))

    def test_archive_is_visible_as_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            (skill / "bundle.zip").write_bytes(b"not really an archive")
            report = MODULE.preflight(skill, "private", None)
        self.assertIn("archive", self.codes(report))

    def test_json_cli_contains_hash_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = write_skill(Path(directory))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(skill), "--visibility", "private", "--format", "json", "--fail-on", "never"],
                text=True,
                capture_output=True,
                check=False,
            )
        payload = json.loads(result.stdout)
        self.assertEqual(0, result.returncode)
        self.assertEqual(64, len(payload["files"][0]["sha256"]))


if __name__ == "__main__":
    unittest.main()
