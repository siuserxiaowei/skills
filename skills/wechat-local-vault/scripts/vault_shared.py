#!/usr/bin/env python3
"""Small, dependency-free building blocks for the private WeChat archive tools."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


class VaultError(Exception):
    """An expected, user-actionable failure."""


def _environment_path(variable: str, fallback: str) -> Path:
    return Path(os.environ.get(variable, fallback)).expanduser()


@dataclass(frozen=True)
class VaultLocations:
    """Resolved storage locations; environment overrides make offline testing safe."""

    home: Path
    config: Path
    keys: Path

    @classmethod
    def current(cls) -> "VaultLocations":
        home = _environment_path(
            "WECHAT_VAULT_HOME",
            "~/Library/Application Support/wechat-local-vault",
        )
        return cls(
            home=home,
            config=_environment_path(
                "WECHAT_VAULT_CONFIG",
                "~/.config/wechat-local-vault.json",
            ),
            keys=_environment_path("WECHAT_VAULT_KEYS", "~/.config/wechat-keys.json"),
        )

    @property
    def snapshots(self) -> Path:
        return self.home / "decrypted" / "current"

    @property
    def exports(self) -> Path:
        return self.home / "exports"

    @property
    def state(self) -> Path:
        return self.home / "state"

    @property
    def manifests(self) -> Path:
        return self.home / "manifests"

    def settings(self) -> dict[str, Any]:
        value = read_json(self.config)
        return value if isinstance(value, dict) else {}

    def decrypted_root(self, override: str | None = None) -> Path:
        configured = self.settings().get("decrypted_dir")
        return Path(override or configured or self.snapshots).expanduser()

    def export_root(self, override: str | None = None) -> Path:
        configured = self.settings().get("exports_dir")
        return Path(override or configured or self.exports).expanduser()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return {} if default is None else default
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise VaultError(f"无法读取 JSON：{path}（{exc}）") from exc


def make_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def write_private_json(path: Path, payload: Any) -> None:
    """Atomically replace a private JSON file without leaking through default umask."""

    make_private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        path.chmod(0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def write_new_private_text(path: Path, text: str) -> None:
    """Create a report once. Existing reports are never replaced implicitly."""

    make_private_directory(path.parent)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise VaultError(f"输出文件已存在，未覆盖：{path}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(text)
        if text and not text.endswith("\n"):
            stream.write("\n")


def parse_clock(value: str | None, finish_day: bool = False) -> int | None:
    if not value:
        return None
    cleaned = value.strip()
    patterns = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
    for pattern in patterns:
        try:
            moment = datetime.strptime(cleaned, pattern)
        except ValueError:
            continue
        if finish_day and pattern == "%Y-%m-%d":
            moment = moment.replace(hour=23, minute=59, second=59)
        return int(moment.timestamp())
    raise VaultError(f"无法识别时间：{value}")


def filename_fragment(value: str, maximum: int = 72) -> str:
    without_controls = "".join(ch for ch in value if ord(ch) >= 32)
    normalized = re.sub(r"[\\/:*?\"<>|\s]+", "-", without_controls).strip("-.")
    return (normalized[:maximum] or "wechat-report").rstrip("-.")


def public_identifier(value: str, enabled: bool) -> str | None:
    return value if enabled else None


def timestamp_text(epoch: int, minute_precision: bool = False) -> str:
    if epoch <= 0:
        return ""
    template = "%Y-%m-%d %H:%M" if minute_precision else "%Y-%m-%d %H:%M:%S"
    return datetime.fromtimestamp(epoch).strftime(template)
