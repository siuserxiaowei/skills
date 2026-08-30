#!/usr/bin/env python3
"""Compatibility entry point for private SQLCipher snapshot creation."""

import sys

from vault_crypto import run_snapshot
from vault_shared import VaultError


if __name__ == "__main__":
    try:
        raise SystemExit(run_snapshot())
    except VaultError as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(2)
