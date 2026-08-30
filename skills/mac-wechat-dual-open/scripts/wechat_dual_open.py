#!/usr/bin/env python3
"""Plan, create, and inspect a separately identified local WeChat copy on macOS."""

from __future__ import annotations

import argparse
import colorsys
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


SOURCE_DEFAULT = Path("/Applications/WeChat.app")
TARGET_DEFAULT = Path("~/Applications/WeChat-Second.app").expanduser()
IDENTIFIER_DEFAULT = "com.tencent.xin.local-second"


class OperationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BundleState:
    path: str
    exists: bool
    identifier: str | None
    version: str | None
    executable: bool
    signature_ok: bool | None


def execute(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if check and result.returncode:
        raise OperationError(f"command failed ({result.returncode}): {' '.join(argv)}\n{result.stdout}")
    return result


def need(program: str) -> str:
    resolved = shutil.which(program)
    if not resolved:
        raise OperationError(f"required program is unavailable: {program}")
    return resolved


def info_file(app: Path) -> Path:
    return app / "Contents" / "Info.plist"


def executable_file(app: Path) -> Path:
    return app / "Contents" / "MacOS" / "WeChat"


def load_info(app: Path) -> dict:
    path = info_file(app)
    try:
        with path.open("rb") as stream:
            value = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException) as exc:
        raise OperationError(f"cannot read bundle metadata at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OperationError(f"bundle metadata is not a dictionary: {path}")
    return value


def save_info(app: Path, value: dict) -> None:
    path = info_file(app)
    descriptor, temporary_name = tempfile.mkstemp(prefix="Info.", suffix=".plist", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            plistlib.dump(value, stream, sort_keys=False)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def bundle_state(app: Path) -> BundleState:
    if not app.exists():
        return BundleState(str(app), False, None, None, False, None)
    try:
        metadata = load_info(app)
        identifier = metadata.get("CFBundleIdentifier")
        version = metadata.get("CFBundleShortVersionString") or metadata.get("CFBundleVersion")
    except OperationError:
        identifier = version = None
    executable = executable_file(app).is_file()
    signature = execute(["codesign", "--verify", "--deep", "--strict", str(app)], check=False) if shutil.which("codesign") else None
    return BundleState(
        str(app),
        True,
        str(identifier) if identifier else None,
        str(version) if version else None,
        executable,
        None if signature is None else signature.returncode == 0,
    )


def validate_paths(source: Path, target: Path) -> None:
    source_resolved = source.resolve(strict=False)
    target_resolved = target.resolve(strict=False)
    if source_resolved == target_resolved:
        raise OperationError("source and target must be different bundles")
    if source_resolved in target_resolved.parents or target_resolved in source_resolved.parents:
        raise OperationError("source and target bundles must not contain one another")
    if source.name != "WeChat.app":
        raise OperationError(f"source does not look like the official WeChat bundle: {source}")
    if target.suffix != ".app":
        raise OperationError(f"target must end in .app: {target}")


def require_apply(args: argparse.Namespace) -> None:
    if not args.apply:
        raise OperationError("this command changes an app bundle; review `plan`, then repeat with --apply")


def clone_bundle(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise OperationError(f"source bundle is missing: {source}")
    if target.exists():
        raise OperationError(f"target already exists: {target}; use repair or choose a new path")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.partial-{uuid.uuid4().hex[:10]}"
    try:
        if shutil.which("ditto"):
            execute(["ditto", str(source), str(staging)])
        else:
            shutil.copytree(source, staging, symlinks=True)
        staging.rename(target)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def assign_identity(target: Path, identifier: str) -> None:
    if not identifier or identifier.count(".") < 2 or any(char.isspace() for char in identifier):
        raise OperationError(f"invalid bundle identifier: {identifier!r}")
    metadata = load_info(target)
    metadata["CFBundleIdentifier"] = identifier
    metadata.pop("CFBundleIconName", None)
    save_info(target, metadata)


def write_languages(identifier: str, languages: list[str]) -> None:
    if not languages or any(not item.strip() for item in languages):
        raise OperationError("at least one non-empty language tag is required")
    execute(["defaults", "write", identifier, "AppleLanguages", "-array", *languages])


def sign_bundle(target: Path) -> None:
    need("codesign")
    if shutil.which("xattr"):
        execute(["xattr", "-cr", str(target)])
    execute(["codesign", "--force", "--deep", "--sign", "-", str(target)])
    execute(["codesign", "--verify", "--deep", "--strict", str(target)])


def register_bundle(target: Path) -> None:
    register = Path(
        "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
    )
    if register.is_file():
        execute([str(register), "-f", str(target)], check=False)
    if shutil.which("qlmanage"):
        execute(["qlmanage", "-r", "cache"], check=False)


def image_library():
    try:
        from PIL import Image
    except ImportError as exc:
        raise OperationError("icon recoloring needs Pillow (`python3 -m pip install Pillow`)") from exc
    return Image


def parse_hex_color(raw: str) -> tuple[int, int, int]:
    value = raw.removeprefix("#")
    if len(value) != 6:
        raise argparse.ArgumentTypeError("color must contain six hexadecimal digits")
    try:
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("color must contain six hexadecimal digits") from exc


def locate_icons(app: Path) -> list[Path]:
    candidates = [
        app / "Contents" / "Resources" / "AppIcon.icns",
        app / "Contents" / "MacOS" / "WeChatAppEx.app" / "Contents" / "Resources" / "app.icns",
    ]
    return [path for path in candidates if path.is_file()]


def decode_largest_icon(icns: Path, work: Path) -> Path:
    need("iconutil")
    iconset = work / "decoded.iconset"
    execute(["iconutil", "-c", "iconset", str(icns), "-o", str(iconset)])
    Image = image_library()
    ranked: list[tuple[int, Path]] = []
    for path in iconset.glob("*.png"):
        with Image.open(path) as image:
            ranked.append((image.width * image.height, path))
    if not ranked:
        raise OperationError(f"no PNG representation found inside {icns}")
    return max(ranked)[1]


def recolor_pixels(source_png: Path, output_png: Path, target: tuple[int, int, int]) -> None:
    Image = image_library()
    image = Image.open(source_png).convert("RGBA")
    target_hue = colorsys.rgb_to_hsv(*(channel / 255 for channel in target))[0]
    changed: list[tuple[int, int, int, int]] = []
    for red, green, blue, alpha in image.getdata():
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        green_region = alpha and 0.18 <= hue <= 0.48 and saturation >= 0.12 and green > red and green > blue
        if green_region:
            mapped = colorsys.hsv_to_rgb(target_hue, min(1.0, max(0.28, saturation)), value)
            red, green, blue = (round(channel * 255) for channel in mapped)
        changed.append((red, green, blue, alpha))
    image.putdata(changed)
    image.save(output_png)


def encode_icns(source_png: Path, output: Path, work: Path) -> None:
    Image = image_library()
    master = Image.open(source_png).convert("RGBA")
    iconset = work / "encoded.iconset"
    iconset.mkdir()
    for points in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = points * scale
            suffix = "@2x" if scale == 2 else ""
            filename = iconset / f"icon_{points}x{points}{suffix}.png"
            master.resize((pixels, pixels), Image.Resampling.LANCZOS).save(filename)
    execute(["iconutil", "-c", "icns", str(iconset), "-o", str(output)])


def replace_icons(source: Path, target: Path, color: tuple[int, int, int]) -> Path:
    source_icons = locate_icons(source)
    target_icons = locate_icons(target)
    if not source_icons or not target_icons:
        raise OperationError("expected WeChat icon resources were not found")
    preview = target.parent / f"{target.stem}-icon-preview.png"
    with tempfile.TemporaryDirectory(prefix="wechat-icon-") as directory:
        work = Path(directory)
        decoded = decode_largest_icon(source_icons[0], work)
        recolored = work / "recolored.png"
        encoded = work / "replacement.icns"
        recolor_pixels(decoded, recolored, color)
        encode_icns(recolored, encoded, work)
        shutil.copy2(recolored, preview)
        for destination in target_icons:
            shutil.copy2(encoded, destination)
    metadata = load_info(target)
    metadata.pop("CFBundleIconName", None)
    save_info(target, metadata)
    return preview


def configure(target: Path, identifier: str, languages: list[str]) -> None:
    assign_identity(target, identifier)
    write_languages(identifier, languages)
    sign_bundle(target)
    register_bundle(target)


def plan(source: Path, target: Path, identifier: str, languages: list[str]) -> dict:
    validate_paths(source, target)
    return {
        "source": asdict(bundle_state(source)),
        "target": asdict(bundle_state(target)),
        "requested_identifier": identifier,
        "languages": languages,
        "mutations": ["copy bundle", "change duplicate identifier", "set duplicate language preference", "ad-hoc sign duplicate"],
        "original_bundle_modified": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--target", type=Path, default=TARGET_DEFAULT)
    parser.add_argument("--identifier", default=IDENTIFIER_DEFAULT)
    parser.add_argument("--languages", nargs="+", default=["zh-Hans", "en"])
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("plan")
    for name in ("create", "repair", "set-language", "launch"):
        command = subparsers.add_parser(name)
        command.add_argument("--apply", action="store_true")
    icon = subparsers.add_parser("recolor-icon")
    icon.add_argument("--color", type=parse_hex_color, default=parse_hex_color("#2878d0"))
    icon.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source, target = args.source.expanduser(), args.target.expanduser()
    validate_paths(source, target)
    if args.command in {"status", "plan"}:
        print(json.dumps(plan(source, target, args.identifier, args.languages), ensure_ascii=False, indent=2))
        return 0
    require_apply(args)
    if sys.platform != "darwin":
        raise OperationError("mutating commands are supported only on macOS")
    if args.command == "create":
        clone_bundle(source, target)
        configure(target, args.identifier, args.languages)
    elif args.command == "repair":
        if not target.is_dir():
            raise OperationError(f"target bundle is missing: {target}")
        configure(target, args.identifier, args.languages)
    elif args.command == "set-language":
        write_languages(args.identifier, args.languages)
    elif args.command == "recolor-icon":
        preview = replace_icons(source, target, args.color)
        sign_bundle(target)
        register_bundle(target)
        print(f"preview: {preview}")
    elif args.command == "launch":
        program = executable_file(target)
        if not program.is_file():
            raise OperationError(f"duplicate executable is missing: {program}")
        subprocess.Popen([str(program)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    print(json.dumps(asdict(bundle_state(target)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OperationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
