#!/usr/bin/env python3
"""Produce a privacy-preserving readiness report for WeChat article exports."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def file_state(path: Path) -> dict:
    return {"path": str(path), "exists": path.is_file(), "size": path.stat().st_size if path.is_file() else None}


def checkout_state(path: Path, markers: list[str]) -> dict:
    return {
        "path": str(path),
        "exists": path.is_dir(),
        "markers": {name: file_state(path / name) for name in markers},
    }


def tool_state(names: list[str]) -> dict[str, str | None]:
    return {name: shutil.which(name) for name in names}


def endpoint_probe(base: str, timeout: float) -> dict:
    endpoint = base.rstrip("/") + "/"
    request = urllib.request.Request(endpoint, headers={"User-Agent": "skill-readiness-probe/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"attempted": True, "ok": 200 <= response.status < 500, "url": endpoint, "status": response.status}
    except Exception as exc:
        return {"attempted": True, "ok": False, "url": endpoint, "error": str(exc)}


def assess(exporter: dict, service: dict, tools: dict, network: dict) -> list[Finding]:
    findings: list[Finding] = []
    local_exporter = exporter["exists"] and exporter["markers"]["package.json"]["exists"]
    public_client = bool(tools.get("python3"))
    if not local_exporter and not public_client:
        findings.append(Finding("error", "no-download-route", "neither a local exporter checkout nor Python HTTP client is available"))
    if service["exists"] and not service["markers"]["main.py"]["exists"]:
        findings.append(Finding("warning", "service-entry-missing", "wxdown checkout exists but main.py is absent"))
    if network.get("attempted") and not network.get("ok"):
        findings.append(Finding("warning", "endpoint-unreachable", str(network.get("error", "network probe failed"))))
    return findings


def build_report(exporter_path: Path, service_path: Path, api_base: str, check_network: bool) -> dict:
    exporter = checkout_state(exporter_path, ["package.json", "README.md"])
    service = checkout_state(service_path, ["main.py", "requirements.txt", ".venv/bin/python"])
    tools = tool_state(["python3", "node", "corepack", "yarn", "mitmdump"])
    network = endpoint_probe(api_base, 8) if check_network else {"attempted": False, "url": api_base.rstrip("/") + "/"}
    findings = assess(exporter, service, tools, network)
    return {
        "platform": platform.platform(),
        "exporter_checkout": exporter,
        "wxdown_checkout": service,
        "tools": tools,
        "public_api": network,
        "privacy": {
            "wechat_launched": False,
            "credentials_read": False,
            "proxy_settings_changed": False,
            "certificates_installed": False,
        },
        "manual_gates": [
            "The user completes QR login or account selection when history access requires it.",
            "The user explicitly approves certificate trust or proxy changes before those separate steps.",
            "Private metrics and comments require current owner-authorized credentials.",
        ],
        "findings": [asdict(item) for item in findings],
        "counts": {
            "error": sum(item.severity == "error" for item in findings),
            "warning": sum(item.severity == "warning" for item in findings),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exporter", type=Path, default=Path(os.environ.get("WECHAT_ARTICLE_EXPORTER_DIR", "~/src/wechat-article-exporter")))
    parser.add_argument("--wxdown", type=Path, default=Path(os.environ.get("WXDOWN_SERVICE_DIR", "~/src/wxdown-service")))
    parser.add_argument("--api-base", default="https://down.mptext.top")
    parser.add_argument("--check-network", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.exporter.expanduser(), args.wxdown.expanduser(), args.api_base, args.check_network)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["counts"]["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
