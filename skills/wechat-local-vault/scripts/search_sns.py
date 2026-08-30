#!/usr/bin/env python3
"""Legacy-shaped read-only Moments query."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from vault_cli import main as vault_main


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="查询已解密快照中的朋友圈")
    parser.add_argument("--name")
    parser.add_argument("--username", action="append")
    parser.add_argument("--list", dest="list_query")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--keyword")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--config")
    options = parser.parse_args(arguments)
    prefix = []
    if options.config:
        with Path(options.config).expanduser().open("r", encoding="utf-8") as stream:
            settings = json.load(stream)
        if settings.get("decrypted_dir"):
            prefix += ["--decrypted-dir", str(settings["decrypted_dir"])]
    if options.list_query is not None:
        return vault_main(prefix + ["contacts", "--query", options.list_query, "--format", "json" if options.json else "text"])
    mapped = prefix + ["moments", "--limit", str(options.limit), "--format", "json" if options.json else "text"]
    for flag, value in (("--name", options.name), ("--start", options.start), ("--end", options.end), ("--keyword", options.keyword)):
        if value:
            mapped += [flag, value]
    for account in options.username or []:
        mapped += ["--username", account]
    return vault_main(mapped)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
