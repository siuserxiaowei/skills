#!/usr/bin/env python3
"""Run deterministic task-status acceptance checks."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import status_title


SCRIPT_DIR = Path(__file__).resolve().parent


def check_titles() -> None:
    expected = {
        "pending": "📝 待派发｜原任务",
        "discussion": "💬 讨论中｜原任务",
        "attention": "🟡 待确认｜原任务",
        "running": "🔵 进行中｜原任务",
        "waiting": "⏳ 等待中｜原任务",
        "paused": "⏸️ 已暂停｜原任务",
        "complete": "✅ 已完成｜原任务",
    }
    for state, title in expected.items():
        assert status_title.format_title(state, "原任务") == title
        entered = status_title.transition(state, "未管理任务")
        assert entered["soundEvent"] == state
        repeated = status_title.transition(state, title)
        assert repeated["changed"] is False
        assert repeated["stateChanged"] is False
        assert repeated["soundEvent"] is None

    stacked = status_title.transition("complete", "🌞 🟡 待确认｜原任务")
    assert stacked["proposedTitle"] == expected["complete"]
    assert stacked["soundEvent"] == "complete"
    attention = status_title.transition("attention", expected["running"])
    assert attention["soundEvent"] == "attention"
    assert status_title.current_state("未管理任务") is None


def check_sounds() -> None:
    sound = SCRIPT_DIR / "play-status-sound.py"
    signatures = set()
    for event in status_title.STATES:
        output = subprocess.check_output([sys.executable, str(sound), event, "--dry-run"], text=True)
        payload = json.loads(output)
        assert payload["event"] == event
        assert payload["backend"]
        assert payload["sound"]
        if payload["backend"] == "macos-afplay":
            signatures.add(payload["sound"])
    if signatures:
        assert len(signatures) == len(status_title.STATES)


def check_always_on() -> None:
    toggle = SCRIPT_DIR / "toggle-always-on.py"
    with tempfile.TemporaryDirectory() as temp_dir:
        agents = Path(temp_dir) / "AGENTS.md"
        original = "# Existing rules\n\nKeep this text.\n"
        agents.write_text(original, encoding="utf-8")

        subprocess.check_call([sys.executable, str(toggle), "enable", "--path", str(agents)])
        first = agents.read_text(encoding="utf-8")
        subprocess.check_call([sys.executable, str(toggle), "enable", "--path", str(agents)])
        second = agents.read_text(encoding="utf-8")
        assert first == second
        assert first.count("BEGIN TASK-STATUS ALWAYS-ON") == 1

        subprocess.check_call([sys.executable, str(toggle), "disable", "--path", str(agents)])
        assert agents.read_text(encoding="utf-8") == original
        backups = list(agents.parent.glob("AGENTS.md.task-status.bak-*"))
        assert len(backups) == 2


def check_packaging() -> None:
    package = SCRIPT_DIR / "package_skill.py"
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "task-status.zip"
        subprocess.check_call([sys.executable, str(package), str(output)])
        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
        assert "task-status/SKILL.md" in names
        assert "task-status/README.md" not in names
        assert "task-status/docs/task-status-demo.png" not in names
        assert not any("/.git/" in name or "/__pycache__/" in name for name in names)


def main() -> int:
    check_titles()
    check_sounds()
    check_always_on()
    check_packaging()
    print("task-status self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
