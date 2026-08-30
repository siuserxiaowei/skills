#!/usr/bin/env python3
"""Locate local account stores and manage private vault metadata."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from page_store import BLOCK_BYTES, classify_first_block, secret_matches


REQUIRED_DATABASES = frozenset({"message.db", "session.db", "user.db"})
CONFIG_FILE = Path.home() / ".config" / "wecom-local-vault.json"
DEFAULT_STORAGE = Path.home() / "Library" / "Application Support" / "wecom-local-vault"
MACOS_SEARCH_ROOTS = (
    Path.home() / "Library" / "Containers" / "com.tencent.WeWorkMac" / "Data" / "Library" / "Application Support" / "WXWork",
    Path.home() / "Library" / "Containers" / "com.tencent.WeWorkMac" / "Data" / "Library" / "WecomPrivate",
    Path.home() / "Library" / "Group Containers" / "88L2Q4487U.com.tencent.WeWorkMac" / "WeWorkMac",
)


@dataclass(frozen=True)
class DataHome:
    path: Path

    @property
    def snapshots(self) -> Path:
        return self.path / "snapshots"

    @property
    def private(self) -> Path:
        return self.path / "private"

    @property
    def exports(self) -> Path:
        return self.path / "exports"


@dataclass(frozen=True)
class SecretRecord:
    secret: bytes
    account_label: str | None
    source: Path


def _settings() -> dict:
    if not CONFIG_FILE.is_file():
        return {}
    value = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"configuration must be a JSON object: {CONFIG_FILE}")
    return value


def active_home() -> DataHome:
    override = os.environ.get("WECOM_LOCAL_VAULT_HOME")
    configured = _settings().get("vault_dir")
    return DataHome(Path(override or configured or DEFAULT_STORAGE).expanduser())


def account_label(account: Path) -> str:
    normalized = str(account.resolve()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()[:12]


def find_accounts(search_roots: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()
    for raw_root in search_roots:
        root = raw_root.expanduser()
        if not root.exists():
            continue
        candidates = [root] if root.is_dir() else []
        candidates.extend(path.parent for path in root.rglob("message.db"))
        for candidate in candidates:
            if all((candidate / name).is_file() for name in REQUIRED_DATABASES):
                found.add(candidate.resolve())
    return sorted(found)


def discover_accounts(explicit: str | None = None) -> list[Path]:
    if explicit:
        return find_accounts([Path(explicit)])
    configured = _settings().get("data_dir")
    return find_accounts([Path(configured)]) if configured else find_accounts(MACOS_SEARCH_ROOTS)


def select_account(explicit: str | None = None) -> Path:
    choices = discover_accounts(explicit)
    if not choices:
        raise SystemExit("未发现同时含 message.db、session.db、user.db 的企业微信数据目录")
    if len(choices) > 1 and explicit is None and not _settings().get("data_dir"):
        labels = ", ".join(account_label(path) for path in choices)
        raise SystemExit(f"发现多个账号数据集（{labels}），请用 --data-dir 精确选择")
    return choices[0]


def database_files(account: Path) -> Iterator[tuple[Path, Path]]:
    for file in sorted(account.rglob("*.db")):
        if file.is_file() and file.stat().st_size >= BLOCK_BYTES:
            yield file.relative_to(account), file


def describe_account(account: Path) -> dict:
    entries: list[dict] = []
    formats: dict[str, int] = {}
    wal_files = 0
    for relative, file in database_files(account):
        with file.open("rb") as handle:
            flavor = classify_first_block(handle.read(BLOCK_BYTES))
        formats[flavor] = formats.get(flavor, 0) + 1
        has_wal = file.with_name(file.name + "-wal").is_file()
        wal_files += int(has_wal)
        entries.append({"name": str(relative), "format": flavor, "bytes": file.stat().st_size, "has_wal": has_wal})
    return {
        "dataset_id": account_label(account),
        "database_count": len(entries),
        "formats": formats,
        "wal_count": wal_files,
        "databases": entries,
    }


def databases_accepting(secret: bytes, account: Path) -> list[str]:
    accepted: list[str] = []
    for relative, file in database_files(account):
        with file.open("rb") as handle:
            first = handle.read(BLOCK_BYTES)
        if classify_first_block(first) == "wecom-aes128" and secret_matches(secret, first):
            accepted.append(str(relative))
    return accepted


def _private_json_write(path: Path, payload: dict) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace existing private file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            rendered = json.dumps(payload, ensure_ascii=False, indent=2)
            handle.write(rendered + chr(10))
    except BaseException:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def store_verified_secret(home: DataHome, account: Path, secret: bytes, destination: Path | None = None) -> Path:
    matches = databases_accepting(secret, account)
    if not matches:
        raise ValueError("candidate secret failed every encrypted database check")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = destination or home.private / f"key-{stamp}.json"
    _private_json_write(target, {
        "schema": 2,
        "dataset_id": account_label(account),
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "secret_hex": secret.hex(),
        "verified_against": matches,
    })
    return target


def _default_secret_path(home: DataHome) -> Path:
    choices = sorted(home.private.glob("key-*.json")) if home.private.is_dir() else []
    if choices:
        return choices[-1]
    compatibility = [home.private / "keys.json"]
    legacy = sorted(home.private.glob("keys-*.json")) if home.private.is_dir() else []
    existing = [path for path in compatibility + legacy if path.is_file()]
    if not existing:
        raise FileNotFoundError("no private key record exists")
    return existing[-1]


def read_secret_record(home: DataHome, source: Path | None = None) -> SecretRecord:
    path = source or _default_secret_path(home)
    permissions = path.stat().st_mode & 0o777
    if permissions & 0o077:
        raise PermissionError(f"密钥文件必须为 0600，当前是 {oct(permissions)}: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("key record must be a JSON object")
    encoded = payload.get("secret_hex") or payload.get("global_key")
    try:
        secret = bytes.fromhex(str(encoded))
    except (TypeError, ValueError) as exc:
        raise ValueError("key record does not contain hexadecimal key material") from exc
    if len(secret) != 16:
        raise ValueError("key record must contain exactly 16 secret bytes")
    label = payload.get("dataset_id")
    return SecretRecord(secret, str(label) if label else None, path)


def newest_snapshot(home: DataHome) -> Path:
    choices = sorted(path for path in home.snapshots.glob("*") if path.is_dir()) if home.snapshots.is_dir() else []
    if not choices:
        raise SystemExit("尚无明文快照，请先执行 decrypt")
    return choices[-1]
