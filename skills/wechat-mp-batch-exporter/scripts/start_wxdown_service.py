#!/usr/bin/env python3
"""Validate and start an owner-provided wxdown-service checkout."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


PROXY_VARIABLES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def valid_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1024 and 65535")
    return port


def resolve_runtime(project: Path) -> tuple[Path, Path]:
    candidates = [project / ".venv/bin/python", project / "venv/bin/python"]
    interpreter = next((path for path in candidates if path.is_file()), candidates[0])
    return interpreter, project / "main.py"


def command_for(project: Path, proxy_port: int, websocket_port: int, debug: bool) -> list[str]:
    interpreter, entrypoint = resolve_runtime(project)
    command = [str(interpreter), str(entrypoint), "--port", str(proxy_port), "--wport", str(websocket_port)]
    if debug:
        command.append("--debug")
    return command


def sanitized_environment(keep_proxy: bool) -> dict[str, str]:
    environment = dict(os.environ)
    if not keep_proxy:
        for name in PROXY_VARIABLES:
            environment.pop(name, None)
    return environment


def preflight(project: Path, command: list[str], keep_proxy: bool) -> dict:
    interpreter, entrypoint = resolve_runtime(project)
    return {
        "project": str(project),
        "project_exists": project.is_dir(),
        "interpreter": str(interpreter),
        "interpreter_exists": interpreter.is_file(),
        "entrypoint": str(entrypoint),
        "entrypoint_exists": entrypoint.is_file(),
        "command": command,
        "inherits_proxy_environment": keep_proxy,
        "changes_system_proxy": False,
        "controls_wechat_ui": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(os.environ.get("WXDOWN_SERVICE_DIR", "~/src/wxdown-service")))
    parser.add_argument("--proxy-port", type=valid_port, default=65000)
    parser.add_argument("--websocket-port", type=valid_port, default=65001)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--inherit-proxy", action="store_true", help="retain existing proxy environment intentionally")
    parser.add_argument("--apply", action="store_true", help="start the process after reviewing preflight")
    args = parser.parse_args(argv)
    project = args.project.expanduser().resolve(strict=False)
    if args.proxy_port == args.websocket_port:
        parser.error("proxy and websocket ports must differ")
    command = command_for(project, args.proxy_port, args.websocket_port, args.debug)
    report = preflight(project, command, args.inherit_proxy)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not args.apply:
        return 0
    if not report["interpreter_exists"] or not report["entrypoint_exists"]:
        return 2
    return subprocess.call(command, cwd=project, env=sanitized_environment(args.inherit_proxy))


if __name__ == "__main__":
    raise SystemExit(main())
