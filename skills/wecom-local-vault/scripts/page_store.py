#!/usr/bin/env python3
"""Decode WeCom's 4096-byte AES database pages into a fresh SQLite image."""

from __future__ import annotations

import struct
import os
import hashlib
from pathlib import Path


BLOCK_BYTES = 4096
SQLITE_SIGNATURE = b"SQLite format 3\x00"
_DERIVATION_SUFFIX = b"sAlT"
_WAL_MAGIC = {0x377F0682, 0x377F0683}


def _aes_cbc(secret: bytes, vector: bytes, material: bytes, *, decrypt: bool) -> bytes:
    try:
        from Crypto.Cipher import AES
    except ImportError as exc:  # pragma: no cover - depends on the host environment
        raise RuntimeError("decrypt requires pycryptodome (Crypto.Cipher.AES)") from exc
    if len(material) % 16:
        raise ValueError("AES page material must end on a 16-byte boundary")
    cipher = AES.new(secret, AES.MODE_CBC, vector)
    return cipher.decrypt(material) if decrypt else cipher.encrypt(material)


def _advance_seed(seed: int) -> int:
    high, low = divmod(seed, 52774)
    next_value = 40692 * low - 3791 * high
    return next_value if next_value >= 0 else next_value + 2147483399


def _page_material(secret: bytes, ordinal: int) -> tuple[bytes, bytes]:
    if len(secret) != 16:
        raise ValueError("database secret must contain 16 bytes")
    if ordinal <= 0:
        raise ValueError("page ordinals begin at one")
    evolving = ordinal + 1
    vector_seed = bytearray()
    for _index in range(4):
        evolving = _advance_seed(evolving)
        vector_seed += struct.pack("<I", evolving & 0xFFFFFFFF)
    vector = hashlib.md5(vector_seed).digest()
    page_secret = hashlib.md5(secret + struct.pack("<I", ordinal) + _DERIVATION_SUFFIX).digest()
    return page_secret, vector


def classify_first_block(block: bytes) -> str:
    if block.startswith(SQLITE_SIGNATURE):
        return "sqlite"
    if len(block) < 24:
        return "unrecognized"
    page_size = int.from_bytes(block[16:18], "big")
    page_size = 65536 if page_size == 1 else page_size
    power_of_two = page_size >= 512 and page_size <= 65536 and not page_size & (page_size - 1)
    if power_of_two and block[21:24] == bytes((0x40, 0x20, 0x20)):
        return "wecom-aes128"
    return "unrecognized"


def _decode_block(block: bytes, secret: bytes, ordinal: int) -> bytes:
    if len(block) != BLOCK_BYTES:
        raise ValueError(f"page {ordinal} is not {BLOCK_BYTES} bytes")
    page_secret, vector = _page_material(secret, ordinal)
    if ordinal != 1:
        return _aes_cbc(page_secret, vector, block, decrypt=True)
    clear_fragment = block[16:24]
    shuffled_ciphertext = block[8:16] + block[24:]
    tail = _aes_cbc(page_secret, vector, shuffled_ciphertext, decrypt=True)
    if tail[:8] != clear_fragment:
        raise ValueError("the supplied secret does not validate against page one")
    return SQLITE_SIGNATURE + tail


def encode_block_for_fixture(block: bytes, secret: bytes, ordinal: int) -> bytes:
    """Create fixture ciphertext; production commands never call this helper."""
    if len(block) != BLOCK_BYTES:
        raise ValueError("fixture page has the wrong size")
    page_secret, vector = _page_material(secret, ordinal)
    if ordinal != 1:
        return _aes_cbc(page_secret, vector, block, decrypt=False)
    if not block.startswith(SQLITE_SIGNATURE):
        raise ValueError("fixture page one must be a SQLite page")
    encrypted_tail = _aes_cbc(page_secret, vector, block[16:], decrypt=False)
    return bytes(8) + encrypted_tail[:8] + block[16:24] + encrypted_tail[8:]


def secret_matches(secret: bytes, encrypted_first_block: bytes) -> bool:
    if len(secret) != 16 or len(encrypted_first_block) < BLOCK_BYTES:
        return False
    try:
        candidate = _decode_block(encrypted_first_block[:BLOCK_BYTES], secret, 1)
    except (RuntimeError, ValueError):
        return False
    return candidate.startswith(SQLITE_SIGNATURE) and len(candidate) > 100 and candidate[100] in {2, 5, 10, 13}


def _committed_wal_pages(wal: bytes) -> list[tuple[int, int, bytes]]:
    if len(wal) < 32 or int.from_bytes(wal[0:4], "big") not in _WAL_MAGIC:
        return []
    page_size = int.from_bytes(wal[8:12], "big") or 65536
    if page_size != BLOCK_BYTES:
        return []
    transaction_salt = wal[16:24]
    stride = 24 + BLOCK_BYTES
    accepted: list[tuple[int, int, bytes]] = []
    cursor = 32
    while cursor + stride <= len(wal):
        frame_header = wal[cursor : cursor + 24]
        cursor += 24
        payload = wal[cursor : cursor + BLOCK_BYTES]
        cursor += BLOCK_BYTES
        page_number = int.from_bytes(frame_header[0:4], "big")
        database_pages = int.from_bytes(frame_header[4:8], "big")
        if page_number == 0:
            break
        if frame_header[8:16] == transaction_salt:
            accepted.append((page_number, database_pages, payload))
    final_commit_index = next(
        (index for index in range(len(accepted) - 1, -1, -1) if accepted[index][1] > 0),
        None,
    )
    return [] if final_commit_index is None else accepted[: final_commit_index + 1]


def decode_database_image(database: bytes, secret: bytes, wal: bytes | None = None) -> tuple[bytes, dict[str, int | str]]:
    if len(database) < BLOCK_BYTES or len(database) % BLOCK_BYTES:
        raise ValueError("database length is not a positive whole number of pages")
    flavor = classify_first_block(database[:BLOCK_BYTES])
    if flavor == "unrecognized":
        raise ValueError("database header is neither SQLite nor the supported WeCom format")
    pages = [database[offset : offset + BLOCK_BYTES] for offset in range(0, len(database), BLOCK_BYTES)]
    if flavor == "wecom-aes128":
        pages = [_decode_block(block, secret, index) for index, block in enumerate(pages, 1)]
    merged = 0
    committed_size: int | None = None
    for page_number, database_pages, encrypted in _committed_wal_pages(wal or b""):
        replacement = encrypted if flavor == "sqlite" else _decode_block(encrypted, secret, page_number)
        while len(pages) < page_number:
            pages.append(bytes(BLOCK_BYTES))
        pages[page_number - 1] = replacement
        merged += 1
        if database_pages:
            committed_size = database_pages
    if committed_size is not None:
        pages = pages[:committed_size]
    output = b"".join(pages)
    return output, {
        "source_format": flavor,
        "base_pages": len(database) // BLOCK_BYTES,
        "wal_pages_merged": merged,
        "plaintext_bytes": len(output),
    }


def _read_stable(path: Path) -> bytes:
    for _attempt in range(3):
        before = path.stat()
        payload = path.read_bytes()
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns):
            return payload
    raise RuntimeError(f"source changed repeatedly while being read: {path.name}")


def materialize_database(source: Path, target: Path, secret: bytes, *, merge_wal: bool = True) -> dict[str, int | str]:
    if target.exists():
        raise FileExistsError(f"output already exists: {target}")
    wal_path = source.with_name(source.name + "-wal")
    wal = _read_stable(wal_path) if merge_wal and wal_path.is_file() else None
    plaintext, report = decode_database_image(_read_stable(source), secret, wal)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(plaintext)
    target.chmod(0o600)
    return report
