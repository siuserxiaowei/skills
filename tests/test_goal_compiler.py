#!/usr/bin/env python3
"""Behavior and security regressions for the Goal Compiler boundary."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"
DEMO_FIXTURES = ROOT / "contest" / "demo-fixtures"
sys.path.insert(0, str(SCRIPTS))

import goal_compiler  # noqa: E402


WEBSITE_REQUEST = "给我做个 AI 网站，越快越好"
TEST_WORKSPACE = Path("/tmp/xiaowei-goal-unit-workspace")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_semantic(name: str) -> dict:
    return goal_compiler.load_semantic_input(FIXTURES / name)


def synthetic_review(metric_id: str) -> dict:
    review = load_fixture("synthetic-approved-review.json")
    review["metric_id"] = metric_id
    return review


def compile_semantic(
    semantic: dict,
    *,
    request: str | None = None,
    workspace_root: Path = TEST_WORKSPACE,
    evidence_bundle: dict | None = None,
) -> dict:
    return goal_compiler.build_contract(
        request or semantic["request"],
        semantic,
        workspace_root=workspace_root,
        evidence_bundle=evidence_bundle,
    )


def set_first_step_content(semantic: dict, content: str) -> None:
    semantic["first_step"]["content_template"] = content
    semantic["first_step"]["content_sha256"] = goal_compiler.sha256_text(content)


class GoalCompilerBoundaryTests(unittest.TestCase):
    def test_compile_requires_complete_semantic_input(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "goal_compiler.py"), "compile", "--request", WEBSITE_REQUEST, "--output", "/tmp/not-created"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--semantic-input", result.stderr)

        missing_workspace = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "goal_compiler.py"),
                "compile",
                "--request",
                WEBSITE_REQUEST,
                "--semantic-input",
                str(DEMO_FIXTURES / "semantic-input.demo.json"),
                "--output",
                "/tmp/not-created",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(missing_workspace.returncode, 2)
        self.assertIn("--workspace-root", missing_workspace.stderr)

    def test_compile_is_deterministic_for_same_agent_payload(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        first = compile_semantic(semantic, request=WEBSITE_REQUEST)
        second = compile_semantic(semantic, request=WEBSITE_REQUEST)
        self.assertEqual(first, second)
        self.assertEqual(first["smart_router"]["task_type"], "website")
        self.assertEqual(first["compiler"]["kind"], "deterministic-cli")
        self.assertFalse(first["semantic_compilation"]["live_ai_claimed"])

    def test_coding_request_rejects_website_semantics(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        coding_request = "修复 CSV parser 忽略空行时崩溃的问题，并增加回归测试"
        semantic["request"] = coding_request
        with self.assertRaisesRegex(goal_compiler.CompilerError, "domain mismatch"):
            compile_semantic(semantic, request=coding_request)

    def test_generic_programming_language_request_routes_as_coding(self) -> None:
        self.assertEqual(
            goal_compiler.infer_request_task_type("写一个 Python 脚本，并为函数增加单元测试"),
            "coding",
        )

    def test_unknown_domain_is_rejected(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        request = "帮我整理这个未定义的事情"
        semantic["request"] = request
        semantic["smart_router"]["task_type"] = "unknown"
        with self.assertRaisesRegex(goal_compiler.CompilerError, "unsupported task type"):
            compile_semantic(semantic, request=request)

    def test_coding_goal_has_no_website_leak_and_dispatches_python(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            contract = compile_semantic(semantic, workspace_root=workspace)
            rendered = goal_compiler.render_goal(contract)
            for forbidden in ("CTA", "15-25 个候选来源", "IdeaSignal", "网站/落地页改版包"):
                self.assertNotIn(forbidden, rendered)

            approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
            report = goal_compiler.execute_first_step(approved)
            output = workspace / semantic["first_step"]["output_directory"]
            artifact = output / "test_csv_empty_lines.py"
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["dispatch"]["action"], "write_python_regression_fixture")
            self.assertEqual(report["resolved_output_directory"], str(output.resolve()))
            self.assertTrue(artifact.is_file())
            self.assertIn("REGRESSION_FIXTURE", artifact.read_text(encoding="utf-8"))
            self.assertTrue(report["checks"]["python_syntax"])

    def test_seo_requires_sources_before_human_approval(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        contract = compile_semantic(semantic)
        errors = goal_compiler.validate_contract(contract, require_human_approval=False, require_evidence=True)
        self.assertTrue(any("evidence_bundle.sources" in error for error in errors))
        with self.assertRaisesRegex(goal_compiler.CompilerError, "evidence-incomplete"):
            goal_compiler.apply_human_review(contract, synthetic_review("seo-source-brief"))

        evidence = load_fixture("seo-evidence.json")
        approved = goal_compiler.apply_human_review(
            contract,
            synthetic_review("seo-source-brief"),
            evidence_bundle=evidence,
        )
        self.assertEqual([], goal_compiler.validate_contract(approved))

    def test_subjective_metric_statement_and_method_fail(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        semantic["strategy_gate"]["success_metrics"][0]["statement"] = "这个修复看起来更专业且令人满意"
        semantic["strategy_gate"]["success_metrics"][0]["measurement"] = {
            "method": "人工主观感受",
            "target": {"reviewers": 1},
        }
        contract = compile_semantic(semantic)
        joined = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("vague wording", joined)
        self.assertIn("subjective method", joined)
        self.assertIn("does not correspond to action", joined)

    def test_pending_review_fixture_cannot_be_applied(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        pending = json.loads((DEMO_FIXTURES / "human-review.pending.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(goal_compiler.CompilerError, "pending"):
            goal_compiler.apply_human_review(contract, pending)

    def test_synthetic_approval_cannot_bypass_non_test_contract(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        contract = compile_semantic(semantic, request=WEBSITE_REQUEST)
        review = synthetic_review("first-validation-page")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "test_fixture"):
            goal_compiler.apply_human_review(contract, review)

    def test_review_must_name_exact_metric(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        review = synthetic_review("wrong-metric")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "metric_id"):
            goal_compiler.apply_human_review(contract, review)

    def test_evidence_sources_must_have_distinct_urls(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        evidence = load_fixture("seo-evidence.json")
        evidence["sources"][1]["url"] = evidence["sources"][0]["url"]
        contract = compile_semantic(semantic, evidence_bundle=evidence)
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("duplicate URL", errors)

    def test_saved_semantic_snapshot_rejects_each_derived_field_drift_before_review(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        mutations = {
            "router": lambda value: value["smart_router"].__setitem__("risk_level", "高"),
            "strategy": lambda value: value["strategy_gate"].__setitem__("smallest_bet", "改成另一个未经 Agent 记录的最小验证。"),
            "tool_gate": lambda value: value["tool_evidence_gate"]["permitted_tools"].append("new tool"),
            "goal_plan": lambda value: value["goal_plan"].__setitem__("outcome", "改成另一个未经 Agent 记录的目标。"),
            "first_step": lambda value: value["first_step"].__setitem__("purpose", "改成另一个未经 Agent 记录的动作目的。"),
        }
        for name, mutate in mutations.items():
            with self.subTest(field=name):
                contract = compile_semantic(semantic)
                mutate(contract)
                errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
                self.assertIn("semantic_input_snapshot", errors)
                with self.assertRaisesRegex(goal_compiler.CompilerError, "saved semantic snapshot"):
                    goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))

    def test_seo_research_gate_cannot_be_downgraded_before_review_or_execution(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        evidence = load_fixture("seo-evidence.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            contract = compile_semantic(semantic, workspace_root=workspace)
            downgraded = copy.deepcopy(contract)
            downgraded["tool_evidence_gate"]["research_required"] = False
            errors = "\n".join(goal_compiler.validate_contract(downgraded, require_human_approval=False))
            self.assertIn("tool_evidence_gate: derived value drifted", errors)
            with self.assertRaisesRegex(goal_compiler.CompilerError, "saved semantic snapshot"):
                goal_compiler.apply_human_review(
                    downgraded,
                    synthetic_review("seo-source-brief"),
                    evidence_bundle=evidence,
                )

            approved = goal_compiler.apply_human_review(
                contract,
                synthetic_review("seo-source-brief"),
                evidence_bundle=evidence,
            )
            post_review_drift = copy.deepcopy(approved)
            post_review_drift["tool_evidence_gate"]["research_required"] = False
            with self.assertRaises(goal_compiler.CompilerError):
                goal_compiler.execute_first_step(post_review_drift)
            self.assertFalse((workspace / semantic["first_step"]["output_directory"]).exists())

    def test_evidence_record_fields_are_required_on_each_source(self) -> None:
        semantic = load_semantic("seo-semantic-input.json")
        semantic["tool_evidence_gate"]["evidence_requirements"][0]["record_fields"].append("published_at")
        evidence = load_fixture("seo-evidence.json")
        contract = compile_semantic(semantic, evidence_bundle=evidence)
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("published_at", errors)

        for source in evidence["sources"]:
            source["published_at"] = "2026-08-31"
        complete_contract = compile_semantic(semantic, evidence_bundle=evidence)
        approved = goal_compiler.apply_human_review(
            complete_contract,
            synthetic_review("seo-source-brief"),
        )
        self.assertEqual([], goal_compiler.validate_contract(approved))

    def test_markdown_source_references_must_be_known_and_cover_claim_minimum(self) -> None:
        evidence = load_fixture("seo-evidence.json")
        cases = {
            "unknown": "# SEO 验证简报\n\nsource_ids: totally-missing-id, seo-001\n",
            "insufficient": "# SEO 验证简报\n\nsource_ids: seo-001\n",
        }
        for name, content in cases.items():
            with self.subTest(case=name):
                semantic = load_semantic("seo-semantic-input.json")
                set_first_step_content(semantic, content)
                contract = compile_semantic(semantic, evidence_bundle=evidence)
                errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
                self.assertIn("validator `source_reference` failed", errors)
                with self.assertRaisesRegex(goal_compiler.CompilerError, "source_reference"):
                    goal_compiler.apply_human_review(contract, synthetic_review("seo-source-brief"))

    def test_execution_output_is_derived_from_approved_workspace(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "explicit absolute"):
            compile_semantic(semantic, workspace_root=Path("relative-workspace"))
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            approved_workspace = parent / "approved-workspace"
            other_workspace = parent / "other-workspace"
            contract = compile_semantic(semantic, workspace_root=approved_workspace)
            approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
            expected = approved_workspace / semantic["first_step"]["output_directory"]

            for unapproved in (other_workspace / "first-output", parent / "absolute-other-output"):
                with self.subTest(path=unapproved):
                    with self.assertRaisesRegex(goal_compiler.CompilerError, "does not match the approved"):
                        goal_compiler.execute_first_step(approved, unapproved.resolve())
                    self.assertFalse(unapproved.exists())

            report = goal_compiler.execute_first_step(approved, expected)
            self.assertEqual(str(expected.resolve()), report["resolved_output_directory"])

    def test_changed_fields_drift_breaks_review_record_consistency(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        approved = goal_compiler.apply_human_review(
            compile_semantic(semantic),
            synthetic_review("csv-empty-line-regression"),
        )
        drifted = copy.deepcopy(approved)
        drifted["human_review"]["changed_fields"].append("goal_plan.outcome")
        errors = "\n".join(goal_compiler.validate_contract(drifted))
        self.assertIn("human_review.changed_fields", errors)
        self.assertIn("human_review.review_id", errors)

        wrong_metric = copy.deepcopy(approved)
        wrong_metric["human_review"]["metric_id"] = "another-metric"
        metric_errors = "\n".join(goal_compiler.validate_contract(wrong_metric))
        self.assertIn("human_review.metric_id", metric_errors)
        self.assertIn("human_review.review_id", metric_errors)

    def test_human_metric_override_is_reconstructed_from_snapshot(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        review = synthetic_review("csv-empty-line-regression")
        override = copy.deepcopy(semantic["strategy_gate"]["success_metrics"][0])
        override["statement"] = "生成 1 个语法有效且包含回归标记的 Python 空行夹具。"
        review["success_metric_override"] = override
        approved = goal_compiler.apply_human_review(compile_semantic(semantic), review)
        self.assertEqual(["strategy_gate.success_metrics[0]"], approved["human_review"]["changed_fields"])
        self.assertEqual([], goal_compiler.validate_contract(approved))

    def test_acceptance_required_terms_rejects_blank_entries(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        semantic["first_step"]["acceptance"]["required_terms"].append("   ")
        with self.assertRaisesRegex(goal_compiler.CompilerError, "entries must be non-empty strings"):
            compile_semantic(semantic)

    def test_html_external_url_parser_rejects_single_quotes_case_and_whitespace(self) -> None:
        semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
        content = semantic["first_step"]["content_template"].replace(
            "</main>",
            "<img SRC = ' HTTPS://example.com/tracker.png ' alt='external'></main>",
        )
        set_first_step_content(semantic, content)
        contract = compile_semantic(semantic, request=WEBSITE_REQUEST)
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("validator `no_external_urls` failed", errors)

    def test_html_external_url_gate_rejects_network_capable_bypasses(self) -> None:
        evidence = {
            "sources": [
                {
                    "id": "web-001",
                    "title": "Synthetic website observation A",
                    "url": "https://example.test/source-a",
                    "source_type": "synthetic test fixture",
                    "tool_channel": "local test data",
                    "access_limit": "not a live source",
                },
                {
                    "id": "web-002",
                    "title": "Synthetic website observation B",
                    "url": "https://example.org/source-b",
                    "source_type": "synthetic test fixture",
                    "tool_channel": "local test data",
                    "access_limit": "not a live source",
                },
            ],
            "claims": [
                {
                    "claim_type": "用户痛点或需求",
                    "statement": "Synthetic claim used only for the HTML execution-boundary regression.",
                    "source_ids": ["web-001", "web-002"],
                }
            ],
            "notice": "TEST ONLY: not research evidence for a real decision.",
        }
        variants = {
            "form action": '<form action="https://example.com/collect"></form>',
            "srcset": '<img srcset="https://example.com/a.png 1x, //example.org/b.png 2x" alt="external">',
            "css import": '<style>@import url(https://example.com/theme.css);</style>',
            "script fetch": '<script>fetch("https://example.com/collect")</script>',
            "encoded URL": '<form action="https:&#47;&#47;example.com/collect"></form>',
            "CSS escaped URL": '<style>@import url(https:\\2f\\2f example.com/theme.css);</style>',
            "computed script": '<script>fetch(["https:", "//example.com"].join(""))</script>',
            "non-HTTP scheme": '<img src="ftp://example.com/pixel.png" alt="external">',
            "active URI scheme": '<a href="javascript:alert(1)">external</a>',
            "embedded active document": '<iframe src="data:text/html,external"></iframe>',
            "HTML newline in scheme": '<a href="java&#10;script:alert(1)">external</a>',
            "HTML tab in scheme": '<iframe src="da&#9;ta:text/html,external"></iframe>',
            "literal carriage return in scheme": '<a href="java\rscript:alert(1)">external</a>',
            "CSS newline in scheme": '<style>@import url(https:\n//example.com/theme.css);</style>',
            "iframe srcdoc": '<iframe srcdoc="&lt;script&gt;top.__x=1&lt;/script&gt;"></iframe>',
            "SVG xlink": '<svg><a xlink:href="javascript:alert(1)">external</a></svg>',
            "meta refresh": '<meta http-equiv="refresh" content="0; url=/next">',
        }
        for name, injection in variants.items():
            with self.subTest(vector=name):
                semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
                semantic["provenance"]["mode"] = "test_fixture"
                content = semantic["first_step"]["content_template"].replace("</main>", f"{injection}</main>")
                set_first_step_content(semantic, content)
                contract = compile_semantic(semantic, request=WEBSITE_REQUEST, evidence_bundle=evidence)
                errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
                self.assertIn("validator `no_external_urls` failed", errors)
                review = synthetic_review("first-validation-page")
                with self.assertRaisesRegex(goal_compiler.CompilerError, "cannot approve an invalid"):
                    goal_compiler.apply_human_review(contract, review)

        with tempfile.TemporaryDirectory() as temp_dir:
            semantic = goal_compiler.load_semantic_input(DEMO_FIXTURES / "semantic-input.demo.json")
            semantic["provenance"]["mode"] = "test_fixture"
            local_links = '<a href="#plan">plan</a><img src="./local.png" alt="local"><a href="/local">local</a>'
            content = semantic["first_step"]["content_template"].replace("</main>", f"{local_links}</main>")
            set_first_step_content(semantic, content)
            contract = compile_semantic(
                semantic,
                request=WEBSITE_REQUEST,
                workspace_root=Path(temp_dir),
                evidence_bundle=evidence,
            )
            approved = goal_compiler.apply_human_review(contract, synthetic_review("first-validation-page"))
            report = goal_compiler.execute_first_step(approved)
            self.assertTrue(report["checks"]["no_external_urls"])
            self.assertTrue((Path(temp_dir) / "first-output" / "index.html").is_file())

    def test_compiler_metadata_is_exact_and_approval_bound(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        approved = goal_compiler.apply_human_review(
            compile_semantic(semantic),
            synthetic_review("csv-empty-line-regression"),
        )
        forged = copy.deepcopy(approved)
        forged["compiler"] = {
            "name": "Forged Compiler",
            "version": "999.0",
            "kind": "cryptographically-signed-runtime",
        }
        errors = goal_compiler.validate_contract(forged)
        self.assertTrue(any(error.startswith("compiler:") for error in errors), errors)
        self.assertTrue(any("approved_payload_sha256" in error for error in errors), errors)
        with self.assertRaises(goal_compiler.CompilerError):
            goal_compiler.execute_first_step(forged)

    def test_request_hash_and_contract_id_are_verified(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        request_drift = copy.deepcopy(contract)
        request_drift["request"]["raw"] += " changed"
        request_errors = "\n".join(goal_compiler.validate_contract(request_drift, require_human_approval=False))
        self.assertIn("request.request_sha256", request_errors)

        id_drift = copy.deepcopy(contract)
        id_drift["contract_id"] = "goal-changed"
        id_errors = "\n".join(goal_compiler.validate_contract(id_drift, require_human_approval=False))
        self.assertIn("contract_id", id_errors)

    def test_approval_digest_detects_unreviewed_execution_payload_drift(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))

        mutations = {
            "request": lambda value: value["request"].__setitem__("raw", value["request"]["raw"] + " changed"),
            "router": lambda value: value["smart_router"].__setitem__("risk_level", "high"),
            "strategy": lambda value: value["strategy_gate"]["success_metrics"][0].__setitem__("statement", "生成 2 个 Python 文件"),
            "evidence": lambda value: value["evidence_bundle"].__setitem__("claims", [{"changed": True}]),
            "action": lambda value: value["first_step"].__setitem__("action", "shell_anything"),
            "artifact": lambda value: value["first_step"].__setitem__("primary_artifact", "first-output/other.py"),
            "checks": lambda value: value["first_step"].__setitem__("validators", ["nonempty"]),
            "content": lambda value: value["first_step"].__setitem__("content_template", "# changed"),
        }
        for name, mutate in mutations.items():
            with self.subTest(field=name):
                drifted = copy.deepcopy(approved)
                mutate(drifted)
                errors = goal_compiler.validate_contract(drifted)
                self.assertTrue(
                    any("approved_payload_sha256" in error for error in errors),
                    f"{name} did not invalidate approval: {errors}",
                )
                with tempfile.TemporaryDirectory() as temp_dir:
                    output = Path(temp_dir) / "blocked"
                    with self.assertRaises(goal_compiler.CompilerError):
                        goal_compiler.execute_first_step(drifted, output)
                    self.assertFalse(output.exists())

    def test_approval_digest_detects_each_declared_execution_field_drift(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        for field in goal_compiler.EXECUTION_BOUND_FIELDS:
            with self.subTest(field=field):
                drifted = copy.deepcopy(approved)
                current = drifted[field]
                if isinstance(current, dict):
                    current["_post_approval_drift"] = True
                elif isinstance(current, list):
                    current.append("post approval drift")
                else:
                    drifted[field] = f"{current}-changed"
                errors = goal_compiler.validate_contract(drifted)
                self.assertTrue(any("approved_payload_sha256" in error for error in errors), errors)

    def test_unknown_action_and_action_specific_checks_are_rejected(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        contract["first_step"]["action"] = "run_shell"
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("unsupported action", errors)

        contract = compile_semantic(semantic)
        contract["first_step"]["validators"] = ["nonempty"]
        errors = "\n".join(goal_compiler.validate_contract(contract, require_human_approval=False))
        self.assertIn("must exactly match action whitelist", errors)

    def test_file_and_directory_outputs_refuse_existing_targets(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            contract = compile_semantic(semantic, workspace_root=root)
            approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
            existing_dir = root / semantic["first_step"]["output_directory"]
            existing_dir.mkdir()
            with self.assertRaisesRegex(goal_compiler.CompilerError, "already exists"):
                goal_compiler.execute_first_step(approved)

            existing_file = root / "existing.json"
            existing_file.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(goal_compiler.CompilerError, "overwrite"):
                goal_compiler.write_json(existing_file, contract, refuse_existing=True)

    def test_demo_writes_only_fail_logs_and_stops_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "demo"
            report = goal_compiler.run_demo(
                output,
                DEMO_FIXTURES / "request.txt",
                DEMO_FIXTURES / "semantic-input.demo.json",
            )
            self.assertEqual(report["status"], "HUMAN_PENDING")
            self.assertFalse(report["liveAiClaimed"])
            self.assertFalse(report["execution"]["attempted"])
            self.assertEqual([], list(output.rglob("validator.PASS.log")))
            self.assertEqual(2, len(list(output.rglob("validator.FAIL.log"))))
            self.assertFalse((output / "03-first-output").exists())
            self.assertTrue((output / "03-human-pending" / "human-review.pending.json").is_file())

    def test_cli_validate_nonzero_for_pending_and_zero_for_synthetic_test_approval(self) -> None:
        semantic = load_semantic("coding-semantic-input.json")
        contract = compile_semantic(semantic)
        approved = goal_compiler.apply_human_review(contract, synthetic_review("csv-empty-line-regression"))
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pending_path = root / "pending.json"
            approved_path = root / "approved.json"
            goal_compiler.write_json(pending_path, contract)
            goal_compiler.write_json(approved_path, approved)
            pending = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(pending_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            passed = subprocess.run(
                [sys.executable, str(SCRIPTS / "goal_compiler.py"), "validate", str(approved_path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(pending.returncode, 1)
            self.assertEqual(passed.returncode, 0, passed.stderr)


if __name__ == "__main__":
    unittest.main()
