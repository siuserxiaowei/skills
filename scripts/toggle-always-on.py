#!/usr/bin/env python3
"""Enable or disable the task-status managed block in a user AGENTS.md."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


START = "<!-- BEGIN TASK-STATUS ALWAYS-ON -->"
END = "<!-- END TASK-STATUS ALWAYS-ON -->"
BLOCK = f"""{START}
## Codex task-status lifecycle

For substantive Codex task work, load and follow `$task-status` so the current task title reflects the seven-state lifecycle. Keep ordinary factual chat in discussion unless execution is authorized. Do not create or dispatch tasks, change history, or expand permissions without the explicit `$task-status` command and confirmations required by that skill.
{END}"""
BLOCK_RE = re.compile(
    rf"(?:\n{{0,2}}){re.escape(START)}.*?{re.escape(END)}(?:\n{{0,2}})",
    flags=re.DOTALL,
)


def default_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return Path(codex_home).expanduser() / "AGENTS.md" if codex_home else Path.home() / ".codex" / "AGENTS.md"


def has_block(text: str) -> bool:
    return START in text and END in text


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target = path.with_name(f"{path.name}.task-status.bak-{stamp}")
    shutil.copy2(path, target)
    return target


def enable(path: Path) -> tuple[bool, Path | None]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if has_block(text):
        return False, None
    if START in text or END in text:
        raise ValueError("found an incomplete task-status marker block; repair it manually before enabling")
    saved = backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = text.rstrip()
    updated = f"{prefix}\n\n{BLOCK}\n" if prefix else f"{BLOCK}\n"
    path.write_text(updated, encoding="utf-8")
    return True, saved


def disable(path: Path) -> tuple[bool, Path | None]:
    if not path.exists():
        return False, None
    text = path.read_text(encoding="utf-8")
    if not has_block(text):
        if START in text or END in text:
            raise ValueError("found an incomplete task-status marker block; repair it manually before disabling")
        return False, None
    saved = backup(path)
    updated, count = BLOCK_RE.subn("\n\n", text, count=1)
    if count != 1:
        raise ValueError("could not isolate the managed task-status block")
    normalized = updated.strip()
    path.write_text(f"{normalized}\n" if normalized else "", encoding="utf-8")
    return True, saved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("enable", "disable", "status"))
    parser.add_argument("--path", type=Path, default=default_path())
    args = parser.parse_args()
    path = args.path.expanduser()

    try:
        if args.action == "status":
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            print("enabled" if has_block(text) else "disabled")
            return 0
        changed, saved = enable(path) if args.action == "enable" else disable(path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    result = "changed" if changed else "unchanged"
    backup_text = f"; backup={saved}" if saved else ""
    print(f"{result}: {path}{backup_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
