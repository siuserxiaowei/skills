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


EVENTS = (
    "pending",
    "discussion",
    "attention",
    "running",
    "waiting",
    "paused",
    "complete",
)

MAC_SOUNDS = {
    "pending": "/System/Library/Sounds/Pop.aiff",
    "discussion": "/System/Library/Sounds/Purr.aiff",
    "attention": "/System/Library/Sounds/Ping.aiff",
    "running": "/System/Library/Sounds/Tink.aiff",
    "waiting": "/System/Library/Sounds/Submarine.aiff",
    "paused": "/System/Library/Sounds/Basso.aiff",
    "complete": "/System/Library/Sounds/Glass.aiff",
}

LINUX_SOUND_IDS = {
    "pending": "message",
    "discussion": "dialog-information",
    "attention": "dialog-warning",
    "running": "service-login",
    "waiting": "bell",
    "paused": "dialog-error",
    "complete": "complete",
}

LINUX_SOUND_FILES = {
    "pending": (
        "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga",
        "/usr/share/sounds/freedesktop/stereo/message.oga",
    ),
    "discussion": (
        "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
        "/usr/share/sounds/freedesktop/stereo/message.oga",
    ),
    "attention": (
        "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga",
        "/usr/share/sounds/freedesktop/stereo/message.oga",
    ),
    "running": (
        "/usr/share/sounds/freedesktop/stereo/service-login.oga",
        "/usr/share/sounds/freedesktop/stereo/device-added.oga",
    ),
    "waiting": (
        "/usr/share/sounds/freedesktop/stereo/bell.oga",
        "/usr/share/sounds/freedesktop/stereo/phone-incoming-call.oga",
    ),
    "paused": (
        "/usr/share/sounds/freedesktop/stereo/dialog-error.oga",
        "/usr/share/sounds/freedesktop/stereo/suspend-error.oga",
    ),
    "complete": (
        "/usr/share/sounds/freedesktop/stereo/complete.oga",
        "/usr/share/sounds/freedesktop/stereo/service-login.oga",
    ),
}

WINDOWS_TONES = {
    "pending": ((523, 140),),
    "discussion": ((659, 90), (659, 90)),
    "attention": ((880, 140), (880, 140)),
    "running": ((523, 90), (659, 120)),
    "waiting": ((659, 110), (440, 180)),
    "paused": ((294, 300),),
    "complete": ((523, 80), (659, 80), (784, 180)),
}


def mac_sound(event: str) -> tuple[str, list[str], str] | None:
    override = os.environ.get(f"CODEX_TASK_STATUS_{event.upper()}_SOUND")
    sound = Path(override or MAC_SOUNDS[event])
    afplay = "/usr/bin/afplay"
    if Path(afplay).is_file() and sound.is_file():
        return "macos-afplay", [afplay, str(sound)], sound.stem
    osascript = shutil.which("osascript")
    if osascript:
        return "macos-beep", [osascript, "-e", "beep 1"], "system-beep"
    return None


def linux_sound(event: str) -> tuple[str, list[str], str] | None:
    canberra = shutil.which("canberra-gtk-play")
    if canberra:
        sound_id = LINUX_SOUND_IDS[event]
        return "linux-canberra", [canberra, "-i", sound_id], sound_id

    paplay = shutil.which("paplay")
    if paplay:
        for candidate in LINUX_SOUND_FILES[event]:
            if Path(candidate).is_file():
                return "linux-paplay", [paplay, candidate], Path(candidate).stem
    return None


def selected_backend(event: str) -> tuple[str, list[str] | None, str]:
    system = platform.system()
    if system == "Darwin":
        choice = mac_sound(event)
    elif system == "Linux":
        choice = linux_sound(event)
    elif system == "Windows":
        tones = WINDOWS_TONES[event]
        signature = ",".join(f"{frequency}Hz/{duration}ms" for frequency, duration in tones)
        return "windows-winsound", None, signature
    else:
        choice = None
    return choice or ("terminal-bell", None, "terminal-bell")


def play(event: str, dry_run: bool) -> int:
    backend, command, sound = selected_backend(event)
    if dry_run:
        print(
            json.dumps(
                {"event": event, "backend": backend, "sound": sound},
                ensure_ascii=False,
            )
        )
        return 0

    if backend == "windows-winsound":
        import winsound

        try:
            for frequency, duration in WINDOWS_TONES[event]:
                winsound.Beep(frequency, duration)
        except RuntimeError:
            winsound.MessageBeep(winsound.MB_OK)
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
    parser.add_argument("event", choices=EVENTS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return play(args.event, args.dry_run or os.environ.get("CODEX_TASK_STATUS_DRY_RUN") == "1")


if __name__ == "__main__":
    raise SystemExit(main())
