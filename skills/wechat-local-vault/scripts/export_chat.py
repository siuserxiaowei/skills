#!/usr/bin/env python3
"""Legacy-shaped command that delegates one conversation export to vault_cli."""

from __future__ import annotations

import argparse
import sys

from vault_cli import main as vault_main


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export one conversation from a decrypted WeChat snapshot.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--contact")
    selector.add_argument("--chat-id")
    parser.add_argument("--since")
    parser.add_argument("--mode", choices=("incremental", "full"), default="full")
    parser.add_argument("--decrypted-dir")
    parser.add_argument("--exports-dir")
    parser.add_argument("--output")
    parser.add_argument("--write-empty", action="store_true")
    options = parser.parse_args(arguments)
    if options.mode == "incremental" and not options.since:
        parser.error("独立实现的增量导出需要显式 --since，避免隐式游标漏数")
    mapped = []
    if options.decrypted_dir:
        mapped += ["--decrypted-dir", options.decrypted_dir]
    mapped += ["export", options.contact or options.chat_id]
    if options.since:
        mapped += ["--start-time", options.since]
    if options.exports_dir:
        mapped += ["--exports-dir", options.exports_dir]
    if options.output:
        mapped += ["--output", options.output]
    return vault_main(mapped)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
