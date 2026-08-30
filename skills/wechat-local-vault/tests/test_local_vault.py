from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).parents[1]
SCRIPTS = SKILL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(f"wechat_local_vault_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_db(path: Path, statements: list[str], rows: list[tuple[str, tuple]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        for statement in statements:
            connection.execute(statement)
        for statement, values in rows:
            connection.execute(statement, values)


class FixtureVault:
    def __init__(self, root: Path):
        self.root = root
        self.group_id = "writers@chatroom"
        self.friend_id = "wxid_client_001"
        self.member_id = "wxid_member_001"
        self._build_contacts()
        self._build_sessions()
        self._build_messages()
        self._build_favorites()
        self._build_moments()

    def _build_contacts(self) -> None:
        schema = [
            "CREATE TABLE contact (id INTEGER PRIMARY KEY, username TEXT, nick_name TEXT, remark TEXT, alias TEXT, description TEXT, small_head_url TEXT)",
            "CREATE TABLE chat_room (id INTEGER PRIMARY KEY, owner TEXT)",
            "CREATE TABLE chatroom_member (room_id INTEGER, member_id INTEGER)",
        ]
        rows = [
            ("INSERT INTO contact VALUES (?, ?, ?, ?, ?, ?, ?)", (1, self.group_id, "写作群", "", "", "", "")),
            ("INSERT INTO contact VALUES (?, ?, ?, ?, ?, ?, ?)", (2, self.friend_id, "客户原名", "客户甲", "client-a", "重点客户", "")),
            ("INSERT INTO contact VALUES (?, ?, ?, ?, ?, ?, ?)", (3, self.member_id, "小林", "", "lin", "", "")),
            ("INSERT INTO chat_room VALUES (?, ?)", (1, self.member_id)),
            ("INSERT INTO chatroom_member VALUES (?, ?)", (1, 3)),
        ]
        create_db(self.root / "contact/contact.db", schema, rows)

    def _build_sessions(self) -> None:
        create_db(
            self.root / "session/session.db",
            [
                "CREATE TABLE SessionTable (username TEXT, unread_count INTEGER, summary TEXT, last_timestamp INTEGER, last_msg_type INTEGER, last_msg_sender INTEGER, last_sender_display_name TEXT)"
            ],
            [
                (
                    "INSERT INTO SessionTable VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.group_id, 2, "项目进展", 1_700_000_100, 1, 3, "小林"),
                ),
                (
                    "INSERT INTO SessionTable VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (self.friend_id, 0, "收到", 1_700_000_000, 1, 2, "客户甲"),
                ),
            ],
        )

    def _build_messages(self) -> None:
        table = "Msg_" + hashlib.md5(self.group_id.encode()).hexdigest()
        private_table = "Msg_" + hashlib.md5(self.friend_id.encode()).hexdigest()
        create_db(
            self.root / "message/message_0.db",
            [
                "CREATE TABLE Name2Id (user_name TEXT)",
                f"CREATE TABLE [{table}] (local_id INTEGER, server_id INTEGER, local_type INTEGER, create_time INTEGER, real_sender_id INTEGER, message_content BLOB, compress_content BLOB)",
                f"CREATE TABLE [{private_table}] (local_id INTEGER, server_id INTEGER, local_type INTEGER, create_time INTEGER, real_sender_id INTEGER, message_content BLOB, compress_content BLOB)",
            ],
            [
                ("INSERT INTO Name2Id VALUES (?)", (self.member_id,)),
                (
                    f"INSERT INTO [{table}] VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (10, 20, 1, 1_700_000_010, 1, "本周项目进入验收", None),
                ),
                (
                    f"INSERT INTO [{table}] VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (11, 21, 3, 1_700_000_020, 1, "", None),
                ),
                (
                    f"INSERT INTO [{private_table}] VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (12, 22, 1, 1_700_000_030, 2, "下周再联系", None),
                ),
            ],
        )

    def _build_favorites(self) -> None:
        xml = "<favitem><weburlitem><pagetitle>研究文章</pagetitle><pagedesc>离线收藏</pagedesc></weburlitem></favitem>"
        create_db(
            self.root / "favorite/favorite.db",
            [
                "CREATE TABLE fav_db_item (local_id INTEGER, type INTEGER, update_time INTEGER, content TEXT, fromusr TEXT, realchatname TEXT)"
            ],
            [
                (
                    "INSERT INTO fav_db_item VALUES (?, ?, ?, ?, ?, ?)",
                    (7, 5, 1_700_000_000, xml, self.member_id, self.group_id),
                )
            ],
        )

    def _build_moments(self) -> None:
        xml = (
            "<TimelineObject><username>wxid_member_001</username><nickname>小林</nickname>"
            "<createTime>1700000000</createTime><contentDesc>离线研究记录</contentDesc>"
            "<ContentObject><contentStyle>1</contentStyle><contentUrl>https://example.test/post</contentUrl></ContentObject>"
            "</TimelineObject>"
        )
        create_db(
            self.root / "sns/sns.db",
            ["CREATE TABLE SnsTimeLine (tid TEXT, user_name TEXT, content TEXT)"],
            [("INSERT INTO SnsTimeLine VALUES (?, ?, ?)", ("99", self.member_id, xml))],
        )


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.fixture = FixtureVault(base / "decrypted")
        self.env = os.environ.copy()
        self.env.update(
            {
                "WECHAT_VAULT_CONFIG": str(base / "settings.json"),
                "WECHAT_VAULT_KEYS": str(base / "keys.json"),
                "WECHAT_VAULT_HOME": str(base / "private"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
        )

    def run_cli(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "vault_cli.py"),
                "--decrypted-dir",
                str(self.fixture.root),
                *arguments,
            ],
            capture_output=True,
            text=True,
            env=self.env,
        )
        self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
        return result

    def json_cli(self, *arguments: str) -> dict:
        return json.loads(self.run_cli(*arguments, "--format", "json").stdout)

    def test_inventory_contacts_sessions_and_unread(self) -> None:
        inventory = self.json_cli("status")
        self.assertTrue(inventory["exists"])
        self.assertGreaterEqual(sum(item["available"] for item in inventory["databases"]), 5)

        contacts = self.json_cli("contacts", "--query", "客户")
        self.assertEqual("客户甲", contacts["contacts"][0]["display_name"])
        self.assertNotIn("wxid_client_001", json.dumps(contacts, ensure_ascii=False))

        sessions = self.json_cli("sessions", "--limit", "5")
        self.assertEqual("写作群", sessions[0]["display_name"])
        unread = self.json_cli("unread")
        self.assertEqual(1, len(unread))

    def test_history_search_stats_members_and_type_filter(self) -> None:
        history = self.json_cli("history", "写作群", "--limit", "20")
        self.assertEqual(2, history["count"])
        self.assertEqual("小林", history["messages"][0]["sender"])

        images = self.json_cli("history", "写作群", "--type", "image")
        self.assertEqual("图片", images["messages"][0]["type"])
        search = self.json_cli("search", "验收")
        self.assertEqual(1, search["count"])
        self.assertEqual("写作群", search["messages"][0]["chat"])

        stats = self.json_cli("stats", "写作群")
        self.assertEqual(2, stats["total"])
        self.assertEqual("小林", stats["top_senders"][0]["name"])
        members = self.json_cli("members", "写作群")
        self.assertEqual("小林", members["members"][0]["display_name"])

    def test_favorites_moments_and_digest_bundle(self) -> None:
        favorites = self.json_cli("favorites", "--type", "article", "--query", "研究")
        self.assertEqual("研究文章 - 离线收藏", favorites["favorites"][0]["summary"])
        moments = self.json_cli("moments", "--name", "小林", "--keyword", "研究")
        self.assertEqual("离线研究记录", moments["moments"][0]["content"])

        data_root = Path(self.temp.name) / "digests"
        bundle = self.json_cli("digest-source", "写作群", "--data-root", str(data_root))
        self.assertTrue(Path(bundle["source_json"]).exists())
        self.assertTrue(Path(bundle["source_markdown"]).exists())
        self.assertFalse((Path(bundle["folder"]) / "history.json").exists())

    def test_export_refuses_to_overwrite_and_queries_are_read_only(self) -> None:
        database = self.fixture.root / "message/message_0.db"
        before = (database.stat().st_mtime_ns, hashlib.sha256(database.read_bytes()).hexdigest())
        target = Path(self.temp.name) / "report.md"
        first = self.run_cli("export", "写作群", "--output", str(target))
        self.assertIn(str(target), first.stdout)
        second = self.run_cli("export", "写作群", "--output", str(target), expected=2)
        self.assertIn("已存在", second.stderr)
        after = (database.stat().st_mtime_ns, hashlib.sha256(database.read_bytes()).hexdigest())
        self.assertEqual(before, after)

    def test_unknown_or_ambiguous_chat_fails_closed(self) -> None:
        missing = self.run_cli("history", "不存在", expected=2)
        self.assertIn("找不到", missing.stderr)


class CryptoAndCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.crypto = load_script("vault_crypto.py")
        cls.capture = load_script("key_capture.py")

    def test_page_unlock_round_trip(self) -> None:
        try:
            from Crypto.Cipher import AES
        except ImportError as exc:  # pragma: no cover - dependency check belongs to the CLI
            self.skipTest(str(exc))
        layout = self.crypto.CipherPageLayout()
        key = bytes(range(32))
        plain = bytearray(layout.bytes_per_page)
        plain[:16] = b"SQLite format 3\x00"
        plain[16:18] = layout.bytes_per_page.to_bytes(2, "big")
        plain[18:24] = bytes((1, 1, layout.trailer_bytes, 64, 32, 32))
        plain[24 : layout.payload_end] = bytes((index % 251 for index in range(layout.payload_end - 24)))
        iv = bytes(range(16, 32))
        encrypted = bytearray(layout.bytes_per_page)
        encrypted[:16] = b"0123456789abcdef"
        encrypted[16 : layout.payload_end] = AES.new(key, AES.MODE_CBC, iv).encrypt(bytes(plain[16 : layout.payload_end]))
        encrypted[layout.payload_end : layout.payload_end + 16] = iv
        unlocked = self.crypto.unlock_page(bytes(encrypted), key, 0, layout)
        self.assertEqual(plain[: layout.payload_end], unlocked[: layout.payload_end])
        self.assertEqual(bytes(layout.trailer_bytes), unlocked[layout.payload_end :])

    def test_capture_log_accepts_only_redacted_key_material(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "capture.jsonl"
            log.write_text(
                "{\"event\":\"derived\",\"salt_hex\":\"0011\",\"key_hex\":\""
                + "ab" * 32
                + "\"}\n{bad json}\n{\"event\":\"derived\",\"password\":\"secret\"}\n",
                encoding="utf-8",
            )
            rows = self.capture.read_capture_events(log)
        self.assertEqual(1, len(rows))
        self.assertNotIn("password", rows[0])


class CompatibilityTests(unittest.TestCase):
    def test_all_historical_entry_points_have_help(self) -> None:
        commands = {
            "decrypt_all_dbs.py": ("--help",),
            "export_chat.py": ("--help",),
            "extract_keys.py": ("--help",),
            "list_contacts.py": ("--help",),
            "search_sns.py": ("--help",),
            "vault_cli.py": ("--help",),
            "wechat_digest.py": ("--help",),
        }
        for filename, arguments in commands.items():
            with self.subTest(filename=filename):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / filename), *arguments],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
