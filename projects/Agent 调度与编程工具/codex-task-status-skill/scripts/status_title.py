#!/usr/bin/env python3
"""Normalize task-status titles and describe idempotent transitions."""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict


STATES = OrderedDict(
    [
        ("pending", ("📝", "待派发")),
        ("discussion", ("💬", "讨论中")),
        ("attention", ("🟡", "待确认")),
        ("running", ("🔵", "进行中")),
        ("waiting", ("⏳", "等待中")),
        ("paused", ("⏸️", "已暂停")),
        ("complete", ("✅", "已完成")),
    ]
)

ALIASES = {
    **{key: key for key in STATES},
    **{label: key for key, (_, label) in STATES.items()},
    **{f"{emoji} {label}": key for key, (emoji, label) in STATES.items()},
    **{f"{emoji}{label}": key for key, (emoji, label) in STATES.items()},
    "🌞": "running",
}

_PREFIX_PARTS = [
    rf"{re.escape(emoji)}\s*{re.escape(label)}" for emoji, label in STATES.values()
]
_PREFIX_PARTS.append(re.escape("🌞"))
_PREFIX_RE = re.compile(
    rf"^\s*(?:{'|'.join(_PREFIX_PARTS)})\s*(?:[｜|]\s*)?",
    flags=re.UNICODE,
)


def canonical_key(value: str) -> str:
    key = ALIASES.get(value.strip())
    if key is None:
        choices = ", ".join(STATES)
        raise ValueError(f"unknown status {value!r}; expected one of: {choices}")
    return key


def strip_prefixes(title: str) -> str:
    base = title
    while True:
        match = _PREFIX_RE.match(base)
        if match is None:
            break
        base = base[match.end() :]
    base = base.strip()
    if not base:
        raise ValueError("base title is empty after removing status prefixes")
    return base


def current_state(title: str) -> str | None:
    stripped = title.lstrip()
    for key, (emoji, label) in STATES.items():
        if re.match(rf"^{re.escape(emoji)}\s*{re.escape(label)}(?:\s*[｜|]|\s|$)", stripped):
            return key
    if stripped.startswith("🌞"):
        return "running"
    return None


def format_title(status: str, title: str) -> str:
    key = canonical_key(status)
    emoji, label = STATES[key]
    return f"{emoji} {label}｜{strip_prefixes(title)}"


def transition(status: str, title: str) -> dict[str, object]:
    key = canonical_key(status)
    previous = current_state(title)
    proposed = format_title(key, title)
    changed = title != proposed
    state_changed = previous != key
    sound_event = key if key in {"attention", "complete"} and state_changed else None
    return {
        "status": key,
        "previousStatus": previous,
        "baseTitle": strip_prefixes(title),
        "proposedTitle": proposed,
        "changed": changed,
        "stateChanged": state_changed,
        "soundEvent": sound_event,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("format", "transition"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--status", required=True)
        sub.add_argument("--title", required=True)

    inspect = subparsers.add_parser("inspect")
    inspect.add_argument("--title", required=True)

    args = parser.parse_args()
    try:
        if args.command == "format":
            print(format_title(args.status, args.title))
        elif args.command == "inspect":
            print(
                json.dumps(
                    {
                        "status": current_state(args.title),
                        "baseTitle": strip_prefixes(args.title),
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(json.dumps(transition(args.status, args.title), ensure_ascii=False))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
