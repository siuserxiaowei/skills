from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_originality.py"
SPEC = importlib.util.spec_from_file_location("audit_originality", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class OriginalityAuditTests(unittest.TestCase):
    def fixture(self, rebuilt=("sample",), new_original=()):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)

        all_skills = sorted(set(rebuilt) | set(new_original))
        for skill in all_skills:
            skill_root = root / "skills" / skill
            skill_root.mkdir(parents=True)
            skill_root.joinpath("SKILL.md").write_text(
                "# Baseline\n\n" + " ".join(f"source_token_{index}" for index in range(100)),
                encoding="utf-8",
            )
        (root / "SKILL_PROVENANCE.json").write_text(
            json.dumps(
                {
                    "origin_groups": {
                        "independently_rebuilt": list(rebuilt),
                        "new_original": list(new_original),
                    }
                }
            ),
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.name=Originality Test",
                "-c",
                "user.email=originality@example.invalid",
                "commit",
                "-q",
                "-m",
                "baseline",
            ],
            check=True,
        )
        baseline = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        manifest_path = root / "SKILL_PROVENANCE.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["originality_assurance"] = {"historical_baseline_commit": baseline}
        manifest["new_original_evidence"] = {
            skill: {
                "first_commit": baseline,
                "anchor": f"skills/{skill}/SKILL.md",
            }
            for skill in new_original
        }
        manifest["reviewed_similarity_findings"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return root, baseline

    def test_exact_nontrivial_file_is_material(self):
        root, baseline = self.fixture()
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["material_findings"], 1)
        self.assertIn("exact-baseline-blob", report["findings"][0]["code"])
        self.assertEqual(MODULE.exit_code(report, "material"), 1)

    def test_independent_rewrite_passes(self):
        root, baseline = self.fixture()
        (root / "skills" / "sample" / "SKILL.md").write_text(
            "# New design\n\n" + " ".join(f"independent_term_{index}" for index in range(100)),
            encoding="utf-8",
        )
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["material_findings"], 0)
        self.assertEqual(report["summary"]["review_findings"], 0)
        self.assertEqual(MODULE.exit_code(report, "material"), 0)

    def test_long_copied_excerpt_is_material_without_exact_file_match(self):
        root, baseline = self.fixture()
        copied_excerpt = " ".join(f"source_token_{index}" for index in range(70))
        independent = " ".join(f"independent_term_{index}" for index in range(700))
        (root / "skills" / "sample" / "SKILL.md").write_text(
            f"# New wrapper\n\n{independent}\n\n{copied_excerpt}", encoding="utf-8"
        )
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["material_findings"], 1)
        self.assertIn("long-token-run", report["findings"][0]["code"])
        self.assertNotIn("exact-baseline-blob", report["findings"][0]["code"])

    def test_short_common_sequence_is_review_not_material(self):
        root, baseline = self.fixture()
        shared = " ".join(f"source_token_{index}" for index in range(16))
        independent = " ".join(f"independent_term_{index}" for index in range(180))
        (root / "skills" / "sample" / "SKILL.md").write_text(
            f"# New design\n\n{shared}\n\n{independent}", encoding="utf-8"
        )
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["material_findings"], 0)
        self.assertEqual(report["summary"]["review_findings"], 1)
        self.assertEqual(report["summary"]["unreviewed_review_findings"], 1)
        self.assertEqual(MODULE.exit_code(report, "material"), 0)
        self.assertEqual(MODULE.exit_code(report, "unreviewed"), 1)
        self.assertEqual(MODULE.exit_code(report, "review"), 1)

    def test_hash_bound_review_record_resolves_review_gate(self):
        root, baseline = self.fixture()
        shared = " ".join(f"source_token_{index}" for index in range(16))
        independent = " ".join(f"independent_term_{index}" for index in range(180))
        target = root / "skills" / "sample" / "SKILL.md"
        target.write_text(f"# New design\n\n{shared}\n\n{independent}", encoding="utf-8")
        manifest_path = root / "SKILL_PROVENANCE.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["reviewed_similarity_findings"] = [
            {
                "skill": "sample",
                "path": "skills/sample/SKILL.md",
                "sha256": MODULE.sha256(target.read_bytes()),
                "disposition": "necessary-interface-expression",
                "rationale": "Synthetic common sequence used to exercise the review workflow.",
            }
        ]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["adjudicated_review_findings"], 1)
        self.assertEqual(report["summary"]["unreviewed_review_findings"], 0)
        self.assertEqual(MODULE.exit_code(report, "unreviewed"), 0)

        target.write_text(target.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
        stale_report = MODULE.audit_repository(root, baseline)
        self.assertEqual(stale_report["summary"]["unreviewed_review_findings"], 1)
        self.assertEqual(stale_report["summary"]["stale_review_records"], 1)
        self.assertEqual(MODULE.exit_code(stale_report, "unreviewed"), 1)

    def test_new_original_group_is_not_compared_to_import_baseline(self):
        root, baseline = self.fixture(rebuilt=(), new_original=("sample",))
        report = MODULE.audit_repository(root, baseline)
        self.assertEqual(report["summary"]["skills_checked"], 0)
        self.assertEqual(report["summary"]["new_original_lineage_checked"], 1)
        self.assertEqual(report["findings"], [])

    def test_missing_new_original_lineage_is_an_evidence_error(self):
        root, baseline = self.fixture(rebuilt=(), new_original=("sample",))
        manifest_path = root / "SKILL_PROVENANCE.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["new_original_evidence"] = {}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(MODULE.AuditError):
            MODULE.audit_repository(root, baseline)

    def test_missing_baseline_is_an_evidence_error(self):
        root, _baseline = self.fixture()
        with self.assertRaises(MODULE.AuditError):
            MODULE.audit_repository(root, "f" * 40)


if __name__ == "__main__":
    unittest.main()
