#!/usr/bin/env python3
"""Create a portable task-status ZIP and reject personal absolute paths."""

from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt"}
EXCLUDED_PARTS = {
    "__pycache__",
    ".DS_Store",
    ".git",
    ".github",
    "dist",
    "docs",
}
EXCLUDED_ROOT_FILES = {
    ".gitignore",
    "LICENSE",
    "README.md",
    "SECURITY.md",
}
PERSONAL_PATHS = [
    re.compile("/" + r"Users/[^/\s]+/"),
    re.compile(r"[A-Za-z]:\\" + r"Users\\[^\\\s]+\\"),
]


def source_files() -> list[Path]:
    files = []
    for path in SKILL_DIR.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.parent == SKILL_DIR and path.name in EXCLUDED_ROOT_FILES:
            continue
        if path.suffix in {".pyc", ".zip"}:
            continue
        files.append(path)
    return sorted(files)


def validate_portable(files: list[Path]) -> None:
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PERSONAL_PATHS:
            if pattern.search(text):
                raise ValueError(f"personal absolute path found in {path.relative_to(SKILL_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    files = source_files()
    validate_portable(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(SKILL_DIR)
            info = zipfile.ZipInfo.from_file(path, arcname=str(Path(SKILL_DIR.name) / relative))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
