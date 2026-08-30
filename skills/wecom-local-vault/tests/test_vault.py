from __future__ import annotations

import json
import os
import sqlite3
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from local_state import (  # noqa: E402
    DataHome,
    find_accounts,
    read_secret_record,
    store_verified_secret,
)
from mac_access import Approval, ensure_authorized  # noqa: E402
from page_store import (  # noqa: E402
    BLOCK_BYTES,
    SQLITE_SIGNATURE,
    classify_first_block,
    decode_database_image,
    encode_block_for_fixture,
    secret_matches,
)


def sqlite_first_block() -> bytes:
    block = bytearray(BLOCK_BYTES)
    block[:16] = SQLITE_SIGNATURE
    block[16:18] = BLOCK_BYTES.to_bytes(2, "big")
    block[21:24] = b"\x40\x20\x20"
    block[100] = 0x0D
    block[120:136] = b"fixture-payload!"
    return bytes(block)


def wal_image(*frames: tuple[int, int, int, bytes]) -> bytes:
    header = struct.pack(">8I", 0x377F0682, 3007000, BLOCK_BYTES, 0, 41, 73, 0, 0)
    body = bytearray(header)
    for page_number, commit_size, salt_selector, payload in frames:
        salt_a, salt_b = (41, 73) if salt_selector == 1 else (99, 101)
        body.extend(struct.pack(">6I", page_number, commit_size, salt_a, salt_b, 0, 0))
        body.extend(payload)
    return bytes(body)


class PageStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = bytes.fromhex("102132435465768798a9bacbdcedfe0f")
        self.first = sqlite_first_block()

    def test_encrypted_first_block_is_recognized_and_verified(self) -> None:
        encrypted = encode_block_for_fixture(self.first, self.secret, 1)
        self.assertEqual(classify_first_block(encrypted), "wecom-aes128")
        self.assertTrue(secret_matches(self.secret, encrypted))
        self.assertFalse(secret_matches(bytes(16), encrypted))

    def test_database_pages_round_trip(self) -> None:
        second = bytes((index * 29) & 0xFF for index in range(BLOCK_BYTES))
        encrypted = encode_block_for_fixture(self.first, self.secret, 1)
        encrypted += encode_block_for_fixture(second, self.secret, 2)
        plain, report = decode_database_image(encrypted, self.secret)
        self.assertEqual(plain, self.first + second)
        self.assertEqual(report["base_pages"], 2)

    def test_only_committed_current_salt_wal_frames_are_folded(self) -> None:
        original = bytes([3]) * BLOCK_BYTES
        committed = bytes([8]) * BLOCK_BYTES
        ignored_after_commit = bytes([9]) * BLOCK_BYTES
        encrypted = encode_block_for_fixture(self.first, self.secret, 1)
        encrypted += encode_block_for_fixture(original, self.secret, 2)
        wal = wal_image(
            (2, 0, 0, encode_block_for_fixture(bytes([7]) * BLOCK_BYTES, self.secret, 2)),
            (2, 2, 1, encode_block_for_fixture(committed, self.secret, 2)),
            (3, 0, 1, encode_block_for_fixture(ignored_after_commit, self.secret, 3)),
        )
        plain, report = decode_database_image(encrypted, self.secret, wal)
        self.assertEqual(plain, self.first + committed)
        self.assertEqual(report["wal_pages_merged"], 1)

    def test_malformed_database_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            decode_database_image(b"short", self.secret)


class LocalStateTests(unittest.TestCase):
    def test_discovers_only_complete_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            complete = root / "nested" / "account-a"
            incomplete = root / "account-b"
            complete.mkdir(parents=True)
            incomplete.mkdir()
            for name in ("message.db", "session.db", "user.db"):
                (complete / name).write_bytes(bytes(BLOCK_BYTES))
            (incomplete / "message.db").write_bytes(bytes(BLOCK_BYTES))
            self.assertEqual(find_accounts([root]), [complete.resolve()])

    def test_secret_is_private_validated_and_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            account = root / "account"
            account.mkdir()
            encrypted = encode_block_for_fixture(sqlite_first_block(), bytes(16), 1)
            for name in ("message.db", "session.db", "user.db"):
                (account / name).write_bytes(encrypted)
            home = DataHome(root / "vault")
            target = root / "vault" / "private" / "key.json"
            stored = store_verified_secret(home, account, bytes(16), target)
            self.assertEqual(stored, target)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            record = read_secret_record(home, target)
            self.assertEqual(record.secret, bytes(16))
            with self.assertRaises(FileExistsError):
                store_verified_secret(home, account, bytes(16), target)

    def test_world_readable_secret_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "key.json"
            path.write_text(json.dumps({"secret_hex": "00" * 16}), encoding="utf-8")
            path.chmod(0o644)
            with self.assertRaises(PermissionError):
                read_secret_record(DataHome(Path(tmp)), path)


class AuthorizationTests(unittest.TestCase):
    def test_attach_and_signed_copy_have_separate_explicit_gates(self) -> None:
        with self.assertRaises(PermissionError):
            ensure_authorized("attach", Approval())
        with self.assertRaises(PermissionError):
            ensure_authorized("spawn-signed-copy", Approval(attach=True))
        with self.assertRaises(PermissionError):
            ensure_authorized("sudo-memory-read", Approval(signed_copy=True))
        ensure_authorized("attach", Approval(attach=True))
        ensure_authorized("spawn-signed-copy", Approval(signed_copy=True))
        ensure_authorized("sudo-memory-read", Approval(sudo_memory_read=True))


class CliJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.snapshot = self.root / "snapshot"
        self.snapshot.mkdir()
        with sqlite3.connect(self.snapshot / "user.db") as db:
            db.execute("CREATE TABLE user_table(id INTEGER, name TEXT, real_name TEXT, account TEXT)")
            db.execute("INSERT INTO user_table VALUES(7, 'alice', 'Alice', 'alice@example')")
        with sqlite3.connect(self.snapshot / "session.db") as db:
            db.execute("CREATE TABLE conversation_table(id TEXT, name TEXT, roomname_remark TEXT, last_message_time INTEGER, last_message_id INTEGER)")
            db.execute("INSERT INTO conversation_table VALUES('R:demo', 'Demo room', '', 1700000000, 11)")
            db.execute("CREATE TABLE conversation_user_table(conversation_id TEXT, user_id INTEGER, nick_name TEXT)")
            db.execute("INSERT INTO conversation_user_table VALUES('R:demo', 7, 'Alice in room')")
        with sqlite3.connect(self.snapshot / "message.db") as db:
            db.execute("CREATE TABLE message_table(message_id INTEGER, server_id INTEGER, sequence INTEGER, sender_id INTEGER, conversation_id TEXT, content_type INTEGER, send_time INTEGER, content BLOB)")
            db.execute("INSERT INTO message_table VALUES(11, 22, 1, 7, 'R:demo', 2, 1700000000, ?)", ("roadmap ready".encode(),))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, *args: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "vault_cli.py"), *args],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_sessions_history_search_and_export(self) -> None:
        sessions = self.run_cli("sessions", "--snapshot", str(self.snapshot))
        self.assertEqual(sessions["sessions"][0]["display_name"], "Demo room")
        history = self.run_cli("history", "R:demo", "--snapshot", str(self.snapshot))
        self.assertEqual(history["messages"][0]["sender"], "Alice in room")
        found = self.run_cli("search", "roadmap", "--snapshot", str(self.snapshot))
        self.assertEqual(found["count"], 1)
        destination = self.root / "export.json"
        exported = self.run_cli(
            "export", "R:demo", "--snapshot", str(self.snapshot),
            "--format", "json", "--output", str(destination),
        )
        self.assertEqual(exported["messages"], 1)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_cli(
                "export", "R:demo", "--snapshot", str(self.snapshot),
                "--format", "json", "--output", str(destination),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
