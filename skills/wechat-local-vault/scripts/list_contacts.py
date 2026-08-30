#!/usr/bin/env python3
"""List local contacts through the read-only archive facade."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from vault_cli import main as vault_main


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="列出已解密快照中的群聊和联系人")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--show-identifiers", action="store_true")
    options = parser.parse_args(arguments)
    mapped = []
    if options.config:
        with Path(options.config).expanduser().open("r", encoding="utf-8") as stream:
            settings = json.load(stream)
        if settings.get("decrypted_dir"):
            mapped += ["--decrypted-dir", str(settings["decrypted_dir"])]
    if options.show_identifiers:
        mapped.append("--show-identifiers")
    return vault_main(mapped + ["contacts", "--limit", "100000", "--format", "text"])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
