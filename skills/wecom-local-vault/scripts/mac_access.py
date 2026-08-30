#!/usr/bin/env python3
"""Small, testable authorization boundary shared by macOS acquisition tools."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Approval:
    attach: bool = False
    signed_copy: bool = False
    sudo_memory_read: bool = False


def ensure_authorized(mode: str, approval: Approval) -> None:
    allowed = {
        "attach": approval.attach,
        "spawn-signed-copy": approval.signed_copy,
        "sudo-memory-read": approval.sudo_memory_read,
    }
    if mode not in allowed:
        raise ValueError(f"unknown privileged mode: {mode}")
    if not allowed[mode]:
        option = {
            "attach": "--confirm-attach",
            "spawn-signed-copy": "--confirm-signed-copy",
            "sudo-memory-read": "--confirm-sudo",
        }[mode]
        raise PermissionError(f"{mode} requires explicit current-run approval via {option}")
