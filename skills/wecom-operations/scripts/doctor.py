#!/usr/bin/env python3
"""Inspect WeCom CLI readiness without opening encrypted configuration files."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path


EXPECTED_PRIVATE_FILES = (".encryption_key", "bot.enc", "mcp_config.enc")


def command_output(argv: list[str], timeout: float = 8) -> dict:
    try:
        result = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return {"exit": result.returncode, "output": " ".join(result.stdout.split())[:500]}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"exit": None, "error": str(exc)}


def configuration_metadata(root: Path) -> list[dict]:
    records = []
    for name in EXPECTED_PRIVATE_FILES:
        path = root / name
        exists = path.is_file()
        mode = stat.S_IMODE(path.stat().st_mode) if exists else None
        records.append({"name": name, "path": str(path), "exists": exists, "mode": oct(mode) if mode is not None else None, "owner_only": mode == 0o600})
    return records


def helper_metadata(raw: str | None) -> dict:
    path = Path(raw).expanduser().resolve(strict=False) if raw else None
    return {
        "configured": path is not None,
        "path": str(path) if path else None,
        "executable": bool(path and path.is_file() and os.access(path, os.X_OK)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=("doc", "meeting", "schedule", "todo", "contact"))
    parser.add_argument("--config-root", type=Path, default=Path("~/.config/wecom"))
    args = parser.parse_args(argv)
    executable = os.environ.get("WECOM_CLI") or shutil.which("wecom-cli")
    files = configuration_metadata(args.config_root.expanduser())
    report = {
        "cli": {"path": executable, "available": bool(executable), "version": command_output([executable, "--version"]) if executable else None},
        "configuration": files,
        "configuration_ready": all(item["exists"] and item["owner_only"] for item in files),
        "upload_helper": helper_metadata(os.environ.get("WECOM_UPLOAD_HELPER")),
        "privacy": {"configuration_contents_read": False, "credentials_printed": False, "remote_calls_made": False},
    }
    if args.category:
        report["category"] = {
            "name": args.category,
            "help": command_output([executable, args.category, "--help"]) if executable else None,
        }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if executable and report["configuration_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
