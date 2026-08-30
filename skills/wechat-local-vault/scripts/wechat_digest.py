#!/usr/bin/env python3
"""Compatibility helper for listing digest candidates in the private snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from vault_cli import main as vault_main


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="微信本地摘要素材助手")
    parser.add_argument("date", nargs="?", help="指定日期 YYYY-MM-DD")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--list", action="store_true", help="列出可选联系人与群聊")
    parser.add_argument("--group", help="要生成素材的群名")
    options = parser.parse_args(arguments)
    prefix = []
    if options.config:
        with Path(options.config).expanduser().open("r", encoding="utf-8") as stream:
            settings = json.load(stream)
        if settings.get("decrypted_dir"):
            prefix += ["--decrypted-dir", str(settings["decrypted_dir"])]
    if options.list or not options.group:
        return vault_main(prefix + ["contacts", "--format", "text"])
    mapped = prefix + ["digest-source", options.group, "--format", "text"]
    if options.date:
        mapped += ["--start", options.date, "--end", options.date]
    return vault_main(mapped)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
