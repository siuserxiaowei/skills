#!/usr/bin/env python3
"""Play cross-platform task-status notification sounds."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


MAC_SOUNDS = {
    "attention": "/System/Library/Sounds/Ping.aiff",
    "complete": "/System/Library/Sounds/Glass.aiff",
}


def mac_sound(event: str) -> tuple[str, list[str]] | None:
    override = os.environ.get(f"CODEX_TASK_STATUS_{event.upper()}_SOUND")
    sound = Path(override or MAC_SOUNDS[event])
    afplay = "/usr/bin/afplay"
    if Path(afplay).is_file() and sound.is_file():
        return "macos-afplay", [afplay, str(sound)]
    osascript = shutil.which("osascript")
    if osascript:
        return "macos-beep", [osascript, "-e", "beep 1"]
    return None


def linux_sound(event: str) -> tuple[str, list[str]] | None:
    canberra = shutil.which("canberra-gtk-play")
    if canberra:
        sound_id = "dialog-warning" if event == "attention" else "complete"
        return "linux-canberra", [canberra, "-i", sound_id]

    paplay = shutil.which("paplay")
    candidates = {
        "attention": [
            "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga",
            "/usr/share/sounds/freedesktop/stereo/message.oga",
        ],
        "complete": [
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
            "/usr/share/sounds/freedesktop/stereo/service-login.oga",
        ],
    }
    if paplay:
        for candidate in candidates[event]:
            if Path(candidate).is_file():
                return "linux-paplay", [paplay, candidate]
    return None


def selected_backend(event: str) -> tuple[str, list[str] | None]:
    system = platform.system()
    if system == "Darwin":
        choice = mac_sound(event)
    elif system == "Linux":
        choice = linux_sound(event)
    elif system == "Windows":
        return "windows-winsound", None
    else:
        choice = None
    return choice or ("terminal-bell", None)


def play(event: str, dry_run: bool) -> int:
    backend, command = selected_backend(event)
    if dry_run:
        print(json.dumps({"event": event, "backend": backend}, ensure_ascii=False))
        return 0

    if backend == "windows-winsound":
        import winsound

        tone = winsound.MB_ICONEXCLAMATION if event == "attention" else winsound.MB_OK
        winsound.MessageBeep(tone)
        return 0

    if command is not None:
        completed = subprocess.run(command, check=False)
        if completed.returncode == 0:
            return 0

    sys.stdout.write("\a")
    sys.stdout.flush()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=("attention", "complete"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return play(args.event, args.dry_run or os.environ.get("CODEX_TASK_STATUS_DRY_RUN") == "1")


if __name__ == "__main__":
    raise SystemExit(main())
