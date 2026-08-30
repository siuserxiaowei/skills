#!/usr/bin/env python3
"""Command line interface for a private, decrypted WeChat snapshot."""

from __future__ import annotations

import json
import hashlib
import argparse
from pathlib import Path
import sqlite3
import sys
from datetime import datetime

from vault_reader import FAVORITE_FILTERS, KIND_CODES, LocalArchive
from vault_shared import (
    VaultError,
    VaultLocations,
    filename_fragment,
    read_json,
    write_new_private_text,
    write_private_json,
)


def _emit(payload, output_format: str, text: str) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2) if output_format == "json" else text)


def _cards_text(cards: list[dict], title: str) -> str:
    if not cards:
        return "没有找到会话"
    lines = [f"{title}：{len(cards)} 个", ""]
    for card in cards:
        unread = f"，未读 {card['unread']}" if card["unread"] else ""
        lines.append(f"[{card['time']}] {card['chat']}{unread}")
        speaker = f"{card['sender']}: " if card["sender"] and card["is_group"] else ""
        lines.append(f"  {speaker}{card['last_message']}")
    return "\n".join(lines)


def _messages_text(messages: list[dict], show_chat: bool = False) -> str:
    if not messages:
        return "没有找到消息"
    lines = []
    for message in messages:
        chat = f"[{message.get('chat')}] " if show_chat and message.get("chat") else ""
        speaker = f"{message['sender']}: " if message.get("sender") else ""
        lines.append(f"[{message['time']}] {chat}{speaker}{message['content']}")
    return "\n".join(lines)


def _contacts_text(payload: dict) -> str:
    if not payload["contacts"]:
        return "没有找到联系人"
    lines = []
    for number, person in enumerate(payload["contacts"], 1):
        category = "群聊" if person["is_group"] else "联系人"
        lines.append(f"{number}. [{category}] {person['display_name']}")
        if person["remark"]:
            lines.append(f"   备注：{person['remark']}")
        if "username" in person:
            lines.append(f"   ID：{person['username']}")
    return "\n".join(lines)


def _stats_text(payload: dict) -> str:
    lines = [f"{payload['chat']}：{payload['total']} 条消息", "消息类型："]
    lines.extend(f"  {name}: {count}" for name, count in payload["type_breakdown"].items())
    lines.append("发言排行：")
    lines.extend(f"  {item['name']}: {item['count']}" for item in payload["top_senders"])
    return "\n".join(lines)


def _favorite_text(payload: dict) -> str:
    return "\n\n".join(
        f"[{item['time']}] [{item['type']}] {item['summary']}" for item in payload["favorites"]
    ) or "没有找到收藏"


def _moments_text(payload: dict) -> str:
    sections = []
    for post in payload["moments"]:
        lines = [f"[{post['time']}] {post['display_name']}", post["content"] or "[无文字内容]"]
        lines.extend(f"  link: {link}" for link in post["links"][:5])
        sections.append("\n".join(lines))
    return "\n\n".join(sections) or "没有找到匹配朋友圈"


def _archive(args: argparse.Namespace) -> LocalArchive:
    locations = VaultLocations.current()
    return LocalArchive(locations.decrypted_root(args.decrypted_dir), args.show_identifiers)


def do_status(args: argparse.Namespace) -> None:
    payload = _archive(args).inventory()
    lines = [f"明文快照：{payload['decrypted_dir']}", f"状态：{'可用' if payload['exists'] else '不存在'}"]
    lines.extend(f"  {'OK' if item['available'] else '--'} {item['path']}" for item in payload["databases"])
    _emit(payload, args.format, "\n".join(lines))


def do_sessions(args: argparse.Namespace) -> None:
    rows = _archive(args).session_cards(False, args.limit)
    _emit(rows, args.format, _cards_text(rows, "最近会话"))


def do_unread(args: argparse.Namespace) -> None:
    rows = _archive(args).session_cards(True, args.limit)
    _emit(rows, args.format, _cards_text(rows, "未读会话"))


def do_new_messages(args: argparse.Namespace) -> None:
    locations = VaultLocations.current()
    internal = LocalArchive(locations.decrypted_root(args.decrypted_dir), True).session_cards(False, None)
    state_file = locations.state / "session-cursors.json"
    previous = read_json(state_file, {})
    first = not bool(previous)
    changed = [row for row in internal if row["timestamp"] > int(previous.get(row["username"], 0))]
    write_private_json(state_file, {row["username"]: row["timestamp"] for row in internal})
    if not args.show_identifiers:
        for row in changed:
            row.pop("username", None)
    payload = {"first_call": first, "new_count": len(changed), "messages": changed}
    _emit(payload, args.format, _cards_text(changed, "新增会话"))


def do_contacts(args: argparse.Namespace) -> None:
    archive = _archive(args)
    if args.detail:
        payload = archive.contact_detail(args.detail)
        text = "\n".join(f"{key}: {value}" for key, value in payload.items() if value not in ("", False))
    else:
        payload = archive.list_contacts(args.query, args.limit)
        text = _contacts_text(payload)
    _emit(payload, args.format, text)


def do_members(args: argparse.Namespace) -> None:
    payload = _archive(args).group_members(args.group)
    lines = [f"{payload['group']}：{payload['member_count']} 位成员"]
    lines.extend(f"{index}. {item['display_name']}" for index, item in enumerate(payload["members"], 1))
    _emit(payload, args.format, "\n".join(lines))


def do_history(args: argparse.Namespace) -> None:
    archive = _archive(args)
    person, rows = archive.messages(
        args.chat,
        start_text=args.start_time,
        end_text=args.end_time,
        limit=args.limit,
        offset=args.offset,
        kind=args.type,
    )
    payload = {"chat": person.display_name, "count": len(rows), "messages": rows}
    if args.show_identifiers:
        payload["username"] = person.account
    _emit(payload, args.format, _messages_text(rows))


def do_search(args: argparse.Namespace) -> None:
    rows = _archive(args).global_search(
        args.keyword,
        chats=args.chat,
        start_text=args.start_time,
        end_text=args.end_time,
        limit=args.limit,
        offset=args.offset,
        kind=args.type,
    )
    payload = {"keyword": args.keyword, "count": len(rows), "messages": rows}
    _emit(payload, args.format, _messages_text(rows, show_chat=True))


def do_stats(args: argparse.Namespace) -> None:
    payload = _archive(args).statistics(args.chat, args.start_time, args.end_time)
    _emit(payload, args.format, _stats_text(payload))


def _export_body(person, rows: list[dict], output_format: str, start: str, end: str) -> str:
    if output_format == "txt":
        return _messages_text(rows)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_total = len(rows)
    lines = [
        f"# 聊天记录：{person.display_name}", "",
        f"- 时间范围：{start or '最早'} 至 {end or '最新'}",
        f"- 生成于：{generated}", f"- 共计：{message_total} 条", "",
        "## 按时间排列", "",
    ]
    lines.extend(f"- {row['time']} [{row['type']}] {row['sender']}: {row['content']}" for row in rows)
    return "\n".join(lines)


def do_export(args: argparse.Namespace) -> None:
    archive = _archive(args)
    person, rows = archive.messages(
        args.chat,
        start_text=args.start_time,
        end_text=args.end_time,
        limit=args.limit,
        kind=args.type,
    )
    suffix = "md" if args.format == "markdown" else "txt"
    locations = VaultLocations.current()
    if args.output:
        target = Path(args.output).expanduser()
    else:
        root = locations.export_root(args.exports_dir) / "conversations"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = root / f"{stamp}-{filename_fragment(person.display_name)}.{suffix}"
    write_new_private_text(target, _export_body(person, rows, args.format, args.start_time, args.end_time))
    print(target)
    print(f"Exported {len(rows)} messages.")


def do_digest(args: argparse.Namespace) -> None:
    archive = _archive(args)
    group = archive.contacts.select(args.group, group_only=True)
    locations = VaultLocations.current()
    root = Path(args.data_root).expanduser() if args.data_root else locations.export_root() / "digests"
    opaque = hashlib.sha256(group.account.encode()).hexdigest()[:12]
    folder = root / f"{opaque}-{filename_fragment(group.display_name)}"
    start = args.start
    if args.since_last:
        history = read_json(folder / "history.json", {})
        last = history.get("last_digest", {}).get("last_message_timestamp") if isinstance(history, dict) else None
        if last:
            start = datetime.fromtimestamp(int(last)).strftime("%Y-%m-%d %H:%M:%S")
    _, rows = archive.messages(group.account, start_text=start, end_text=args.end, limit=args.limit)
    usable = [row for row in rows if row["type"] != "系统"]
    counts: dict[str, int] = {}
    for row in usable:
        counts[row["sender"] or "未知"] = counts.get(row["sender"] or "未知", 0) + 1
    ordered_speakers = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ranking = [{"count": total, "name": speaker} for speaker, total in ordered_speakers]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    json_path = folder / "sources" / f"{stamp}.json"
    md_path = folder / "sources" / f"{stamp}.md"
    payload = {
        "group": {"name": group.display_name},
        "range": {"start": start or "", "end": args.end or "", "since_last": args.since_last},
        "stats": {"message_count": len(usable), "leaderboard": ranking, "last_message_timestamp": max((r["timestamp"] for r in rows), default=0)},
        "messages": rows,
        "image_policy": "No image claim is allowed unless a user-supplied description exists.",
    }
    lines = [f"# {group.display_name} 摘要素材", "", f"可用消息：{len(usable)}", "", "## 消息"]
    lines.extend(f"- {row['time']} | {row['sender']} | {row['type']} | {row['content']}" for row in rows)
    write_new_private_text(json_path, json.dumps(payload, ensure_ascii=False, indent=2))
    write_new_private_text(md_path, "\n".join(lines))
    result = {"folder": str(folder), "source_json": str(json_path), "source_markdown": str(md_path), "message_count": len(rows)}
    _emit(result, args.format, "\n".join(f"{key}: {value}" for key, value in result.items()))


def do_favorites(args: argparse.Namespace) -> None:
    payload = _archive(args).favorites(args.limit, args.type, args.query)
    _emit(payload, args.format, _favorite_text(payload))


def do_moments(args: argparse.Namespace) -> None:
    payload = _archive(args).moments(
        name=args.name, usernames=args.username, start_text=args.start, end_text=args.end,
        keyword=args.keyword, limit=args.limit,
    )
    _emit(payload, args.format, _moments_text(payload))


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query a decrypted local WeChat snapshot without modifying it.")
    parser.add_argument("--decrypted-dir")
    parser.add_argument("--show-identifiers", action="store_true", help="include wxid/userName fields in output")
    subcommands = parser.add_subparsers(dest="command", required=True)

    def format_option(command, default="json"):
        command.add_argument("--format", choices=("json", "text"), default=default)

    command = subcommands.add_parser("status", help="查看快照中的数据库")
    format_option(command, "text"); command.set_defaults(handler=do_status)
    for name, title, handler, default_limit in (
        ("sessions", "最近会话", do_sessions, 20), ("unread", "未读会话", do_unread, 50),
    ):
        command = subcommands.add_parser(name, help=title); command.add_argument("--limit", type=int, default=default_limit)
        format_option(command); command.set_defaults(handler=handler)
    command = subcommands.add_parser("new-messages", help="比较上一次本地检查后的会话变化")
    format_option(command); command.set_defaults(handler=do_new_messages)
    command = subcommands.add_parser("contacts", help="搜索联系人和群聊")
    command.add_argument("--query"); command.add_argument("--detail"); command.add_argument("--limit", type=int, default=50)
    format_option(command); command.set_defaults(handler=do_contacts)
    command = subcommands.add_parser("members", help="列出群成员"); command.add_argument("group")
    format_option(command); command.set_defaults(handler=do_members)
    command = subcommands.add_parser("history", help="读取一个会话的历史")
    command.add_argument("chat"); command.add_argument("--limit", type=int, default=50); command.add_argument("--offset", type=int, default=0)
    command.add_argument("--start-time", default=""); command.add_argument("--end-time", default="")
    command.add_argument("--type", choices=sorted(KIND_CODES)); command.add_argument("--media", action="store_true")
    format_option(command); command.set_defaults(handler=do_history)
    command = subcommands.add_parser("search", help="搜索消息"); command.add_argument("keyword"); command.add_argument("--chat", action="append")
    command.add_argument("--limit", type=int, default=50); command.add_argument("--offset", type=int, default=0)
    command.add_argument("--start-time", default=""); command.add_argument("--end-time", default=""); command.add_argument("--type", choices=sorted(KIND_CODES))
    format_option(command); command.set_defaults(handler=do_search)
    command = subcommands.add_parser("stats", help="统计一个会话"); command.add_argument("chat")
    command.add_argument("--start-time", default=""); command.add_argument("--end-time", default="")
    format_option(command); command.set_defaults(handler=do_stats)
    command = subcommands.add_parser("export", help="导出聊天记录"); command.add_argument("chat")
    command.add_argument("--format", choices=("markdown", "txt"), default="markdown"); command.add_argument("--output"); command.add_argument("--exports-dir")
    command.add_argument("--start-time", default=""); command.add_argument("--end-time", default=""); command.add_argument("--limit", type=int, default=500)
    command.add_argument("--type", choices=sorted(KIND_CODES)); command.add_argument("--media", action="store_true"); command.set_defaults(handler=do_export)
    command = subcommands.add_parser("digest-source", help="生成群聊摘要素材包"); command.add_argument("group")
    command.add_argument("--start"); command.add_argument("--end"); command.add_argument("--since-last", action="store_true"); command.add_argument("--data-root")
    command.add_argument("--limit", type=int, default=5000); command.add_argument("--media", action="store_true")
    format_option(command); command.set_defaults(handler=do_digest)
    command = subcommands.add_parser("favorites", help="读取收藏夹"); command.add_argument("--limit", type=int, default=20)
    command.add_argument("--type", choices=sorted(FAVORITE_FILTERS)); command.add_argument("--query")
    format_option(command); command.set_defaults(handler=do_favorites)
    command = subcommands.add_parser("moments", help="读取朋友圈"); command.add_argument("--name"); command.add_argument("--username", action="append")
    command.add_argument("--start"); command.add_argument("--end"); command.add_argument("--keyword"); command.add_argument("--limit", type=int, default=50)
    format_option(command); command.set_defaults(handler=do_moments)
    return parser


def main(arguments: list[str] | None = None) -> int:
    options = create_parser().parse_args(arguments)
    try:
        options.handler(options)
        return 0
    except (VaultError, sqlite3.Error, OSError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
