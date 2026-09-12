#!/usr/bin/env python3
"""Check that README repository guide topics match manifest metadata."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MANIFEST = ROOT / "manifest.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = manifest.get("repository_topics", [])
    if not expected:
        print("manifest.json: missing repository_topics", file=sys.stderr)
        return 1

    readme = README.read_text(encoding="utf-8")
    match = re.search(r"^- Topics:\s*(.+)$", readme, flags=re.MULTILINE)
    if not match:
        print("README.md: missing repository guide topics line", file=sys.stderr)
        return 1

    actual = re.findall(r"`([^`]+)`", match.group(1))
    if actual != expected:
        print("README.md topics do not match manifest.json repository_topics", file=sys.stderr)
        print(f"expected: {expected}", file=sys.stderr)
        print(f"actual:   {actual}", file=sys.stderr)
        return 1

    print("README topics match manifest metadata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
