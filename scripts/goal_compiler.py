#!/usr/bin/env python3
"""Validate Agent-authored semantics, record review consistency, and dispatch one safe step.

The CLI is deliberately not an AI model. `compile` requires a complete semantic
input produced by an Agent/Skill (or an explicitly labelled deterministic demo
fixture). The CLI serializes that input, rejects cross-domain or incomplete
contracts, checks saved review/payload consistency, and exposes a
small whitelist of deterministic text-artifact dispatches.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_REQUEST = ROOT / "contest" / "demo-fixtures" / "request.txt"
DEFAULT_DEMO_SEMANTIC = ROOT / "contest" / "demo-fixtures" / "semantic-input.demo.json"
DEFAULT_DEMO_WORKSPACE = Path("/tmp/xiaowei-goal-demo-execution-workspace")
SCHEMA_VERSION = "1.2"
SEMANTIC_SCHEMA_VERSION = "1.0"

SUPPORTED_TASK_TYPES = {"website", "app", "SEO", "competitor", "growth", "coding", "docs", "mixed"}
SUPPORTED_SEMANTIC_MODES = {"agent_result", "deterministic_demo_fixture", "test_fixture"}

VAGUE_METRIC_PATTERNS = (
    r"好看",
    r"更好",
    r"尽快",
    r"越快越好",
    r"高质量",
    r"提升体验",
    r"用户满意",
    r"感觉不错",
    r"看起来",
    r"挺好",
    r"不错",
    r"更专业",
    r"令人满意",
    r"beautiful",
    r"better",
    r"as fast as possible",
    r"high[ -]?quality",
    r"looks? good",
    r"nice",
    r"professional",
    r"satisfying",
)

SUBJECTIVE_METHOD_PATTERNS = (
    r"主观",
    r"感觉",
    r"审美",
    r"凭印象",
    r"人工感受",
    r"subjective",
    r"gut feel",
    r"visual appeal only",
    r"qualitative only",
)

TASK_PACKS = {
    "website": {"网站/落地页改版包"},
    "app": {"App MVP 研究包"},
    "SEO": {"SEO 内容集群包"},
    "competitor": {"竞品分析包"},
    "growth": {"增长实验包"},
    "coding": {"Coding 回归包", "不适用"},
    "docs": {"文档交付包", "不适用"},
    "mixed": {"混合验证包", "不适用"},
}

DOMAIN_FORBIDDEN = {
    "coding": ("IdeaSignal", "15-25", "网站/落地页改版包", "CTA", "首屏", "landing page"),
    "SEO": ("IdeaSignal", "write_python_regression_fixture", "Coding 回归包"),
}

ACTION_POLICIES: dict[str, dict[str, Any]] = {
    "write_static_hypothesis_page": {
        "task_types": {"website", "app"},
        "artifact_kind": "html",
        "suffix": ".html",
        "media_type": "text/html",
        "validators": (
            "nonempty",
            "html_single_h1",
            "html_primary_cta",
            "assumption_label",
            "no_external_urls",
            "no_unresolved_template",
        ),
        "measurement_methods": {"HTML 结构检查", "HTML structure checks"},
        "metric_targets": {
            "min_html_pages": 1,
            "min_primary_cta": 1,
            "assumption_label_required": True,
        },
        "dispatch": "write_approved_text_artifact",
    },
    "write_python_regression_fixture": {
        "task_types": {"coding"},
        "artifact_kind": "python",
        "suffix": ".py",
        "media_type": "text/x-python",
        "validators": ("nonempty", "python_syntax", "regression_marker", "no_unresolved_template"),
        "measurement_methods": {"Python 语法与回归夹具检查", "Python syntax and regression fixture checks"},
        "metric_targets": {
            "min_python_files": 1,
            "syntax_valid": True,
            "regression_case_required": True,
        },
        "dispatch": "write_approved_text_artifact",
    },
    "write_markdown_validation_brief": {
        "task_types": {"SEO", "competitor", "growth", "docs", "mixed"},
        "artifact_kind": "markdown",
        "suffix": ".md",
        "media_type": "text/markdown",
        "validators": ("nonempty", "markdown_heading", "source_reference", "no_unresolved_template"),
        "measurement_methods": {"Markdown 结构与来源引用检查", "Markdown structure and source reference checks"},
        "metric_targets": {
            "min_markdown_files": 1,
            "heading_required": True,
            "source_reference_required": True,
        },
        "dispatch": "write_approved_text_artifact",
    },
}

EXECUTION_BOUND_FIELDS = (
    "schema_version",
    "contract_id",
    "request",
    "semantic_compilation",
    "semantic_input_snapshot",
    "execution_workspace",
    "smart_router",
    "default_assumptions",
    "strategy_gate",
    "tool_evidence_gate",
    "evidence_bundle",
    "goal_plan",
    "first_step",
)

SEMANTIC_DERIVED_FIELDS = (
    "smart_router",
    "default_assumptions",
    "strategy_gate",
    "tool_evidence_gate",
    "goal_plan",
    "first_step",
)


class CompilerError(ValueError):
    """Raised for invalid input, unsafe paths, or failed execution gates."""


def compiler_version() -> str:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    return str(manifest["version"])


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    return f"{prefix}-{sha256_value(value)[:12]}"


def normalized_request(value: str) -> str:
    return " ".join(value.split())


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompilerError(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CompilerError(f"expected a JSON object in {path}")
    return value


def ensure_new_file(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.exists():
        raise CompilerError(f"refusing to overwrite existing file: {resolved}")
    if resolved in {Path("/").resolve(), Path.home().resolve(), ROOT.resolve()}:
        raise CompilerError(f"refusing protected file path: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def write_json(path: Path, value: Any, *, refuse_existing: bool = False) -> None:
    target = ensure_new_file(path) if refuse_existing else path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str, *, refuse_existing: bool = False) -> None:
    target = ensure_new_file(path) if refuse_existing else path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def prepare_new_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved in {Path("/").resolve(), Path.home().resolve(), ROOT.resolve()}:
        raise CompilerError(f"refusing protected output directory: {resolved}")
    if resolved.exists():
        raise CompilerError(f"output already exists; choose a new directory: {resolved}")
    resolved.mkdir(parents=True)
    return resolved


def safe_relative_path(value: str) -> bool:
    path = Path(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts


def searchable_text(value: Any) -> str:
    """Flatten only payload values so schema keys/acceptance lists cannot self-satisfy checks."""
    if isinstance(value, dict):
        return "\n".join(searchable_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(searchable_text(item) for item in value)
    return str(value)


def infer_request_task_type(request: str) -> str:
    text = request.lower()
    if any(
        token in text
        for token in (
            "bug",
            "fix",
            "parser",
            "csv",
            "python",
            "javascript",
            "typescript",
            "pytest",
            "修复",
            "崩溃",
            "代码",
            "编程",
            "程序",
            "脚本",
            "函数",
            "单元测试",
            "回归测试",
            "api 报错",
        )
    ):
        return "coding"
    if any(token in text for token in ("seo", "关键词", "serp", "搜索流量")):
        return "SEO"
    if any(token in text for token in ("竞品", "competitor")):
        return "competitor"
    if any(token in text for token in ("增长", "growth", "获客")):
        return "growth"
    if any(token in text for token in ("网站", "官网", "落地页", "website", "landing page")):
        return "website"
    if any(token in text for token in ("app", "saas", "应用")):
        return "app"
    if any(token in text for token in ("文档", "readme", "docs")):
        return "docs"
    return "unknown"


def load_semantic_input(path: Path) -> dict[str, Any]:
    semantic = load_json(path)
    first_step = semantic.get("first_step")
    if not isinstance(first_step, dict):
        return semantic
    content_file = first_step.get("content_file")
    if content_file:
        if not isinstance(content_file, str) or not safe_relative_path(content_file):
            raise CompilerError("first_step.content_file must be a safe path relative to semantic input")
        base = path.expanduser().resolve().parent
        content_path = (base / content_file).resolve()
        try:
            content_path.relative_to(base)
        except ValueError as exc:
            raise CompilerError("first_step.content_file escapes semantic input directory") from exc
        try:
            content = content_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CompilerError(f"cannot read first-step content file: {content_path}: {exc}") from exc
        first_step = copy.deepcopy(first_step)
        first_step.pop("content_file", None)
        first_step["content_template"] = content
        first_step["content_source"] = content_file
        first_step["content_sha256"] = sha256_text(content)
        semantic = copy.deepcopy(semantic)
        semantic["first_step"] = first_step
    return semantic


def _semantic_required_object(semantic: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = semantic.get(key)
    if not isinstance(value, dict):
        errors.append(f"semantic_input.{key}: must be an object")
        return {}
    return value


def semantic_input_errors(request: str, semantic: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if semantic.get("semantic_schema_version") != SEMANTIC_SCHEMA_VERSION:
        errors.append(f"semantic_input.semantic_schema_version: expected {SEMANTIC_SCHEMA_VERSION}")
    if normalized_request(str(semantic.get("request", ""))) != normalized_request(request):
        errors.append("semantic_input.request: must exactly match the compiled request")

    provenance = _semantic_required_object(semantic, "provenance", errors)
    mode = provenance.get("mode")
    if mode not in SUPPORTED_SEMANTIC_MODES:
        errors.append(f"semantic_input.provenance.mode: unsupported mode `{mode}`")
    if not str(provenance.get("producer", "")).strip():
        errors.append("semantic_input.provenance.producer: is required")
    if not isinstance(provenance.get("live_ai_claimed"), bool):
        errors.append("semantic_input.provenance.live_ai_claimed: must be boolean")
    if "liveAiClaimed" in provenance and provenance.get("liveAiClaimed") != provenance.get("live_ai_claimed"):
        errors.append("semantic_input.provenance: live AI provenance flags disagree")
    if mode == "deterministic_demo_fixture" and provenance.get("live_ai_claimed") is not False:
        errors.append("semantic_input.provenance: deterministic demo fixtures must set live_ai_claimed=false")
    if mode == "agent_result" and not str(provenance.get("transcript_ref", "")).strip():
        errors.append("semantic_input.provenance.transcript_ref: agent results require a transcript reference")

    router = _semantic_required_object(semantic, "smart_router", errors)
    task_type = router.get("task_type")
    if task_type not in SUPPORTED_TASK_TYPES:
        errors.append(f"semantic_input.smart_router.task_type: unsupported task type `{task_type}`")
    inferred = infer_request_task_type(request)
    if inferred != "unknown" and task_type != inferred:
        errors.append(f"semantic_input domain mismatch: request implies `{inferred}` but router says `{task_type}`")
    for key in ("maturity", "risk_level", "external_information_need", "output_length", "routing_reason"):
        if not str(router.get(key, "")).strip():
            errors.append(f"semantic_input.smart_router.{key}: is required")

    assumptions = semantic.get("default_assumptions")
    if not isinstance(assumptions, list) or not assumptions or any(len(str(item).strip()) < 8 for item in assumptions):
        errors.append("semantic_input.default_assumptions: needs at least one concrete assumption")

    strategy = _semantic_required_object(semantic, "strategy_gate", errors)
    for key in ("problem_reframe", "smallest_bet"):
        if len(str(strategy.get(key, "")).strip()) < 20:
            errors.append(f"semantic_input.strategy_gate.{key}: is too thin")
    if not isinstance(strategy.get("success_metrics"), list) or not strategy.get("success_metrics"):
        errors.append("semantic_input.strategy_gate.success_metrics: at least one metric is required")
    if not isinstance(strategy.get("disconfirming_evidence"), list) or not strategy.get("disconfirming_evidence"):
        errors.append("semantic_input.strategy_gate.disconfirming_evidence: at least one signal is required")
    if not isinstance(strategy.get("kill_criteria"), list) or not strategy.get("kill_criteria"):
        errors.append("semantic_input.strategy_gate.kill_criteria: at least one stop rule is required")

    tool_gate = _semantic_required_object(semantic, "tool_evidence_gate", errors)
    research_required = tool_gate.get("research_required")
    if not isinstance(research_required, bool):
        errors.append("semantic_input.tool_evidence_gate.research_required: must be boolean")
    external_none = router.get("external_information_need") in {"不需要", "none"}
    if isinstance(research_required, bool) and research_required == external_none:
        errors.append("semantic_input: research_required must agree with external_information_need")
    for key in ("permitted_tools", "authorization_required_for", "blocked_claims"):
        if not isinstance(tool_gate.get(key), list) or not tool_gate.get(key):
            errors.append(f"semantic_input.tool_evidence_gate.{key}: must be a non-empty list")
    evidence_requirements = tool_gate.get("evidence_requirements")
    if not isinstance(evidence_requirements, list) or (research_required and not evidence_requirements):
        errors.append(
            "semantic_input.tool_evidence_gate.evidence_requirements: "
            "must be a list and non-empty for research tasks"
        )
    elif isinstance(evidence_requirements, list):
        for index, requirement in enumerate(evidence_requirements):
            if not isinstance(requirement, dict):
                errors.append(f"semantic_input.tool_evidence_gate.evidence_requirements[{index}]: must be an object")
                continue
            if not str(requirement.get("claim_type", "")).strip():
                errors.append(f"semantic_input.tool_evidence_gate.evidence_requirements[{index}].claim_type: is required")
            minimum = requirement.get("minimum_independent_sources")
            if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
                errors.append(
                    f"semantic_input.tool_evidence_gate.evidence_requirements[{index}].minimum_independent_sources: "
                    "must be a positive integer"
                )
            record_fields = requirement.get("record_fields")
            if not isinstance(record_fields, list) or not record_fields or any(not str(item).strip() for item in record_fields):
                errors.append(f"semantic_input.tool_evidence_gate.evidence_requirements[{index}].record_fields: must be non-empty")

    goal_plan = _semantic_required_object(semantic, "goal_plan", errors)
    for key in (
        "preference_application",
        "feedback_adjustment",
        "business_priority",
        "output_length_reason",
        "choice_rationale",
        "outcome",
        "task_pack_application",
        "domain_pack_application",
        "tool_stack",
        "deliverables",
        "quality_gate",
        "verification",
        "limits",
        "boundary",
        "progress_rules",
        "stop_criteria",
        "pause_conditions",
    ):
        if len(str(goal_plan.get(key, "")).strip()) < 8:
            errors.append(f"semantic_input.goal_plan.{key}: is required and must be concrete")
    for key in ("task_pack", "domain_pack"):
        if not str(goal_plan.get(key, "")).strip():
            errors.append(f"semantic_input.goal_plan.{key}: is required")
    if task_type in TASK_PACKS and goal_plan.get("task_pack") not in TASK_PACKS[task_type]:
        errors.append(f"semantic_input.goal_plan.task_pack: `{goal_plan.get('task_pack')}` does not match `{task_type}`")
    stages = goal_plan.get("research_stages")
    if research_required:
        if not isinstance(stages, dict) or any(len(str(stages.get(key, "")).strip()) < 16 for key in ("stage_1", "stage_2", "stage_3")):
            errors.append("semantic_input.goal_plan.research_stages: research tasks require three concrete stages")
    elif stages not in (None, {}):
        errors.append("semantic_input.goal_plan.research_stages: direct tasks must not contain research stages")

    first_step = _semantic_required_object(semantic, "first_step", errors)
    action = first_step.get("action")
    policy = ACTION_POLICIES.get(str(action))
    if policy is None:
        errors.append(f"semantic_input.first_step.action: unsupported action `{action}`")
    else:
        if task_type not in policy["task_types"]:
            errors.append(f"semantic_input.first_step.action: `{action}` is not allowed for `{task_type}`")
        if first_step.get("artifact_kind") != policy["artifact_kind"]:
            errors.append("semantic_input.first_step.artifact_kind: does not match action policy")
        if first_step.get("media_type") != policy["media_type"]:
            errors.append("semantic_input.first_step.media_type: does not match action policy")
        if tuple(first_step.get("validators", [])) != policy["validators"]:
            errors.append("semantic_input.first_step.validators: must exactly match the action policy")
        artifact = str(first_step.get("primary_artifact", ""))
        if not safe_relative_path(artifact) or Path(artifact).suffix != policy["suffix"]:
            errors.append("semantic_input.first_step.primary_artifact: unsafe path or wrong action suffix")
        output_directory = str(first_step.get("output_directory", ""))
        if not safe_relative_path(output_directory) or Path(artifact).parent != Path(output_directory):
            errors.append("semantic_input.first_step: artifact must be directly inside output_directory")
        expected_report = str(Path(output_directory) / "execution-report.json")
        if first_step.get("report_path") != expected_report:
            errors.append("semantic_input.first_step.report_path: must be execution-report.json in output_directory")
        if not str(first_step.get("content_template", "")).strip():
            errors.append("semantic_input.first_step.content_template: is required")
        content_hash = first_step.get("content_sha256")
        if content_hash and content_hash != sha256_text(str(first_step.get("content_template", ""))):
            errors.append("semantic_input.first_step.content_sha256: does not match content_template")

    acceptance = first_step.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("semantic_input.first_step.acceptance: must be an object")
        acceptance = {}
    if acceptance.get("task_type") != task_type:
        errors.append("semantic_input.first_step.acceptance.task_type: must match router task_type")
    required_terms = acceptance.get("required_terms")
    forbidden_terms = acceptance.get("forbidden_terms")
    if (
        not isinstance(required_terms, list)
        or not required_terms
        or any(not str(term).strip() for term in required_terms)
    ):
        errors.append("semantic_input.first_step.acceptance.required_terms: entries must be non-empty strings")
        required_terms = []
    if not isinstance(forbidden_terms, list):
        errors.append("semantic_input.first_step.acceptance.forbidden_terms: must be a list")
        forbidden_terms = []

    domain_first_step = copy.deepcopy(first_step)
    domain_first_step.pop("acceptance", None)
    semantic_domain_text = searchable_text({"goal_plan": goal_plan, "first_step": domain_first_step})
    for term in required_terms:
        if str(term) not in semantic_domain_text:
            errors.append(f"semantic_input domain acceptance: required term `{term}` is absent")
    for term in [*forbidden_terms, *DOMAIN_FORBIDDEN.get(str(task_type), ())]:
        if str(term) and str(term).lower() in semantic_domain_text.lower():
            errors.append(f"semantic_input domain acceptance: forbidden term `{term}` leaked into `{task_type}`")
    return errors


def resolve_workspace_root(value: str | Path) -> Path:
    raw_root = Path(value).expanduser()
    if not raw_root.is_absolute():
        raise CompilerError(f"execution workspace must be an explicit absolute directory: {value}")
    root = raw_root.resolve()
    if root in {Path("/").resolve(), Path.home().resolve()}:
        raise CompilerError(f"execution workspace must be an explicit, non-home absolute directory: {root}")
    return root


def build_contract(
    request: str,
    semantic: dict[str, Any],
    *,
    workspace_root: str | Path,
    evidence_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request_text = normalized_request(request)
    if len(request_text) < 8:
        raise CompilerError("request must contain at least 8 non-whitespace characters")
    fatal = semantic_input_errors(request_text, semantic)
    if fatal:
        raise CompilerError("semantic input rejected:\n- " + "\n- ".join(fatal))

    semantic_hash = sha256_value(semantic)
    request_hash = sha256_text(request_text)
    workspace = resolve_workspace_root(workspace_root)
    workspace_hash = sha256_text(str(workspace))
    identity = {
        "schema_version": SCHEMA_VERSION,
        "request_sha256": request_hash,
        "semantic_input_sha256": semantic_hash,
        "execution_workspace_sha256": workspace_hash,
    }
    provenance = copy.deepcopy(semantic["provenance"])
    return {
        "schema_version": SCHEMA_VERSION,
        "compiler": {"name": "Goal Compiler | 需求编译器", "version": compiler_version(), "kind": "deterministic-cli"},
        "contract_id": stable_id("goal", identity),
        "request": {"raw": request_text, "request_sha256": request_hash},
        "semantic_compilation": {
            **provenance,
            "semantic_schema_version": semantic["semantic_schema_version"],
            "semantic_input_sha256": semantic_hash,
        },
        "semantic_input_snapshot": copy.deepcopy(semantic),
        "execution_workspace": {
            "root": str(workspace),
            "root_sha256": workspace_hash,
        },
        "smart_router": copy.deepcopy(semantic["smart_router"]),
        "default_assumptions": copy.deepcopy(semantic["default_assumptions"]),
        "strategy_gate": copy.deepcopy(semantic["strategy_gate"]),
        "tool_evidence_gate": copy.deepcopy(semantic["tool_evidence_gate"]),
        "evidence_bundle": copy.deepcopy(evidence_bundle or semantic.get("evidence_bundle") or {"sources": [], "claims": []}),
        "goal_plan": copy.deepcopy(semantic["goal_plan"]),
        "first_step": copy.deepcopy(semantic["first_step"]),
        "human_review": {
            "decision": "pending",
            "reviewer": None,
            "reason": "",
            "changed_fields": [],
            "approved_payload_sha256": None,
            "sign_off": "PENDING HUMAN SIGN-OFF",
        },
    }


def expected_contract_id(contract: dict[str, Any]) -> str:
    request = contract.get("request", {})
    snapshot = contract.get("semantic_input_snapshot")
    workspace = contract.get("execution_workspace", {})
    request_raw = str(request.get("raw", "")) if isinstance(request, dict) else ""
    semantic_hash = sha256_value(snapshot) if isinstance(snapshot, dict) else None
    workspace_root = str(workspace.get("root", "")) if isinstance(workspace, dict) else ""
    identity = {
        "schema_version": contract.get("schema_version"),
        "request_sha256": sha256_text(request_raw),
        "semantic_input_sha256": semantic_hash,
        "execution_workspace_sha256": sha256_text(workspace_root),
    }
    return stable_id("goal", identity)


def expected_output_directory(contract: dict[str, Any]) -> Path:
    workspace = contract.get("execution_workspace")
    first_step = contract.get("first_step")
    if not isinstance(workspace, dict) or not isinstance(first_step, dict):
        raise CompilerError("execution_workspace and first_step must be objects")
    root = resolve_workspace_root(str(workspace.get("root", "")))
    relative = str(first_step.get("output_directory", ""))
    if not safe_relative_path(relative):
        raise CompilerError("first_step.output_directory must be a safe relative path")
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise CompilerError("resolved output directory escapes the approved execution workspace") from exc
    if target == root:
        raise CompilerError("resolved output directory must be below the approved execution workspace")
    return target


def _identity_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION}")
    request = contract.get("request")
    if not isinstance(request, dict):
        errors.append("request: must be an object")
    else:
        raw = str(request.get("raw", ""))
        if request.get("request_sha256") != sha256_text(raw):
            errors.append("request.request_sha256: does not match request.raw")
    semantic = contract.get("semantic_compilation")
    if not isinstance(semantic, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(semantic.get("semantic_input_sha256", ""))):
        errors.append("semantic_compilation.semantic_input_sha256: must be a SHA-256 digest")
    workspace = contract.get("execution_workspace")
    if not isinstance(workspace, dict):
        errors.append("execution_workspace: must be an object")
    else:
        try:
            root = resolve_workspace_root(str(workspace.get("root", "")))
        except CompilerError as exc:
            errors.append(f"execution_workspace.root: {exc}")
        else:
            if str(root) != str(workspace.get("root", "")):
                errors.append("execution_workspace.root: must be canonical and absolute")
            if workspace.get("root_sha256") != sha256_text(str(root)):
                errors.append("execution_workspace.root_sha256: does not match root")
    if contract.get("contract_id") != expected_contract_id(contract):
        errors.append("contract_id: inconsistent with request, saved semantic snapshot, schema, or execution workspace")
    try:
        expected_output_directory(contract)
    except CompilerError as exc:
        errors.append(f"execution_workspace: {exc}")
    return errors


def _expected_semantic_compilation(snapshot: dict[str, Any]) -> dict[str, Any]:
    provenance = snapshot.get("provenance")
    return {
        **(copy.deepcopy(provenance) if isinstance(provenance, dict) else {}),
        "semantic_schema_version": snapshot.get("semantic_schema_version"),
        "semantic_input_sha256": sha256_value(snapshot),
    }


def _semantic_snapshot_errors(contract: dict[str, Any]) -> list[str]:
    """Rebuild all semantic derivatives from the saved source snapshot."""
    snapshot = contract.get("semantic_input_snapshot")
    if not isinstance(snapshot, dict):
        return ["semantic_input_snapshot: must be the complete saved Agent semantic object"]

    errors: list[str] = []
    request = contract.get("request")
    raw_request = str(request.get("raw", "")) if isinstance(request, dict) else ""
    for error in semantic_input_errors(raw_request, snapshot):
        errors.append(error.replace("semantic_input", "semantic_input_snapshot", 1))

    semantic_compilation = contract.get("semantic_compilation")
    expected_compilation = _expected_semantic_compilation(snapshot)
    if semantic_compilation != expected_compilation:
        errors.append("semantic_compilation: does not match the saved semantic input snapshot")

    expected_fields = {field: copy.deepcopy(snapshot.get(field)) for field in SEMANTIC_DERIVED_FIELDS}
    review = contract.get("human_review")
    if isinstance(review, dict) and review.get("decision") == "approved":
        metric_override = review.get("success_metric_override")
        expected_changed_fields: list[str] = []
        if metric_override is not None:
            metrics = expected_fields.get("strategy_gate", {}).get("success_metrics", [])
            metric_id = review.get("metric_id")
            matches = [index for index, metric in enumerate(metrics) if isinstance(metric, dict) and metric.get("id") == metric_id]
            if not isinstance(metric_override, dict) or len(matches) != 1:
                errors.append("human_review.success_metric_override: cannot be reconstructed from the saved semantic snapshot")
            else:
                index = matches[0]
                metrics[index] = copy.deepcopy(metric_override)
                expected_changed_fields.append(f"strategy_gate.success_metrics[{index}]")
        if review.get("changed_fields") != expected_changed_fields:
            errors.append("human_review.changed_fields: does not match the recorded metric override")

    for field, expected in expected_fields.items():
        if contract.get(field) != expected:
            errors.append(f"{field}: derived value drifted from semantic_input_snapshot")
    return errors


def approved_payload(contract: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(contract.get(key)) for key in EXECUTION_BOUND_FIELDS}


def approved_payload_sha256(contract: dict[str, Any]) -> str:
    return sha256_value(approved_payload(contract))


def expected_review_id(contract: dict[str, Any]) -> str:
    review = contract.get("human_review", {})
    seed = {
        "contract_id": contract.get("contract_id"),
        "approved_payload_sha256": review.get("approved_payload_sha256") if isinstance(review, dict) else None,
        "reviewer": review.get("reviewer") if isinstance(review, dict) else None,
        "reason": review.get("reason") if isinstance(review, dict) else None,
        "decision": review.get("decision") if isinstance(review, dict) else None,
        "review_kind": review.get("review_kind") if isinstance(review, dict) else None,
        "metric_id": review.get("metric_id") if isinstance(review, dict) else None,
        "success_metric_override": review.get("success_metric_override") if isinstance(review, dict) else None,
        "changed_fields": review.get("changed_fields") if isinstance(review, dict) else None,
        "acknowledgements": review.get("acknowledgements") if isinstance(review, dict) else None,
        "sign_off": review.get("sign_off") if isinstance(review, dict) else None,
    }
    return stable_id("review", seed)


def _contains_number_or_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if isinstance(value, dict):
        return any(_contains_number_or_boolean(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_number_or_boolean(item) for item in value)
    return bool(re.search(r"\d", str(value)))


def _metric_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    strategy = contract.get("strategy_gate", {})
    first_step = contract.get("first_step", {})
    if not isinstance(strategy, dict) or not isinstance(first_step, dict):
        return ["strategy_gate and first_step must be objects"]
    policy = ACTION_POLICIES.get(str(first_step.get("action")))
    metrics = strategy.get("success_metrics")
    if not isinstance(metrics, list) or not metrics:
        return ["strategy_gate.success_metrics: at least one metric is required"]

    metric_id = first_step.get("metric_id")
    matched = [metric for metric in metrics if isinstance(metric, dict) and metric.get("id") == metric_id]
    if len(matched) != 1:
        errors.append("first_step.metric_id: must match exactly one success metric")
    for index, metric in enumerate(metrics):
        prefix = f"strategy_gate.success_metrics[{index}]"
        if not isinstance(metric, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        statement = str(metric.get("statement", "")).strip()
        method = str(metric.get("measurement", {}).get("method", "")) if isinstance(metric.get("measurement"), dict) else ""
        if len(statement) < 10:
            errors.append(f"{prefix}.statement: must describe an observable outcome")
        for pattern in VAGUE_METRIC_PATTERNS:
            if re.search(pattern, statement, flags=re.IGNORECASE):
                errors.append(f"{prefix}.statement: vague wording matched `{pattern}`")
                break
        for pattern in SUBJECTIVE_METHOD_PATTERNS:
            if re.search(pattern, method, flags=re.IGNORECASE):
                errors.append(f"{prefix}.measurement.method: subjective method matched `{pattern}`")
                break
        measurement = metric.get("measurement")
        if not isinstance(measurement, dict):
            errors.append(f"{prefix}.measurement: must be an object")
            continue
        target = measurement.get("target")
        if not isinstance(target, dict) or not target or not _contains_number_or_boolean(target):
            errors.append(f"{prefix}.measurement.target: needs explicit number or boolean gates")
        if metric.get("id") == metric_id and policy:
            if method not in policy["measurement_methods"]:
                errors.append(f"{prefix}.measurement.method: does not correspond to action `{first_step.get('action')}`")
            for key, expected in policy["metric_targets"].items():
                if not isinstance(target, dict) or target.get(key) != expected:
                    errors.append(f"{prefix}.measurement.target.{key}: expected {expected!r} for action")
            if metric.get("evidence_path") != first_step.get("report_path"):
                errors.append(f"{prefix}.evidence_path: must equal first_step.report_path")
    return errors


def _evidence_errors(contract: dict[str, Any]) -> list[str]:
    gate = contract.get("tool_evidence_gate", {})
    bundle = contract.get("evidence_bundle", {})
    if not isinstance(gate, dict):
        return ["tool_evidence_gate: must be an object"]
    if not gate.get("research_required"):
        return []
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["evidence_bundle: research-required contracts need an evidence object"]
    sources = bundle.get("sources")
    claims = bundle.get("claims")
    if not isinstance(sources, list) or not sources:
        errors.append("evidence_bundle.sources: research-required contract needs recorded sources")
        sources = []
    if not isinstance(claims, list) or not claims:
        errors.append("evidence_bundle.claims: research-required contract needs source-backed claims")
        claims = []

    source_map: dict[str, dict[str, Any]] = {}
    source_urls: set[str] = set()
    requirements = gate.get("evidence_requirements", [])
    configured_record_fields: set[str] = set()
    for requirement in requirements if isinstance(requirements, list) else []:
        if not isinstance(requirement, dict):
            continue
        record_fields = requirement.get("record_fields")
        if isinstance(record_fields, list):
            configured_record_fields.update(str(field).strip() for field in record_fields if str(field).strip())
    required_source_fields = {
        "id",
        "title",
        "url",
        "source_type",
        "tool_channel",
        "access_limit",
        *configured_record_fields,
    }
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"evidence_bundle.sources[{index}]: must be an object")
            continue
        missing = [key for key in sorted(required_source_fields) if not str(source.get(key, "")).strip()]
        if missing:
            errors.append(f"evidence_bundle.sources[{index}]: missing {missing}")
        source_id = str(source.get("id", ""))
        source_url = str(source.get("url", "")).strip()
        if source_url and not re.match(r"^https?://[^\s]+$", source_url, flags=re.IGNORECASE):
            errors.append(f"evidence_bundle.sources[{index}].url: must be an HTTP(S) URL")
        if source_url in source_urls:
            errors.append(f"evidence_bundle.sources[{index}].url: duplicate URL is not an independent source")
        elif source_url:
            source_urls.add(source_url)
        if source_id in source_map:
            errors.append(f"evidence_bundle.sources[{index}].id: duplicate `{source_id}`")
        elif source_id:
            source_map[source_id] = source

    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"evidence_bundle.claims[{index}]: must be an object")
            continue
        if not str(claim.get("claim_type", "")).strip():
            errors.append(f"evidence_bundle.claims[{index}].claim_type: is required")
        if len(str(claim.get("statement", "")).strip()) < 8:
            errors.append(f"evidence_bundle.claims[{index}].statement: must record the source-backed claim")
        if not isinstance(claim.get("source_ids"), list) or not claim.get("source_ids"):
            errors.append(f"evidence_bundle.claims[{index}].source_ids: must be non-empty")
    for requirement_index, requirement in enumerate(requirements if isinstance(requirements, list) else []):
        if not isinstance(requirement, dict):
            errors.append(f"tool_evidence_gate.evidence_requirements[{requirement_index}]: must be an object")
            continue
        claim_type = requirement.get("claim_type")
        minimum = requirement.get("minimum_independent_sources")
        if not isinstance(minimum, int) or minimum < 1:
            errors.append(f"tool_evidence_gate.evidence_requirements[{requirement_index}]: invalid source minimum")
            continue
        matching_claims = [claim for claim in claims if isinstance(claim, dict) and claim.get("claim_type") == claim_type]
        if not matching_claims:
            errors.append(f"evidence_bundle.claims: missing claim_type `{claim_type}`")
            continue
        requirement_satisfied = False
        for claim in matching_claims:
            source_ids = claim.get("source_ids")
            if not isinstance(source_ids, list):
                continue
            unique_ids = set(str(item) for item in source_ids)
            unknown = unique_ids.difference(source_map)
            if unknown:
                errors.append(f"evidence_bundle claim `{claim_type}` references unknown sources {sorted(unknown)}")
            if len(unique_ids.intersection(source_map)) >= minimum:
                requirement_satisfied = True
        if not requirement_satisfied:
            errors.append(f"evidence_bundle claim `{claim_type}` needs at least {minimum} independent sources")
    return errors


def _domain_action_errors(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    router = contract.get("smart_router", {})
    first_step = contract.get("first_step", {})
    goal_plan = contract.get("goal_plan", {})
    if not isinstance(router, dict) or not isinstance(first_step, dict) or not isinstance(goal_plan, dict):
        return ["smart_router, goal_plan, and first_step must be objects"]
    task_type = router.get("task_type")
    if task_type not in SUPPORTED_TASK_TYPES:
        errors.append(f"smart_router.task_type: unsupported `{task_type}`")
    request = contract.get("request", {})
    raw_request = str(request.get("raw", "")) if isinstance(request, dict) else ""
    inferred = infer_request_task_type(raw_request)
    if inferred != "unknown" and task_type != inferred:
        errors.append(f"contract domain mismatch: request implies `{inferred}` but router says `{task_type}`")
    if task_type in TASK_PACKS and goal_plan.get("task_pack") not in TASK_PACKS[task_type]:
        errors.append(f"goal_plan.task_pack: does not match task type `{task_type}`")

    action = str(first_step.get("action", ""))
    policy = ACTION_POLICIES.get(action)
    if policy is None:
        return [*errors, f"first_step.action: unsupported action `{action}`"]
    if task_type not in policy["task_types"]:
        errors.append(f"first_step.action: `{action}` is not allowed for `{task_type}`")
    if first_step.get("artifact_kind") != policy["artifact_kind"]:
        errors.append("first_step.artifact_kind: does not match action whitelist")
    if first_step.get("media_type") != policy["media_type"]:
        errors.append("first_step.media_type: does not match action whitelist")
    if tuple(first_step.get("validators", [])) != policy["validators"]:
        errors.append("first_step.validators: must exactly match action whitelist")
    artifact = str(first_step.get("primary_artifact", ""))
    if not safe_relative_path(artifact) or Path(artifact).suffix != policy["suffix"]:
        errors.append("first_step.primary_artifact: unsafe or incompatible with action")
    output_directory = str(first_step.get("output_directory", ""))
    if Path(artifact).parent != Path(output_directory):
        errors.append("first_step.primary_artifact: must be directly inside output_directory")
    if first_step.get("report_path") != str(Path(output_directory) / "execution-report.json"):
        errors.append("first_step.report_path: inconsistent with output_directory")
    content = str(first_step.get("content_template", ""))
    content_hash = first_step.get("content_sha256")
    if content_hash and content_hash != sha256_text(content):
        errors.append("first_step.content_sha256: does not match content_template")

    acceptance = first_step.get("acceptance", {})
    if not isinstance(acceptance, dict) or acceptance.get("task_type") != task_type:
        errors.append("first_step.acceptance.task_type: must match router")
        acceptance = {}
    required_terms = acceptance.get("required_terms")
    if (
        not isinstance(required_terms, list)
        or not required_terms
        or any(not str(term).strip() for term in required_terms)
    ):
        errors.append("first_step.acceptance.required_terms: entries must be non-empty strings")
        required_terms = []
    domain_first_step = copy.deepcopy(first_step)
    domain_first_step.pop("acceptance", None)
    domain_text = searchable_text({"goal_plan": goal_plan, "first_step": domain_first_step})
    for term in required_terms:
        if str(term) not in domain_text:
            errors.append(f"first_step.acceptance: required term `{term}` absent")
    forbidden = acceptance.get("forbidden_terms", []) if isinstance(acceptance.get("forbidden_terms"), list) else []
    for term in [*forbidden, *DOMAIN_FORBIDDEN.get(str(task_type), ())]:
        if str(term) and str(term).lower() in domain_text.lower():
            errors.append(f"first_step.acceptance: forbidden term `{term}` leaked into `{task_type}`")
    return errors


def validate_contract(
    contract: dict[str, Any],
    *,
    require_human_approval: bool = True,
    require_evidence: bool = True,
) -> list[str]:
    errors = _identity_errors(contract)
    errors.extend(_semantic_snapshot_errors(contract))

    errors.extend(_domain_action_errors(contract))
    errors.extend(_metric_errors(contract))
    strategy = contract.get("strategy_gate", {})
    if isinstance(strategy, dict):
        for key in ("disconfirming_evidence", "kill_criteria"):
            items = strategy.get(key)
            if not isinstance(items, list) or not items:
                errors.append(f"strategy_gate.{key}: must be non-empty")
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict) or not item.get("threshold") or not _contains_number_or_boolean(item.get("threshold")):
                    errors.append(f"strategy_gate.{key}[{index}].threshold: must be measurable")
    if require_evidence:
        errors.extend(_evidence_errors(contract))
    errors.extend(_artifact_template_errors(contract))

    review = contract.get("human_review")
    if not isinstance(review, dict):
        errors.append("human_review: must be an object")
    elif require_human_approval:
        decision_is_approved = review.get("decision") == "approved"
        if not decision_is_approved:
            errors.append("human_review.decision: must be `approved` before execution")
        else:
            if len(str(review.get("reviewer") or "").strip()) < 2:
                errors.append("human_review.reviewer: is required before execution")
            if len(str(review.get("reason") or "").strip()) < 8:
                errors.append("human_review.reason: must explain the approval")
            acknowledgements = review.get("acknowledgements")
            required_acknowledgements = ("metric_reviewed", "evidence_reviewed", "action_reviewed", "execution_scope_reviewed")
            if not isinstance(acknowledgements, dict) or any(acknowledgements.get(key) is not True for key in required_acknowledgements):
                errors.append("human_review.acknowledgements: all execution acknowledgements must be true")
            semantic_mode = (
                contract.get("semantic_compilation", {}).get("mode")
                if isinstance(contract.get("semantic_compilation"), dict)
                else None
            )
            review_kind = review.get("review_kind")
            if review_kind == "synthetic_test":
                if semantic_mode != "test_fixture":
                    errors.append("human_review.review_kind: synthetic approval is allowed only for test_fixture contracts")
                if review.get("sign_off") != "SYNTHETIC TEST APPROVAL":
                    errors.append("human_review.sign_off: invalid synthetic test sign-off")
            elif review_kind == "human":
                if review.get("sign_off") != "APPROVED BY HUMAN":
                    errors.append("human_review.sign_off: must equal `APPROVED BY HUMAN`")
            else:
                errors.append("human_review.review_kind: must be `human` (or `synthetic_test` for test_fixture only)")
            first_step = contract.get("first_step")
            reviewed_metric_id = first_step.get("metric_id") if isinstance(first_step, dict) else None
            if review.get("metric_id") != reviewed_metric_id:
                errors.append("human_review.metric_id: must match the exact first-step success metric")
            current_payload_hash = approved_payload_sha256(contract)
            if review.get("approved_payload_sha256") != current_payload_hash:
                errors.append("human_review.approved_payload_sha256: current execution payload differs from the recorded review digest")
            if review.get("review_id") != expected_review_id(contract):
                errors.append("human_review.review_id: inconsistent with approval record")
    return errors


def validation_report(
    contract: dict[str, Any],
    *,
    require_human_approval: bool = True,
    require_evidence: bool = True,
) -> dict[str, Any]:
    errors = validate_contract(
        contract,
        require_human_approval=require_human_approval,
        require_evidence=require_evidence,
    )
    return {
        "contract_id": contract.get("contract_id"),
        "status": "PASS" if not errors else "FAIL",
        "human_approval_required": require_human_approval,
        "approval_context": (
            contract.get("human_review", {}).get("review_kind")
            if isinstance(contract.get("human_review"), dict)
            else None
        ),
        "evidence_required": bool(contract.get("tool_evidence_gate", {}).get("research_required")) if isinstance(contract.get("tool_evidence_gate"), dict) else None,
        "error_count": len(errors),
        "errors": errors,
    }


def pending_human_review_template(contract: dict[str, Any]) -> dict[str, Any]:
    strategy = contract.get("strategy_gate", {})
    return {
        "record_type": "pending_human_review_example",
        "decision": "pending",
        "reviewer": "",
        "reason": "",
        "metric_id": contract.get("first_step", {}).get("metric_id"),
        "agent_proposed_metric": copy.deepcopy(strategy.get("success_metrics", [None])[0]) if isinstance(strategy, dict) else None,
        "success_metric_override": None,
        "acknowledgements": {
            "metric_reviewed": False,
            "evidence_reviewed": False,
            "action_reviewed": False,
            "execution_scope_reviewed": False,
        },
        "notice": "这是待人工填写的记录模板，不是已审批证明。",
    }


def attach_evidence(contract: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    review = contract.get("human_review", {})
    if isinstance(review, dict) and review.get("decision") == "approved":
        raise CompilerError("cannot attach evidence after approval; create a new review cycle")
    structural_errors = [*_identity_errors(contract), *_semantic_snapshot_errors(contract)]
    if structural_errors:
        raise CompilerError(
            "cannot attach evidence to a contract that drifted from its saved semantic snapshot:\n- "
            + "\n- ".join(structural_errors)
        )
    updated = copy.deepcopy(contract)
    updated["evidence_bundle"] = copy.deepcopy(evidence)
    return updated


def apply_human_review(
    contract: dict[str, Any],
    review_record: dict[str, Any],
    evidence_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record_type = review_record.get("record_type")
    if record_type == "pending_human_review_example" or review_record.get("decision") != "approved":
        raise CompilerError("review record is pending; exact metric and approval must come from a human")
    if record_type not in {"human_review", "synthetic_test_review"}:
        raise CompilerError("review record_type must be `human_review` or the test-only `synthetic_test_review`")
    semantic_mode = (
        contract.get("semantic_compilation", {}).get("mode")
        if isinstance(contract.get("semantic_compilation"), dict)
        else None
    )
    if record_type == "synthetic_test_review" and semantic_mode != "test_fixture":
        raise CompilerError("synthetic test approval is allowed only for a test_fixture contract")
    current_review = contract.get("human_review")
    if not isinstance(current_review, dict) or current_review.get("decision") != "pending":
        raise CompilerError("apply-review requires a pending contract and a new review cycle")
    structural_errors = [*_identity_errors(contract), *_semantic_snapshot_errors(contract)]
    if structural_errors:
        raise CompilerError(
            "cannot review a contract that drifted from its saved semantic snapshot:\n- "
            + "\n- ".join(structural_errors)
        )
    reviewer = str(review_record.get("reviewer", "")).strip()
    reason = str(review_record.get("reason", "")).strip()
    if len(reviewer) < 2 or len(reason) < 8:
        raise CompilerError("human review needs a named reviewer and a concrete reason")
    acknowledgements = review_record.get("acknowledgements")
    required_acknowledgements = ("metric_reviewed", "evidence_reviewed", "action_reviewed", "execution_scope_reviewed")
    if not isinstance(acknowledgements, dict) or any(acknowledgements.get(key) is not True for key in required_acknowledgements):
        raise CompilerError("human review must explicitly acknowledge metric, evidence, action, and execution scope")
    reviewed_metric_id = contract.get("first_step", {}).get("metric_id") if isinstance(contract.get("first_step"), dict) else None
    if review_record.get("metric_id") != reviewed_metric_id:
        raise CompilerError("human review metric_id must match the exact first-step success metric")

    reviewed = copy.deepcopy(contract)
    if evidence_bundle is not None:
        reviewed["evidence_bundle"] = copy.deepcopy(evidence_bundle)
    metric_override = review_record.get("success_metric_override")
    changed_fields: list[str] = []
    if metric_override is not None:
        if not isinstance(metric_override, dict):
            raise CompilerError("success_metric_override must be an object or null")
        metric_id = review_record.get("metric_id") or reviewed.get("first_step", {}).get("metric_id")
        metrics = reviewed.get("strategy_gate", {}).get("success_metrics", [])
        matches = [index for index, metric in enumerate(metrics) if isinstance(metric, dict) and metric.get("id") == metric_id]
        if len(matches) != 1:
            raise CompilerError("review metric_id must match exactly one success metric")
        index = matches[0]
        reviewed["strategy_gate"]["success_metrics"][index] = copy.deepcopy(metric_override)
        changed_fields.append(f"strategy_gate.success_metrics[{index}]")

    reviewed["human_review"] = {
        "decision": "approved",
        "reviewer": reviewer,
        "reason": reason,
        "review_kind": "synthetic_test" if record_type == "synthetic_test_review" else "human",
        "metric_id": reviewed_metric_id,
        "success_metric_override": copy.deepcopy(metric_override),
        "changed_fields": changed_fields,
        "acknowledgements": copy.deepcopy(acknowledgements),
        "approved_payload_sha256": None,
        "sign_off": "SYNTHETIC TEST APPROVAL" if record_type == "synthetic_test_review" else "APPROVED BY HUMAN",
    }
    preapproval_errors = validate_contract(reviewed, require_human_approval=False, require_evidence=True)
    if preapproval_errors:
        raise CompilerError("cannot approve an invalid/evidence-incomplete payload:\n- " + "\n- ".join(preapproval_errors))

    reviewed["human_review"]["approved_payload_sha256"] = approved_payload_sha256(reviewed)
    reviewed["human_review"]["review_id"] = expected_review_id(reviewed)
    strict_errors = validate_contract(reviewed, require_human_approval=True, require_evidence=True)
    if strict_errors:
        raise CompilerError("reviewed contract failed strict validation:\n- " + "\n- ".join(strict_errors))
    return reviewed


def render_goal(contract: dict[str, Any]) -> str:
    router = contract["smart_router"]
    strategy = contract["strategy_gate"]
    goal = contract["goal_plan"]
    review = contract["human_review"]
    metric = next(
        metric for metric in strategy["success_metrics"] if metric.get("id") == contract["first_step"]["metric_id"]
    )
    disconfirm = strategy["disconfirming_evidence"][0]
    kill = strategy["kill_criteria"][0]
    if review.get("decision") == "approved" and review.get("review_kind") == "synthetic_test":
        review_text = f"仅测试用的合成批准，payload 一致性摘要 {review['approved_payload_sha256'][:12]}；不是真人签字。"
    elif review.get("decision") == "approved":
        review_text = f"已记录 {review['reviewer']} 的批准，payload 一致性摘要 {review['approved_payload_sha256'][:12]}（非签名）。"
    else:
        review_text = "Agent 语义结果已记录，精确指标与执行范围仍待人工批准。"
    lines = [
        f"决策摘要：任务类型={router['task_type']}；成熟度={router['maturity']}；外部信息需求={router['external_information_need']}；风险等级={router['risk_level']}；输出长度={router['output_length']}；是否先提问={'是' if router.get('ask_questions_first') else '否'}",
        f"默认假设：{'；'.join(contract['default_assumptions'])}",
        f"偏好应用：{goal['preference_application']}",
        f"反馈调整：{goal['feedback_adjustment']}；{review_text}",
        f"策略判断：问题重构={strategy['problem_reframe']}；最小验证={strategy['smallest_bet']}；成功指标={metric['statement']}；反证信号={disconfirm['signal']}；终止/暂缓条件={kill['condition']}",
        f"优先级判断：{goal['business_priority']}",
        f"输出长度：{router['output_length']}；{goal['output_length_reason']}",
        f"选择理由：{goal['choice_rationale']}",
        "推荐执行版（中文，可直接复制）",
        f"/goal {goal['outcome']}",
        f"任务包：{goal['task_pack']}；{goal['task_pack_application']}",
        f"领域包：{goal['domain_pack']}；{goal['domain_pack_application']}",
        f"工具栈：{goal['tool_stack']}",
    ]
    stages = goal.get("research_stages")
    if isinstance(stages, dict):
        lines.extend(
            (
                f"阶段 1 - 广域调研：{stages['stage_1']}",
                f"阶段 2 - Deep Research：{stages['stage_2']}",
                f"阶段 3 - 业务应用：{stages['stage_3']}",
                f"输出物：{goal['deliverables']}",
                f"质量门槛：{goal['quality_gate']}",
            )
        )
    lines.extend(
        (
            f"验证方式：{goal['verification']}",
            f"限制：{goal['limits']}",
            f"工作边界：{goal['boundary']}",
            f"推进规则：{goal['progress_rules']}",
            f"停止标准：{goal['stop_criteria']}",
            f"暂停条件：{goal['pause_conditions']}",
        )
    )
    return "\n".join(lines) + "\n"


class ArtifactHTMLInspector(HTMLParser):
    """Collect structural HTML facts without relying on quote-sensitive regexes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.h1_count = 0
        self.primary_cta_count = 0
        self.external_urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "h1":
            self.h1_count += 1
        normalized = {name.lower(): (value or "").strip() for name, value in attrs}
        if normalized.get("data-primary-cta", "").lower() == "true":
            self.primary_cta_count += 1
        for name in ("src", "href"):
            value = normalized.get(name, "")
            if value.lower().startswith(("http://", "https://", "//")):
                self.external_urls.append(value)


def artifact_source_ids(content: str) -> set[str]:
    """Parse explicit `source_ids:` lines from a Markdown validation brief."""
    source_ids: set[str] = set()
    for match in re.finditer(r"(?im)^\s*source_ids\s*:\s*(.*?)\s*$", content):
        raw = match.group(1).strip().strip("[]")
        for token in re.split(r"[,，]", raw):
            source_id = token.strip().strip("`'\"")
            if source_id:
                source_ids.add(source_id)
    return source_ids


def source_reference_details(contract: dict[str, Any], content: str) -> dict[str, Any]:
    referenced = artifact_source_ids(content)
    bundle = contract.get("evidence_bundle", {})
    sources = bundle.get("sources", []) if isinstance(bundle, dict) else []
    claims = bundle.get("claims", []) if isinstance(bundle, dict) else []
    known_ids = {
        str(source.get("id"))
        for source in sources
        if isinstance(source, dict) and str(source.get("id", "")).strip()
    }
    unknown_ids = referenced.difference(known_ids)
    gate = contract.get("tool_evidence_gate")
    requirements = gate.get("evidence_requirements", []) if isinstance(gate, dict) else []
    coverage: list[dict[str, Any]] = []
    for requirement in requirements if isinstance(requirements, list) else []:
        if not isinstance(requirement, dict):
            continue
        claim_type = requirement.get("claim_type")
        minimum = requirement.get("minimum_independent_sources")
        supporting_ids: set[str] = set()
        for claim in claims if isinstance(claims, list) else []:
            if not isinstance(claim, dict) or claim.get("claim_type") != claim_type:
                continue
            claim_source_ids = claim.get("source_ids")
            if isinstance(claim_source_ids, list):
                supporting_ids.update(str(source_id) for source_id in claim_source_ids)
        cited_supporting_ids = referenced.intersection(known_ids, supporting_ids)
        passed = isinstance(minimum, int) and not isinstance(minimum, bool) and len(cited_supporting_ids) >= minimum
        coverage.append(
            {
                "claim_type": claim_type,
                "minimum_independent_sources": minimum,
                "cited_supporting_ids": sorted(cited_supporting_ids),
                "passed": passed,
            }
        )
    return {
        "referenced_ids": sorted(referenced),
        "unknown_ids": sorted(unknown_ids),
        "coverage": coverage,
        "passed": bool(referenced) and not unknown_ids and all(item["passed"] for item in coverage),
    }


def inspect_artifact(contract: dict[str, Any], artifact_path: Path, content: str) -> dict[str, bool]:
    first_step = contract["first_step"]
    validators = first_step["validators"]
    checks: dict[str, bool] = {}
    html_inspector = ArtifactHTMLInspector()
    if any(validator.startswith("html_") or validator == "no_external_urls" for validator in validators):
        html_inspector.feed(content)
        html_inspector.close()
    source_details = source_reference_details(contract, content) if "source_reference" in validators else None
    for validator in validators:
        if validator == "nonempty":
            checks[validator] = bool(content.strip())
        elif validator == "html_single_h1":
            checks[validator] = html_inspector.h1_count == 1
        elif validator == "html_primary_cta":
            checks[validator] = html_inspector.primary_cta_count == 1
        elif validator == "assumption_label":
            checks[validator] = "NOT A MARKET CLAIM" in content and "假设待验证" in content
        elif validator == "no_external_urls":
            checks[validator] = not html_inspector.external_urls
        elif validator == "no_unresolved_template":
            checks[validator] = "{{" not in content and "}}" not in content
        elif validator == "python_syntax":
            try:
                compile(content, str(artifact_path), "exec")
            except SyntaxError:
                checks[validator] = False
            else:
                checks[validator] = True
        elif validator == "regression_marker":
            checks[validator] = "REGRESSION_FIXTURE" in content
        elif validator == "markdown_heading":
            checks[validator] = bool(re.search(r"^#\s+\S", content, flags=re.MULTILINE))
        elif validator == "source_reference":
            checks[validator] = bool(source_details and source_details["passed"])
        else:
            checks[f"unknown_validator:{validator}"] = False
    acceptance = first_step.get("acceptance", {})
    for term in acceptance.get("required_terms", []):
        checks[f"required_term:{term}"] = str(term) in content
    for term in acceptance.get("forbidden_terms", []):
        checks[f"forbidden_term_absent:{term}"] = str(term).lower() not in content.lower()
    return checks


def _artifact_template_errors(contract: dict[str, Any]) -> list[str]:
    first_step = contract.get("first_step")
    if not isinstance(first_step, dict):
        return ["first_step.content_template: cannot validate a non-object first step"]
    content = str(first_step.get("content_template", "")).replace("{{CONTRACT_ID}}", str(contract.get("contract_id", "")))
    artifact = Path(str(first_step.get("primary_artifact", "artifact.txt")))
    try:
        checks = inspect_artifact(contract, artifact, content)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return [f"first_step.content_template: validator setup failed: {exc}"]
    return [f"first_step.content_template: validator `{name}` failed" for name, passed in checks.items() if not passed]


def execute_first_step(contract: dict[str, Any], output: Path | None = None) -> dict[str, Any]:
    errors = validate_contract(contract, require_human_approval=True, require_evidence=True)
    if errors:
        raise CompilerError("contract failed strict validation:\n- " + "\n- ".join(errors))
    first_step = contract["first_step"]
    action = first_step["action"]
    policy = ACTION_POLICIES[action]
    approved_output_dir = expected_output_directory(contract)
    if output is not None and output.expanduser().resolve() != approved_output_dir:
        raise CompilerError(
            "caller-supplied output does not match the approved execution workspace and relative output_directory: "
            f"expected {approved_output_dir}"
        )
    artifact_name = Path(first_step["primary_artifact"]).name
    artifact_path = approved_output_dir / artifact_name
    content = str(first_step["content_template"]).replace("{{CONTRACT_ID}}", str(contract["contract_id"]))
    checks = inspect_artifact(contract, artifact_path, content)
    if not checks or not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise CompilerError(f"approved artifact content failed checks before write: {failed}")
    output_dir = prepare_new_directory(approved_output_dir)
    write_text(artifact_path, content, refuse_existing=True)
    report = {
        "status": "PASS",
        "contract_id": contract["contract_id"],
        "approved_payload_sha256": approved_payload_sha256(contract),
        "approval_context": contract["human_review"].get("review_kind"),
        "execution_workspace": copy.deepcopy(contract["execution_workspace"]),
        "resolved_output_directory": str(approved_output_dir),
        "dispatch": {
            "action": action,
            "handler": policy["dispatch"],
            "artifact_kind": policy["artifact_kind"],
        },
        "artifact": artifact_name,
        "artifact_sha256": sha256_text(content),
        "checks": checks,
        "external_side_effects": [],
    }
    if "source_reference" in first_step["validators"]:
        report["source_reference_details"] = source_reference_details(contract, content)
    write_json(output_dir / "execution-report.json", report, refuse_existing=True)
    return report


def write_validation_log(directory: Path, report: dict[str, Any]) -> Path:
    status = report["status"]
    path = directory / f"validator.{status}.log"
    lines = [f"VALIDATOR {status}"]
    if status == "PASS":
        lines.extend(("- contract identity: PASS", "- domain/action policy: PASS", "- metric/evidence correspondence: PASS", "- evidence precondition: PASS", "- review/payload consistency: PASS"))
    else:
        lines.extend(f"- {error}" for error in report["errors"])
    write_text(path, "\n".join(lines) + "\n")
    return path


def _write_bundle(directory: Path, request: str, semantic: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=False)
    write_text(directory / "request.txt", normalized_request(request) + "\n")
    write_json(directory / "semantic-input.snapshot.json", semantic)
    write_json(directory / "router.json", contract["smart_router"])
    write_json(directory / "strategy-gate.json", contract["strategy_gate"])
    write_json(directory / "goal-contract.json", contract)
    write_text(directory / "goal.md", render_goal(contract))
    write_json(directory / "human-review.pending.json", pending_human_review_template(contract))
    report = validation_report(contract, require_human_approval=True, require_evidence=True)
    report["next_action"] = "complete evidence first when required, then have the human edit and approve human-review.pending.json"
    write_json(directory / "preflight-report.json", report)
    write_validation_log(directory, report)
    return report


def write_compile_bundle(
    output: Path,
    request: str,
    semantic: dict[str, Any],
    workspace_root: Path,
    evidence_bundle: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output_dir = output.expanduser().resolve()
    if output_dir.exists():
        raise CompilerError(f"output already exists; choose a new directory: {output_dir}")
    contract = build_contract(request, semantic, workspace_root=workspace_root, evidence_bundle=evidence_bundle)
    report = _write_bundle(output_dir, request, semantic, contract)
    return contract, report


def render_demo_walkthrough(report: dict[str, Any]) -> str:
    agent_errors = report["agent_preflight"]["errors"]
    evidence_errors = [error for error in agent_errors if "evidence_bundle" in error]
    evidence_text = "<br>".join(html.escape(error) for error in evidence_errors[:2]) or "等待来源证据包"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Goal Compiler · Agent result to human pending</title>
<style>
:root{{--ink:#111827;--paper:#fffdf5;--lime:#d9ff57;--red:#ff5c5c;--amber:#ffbf47;--violet:#7557ff}}*{{box-sizing:border-box}}body{{margin:0;background:#ebe9e1;color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"PingFang SC",sans-serif}}main{{width:min(1180px,calc(100% - 32px));margin:0 auto;padding:40px 0 70px}}header{{display:flex;justify-content:space-between;gap:24px;align-items:flex-start}}h1{{margin:10px 0 12px;font-size:clamp(40px,7vw,78px);line-height:.95;letter-spacing:-.06em}}.k{{color:var(--violet);font-weight:900;letter-spacing:.1em}}.overall{{padding:10px 14px;background:var(--amber);border:2px solid var(--ink);border-radius:999px;font-weight:950}}.flow{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:40px}}article{{min-height:320px;display:flex;flex-direction:column;background:var(--paper);border:2px solid var(--ink);border-radius:20px;padding:24px;box-shadow:6px 6px 0 var(--ink)}}.step{{font-size:14px;font-weight:900}}h2{{margin:34px 0 12px;font-size:26px;line-height:1.08}}p{{color:#475467;line-height:1.55}}.status{{margin-top:auto;padding:9px 12px;width:max-content;border-radius:8px;font-weight:950}}.agent{{background:var(--violet);color:white}}.fail{{background:var(--red);color:white}}.pending{{background:var(--amber)}}.links{{margin-top:32px;padding:24px;background:var(--ink);color:white;border-radius:18px}}.links a{{color:var(--lime);margin-right:18px;font-weight:900}}@media(max-width:900px){{.flow{{grid-template-columns:1fr 1fr}}}}@media(max-width:560px){{.flow{{grid-template-columns:1fr}}header{{display:block}}}}
</style></head><body><main><header><div><div class="k">GOAL COMPILER / AUDIT-CORRECT DEMO</div><h1>Agent 负责语义。<br>证据先到，人再批准。</h1></div><span class="overall">{html.escape(report['status'])}</span></header>
<section class="flow">
<article><span class="step">01 / SEMANTIC INPUT</span><h2>完整 Agent 结果进入 CLI</h2><p>Router、Strategy、Metric、反证、Kill criteria、工具/证据门禁与任务专属验收一次传入。</p><span class="status agent">AGENT_RESULT</span></article>
<article><span class="step">02 / STRICT METRIC</span><h2>“好看”仍然会被拒绝</h2><p>主观 statement、主观 method、空 threshold 都只能写 FAIL.log，不会写 PASS.log。</p><span class="status fail">VALIDATOR FAIL</span></article>
<article><span class="step">03 / EVIDENCE PRECONDITION</span><h2>研究型任务不能跳过来源</h2><p>{evidence_text}</p><span class="status pending">EVIDENCE PENDING</span></article>
<article><span class="step">04 / HUMAN APPROVAL</span><h2>精确指标和执行 payload 留给人</h2><p>人工审批后记录无密钥 SHA-256；审批记录不变时，payload 漂移会被拒绝。它不是数字签名。</p><span class="status pending">HUMAN PENDING</span></article>
</section><nav class="links"><a href="./01-agent-result/semantic-input.snapshot.json">Agent semantic JSON</a><a href="./01-agent-result/validator.FAIL.log">Preflight FAIL</a><a href="./02-subjective-metric/validator.FAIL.log">Metric FAIL</a><a href="./03-human-pending/human-review.pending.json">Human pending</a></nav>
</main></body></html>"""


def run_demo(output: Path, request_file: Path, semantic_file: Path) -> dict[str, Any]:
    output_dir = prepare_new_directory(output)
    request = request_file.read_text(encoding="utf-8").strip()
    semantic = load_semantic_input(semantic_file)
    agent_contract = build_contract(request, semantic, workspace_root=DEFAULT_DEMO_WORKSPACE)
    agent_report = _write_bundle(output_dir / "01-agent-result", request, semantic, agent_contract)

    negative_semantic = copy.deepcopy(semantic)
    metric = negative_semantic["strategy_gate"]["success_metrics"][0]
    metric["statement"] = "看起来足够好看"
    metric["measurement"] = {"method": "主观感受", "target": {}}
    negative_contract = build_contract(request, negative_semantic, workspace_root=DEFAULT_DEMO_WORKSPACE)
    negative_dir = output_dir / "02-subjective-metric"
    negative_report = _write_bundle(negative_dir, request, negative_semantic, negative_contract)

    pending_dir = output_dir / "03-human-pending"
    pending_dir.mkdir()
    pending_review = pending_human_review_template(agent_contract)
    write_json(pending_dir / "human-review.pending.json", pending_review)
    write_text(pending_dir / "NOTICE.md", "# Human approval pending\n\n此记录未经真人批准，不得用于 execute。\n")

    expected = (
        agent_report["status"] == "FAIL"
        and negative_report["status"] == "FAIL"
        and any("vague wording" in error or "subjective method" in error for error in negative_report["errors"])
        and pending_review["decision"] == "pending"
        and not (negative_dir / "validator.PASS.log").exists()
    )
    report = {
        "status": "HUMAN_PENDING" if expected else "FAIL",
        "liveAiClaimed": False,
        "request": request,
        "agent_preflight": agent_report,
        "subjective_metric_gate": negative_report,
        "human_review": {"decision": "pending", "record": "03-human-pending/human-review.pending.json"},
        "execution": {"attempted": False, "reason": "evidence and exact human approval are pending"},
    }
    write_json(output_dir / "demo-report.json", report)
    write_text(output_dir / "walkthrough.html", render_demo_walkthrough(report))
    write_text(
        output_dir / "DEMO_RESULT.md",
        "# Goal Compiler Demo Result\n\n"
        f"- Overall: **{report['status']}**\n"
        f"- Agent semantic contract: **{agent_report['status']}** until evidence/human approval\n"
        f"- Subjective metric fixture: **{negative_report['status']}**\n"
        "- Human review: **PENDING**\n"
        "- Execution attempted: **NO**\n",
    )
    return report


def command_compile(args: argparse.Namespace) -> int:
    request = args.request or Path(args.request_file).read_text(encoding="utf-8")
    semantic = load_semantic_input(Path(args.semantic_input))
    evidence = load_json(Path(args.evidence_input)) if args.evidence_input else None
    contract, report = write_compile_bundle(
        Path(args.output),
        request,
        semantic,
        Path(args.workspace_root),
        evidence_bundle=evidence,
    )
    print(f"Compiled {contract['contract_id']} from semantic input -> {Path(args.output).resolve()}")
    print(f"Preflight: {report['status']} / HUMAN SIGN-OFF PENDING")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    report = validation_report(
        contract,
        require_human_approval=not args.allow_pending_review,
        require_evidence=not args.allow_missing_evidence,
    )
    if args.report:
        write_json(Path(args.report), report, refuse_existing=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


def command_attach_evidence(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    evidence = load_json(Path(args.evidence))
    updated = attach_evidence(contract, evidence)
    write_json(Path(args.output), updated, refuse_existing=True)
    report = validation_report(updated, require_human_approval=False, require_evidence=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


def command_apply_review(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    review = load_json(Path(args.review))
    evidence = load_json(Path(args.evidence)) if args.evidence else None
    reviewed = apply_human_review(contract, review, evidence_bundle=evidence)
    write_json(Path(args.output), reviewed, refuse_existing=True)
    context = reviewed["human_review"]["review_kind"]
    label = "Human approval" if context == "human" else "Synthetic test approval (not human)"
    print(f"{label} recorded payload consistency digest {reviewed['human_review']['approved_payload_sha256']} -> {Path(args.output).resolve()}")
    return 0


def command_execute(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    report = execute_first_step(contract, Path(args.output) if args.output else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    report = run_demo(Path(args.output), Path(args.request_file), Path(args.semantic_input))
    print("Agent semantic result: RECORDED")
    print("Subjective metric: FAIL (expected)")
    print("Evidence: PENDING")
    print("Human approval: PENDING")
    print("Execution: NOT ATTEMPTED")
    print(f"Demo -> {Path(args.output).resolve()}")
    return 0 if report["status"] == "HUMAN_PENDING" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="compile a request plus complete Agent semantic JSON")
    request_group = compile_parser.add_mutually_exclusive_group(required=True)
    request_group.add_argument("--request")
    request_group.add_argument("--request-file")
    compile_parser.add_argument("--semantic-input", required=True, help="complete Agent/Skill semantic result JSON")
    compile_parser.add_argument("--evidence-input", help="optional evidence bundle JSON collected before human review")
    compile_parser.add_argument("--workspace-root", required=True, help="absolute execution workspace bound into the contract")
    compile_parser.add_argument("--output", required=True, help="new output directory")
    compile_parser.set_defaults(handler=command_compile)

    validate_parser = subparsers.add_parser("validate", help="validate identity, domain, evidence, review/payload consistency, and action")
    validate_parser.add_argument("contract")
    validate_parser.add_argument("--report", help="new JSON report path")
    validate_parser.add_argument("--allow-pending-review", action="store_true")
    validate_parser.add_argument("--allow-missing-evidence", action="store_true")
    validate_parser.set_defaults(handler=command_validate)

    evidence_parser = subparsers.add_parser("attach-evidence", help="attach evidence before human approval")
    evidence_parser.add_argument("contract")
    evidence_parser.add_argument("--evidence", required=True)
    evidence_parser.add_argument("--output", required=True, help="new contract JSON path")
    evidence_parser.set_defaults(handler=command_attach_evidence)

    review_parser = subparsers.add_parser("apply-review", help="record an exact review plus an unkeyed payload consistency digest")
    review_parser.add_argument("contract")
    review_parser.add_argument("--review", required=True)
    review_parser.add_argument("--evidence", help="optional evidence bundle to attach before approval")
    review_parser.add_argument("--output", required=True, help="new reviewed contract JSON path")
    review_parser.set_defaults(handler=command_apply_review)

    execute_parser = subparsers.add_parser("execute", help="dispatch one whitelisted first step from an approved contract")
    execute_parser.add_argument("contract")
    execute_parser.add_argument(
        "--output",
        help="optional path assertion; must equal approved workspace root + first_step.output_directory",
    )
    execute_parser.set_defaults(handler=command_execute)

    demo_parser = subparsers.add_parser("demo", help="create an honest agent-result/evidence/human-pending demo")
    demo_parser.add_argument("--output", required=True, help="new output directory")
    demo_parser.add_argument("--request-file", default=str(DEFAULT_DEMO_REQUEST))
    demo_parser.add_argument("--semantic-input", default=str(DEFAULT_DEMO_SEMANTIC))
    demo_parser.set_defaults(handler=command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (CompilerError, OSError, KeyError, StopIteration) as exc:
        print(f"goal-compiler: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
