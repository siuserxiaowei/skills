#!/usr/bin/env python3
"""SQLCipher page decoding used by the local snapshot command."""

from __future__ import annotations

from dataclasses import dataclass
import json
import argparse
import os
import hashlib
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

from vault_shared import VaultError, VaultLocations, make_private_directory, read_json, write_private_json


@dataclass(frozen=True)
class CipherPageLayout:
    bytes_per_page: int = 4096
    trailer_bytes: int = 80
    salt_bytes: int = 16
    iv_bytes: int = 16

    @property
    def payload_end(self) -> int:
        return self.bytes_per_page - self.trailer_bytes


def unlock_page(ciphertext: bytes, key: bytes, page_number: int, layout: CipherPageLayout) -> bytes:
    if len(ciphertext) != layout.bytes_per_page:
        raise VaultError("密文页长度与 SQLCipher 页规格不符")
    if len(key) != 32:
        raise VaultError("数据库密钥必须是 32 字节")
    try:
        from Crypto.Cipher import AES
    except ImportError as exc:
        raise VaultError("缺少 pycryptodome，无法执行本地解密") from exc
    begin = layout.salt_bytes if page_number == 0 else 0
    iv = ciphertext[layout.payload_end : layout.payload_end + layout.iv_bytes]
    clear = AES.new(key, AES.MODE_CBC, iv).decrypt(ciphertext[begin : layout.payload_end])
    page = bytearray(layout.bytes_per_page)
    page[begin : layout.payload_end] = clear
    if page_number == 0:
        page[: layout.salt_bytes] = b"SQLite format 3\x00"
    return bytes(page)


def first_page_accepts(path: Path, key_hex: str) -> bool:
    try:
        key = bytes.fromhex(key_hex)
        layout = CipherPageLayout()
        with path.open("rb") as stream:
            page = stream.read(layout.bytes_per_page)
        clear = unlock_page(page, key, 0, layout)
        size = int.from_bytes(clear[16:18], "big")
        return clear[:16] == b"SQLite format 3\x00" and size == layout.bytes_per_page and clear[20] == layout.trailer_bytes
    except (OSError, ValueError, VaultError):
        return False


def decode_database(source: Path, destination: Path, key_hex: str) -> int:
    layout = CipherPageLayout()
    try:
        key = bytes.fromhex(key_hex)
    except ValueError as exc:
        raise VaultError("密钥不是十六进制") from exc
    if not first_page_accepts(source, key_hex):
        raise VaultError("密钥未通过首页校验")
    wal = Path(str(source) + "-wal")
    if wal.exists() and wal.stat().st_size:
        raise VaultError("源库存在活动 WAL；请退出微信并重新制作一致快照")
    before = source.stat()
    make_private_directory(destination.parent)
    partial = destination.with_name("." + destination.name + ".partial")
    pages = 0
    try:
        with source.open("rb") as incoming, partial.open("wb") as outgoing:
            while block := incoming.read(layout.bytes_per_page):
                if len(block) != layout.bytes_per_page:
                    raise VaultError("数据库尾部不是完整页")
                outgoing.write(unlock_page(block, key, pages, layout))
                pages += 1
            outgoing.flush()
            os.fsync(outgoing.fileno())
        partial.chmod(0o600)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise VaultError("解密期间源库发生变化，结果已丢弃")
        with sqlite3.connect(partial) as connection:
            verdict = connection.execute("PRAGMA quick_check").fetchone()[0]
        if verdict != "ok":
            raise VaultError(f"SQLite 校验失败：{verdict}")
        partial.replace(destination)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return pages


_KNOWN_DATABASES = (
    ("favorite", "favorite/favorite.db"),
    ("sns", "sns/sns.db"),
    ("session", "session/session.db"),
    ("contact", "contact/contact.db"),
    ("message_resource", "message/message_resource.db"),
    ("message_fts", "message/message_fts.db"),
    ("message_3", "message/message_3.db"),
    ("message_2", "message/message_2.db"),
    ("message_1", "message/message_1.db"),
    ("message_0", "message/message_0.db"),
)
ALIASES = dict(_KNOWN_DATABASES)


def _relative_name(alias: str) -> str | None:
    if alias in ALIASES:
        return ALIASES[alias]
    path = Path(alias)
    if path.suffix == ".db" and not path.is_absolute() and ".." not in path.parts:
        return path.as_posix()
    return None


def run_snapshot(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Decrypt keyed WeChat databases into a private local snapshot.")
    parser.add_argument("-o", "--output")
    parser.add_argument("--clean", action="store_true", help="rotate the previous snapshot before rebuilding")
    parser.add_argument("--mode", choices=("full", "incremental"), default="full")
    parser.add_argument("--no-manifest", action="store_true")
    options = parser.parse_args(arguments)
    places = VaultLocations.current()
    settings = places.settings()
    raw_root = settings.get("db_base_path")
    if not raw_root:
        raise VaultError(f"配置缺少 db_base_path：{places.config}")
    source_root = Path(str(raw_root)).expanduser()
    target_root = Path(options.output).expanduser() if options.output else places.snapshots
    keys = read_json(places.keys)
    if not isinstance(keys, dict) or not keys:
        raise VaultError(f"没有可用密钥：{places.keys}")
    if options.clean and target_root.exists():
        rotated = target_root.with_name(target_root.name + ".previous-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
        target_root.replace(rotated)
    state_file = places.state / "snapshot.json"
    prior = read_json(state_file, {})
    next_state = dict(prior) if isinstance(prior, dict) else {}
    records = []
    for alias, stored in sorted(keys.items()):
        relative = _relative_name(str(alias))
        if relative is None:
            continue
        key_hex = str(stored.get("key_hex")) if isinstance(stored, dict) else str(stored)
        source = source_root / relative
        destination = target_root / relative
        if not source.is_file():
            records.append({"database": relative, "status": "missing"})
            continue
        signature = f"{source.stat().st_size}:{source.stat().st_mtime_ns}:{hashlib.sha256(key_hex.encode()).hexdigest()}"
        if options.mode == "incremental" and destination.is_file() and prior.get(relative) == signature:
            records.append({"database": relative, "status": "unchanged"})
            continue
        try:
            pages = decode_database(source, destination, key_hex)
            next_state[relative] = signature
            records.append({"database": relative, "status": "ok", "pages": pages})
        except VaultError as exc:
            records.append({"database": relative, "status": "failed", "reason": str(exc)})
    write_private_json(state_file, next_state)
    settings.update({"vault_dir": str(places.home), "decrypted_dir": str(target_root)})
    write_private_json(places.config, settings)
    if not options.no_manifest:
        manifest = places.manifests / ("snapshot-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json")
        write_private_json(manifest, {"created_at": datetime.now().isoformat(timespec="seconds"), "records": records})
        print(f"Manifest: {manifest}")
    print(json.dumps({"output": str(target_root), "records": records}, ensure_ascii=False, indent=2))
    return 0 if all(row["status"] != "failed" for row in records) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run_snapshot())
    except VaultError as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(2)
