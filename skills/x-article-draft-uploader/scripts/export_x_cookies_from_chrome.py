#!/usr/bin/env python3
"""Export only X-domain cookies from an owner-selected macOS Chrome profile."""

from __future__ import annotations

import argparse
import datetime as datetime_module
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2


CHROME_TO_UNIX_SECONDS = 11_644_473_600


class CookieExportError(RuntimeError):
    pass


def unix_expiry(chrome_microseconds: int | None) -> float:
    if not chrome_microseconds:
        return -1
    return max(0.0, chrome_microseconds / 1_000_000 - CHROME_TO_UNIX_SECONDS)


def exact_domain_match(host: str, allowed: str) -> bool:
    host_value = host.casefold().lstrip(".")
    allowed_value = allowed.casefold().lstrip(".")
    return host_value == allowed_value or host_value.endswith("." + allowed_value)


def safe_storage_secret() -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode or not result.stdout.strip():
        raise CookieExportError("macOS Keychain did not provide Chrome Safe Storage")
    return result.stdout.strip()


def legacy_key(secret: str) -> bytes:
    return PBKDF2(secret.encode(), b"saltysalt", dkLen=16, count=1003)


def unpad(value: bytes) -> bytes:
    if not value:
        return value
    count = value[-1]
    return value[:-count] if 1 <= count <= 16 and value.endswith(bytes([count]) * count) else value


def decrypt_value(host: str, encrypted: bytes, secret: str) -> str:
    if not encrypted:
        return ""
    if encrypted[:3] not in (b"v10", b"v11"):
        return encrypted.decode("utf-8", errors="ignore")
    plaintext = AES.new(legacy_key(secret), AES.MODE_CBC, iv=b" " * 16).decrypt(encrypted[3:])
    plaintext = unpad(plaintext)
    prefix = hashlib.sha256(host.encode()).digest()
    if plaintext.startswith(prefix):
        plaintext = plaintext[len(prefix) :]
    return plaintext.decode("utf-8", errors="ignore")


def copy_database(source: Path, destination: Path) -> None:
    try:
        original = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        clone = sqlite3.connect(destination)
        original.backup(clone)
    except sqlite3.Error as exc:
        raise CookieExportError(f"cannot snapshot Chrome Cookies database: {exc}") from exc
    finally:
        if "clone" in locals():
            clone.close()
        if "original" in locals():
            original.close()


def same_site_label(value: int | None) -> str:
    return {0: "None", 1: "Lax", 2: "Strict"}.get(value, "Lax")


def read_allowed_rows(database: Path, domains: list[str]) -> list[sqlite3.Row]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT host_key,name,path,value,encrypted_value,expires_utc,is_secure,is_httponly,samesite FROM cookies"
        ).fetchall()
    finally:
        connection.close()
    return [row for row in rows if any(exact_domain_match(row["host_key"], domain) for domain in domains)]


def playwright_cookie(row: sqlite3.Row, secret: str) -> dict | None:
    value = row["value"] or decrypt_value(row["host_key"], row["encrypted_value"], secret)
    if not value:
        return None
    return {
        "name": row["name"],
        "value": value,
        "domain": row["host_key"],
        "path": row["path"] or "/",
        "expires": unix_expiry(row["expires_utc"]),
        "httpOnly": bool(row["is_httponly"]),
        "secure": bool(row["is_secure"]),
        "sameSite": same_site_label(row["samesite"]),
    }


def atomic_private_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def export(profile: Path, output: Path, domains: list[str]) -> int:
    source = profile / "Cookies"
    if not source.is_file():
        raise CookieExportError(f"Cookies database is missing: {source}")
    secret = safe_storage_secret()
    with tempfile.TemporaryDirectory(prefix="chrome-cookie-snapshot-") as directory:
        snapshot = Path(directory) / "Cookies.sqlite"
        copy_database(source, snapshot)
        rows = read_allowed_rows(snapshot, domains)
    cookies = [cookie for row in rows if (cookie := playwright_cookie(row, secret)) is not None]
    payload = {"cookies": cookies, "origins": []}
    atomic_private_json(output, payload)
    return len(cookies)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True, help="exact Chrome profile directory selected by the user")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--domains", nargs="+", default=["x.com", "twitter.com"])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    profile = args.profile.expanduser().resolve(strict=False)
    output = args.output.expanduser().resolve(strict=False)
    preview = {"profile": str(profile), "output": str(output), "domains": args.domains, "reads_cookie_values": args.apply, "prints_cookie_values": False}
    if not args.apply:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    count = export(profile, output, args.domains)
    print(
        json.dumps(
            {
                "exported_cookie_count": count,
                "output": str(output),
                "mode": oct(output.stat().st_mode & 0o777),
                "created_at": datetime_module.datetime.now(datetime_module.timezone.utc).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CookieExportError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
