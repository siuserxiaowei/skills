#!/usr/bin/env python3
"""Validate fixed Goal Compiler contest evidence without external packages."""

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

REQUIRED = (
    CONTEST / "README.md",
    CONTEST / "weibo-copy.md",
    CONTEST / "demo-script.md",
    CONTEST / "shot-list.md",
    CONTEST / "submission.json",
    CONTEST / "media-manifest.json",
    CONTEST / "goal-compiler-board-1920x1080.png",
    DEMO / "01-invalid-draft" / "router.json",
    DEMO / "01-invalid-draft" / "strategy-gate.json",
    DEMO / "01-invalid-draft" / "validator.FAIL.log",
    DEMO / "human-metric-patch.json",
    DEMO / "02-reviewed-contract" / "strategy-gate.json",
    DEMO / "02-reviewed-contract" / "validator.PASS.log",
    DEMO / "03-first-output" / "index.html",
    DEMO / "03-first-output" / "execution-report.json",
    DEMO / "walkthrough.html",
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
    if not isinstance(provenance, dict) or provenance.get("liveAiClaimed") is not False:
        errors.append("submission.json: bundled fixture must set liveAiClaimed to false")

    demo_report = load_json(DEMO / "demo-report.json")
    if demo_report.get("status") != "PASS":
        errors.append("demo-report.json: overall status is not PASS")
    negative = demo_report.get("negative_gate", {})
    positive = demo_report.get("positive_gate", {})
    if not isinstance(negative, dict) or negative.get("status") != "FAIL":
        errors.append("demo-report.json: negative gate is not FAIL")
    if not isinstance(positive, dict) or positive.get("status") != "PASS":
        errors.append("demo-report.json: positive gate is not PASS")

    execution = load_json(DEMO / "03-first-output" / "execution-report.json")
    checks = execution.get("checks", {})
    if execution.get("status") != "PASS" or not isinstance(checks, dict) or not checks or not all(checks.values()):
        errors.append("execution-report.json: deterministic checks did not all pass")
    if execution.get("external_side_effects") != []:
        errors.append("execution-report.json: fixed demo must have no external side effects")

    reviewed = load_json(DEMO / "02-reviewed-contract" / "goal-contract.json")
    human_review = reviewed.get("human_review", {})
    if not isinstance(human_review, dict) or human_review.get("previous_metric_statement") != "好看":
        errors.append("reviewed contract: missing human change from the vague metric `好看`")
    if not isinstance(human_review, dict) or human_review.get("sign_off") != "APPROVED BY HUMAN":
        errors.append("reviewed contract: missing explicit human sign-off")

    if png_dimensions(CONTEST / "goal-compiler-board-1920x1080.png") != (1920, 1080):
        errors.append("contest board must be exactly 1920x1080")

    for relative in (
        Path("walkthrough.html"),
        Path("01-invalid-draft/router.json"),
        Path("01-invalid-draft/validator.FAIL.log"),
        Path("02-reviewed-contract/validator.PASS.log"),
        Path("03-first-output/index.html"),
        Path("03-first-output/execution-report.json"),
    ):
        if digest(DEMO / relative) != digest(DOCS_DEMO / relative):
            errors.append(f"docs/demo drifted from contest/demo-output: {relative}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Goal Compiler contest pack validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
