#!/usr/bin/env python3
"""Read a live WeCom process with Mach APIs after an explicit sudo gate."""

from __future__ import annotations

import ctypes
import sys
import struct
import re
import os
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from local_state import active_home, databases_accepting, discover_accounts, select_account, store_verified_secret
from mac_access import Approval, ensure_authorized


IMAGE_BASE = 0x100000000
MANAGER_VTABLE = 0x10C3550C8
KEY_FIELD = 0x68
READABLE, WRITABLE = 1, 2
SUCCESS, REGION_INFO, REGION_WORDS = 0, 9, 9
WINDOW = 4 * 1024 * 1024


class Region(ctypes.Structure):
    _fields_ = [
        ("current_access", ctypes.c_uint32), ("maximum_access", ctypes.c_uint32),
        ("inheritance_mode", ctypes.c_uint32), ("is_shared", ctypes.c_uint32),
        ("is_reserved", ctypes.c_uint32), ("mapped_offset", ctypes.c_uint64),
        ("access_pattern", ctypes.c_uint32), ("wire_count", ctypes.c_uint16),
    ]


def _system_library():
    library = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
    library.task_for_pid.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.POINTER(ctypes.c_uint32)]
    u32, u64 = ctypes.c_uint32, ctypes.c_uint64
    pointer = ctypes.POINTER
    library.mach_vm_region.argtypes = [u32, pointer(u64), pointer(u64), ctypes.c_int, ctypes.c_void_p, pointer(u32), pointer(u32)]
    library.mach_vm_read_overwrite.argtypes = [u32, u64, u64, u64, pointer(u64)]
    return library


def _read(library, task: int, address: int, size: int) -> bytes | None:
    buffer = ctypes.create_string_buffer(size)
    delivered = ctypes.c_uint64()
    code = library.mach_vm_read_overwrite(task, address, size, ctypes.cast(buffer, ctypes.c_void_p).value, ctypes.byref(delivered))
    return buffer.raw[: delivered.value] if code == SUCCESS and delivered.value else None


def _string_value(library, task: int, raw: bytes) -> bytes | None:
    if len(raw) != 24:
        return None
    inline_size = raw[23]
    if 0 < inline_size <= 23:
        return raw[:inline_size]
    pointer, length, _capacity = struct.unpack("<QQQ", raw)
    return _read(library, task, pointer, int(length)) if pointer and 0 < length <= 4096 else None


def root_scan(pid: int, vtable: int, destination: Path) -> int:
    library = _system_library()
    self_task = ctypes.c_uint32.in_dll(library, "mach_task_self_").value
    task = ctypes.c_uint32()
    code = library.task_for_pid(self_task, pid, ctypes.byref(task))
    if code != SUCCESS:
        print(f"task_for_pid failed: kern_return={code}", file=sys.stderr)
        return 73
    needle, candidates, address = struct.pack("<Q", vtable), [], ctypes.c_uint64()
    while True:
        size, info, count, object_name = ctypes.c_uint64(), Region(), ctypes.c_uint32(REGION_WORDS), ctypes.c_uint32()
        code = library.mach_vm_region(task.value, ctypes.byref(address), ctypes.byref(size), REGION_INFO, ctypes.byref(info), ctypes.byref(count), ctypes.byref(object_name))
        if code != SUCCESS:
            break
        start, region_size = address.value, size.value
        if info.current_access & READABLE and info.current_access & WRITABLE:
            offset, overlap = 0, b""
            while offset < region_size:
                length = min(WINDOW, region_size - offset)
                chunk = _read(library, task.value, start + offset, length)
                if chunk:
                    haystack, base = overlap + chunk, start + offset - len(overlap)
                    cursor = haystack.find(needle)
                    while cursor >= 0:
                        object_address = base + cursor
                        raw = _read(library, task.value, object_address + KEY_FIELD, 24)
                        key = _string_value(library, task.value, raw or b"")
                        if key and len(key) == 16 and len(set(key)) >= 6:
                            candidates.append(key.hex())
                        cursor = haystack.find(needle, cursor + 1)
                    overlap = haystack[-7:]
                else:
                    overlap = b""
                offset += length
        address.value = start + region_size
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.chmod(0o700)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump({"candidate_hex": list(dict.fromkeys(candidates))}, handle)
    owner, group = os.environ.get("SUDO_UID"), os.environ.get("SUDO_GID")
    if owner and group:
        os.chown(destination, int(owner), int(group))
    print(f"read-only scan complete; candidates={len(candidates)}")
    return 0 if candidates else 2


def _pid(value: int | None) -> int:
    if value:
        return value
    result = subprocess.run(["/bin/ps", "-axo", "pid=,command="], capture_output=True, text=True, check=True)
    app_name = "\u4f01\u4e1a\u5fae\u4fe1"
    executable = str(Path("/Applications") / f"{app_name}.app" / "Contents" / "MacOS" / app_name)
    for line in result.stdout.splitlines():
        if executable in line:
            return int(line.strip().split(None, 1)[0])
    raise SystemExit("企微主进程当前不在运行，无法读取内存")


def _load_address(pid: int) -> int:
    result = subprocess.run(["/usr/bin/vmmap", str(pid)], capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        label, separator, raw_value = line.strip().partition(":")
        if separator and label == "Load Address" and raw_value.strip().lower().startswith("0x"):
            return int(raw_value.strip(), 16)
    raise SystemExit("vmmap 没有提供可识别的映像载入地址")


def run(args: argparse.Namespace) -> int:
    if sys.platform != "darwin":
        raise SystemExit("Mach 内存读取只支持 macOS")
    try:
        ensure_authorized("sudo-memory-read", Approval(sudo_memory_read=args.confirm_sudo))
    except PermissionError as exc:
        print(str(exc))
        return 64
    account = select_account(args.data_dir) if args.data_dir else (discover_accounts()[0] if len(discover_accounts()) == 1 else select_account(None))
    pid = _pid(args.pid)
    slide = _load_address(pid)
    vtable = slide + MANAGER_VTABLE - IMAGE_BASE
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    candidate_file = active_home().private / f"memory-candidates-{stamp}.json"
    if os.geteuid() == 0:
        status = root_scan(pid, vtable, candidate_file)
    else:
        print("即将由 sudo 请求本机管理员密码；不要把密码发到聊天中。")
        child = [sys.executable, str(Path(__file__).resolve()), "root-scan"]
        child.extend(["--out", str(candidate_file), "--vtable", hex(vtable), "--pid", str(pid), "--confirmed-parent"])
        status = subprocess.call(["sudo", *child])
    if status not in {0, 2} or not candidate_file.is_file():
        return status or 1
    with candidate_file.open(encoding="utf-8") as handle:
        values = json.load(handle).get("candidate_hex", [])
    for encoded in values:
        try:
            candidate = bytes.fromhex(str(encoded))
        except ValueError:
            continue
        if databases_accepting(candidate, account):
            saved = store_verified_secret(active_home(), account, candidate)
            print(f"VALIDATED_AND_SAVED {saved}")
            return 0
    print("没有候选通过数据库第一页校验；未保存密钥。")
    return 2


def entrypoint(argv=None):
    parser = argparse.ArgumentParser(description="Authorized read-only DbKeyManager memory scan")
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("scan")
    scan.add_argument("--data-dir")
    scan.add_argument("--confirm-sudo", action="store_true")
    scan.add_argument("--pid", type=int)
    child = commands.add_parser("root-scan"); child.add_argument("--pid", type=int, required=True); child.add_argument("--vtable", type=lambda value: int(value, 0), required=True); child.add_argument("--out", required=True); child.add_argument("--confirmed-parent", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "root-scan":
        if not args.confirmed_parent:
            print("root-scan requires explicit parent confirmation", file=sys.stderr)
            return 64
        return root_scan(args.pid, args.vtable, Path(args.out))
    return run(args)


if __name__ == "__main__":
    raise SystemExit(entrypoint())
