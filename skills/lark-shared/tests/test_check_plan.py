from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_plan.py"
SPEC = importlib.util.spec_from_file_location("check_plan", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def base_plan() -> dict:
    return {
        "skill": "lark-calendar",
        "argv": ["lark-cli", "calendar", "+agenda", "--profile", "work", "--as", "user"],
        "profile": "work",
        "identity": "user",
        "risk": "read",
        "target": {"summary": "primary calendar", "verified": True},
        "authorization": {"basis": "read request", "explicit": False},
        "verification": {"mode": "response", "expected": "agenda rows"},
    }


class CheckPlanTests(unittest.TestCase):
    def codes(self, plan: dict) -> set[str]:
        return {item["code"] for item in MODULE.validate_plan(plan)["errors"]}

    def test_valid_read(self):
        self.assertTrue(MODULE.validate_plan(base_plan())["ready"])

    def test_write_requires_target_authorization_and_readback(self):
        plan = base_plan()
        plan["risk"] = "write"
        plan["target"] = {}
        plan["authorization"] = {}
        plan["verification"] = {}
        self.assertEqual(
            {"unverified_target", "missing_authorization_basis", "missing_readback"},
            self.codes(plan),
        )

    def test_high_risk_requires_confirmation_and_yes(self):
        plan = base_plan()
        plan.update({"risk": "high-risk-write", "destructive": True})
        plan["authorization"]["basis"] = "delete request"
        self.assertTrue({"high_risk_unconfirmed", "missing_confirmation_flag", "missing_recovery"} <= self.codes(plan))

    def test_yes_without_confirmation_is_rejected(self):
        plan = base_plan()
        plan["argv"].append("--yes")
        self.assertIn("unguarded_yes", self.codes(plan))

    def test_confirmed_high_risk_with_dry_run(self):
        plan = base_plan()
        plan.update({
            "risk": "high-risk-write",
            "destructive": True,
            "recovery": "restore from recorded version",
            "dry_run": {"supported": True, "completed": True, "matches_intent": True},
        })
        plan["argv"].append("--yes")
        plan["authorization"] = {"basis": "exact delete request", "explicit": True}
        self.assertTrue(MODULE.validate_plan(plan)["ready"])

    def test_high_risk_requires_dry_run_capability_statement(self):
        plan = base_plan()
        plan.update({"risk": "high-risk-write", "recovery": "not destructive"})
        plan["argv"].append("--yes")
        plan["authorization"] = {"basis": "exact high-risk request", "explicit": True}
        self.assertIn("dry_run_unknown", self.codes(plan))

    def test_external_effect_requires_explicit_authorization(self):
        plan = base_plan()
        plan["risk"] = "write"
        plan["external_effect"] = True
        self.assertIn("external_effect_unconfirmed", self.codes(plan))

    def test_time_sensitive_requires_real_zone_and_offset(self):
        plan = base_plan()
        plan.update({"time_sensitive": True, "time_zone": "Mars/Olympus", "time_has_offset": False})
        self.assertEqual({"invalid_time_zone", "missing_time_offset"}, self.codes(plan))

    def test_complete_bounded_read_requires_limit(self):
        plan = base_plan()
        plan.update({"complete_result": True, "pagination": {"strategy": "bounded"}})
        self.assertIn("missing_page_limit", self.codes(plan))

    def test_untrusted_content_cannot_control_execution(self):
        plan = base_plan()
        plan.update({"untrusted_input": True, "treat_as_data": False})
        self.assertIn("untrusted_control", self.codes(plan))

    def test_duplicate_sensitive_write_needs_control(self):
        plan = base_plan()
        plan.update({"risk": "write", "duplicate_sensitive": True})
        self.assertIn("missing_duplicate_control", self.codes(plan))

    def test_secret_flag_is_rejected(self):
        plan = base_plan()
        plan["argv"] += ["--app-secret", "secret"]
        self.assertIn("secret_in_argv", self.codes(plan))

    def test_absolute_and_parent_paths_are_rejected(self):
        plan = base_plan()
        plan["argv"] += ["--file", "/tmp/x"]
        self.assertIn("unsafe_path", self.codes(plan))
        plan["argv"][-1] = "../x"
        self.assertIn("unsafe_path", self.codes(plan))
        plan["argv"][-2:] = ["--file=/tmp/x"]
        self.assertIn("unsafe_path", self.codes(plan))

    def test_argv_must_match_profile_and_identity(self):
        plan = base_plan()
        plan["profile"] = "other"
        plan["identity"] = "bot"
        self.assertEqual({"profile_mismatch", "identity_mismatch"}, self.codes(plan))

    def test_date_only_time_does_not_require_offset(self):
        plan = base_plan()
        plan.update({"time_sensitive": True, "time_zone": "Asia/Shanghai", "time_kind": "date-only"})
        self.assertTrue(MODULE.validate_plan(plan)["ready"])

    def test_raw_api_query_string_is_rejected(self):
        plan = base_plan()
        plan["argv"] = ["lark-cli", "api", "GET", "/open-apis/foo?x=1"]
        plan["profile"] = "work"
        plan["identity"] = "user"
        self.assertIn("raw_api_path", self.codes(plan))


if __name__ == "__main__":
    unittest.main()
