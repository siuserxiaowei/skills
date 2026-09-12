#!/usr/bin/env python3
"""Validate Xiaowei-style goal drafts."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_DIRECT = {
    "command": [r"^/goal\s+.+"],
    "verification": [r"^(?:验证方式|Verification)[:：]\s*"],
    "limits": [r"^(?:限制|Limits?)[:：]\s*"],
    "boundary": [r"^(?:工作边界|Work Boundary)[:：]\s*"],
    "progress": [r"^(?:推进规则|Progress Rules?)[:：]\s*"],
    "stop": [r"^(?:停止标准|Stop Criteria|Stop Standard)[:：]\s*"],
    "pause": [r"^(?:暂停条件|Pause Conditions?)[:：]\s*"],
}

SMART_FIELDS = {
    "decision summary": [r"^(?:决策摘要|Decision Summary)[:：]\s*"],
    "default assumptions": [r"^(?:默认假设|Default Assumptions)[:：]\s*"],
    "preference application": [r"^(?:偏好应用|Preference Application)[:：]\s*"],
    "feedback adjustment": [r"^(?:反馈调整|Feedback Adjustment)[:：]\s*"],
    "strategy gate": [r"^(?:策略判断|Strategy Gate)[:：]\s*"],
    "business priority": [r"^(?:优先级判断|Business Priority)[:：]\s*"],
    "output length": [r"^(?:输出长度|Output Length)[:：]\s*"],
    "choice rationale": [r"^(?:选择理由|Choice Rationale)[:：]\s*"],
}

RESEARCH_FIELDS = {
    "task pack": [r"^(?:任务包|Task Pack)[:：]\s*"],
    "domain pack": [r"^(?:领域包|Domain Pack)[:：]\s*"],
    "tool stack": [r"^(?:工具栈|Tool Stack)[:：]\s*"],
    "stage 1 broad research": [r"^(?:阶段\s*1\s*-\s*广域调研|Stage\s*1\s*-\s*Broad Research)[:：]\s*"],
    "stage 2 deep research": [r"^(?:阶段\s*2\s*-\s*Deep Research|Stage\s*2\s*-\s*Deep Research)[:：]\s*"],
    "stage 3 business application": [r"^(?:阶段\s*3\s*-\s*业务应用|Stage\s*3\s*-\s*Business Application)[:：]\s*"],
    "deliverable": [r"^(?:输出物|Deliverables?)[:：]\s*"],
    "quality gate": [r"^(?:质量门槛|Quality Gate)[:：]\s*"],
}

PLACEHOLDERS = [
    r"\[[^\]]+\]",
    r"\bTODO\b",
    r"\bTBD\b",
    r"待定",
    r"待补充",
    r"<[^>]+>",
]

BAD_PHRASES = [
    r"随便搜",
    r"随便改",
    r"全网都搜",
    r"一直试",
    r"直到满意",
    r"看起来可以",
    r"感觉可以",
    r"照抄",
    r"扒下来",
    r"做一个一样的",
    r"make sure it works",
    r"keep trying",
    r"edit anything",
    r"search the whole internet",
    r"entire internet",
]

EVIDENCE_HINTS = [
    r"来源",
    r"URL",
    r"检索日期",
    r"命令",
    r"日志",
    r"截图",
    r"产物",
    r"运行",
    r"测试",
    r"检查",
    r"证据",
    r"\b(test|build|lint|log|screenshot|source|url|evidence)\b",
]

SOURCE_COUNT_HINTS = [
    r"\d+\s*[-~]\s*\d+\s*个?\s*(候选)?来源",
    r"\d+\+\s*个?\s*(候选)?来源",
    r"\d+\s*[-~]\s*\d+\s*(candidate\s*)?sources",
    r"\d+\+\s*(candidate\s*)?sources",
    r"轻量[:：]?\s*6\s*[-~]\s*8",
    r"标准[:：]?\s*15\s*[-~]\s*25",
    r"深度[:：]?\s*40\+",
]

TASK_PACK_HINTS = [
    r"App MVP\s*研究包",
    r"网站/落地页改版包",
    r"SEO\s*内容集群包",
    r"竞品分析包",
    r"增长实验包",
    r"App MVP\s*Research Pack",
    r"Website\s*/\s*Landing Page Revamp Pack",
    r"SEO\s*Content Cluster Pack",
    r"Competitor Analysis Pack",
    r"Growth Experiment Pack",
]

DOMAIN_PACK_HINTS = [
    r"AI\s*工具站包",
    r"Chrome\s*插件包",
    r"出海\s*SaaS\s*包",
    r"小红书/抖音内容验证包",
    r"GitHub\s*开源项目增长包",
    r"不适用",
    r"AI Tool Site Pack",
    r"Chrome Extension Pack",
    r"Global SaaS Pack",
    r"Xiaohongshu\s*/\s*Douyin Validation Pack",
    r"GitHub Open Source Growth Pack",
    r"not applicable",
]

QUALITY_GATE_HINTS = {
    "2 independent sources": [
        r"至少.*2\s*个.*来源",
        r"2\s*个.*独立来源",
        r"2\s+independent\s+sources",
    ],
    "source strength": [r"来源强弱", r"证据强度", r"source strength"],
    "outdated downgrade": [r"过期", r"outdated"],
    "promotional downgrade": [r"营销", r"promotional"],
    "inaccessible downgrade": [r"不可访问", r"inaccessible"],
    "contradictions": [r"矛盾", r"contradiction"],
    "low confidence or hypothesis": [r"低置信度", r"假设", r"low[- ]confidence", r"hypothesis"],
}

TOOL_STACK_HINTS = {
    "Agent Reach": [r"Agent Reach"],
    "Scrapling": [r"Scrapling"],
    "browser-use": [r"browser-use", r"browser use"],
    "Claude for Chrome": [r"Claude for Chrome"],
    "authorization boundary": [r"授权", r"人工接管", r"暂停", r"authorized", r"user-supervised"],
}

ANTI_OVERCLAIM_HINTS = [
    r"不把\s*Agent Reach\s*描述成无限制全网访问",
    r"不宣称.*全网覆盖",
    r"不能.*无限制.*全网",
    r"not.*unlimited.*internet",
    r"not.*full.*internet.*coverage",
    r"do not describe\s*Agent Reach\s*as unlimited internet access",
]

SOURCE_RECORD_HINTS = {
    "tool/channel": [r"工具/渠道", r"tool/channel", r"tool or channel"],
    "access limitation": [r"访问限制", r"access limitation", r"access restriction"],
}

SMART_SUMMARY_HINTS = {
    "task type": [r"任务类型", r"Task type"],
    "maturity": [r"成熟度", r"maturity"],
    "external information need": [r"外部信息需求", r"External information need"],
    "risk level": [r"风险等级", r"Risk level"],
    "output length": [r"输出长度", r"Output length"],
    "question gate": [r"是否先提问", r"Ask clarifying questions first"],
}

BUSINESS_PRIORITY_HINTS = {
    "business value": [r"业务价值", r"business value"],
    "evidence strength": [r"证据强度", r"evidence strength"],
    "execution cost": [r"执行成本", r"execution cost"],
    "distribution potential": [r"分发潜力", r"distribution potential"],
    "monetization path": [r"变现路径", r"monetization path"],
    "risk": [r"风险", r"risk"],
    "recommendation": [r"建议", r"recommendation"],
}

STRATEGY_GATE_HINTS = {
    "problem reframe": [r"问题重构", r"reframe", r"real problem", r"真正.*问题"],
    "smallest bet": [r"最小验证", r"最小.*赌注", r"小实验", r"smallest bet", r"smallest test"],
    "success metric": [r"成功指标", r"success metric", r"metric"],
    "counter evidence": [r"反证", r"失败信号", r"counter[- ]evidence", r"disconfirm"],
    "kill criteria": [r"终止", r"暂缓", r"kill criteria", r"stop condition", r"pause condition"],
}

OUTPUT_LENGTH_HINTS = [
    r"短版",
    r"标准版",
    r"完整版",
    r"\bshort\b",
    r"\bstandard\b",
    r"\bfull\b",
]

SELF_EVOLUTION_TRIGGERS = [
    r"自我进化",
    r"自动化自我进化",
    r"自动.*进化",
    r"自己.*进化",
    r"self[- ]evolution",
    r"auto[- ]evolution",
    r"自动提交",
    r"自动.*发布",
    r"每日进化",
    r"每天.*进化",
    r"daily evolution",
    r"scheduled evolution",
]

SELF_EVOLUTION_HINTS = {
    "automation boundary": [r"自动化边界", r"Automation Boundary"],
    "feedback source": [r"反馈来源", r"feedback source"],
    "allowed paths": [r"允许修改路径", r"allowed paths", r"allowlist"],
    "evaluation": [r"评估方式", r"evaluate_goal_output\.py", r"evaluation"],
    "validation suite": [
        r"validate_xiaowei_goal\.py",
        r"test_validator_negative_cases\.py",
        r"check_installed_skill\.py",
    ],
    "ci gate": [r"GitHub Actions", r"\bCI\b", r"gh run watch"],
    "release policy": [r"发布规则", r"release", r"tag", r"语义化版本", r"semantic version"],
    "rollback": [r"回滚方式", r"rollback", r"revert"],
    "pause risks": [r"凭证", r"破坏性", r"生产数据", r"私域", r"CI.*失败", r"credential", r"destructive"],
}

DAILY_EVOLUTION_TRIGGERS = [
    r"每日进化",
    r"每天.*进化",
    r"每天自动",
    r"daily evolution",
    r"scheduled evolution",
    r"schedule",
]

DAILY_EVOLUTION_HINTS = {
    "daily schedule": [r"cron", r"schedule", r"每天", r"每日", r"定时"],
    "audit script": [r"daily_evolution_audit\.py", r"每日.*审计", r"daily evolution audit"],
    "github actions": [r"GitHub Actions", r"\.github/workflows", r"workflow"],
    "issue handoff": [r"issue", r"议题", r"问题单", r"handoff"],
    "release consistency": [r"check_release_consistency\.py"],
    "strategy gate": [r"strategy-gate\.md|策略判断|Strategy Gate"],
    "no unattended code rewrite": [r"不.*无人值守.*改", r"不.*随机改", r"不.*后台.*乱改", r"not.*unattended.*rewrite"],
}


def _line_starts(text: str, patterns: list[str]) -> list[re.Match[str]]:
    matches: list[re.Match[str]] = []
    for pattern in patterns:
        matches.extend(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
    return sorted(matches, key=lambda match: match.start())


def _field_content(text: str, patterns: list[str], all_markers: list[re.Match[str]]) -> str | None:
    starts = _line_starts(text, patterns)
    if not starts:
        return None

    start = starts[0]
    next_markers = [marker for marker in all_markers if marker.start() > start.start()]
    end = next_markers[0].start() if next_markers else len(text)
    line = text[start.start() : end]
    for pattern in patterns:
        stripped = re.sub(pattern, "", line, count=1, flags=re.IGNORECASE | re.MULTILINE)
        if stripped != line:
            return stripped.strip()
    return line.strip()


def lint_text(text: str, source: str) -> list[str]:
    errors: list[str] = []
    marker_patterns = [
        pattern
        for patterns in (list(SMART_FIELDS.values()) + list(REQUIRED_DIRECT.values()) + list(RESEARCH_FIELDS.values()))
        for pattern in patterns
    ]
    all_markers = _line_starts(text, marker_patterns)

    if re.search(r"^\s*/目标\b", text, flags=re.MULTILINE):
        errors.append(f"{source}: use `/goal`, not `/目标`")

    for name, patterns in SMART_FIELDS.items():
        if not _line_starts(text, patterns):
            errors.append(f"{source}: missing smart field `{name}`")

    decision_summary = _field_content(text, SMART_FIELDS["decision summary"], all_markers)
    if decision_summary:
        for name, patterns in SMART_SUMMARY_HINTS.items():
            if not any(re.search(pattern, decision_summary, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: decision summary missing `{name}`")

    default_assumptions = _field_content(text, SMART_FIELDS["default assumptions"], all_markers)
    if default_assumptions is not None and len(default_assumptions) < 16:
        errors.append(f"{source}: default assumptions are too thin")

    preference_application = _field_content(text, SMART_FIELDS["preference application"], all_markers)
    if preference_application is not None and len(preference_application) < 16:
        errors.append(f"{source}: preference application is too thin")

    feedback_adjustment = _field_content(text, SMART_FIELDS["feedback adjustment"], all_markers)
    if feedback_adjustment is not None and len(feedback_adjustment) < 16:
        errors.append(f"{source}: feedback adjustment is too thin")

    strategy_gate = _field_content(text, SMART_FIELDS["strategy gate"], all_markers)
    if strategy_gate:
        for name, patterns in STRATEGY_GATE_HINTS.items():
            if not any(re.search(pattern, strategy_gate, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: strategy gate missing `{name}`")
    elif strategy_gate is not None:
        errors.append(f"{source}: strategy gate is too thin")

    business_priority = _field_content(text, SMART_FIELDS["business priority"], all_markers)
    if business_priority:
        for name, patterns in BUSINESS_PRIORITY_HINTS.items():
            if not any(re.search(pattern, business_priority, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: business priority missing `{name}`")

    output_length = _field_content(text, SMART_FIELDS["output length"], all_markers)
    if output_length and not any(re.search(pattern, output_length, flags=re.IGNORECASE) for pattern in OUTPUT_LENGTH_HINTS):
        errors.append(f"{source}: output length should be short, standard, or full")

    choice_rationale = _field_content(text, SMART_FIELDS["choice rationale"], all_markers)
    if choice_rationale is not None and len(choice_rationale) < 24:
        errors.append(f"{source}: choice rationale is too thin")

    for name, patterns in REQUIRED_DIRECT.items():
        if not _line_starts(text, patterns):
            errors.append(f"{source}: missing required field `{name}`")

    external_information_none = bool(
        re.search(
            r"外部信息需求\s*=\s*不需要|External information need\s*=\s*none",
            text,
            flags=re.IGNORECASE,
        )
    )
    is_research_goal = (not external_information_none) and bool(
        re.search(
            r"联网研究|广域调研|Deep Research|业务应用|Broad Research|Business Application|Agent Reach|竞品|competitor|来源|检索|sources|search",
            text,
            flags=re.IGNORECASE,
        )
    )
    if is_research_goal:
        for name, patterns in RESEARCH_FIELDS.items():
            if not _line_starts(text, patterns):
                errors.append(f"{source}: research goal missing `{name}`")

        if not re.search(r"agent-reach\s+doctor", text, flags=re.IGNORECASE):
            errors.append(f"{source}: research goal should require `agent-reach doctor` or channel availability check")

        if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SOURCE_COUNT_HINTS):
            errors.append(f"{source}: research goal should name a concrete source count")

        for name, patterns in SOURCE_RECORD_HINTS.items():
            if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: research goal should record `{name}`")

        if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in ANTI_OVERCLAIM_HINTS):
            errors.append(f"{source}: research goal should prohibit overclaiming Agent Reach/full internet coverage")

        task_pack = _field_content(text, RESEARCH_FIELDS["task pack"], all_markers)
        if task_pack and not any(re.search(pattern, task_pack, flags=re.IGNORECASE) for pattern in TASK_PACK_HINTS):
            errors.append(f"{source}: task pack should name a supported pack")

        domain_pack = _field_content(text, RESEARCH_FIELDS["domain pack"], all_markers)
        if domain_pack and not any(re.search(pattern, domain_pack, flags=re.IGNORECASE) for pattern in DOMAIN_PACK_HINTS):
            errors.append(f"{source}: domain pack should name a supported pack or not applicable")

        tool_stack = _field_content(text, RESEARCH_FIELDS["tool stack"], all_markers) or ""
        for name, patterns in TOOL_STACK_HINTS.items():
            if not any(re.search(pattern, tool_stack, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: tool stack missing `{name}`")

        quality_gate = _field_content(text, RESEARCH_FIELDS["quality gate"], all_markers) or ""
        for name, patterns in QUALITY_GATE_HINTS.items():
            if not any(re.search(pattern, quality_gate, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: quality gate missing `{name}`")

    is_self_evolution_goal = any(
        re.search(pattern, text, flags=re.IGNORECASE) for pattern in SELF_EVOLUTION_TRIGGERS
    )
    if is_self_evolution_goal:
        for name, patterns in SELF_EVOLUTION_HINTS.items():
            if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: self-evolution goal missing `{name}`")

    is_daily_evolution_goal = any(
        re.search(pattern, text, flags=re.IGNORECASE) for pattern in DAILY_EVOLUTION_TRIGGERS
    )
    if is_daily_evolution_goal:
        for name, patterns in DAILY_EVOLUTION_HINTS.items():
            if not any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
                errors.append(f"{source}: daily evolution goal missing `{name}`")

    for pattern in PLACEHOLDERS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"{source}: unresolved placeholder matched `{pattern}`")

    for pattern in BAD_PHRASES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"{source}: unsafe vague phrase matched `{pattern}`")

    goal_line = next((line.strip() for line in text.splitlines() if line.strip().startswith("/goal")), "")
    if goal_line and len(goal_line.removeprefix("/goal").strip()) < 20:
        errors.append(f"{source}: /goal outcome is too short")

    verification = _field_content(text, REQUIRED_DIRECT["verification"], all_markers)
    if verification is not None and len(verification) < 16:
        errors.append(f"{source}: verification is too thin")
    if verification and not any(re.search(pattern, verification, flags=re.IGNORECASE) for pattern in EVIDENCE_HINTS):
        errors.append(f"{source}: verification should name concrete evidence")

    for name, patterns in REQUIRED_DIRECT.items():
        if name == "command":
            continue
        content = _field_content(text, patterns, all_markers)
        if content is not None and len(content) < 10:
            errors.append(f"{source}: `{name}` content is too thin")

    if is_research_goal:
        for name, patterns in RESEARCH_FIELDS.items():
            content = _field_content(text, patterns, all_markers)
            if content is not None and len(content) < 16:
                errors.append(f"{source}: `{name}` content is too thin")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate_xiaowei_goal.py <file> [<file> ...]", file=sys.stderr)
        return 2

    errors: list[str] = []
    for raw_path in argv[1:]:
        path = Path(raw_path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{path}: cannot read file: {exc}")
            continue
        errors.extend(lint_text(text, str(path)))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Xiaowei goal validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
