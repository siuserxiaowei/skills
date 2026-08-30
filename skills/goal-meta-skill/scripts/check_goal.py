#!/usr/bin/env python3
"""Statically check a draft Codex /goal instruction.

The checker is intentionally conservative and dependency-free. It reports structural
signals; it does not decide whether the user's chosen outcome is desirable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE),
    re.compile(r"\[(?:目标|结果|命令|路径|填写|待补充|outcome|command|path|fill[^]]*)\]", re.IGNORECASE),
    re.compile(r"<(?:目标|结果|命令|路径|outcome|command|path|placeholder)>", re.IGNORECASE),
)

EVIDENCE_TERMS = (
    "验证", "证据", "测试", "构建", "运行", "日志", "截图", "复现", "核对", "比对",
    "verify", "evidence", "test", "build", "runtime", "log", "screenshot", "reproduce", "compare",
)
COMPLETION_TERMS = (
    "完成条件", "完成时", "仅当", "证明完成", "全部通过", "无剩余", "ready when", "done when",
    "complete when", "finish only", "stop when", "all required", "no required work",
)
AUTHORITY_TERMS = (
    "授权", "确认后", "用户确认", "批准", "暂停", "不得", "禁止", "只允许", "只写入",
    "authorized", "approval", "confirm", "consent", "pause", "must not", "do not", "only write",
)
HIGH_RISK_TERMS = (
    "删除", "覆盖", "清空", "生产", "线上", "发布", "推送", "公开", "付款", "支付", "购买",
    "凭证", "密钥", "密码", "权限", "迁移", "客户数据", "个人数据", "医疗", "法律", "金融",
    "delete", "overwrite", "production", "deploy", "publish", "push", "public", "payment", "purchase",
    "credential", "secret", "password", "permission", "migration", "customer data", "personal data",
    "medical", "legal", "financial",
)
UNBOUNDED_TERMS = (
    "无限", "永不停止", "不要停", "一直重试", "直到成功", "不惜一切", "never stop", "retry forever",
    "keep retrying", "at all costs", "until success",
)
VAGUE_ONLY = re.compile(
    r"^(?:请|帮我|给我|please\s+)?(?:研究一下|看一下|优化一下|完善一下|改进一下|弄好|做完|完成|"
    r"research|look into|improve|optimi[sz]e|finish|complete|fix it)(?:吧|。|！|!|\.)?$",
    re.IGNORECASE,
)


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(term.casefold() in lowered for term in terms)


def analyze(text: str) -> list[Finding]:
    findings: list[Finding] = []
    normalized = text.strip()

    if not normalized:
        return [Finding("error", "empty", "Goal draft is empty.")]

    if not re.match(r"^/goal(?:\s|$)", normalized, re.IGNORECASE):
        findings.append(Finding("error", "missing-command", "Paste-ready draft must start with /goal."))

    for pattern in PLACEHOLDER_PATTERNS:
        match = pattern.search(normalized)
        if match:
            findings.append(
                Finding("error", "placeholder", f"Unresolved placeholder found: {match.group(0)}")
            )
            break

    body = re.sub(r"^/goal\s*", "", normalized, count=1, flags=re.IGNORECASE).strip()
    first_sentence = re.split(r"[\n。.!?！？]", body, maxsplit=1)[0].strip()
    if not body:
        findings.append(Finding("error", "missing-outcome", "The goal has no objective after /goal."))
    elif VAGUE_ONLY.fullmatch(first_sentence) or len(body) < 40:
        findings.append(
            Finding("warning", "weak-outcome", "Outcome appears too vague or short to define an observable end state.")
        )

    if not contains_any(normalized, EVIDENCE_TERMS):
        findings.append(
            Finding("warning", "missing-evidence", "No concrete verification or evidence signal was found.")
        )

    if not contains_any(normalized, COMPLETION_TERMS):
        findings.append(
            Finding("warning", "missing-completion", "No evidence-based completion condition was found.")
        )

    risks = sorted({term for term in HIGH_RISK_TERMS if term.casefold() in normalized.casefold()})
    if risks and not contains_any(normalized, AUTHORITY_TERMS):
        findings.append(
            Finding(
                "error",
                "missing-authority-boundary",
                "High-impact work is mentioned without an authorization or pause boundary: " + ", ".join(risks[:5]),
            )
        )

    if contains_any(normalized, UNBOUNDED_TERMS):
        findings.append(
            Finding("error", "unbounded-persistence", "Goal requests unbounded retry or persistence without a safe stop condition.")
        )

    goal_count = len(re.findall(r"(?im)^\s*/goal(?:\s|$)", normalized))
    if goal_count > 1:
        findings.append(
            Finding("warning", "multiple-goals", "Draft contains multiple /goal commands; use one durable outcome unless separate goals are intentional.")
        )

    return findings


def render_text(findings: list[Finding]) -> str:
    if not findings:
        return "PASS: no structural findings"
    return "\n".join(f"{item.severity.upper()} [{item.code}] {item.message}" for item in findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Codex /goal draft without executing it.")
    parser.add_argument("path", nargs="?", help="Draft file; omit or use - to read stdin")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args(argv)

    if args.path in (None, "-"):
        text = sys.stdin.read()
        source = "stdin"
    else:
        path = Path(args.path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"ERROR [read-failed] {exc}", file=sys.stderr)
            return 2
        source = str(path)

    findings = analyze(text)
    if args.format == "json":
        payload = {
            "source": source,
            "findings": [asdict(item) for item in findings],
            "counts": {
                "error": sum(item.severity == "error" for item in findings),
                "warning": sum(item.severity == "warning" for item in findings),
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_text(findings))

    has_error = any(item.severity == "error" for item in findings)
    has_warning = any(item.severity == "warning" for item in findings)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
