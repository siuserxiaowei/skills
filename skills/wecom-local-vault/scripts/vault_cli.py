#!/usr/bin/env python3
"""Build and query private, read-only WeCom snapshots."""

from __future__ import annotations

import sqlite3
import re
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from local_state import (
    REQUIRED_DATABASES,
    account_label,
    active_home,
    database_files,
    describe_account,
    discover_accounts,
    newest_snapshot,
    read_secret_record,
    select_account,
)
from page_store import materialize_database


MESSAGE_SOURCES = ("message_table", "message_small_table", "kf_message_tableV1")
CONTENT_LABELS = {}
CONTENT_LABELS.update({0: "混合正文", 2: "纯文本", 4: "图片内容"})
CONTENT_LABELS.update({7: "音频", 15: "文件或图片", 38: "应用卡片"})
CONTENT_LABELS.update({40: "通话事件", 503: "状态变化", 1011: "会议事件"})


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _readonly(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _has_table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type=? AND name=?", ("table", name)).fetchone() is not None


def _columns(connection: sqlite3.Connection, name: str) -> set[str]:
    names: set[str] = set()
    cursor = connection.execute(f'PRAGMA table_info("{name}")')
    for entry in cursor:
        names.add(str(entry[1]))
    return names


def _fields(connection: sqlite3.Connection, table: str, candidates: Iterable[str]) -> list[str]:
    available = _columns(connection, table)
    return [field for field in candidates if field in available]


def _clean(text: str) -> str:
    filtered = "".join(char if char in "\n\t" or char.isprintable() else " " for char in text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", filtered)).strip()


def _varint(buffer: bytes, cursor: int) -> tuple[int, int]:
    total = 0
    for shift in range(0, 64, 7):
        if cursor >= len(buffer):
            break
        byte = buffer[cursor]
        cursor += 1
        total |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return total, cursor
    raise ValueError("truncated protobuf varint")


def _wire_strings(buffer: bytes, level: int = 0) -> list[str]:
    if not buffer or level > 4:
        return []
    cursor, found = 0, []
    try:
        while cursor < len(buffer):
            tag, cursor = _varint(buffer, cursor)
            wire = tag & 7
            if tag == 0:
                return []
            if wire == 0:
                _ignored, cursor = _varint(buffer, cursor)
            elif wire in {1, 5}:
                cursor += 8 if wire == 1 else 4
            elif wire == 2:
                width, cursor = _varint(buffer, cursor)
                piece, cursor = buffer[cursor : cursor + width], cursor + width
                if cursor > len(buffer):
                    return []
                try:
                    decoded = "" if b"\x00" in piece else _clean(piece.decode("utf-8"))
                except UnicodeDecodeError:
                    decoded = ""
                if len(decoded) > 1 and not re.fullmatch(r"[0-9a-fA-F]{32,}", decoded):
                    found.append(decoded)
                else:
                    found.extend(_wire_strings(piece, level + 1))
            else:
                return []
    except (IndexError, ValueError):
        return []
    return list(dict.fromkeys(value for value in found if value))


def readable_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _clean(value)
    payload = bytes(value)
    if not payload:
        return ""
    try:
        text = payload.decode("utf-8")
        controls = sum(byte < 32 and byte not in {9, 10, 13} for byte in payload)
        if controls / len(payload) <= 0.08:
            return _clean(text)
    except UnicodeDecodeError:
        pass
    fragments = _wire_strings(payload)
    return "\n".join(fragments[:12]) if fragments else f"[无法显示的二进制内容：{len(payload)} 字节]"


def _snapshot(value: str | None) -> Path:
    selected = Path(value).expanduser() if value else newest_snapshot(active_home())
    if not selected.is_dir():
        raise SystemExit(f"快照目录不存在: {selected}")
    return selected


def _time(value: str | None) -> int | None:
    if not value:
        return None
    normalized = value.strip().replace(" ", "T", 1)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SystemExit(f"时间必须采用 ISO 日期或日期时间格式: {value}") from exc
    return int(parsed.timestamp())


def _formatted_time(value: Any) -> str:
    try:
        stamp = int(value or 0)
    except (TypeError, ValueError):
        return ""
    stamp = stamp // 1000 if stamp > 20_000_000_000 else stamp
    if not stamp:
        return ""
    moment = datetime.fromtimestamp(stamp)
    return moment.isoformat(sep=" ", timespec="seconds")


def _people(snapshot: Path) -> dict[int, dict]:
    database, result = snapshot / "user.db", {}
    if not database.is_file():
        return result
    with _readonly(database) as connection:
        if _has_table(connection, "user_table"):
            fields = _fields(connection, "user_table", ("id", "name", "real_name", "account", "external_corp_name", "external_job"))
            if "id" in fields:
                for row in connection.execute(f'SELECT {",".join(fields)} FROM "user_table"'):
                    item = dict(row)
                    try:
                        identifier = int(item["id"])
                    except (TypeError, ValueError):
                        continue
                    label = str(identifier)
                    for candidate in (item.get("real_name"), item.get("name"), item.get("account")):
                        if candidate:
                            label = candidate
                            break
                    company = item.get("external_corp_name") or ""
                    item["display_name"] = f"{label} ({company})" if company and company not in str(label) else label
                    result[identifier] = item
        relation = "external_user_relation_v3"
        if _has_table(connection, relation):
            fields = _fields(connection, relation, ("user_id", "remarks", "real_remarks", "corp_remark"))
            if "user_id" in fields:
                for row in connection.execute(f'SELECT {",".join(fields)} FROM "{relation}"'):
                    item = dict(row)
                    try:
                        identifier = int(item["user_id"])
                    except (TypeError, ValueError):
                        continue
                    alias = next((item[field] for field in ("real_remarks", "remarks", "corp_remark") if item.get(field)), None)
                    if alias:
                        result.setdefault(identifier, {"id": identifier})["display_name"] = alias
    return result


def _conversations(snapshot: Path) -> dict[str, dict]:
    database, result = snapshot / "session.db", {}
    if not database.is_file():
        return result
    with _readonly(database) as connection:
        table = "conversation_table"
        if not _has_table(connection, table):
            return result
        fields = _fields(connection, table, ("id", "name", "roomname_remark", "last_message_time", "last_message_id"))
        if "id" not in fields:
            return result
        for row in connection.execute(f'SELECT {",".join(fields)} FROM "{table}"'):
            item, identifier = dict(row), str(row["id"] or "")
            if identifier:
                prefix = identifier[:1]
                if prefix == "R":
                    conversation_kind = "群聊"
                elif prefix == "S":
                    conversation_kind = "单聊"
                elif prefix == "M":
                    conversation_kind = "微信联系人"
                elif prefix == "O":
                    conversation_kind = "应用"
                elif prefix == "Y":
                    conversation_kind = "系统"
                else:
                    conversation_kind = "其他"
                record = {"conversation_id": identifier, "kind": conversation_kind}
                record["display_name"] = item.get("roomname_remark") or item.get("name") or identifier
                record["last_message_id"] = int(item.get("last_message_id") or 0)
                record["last_message_time"] = int(item.get("last_message_time") or 0)
                result[identifier] = record
    return result


def _aliases(snapshot: Path) -> dict[str, dict[int, str]]:
    database, result = snapshot / "session.db", {}
    if not database.is_file():
        return result
    with _readonly(database) as connection:
        table = "conversation_user_table"
        needed = {"conversation_id", "user_id", "nick_name"}
        if not _has_table(connection, table) or not needed.issubset(_columns(connection, table)):
            return result
        cursor = connection.execute('SELECT "nick_name","user_id","conversation_id" FROM "conversation_user_table"')
        for row in cursor:
            if row["nick_name"]:
                result.setdefault(str(row["conversation_id"]), {})[int(row["user_id"])] = str(row["nick_name"])
    return result


def _select_chat(value: str, sessions: dict[str, dict]) -> dict:
    if value in sessions:
        return sessions[value]
    needle = value.casefold()
    exact = [item for item in sessions.values() if str(item["display_name"]).casefold() == needle]
    fuzzy = [item for item in sessions.values() if needle in str(item["display_name"]).casefold() or needle in item["conversation_id"].casefold()]
    matches = exact if exact else fuzzy
    if len(matches) == 0:
        raise SystemExit(f"找不到会话: {value}")
    if len(matches) != 1:
        raise SystemExit("会话名称不唯一，请使用 conversation_id")
    return matches[0]


def _messages(snapshot, chat_id, start, end, keyword, limit):
    database = snapshot / "message.db"
    if not database.is_file():
        raise SystemExit(f"快照缺少 message.db: {snapshot}")
    users, sessions, aliases, result = _people(snapshot), _conversations(snapshot), _aliases(snapshot), []
    with _readonly(database) as connection:
        for table in MESSAGE_SOURCES:
            if not _has_table(connection, table):
                continue
            available = _columns(connection, table)
            if not {"conversation_id", "sender_id", "content_type", "send_time"}.issubset(available):
                continue
            desired = ("conversation_id", "send_time", "sender_id", "content_type", "content", "message_id", "sequence", "server_id", "local_extra_content", "extra_content", "flag")
            fields = [column for column in desired if column in available]
            conditions, parameters = [], []
            if chat_id:
                conditions.append('"conversation_id"=?')
                parameters.append(chat_id)
            maximum = connection.execute(f'SELECT MAX("send_time") FROM "{table}"').fetchone()
            scale = 1
            if maximum and int(maximum[0] or 0) > 20_000_000_000:
                scale = 1000
            if start is not None:
                conditions.append('"send_time">=?')
                parameters.append(start * scale)
            if end is not None:
                conditions.append('"send_time"<=?')
                parameters.append(end * scale)
            where = " WHERE " + " AND ".join(conditions) if conditions else ""
            parameters.append(min(max(limit * 50, 1000), 50000) if keyword else limit)
            projection = ",".join(fields)
            query = f'SELECT {projection} FROM "{table}"{where}'
            query += ' ORDER BY "send_time" DESC LIMIT ?'
            for row in connection.execute(query, parameters):
                item = dict(row)
                body = next((readable_content(item.get(name)) for name in ("content", "extra_content", "local_extra_content") if readable_content(item.get(name))), "")
                kind = int(item.get("content_type") or 0)
                body = body or f"[{CONTENT_LABELS.get(kind, f'未知类型 {kind}')}]"
                if keyword and keyword.casefold() not in body.casefold():
                    continue
                cid, sender = str(item.get("conversation_id") or ""), int(item.get("sender_id") or 0)
                record = {"conversation_id": cid, "sender_id": sender, "content": body}
                record["source_table"] = table
                record["sequence"] = int(item.get("sequence") or 0)
                record["server_id"] = int(item.get("server_id") or 0)
                record["message_id"] = int(item.get("message_id") or 0)
                record["conversation"] = sessions.get(cid, {}).get("display_name") or cid
                record["sender"] = aliases.get(cid, {}).get(sender) or users.get(sender, {}).get("display_name") or (str(sender) if sender else "系统")
                record["content_type"] = kind
                record["type_name"] = CONTENT_LABELS.get(kind, f"未知类型 {kind}")
                record["send_time"] = int(item.get("send_time") or 0)
                record["time"] = _formatted_time(item.get("send_time"))
                result.append(record)
    result.sort(key=lambda item: (item["send_time"], item["sequence"], item["message_id"]))
    return result[-limit:]


def _message_request(args: argparse.Namespace) -> tuple[dict | None, list[dict]]:
    snapshot, chat = _snapshot(args.snapshot), getattr(args, "chat", None)
    session = _select_chat(chat, _conversations(snapshot)) if chat else None
    rows = _messages(snapshot, session["conversation_id"] if session else None, _time(args.start), _time(args.end), getattr(args, "keyword", None), args.limit)
    return session, rows


def command_discover(args: argparse.Namespace) -> None:
    accounts = discover_accounts(args.data_dir)
    rows = [{"dataset_id": account_label(path), "core_databases": sorted(REQUIRED_DATABASES)} for path in accounts]
    if args.show_paths:
        for row, path in zip(rows, accounts):
            row["path"] = str(path)
    emit({"count": len(rows), "datasets": rows})


def command_status(args: argparse.Namespace) -> None:
    account = select_account(args.data_dir)
    result = describe_account(account)
    if args.show_paths:
        result["path"] = str(account)
    emit(result)


def command_decrypt(args: argparse.Namespace) -> None:
    home = active_home()
    record = read_secret_record(home, Path(args.key_file).expanduser() if args.key_file else None)
    if args.data_dir:
        account = select_account(args.data_dir)
    else:
        matches = [path for path in discover_accounts() if account_label(path) == record.account_label]
        account = matches[0] if len(matches) == 1 else select_account(None)
    if record.account_label and account_label(account) != record.account_label:
        raise SystemExit("密钥记录与所选数据集不匹配")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    target = home.snapshots / f"{stamp}-{account_label(account)}"
    target.mkdir(parents=True, exist_ok=False)
    target.chmod(0o700)
    reports = []
    for relative, source in database_files(account):
        try:
            reports.append({"database": str(relative), "status": "ok", **materialize_database(source, target / relative, record.secret, merge_wal=not args.no_wal)})
        except Exception as exc:
            reports.append({"database": str(relative), "status": "failed", "reason": str(exc)})
    manifest = {"schema": 2, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dataset_id": account_label(account), "contains_plaintext_wecom_data": True, "wal_merge_enabled": not args.no_wal, "results": reports}
    manifest_path = target / "manifest.json"
    descriptor = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        serialized = json.dumps(manifest, ensure_ascii=False, indent=2)
        handle.write(serialized + chr(10))
    failures = sum(row["status"] != "ok" for row in reports)
    emit({"snapshot": str(target), "decrypted": len(reports) - failures, "not_decrypted": failures, "manifest": str(manifest_path)})


def command_sessions(args: argparse.Namespace) -> None:
    rows = sorted(_conversations(_snapshot(args.snapshot)).values(), key=lambda item: item["last_message_time"], reverse=True)
    if args.query:
        needle = args.query.casefold()
        rows = [row for row in rows if needle in str(row["display_name"]).casefold() or needle in row["conversation_id"].casefold()]
    emit({"count": len(rows[: args.limit]), "sessions": rows[: args.limit]})


def command_contacts(args: argparse.Namespace) -> None:
    rows = list(_people(_snapshot(args.snapshot)).values())
    if args.query:
        needle = args.query.casefold()
        rows = [row for row in rows if needle in str(row.get("display_name", "")).casefold() or needle in str(row.get("account", "")).casefold()]
    rows.sort(key=lambda row: str(row.get("display_name", "")).casefold())
    emit({"count": len(rows[: args.limit]), "contacts": rows[: args.limit]})


def command_history(args: argparse.Namespace) -> None:
    session, rows = _message_request(args)
    emit({"session": session, "count": len(rows), "messages": rows})


def command_search(args: argparse.Namespace) -> None:
    _session, rows = _message_request(args)
    emit({"keyword": args.keyword, "count": len(rows), "messages": rows})


def command_export(args: argparse.Namespace) -> None:
    session, rows = _message_request(args)
    suffix = "json" if args.format == "json" else "md"
    if not session:
        raise SystemExit("export 缺少必需的会话参数")
    safe = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", str(session["display_name"])).strip(" .")[:100] or "wecom-export"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = Path(args.output).expanduser() if args.output else active_home().exports / f"{stamp}-{safe}.{suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise SystemExit(f"目标已存在，未执行写入: {destination}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        if args.format == "json":
            json.dump({"session": session, "count": len(rows), "messages": rows}, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        else:
            handle.write(f"# {session['display_name']}\n\n消息数：{len(rows)}\n\n")
            for row in rows:
                body = str(row["content"]).replace("\n", "\n  ")
                handle.write(f"- {row['time']} · {row['sender']}\n  {body}\n")
    emit({"output": str(destination), "messages": len(rows), "contains_plaintext_wecom_data": True})


def _message_options(parser: argparse.ArgumentParser, positional: bool) -> None:
    parser.add_argument("chat" if positional else "--chat", help="会话名称或 conversation_id")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--end")
    parser.add_argument("--snapshot")
    parser.add_argument("--start")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query a private WeCom snapshot")
    commands = parser.add_subparsers(dest="command", required=True)
    discover = commands.add_parser("discover"); discover.add_argument("--data-dir"); discover.add_argument("--show-paths", action="store_true"); discover.set_defaults(handler=command_discover)
    status = commands.add_parser("status"); status.add_argument("--data-dir"); status.add_argument("--show-paths", action="store_true"); status.set_defaults(handler=command_status)
    decrypt = commands.add_parser("decrypt"); decrypt.add_argument("--data-dir"); decrypt.add_argument("--key-file"); decrypt.add_argument("--no-wal", action="store_true"); decrypt.set_defaults(handler=command_decrypt)
    sessions = commands.add_parser("sessions"); sessions.add_argument("--snapshot"); sessions.add_argument("--query"); sessions.add_argument("--limit", type=int, default=50); sessions.set_defaults(handler=command_sessions)
    contacts = commands.add_parser("contacts"); contacts.add_argument("--snapshot"); contacts.add_argument("--query"); contacts.add_argument("--limit", type=int, default=100); contacts.set_defaults(handler=command_contacts)
    history = commands.add_parser("history"); _message_options(history, True); history.set_defaults(handler=command_history)
    search = commands.add_parser("search"); search.add_argument("keyword"); _message_options(search, False); search.set_defaults(handler=command_search)
    export = commands.add_parser("export"); _message_options(export, True); export.add_argument("--format", choices=("markdown", "json"), default="markdown"); export.add_argument("--output"); export.set_defaults(handler=command_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    limit = getattr(args, "limit", 1)
    if limit <= 0:
        raise SystemExit("--limit 必须大于 0")
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
