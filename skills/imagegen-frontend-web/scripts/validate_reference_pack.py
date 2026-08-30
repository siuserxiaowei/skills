#!/usr/bin/env python3
"""Validate an image-based web reference pack without external dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any


DELIVERABLES = {"single-concept", "responsive-set", "reference-pack", "production-assets"}
SCOPES = {"page", "section", "state", "asset"}
PURPOSES = {"reference", "production-asset"}
TEXT_STRATEGIES = {"live-overlay", "placeholder-only", "essential-raster", "no-text"}
ALT_MODES = {"descriptive", "decorative"}


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_message(messages: list[dict[str, Any]], level: str, code: str, message: str, location: str) -> None:
    messages.append({"level": level, "code": code, "message": message, "location": location})


def image_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        data = handle.read(4 * 1024 * 1024)
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])

    if data.startswith(b"\xff\xd8"):
        offset = 2
        sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
        while offset + 4 <= len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            while offset < len(data) and data[offset] == 0xFF:
                offset += 1
            if offset >= len(data):
                break
            marker = data[offset]
            offset += 1
            if marker in {0x01, 0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if offset + 2 > len(data):
                break
            segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
            if segment_length < 2 or offset + segment_length > len(data):
                break
            if marker in sof_markers and segment_length >= 7:
                height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
                return width, height
            offset += segment_length

    if len(data) >= 30 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
            height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
            return width, height
        if chunk == b"VP8L" and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1

    raise ValueError("unsupported or malformed image header; expected PNG, JPEG, or WebP")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_pack_file(root: Path, raw_path: Any) -> tuple[Path | None, str | None]:
    if not nonempty(raw_path):
        return None, "file must be a non-empty relative path"
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        return None, "file must stay inside the reference-pack directory"
    candidate = root / relative
    cursor = candidate
    while cursor != root:
        if cursor.is_symlink():
            return None, "symlinked files or directories are not accepted"
        cursor = cursor.parent
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError):
        return None, "file does not exist inside the reference-pack directory"
    if not resolved.is_file():
        return None, "path is not a regular file"
    return resolved, None


def validate(manifest_path: Path) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        add_message(messages, "error", "manifest.unreadable", str(exc), "$")
        return {"valid": False, "errors": 1, "warnings": 0, "messages": messages, "files": files}

    if not isinstance(data, dict):
        add_message(messages, "error", "manifest.type", "manifest root must be an object", "$")
        return {"valid": False, "errors": 1, "warnings": 0, "messages": messages, "files": files}

    if data.get("version") != 1:
        add_message(messages, "error", "manifest.version", "version must be 1", "$.version")
    if data.get("deliverable") not in DELIVERABLES:
        add_message(messages, "error", "deliverable.value", f"deliverable must be one of {sorted(DELIVERABLES)}", "$.deliverable")

    brief = data.get("brief")
    if not isinstance(brief, dict):
        add_message(messages, "error", "brief.type", "brief must be an object", "$.brief")
    else:
        for field in ("page_kind", "audience", "goal", "primary_action"):
            if not nonempty(brief.get(field)):
                add_message(messages, "error", "brief.required", f"brief.{field} must be non-empty", f"$.brief.{field}")

    design_system = data.get("design_system")
    if not isinstance(design_system, dict):
        add_message(messages, "error", "design_system.type", "design_system must be an object", "$.design_system")
    else:
        for field in ("colors", "typography", "grid", "shape"):
            if not nonempty(design_system.get(field)):
                add_message(messages, "error", "design_system.required", f"design_system.{field} must be non-empty", f"$.design_system.{field}")

    viewports = data.get("viewports")
    viewport_map: dict[str, tuple[int, int]] = {}
    if not isinstance(viewports, list) or not viewports:
        add_message(messages, "error", "viewports.required", "viewports must be a non-empty array", "$.viewports")
    else:
        for index, viewport in enumerate(viewports):
            location = f"$.viewports[{index}]"
            if not isinstance(viewport, dict):
                add_message(messages, "error", "viewport.type", "viewport must be an object", location)
                continue
            viewport_id = viewport.get("id")
            width = viewport.get("width")
            height = viewport.get("height")
            if not nonempty(viewport_id):
                add_message(messages, "error", "viewport.id", "viewport id must be non-empty", f"{location}.id")
                continue
            if viewport_id in viewport_map:
                add_message(messages, "error", "viewport.duplicate", f"duplicate viewport id: {viewport_id}", f"{location}.id")
                continue
            if not isinstance(width, int) or isinstance(width, bool) or not 240 <= width <= 8000:
                add_message(messages, "error", "viewport.width", "width must be an integer from 240 to 8000", f"{location}.width")
                continue
            if not isinstance(height, int) or isinstance(height, bool) or not 240 <= height <= 20000:
                add_message(messages, "error", "viewport.height", "height must be an integer from 240 to 20000", f"{location}.height")
                continue
            viewport_map[viewport_id] = (width, height)

    frames = data.get("frames")
    frame_ids: set[str] = set()
    used_viewports: set[str] = set()
    root = manifest_path.parent.resolve()
    if not isinstance(frames, list) or not frames:
        add_message(messages, "error", "frames.required", "frames must be a non-empty array", "$.frames")
    else:
        for index, frame in enumerate(frames):
            location = f"$.frames[{index}]"
            if not isinstance(frame, dict):
                add_message(messages, "error", "frame.type", "frame must be an object", location)
                continue

            frame_id = frame.get("id")
            if not nonempty(frame_id):
                add_message(messages, "error", "frame.id", "frame id must be non-empty", f"{location}.id")
            elif frame_id in frame_ids:
                add_message(messages, "error", "frame.duplicate", f"duplicate frame id: {frame_id}", f"{location}.id")
            else:
                frame_ids.add(frame_id)

            scope = frame.get("scope")
            if scope not in SCOPES:
                add_message(messages, "error", "frame.scope", f"scope must be one of {sorted(SCOPES)}", f"{location}.scope")
            if not nonempty(frame.get("job")):
                add_message(messages, "error", "frame.job", "job must explain the decision this frame resolves", f"{location}.job")

            purpose = frame.get("purpose")
            if purpose not in PURPOSES:
                add_message(messages, "error", "frame.purpose", f"purpose must be one of {sorted(PURPOSES)}", f"{location}.purpose")
            if purpose == "production-asset" and not nonempty(frame.get("rights")):
                add_message(messages, "error", "frame.rights", "production assets require a non-empty rights statement", f"{location}.rights")

            text_strategy = frame.get("text_strategy")
            if text_strategy not in TEXT_STRATEGIES:
                add_message(messages, "error", "frame.text_strategy", f"text_strategy must be one of {sorted(TEXT_STRATEGIES)}", f"{location}.text_strategy")
            if text_strategy == "essential-raster":
                if not nonempty(frame.get("raster_text_reason")):
                    add_message(messages, "error", "frame.raster_reason", "essential-raster requires raster_text_reason", f"{location}.raster_text_reason")
                add_message(messages, "warning", "frame.raster_accessibility", "verify an accessible equivalent for essential raster text", location)

            alt_mode = frame.get("alt_mode")
            alt_text = frame.get("alt_text")
            if alt_mode not in ALT_MODES:
                add_message(messages, "error", "frame.alt_mode", f"alt_mode must be one of {sorted(ALT_MODES)}", f"{location}.alt_mode")
            elif alt_mode == "descriptive" and not nonempty(alt_text):
                add_message(messages, "error", "frame.alt_text", "descriptive media requires non-empty alt_text", f"{location}.alt_text")
            elif alt_mode == "decorative" and alt_text not in ("", None):
                add_message(messages, "warning", "frame.decorative_alt", "decorative media should use an empty alternative", f"{location}.alt_text")

            notes = frame.get("implementation_notes")
            if not isinstance(notes, list) or not notes or not all(nonempty(note) for note in notes):
                add_message(messages, "error", "frame.implementation_notes", "implementation_notes must contain at least one non-empty string", f"{location}.implementation_notes")
            if not nonempty(frame.get("provenance")):
                add_message(messages, "error", "frame.provenance", "provenance must identify how this media was created or supplied", f"{location}.provenance")

            focal_point = frame.get("focal_point")
            if focal_point is not None:
                valid_focal = (
                    isinstance(focal_point, list)
                    and len(focal_point) == 2
                    and all(isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1 for value in focal_point)
                )
                if not valid_focal:
                    add_message(messages, "error", "frame.focal_point", "focal_point must be [x, y] with values from 0 to 1", f"{location}.focal_point")

            viewport_id = frame.get("viewport")
            if scope != "asset":
                if viewport_id not in viewport_map:
                    add_message(messages, "error", "frame.viewport", "page, section, and state frames require a declared viewport", f"{location}.viewport")
                else:
                    used_viewports.add(viewport_id)
            elif viewport_id is not None and viewport_id not in viewport_map:
                add_message(messages, "error", "frame.viewport", "asset viewport must be omitted or declared", f"{location}.viewport")

            resolved, path_error = resolve_pack_file(root, frame.get("file"))
            if path_error:
                add_message(messages, "error", "frame.file", path_error, f"{location}.file")
                continue
            assert resolved is not None
            try:
                width, height = image_dimensions(resolved)
            except (OSError, ValueError, struct.error) as exc:
                add_message(messages, "error", "frame.image", str(exc), f"{location}.file")
                continue

            files.append({
                "id": frame_id,
                "path": os.path.relpath(resolved, root),
                "width": width,
                "height": height,
                "sha256": sha256(resolved),
            })

            if viewport_id in viewport_map and scope != "asset":
                target_width, target_height = viewport_map[viewport_id]
                actual_ratio = width / height
                target_ratio = target_width / target_height
                drift = abs(actual_ratio - target_ratio) / target_ratio
                if drift > 0.08:
                    add_message(messages, "warning", "frame.aspect_ratio", f"image aspect ratio differs from viewport by {drift:.1%}; document the crop or regenerate", f"{location}.file")

    if data.get("deliverable") == "responsive-set":
        widths = [viewport_map[item][0] for item in used_viewports if item in viewport_map]
        if not any(width <= 480 for width in widths) or not any(width >= 1024 for width in widths):
            add_message(messages, "error", "responsive.coverage", "responsive-set requires used narrow (<=480px) and desktop (>=1024px) viewports", "$.frames")

    errors = sum(message["level"] == "error" for message in messages)
    warnings = sum(message["level"] == "warning" for message in messages)
    return {
        "valid": errors == 0,
        "errors": errors,
        "warnings": warnings,
        "messages": messages,
        "files": files,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="path to the reference-pack JSON manifest")
    parser.add_argument("--strict", action="store_true", help="return non-zero for warnings as well as errors")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = validate(args.manifest)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for message in result["messages"]:
            print(f"{message['level'].upper():7} {message['code']}: {message['message']} ({message['location']})")
        print(f"files={len(result['files'])} errors={result['errors']} warnings={result['warnings']}")
    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
