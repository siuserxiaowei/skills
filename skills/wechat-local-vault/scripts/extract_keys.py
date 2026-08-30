#!/usr/bin/env python3
"""Compatibility entry point for key candidate verification."""

import json
import sys

from key_capture import run_key_tool
from vault_shared import VaultError


if __name__ == "__main__":
    try:
        raise SystemExit(run_key_tool())
    except (VaultError, OSError, json.JSONDecodeError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(2)
