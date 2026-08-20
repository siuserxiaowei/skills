#!/usr/bin/env python3
"""Speak cross-platform task-status announcements with tone fallbacks."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
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

PHRASES = {
    "pending": "任务待派发。",
    "discussion": "任务讨论中。",
    "attention": "任务待确认。",
    "running": "任务进行中。",
    "waiting": "任务等待中。",
    "paused": "任务已暂停。",
    "complete": "任务已完成。",
}

MAC_VOICES = {
    "pending": ("Tingting", 175),
    "discussion": ("Tingting", 168),
    "attention": ("Tingting", 180),
    "running": ("Tingting", 182),
    "waiting": ("Tingting", 165),
    "paused": ("Tingting", 158),
    "complete": ("Tingting", 188),
}

WINDOWS_RATES = {
    "pending": 0,
    "discussion": -1,
    "attention": 1,
    "running": 1,
    "waiting": -1,
    "paused": -2,
    "complete": 2,
}

LINUX_PROFILES = {
    "pending": (0, 50),
    "discussion": (-5, 48),
    "attention": (8, 52),
    "running": (8, 52),
    "waiting": (-8, 48),
    "paused": (-12, 45),
    "complete": (12, 55),
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


def mac_speech(event: str) -> tuple[str, list[str], str] | None:
    override = os.environ.get(f"CODEX_TASK_STATUS_{event.upper()}_SOUND")
    afplay = "/usr/bin/afplay"
    if override and Path(afplay).is_file() and (sound := Path(override)).is_file():
        return "macos-afplay", [afplay, str(sound)], sound.stem

    say = "/usr/bin/say"
    if Path(say).is_file():
        default_voice, default_rate = MAC_VOICES[event]
        voice = os.environ.get(
            f"CODEX_TASK_STATUS_{event.upper()}_VOICE",
            default_voice,
        )
        rate_value = os.environ.get(
            f"CODEX_TASK_STATUS_{event.upper()}_RATE",
            str(default_rate),
        )
        try:
            rate = max(80, min(350, int(rate_value)))
        except ValueError:
            rate = default_rate
        phrase = PHRASES[event]
        signature = f"{voice}@{rate}:{phrase}"
        return "macos-say", [say, "-v", voice, "-r", str(rate), phrase], signature

    return mac_tone(event)


def mac_tone(event: str) -> tuple[str, list[str], str] | None:
    sound = Path(MAC_SOUNDS[event])
    afplay = "/usr/bin/afplay"
    if Path(afplay).is_file() and sound.is_file():
        return "macos-afplay", [afplay, str(sound)], sound.stem
    osascript = shutil.which("osascript")
    if osascript:
        return "macos-beep", [osascript, "-e", "beep 1"], "system-beep"
    return None


def linux_speech(event: str) -> tuple[str, list[str], str] | None:
    rate, pitch = LINUX_PROFILES[event]
    phrase = PHRASES[event]

    speech_dispatcher = shutil.which("spd-say")
    if speech_dispatcher:
        signature = f"zh@{rate}/{pitch}:{phrase}"
        return (
            "linux-spd-say",
            [
                speech_dispatcher,
                "--wait",
                "--language",
                "zh",
                "--rate",
                str(rate),
                "--pitch",
                str(pitch),
                phrase,
            ],
            signature,
        )

    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        words_per_minute = max(90, min(300, 175 + rate))
        signature = f"zh@{words_per_minute}/{pitch}:{phrase}"
        return (
            "linux-espeak",
            [
                espeak,
                "-v",
                "zh",
                "-s",
                str(words_per_minute),
                "-p",
                str(pitch),
                phrase,
            ],
            signature,
        )

    return linux_tone(event)


def linux_tone(event: str) -> tuple[str, list[str], str] | None:
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


def windows_speech(event: str) -> tuple[str, list[str] | None, str]:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    phrase = PHRASES[event]
    rate = WINDOWS_RATES[event]
    if powershell:
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$speaker.Rate = {rate}; "
            f"$speaker.Speak('{phrase}')"
        )
        signature = f"system-default@{rate}:{phrase}"
        return "windows-powershell-speech", [powershell, "-NoProfile", "-Command", script], signature

    tones = WINDOWS_TONES[event]
    signature = ",".join(f"{frequency}Hz/{duration}ms" for frequency, duration in tones)
    return "windows-winsound", None, signature


def play_windows_tones(event: str) -> None:
    import winsound

    try:
        for frequency, duration in WINDOWS_TONES[event]:
            winsound.Beep(frequency, duration)
    except (OSError, RuntimeError):
        winsound.MessageBeep(winsound.MB_OK)


def selected_backend(event: str) -> tuple[str, list[str] | None, str]:
    system = platform.system()
    if system == "Darwin":
        choice = mac_speech(event)
    elif system == "Linux":
        choice = linux_speech(event)
    elif system == "Windows":
        return windows_speech(event)
    else:
        choice = None
    return choice or ("terminal-bell", None, "terminal-bell")


def play(event: str, dry_run: bool) -> int:
    backend, command, sound = selected_backend(event)
    if dry_run:
        print(
            json.dumps(
                {
                    "event": event,
                    "phrase": PHRASES[event],
                    "backend": backend,
                    "sound": sound,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if backend == "windows-winsound":
        play_windows_tones(event)
        return 0

    if command is not None:
        completed = subprocess.run(command, check=False)
        if completed.returncode == 0:
            return 0

        if platform.system() == "Darwin":
            fallback = mac_tone(event)
        elif platform.system() == "Linux":
            fallback = linux_tone(event)
        elif platform.system() == "Windows":
            play_windows_tones(event)
            return 0
        else:
            fallback = None
        if fallback is not None:
            _, fallback_command, _ = fallback
            if subprocess.run(fallback_command, check=False).returncode == 0:
                return 0

    sys.stdout.write("\a")
    sys.stdout.flush()
    return 0


def demo(dry_run: bool) -> int:
    for index, event in enumerate(EVENTS):
        if index and not dry_run:
            time.sleep(0.55)
        result = play(event, dry_run)
        if result != 0:
            return result
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=EVENTS + ("demo",))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    dry_run = args.dry_run or os.environ.get("CODEX_TASK_STATUS_DRY_RUN") == "1"
    if args.event == "demo":
        return demo(dry_run)
    return play(args.event, dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
