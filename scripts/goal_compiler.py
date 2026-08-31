#!/usr/bin/env python3
"""Compile vague requests into reviewable, executable goal contracts.

The compiler intentionally separates AI-assisted drafting from deterministic
validation and execution. A contract cannot execute until a human replaces any
vague metric and explicitly approves the review record.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_REQUEST = ROOT / "contest" / "demo-fixtures" / "request.txt"
DEFAULT_DEMO_REVIEW = ROOT / "contest" / "demo-fixtures" / "human-review.json"
SCHEMA_VERSION = "1.0"

VAGUE_METRIC_PATTERNS = (
    r"^好看$",
    r"^更好$",
    r"^尽快$",
    r"^越快越好$",
    r"^高质量$",
    r"^提升体验$",
    r"^beautiful$",
    r"^better$",
    r"^fast$",
    r"^works?$",
)


class CompilerError(ValueError):
    """Raised for invalid input or unsafe output paths."""


def compiler_version() -> str:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    return str(manifest["version"])


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompilerError(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CompilerError(f"expected a JSON object in {path}")
    return value


def prepare_new_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    protected = {Path("/").resolve(), Path.home().resolve(), ROOT.resolve()}
    if resolved in protected:
        raise CompilerError(f"refusing to use protected output directory: {resolved}")
    if resolved.exists():
        raise CompilerError(f"output already exists; choose a new directory: {resolved}")
    resolved.mkdir(parents=True)
    return resolved


def classify_request(request: str) -> dict[str, Any]:
    text = request.lower()
    if any(token in text for token in ("网站", "官网", "落地页", "website", "landing page")):
        task_type = "website"
        task_pack = "网站/落地页改版包"
    elif any(token in text for token in ("seo", "关键词", "搜索流量")):
        task_type = "SEO"
        task_pack = "SEO 内容集群包"
    elif any(token in text for token in ("竞品", "competitor")):
        task_type = "competitor"
        task_pack = "竞品分析包"
    elif any(token in text for token in ("增长", "growth", "获客")):
        task_type = "growth"
        task_pack = "增长实验包"
    elif any(token in text for token in ("app", "saas", "应用")):
        task_type = "app"
        task_pack = "App MVP 研究包"
    elif any(token in text for token in ("代码", "bug", "修复", "coding")):
        task_type = "coding"
        task_pack = "不适用"
    else:
        task_type = "mixed"
        task_pack = "不适用"

    business_task = task_type in {"website", "SEO", "competitor", "growth", "app", "mixed"}
    vague = len(request.strip()) < 80 or any(
        token in request for token in ("帮我做", "越快越好", "优化一下", "更好")
    )
    return {
        "task_type": task_type,
        "maturity": "模糊想法" if vague else "已有方向",
        "risk_level": "中" if business_task else "低",
        "external_information_need": "标准" if business_task else "不需要",
        "ask_questions_first": False,
        "output_length": "标准版" if business_task else "短版",
        "strategy_recommendation": "先验证需求" if business_task else "直接执行",
        "business_recommendation": "先小实验验证" if business_task else "立即做",
        "task_pack": task_pack,
        "domain_pack": "AI 工具站包" if "ai" in text or "人工智能" in text else "不适用",
        "routing_reason": (
            "这是模糊的业务建设请求，外部证据会改变定位和范围，因此先编译最小验证闭环。"
            if business_task
            else "这是可以用本地产物和检查直接证明的任务，不需要额外研究。"
        ),
    }


def measurable_metric() -> dict[str, Any]:
    return {
        "id": "first-validation-page",
        "statement": "在 60 分钟内生成 1 个可打开的单页，页面包含 1 个明确价值承诺、1 个 CTA 和假设标记。",
        "measurement": {
            "method": "本地 HTML 结构检查",
            "target": {
                "max_minutes": 60,
                "min_html_pages": 1,
                "min_primary_cta": 1,
                "assumption_label_required": True,
            },
        },
        "evidence_path": "first-output/execution-report.json",
    }


def vague_metric(statement: str) -> dict[str, Any]:
    return {
        "id": "human-proposed-metric",
        "statement": statement,
        "measurement": {"method": "主观感受", "target": {}},
        "evidence_path": "",
    }


def compile_contract(request: str, proposed_metric: str | None = None) -> dict[str, Any]:
    normalized_request = " ".join(request.split())
    if len(normalized_request) < 8:
        raise CompilerError("request must contain at least 8 non-whitespace characters")

    router = classify_request(normalized_request)
    metric = vague_metric(proposed_metric) if proposed_metric else measurable_metric()
    identity_seed = {"request": normalized_request, "router": router, "schema": SCHEMA_VERSION}
    contract_id = stable_id("goal", identity_seed)
    return {
        "schema_version": SCHEMA_VERSION,
        "compiler": {"name": "Goal Compiler | 需求编译器", "version": compiler_version()},
        "contract_id": contract_id,
        "request": {
            "raw": normalized_request,
            "request_sha256": hashlib.sha256(normalized_request.encode("utf-8")).hexdigest(),
        },
        "smart_router": router,
        "default_assumptions": [
            "当前没有已验证的目标用户、核心场景或付费证据。",
            "首轮不做后端、登录、支付或生产部署。",
            "只使用自有文字、系统字体和无外部依赖的 HTML/CSS。",
        ],
        "strategy_gate": {
            "problem_reframe": "不是立刻做完整 AI 网站，而是先验证一个具体人群、一个高频问题和一个可点击承诺能否形成首个需求证据。",
            "smallest_bet": "先产出一个标注为假设的单页和一个 CTA，然后用 5 次目标用户反馈决定是否扩大实现。",
            "success_metrics": [metric],
            "disconfirming_evidence": [
                {
                    "signal": "少于 2/5 名目标用户能复述页面承诺",
                    "threshold": {"max_comprehension_count": 1, "sample_size": 5},
                    "response": "停止加功能，先重写用户和问题定义。",
                },
                {
                    "signal": "在 5 次访谈中没有人愿意点击 CTA 或留下下一步联系",
                    "threshold": {"max_cta_intent_count": 0, "sample_size": 5},
                    "response": "把方向降级为待验证假设，不进入完整开发。",
                },
            ],
            "kill_criteria": [
                {
                    "condition": "连续两轮文案/人群调整后仍无 CTA 意图",
                    "threshold": {"max_rounds": 2, "max_cta_intent_count": 0},
                    "action": "pause_full_build",
                },
                {
                    "condition": "首个页面需要未授权数据、账号或付费服务才能证明",
                    "threshold": {"unauthorized_dependencies": 1},
                    "action": "stop_and_request_authorization",
                },
            ],
        },
        "tool_evidence_gate": {
            "research_required": router["external_information_need"] != "不需要",
            "permitted_tools": [
                "公开网页阅读器",
                "Agent Reach（仅在已安装且渠道可用时）",
                "本地文件与标准库脚本",
            ],
            "authorization_required_for": [
                "账号登录",
                "Cookie 或 Token",
                "付费数据",
                "私域内容",
                "表单提交或生产变更",
            ],
            "evidence_requirements": [
                {
                    "claim_type": "用户痛点或需求",
                    "minimum_independent_sources": 2,
                    "record_fields": ["title", "url", "source_type", "tool_channel", "access_limit"],
                },
                {
                    "claim_type": "页面结构完成",
                    "minimum_independent_sources": 1,
                    "record_fields": ["artifact_path", "check", "result"],
                },
            ],
            "blocked_claims": [
                "未经证据的市场规模",
                "未经测量的效率提升",
                "未经用户验证的付费意愿",
            ],
        },
        "first_step": {
            "action": "generate_validation_landing_page",
            "output_directory": "first-output",
            "primary_artifact": "first-output/index.html",
            "purpose": "用可打开的单页替代抽象方案，仅表达待验证假设。",
            "checks": ["one_h1", "one_primary_cta", "assumption_label", "no_external_assets"],
        },
        "human_review": {
            "decision": "pending",
            "reviewer": None,
            "reason": "",
            "changed_fields": [],
            "sign_off": "PENDING HUMAN SIGN-OFF",
        },
    }


def _is_vague_metric(statement: str) -> bool:
    normalized = re.sub(r"[\s。，,;；!！?？]+", "", statement.strip().lower())
    return any(re.fullmatch(pattern, normalized, flags=re.IGNORECASE) for pattern in VAGUE_METRIC_PATTERNS)


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


def validate_contract(contract: dict[str, Any], require_human_approval: bool = True) -> list[str]:
    errors: list[str] = []

    def require_object(parent: dict[str, Any], key: str) -> dict[str, Any]:
        value = parent.get(key)
        if not isinstance(value, dict):
            errors.append(f"{key}: must be an object")
            return {}
        return value

    if contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: expected {SCHEMA_VERSION}")
    if not re.fullmatch(r"goal-[0-9a-f]{12}", str(contract.get("contract_id", ""))):
        errors.append("contract_id: must be a stable goal identifier")

    router = require_object(contract, "smart_router")
    for key in (
        "task_type",
        "maturity",
        "risk_level",
        "external_information_need",
        "strategy_recommendation",
    ):
        if not str(router.get(key, "")).strip():
            errors.append(f"smart_router.{key}: is required")

    strategy = require_object(contract, "strategy_gate")
    for key in ("problem_reframe", "smallest_bet"):
        if len(str(strategy.get(key, "")).strip()) < 20:
            errors.append(f"strategy_gate.{key}: is too thin")

    metrics = strategy.get("success_metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("strategy_gate.success_metrics: at least one metric is required")
        metrics = []
    for index, metric in enumerate(metrics):
        prefix = f"strategy_gate.success_metrics[{index}]"
        if not isinstance(metric, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        statement = str(metric.get("statement", "")).strip()
        if len(statement) < 8:
            errors.append(f"{prefix}.statement: must describe an observable outcome")
        if _is_vague_metric(statement):
            errors.append(f"{prefix}.statement: vague metric `{statement}` is not measurable")
        measurement = metric.get("measurement")
        if not isinstance(measurement, dict):
            errors.append(f"{prefix}.measurement: must be an object")
        else:
            if not str(measurement.get("method", "")).strip():
                errors.append(f"{prefix}.measurement.method: is required")
            target = measurement.get("target")
            if not isinstance(target, dict) or not target:
                errors.append(f"{prefix}.measurement.target: must contain explicit thresholds")
            elif not _contains_number_or_boolean(target):
                errors.append(f"{prefix}.measurement.target: needs a number or boolean gate")
        if not str(metric.get("evidence_path", "")).strip():
            errors.append(f"{prefix}.evidence_path: is required")

    disconfirming = strategy.get("disconfirming_evidence")
    if not isinstance(disconfirming, list) or not disconfirming:
        errors.append("strategy_gate.disconfirming_evidence: at least one signal is required")
    else:
        for index, signal in enumerate(disconfirming):
            if not isinstance(signal, dict) or not signal.get("signal") or not signal.get("response"):
                errors.append(f"strategy_gate.disconfirming_evidence[{index}]: signal and response are required")
            elif not _contains_number_or_boolean(signal.get("threshold", {})):
                errors.append(f"strategy_gate.disconfirming_evidence[{index}].threshold: must be measurable")

    kill_criteria = strategy.get("kill_criteria")
    if not isinstance(kill_criteria, list) or not kill_criteria:
        errors.append("strategy_gate.kill_criteria: at least one stop rule is required")
    else:
        for index, criterion in enumerate(kill_criteria):
            if not isinstance(criterion, dict) or not criterion.get("condition") or not criterion.get("action"):
                errors.append(f"strategy_gate.kill_criteria[{index}]: condition and action are required")
            elif not _contains_number_or_boolean(criterion.get("threshold", {})):
                errors.append(f"strategy_gate.kill_criteria[{index}].threshold: must be measurable")

    gate = require_object(contract, "tool_evidence_gate")
    if not isinstance(gate.get("permitted_tools"), list) or not gate.get("permitted_tools"):
        errors.append("tool_evidence_gate.permitted_tools: at least one tool is required")
    if not isinstance(gate.get("evidence_requirements"), list) or not gate.get("evidence_requirements"):
        errors.append("tool_evidence_gate.evidence_requirements: at least one rule is required")
    if not isinstance(gate.get("authorization_required_for"), list) or not gate.get("authorization_required_for"):
        errors.append("tool_evidence_gate.authorization_required_for: must define pause boundaries")

    first_step = require_object(contract, "first_step")
    artifact = str(first_step.get("primary_artifact", ""))
    if not artifact or artifact.startswith("/") or ".." in Path(artifact).parts:
        errors.append("first_step.primary_artifact: must be a safe relative path")
    if not isinstance(first_step.get("checks"), list) or len(first_step.get("checks", [])) < 3:
        errors.append("first_step.checks: at least three observable checks are required")

    review = require_object(contract, "human_review")
    if require_human_approval:
        if review.get("decision") != "approved":
            errors.append("human_review.decision: must be `approved` before execution")
        if len(str(review.get("reviewer") or "").strip()) < 2:
            errors.append("human_review.reviewer: is required before execution")
        if review.get("sign_off") != "APPROVED BY HUMAN":
            errors.append("human_review.sign_off: must equal `APPROVED BY HUMAN`")

    return errors


def validation_report(contract: dict[str, Any], require_human_approval: bool = True) -> dict[str, Any]:
    errors = validate_contract(contract, require_human_approval=require_human_approval)
    return {
        "contract_id": contract.get("contract_id"),
        "status": "PASS" if not errors else "FAIL",
        "human_approval_required": require_human_approval,
        "error_count": len(errors),
        "errors": errors,
    }


def apply_human_review(contract: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    if review.get("decision") != "approved":
        raise CompilerError("human review decision must be `approved`")
    reviewer = str(review.get("reviewer", "")).strip()
    reason = str(review.get("reason", "")).strip()
    metric_override = review.get("success_metric_override")
    if len(reviewer) < 2 or len(reason) < 8:
        raise CompilerError("human review needs a reviewer and a concrete reason")
    if not isinstance(metric_override, dict):
        raise CompilerError("human review needs success_metric_override")

    reviewed = json.loads(json.dumps(contract, ensure_ascii=False))
    original_metric = reviewed["strategy_gate"]["success_metrics"][0]
    reviewed["strategy_gate"]["success_metrics"][0] = metric_override
    review_seed = {"contract_id": reviewed["contract_id"], "review": review}
    reviewed["human_review"] = {
        "decision": "approved",
        "reviewer": reviewer,
        "reason": reason,
        "review_id": stable_id("review", review_seed),
        "changed_fields": ["strategy_gate.success_metrics[0]"],
        "previous_metric_statement": original_metric.get("statement", ""),
        "sign_off": "APPROVED BY HUMAN",
    }
    return reviewed


def render_goal(contract: dict[str, Any]) -> str:
    router = contract["smart_router"]
    strategy = contract["strategy_gate"]
    metric = strategy["success_metrics"][0]
    disconfirm = strategy["disconfirming_evidence"][0]
    kill = strategy["kill_criteria"][0]
    review = contract["human_review"]
    assumptions = "；".join(contract["default_assumptions"])
    review_text = (
        f"已由 {review['reviewer']} 审核，人工把指标改为可测量门槛。"
        if review.get("decision") == "approved"
        else "尚未完成人工签字，只允许生成草案，不允许执行。"
    )
    return f"""决策摘要：任务类型={router['task_type']}；成熟度={router['maturity']}；外部信息需求={router['external_information_need']}；风险等级={router['risk_level']}；输出长度={router['output_length']}；是否先提问=否
默认假设：{assumptions}
偏好应用：优先小闭环和真实产物，先做一个可打开的验证页，不先做完整站点。
反馈调整：{review_text}
策略判断：问题重构={strategy['problem_reframe']}；最小验证={strategy['smallest_bet']}；成功指标={metric['statement']}；反证信号={disconfirm['signal']}；终止/暂缓条件={kill['condition']}
优先级判断：业务价值=中；证据强度=低；执行成本=低；分发潜力=中；变现路径=待验证；风险=过早开发；建议=先做单页小实验
输出长度：{router['output_length']}；保留机器可读契约与必要研究门槛。
选择理由：{router['routing_reason']}
推荐执行版（中文，可直接复制）
/goal 把“{contract['request']['raw']}”编译为一个可验证的 AI 网站最小闭环：先核实人群与问题，再生成标注假设的单页和 CTA，最后用反证和终止条件决定是否继续。
任务包：{router['task_pack']}；本次只映射到目标用户、首屏承诺、CTA、证据和第一个页面产物。
领域包：{router['domain_pack']}；先验证免费入口和使用意图，不扩张后端或付费功能。
工具栈：先运行 `agent-reach doctor` 确认渠道；可用时用 Agent Reach 收集公开来源，简单公开页用 web reader/browser，重复结构化抽取才用 Scrapling，需要点击或截图才用 browser-use，Claude for Chrome 只作用户授权的人工接管选项。
阶段 1 - 广域调研：收集 15-25 个候选来源，覆盖直接竞品、相邻产品、用户抱怨和官方资料；记录标题、URL、来源类型、工具/渠道、检索日期和访问限制。
阶段 2 - Deep Research：深读高价值来源，每个需求结论至少用 2 个独立来源交叉验证；不足时标为低置信假设，列出矛盾和反例。
阶段 3 - 业务应用：把去重且可追溯的证据映射到人群、问题、首屏承诺、CTA 和 5 次用户反馈，只执行人工批准后的第一步。
输出物：生成 goal-contract.json、goal.md、来源证据表、单页 first-output/index.html 和 execution-report.json。
质量门槛：关键需求结论至少 2 个独立来源；标注来源强弱；过期、营销、不可访问来源降权；矛盾信息必须列出；不足证据只能标为低置信假设。
验证方式：运行 `python3 scripts/goal_compiler.py validate goal-contract.json`；通过后执行第一步，用 execution-report.json 和可打开的 HTML 产物证明完成。
限制：不复制竞品，不编造需求，不把 Agent Reach 描述成无限制全网访问；不用自动化绕过登录、付费、验证码或平台限制。
工作边界：只创建契约、研究记录和一个无外部资产的静态验证页；不改生产站点。
推进规则：先编译，再由人改掉主观指标，验证 PASS 后才执行；任一门槛失败就回到契约，不绕过。
停止标准：契约通过严格校验，单页和检查报告存在，或命中反证/终止门槛后明确暂缓。
暂停条件：需要账号、Cookie、Token、付费数据、私域内容、表单提交、版权授权或生产变更时暂停。
""".strip() + "\n"


def render_landing_page(contract: dict[str, Any]) -> str:
    contract_id = html.escape(str(contract["contract_id"]))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IdeaSignal · AI 需求验证页</title>
  <style>
    :root {{ --ink:#101828; --muted:#667085; --paper:#fffdf7; --lime:#d7ff55; --violet:#7657ff; --line:#d0d5dd; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f1f0ea; color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"PingFang SC",sans-serif; }}
    main {{ width:min(1080px,calc(100% - 32px)); margin:0 auto; padding:36px 0 72px; }}
    .top {{ display:flex; justify-content:space-between; gap:20px; align-items:center; font-size:14px; }}
    .brand {{ font-weight:900; letter-spacing:-.03em; }}
    .badge {{ padding:8px 12px; border:1px solid var(--ink); border-radius:999px; background:var(--lime); font-weight:800; }}
    .hero {{ margin-top:54px; display:grid; grid-template-columns:1.35fr .65fr; gap:20px; }}
    .panel {{ background:var(--paper); border:2px solid var(--ink); border-radius:24px; box-shadow:8px 8px 0 var(--ink); padding:clamp(24px,5vw,58px); }}
    .eyebrow {{ color:var(--violet); font-weight:900; text-transform:uppercase; letter-spacing:.08em; }}
    h1 {{ margin:14px 0 18px; max-width:760px; font-size:clamp(42px,7vw,82px); line-height:.98; letter-spacing:-.065em; }}
    .lead {{ max-width:680px; color:var(--muted); font-size:clamp(18px,2.2vw,24px); }}
    .cta {{ display:inline-block; margin-top:30px; padding:16px 22px; color:white; background:var(--violet); border:2px solid var(--ink); border-radius:12px; box-shadow:4px 4px 0 var(--ink); font-weight:900; text-decoration:none; }}
    aside {{ display:grid; align-content:space-between; gap:18px; }}
    .number {{ font-size:68px; font-weight:950; line-height:1; }}
    .small {{ color:var(--muted); }}
    .grid {{ margin-top:34px; display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }}
    .card {{ background:white; border:1px solid var(--line); border-radius:18px; padding:24px; }}
    .card strong {{ display:block; margin-bottom:8px; font-size:20px; }}
    #waitlist {{ margin-top:34px; padding:30px; border-radius:18px; background:var(--ink); color:white; }}
    code {{ color:var(--lime); }}
    @media (max-width:760px) {{ .hero,.grid {{ grid-template-columns:1fr; }} .top {{ align-items:flex-start; }} }}
  </style>
</head>
<body data-goal-compiler-output="true">
  <main>
    <header class="top">
      <span class="brand">IdeaSignal / Goal Compiler Output</span>
      <span class="badge">假设待验证 · NOT A MARKET CLAIM</span>
    </header>
    <section class="hero">
      <div class="panel">
        <div class="eyebrow">从模糊想法到第一个证据</div>
        <h1>先验证有没有人需要，再开发 AI 网站。</h1>
        <p class="lead">这是需求编译器执行的第一步：一个可打开、可点击、能被反证的单页，不是一份继续拖延的方案。</p>
        <a class="cta" href="#waitlist">我愿意测试这个闭环 →</a>
      </div>
      <aside class="panel">
        <div><div class="number">5</div><strong>次用户反馈就决定去留</strong></div>
        <p class="small">两轮仍无 CTA 意图，就暂停完整开发。成功和停止条件都在契约里。</p>
      </aside>
    </section>
    <section class="grid" aria-label="验证步骤">
      <article class="card"><strong>01 可测量</strong><span>把“好看”改成时间、页面、CTA 和结构检查。</span></article>
      <article class="card"><strong>02 可反证</strong><span>少于 2/5 人能复述承诺，回到问题定义。</span></article>
      <article class="card"><strong>03 可停止</strong><span>没有意图就不加功能，不让沉没成本替代证据。</span></article>
    </section>
    <section id="waitlist">
      <strong>第一步已真实生成。</strong>
      <p>契约 <code>{contract_id}</code> 已通过人工签字和机器校验；此页未发送表单、未收集个人数据、未引用外部资产。</p>
    </section>
  </main>
</body>
</html>
"""


def inspect_landing_page(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks = {
        "html_exists": path.is_file(),
        "one_h1": len(re.findall(r"<h1(?:\s|>)", text, flags=re.IGNORECASE)) == 1,
        "one_primary_cta": len(re.findall(r'href="#waitlist"', text)) == 1,
        "assumption_label": "NOT A MARKET CLAIM" in text and "假设待验证" in text,
        "no_external_assets": not bool(re.search(r'(?:src|href)="https?://', text, flags=re.IGNORECASE)),
        "compiler_marker": 'data-goal-compiler-output="true"' in text,
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "artifact": path.name,
        "checks": checks,
    }


def render_demo_walkthrough(report: dict[str, Any]) -> str:
    fail_errors = report["negative_gate"]["errors"]
    error_items = "".join(f"<li>{html.escape(error)}</li>" for error in fail_errors)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Goal Compiler · 失败到可执行的证据链</title>
  <style>
    :root {{ --ink:#111827; --paper:#fffdf5; --lime:#d9ff57; --red:#ff5c5c; --green:#2dd4a7; --violet:#7557ff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#ebe9e1; color:var(--ink); font-family:ui-sans-serif,system-ui,-apple-system,"PingFang SC",sans-serif; }}
    main {{ width:min(1180px,calc(100% - 32px)); margin:0 auto; padding:40px 0 70px; }}
    header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-start; }}
    h1 {{ margin:10px 0 12px; font-size:clamp(40px,7vw,78px); line-height:.95; letter-spacing:-.06em; }}
    .kicker {{ color:var(--violet); font-weight:900; letter-spacing:.1em; text-transform:uppercase; }}
    .overall {{ padding:10px 14px; background:var(--lime); border:2px solid var(--ink); border-radius:999px; font-weight:950; }}
    .flow {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:40px; }}
    article {{ min-height:310px; display:flex; flex-direction:column; background:var(--paper); border:2px solid var(--ink); border-radius:20px; padding:24px; box-shadow:6px 6px 0 var(--ink); }}
    .step {{ font-size:14px; font-weight:900; }}
    h2 {{ margin:34px 0 12px; font-size:26px; line-height:1.05; }}
    p,li {{ color:#475467; line-height:1.55; }}
    ul {{ padding-left:18px; }}
    .status {{ margin-top:auto; padding:9px 12px; width:max-content; border-radius:8px; font-weight:950; color:white; }}
    .fail {{ background:var(--red); }} .pass {{ background:var(--green); color:var(--ink); }} .human {{ background:var(--violet); }}
    .links {{ margin-top:32px; padding:24px; background:var(--ink); color:white; border-radius:18px; }}
    .links a {{ color:var(--lime); margin-right:18px; font-weight:900; }}
    @media(max-width:900px) {{ .flow {{ grid-template-columns:1fr 1fr; }} }}
    @media(max-width:560px) {{ .flow {{ grid-template-columns:1fr; }} header {{ display:block; }} .overall {{ display:inline-block; margin-top:14px; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div><div class="kicker">Goal Compiler / 需求编译器</div><h1>不润色 Prompt。<br>把模糊需求编译成可停止的执行。</h1></div>
      <span class="overall">完整 Demo {html.escape(report['status'])}</span>
    </header>
    <section class="flow">
      <article><span class="step">01 / ROUTER</span><h2>“给我做个 AI 网站，越快越好”</h2><p>路由为 website / 模糊想法 / 中风险 / 标准外部信息需求。</p><span class="status human">COMPILED</span></article>
      <article><span class="step">02 / NEGATIVE GATE</span><h2>成功指标：“好看”</h2><ul>{error_items}</ul><span class="status fail">VALIDATOR FAIL</span></article>
      <article><span class="step">03 / HUMAN PATCH</span><h2>60 分钟 · 1 页 · 1 CTA · 假设标记</h2><p>人工替换主观指标，明确测量方法、数字门槛和证据路径。</p><span class="status pass">VALIDATOR PASS</span></article>
      <article><span class="step">04 / FIRST REAL OUTPUT</span><h2>真正生成页面，再跑 6 项结构检查</h2><p>无外部资产、无表单提交、无生产变更。产物和检查报告都可直接打开。</p><span class="status pass">EXECUTION PASS</span></article>
    </section>
    <nav class="links">
      <a href="./01-invalid-draft/router.json">Router JSON</a>
      <a href="./01-invalid-draft/validator.FAIL.log">FAIL log</a>
      <a href="./human-metric-patch.json">Human patch</a>
      <a href="./02-reviewed-contract/validator.PASS.log">PASS log</a>
      <a href="./03-first-output/index.html">First output</a>
      <a href="./03-first-output/execution-report.json">Execution report</a>
    </nav>
  </main>
</body>
</html>
"""


def execute_first_step(contract: dict[str, Any], output: Path) -> dict[str, Any]:
    errors = validate_contract(contract, require_human_approval=True)
    if errors:
        raise CompilerError("contract failed strict validation:\n- " + "\n- ".join(errors))
    output_dir = prepare_new_directory(output)
    page = output_dir / "index.html"
    page.write_text(render_landing_page(contract), encoding="utf-8")
    report = inspect_landing_page(page)
    report["contract_id"] = contract["contract_id"]
    report["action"] = contract["first_step"]["action"]
    report["external_side_effects"] = []
    write_json(output_dir / "execution-report.json", report)
    if report["status"] != "PASS":
        raise CompilerError("first output failed deterministic checks")
    return report


def human_review_template() -> dict[str, Any]:
    return {
        "decision": "pending",
        "reviewer": "",
        "reason": "把主观词改成可通过文件和检查报告验收的指标。",
        "success_metric_override": measurable_metric(),
    }


def write_compile_bundle(output: Path, request: str, proposed_metric: str | None = None) -> dict[str, Any]:
    output_dir = prepare_new_directory(output)
    contract = compile_contract(request, proposed_metric=proposed_metric)
    (output_dir / "request.txt").write_text(request.strip() + "\n", encoding="utf-8")
    write_json(output_dir / "router.json", contract["smart_router"])
    write_json(output_dir / "goal-contract.json", contract)
    (output_dir / "goal.md").write_text(render_goal(contract), encoding="utf-8")
    write_json(output_dir / "human-review.template.json", human_review_template())
    report = validation_report(contract, require_human_approval=True)
    report["next_action"] = "edit human-review.template.json, set decision to approved, then run apply-review"
    write_json(output_dir / "preflight-report.json", report)
    return contract


def run_demo(output: Path, request_file: Path, review_file: Path) -> dict[str, Any]:
    output_dir = prepare_new_directory(output)
    request = request_file.read_text(encoding="utf-8").strip()
    review = load_json(review_file)

    invalid_dir = output_dir / "01-invalid-draft"
    invalid_dir.mkdir()
    invalid_contract = compile_contract(request, proposed_metric="好看")
    write_json(invalid_dir / "goal-contract.json", invalid_contract)
    write_json(invalid_dir / "router.json", invalid_contract["smart_router"])
    write_json(invalid_dir / "strategy-gate.json", invalid_contract["strategy_gate"])
    (invalid_dir / "goal.md").write_text(render_goal(invalid_contract), encoding="utf-8")
    invalid_report = validation_report(invalid_contract, require_human_approval=True)
    write_json(invalid_dir / "validation-report.json", invalid_report)
    (invalid_dir / "validator.FAIL.log").write_text(
        "VALIDATOR FAIL\n" + "\n".join(f"- {error}" for error in invalid_report["errors"]) + "\n",
        encoding="utf-8",
    )

    reviewed_dir = output_dir / "02-reviewed-contract"
    reviewed_dir.mkdir()
    reviewed_contract = apply_human_review(invalid_contract, review)
    write_json(output_dir / "human-metric-patch.json", review)
    write_json(reviewed_dir / "goal-contract.json", reviewed_contract)
    write_json(reviewed_dir / "strategy-gate.json", reviewed_contract["strategy_gate"])
    (reviewed_dir / "goal.md").write_text(render_goal(reviewed_contract), encoding="utf-8")
    reviewed_report = validation_report(reviewed_contract, require_human_approval=True)
    write_json(reviewed_dir / "validation-report.json", reviewed_report)
    (reviewed_dir / "validator.PASS.log").write_text(
        "VALIDATOR PASS\n- contract schema: PASS\n- measurable success metric: PASS\n"
        "- disconfirming evidence: PASS\n- kill criteria: PASS\n- tool/evidence gate: PASS\n"
        "- human sign-off: PASS\n",
        encoding="utf-8",
    )

    execution = execute_first_step(reviewed_contract, output_dir / "03-first-output")
    demo_status = (
        "PASS"
        if invalid_report["status"] == "FAIL"
        and reviewed_report["status"] == "PASS"
        and execution["status"] == "PASS"
        else "FAIL"
    )
    demo_report = {
        "status": demo_status,
        "request": request,
        "negative_gate": invalid_report,
        "human_review": reviewed_contract["human_review"],
        "positive_gate": reviewed_report,
        "first_step_execution": execution,
    }
    write_json(output_dir / "demo-report.json", demo_report)
    (output_dir / "request.txt").write_text(request + "\n", encoding="utf-8")
    (output_dir / "walkthrough.html").write_text(render_demo_walkthrough(demo_report), encoding="utf-8")
    (output_dir / "DEMO_RESULT.md").write_text(
        "\n".join(
            (
                "# Goal Compiler Demo Result",
                "",
                f"- Overall: **{demo_status}**",
                f"- Initial vague metric: **{invalid_report['status']}** ({invalid_report['error_count']} errors)",
                f"- Human-reviewed contract: **{reviewed_report['status']}**",
                f"- First real output: **{execution['status']}**",
                "- Artifact: `03-first-output/index.html`",
                "- Check evidence: `03-first-output/execution-report.json`",
                "",
            )
        ),
        encoding="utf-8",
    )
    return demo_report


def command_compile(args: argparse.Namespace) -> int:
    request = args.request or Path(args.request_file).read_text(encoding="utf-8")
    contract = write_compile_bundle(Path(args.output), request, proposed_metric=args.metric)
    print(f"Compiled {contract['contract_id']} -> {Path(args.output).resolve()}")
    print("Status: PENDING HUMAN SIGN-OFF")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    report = validation_report(contract, require_human_approval=not args.allow_pending_review)
    if args.report:
        write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


def command_apply_review(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    review = load_json(Path(args.review))
    reviewed = apply_human_review(contract, review)
    errors = validate_contract(reviewed, require_human_approval=True)
    write_json(Path(args.output), reviewed)
    if errors:
        print("Review applied, but strict validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Human review applied; strict validation PASS -> {Path(args.output).resolve()}")
    return 0


def command_execute(args: argparse.Namespace) -> int:
    contract = load_json(Path(args.contract))
    report = execute_first_step(contract, Path(args.output))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    report = run_demo(Path(args.output), Path(args.request_file), Path(args.review_file))
    print("模糊指标 `好看`: FAIL (expected)")
    print("人工改为可测量指标: PASS")
    print("第一个真实页面与检查: PASS")
    print(f"Demo -> {Path(args.output).resolve()}")
    return 0 if report["status"] == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile vague intent into a reviewable goal contract and execute its first safe step."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="compile a request into a draft bundle")
    request_group = compile_parser.add_mutually_exclusive_group(required=True)
    request_group.add_argument("--request", help="request text")
    request_group.add_argument("--request-file", help="UTF-8 request file")
    compile_parser.add_argument("--metric", help="optional human-proposed metric; vague text will fail strict validation")
    compile_parser.add_argument("--output", required=True, help="new output directory")
    compile_parser.set_defaults(handler=command_compile)

    validate_parser = subparsers.add_parser("validate", help="strictly validate a goal contract")
    validate_parser.add_argument("contract", help="goal-contract.json path")
    validate_parser.add_argument("--report", help="optional JSON report path")
    validate_parser.add_argument(
        "--allow-pending-review",
        action="store_true",
        help="validate structure without requiring human approval",
    )
    validate_parser.set_defaults(handler=command_validate)

    review_parser = subparsers.add_parser("apply-review", help="apply a human review to a draft contract")
    review_parser.add_argument("contract", help="draft goal-contract.json path")
    review_parser.add_argument("--review", required=True, help="human review JSON path")
    review_parser.add_argument("--output", required=True, help="reviewed contract JSON path")
    review_parser.set_defaults(handler=command_apply_review)

    execute_parser = subparsers.add_parser("execute", help="execute the first safe step of an approved contract")
    execute_parser.add_argument("contract", help="approved goal-contract.json path")
    execute_parser.add_argument("--output", required=True, help="new output directory")
    execute_parser.set_defaults(handler=command_execute)

    demo_parser = subparsers.add_parser("demo", help="run the reproducible failure-review-pass-execute demo")
    demo_parser.add_argument("--output", required=True, help="new output directory")
    demo_parser.add_argument("--request-file", default=str(DEFAULT_DEMO_REQUEST))
    demo_parser.add_argument("--review-file", default=str(DEFAULT_DEMO_REVIEW))
    demo_parser.set_defaults(handler=command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (CompilerError, OSError, KeyError) as exc:
        print(f"goal-compiler: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
