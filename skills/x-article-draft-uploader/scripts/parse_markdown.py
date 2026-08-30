#!/usr/bin/env python3
"""Prepare a local Markdown document for an X Articles draft.

The parser is deliberately small and deterministic. It never fetches remote
images, walks unrelated home-directory folders, or executes Markdown content.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path


DIVIDER_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
UNORDERED_RE = re.compile(r"^\s*[-+*]\s+(.+)$")
ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
SAFE_LINK_RE = re.compile(r"^(?:https?://|mailto:)", re.IGNORECASE)


@dataclass(frozen=True)
class ImageToken:
    alt: str
    target: str


@dataclass
class BodyBlock:
    kind: str
    lines: list[str]

    @property
    def source(self) -> str:
        return "\n".join(self.lines).strip()


def strip_frontmatter(text: str) -> str:
    """Remove only a leading, line-delimited YAML frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :]).lstrip("\n")
    return text


def parse_image_at(text: str, start: int) -> tuple[ImageToken, int] | None:
    """Parse one Markdown image using balanced parentheses in its target."""
    if not text.startswith("![", start):
        return None
    alt_end = text.find("](", start + 2)
    if alt_end == -1:
        return None
    cursor = alt_end + 2
    depth = 1
    escaped = False
    while cursor < len(text):
        char = text[cursor]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                token = ImageToken(text[start + 2 : alt_end], text[alt_end + 2 : cursor].strip())
                return token, cursor + 1
        cursor += 1
    return None


def split_inline_images(line: str) -> list[str | ImageToken]:
    """Return text/image parts without interpreting image-like text in code."""
    parts: list[str | ImageToken] = []
    cursor = 0
    while cursor < len(line):
        start = line.find("![", cursor)
        if start == -1:
            if cursor < len(line):
                parts.append(line[cursor:])
            break
        parsed = parse_image_at(line, start)
        if parsed is None:
            parts.append(line[cursor:])
            break
        token, end = parsed
        if start > cursor:
            parts.append(line[cursor:start])
        parts.append(token)
        cursor = end
    return parts


def normalize_image_lines(text: str) -> tuple[list[str | ImageToken], list[str]]:
    """Lift inline images into their own sequence items and report the repair."""
    items: list[str | ImageToken] = []
    repairs: list[str] = []
    lifted = 0
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            items.append(line)
            continue
        if in_fence:
            items.append(line)
            continue
        parts = split_inline_images(line)
        images = [part for part in parts if isinstance(part, ImageToken)]
        if not images:
            items.append(line)
            continue
        text_parts = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
        if text_parts:
            lifted += len(images)
        for part in parts:
            if isinstance(part, ImageToken):
                items.append(part)
            elif part.strip():
                items.append(part.strip())
    if lifted:
        repairs.append(f"lifted {lifted} inline image(s) into standalone positions")
    return items, repairs


def flush_block(sequence: list[BodyBlock | ImageToken | str], paragraph: list[str]) -> None:
    if paragraph:
        sequence.append(BodyBlock("paragraph", paragraph.copy()))
        paragraph.clear()


def scan_document(text: str) -> tuple[list[BodyBlock | ImageToken | str], list[str]]:
    """Scan Markdown into body blocks, image tokens, and divider sentinels."""
    sequence: list[BodyBlock | ImageToken | str] = []
    items, repairs = normalize_image_lines(strip_frontmatter(text))
    paragraph: list[str] = []
    code_lines: list[str] = []
    in_fence = False

    for item in items:
        if isinstance(item, ImageToken):
            flush_block(sequence, paragraph)
            sequence.append(item)
            continue
        line = item
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_fence:
                sequence.append(BodyBlock("code", code_lines.copy()))
                code_lines.clear()
                in_fence = False
            else:
                flush_block(sequence, paragraph)
                in_fence = True
            continue
        if in_fence:
            code_lines.append(line)
            continue
        if not stripped:
            flush_block(sequence, paragraph)
            continue
        if DIVIDER_RE.match(line):
            flush_block(sequence, paragraph)
            sequence.append("divider")
            continue
        heading = HEADING_RE.match(line)
        if heading:
            flush_block(sequence, paragraph)
            kind = "title" if len(heading.group(1)) == 1 else "heading"
            sequence.append(BodyBlock(kind, [heading.group(2)]))
            continue
        if stripped.startswith(">"):
            flush_block(sequence, paragraph)
            sequence.append(BodyBlock("quote", [stripped.lstrip("> ")]))
            continue
        if UNORDERED_RE.match(line) or ORDERED_RE.match(line):
            flush_block(sequence, paragraph)
            match = UNORDERED_RE.match(line) or ORDERED_RE.match(line)
            sequence.append(BodyBlock("list-item", [match.group(1)]))
            continue
        paragraph.append(line)

    flush_block(sequence, paragraph)
    if in_fence:
        sequence.append(BodyBlock("code", code_lines.copy()))
        repairs.append("closed one unterminated code fence at end of document")
    return sequence, repairs


def resolve_image(token: ImageToken, markdown_dir: Path) -> tuple[Path, bool]:
    """Resolve only the declared path and the document-local assets tree."""
    decoded = urllib.parse.unquote(urllib.parse.unquote(token.target)).replace("%20", " ")
    declared = Path(decoded).expanduser()
    if not declared.is_absolute():
        declared = markdown_dir / declared
    if declared.is_file():
        return declared.resolve(), True

    filename = Path(decoded).name
    direct_asset = markdown_dir / "assets" / filename
    if direct_asset.is_file():
        return direct_asset.resolve(), True
    assets = markdown_dir / "assets"
    if assets.is_dir():
        matches = sorted(path for path in assets.glob(f"*/{filename}") if path.is_file())
        if len(matches) == 1:
            return matches[0].resolve(), True
    return declared.resolve(strict=False), False


def title_from_filename(path: Path) -> str:
    value = re.sub(r"^\d{4}-\d{2}-\d{2}[-_ ]*", "", path.stem)
    value = re.sub(r"[-_]+", " ", value).strip()
    return value if len(value) > 3 else ""


def render_inline(value: str) -> str:
    escaped = html.escape(value, quote=True)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)

    def link(match: re.Match[str]) -> str:
        label, target = match.group(1), html.unescape(match.group(2))
        if not SAFE_LINK_RE.match(target):
            return label
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, escaped)


def render_html(blocks: list[BodyBlock]) -> str:
    rendered: list[str] = []
    list_buffer: list[str] = []

    def flush_list() -> None:
        if list_buffer:
            rendered.append("<ul>" + "".join(f"<li>{render_inline(item)}</li>" for item in list_buffer) + "</ul>")
            list_buffer.clear()

    for block in blocks:
        if block.kind == "list-item":
            list_buffer.append(block.source)
            continue
        flush_list()
        if block.kind in {"title", "heading"}:
            rendered.append(f"<h2>{render_inline(block.source)}</h2>")
        elif block.kind == "quote":
            rendered.append(f"<blockquote>{render_inline(block.source)}</blockquote>")
        elif block.kind == "code":
            code = "<br>".join(html.escape(line, quote=False) for line in block.lines)
            rendered.append(f"<blockquote><code>{code}</code></blockquote>")
        else:
            rendered.append(f"<p>{'<br>'.join(render_inline(line) for line in block.lines)}</p>")
    flush_list()
    return "".join(rendered)


def prepare_article(filepath: str) -> dict:
    path = Path(filepath).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Markdown file not found: {path}")
    if path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"Expected a Markdown file, got: {path.name}")

    sequence, repairs = scan_document(path.read_text(encoding="utf-8"))
    all_blocks = [item for item in sequence if isinstance(item, BodyBlock)]
    first_heading = next((item.source for item in all_blocks if item.kind in {"title", "heading"}), "")
    title = title_from_filename(path) or first_heading or "Untitled"

    images: list[dict] = []
    dividers: list[dict] = []
    visible_blocks: list[BodyBlock] = []
    title_removed = False
    for item in sequence:
        if isinstance(item, BodyBlock):
            if first_heading and not title_removed and item.kind == "title" and item.source == first_heading:
                title_removed = True
                continue
            visible_blocks.append(item)
            continue
        anchor = visible_blocks[-1].source if visible_blocks else ""
        if item == "divider":
            dividers.append({"block_index": len(visible_blocks), "after_text": anchor[-80:]})
            continue
        resolved, exists = resolve_image(item, path.parent)
        images.append(
            {
                "path": str(resolved),
                "original_path": item.target,
                "exists": exists,
                "alt": item.alt,
                "block_index": len(visible_blocks),
                "after_text": anchor[-80:],
                "text_before": anchor[:80],
                "text_after": "",
                "block_type": visible_blocks[-1].kind if visible_blocks else "document-start",
            }
        )

    for image in images:
        index = image["block_index"]
        image["text_after"] = visible_blocks[index].source[:80] if index < len(visible_blocks) else ""

    cover = images[0] if images else None
    content_images = images[1:]
    missing = [item for item in images if not item["exists"]]
    return {
        "title": title,
        "filename_title": title_from_filename(path),
        "content_title": first_heading,
        "cover_image": cover["path"] if cover else None,
        "cover_exists": cover["exists"] if cover else True,
        "content_images": content_images,
        "dividers": dividers,
        "html": render_html(visible_blocks),
        "total_blocks": len(visible_blocks),
        "source_file": str(path),
        "missing_images": len(missing),
        "errors_fixed": repairs,
        "expected_image_count": len(content_images),
    }


def locate_markdown(value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if candidate.is_dir():
        matches = sorted(candidate.glob("*.md")) + sorted(candidate.glob("*.markdown"))
        if len(matches) == 1:
            return matches[0].resolve()
        raise ValueError(f"Expected one Markdown file in {candidate}, found {len(matches)}")
    raise FileNotFoundError(f"Markdown input does not exist: {candidate}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Markdown for an X Articles draft")
    parser.add_argument("file", nargs="?", help="Markdown file or a directory containing exactly one Markdown file")
    parser.add_argument("--output", choices=("json", "html"), default="json")
    parser.add_argument("--html-only", action="store_true")
    args = parser.parse_args()

    input_value = os.environ.get("MARKDOWN_FILE") or args.file
    if not input_value:
        parser.error("provide a Markdown file or set MARKDOWN_FILE")
    try:
        result = prepare_article(str(locate_markdown(input_value)))
    except (FileNotFoundError, OSError, UnicodeError, ValueError) as error:
        print(f"parse_markdown: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    if args.html_only or args.output == "html":
        print(result["html"])
    else:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
