#!/usr/bin/env python3
"""Local-only helper for the agent-network internal workbench.

This script intentionally avoids destructive operations. It writes only under
the configured allowed Obsidian roots, mainly 90_Agent.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PATHS = json.loads((ROOT / "config" / "paths.json").read_text(encoding="utf-8"))
ROLES = json.loads((ROOT / "config" / "roles.json").read_text(encoding="utf-8"))["roles"]
PIPELINES = json.loads((ROOT / "config" / "pipelines.json").read_text(encoding="utf-8"))["pipelines"]
ROLE_BY_ID = {role["id"]: role for role in ROLES}
ANET_RUNTIME = Path(
    os.environ.get("ANET_RUNTIME", str(Path.home() / "Workspace" / "agent-network-runtime"))
).expanduser()

def expand_config_path(value: str, variables: dict[str, str] = None) -> Path:
    text = value
    for key, replacement in (variables or {}).items():
        text = text.replace(f"${{{key}}}", replacement)
    return Path(os.path.expandvars(text)).expanduser()


WORKSPACE = expand_config_path(PATHS["workspace_root"])
VAULT = expand_config_path(PATHS["obsidian_vault"])
CONFIG_VARS = {
    "WORKSPACE_ROOT": str(WORKSPACE),
    "OBSIDIAN_VAULT": str(VAULT),
}
AGENT_ROOT = VAULT / "90_Agent"
TASKS_DIR = AGENT_ROOT / "tasks"
OUTPUTS_DIR = AGENT_ROOT / "outputs"
DRAFTS_DIR = AGENT_ROOT / "drafts"
REVIEWS_DIR = AGENT_ROOT / "reviews"
SKILL_REPORTS_DIR = AGENT_ROOT / "skill-reports"
QA_DIR = AGENT_ROOT / "qa"
LOGS_DIR = AGENT_ROOT / "logs"
TEST_DIR = AGENT_ROOT / "test"
WECHAT_DAILY_DIR = VAULT / "微信渠道" / "_daily"
ARTICLE_DRAFTS_DIR = VAULT / "03.公众号" / "_agent_drafts"

ALLOWED_WRITE_ROOTS = [expand_config_path(p, CONFIG_VARS).resolve() for p in PATHS["allowed_write_roots"]]
STATUS_LABELS = {
    "queued": {"zh": "排队中", "en": "queued"},
    "running": {"zh": "运行中", "en": "running"},
    "review_needed": {"zh": "需要人工审阅", "en": "review needed"},
    "done": {"zh": "已完成", "en": "done"},
    "blocked": {"zh": "被阻塞", "en": "blocked"},
}


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def is_allowed_write(path: Path) -> bool:
    target = path.resolve()
    return any(target == root or root in target.parents for root in ALLOWED_WRITE_ROOTS)


def safe_write(path: Path, content: str) -> None:
    if not is_allowed_write(path):
        raise SystemExit(f"Refusing to write outside allowed roots: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path, max_chars: int = 12000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def resolve_source(value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    return p


def run_capture(cmd: list[str], cwd: Path = ROOT, timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 124, str(exc)


def cmd_doctor(_: argparse.Namespace) -> None:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("workspace_root", WORKSPACE.exists(), str(WORKSPACE)))
    checks.append(("obsidian_vault", VAULT.exists(), str(VAULT)))
    checks.append(("node", shutil.which("node") is not None, shutil.which("node") or "missing"))
    checks.append(("npm", shutil.which("npm") is not None, shutil.which("npm") or "missing"))
    checks.append(("npx", shutil.which("npx") is not None, shutil.which("npx") or "missing"))
    checks.append(("agent-network runtime", ANET_RUNTIME.exists(), str(ANET_RUNTIME)))
    checks.append(("runtime anet", (ANET_RUNTIME / "node_modules" / ".bin" / "anet").exists(), str(ANET_RUNTIME / "node_modules" / ".bin" / "anet")))
    checks.append(("runtime bunx", (ANET_RUNTIME / "node_modules" / ".bin" / "bunx").exists(), str(ANET_RUNTIME / "node_modules" / ".bin" / "bunx")))
    security_scan_skill = expand_config_path(PATHS["local_sources"]["security_scan_skill"], CONFIG_VARS)
    checks.append(("security-scan skill", security_scan_skill.exists(), str(security_scan_skill)))

    print("# agent-network workbench doctor")
    failed = False
    for name, ok, detail in checks:
        mark = "OK" if ok else "MISSING"
        print(f"- {mark}: {name} -> {detail}")
        failed = failed or not ok

    if (ANET_RUNTIME / "node_modules" / ".bin" / "anet").exists():
        code, out = run_capture(["npm", "run", "-s", "anet", "--", "-v"], timeout=45)
        print("\n## anet version")
        print(out or f"exit={code}")

    if failed:
        print("\nInstall local dependencies with: npm install")
        raise SystemExit(1)


def cmd_init(_: argparse.Namespace) -> None:
    for directory in [
        TASKS_DIR,
        OUTPUTS_DIR,
        DRAFTS_DIR,
        REVIEWS_DIR,
        SKILL_REPORTS_DIR,
        QA_DIR,
        LOGS_DIR,
        TEST_DIR,
        WECHAT_DAILY_DIR,
        ARTICLE_DRAFTS_DIR,
    ]:
        if not is_allowed_write(directory):
            raise SystemExit(f"Refusing to create directory outside allowed roots: {directory}")
        directory.mkdir(parents=True, exist_ok=True)

    test_note = TEST_DIR / f"agent-network-smoke-{now_id()}.md"
    safe_write(
        test_note,
        "\n".join(
            [
                "---",
                "type: agent-network-smoke-test",
                f"created_at: {now_iso()}",
                "status: created",
                "---",
                "",
                "# Agent Network Smoke Test",
                "",
                "This note proves the workbench can write only inside the approved `90_Agent/test` area.",
                "",
                "- No core Obsidian notes were modified.",
                "- No publish, push, or delete operation was performed.",
                "",
            ]
        ),
    )
    print(f"Initialized workbench directories under: {AGENT_ROOT}")
    print(f"Created smoke note: {test_note}")


def cmd_roles(_: argparse.Namespace) -> None:
    for role in ROLES:
        print(f"## {role.get('name_zh', role['id'])} / {role.get('name_en', role['id'])}")
        print(f"- id: {role['id']}")
        print(f"- runtime: {role['runtime']}")
        print(f"- 用途 / Purpose: {role.get('purpose_zh', '')}")
        print(f"- English: {role['purpose']}")
        print(f"- 可写目录 / write_roots: {', '.join(role['write_roots'])}")
        print()


def task_output_path(task_type: str, task_id: str) -> Path:
    if task_type == "article_pipeline":
        return ARTICLE_DRAFTS_DIR / f"{task_id}.md"
    if task_type == "skill_maintenance":
        return SKILL_REPORTS_DIR / f"{task_id}.md"
    return WECHAT_DAILY_DIR / f"{task_id}.md"


def cmd_create_task(args: argparse.Namespace) -> None:
    task_type = args.type
    if task_type not in PIPELINES:
        raise SystemExit(f"Unknown task type: {task_type}")
    task_id = f"{task_type}_{now_id()}"
    source = str(resolve_source(args.source) or default_source_for(task_type))
    output = str(task_output_path(task_type, task_id))
    pipeline = PIPELINES[task_type]
    assigned_roles = pipeline["roles"]
    task = {
        "id": task_id,
        "type": task_type,
        "type_label": {
            "zh": pipeline.get("label_zh", task_type),
            "en": pipeline.get("label_en", task_type),
        },
        "source": source,
        "output": output,
        "status": "queued",
        "status_label": STATUS_LABELS["queued"],
        "created_at": now_iso(),
        "assigned_roles": assigned_roles,
        "assigned_roles_detail": [
            {
                "id": role_id,
                "name_zh": ROLE_BY_ID.get(role_id, {}).get("name_zh", role_id),
                "name_en": ROLE_BY_ID.get(role_id, {}).get("name_en", role_id),
            }
            for role_id in assigned_roles
        ],
        "notes": args.notes or "本地工作台创建的任务 / Created by local workbench helper.",
    }
    task_path = TASKS_DIR / f"{task_id}.json"
    safe_write(task_path, json.dumps(task, ensure_ascii=False, indent=2) + "\n")
    print(f"Created task: {task_path}")
    print(json.dumps(task, ensure_ascii=False, indent=2))


def default_source_for(task_type: str) -> Path:
    if task_type == "article_pipeline":
        return WORKSPACE / "wechat-articles"
    if task_type == "skill_maintenance":
        return WORKSPACE / ".agents" / "skills"
    return VAULT / "微信渠道"


def recent_markdown(root: Path, limit: int = 8) -> list[Path]:
    if not root.exists():
        return []
    files = [p for p in root.rglob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def summarize_markdown_file(path: Path) -> str:
    text = read_text(path, 200000)
    lines = text.splitlines()
    types: Counter[str] = Counter()
    for line in lines:
        if line.startswith("## ") and " · " in line:
            kind = line.rsplit(" · ", 1)[-1].strip().split(" ", 1)[0]
            if kind:
                types[kind] += 1
    type_summary = ", ".join(f"{kind}:{count}" for kind, count in types.most_common(5)) or "未识别"
    return f"{path.name}：约 {len(lines)} 行，消息类型统计 {type_summary}。未展示原始聊天内容。"


def cmd_pilot(args: argparse.Namespace) -> None:
    task_type = args.type
    source = resolve_source(args.source) or default_source_for(task_type)
    task_id = f"{task_type}_{now_id()}"
    output = task_output_path(task_type, task_id)

    if task_type == "daily_digest":
        content = render_daily_digest(source, task_id)
    elif task_type == "article_pipeline":
        content = render_article_pipeline(source, task_id)
    elif task_type == "skill_maintenance":
        content = render_skill_maintenance(source, task_id)
    else:
        raise SystemExit(f"Unknown pilot type: {task_type}")

    safe_write(output, content)
    print(f"已写入试点产物 / Wrote pilot output: {output}")


def render_header(title: str, task_id: str, task_type: str, source: Path) -> list[str]:
    pipeline = PIPELINES.get(task_type, {})
    return [
        "---",
        "type: agent-network-pilot-output",
        f"task_id: {task_id}",
        f"task_type: {task_type}",
        f"task_type_label_zh: {json.dumps(pipeline.get('label_zh', task_type), ensure_ascii=False)}",
        f"task_type_label_en: {json.dumps(pipeline.get('label_en', task_type), ensure_ascii=False)}",
        f"source: {json.dumps(str(source), ensure_ascii=False)}",
        f"created_at: {now_iso()}",
        "status: review_needed",
        "status_label_zh: 需要人工审阅",
        "status_label_en: review needed",
        "---",
        "",
        f"# {title}",
        "",
    ]


def render_daily_digest(source: Path, task_id: str) -> str:
    lines = render_header("Obsidian 日报线试点输出", task_id, "daily_digest", source)
    candidates = [
        p for p in recent_markdown(VAULT / "微信渠道", 12)
        if "_daily" not in p.parts
    ][:6]
    if not candidates:
        candidates = recent_markdown(WORKSPACE / "wechat-obsidian-pipeline", 6)
    lines += [
        "## 输入概览 / Input Overview",
        "",
        f"- 优先扫描源：`{source}`",
        f"- 候选 Markdown 数量：{len(candidates)}",
        "",
        "## 今日可沉淀内容 / Things Worth Capturing",
        "",
    ]
    for path in candidates:
        lines.append(f"- {summarize_markdown_file(path)}")
    lines += [
        "",
        "## 公开前检查 / Public Sharing Review",
        "",
        "- [ ] 不包含原始私聊或完整群聊原文",
        "- [ ] 不包含群成员姓名、手机号、微信号等隐私信息",
        "- [ ] 只保留观点、工具、链接、二次整理结论",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_article_pipeline(source: Path, task_id: str) -> str:
    lines = render_header("公众号生产线试点输出", task_id, "article_pipeline", source)
    text = read_text(source, 12000) if source.is_file() else ""
    title_candidates = [
        "这篇文章可以再讲得更像人话",
        "给小白看的 AI 工具/安全/工作流文章检查清单",
        "从资料到公众号：一次 Agent 协作写作试跑",
    ]
    lines += [
        "## 标题备选 / Title Options",
        "",
        *(f"- {item}" for item in title_candidates),
        "",
        "## 初步审校 / First-pass Review",
        "",
        f"- 来源：`{source}`",
        f"- 字符数：{len(text)}",
        "- 建议补强：开头个人动机、事实来源、读者下一步操作。",
        "- 建议删除：空泛判断、未核实数字、过度产品化表述。",
        "",
        "## 配图建议 / Image Prompt Ideas",
        "",
        "- 封面：一个本地工作台调度多个 AI Agent 的可视化场景。",
        "- 中段：资料输入 -> Agent 分工 -> Markdown 输出的流程图。",
        "- 结尾：Obsidian 作为知识库，Agent Network 作为调度台。",
        "",
        "## 发布清单 / Publishing Checklist",
        "",
        "- [ ] 链接可打开",
        "- [ ] 数据有来源",
        "- [ ] 标题不夸大",
        "- [ ] 配图不泄露本地路径或私密内容",
        "",
    ]
    return "\n".join(lines) + "\n"


def render_skill_maintenance(source: Path, task_id: str) -> str:
    lines = render_header("Skill 工厂线试点输出", task_id, "skill_maintenance", source)
    skill_files = []
    if source.is_dir():
        skill_files = sorted(source.rglob("SKILL.md"))
    elif source.name == "SKILL.md":
        skill_files = [source]

    lines += [
        "## Skill 清单 / Skill Inventory",
        "",
    ]
    for path in skill_files[:20]:
        first = read_text(path, 800).splitlines()[:8]
        name = next((line for line in first if line.startswith("name:")), "name: unknown")
        desc = next((line for line in first if line.startswith("description:")), "description: missing or multiline")
        lines.append(f"- `{path}`：{name}; {desc}")

    scanner = WORKSPACE / ".agents" / "skills" / "security-scan" / "scripts" / "supply_chain_scan.py"
    if scanner.exists():
        code, out = run_capture(["python3", str(scanner), str(source), "--json"], timeout=60)
        lines += [
            "",
            "## security-scan 只读结果 / Read-only Scan Result",
            "",
            f"- exit_code: {code}",
            "",
            "```json",
            out[:4000],
            "```",
        ]
    lines += [
        "",
        "## 发布前检查 / Pre-release Checklist",
        "",
        "- [ ] SKILL.md frontmatter 有 name 和 description",
        "- [ ] description 覆盖触发场景",
        "- [ ] scripts 可只读运行或有明确安全边界",
        "- [ ] README 没有泄露本地绝对隐私路径或 token",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Local helper for siuser agent-network workbench.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("init")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("roles")
    p.set_defaults(func=cmd_roles)

    p = sub.add_parser("create-task")
    p.add_argument("type", choices=sorted(PIPELINES.keys()))
    p.add_argument("--source")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_create_task)

    p = sub.add_parser("pilot")
    p.add_argument("type", choices=sorted(PIPELINES.keys()))
    p.add_argument("--source")
    p.set_defaults(func=cmd_pilot)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
