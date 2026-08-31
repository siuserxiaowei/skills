#!/usr/bin/env python3
"""Validate the fixed, human-pending Goal Compiler contest evidence."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEST = ROOT / "contest"
DEMO = CONTEST / "demo-output"
DOCS_DEMO = ROOT / "docs" / "demo"

SYNCED_DEMO_FILES = (
    Path("walkthrough.html"),
    Path("demo-report.json"),
    Path("DEMO_RESULT.md"),
    Path("01-agent-result/semantic-input.snapshot.json"),
    Path("01-agent-result/router.json"),
    Path("01-agent-result/strategy-gate.json"),
    Path("01-agent-result/goal-contract.json"),
    Path("01-agent-result/validator.FAIL.log"),
    Path("02-subjective-metric/strategy-gate.json"),
    Path("02-subjective-metric/goal-contract.json"),
    Path("02-subjective-metric/validator.FAIL.log"),
    Path("03-human-pending/human-review.pending.json"),
    Path("03-human-pending/NOTICE.md"),
)

REQUIRED = (
    CONTEST / "README.md",
    CONTEST / "weibo-copy.md",
    CONTEST / "demo-script.md",
    CONTEST / "shot-list.md",
    CONTEST / "submission.json",
    CONTEST / "media-manifest.json",
    CONTEST / "goal-compiler-board-1920x1080.png",
    CONTEST / "demo-fixtures" / "semantic-input.demo.json",
    CONTEST / "demo-fixtures" / "human-review.pending.json",
    CONTEST / "demo-fixtures" / "website-first-output.html",
    CONTEST / "forward-test-prompt.txt",
    CONTEST / "forward-test" / "transcript.md",
    CONTEST / "forward-test" / "semantic-result.json",
    CONTEST / "test-evidence" / "coding-reviewed.test.json",
    CONTEST / "test-evidence" / "coding-validation.PASS.json",
    CONTEST / "test-evidence" / "coding-first-output" / "test_csv_empty_lines.py",
    CONTEST / "test-evidence" / "coding-first-output" / "execution-report.json",
    *(DEMO / relative for relative in SYNCED_DEMO_FILES),
)


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"{path}: invalid PNG header")
    return struct.unpack(">II", data[16:24])


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required contest artifact: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    submission = load_json(CONTEST / "submission.json")
    provenance = submission.get("demoProvenance", {})
    if submission.get("demoStatus") != "HUMAN_PENDING":
        errors.append("submission.json: fixed demo must be HUMAN_PENDING")
    if not isinstance(provenance, dict) or provenance.get("liveAiClaimed") is not False:
        errors.append("submission.json: bundled fixture must set liveAiClaimed=false")

    semantic = load_json(DEMO / "01-agent-result" / "semantic-input.snapshot.json")
    contract = load_json(DEMO / "01-agent-result" / "goal-contract.json")
    semantic_provenance = semantic.get("provenance", {})
    if not isinstance(semantic_provenance, dict):
        errors.append("semantic snapshot: missing provenance object")
    else:
        if semantic_provenance.get("mode") != "deterministic_demo_fixture":
            errors.append("semantic snapshot: fixed demo must be deterministic_demo_fixture")
        if semantic_provenance.get("live_ai_claimed") is not False or semantic_provenance.get("liveAiClaimed") is not False:
            errors.append("semantic snapshot: both live AI provenance flags must be false")
    if contract.get("semantic_input_snapshot") != semantic:
        errors.append("goal contract must embed the exact saved semantic snapshot")
    workspace = contract.get("execution_workspace", {})
    expected_demo_workspace = str(Path("/tmp/xiaowei-goal-demo-execution-workspace").resolve())
    if not isinstance(workspace, dict) or workspace.get("root") != expected_demo_workspace:
        errors.append("fixed demo contract must record the deterministic execution workspace")

    demo_report = load_json(DEMO / "demo-report.json")
    if demo_report.get("status") != "HUMAN_PENDING":
        errors.append("demo-report.json: fixed demo must stop at HUMAN_PENDING")
    if demo_report.get("liveAiClaimed") is not False:
        errors.append("demo-report.json: fixed demo must set liveAiClaimed=false")
    agent_preflight = demo_report.get("agent_preflight", {})
    metric_gate = demo_report.get("subjective_metric_gate", {})
    execution = demo_report.get("execution", {})
    if not isinstance(agent_preflight, dict) or agent_preflight.get("status") != "FAIL":
        errors.append("demo-report.json: evidence/human preflight must be FAIL")
    if not isinstance(metric_gate, dict) or metric_gate.get("status") != "FAIL":
        errors.append("demo-report.json: subjective metric gate must be FAIL")
    if not isinstance(execution, dict) or execution.get("attempted") is not False:
        errors.append("demo-report.json: execution must not be attempted")

    pending = load_json(DEMO / "03-human-pending" / "human-review.pending.json")
    if pending.get("record_type") != "pending_human_review_example" or pending.get("decision") != "pending":
        errors.append("human review fixture must remain an explicit pending example")
    acknowledgements = pending.get("acknowledgements", {})
    if not isinstance(acknowledgements, dict) or any(value is not False for value in acknowledgements.values()):
        errors.append("pending human review acknowledgements must all remain false")

    pass_logs = sorted(DEMO.rglob("validator.PASS.log"))
    fail_logs = sorted(DEMO.rglob("validator.FAIL.log"))
    if pass_logs:
        errors.append(f"fixed demo must contain no PASS logs: {[path.relative_to(DEMO) for path in pass_logs]}")
    if len(fail_logs) != 2:
        errors.append(f"fixed demo must contain exactly two FAIL logs, found {len(fail_logs)}")
    if (DEMO / "03-first-output").exists():
        errors.append("fixed demo must not contain an executed first-output directory")

    forward = load_json(CONTEST / "forward-test" / "semantic-result.json")
    forward_provenance = forward.get("provenance", {})
    if forward.get("status") != "agent_result" or forward.get("human_status") != "human_pending":
        errors.append("forward test must be labelled agent_result + human_pending")
    if not isinstance(forward_provenance, dict) or forward_provenance.get("agentExecutionRecorded") is not True:
        errors.append("forward test must record its Agent execution provenance")
    if isinstance(forward_provenance, dict) and (
        forward_provenance.get("humanApprovalClaimed") is not False
        or forward_provenance.get("executionClaimed") is not False
    ):
        errors.append("forward test must not claim human approval or execution")

    coding_validation = load_json(CONTEST / "test-evidence" / "coding-validation.PASS.json")
    coding_execution = load_json(CONTEST / "test-evidence" / "coding-first-output" / "execution-report.json")
    coding_reviewed = load_json(CONTEST / "test-evidence" / "coding-reviewed.test.json")
    coding_goal = (CONTEST / "test-evidence" / "coding-compile" / "goal.md").read_text(encoding="utf-8")
    if coding_validation.get("status") != "PASS" or coding_validation.get("approval_context") != "synthetic_test":
        errors.append("coding test evidence must pass only under explicit synthetic_test context")
    dispatch = coding_execution.get("dispatch", {})
    checks = coding_execution.get("checks", {})
    if (
        coding_execution.get("status") != "PASS"
        or coding_execution.get("approval_context") != "synthetic_test"
        or not isinstance(dispatch, dict)
        or dispatch.get("action") != "write_python_regression_fixture"
        or not isinstance(checks, dict)
        or not checks
        or not all(checks.values())
    ):
        errors.append("coding test evidence does not prove the domain-correct Python dispatch")
    if coding_reviewed.get("semantic_input_snapshot") is None or coding_reviewed.get("execution_workspace") is None:
        errors.append("coding test evidence must preserve semantic snapshot and approved workspace")
    if coding_execution.get("execution_workspace") != coding_reviewed.get("execution_workspace"):
        errors.append("coding execution workspace must match the reviewed contract")
    for forbidden in ("CTA", "15-25 个候选来源", "IdeaSignal", "网站/落地页改版包"):
        if forbidden in coding_goal:
            errors.append(f"coding goal leaked website term: {forbidden}")

    media = load_json(CONTEST / "media-manifest.json")
    if media.get("targetDurationSeconds") not in range(60, 76):
        errors.append("media manifest duration must stay within 60-75 seconds")
    if media.get("liveAiClaimed") is not False or media.get("executionClaimed") is not False:
        errors.append("media manifest must not claim live AI or execution for fixed demo")
    shots = media.get("shots", [])
    if not isinstance(shots, list) or not shots:
        errors.append("media manifest needs a non-empty shot list")
    else:
        for index, shot in enumerate(shots):
            if not isinstance(shot, dict) or not str(shot.get("artifact", "")).strip():
                errors.append(f"media manifest shot {index} has no artifact")

    if png_dimensions(CONTEST / "goal-compiler-board-1920x1080.png") != (1920, 1080):
        errors.append("contest board must be exactly 1920x1080")

    for relative in SYNCED_DEMO_FILES:
        docs_path = DOCS_DEMO / relative
        if not docs_path.is_file():
            errors.append(f"docs/demo missing synced artifact: {relative}")
        elif digest(DEMO / relative) != digest(docs_path):
            errors.append(f"docs/demo drifted from contest/demo-output: {relative}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Goal Compiler contest pack validation passed (HUMAN_PENDING, no execution claim).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
