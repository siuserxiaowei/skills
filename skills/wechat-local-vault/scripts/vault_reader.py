#!/usr/bin/env python3
"""Read-only projections over a decrypted WeChat database snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterable, Iterator
from xml.etree import ElementTree

from vault_shared import VaultError, parse_clock, public_identifier, timestamp_text

try:
    import zstandard
except ImportError:  # optional; ordinary text remains available without it
    zstandard = None


KIND_CODES: dict[str, tuple[int, int | None]] = dict(
    (
        ("system", (10000, None)), ("file", (49, 6)), ("voice", (34, None)),
        ("text", (1, None)), ("call", (50, None)), ("location", (48, None)),
        ("video", (43, None)), ("image", (3, None)), ("link", (49, None)),
        ("sticker", (47, None)),
    )
)

KIND_NAMES = dict(
    (
        (10002, "撤回"), (50, "通话"), (3, "图片"), (43, "视频"),
        (1, "文本"), (49, "链接/文件"), (34, "语音"), (10000, "系统"),
        (48, "位置"), (42, "名片"), (47, "表情"),
    )
)

FAVORITE_FILTERS = {"text": 1, "image": 2, "article": 5, "card": 19, "video": 20}
FAVORITE_NAMES = {1: "文本", 2: "图片", 5: "文章", 19: "名片", 20: "视频号"}


def _readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise VaultError(f"数据库不存在：{path}")
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _quoted(identifier: str) -> str:
    return "[" + identifier.replace("]", "]]" ) + "]"


def _tables(connection: sqlite3.Connection) -> set[str]:
    statement = "SELECT name FROM sqlite_master WHERE type = 'table'"
    return {str(row[0]) for row in connection.execute(statement)}


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_quoted(table)})")}


def _first(columns: set[str], *possibilities: str) -> str | None:
    return next((name for name in possibilities if name in columns), None)


def _text(value: object, compression: object = None) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    raw = bytes(value)
    compressed = raw.startswith(b"\x28\xb5\x2f\xfd") or compression == 4
    if compressed:
        if zstandard is None:
            return "[压缩内容：缺少 zstandard，未展开]"
        try:
            raw = zstandard.ZstdDecompressor().decompress(raw, max_output_size=4_000_000)
        except zstandard.ZstdError:
            return "[压缩内容损坏]"
    return raw.decode("utf-8", errors="replace")


def _split_type(raw_value: object) -> tuple[int, int]:
    try:
        packed = int(raw_value or 0)
    except (TypeError, ValueError):
        return 0, 0
    return packed & 0xFFFFFFFF, (packed >> 32) & 0xFFFFFFFF


def _kind(raw_value: object) -> str:
    base, _ = _split_type(raw_value)
    return KIND_NAMES.get(base, f"类型 {raw_value}")


def _passes_kind(raw_value: object, requested: str | None) -> bool:
    if requested is None:
        return True
    actual_base, actual_subtype = _split_type(raw_value)
    wanted_base, wanted_subtype = KIND_CODES[requested]
    return actual_base == wanted_base and (wanted_subtype is None or actual_subtype == wanted_subtype)


@dataclass(frozen=True)
class Person:
    internal_id: int | None
    account: str
    display_name: str
    remark: str
    nickname: str
    alias: str
    description: str
    avatar: str

    @property
    def group(self) -> bool:
        return self.account.endswith("@chatroom")

    def expose(self, include_identifiers: bool = False) -> dict:
        result = {
            "display_name": self.display_name,
            "remark": self.remark,
            "nick_name": self.nickname,
            "alias": self.alias,
            "description": self.description,
            "avatar": self.avatar,
            "is_group": self.group,
            "is_subscription": self.account.startswith("gh_"),
        }
        visible = public_identifier(self.account, include_identifiers)
        if visible is not None:
            result["username"] = visible
        return result


class ContactBook:
    def __init__(self, people: Iterable[Person]):
        self.people = tuple(people)
        self.by_account = {person.account: person for person in self.people}
        self.by_number = {
            person.internal_id: person.account
            for person in self.people
            if person.internal_id is not None
        }

    @classmethod
    def open(cls, root: Path) -> "ContactBook":
        location = root / "contact" / "contact.db"
        if not location.is_file():
            return cls(())
        with _readonly(location) as connection:
            if "contact" not in _tables(connection):
                return cls(())
            records: list[Person] = []
            for raw in connection.execute("SELECT * FROM contact"):
                row = dict(raw)
                account = str(row.get("username") or row.get("userName") or "")
                if not account:
                    continue
                nickname = str(row.get("nick_name") or row.get("nickname") or "")
                remark = str(row.get("remark") or "")
                alias = str(row.get("alias") or "")
                display = remark or nickname or alias or account
                number = row.get("id")
                try:
                    contact_number = int(number) if number is not None else None
                except (TypeError, ValueError):
                    contact_number = None
                records.append(
                    Person(
                        internal_id=contact_number,
                        account=account,
                        display_name=display,
                        remark=remark,
                        nickname=nickname,
                        alias=alias,
                        description=str(row.get("description") or ""),
                        avatar=str(row.get("small_head_url") or row.get("big_head_url") or ""),
                    )
                )
        return cls(records)

    def display(self, account: str) -> str:
        person = self.by_account.get(account)
        return person.display_name if person else account

    def select(self, query: str, group_only: bool = False) -> Person:
        direct = self.by_account.get(query)
        if direct and (not group_only or direct.group):
            return direct
        needle = query.casefold()
        pool = [person for person in self.people if not group_only or person.group]
        exact = [person for person in pool if person.display_name.casefold() == needle]
        candidates = exact or [
            person
            for person in pool
            if any(
                needle in value.casefold()
                for value in (
                    person.display_name,
                    person.remark,
                    person.nickname,
                    person.alias,
                    person.account,
                )
            )
        ]
        if not candidates:
            label = "群聊" if group_only else "聊天对象"
            raise VaultError(f"找不到{label}：{query}")
        if len(candidates) > 1:
            names = "、".join(sorted({person.display_name for person in candidates})[:5])
            raise VaultError(f"名称不唯一，请改用更精确的名称：{names}")
        return candidates[0]

    def search(self, term: str | None, limit: int) -> list[Person]:
        selected = list(self.people)
        if term:
            needle = term.casefold()
            selected = [
                person
                for person in selected
                if any(
                    needle in value.casefold()
                    for value in (
                        person.account,
                        person.display_name,
                        person.remark,
                        person.nickname,
                        person.alias,
                    )
                )
            ]
        selected.sort(key=lambda person: (not person.group, person.display_name.casefold()))
        return selected[:limit]


class LocalArchive:
    """A query facade that never opens an SQLite database for writing."""

    def __init__(self, root: Path, include_identifiers: bool = False):
        self.root = root
        self.identifiers = include_identifiers
        self.contacts = ContactBook.open(root)

    def inventory(self) -> dict:
        expected = {
            "message/message_resource.db", "favorite/favorite.db",
            "contact/contact.db", "sns/sns.db", "session/session.db",
        }
        message_dir = self.root / "message"
        if message_dir.is_dir():
            expected.update(str(path.relative_to(self.root)) for path in message_dir.glob("message_*.db"))
        return {
            "decrypted_dir": str(self.root),
            "exists": self.root.is_dir(),
            "databases": [
                {"path": relative, "available": (self.root / relative).is_file()}
                for relative in sorted(expected)
            ],
        }

    def list_contacts(self, term: str | None, limit: int) -> dict:
        rows = [person.expose(self.identifiers) for person in self.contacts.search(term, limit)]
        return {"count": len(rows), "contacts": rows}

    def contact_detail(self, query: str) -> dict:
        return self.contacts.select(query).expose(self.identifiers)

    def session_cards(self, unread_only: bool, limit: int | None) -> list[dict]:
        database = self.root / "session" / "session.db"
        with _readonly(database) as connection:
            if "SessionTable" not in _tables(connection):
                raise VaultError("session.db 缺少 SessionTable")
            columns = _columns(connection, "SessionTable")
            required = {"username", "unread_count", "summary", "last_timestamp"}
            if not required.issubset(columns):
                raise VaultError("SessionTable 字段不完整")
            statement = "SELECT * FROM SessionTable"
            restrictions: list[str] = []
            if unread_only:
                restrictions.append("unread_count > 0")
            else:
                restrictions.append("last_timestamp > 0")
            statement += " WHERE " + " AND ".join(restrictions)
            statement += " ORDER BY last_timestamp DESC"
            parameters: tuple[int, ...] = ()
            if limit is not None:
                statement += " LIMIT ?"
                parameters = (limit,)
            result: list[dict] = []
            for record in connection.execute(statement, parameters):
                row = dict(record)
                account = str(row.get("username") or "")
                summary = _text(row.get("summary"), 4)
                if ":\n" in summary:
                    summary = summary.partition(":\n")[2]
                sender_value = row.get("last_msg_sender")
                sender_account = self.contacts.by_number.get(sender_value, str(sender_value or ""))
                sender = self.contacts.display(sender_account) if sender_account else str(row.get("last_sender_display_name") or "")
                epoch = int(row.get("last_timestamp") or 0)
                item = {
                    "chat": self.contacts.display(account),
                    "display_name": self.contacts.display(account),
                    "is_group": account.endswith("@chatroom"),
                    "unread": int(row.get("unread_count") or 0),
                    "last_message": summary,
                    "msg_type": _kind(row.get("last_msg_type")),
                    "sender": sender,
                    "timestamp": epoch,
                    "time": timestamp_text(epoch),
                }
                if self.identifiers:
                    item["username"] = account
                result.append(item)
        return result

    def group_members(self, query: str) -> dict:
        group = self.contacts.select(query, group_only=True)
        database = self.root / "contact" / "contact.db"
        members: list[dict] = []
        owner_name = ""
        with _readonly(database) as connection:
            available = _tables(connection)
            if {"contact", "chat_room", "chatroom_member"}.issubset(available):
                contact_columns = _columns(connection, "contact")
                account_column = _first(contact_columns, "username", "userName")
                if account_column:
                    room = connection.execute(
                        f"SELECT id FROM contact WHERE {_quoted(account_column)} = ?",
                        (group.account,),
                    ).fetchone()
                    if room:
                        room_number = int(room[0])
                        owner_row = connection.execute(
                            "SELECT owner FROM chat_room WHERE id = ?",
                            (room_number,),
                        ).fetchone()
                        owner_account = str(owner_row[0] or "") if owner_row else ""
                        owner_name = self.contacts.display(owner_account) if owner_account else ""
                        member_numbers = [
                            int(row[0])
                            for row in connection.execute(
                                "SELECT member_id FROM chatroom_member WHERE room_id = ?",
                                (room_number,),
                            )
                        ]
                        for number in member_numbers:
                            account = self.contacts.by_number.get(number, "")
                            person = self.contacts.by_account.get(account)
                            if not person:
                                continue
                            item = {
                                "display_name": person.display_name,
                                "remark": person.remark,
                                "nick_name": person.nickname,
                                "is_owner": account == owner_account,
                            }
                            if self.identifiers:
                                item["username"] = account
                            members.append(item)
        members.sort(key=lambda item: (not item["is_owner"], item["display_name"].casefold()))
        answer = {
            "group": group.display_name,
            "owner": owner_name,
            "member_count": len(members),
            "members": members,
        }
        if self.identifiers:
            answer["username"] = group.account
        return answer

    def _message_files(self) -> list[Path]:
        directory = self.root / "message"
        return sorted(directory.glob("message_*.db")) if directory.is_dir() else []

    @staticmethod
    def _message_table(account: str) -> str:
        digest = hashlib.md5(account.encode("utf-8"), usedforsecurity=False).hexdigest()
        return "Msg_" + digest

    @staticmethod
    def _sender_map(connection: sqlite3.Connection) -> dict[int, str]:
        if "Name2Id" not in _tables(connection):
            return {}
        columns = _columns(connection, "Name2Id")
        account_column = _first(columns, "user_name", "username", "userName")
        if not account_column:
            return {}
        mapping: dict[int, str] = {}
        query = f"SELECT rowid, {_quoted(account_column)} FROM Name2Id"
        for number, account in connection.execute(query):
            if account:
                mapping[int(number)] = str(account)
        return mapping

    @staticmethod
    def _table_account(table: str, contacts: ContactBook) -> str:
        if not table.startswith("Msg_"):
            return ""
        suffix = table[4:]
        for account in contacts.by_account:
            encoded = hashlib.md5(account.encode("utf-8"), usedforsecurity=False).hexdigest()
            if encoded == suffix:
                return account
        return ""

    @staticmethod
    def _projection(connection: sqlite3.Connection, table: str) -> dict[str, str | None]:
        columns = _columns(connection, table)
        return {
            "local_id": _first(columns, "local_id", "id"),
            "server_id": _first(columns, "server_id"),
            "raw_type": _first(columns, "local_type", "type"),
            "created": _first(columns, "create_time", "timestamp"),
            "sender_number": _first(columns, "real_sender_id", "sender_id"),
            "body": _first(columns, "message_content", "content"),
            "compressed_body": _first(columns, "compress_content", "WCDB_CT_message_content"),
            "compression": "WCDB_CT_message_content" if "WCDB_CT_message_content" in columns else None,
        }

    @staticmethod
    def _select_expression(column: str | None, alias: str, fallback: str = "NULL") -> str:
        source = _quoted(column) if column else fallback
        return f"{source} AS {_quoted(alias)}"

    def _scan_table(
        self,
        connection: sqlite3.Connection,
        table: str,
        person: Person,
        start: int | None,
        end: int | None,
        kind: str | None,
        keyword: str | None,
        ceiling: int,
    ) -> Iterator[dict]:
        projection = self._projection(connection, table)
        if projection["created"] is None:
            return
        fields = [
            self._select_expression(projection[name], name, "rowid" if name == "local_id" else "NULL")
            for name in projection
        ]
        conditions: list[str] = []
        values: list[object] = []
        created = _quoted(str(projection["created"]))
        if start is not None:
            conditions.append(f"{created} >= ?")
            values.append(start)
        if end is not None:
            conditions.append(f"{created} <= ?")
            values.append(end)
        if keyword and projection["body"]:
            conditions.append(f"{_quoted(str(projection['body']))} LIKE ?")
            values.append("%" + keyword + "%")
        query = f"SELECT {', '.join(fields)} FROM {_quoted(table)}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" ORDER BY {created} DESC LIMIT ?"
        values.append(ceiling)
        senders = self._sender_map(connection)
        for raw in connection.execute(query, values):
            row = dict(raw)
            if not _passes_kind(row.get("raw_type"), kind):
                continue
            body = _text(row.get("body"), row.get("compression"))
            if not body:
                body = _text(row.get("compressed_body"), row.get("compression"))
            prefixed_sender = ""
            if person.group and ":\n" in body:
                possible, delimiter, remainder = body.partition(":\n")
                if delimiter and len(possible) < 160:
                    prefixed_sender, body = possible, remainder
            sender_number = row.get("sender_number")
            try:
                sender_account = senders.get(int(sender_number), "")
            except (TypeError, ValueError):
                sender_account = ""
            sender_account = sender_account or prefixed_sender
            if person.group:
                sender = self.contacts.display(sender_account) if sender_account else ""
            elif str(sender_number) == "2":
                sender = "我"
            else:
                sender = person.display_name
            epoch = int(row.get("created") or 0)
            content = self._present_content(row.get("raw_type"), body)
            item = {
                "local_id": row.get("local_id"),
                "server_id": row.get("server_id"),
                "type": _kind(row.get("raw_type")),
                "sender": sender,
                "timestamp": epoch,
                "time": timestamp_text(epoch),
                "content": content,
            }
            if self.identifiers and sender_account:
                item["sender_username"] = sender_account
            yield item

    @staticmethod
    def _present_content(raw_type: object, body: str) -> str:
        base, subtype = _split_type(raw_type)
        fixed_labels = {
            50: "[通话]", 42: "[名片]", 3: "[图片]", 48: "[位置]",
            34: "[语音]", 47: "[表情]", 43: "[视频]",
        }
        if base in fixed_labels:
            return fixed_labels[base]
        if base != 49:
            return body.strip() or f"[{_kind(raw_type)}]"
        try:
            root = ElementTree.fromstring(body)
            subtype_from_xml = int(root.findtext(".//type") or 0)
            title = (root.findtext(".//title") or root.findtext(".//des") or "").strip()
        except (ElementTree.ParseError, ValueError):
            subtype_from_xml, title = 0, ""
        if subtype == 6 or subtype_from_xml == 6:
            return "[文件]" + (" " + title if title else "")
        if subtype_from_xml in {33, 36, 44}:
            return "[小程序]" + (" " + title if title else "")
        return "[链接]" + (" " + title if title else "")

    def messages(
        self,
        chat_query: str,
        *,
        start_text: str | None = None,
        end_text: str | None = None,
        limit: int = 50,
        offset: int = 0,
        kind: str | None = None,
        keyword: str | None = None,
    ) -> tuple[Person, list[dict]]:
        person = self.contacts.select(chat_query)
        target = self._message_table(person.account)
        gathered: list[dict] = []
        start = parse_clock(start_text)
        end = parse_clock(end_text, finish_day=True)
        for database in self._message_files():
            with _readonly(database) as connection:
                if target not in _tables(connection):
                    continue
                gathered.extend(
                    self._scan_table(
                        connection,
                        target,
                        person,
                        start,
                        end,
                        kind,
                        keyword,
                        limit + offset,
                    )
                )
        gathered.sort(key=lambda item: (item["timestamp"], str(item["local_id"])), reverse=True)
        window = gathered[offset : offset + limit]
        window.reverse()
        return person, window

    def global_search(
        self,
        keyword: str,
        *,
        chats: list[str] | None,
        start_text: str | None,
        end_text: str | None,
        limit: int,
        offset: int,
        kind: str | None,
    ) -> list[dict]:
        if chats:
            found: list[dict] = []
            for query in chats:
                person, messages = self.messages(
                    query,
                    start_text=start_text,
                    end_text=end_text,
                    limit=limit + offset,
                    kind=kind,
                    keyword=keyword,
                )
                for message in messages:
                    message["chat"] = person.display_name
                    if self.identifiers:
                        message["chat_username"] = person.account
                    found.append(message)
        else:
            found = []
            start = parse_clock(start_text)
            end = parse_clock(end_text, finish_day=True)
            for database in self._message_files():
                with _readonly(database) as connection:
                    for table in sorted(name for name in _tables(connection) if name.startswith("Msg_")):
                        account = self._table_account(table, self.contacts)
                        person = self.contacts.by_account.get(account)
                        if person is None:
                            person = Person(None, account, table, "", "", "", "", "")
                        for message in self._scan_table(
                            connection,
                            table,
                            person,
                            start,
                            end,
                            kind,
                            keyword,
                            limit + offset,
                        ):
                            if keyword.casefold() not in message["content"].casefold():
                                continue
                            message["chat"] = person.display_name
                            if self.identifiers and person.account:
                                message["chat_username"] = person.account
                            found.append(message)
        found.sort(key=lambda item: item["timestamp"], reverse=True)
        page = found[offset : offset + limit]
        page.reverse()
        return page

    def statistics(self, chat_query: str, start_text: str | None, end_text: str | None) -> dict:
        person, rows = self.messages(
            chat_query,
            start_text=start_text,
            end_text=end_text,
            limit=1_000_000,
        )
        types: dict[str, int] = {}
        senders: dict[str, int] = {}
        hours = {hour: 0 for hour in range(24)}
        for message in rows:
            types[message["type"]] = types.get(message["type"], 0) + 1
            sender = message["sender"] or "未知"
            senders[sender] = senders.get(sender, 0) + 1
            if message["timestamp"]:
                hours[datetime.fromtimestamp(message["timestamp"]).hour] += 1
        report = {
            "chat": person.display_name,
            "is_group": person.group,
            "total": len(rows),
            "type_breakdown": dict(sorted(types.items(), key=lambda pair: (-pair[1], pair[0]))),
            "top_senders": [
                {"name": name, "count": count}
                for name, count in sorted(senders.items(), key=lambda pair: (-pair[1], pair[0]))[:10]
            ],
            "hourly": hours,
        }
        if self.identifiers:
            report["username"] = person.account
        return report

    @staticmethod
    def _favorite_summary(raw: str, item_type: int) -> str:
        if not raw:
            return ""
        try:
            root = ElementTree.fromstring(raw)
        except ElementTree.ParseError:
            return "[收藏内容无法解析]"
        if item_type == 2:
            return "[图片收藏]"
        if item_type == 5:
            title = (root.findtext(".//pagetitle") or "").strip()
            detail = (root.findtext(".//pagedesc") or "").strip()
            return " - ".join(piece for piece in (title, detail) if piece)
        if item_type == 20:
            creator = (root.findtext(".//nickname") or "").strip()
            detail = (root.findtext(".//desc") or "").strip()
            return " ".join(piece for piece in (creator, detail) if piece) or "[视频号收藏]"
        return (root.findtext(".//desc") or "").strip() or "[收藏]"

    def favorites(self, limit: int, kind: str | None, query: str | None) -> dict:
        database = self.root / "favorite" / "favorite.db"
        with _readonly(database) as connection:
            if "fav_db_item" not in _tables(connection):
                raise VaultError("favorite.db 缺少 fav_db_item")
            restrictions: list[str] = []
            parameters: list[object] = []
            if kind:
                restrictions.append("type = ?")
                parameters.append(FAVORITE_FILTERS[kind])
            if query:
                restrictions.append("content LIKE ?")
                parameters.append("%" + query + "%")
            statement = "SELECT * FROM fav_db_item"
            if restrictions:
                statement += " WHERE " + " AND ".join(restrictions)
            statement += " ORDER BY update_time DESC LIMIT ?"
            parameters.append(limit)
            items = []
            for record in connection.execute(statement, parameters):
                row = dict(record)
                item_type = int(row.get("type") or 0)
                epoch = int(row.get("update_time") or 0)
                items.append(
                    {
                        "id": row.get("local_id"),
                        "type": FAVORITE_NAMES.get(item_type, f"类型 {item_type}"),
                        "time": timestamp_text(epoch, minute_precision=True),
                        "summary": self._favorite_summary(str(row.get("content") or ""), item_type),
                        "from": self.contacts.display(str(row.get("fromusr") or "")) if row.get("fromusr") else "",
                        "source_chat": self.contacts.display(str(row.get("realchatname") or "")) if row.get("realchatname") else "",
                    }
                )
        return {"count": len(items), "favorites": items}

    @staticmethod
    def _moment(raw_xml: str, fallback_account: str, timeline_id: object) -> dict:
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw_xml)
        try:
            root = ElementTree.fromstring(cleaned)
        except ElementTree.ParseError as exc:
            raise VaultError(f"朋友圈 XML 无法解析：{exc}") from exc
        timeline = root if root.tag == "TimelineObject" else root.find(".//TimelineObject") or root

        def value(path: str) -> str:
            node = timeline.find(path)
            return "" if node is None else (node.text or "").strip()

        account = value("username") or fallback_account
        created = value("createTime")
        epoch = int(created) if created.isdigit() else 0
        links = {
            node.text.strip()
            for node in timeline.findall(".//url") + timeline.findall("ContentObject/contentUrl")
            if node.text and node.text.strip()
        }
        media = []
        for node in timeline.findall(".//media"):
            media.append(
                {
                    "type": (node.findtext("type") or "").strip(),
                    "url": (node.findtext("url") or "").strip(),
                    "thumb": (node.findtext("thumb") or "").strip(),
                }
            )
        return {
            "tid": str(timeline_id),
            "account": account,
            "nickname": value("nickname"),
            "timestamp": epoch,
            "time": timestamp_text(epoch, minute_precision=True),
            "content": value("contentDesc"),
            "type": value("ContentObject/contentStyle") or value("ContentObject/contentSubStyle"),
            "media": media,
            "links": sorted(links),
        }

    def moments(
        self,
        *,
        name: str | None,
        usernames: list[str] | None,
        start_text: str | None,
        end_text: str | None,
        keyword: str | None,
        limit: int,
    ) -> dict:
        accounts = set(usernames or [])
        if name:
            needle = name.casefold()
            accounts.update(
                person.account
                for person in self.contacts.people
                if any(
                    needle in value.casefold()
                    for value in (person.display_name, person.remark, person.nickname, person.alias, person.account)
                )
            )
        if not accounts:
            raise VaultError("朋友圈查询需要 --name 或 --username")
        database = self.root / "sns" / "sns.db"
        start = parse_clock(start_text)
        end = parse_clock(end_text, finish_day=True)
        with _readonly(database) as connection:
            if "SnsTimeLine" not in _tables(connection):
                raise VaultError("sns.db 缺少 SnsTimeLine")
            placeholders = ",".join("?" for _ in accounts)
            statement = f"SELECT tid, user_name, content FROM SnsTimeLine WHERE user_name IN ({placeholders})"
            posts: list[dict] = []
            for timeline_id, account, raw_xml in connection.execute(statement, tuple(sorted(accounts))):
                if not raw_xml:
                    continue
                post = self._moment(str(raw_xml), str(account or ""), timeline_id)
                if start is not None and post["timestamp"] < start:
                    continue
                if end is not None and post["timestamp"] > end:
                    continue
                if keyword and keyword.casefold() not in json.dumps(post, ensure_ascii=False).casefold():
                    continue
                post["display_name"] = self.contacts.display(post.pop("account"))
                if self.identifiers:
                    post["username"] = str(account or "")
                posts.append(post)
        posts.sort(key=lambda post: post["timestamp"], reverse=True)
        posts = posts[:limit]
        return {"count": len(posts), "moments": posts}
