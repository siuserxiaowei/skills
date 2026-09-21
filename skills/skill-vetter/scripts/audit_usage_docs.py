#!/usr/bin/env python3
"""Audit whether every Skill has actionable usage guidance and concrete cases."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


CASE_HEADINGS = ("正向案例", "边界案例", "失败与恢复")
USAGE_HEADING = "使用说明"
ENTRY_SIGNALS = {
    "inputs": re.compile(r"输入|准备|前提|确认|request|input|prereq|context|resolve|establish|依頼", re.I),
    "workflow": re.compile(r"流程|步骤|执行|处理|workflow|procedure|process|sequence|実行", re.I),
    "verification": re.compile(r"验收|验证|证据|verify|verification|evidence|completion|検証|証拠", re.I),
    "boundary": re.compile(r"边界|范围|失败|恢复|停止|授权|boundary|failure|recover|stop|permission|scope|境界|失敗|回復", re.I),
}
CASE_SIGNALS = {
    "正向案例": {
        "request": re.compile(r"用户请求|\bRequest\b|ユーザー(?:の)?依頼", re.I),
        "preparation": re.compile(r"准备信息|输入|前提|\bContext\b|\bInputs?\b|\bPrerequisites?\b|前提情報", re.I),
        "process": re.compile(r"处理|\bProcess\b|\bSteps?\b|\bDecision\b|処理", re.I),
        "output": re.compile(r"预期输出|预期结果|\bExpected (?:Output|Result)\b|\bDeliverable\b|期待される出力", re.I),
        "evidence": re.compile(r"验收证据|\bAcceptance\b|\bEvidence\b|検証証拠", re.I),
    },
    "边界案例": {
        "situation": re.compile(r"场景|用户请求|\bSituation\b|\bRequest\b|状況", re.I),
        "boundary": re.compile(r"边界判断|输入(?:与|/)?前提|\bBoundary\b|境界判断", re.I),
        "process": re.compile(r"处理|\bProcess\b|\bDecision\b|\bRoute\b|処理", re.I),
        "evidence": re.compile(r"验收证据|\bAcceptance\b|\bEvidence\b|検証証拠", re.I),
    },
    "失败与恢复": {
        "failure": re.compile(r"失败场景|场景|现象|\bFailure\b|\bSituation\b|失敗状況", re.I),
        "recovery": re.compile(r"处理与恢复|处理步骤|恢复|\bRecovery\b|\bDecision\b|\bProcess\b|回復", re.I),
        "evidence": re.compile(r"验收证据|\bAcceptance\b|\bEvidence\b|検証証拠", re.I),
    },
}
GENERIC_CASE_LINES = {
    "- **验收证据：** 未获授权的动作没有发生，结果明确标记适用范围与剩余选择。",
    "- **验收证据：** 失败状态、已完成范围和下一次安全重试条件均可复核。",
    "- **验收证据：** 用户自主性、权限边界和事实准确性均被保留。",
    "- **验收证据：** 新一轮必须产生新证据或新决策；没有把重复、语气或消耗本身当作进展。",
    "- **验收证据：** 任何额外写入、外部发送、权限或高风险动作均未越过用户本轮授权。",
    "- **验收证据：** 保留结构化错误、实际远端状态和下一步条件；没有把未知状态伪装成成功。",
}


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    detail: str


def case_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"^## ([^\n]+)\s*$", text, re.M))
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        if name not in (USAGE_HEADING, *CASE_HEADINGS):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[match.end() : end].strip()
    return sections


def audit(
    root: Path,
    expected_count: int = 57,
    min_case_chars: int = 220,
    min_usage_chars: int = 220,
) -> tuple[list[Finding], dict]:
    root = root.resolve()
    skills_root = root / "skills"
    skill_dirs = sorted(
        path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file()
    )
    findings: list[Finding] = []
    if len(skill_dirs) != expected_count:
        findings.append(Finding("skill-count", "skills", f"expected {expected_count}, found {len(skill_dirs)}"))

    guide_path = root / "USAGE_GUIDE.md"
    try:
        guide_text = guide_path.read_text(encoding="utf-8")
    except OSError as error:
        guide_text = ""
        findings.append(Finding("usage-guide-missing", guide_path.name, str(error)))
    guide_entries = 0
    for skill_dir in skill_dirs:
        name = skill_dir.name
        entry_target = f"skills/{name}/SKILL.md"
        example_target = f"skills/{name}/references/examples.md"
        if entry_target in guide_text and example_target in guide_text:
            guide_entries += 1
        else:
            findings.append(
                Finding("usage-guide-coverage", guide_path.name, f"missing links for {name}")
            )

    section_counts = {heading: 0 for heading in CASE_HEADINGS}
    usage_sections = 0
    for skill_dir in skill_dirs:
        skill_path = skill_dir / "SKILL.md"
        examples_path = skill_dir / "references" / "examples.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        skill_relative = skill_path.relative_to(root).as_posix()

        if len(skill_text.strip()) < 800:
            findings.append(Finding("entry-thin", skill_relative, f"{len(skill_text.strip())} characters"))
        if "[references/examples.md](references/examples.md)" not in skill_text:
            findings.append(Finding("examples-not-routed", skill_relative, "direct examples link is missing"))
        for signal_name, pattern in ENTRY_SIGNALS.items():
            if not pattern.search(skill_text):
                findings.append(Finding("entry-signal", skill_relative, f"missing {signal_name} guidance"))

        if not examples_path.is_file():
            findings.append(
                Finding("examples-missing", examples_path.relative_to(root).as_posix(), "file is missing")
            )
            continue
        examples_text = examples_path.read_text(encoding="utf-8")
        examples_relative = examples_path.relative_to(root).as_posix()
        usage_body = case_sections(examples_text).get(USAGE_HEADING)
        if usage_body is None:
            findings.append(Finding("usage-section-missing", examples_relative, USAGE_HEADING))
        else:
            usage_sections += 1
            if len(usage_body) < min_usage_chars:
                findings.append(
                    Finding(
                        "usage-section-thin",
                        examples_relative,
                        f"{len(usage_body)} < {min_usage_chars} characters",
                    )
                )
        for generic in GENERIC_CASE_LINES:
            if generic in examples_text:
                findings.append(
                    Finding("generic-case-evidence", examples_relative, generic.removeprefix("- "))
                )

        sections = case_sections(examples_text)
        for heading in CASE_HEADINGS:
            body = sections.get(heading)
            if body is None:
                findings.append(Finding("case-missing", examples_relative, heading))
                continue
            section_counts[heading] += 1
            if len(body) < min_case_chars:
                findings.append(
                    Finding("case-thin", examples_relative, f"{heading}: {len(body)} < {min_case_chars} characters")
                )
            for signal_name, pattern in CASE_SIGNALS[heading].items():
                if not pattern.search(body):
                    findings.append(
                        Finding("case-signal", examples_relative, f"{heading}: missing {signal_name}")
                    )

    summary = {
        "skills": len(skill_dirs),
        "guide_entries": guide_entries,
        "usage_sections": usage_sections,
        "case_sections": section_counts,
        "findings": len(findings),
    }
    return findings, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--expected-count", type=int, default=59)
    parser.add_argument("--min-case-chars", type=int, default=220)
    parser.add_argument("--min-usage-chars", type=int, default=220)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    findings, summary = audit(
        Path(args.root),
        args.expected_count,
        args.min_case_chars,
        args.min_usage_chars,
    )
    payload = {"summary": summary, "findings": [asdict(item) for item in findings]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"skills={summary['skills']} guide_entries={summary['guide_entries']} "
            f"usage_sections={summary['usage_sections']} "
            f"positive={summary['case_sections']['正向案例']} "
            f"boundary={summary['case_sections']['边界案例']} "
            f"recovery={summary['case_sections']['失败与恢复']} findings={summary['findings']}"
        )
        for finding in findings:
            print(f"{finding.code}: {finding.path}: {finding.detail}")
    raise SystemExit(1 if findings else 0)


if __name__ == "__main__":
    main()
