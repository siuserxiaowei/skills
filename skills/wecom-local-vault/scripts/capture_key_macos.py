#!/usr/bin/env python3
"""Capture a candidate WeCom database secret through explicitly authorized Frida use."""

from __future__ import annotations

import argparse
import importlib
import queue
import platform
import json
import time
import shutil
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from local_state import active_home, databases_accepting, describe_account, discover_accounts, select_account, store_verified_secret
from mac_access import Approval, ensure_authorized


AGENT_SOURCE = r"""
'use strict';
const delivered = new Set();
function publish(address, count, origin) {
  if (!address || address.isNull() || count !== 16) return;
  try {
    const bytes = new Uint8Array(address.readByteArray(16));
    const encoded = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
    if (!delivered.has(encoded)) {
      delivered.add(encoded);
      send({event: 'candidate', origin: origin, encoded: encoded});
    }
  } catch (ignored) {}
}
function exported(symbol) {
  try { return Module.findGlobalExportByName(symbol); } catch (ignored) { return null; }
}
function install(symbol, callback) {
  const address = exported(symbol);
  if (!address) return;
  try {
    Interceptor.attach(address, {onEnter: callback});
    send({event: 'hook', symbol: symbol});
  } catch (error) { send({event: 'warning', detail: symbol + ': ' + error}); }
}
install('CC_MD5', function (args) {
  const count = args[1].toUInt32();
  if (count !== 24) return;
  try {
    const tail = new Uint8Array(args[0].add(20).readByteArray(4));
    if (tail[0] === 0x73 && tail[1] === 0x41 && tail[2] === 0x6c && tail[3] === 0x54) publish(args[0], 16, 'md5-page-derivation');
  } catch (ignored) {}
});
install('sqlite3_key', function (args) { publish(args[1], args[2].toInt32(), 'sqlite3_key'); });
install('sqlite3_key_v2', function (args) { publish(args[2], args[3].toInt32(), 'sqlite3_key_v2'); });
send({event: 'ready'});
"""


ORIGINAL_APP = Path("/Applications/企业微信.app")


def _account(value: str | None) -> Path:
    if value:
        return select_account(value)
    choices = discover_accounts()
    if len(choices) <= 1:
        return select_account(None)
    return max(choices, key=lambda path: (describe_account(path)["wal_count"], describe_account(path)["database_count"]))


def _pid(explicit: int | None) -> int:
    if explicit:
        return explicit
    result = subprocess.run(["/usr/bin/pgrep", "-f", "/Contents/MacOS/企业微信"], capture_output=True, text=True, check=False)
    values = [int(line) for line in result.stdout.splitlines() if line.strip().isdigit()]
    if not values:
        raise SystemExit("企业微信未运行；attach 模式不会替你启动客户端")
    return values[0]


def _signed_copy(source: Path, target: Path, reuse: bool) -> Path:
    if not source.is_dir():
        raise SystemExit(f"找不到企业微信应用: {source}")
    if target.exists() and not reuse:
        raise SystemExit(f"拒绝覆盖已存在的签名副本: {target}")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=True)
        signing = ["/usr/bin/codesign", "--sign", "-", "--deep"]
        signing.extend(["--preserve-metadata=entitlements", "--force", str(target)])
        subprocess.run(signing, check=True)
    executable = target / "Contents" / "MacOS" / "企业微信"
    if not executable.is_file():
        raise SystemExit("签名副本缺少主可执行文件")
    return executable


def list_databases(data_dir: str | None) -> int:
    report = describe_account(_account(data_dir))
    print(json.dumps({key: report[key] for key in ("dataset_id", "database_count", "formats", "wal_count")}, ensure_ascii=False, indent=2))
    print("未附加进程。")
    return 0


def doctor(data_dir: str | None) -> int:
    report = describe_account(_account(data_dir))
    try:
        frida = importlib.import_module("frida")
        version = getattr(frida, "__version__", "unknown")
    except ModuleNotFoundError:
        version = "missing"
    print(json.dumps({"platform": platform.platform(), "python": platform.python_version(), "frida": version, "dataset_id": report["dataset_id"], "encrypted_databases": report["formats"].get("wecom-aes128", 0)}, ensure_ascii=False, indent=2))
    print("doctor 只做环境检查，不附加进程，也不修改系统设置。")
    return 2 if version == "missing" else 0


def capture(args: argparse.Namespace) -> int:
    try:
        ensure_authorized(args.mode, Approval(attach=args.confirm_attach, signed_copy=args.confirm_signed_copy))
    except PermissionError as exc:
        raise SystemExit(str(exc)) from exc
    if sys.platform != "darwin":
        raise SystemExit("密钥捕获只支持 macOS")
    if args.duration < 1:
        raise SystemExit("--duration 必须大于 0")
    try:
        frida = importlib.import_module("frida")
    except ModuleNotFoundError as exc:
        raise SystemExit("frida 模块不可用；在隔离环境准备该依赖后再执行") from exc
    account = _account(args.data_dir)
    device = frida.get_local_device()
    spawned = False
    if args.mode == "attach":
        pid = _pid(args.pid)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = Path(args.wecom_copy).expanduser() if args.wecom_copy else active_home().path / "apps" / f"WeComSigned-{stamp}.app"
        executable = _signed_copy(Path(args.source_app).expanduser(), target, args.reuse_signed_copy)
        pid = device.spawn([str(executable)])
        spawned = True
    inbox: queue.Queue[dict] = queue.Queue()
    hooks: set[str] = set()

    def receive(message: dict, _data: object) -> None:
        if message.get("type") == "send" and isinstance(message.get("payload"), dict):
            inbox.put(message["payload"])

    try:
        session = device.attach(pid)
        script = session.create_script(AGENT_SOURCE)
        script.on("message", receive)
        script.load()
        if spawned:
            device.resume(pid)
    except frida.PermissionDeniedError as exc:
        raise SystemExit("macOS 拒绝 task_for_pid；未获得密钥，也未修改系统安全设置") from exc
    deadline, accepted = time.monotonic() + args.duration, None
    try:
        while time.monotonic() < deadline and accepted is None:
            remaining = deadline - time.monotonic()
            try:
                event = inbox.get(timeout=max(0.01, min(remaining, 0.25)))
            except queue.Empty:
                continue
            if event.get("event") == "hook":
                hooks.add(str(event.get("symbol")))
            elif event.get("event") == "candidate":
                try:
                    candidate = bytes.fromhex(str(event.get("encoded", "")))
                except ValueError:
                    continue
                matches = databases_accepting(candidate, account)
                if matches:
                    accepted = candidate
    finally:
        try:
            script.unload()
        finally:
            session.detach()
    if not hooks:
        print("没有可用的已知加密入口；未保存密钥。", file=sys.stderr)
        return 2
    if accepted is None:
        print("等待期内没有候选通过数据库第一页校验；未保存密钥。", file=sys.stderr)
        return 3
    destination = Path(args.output).expanduser() if args.output else None
    saved = store_verified_secret(active_home(), account, accepted, destination)
    print(f"已私密保存通过校验的密钥记录：{saved}")
    print("终端未输出密钥内容。")
    return 0


def entrypoint(argv=None):
    parser = argparse.ArgumentParser(description="Authorized WeCom database-key acquisition for macOS")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list"); listing.add_argument("--data-dir")
    checking = commands.add_parser("doctor"); checking.add_argument("--data-dir")
    run = commands.add_parser("capture")
    run.add_argument("--mode", choices=("attach", "spawn-signed-copy"), default="attach")
    run.add_argument("--data-dir"); run.add_argument("--pid", type=int); run.add_argument("--duration", type=int, default=60); run.add_argument("--output")
    run.add_argument("--confirm-attach", action="store_true"); run.add_argument("--confirm-signed-copy", action="store_true")
    run.add_argument("--source-app", default=str(ORIGINAL_APP)); run.add_argument("--wecom-copy"); run.add_argument("--reuse-signed-copy", action="store_true")
    args = parser.parse_args(argv)
    passive = {"list": list_databases, "doctor": doctor}
    if args.command in passive:
        return passive[args.command](args.data_dir)
    result = capture(args)
    return result


if __name__ == "__main__":
    raise SystemExit(entrypoint())
