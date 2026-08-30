#!/usr/bin/env python3
"""Offline key-candidate inventory and verification for local WeChat databases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys

from vault_crypto import ALIASES, first_page_accepts
from vault_shared import VaultError, VaultLocations, write_private_json


CAPTURE_LOG = Path(os.environ.get("WECHAT_VAULT_CAPTURE_LOG", "/tmp/wechat_frida_keys.log"))


@dataclass(frozen=True)
class EncryptedDatabase:
    label: str
    relative: str
    path: Path
    salt_hex: str
    byte_count: int


def locate_database_root(override: str | None, locations: VaultLocations) -> tuple[str, Path]:
    if override:
        root = Path(override).expanduser()
        return root.parent.name, root
    settings = locations.settings()
    if settings.get("db_base_path"):
        root = Path(str(settings["db_base_path"])).expanduser()
        return str(settings.get("wxid") or root.parent.name), root
    container = Path("~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files").expanduser()
    candidates = sorted(container.glob("*/db_storage"))
    if len(candidates) != 1:
        raise VaultError("无法唯一确定官方微信数据库目录；请传 --db-base")
    return candidates[0].parent.name, candidates[0]


def discover_encrypted_files(root: Path) -> list[EncryptedDatabase]:
    if not root.is_dir():
        raise VaultError(f"数据库目录不存在：{root}")
    aliases_by_path = {relative: alias for alias, relative in ALIASES.items()}
    result = []
    for path in sorted(root.rglob("*.db")):
        if not path.is_file() or path.stat().st_size < 4096:
            continue
        relative = path.relative_to(root).as_posix()
        with path.open("rb") as stream:
            salt = stream.read(16).hex()
        result.append(
            EncryptedDatabase(
                label=aliases_by_path.get(relative, relative),
                relative=relative,
                path=path,
                salt_hex=salt,
                byte_count=path.stat().st_size,
            )
        )
    return result


def read_capture_events(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    valid_hex = re.compile(r"^[0-9a-fA-F]+$")
    events: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_name = raw.get("event") or raw.get("type")
            salt = str(raw.get("salt_hex") or raw.get("salt") or "")
            key = str(raw.get("key_hex") or raw.get("dk") or "")[:64]
            if event_name not in {"derived", "pbkdf2"}:
                continue
            if len(key) != 64 or not valid_hex.fullmatch(key):
                continue
            if salt and not valid_hex.fullmatch(salt):
                continue
            events.append({"salt_hex": salt.lower(), "key_hex": key.lower()})
    return events


def verify_candidates(
    databases: list[EncryptedDatabase],
    events: list[dict[str, str]],
    existing: dict,
    targets: set[str],
) -> tuple[dict[str, str], list[str]]:
    accepted = {
        str(name): str(value.get("key_hex") if isinstance(value, dict) else value)
        for name, value in existing.items()
    }
    missing = []
    for database in databases:
        if database.label not in targets and database.relative not in targets:
            continue
        candidates = []
        old = accepted.get(database.label) or accepted.get(database.relative)
        if old:
            candidates.append(old)
        candidates.extend(
            event["key_hex"]
            for event in events
            if not event["salt_hex"] or event["salt_hex"] == database.salt_hex
        )
        match = next((candidate for candidate in dict.fromkeys(candidates) if first_page_accepts(database.path, candidate)), None)
        if match:
            accepted[database.label] = match
        else:
            missing.append(database.label)
    return accepted, missing


def run_key_tool(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect encrypted WeChat databases and verify captured key candidates.")
    parser.add_argument("--db-base")
    parser.add_argument("--targets", default="sns,favorite")
    parser.add_argument("--duration", type=int, default=120)
    parser.add_argument("--mode", choices=("attach", "spawn"), default="spawn")
    parser.add_argument("--wechat-copy")
    parser.add_argument("--reuse-log", action="store_true")
    parser.add_argument("--skip-prepare", action="store_true")
    parser.add_argument("--list-dbs", action="store_true")
    parser.add_argument("--match-only", action="store_true")
    parser.add_argument("--show-sensitive", action="store_true")
    options = parser.parse_args(arguments)
    locations = VaultLocations.current()
    account, root = locate_database_root(options.db_base, locations)
    databases = discover_encrypted_files(root)
    for database in databases:
        details = f"{database.label}: {database.byte_count} bytes"
        if options.show_sensitive:
            details += f" salt={database.salt_hex} path={database.path}"
        print(details)
    if options.list_dbs:
        return 0
    if not options.match_only:
        raise VaultError("本原创版本不执行实时进程注入；请将本机授权工具产生的候选写入 capture log，再用 --match-only 离线校验")
    existing = {}
    if locations.keys.is_file():
        with locations.keys.open("r", encoding="utf-8") as stream:
            existing = json.load(stream)
    targets = {item.strip() for item in options.targets.split(",") if item.strip()}
    if options.targets == "all":
        targets = {database.label for database in databases}
    matched, missing = verify_candidates(databases, read_capture_events(CAPTURE_LOG), existing, targets)
    write_private_json(locations.keys, matched)
    settings = locations.settings()
    settings.update({"wxid": account, "db_base_path": str(root)})
    write_private_json(locations.config, settings)
    print(json.dumps({"matched": len(targets) - len(missing), "missing": missing}, ensure_ascii=False))
    return 2 if missing else 0


if __name__ == "__main__":
    try:
        raise SystemExit(run_key_tool())
    except (VaultError, OSError, json.JSONDecodeError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(2)
