#!/usr/bin/env python3
from __future__ import annotations
"""
Markdown parser that prepares article data for X Articles publishing.

It pulls out:
- the article title (taken from the filename, or the first H1/H2 in the content)
- a cover image (the first image in the file)
- every content image together with a block index for accurate placement
- dividers (---) together with their block index for menu-based insertion
- the HTML body (with images and dividers removed)

Usage:
    python parse_markdown.py <markdown_file> [--output json|html] [--html-only]

Output (JSON):
{
    "title": "Sample Article",
    "cover_image": "/path/to/cover.png",
    "content_images": [
        {"path": "/path/to/image.png", "block_index": 5, "after_text": "nearby text..."},
        ...
    ],
    "dividers": [
        {"block_index": 9, "after_text": "nearby text..."},
        ...
    ],
    "html": "<p>Body...</p><h2>Heading</h2>...",
    "total_blocks": 30
}

block_index points at the block element (0-indexed) that the image or divider follows,
so placement stays accurate without depending on text matching.

Keep in mind: dividers go in through the X Articles Insert > Divider menu; HTML <hr> tags will not work.
"""

import argparse
import io
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

# 修正 Windows 控制台的 UTF-8 输出
# 避免中文路径与内容在 Windows 命令行里显示成乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# Fallback locations to check when an image is missing from its original path
SEARCH_DIRS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Pictures",
]


def find_image_in_assets(md_dir: Path, img_filename: str) -> str | None:
    """Look up an image inside the assets directory layout.

    Covers Obsidian-style asset folders, where a picture may sit at
    assets/<article_name>/<image_file> or directly at assets/<image_file>.

    Args:
        md_dir: directory where the markdown file lives
        img_filename: name of the image file to look for

    Returns:
        Absolute path when found, otherwise None
    """
    # Undo URL encoding on the filename
    img_filename = urllib.parse.unquote(img_filename)

    # Look through the assets subfolders first
    assets_dir = md_dir / "assets"
    if assets_dir.exists():
        for subdir in assets_dir.iterdir():
            if subdir.is_dir():
                candidate = subdir / img_filename
                if candidate.exists():
                    return str(candidate)
            elif subdir.name == img_filename:
                return str(subdir)

    # Fall back to the markdown file's own directory
    candidate = md_dir / img_filename
    if candidate.exists():
        return str(candidate)

    return None


def find_image_file(original_path: str, filename: str, md_dir: Path) -> tuple[str, bool]:
    """Locate an image file, falling back to common directories when the original path misses.

    Args:
        original_path: resolved absolute path taken from the markdown
        filename: bare filename used for the fallback search
        md_dir: directory where the markdown file lives

    Returns:
        (found_path, exists): the path to use plus a flag telling whether the file is really there
    """
    # Undo URL encoding, twice to catch double-encoded paths
    decoded_path = urllib.parse.unquote(urllib.parse.unquote(original_path))
    decoded_filename = urllib.parse.unquote(urllib.parse.unquote(filename))

    # Turn any leftover %20 into real spaces
    decoded_path = decoded_path.replace('%20', ' ')
    decoded_filename = decoded_filename.replace('%20', ' ')

    # 1. Try the decoded original path first
    if os.path.isfile(decoded_path):
        return decoded_path, True

    # 2. Then try the assets folder
    found_in_assets = find_image_in_assets(md_dir, decoded_filename)
    if found_in_assets:
        print(f"[parse_markdown] Found image in assets: {found_in_assets}", file=sys.stderr)
        return found_in_assets, True

    # 3. Finally scan the common fallback folders
    for search_dir in SEARCH_DIRS:
        candidate = search_dir / decoded_filename
        if candidate.is_file():
            print(f"[parse_markdown] Found image in {search_dir}: {decoded_filename}", file=sys.stderr)
            return str(candidate), True

    print(f"[parse_markdown] WARNING: Image not found: '{decoded_path}'", file=sys.stderr)
    return original_path, False


def clean_markdown_errors(markdown: str) -> tuple[str, list[str]]:
    """Repair frequent markdown formatting mistakes.

    Returns:
        (cleaned_markdown, fixed_error_descriptions)
    """
    errors_fixed = []

    # Pull images that share a line with text onto their own lines
    # Detect every image and check whether the line carries other content too
    count_extracted = 0
    lines = markdown.split('\n')
    new_lines = []

    img_pattern_inline = re.compile(r'!\[[^\]]*\]\(.+\)')

    for line in lines:
        # Collect all image matches on this line
        img_matches = list(img_pattern_inline.finditer(line))

        if not img_matches:
            # Line has no image: keep it untouched
            new_lines.append(line)
        elif len(img_matches) == 1 and line.strip() == img_matches[0].group(0):
            # The whole line is just one image: already fine
            new_lines.append(line)
        else:
            # The line mixes image(s) with text: split them apart
            # Cut the line at each image and rebuild it
            pos = 0
            for match in img_matches:
                # Emit any text that precedes the image
                before = line[pos:match.start()].strip()
                if before:
                    new_lines.append(before)
                # Then the image alone on its own line
                new_lines.append(match.group(0))
                pos = match.end()
                count_extracted += 1

            # Finally any text trailing the last image
            after = line[pos:].strip()
            if after:
                new_lines.append(after)

    markdown = '\n'.join(new_lines)

    if count_extracted > 0:
        errors_fixed.append(f"Extracted {count_extracted} inline image(s) to standalone lines")
        print(f"[parse_markdown] Extracted {count_extracted} inline images to standalone lines", file=sys.stderr)

    # Mend image references where the extension got duplicated: ![](path (1).jpeg).jpeg)
    # This covers repeated extensions even when the path itself contains parentheses
    # Greedy .+ matching so paths like "image (1).jpeg" still parse fully
    pattern1 = r'(!\[[^\]]*\]\((.+?)\.(\w+)\))\.\3\)'
    matches1 = re.findall(pattern1, markdown)
    if matches1:
        markdown = re.sub(pattern1, r'\1', markdown)
        errors_fixed.append(f"Fixed {len(matches1)} .ext).ext) format error(s)")
        print(f"[parse_markdown] Fixed .ext).ext) format errors: {len(matches1)}", file=sys.stderr)

    # Drop a surplus closing parenthesis: ![](path))
    # Greedy .+ matching keeps working when the path has parentheses
    pattern2 = r'(!\[[^\]]*\]\((.+)\))\)'
    matches2 = re.findall(pattern2, markdown)
    if matches2:
        markdown = re.sub(pattern2, r'\1', markdown)
        errors_fixed.append(f"Fixed {len(matches2)} extra parenthesis error(s)")
        print(f"[parse_markdown] Fixed extra closing parenthesis: {len(matches2)}", file=sys.stderr)

    # Collapse doubled extensions such as .jpeg.jpeg
    double_ext = re.findall(r'\.(jpe?g|png|gif|webp)\.\1', markdown, re.IGNORECASE)
    if double_ext:
        markdown = re.sub(r'\.(jpe?g|png|gif|webp)\.\1', r'.\1', markdown, flags=re.IGNORECASE)
        errors_fixed.append(f"Fixed {len(double_ext)} double extension(s)")

    # Spot image syntax that was never closed
    unclosed = re.findall(r'!\[[^\]]*\]\([^)]*$', markdown, re.MULTILINE)
    if unclosed:
        errors_fixed.append(f"WARNING: {len(unclosed)} unclosed image reference(s)")

    return markdown, errors_fixed


def extract_title_from_filename(filepath: str) -> str:
    """Derive the article title from the file name.

    The filename (minus its extension) wins over any H1 chapter heading
    found in the body, which keeps the two from being confused.

    Args:
        filepath: path of the markdown file

    Returns:
        Title taken from the file name
    """
    filename = os.path.basename(filepath)
    # Strip the extension
    title = os.path.splitext(filename)[0]
    # Tidy up frequent prefixes and suffixes
    title = re.sub(r'^\d{4}-?\d{2}-?\d{2}[-_]?', '', title)  # Drop a leading date
    title = title.strip('_- ')
    return title if title else "Untitled"


def split_into_blocks(markdown: str) -> list[str]:
    """Break markdown down into logical blocks: paragraphs, headings, quotes, code fences, and so on."""
    blocks = []
    current_block = []
    in_code_block = False
    code_block_lines = []

    lines = markdown.split('\n')

    for line in lines:
        stripped = line.strip()

        # Opening or closing fence of a code block
        if stripped.startswith('```'):
            if in_code_block:
                # Closing fence reached
                in_code_block = False
                if code_block_lines:
                    blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')
                code_block_lines = []
            else:
                # Opening fence reached
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                in_code_block = True
            continue

        # Inside a code block every line is collected verbatim
        if in_code_block:
            code_block_lines.append(line)
            continue

        # A blank line closes the current block
        if not stripped:
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            continue

        # A horizontal rule (divider) becomes a standalone block
        if re.match(r'^---+$', stripped):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append('___DIVIDER___')
            continue

        # Headings and blockquotes also stand alone as blocks
        if stripped.startswith(('#', '>')):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            continue

        # An image occupying a whole line is a block of its own
        if re.match(r'^!\[.*\]\(.*\)$', stripped):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
            blocks.append(stripped)
            continue

        current_block.append(line)

    if current_block:
        blocks.append('\n'.join(current_block))

    # Tidy up a code block that was never closed
    if code_block_lines:
        blocks.append('___CODE_BLOCK_START___' + '\n'.join(code_block_lines) + '___CODE_BLOCK_END___')

    return blocks


def extract_images_and_dividers(markdown: str, base_path: Path) -> tuple[list[dict], list[dict], str, int]:
    """Collect images and dividers together with the block index of each.

    Returns:
        (images, dividers, markdown_with_images_and_dividers_removed, total_blocks)
    """
    blocks = split_into_blocks(markdown)
    images = []
    dividers = []
    clean_blocks = []

    # .+ is greedy on purpose so paths like "image (1).jpeg" match fully
    img_pattern = re.compile(r'^!\[([^\]]*)\]\((.+)\)$')

    for i, block in enumerate(blocks):
        block_stripped = block.strip()

        # Divider block?
        if block_stripped == '___DIVIDER___':
            block_index = len(clean_blocks)
            after_text = ""
            if clean_blocks:
                prev_block = clean_blocks[-1].strip()
                lines = [l for l in prev_block.split('\n') if l.strip()]
                after_text = lines[-1][:80] if lines else ""
            dividers.append({
                "block_index": block_index,
                "after_text": after_text
            })
            continue

        match = img_pattern.match(block_stripped)
        if match:
            alt_text = match.group(1)
            img_path = match.group(2)

            # Undo URL encoding on the path
            img_path_decoded = urllib.parse.unquote(img_path)

            if not os.path.isabs(img_path_decoded):
                resolved_path = str(base_path / img_path_decoded)
            else:
                resolved_path = img_path_decoded

            filename = os.path.basename(img_path_decoded)
            full_path, exists = find_image_file(resolved_path, filename, base_path)

            block_index = len(clean_blocks)

            after_text = ""
            text_before = ""
            block_type = "paragraph"  # default

            if clean_blocks:
                prev_block = clean_blocks[-1].strip()
                lines = [l for l in prev_block.split('\n') if l.strip()]
                after_text = lines[-1][:80] if lines else ""

                # text_before holds the opening 50 characters of that block
                text_before = prev_block[:50]

                # Work out what kind of block it is
                if prev_block.startswith('#'):
                    if prev_block.startswith('# '):
                        block_type = "heading"
                    elif prev_block.startswith('## '):
                        block_type = "heading"
                elif prev_block.startswith('>'):
                    block_type = "blockquote"
                elif prev_block.startswith('- ') or prev_block.startswith('* '):
                    block_type = "list-item"
                else:
                    block_type = "paragraph"

            images.append({
                "path": full_path,
                "original_path": resolved_path,
                "exists": exists,
                "alt": alt_text,
                "block_index": block_index,
                "after_text": after_text,
                "text_before": text_before,
                "text_after": "",  # Filled in once the loop finishes
                "block_type": block_type
            })
        else:
            clean_blocks.append(block)

    # Backfill text_after with the block that follows each image's insertion point
    for img in images:
        next_block_index = img["block_index"] + 1
        if next_block_index < len(clean_blocks):
            next_block = clean_blocks[next_block_index].strip()
            img["text_after"] = next_block[:30]  # opening 30 characters of that next block
        else:
            img["text_after"] = ""  # there is no following block

    clean_markdown = '\n\n'.join(clean_blocks)
    return images, dividers, clean_markdown, len(clean_blocks)


def extract_title(markdown: str, use_h1: bool = False) -> tuple[str, str]:
    """Take the title from the first H1 or H2 heading, or the first non-empty line.

    Args:
        markdown: the markdown text
        use_h1: True to force the H1 as title (defaults to False, filename wins)

    Returns:
        (title, markdown_without_title): the title plus the markdown with the H1 title line stripped out.
    """
    lines = markdown.strip().split('\n')
    title = "Untitled"
    title_line_idx = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # H1: becomes the title and is flagged for removal
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            title_line_idx = idx
            break
        # H2: becomes the title but stays in place, since it is a section heading
        if stripped.startswith('## '):
            title = stripped[3:].strip()
            break
        # Otherwise the first non-empty line that is not an image
        if not stripped.startswith('!['):
            title = stripped[:100]
            break

    # Drop the H1 title line so it does not appear twice in the body
    if title_line_idx is not None:
        lines.pop(title_line_idx)
        markdown = '\n'.join(lines)

    return title, markdown


def markdown_to_html(markdown: str) -> str:
    """Render markdown as HTML suitable for pasting into the X Articles rich text editor."""
    html = markdown

    # Code blocks get converted before anything else
    def convert_code_block(match):
        code_content = match.group(1)
        lines = code_content.strip().split('\n')
        formatted = '<br>'.join(line for line in lines if line.strip())
        return f'<blockquote>{formatted}</blockquote>'

    html = re.sub(r'___CODE_BLOCK_START___(.*?)___CODE_BLOCK_END___', convert_code_block, html, flags=re.DOTALL)

    # Demote H1 to H2, since X Articles renders section headings as H2
    html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)

    # Headings
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Italic
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Blockquotes
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # Unordered lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Ordered lists
    html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Group runs of <li> items inside a <ul>
    html = re.sub(r'((?:<li>.*?</li>\n?)+)', r'<ul>\1</ul>', html)

    # Paragraphs
    parts = html.split('\n\n')
    processed_parts = []

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith(('<h2>', '<h3>', '<blockquote>', '<ul>', '<ol>')):
            processed_parts.append(part)
        else:
            part = part.replace('\n', '<br>')
            processed_parts.append(f'<p>{part}</p>')

    # Prepend a UTF-8 marker comment as an extra safeguard
    # The X Articles editor might drop <meta> tags; we still emit one as a matter of convention
    utf8_marker = '<!-- UTF-8 Encoding Marker -->\n'
    return utf8_marker + ''.join(processed_parts)


def parse_markdown_file(filepath: str) -> dict:
    """Parse one markdown file and hand back the structured result."""
    print(f"[parse_markdown] === Starting to parse: {filepath} ===", file=sys.stderr)

    path = Path(filepath)
    base_path = path.parent

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Repair formatting mistakes before anything else
    content, errors_fixed = clean_markdown_errors(content)
    if errors_fixed:
        for err in errors_fixed:
            print(f"[parse_markdown] {err}", file=sys.stderr)

    # Strip a YAML frontmatter block when one exists
    if content.startswith('---'):
        end_marker = content.find('---', 3)
        if end_marker != -1:
            content = content[end_marker + 3:].strip()

    # Title candidates: the file name (preferred) and the content's H1
    filename_title = extract_title_from_filename(filepath)
    content_title, content = extract_title(content)

    # Prefer the filename title when it looks meaningful; fall back to the content title
    if filename_title and filename_title != "Untitled" and len(filename_title) > 3:
        title = filename_title
    else:
        title = content_title

    # Pull out images and dividers, each with its block index
    images, dividers, clean_markdown, total_blocks = extract_images_and_dividers(content, base_path)

    # Render the body as HTML
    html = markdown_to_html(clean_markdown)

    cover_image = images[0]["path"] if images else None
    cover_exists = images[0]["exists"] if images else True
    content_images = images[1:] if len(images) > 1 else []

    missing = [img for img in images if not img["exists"]]
    if missing:
        print(f"[parse_markdown] WARNING: {len(missing)} image(s) not found", file=sys.stderr)

    # Emit detailed statistics
    print(f"[parse_markdown] === Image Statistics ===", file=sys.stderr)
    print(f"[parse_markdown] Total images found: {len(images)}", file=sys.stderr)
    print(f"[parse_markdown] - Cover image: {1 if cover_image else 0}", file=sys.stderr)
    print(f"[parse_markdown] - Content images: {len(content_images)}", file=sys.stderr)
    print(f"[parse_markdown] - Missing images: {len(missing)}", file=sys.stderr)

    # Report every content image together with its status
    for i, img in enumerate(content_images):
        status = "✓" if img['exists'] else "✗"
        img_name = Path(img['path']).name
        print(f"[parse_markdown] [{status}] Image {i+1}: {img_name}", file=sys.stderr)

    # Sanity-check the resolved image count against the markdown
    expected_count = len(re.findall(r'!\[[^\]]*\]\([^\)]+\)', content))
    actual_count = len(images)

    if expected_count != actual_count:
        print(f"[parse_markdown] WARNING: Image count mismatch!", file=sys.stderr)
        print(f"[parse_markdown]   Expected (from Markdown): {expected_count}", file=sys.stderr)
        print(f"[parse_markdown]   Actual (resolved): {actual_count}", file=sys.stderr)
        print(f"[parse_markdown]   Missing: {expected_count - actual_count}", file=sys.stderr)
    else:
        print(f"[parse_markdown] ✓ All {actual_count} images resolved successfully", file=sys.stderr)

    return {
        "title": title,
        "filename_title": filename_title,
        "content_title": content_title,
        "cover_image": cover_image,
        "cover_exists": cover_exists,
        "content_images": content_images,
        "dividers": dividers,
        "html": html,
        "total_blocks": total_blocks,
        "source_file": str(path.absolute()),
        "missing_images": len(missing),
        "errors_fixed": errors_fixed,
        "expected_image_count": len(content_images)
    }


def find_markdown_file(input_path: str) -> str:
    """
    智能定位 Markdown 文件。

    支持三种入参：
    1. 文件路径：直接返回
    2. 目录路径：列出目录下所有 .md 文件，唯一则返回，多个则报错并提示选择
    3. 关键词：在当前目录中搜索文件名包含关键词的 .md 文件

    Args:
        input_path: 可以是文件路径、目录路径或关键词

    Returns:
        匹配到的 Markdown 文件完整路径

    Raises:
        SystemExit: 找不到文件，或匹配结果不止一个时
    """
    import glob

    # 情形一：入参本身就是一个存在的文件
    if os.path.isfile(input_path):
        print(f"[parse_markdown] Found file directly: {input_path}", file=sys.stderr)
        return os.path.abspath(input_path)

    # 情形二：入参是目录
    if os.path.isdir(input_path):
        search_dir = input_path
        pattern = os.path.join(search_dir, "*.md")
        md_files = glob.glob(pattern)

        if len(md_files) == 0:
            print(f"Error: No .md files found in directory: {search_dir}", file=sys.stderr)
            sys.exit(1)
        elif len(md_files) == 1:
            print(f"[parse_markdown] Found single .md file in directory: {md_files[0]}", file=sys.stderr)
            return os.path.abspath(md_files[0])
        else:
            print(f"Error: Multiple .md files found in directory: {search_dir}", file=sys.stderr)
            print("Please specify which file to parse:", file=sys.stderr)
            for i, f in enumerate(md_files, 1):
                print(f"  {i}. {os.path.basename(f)}", file=sys.stderr)
            sys.exit(1)

    # 情形三：入参可能是关键词，也可能是个不存在的路径
    # 尝试在当前目录里按关键词搜索 .md 文件
    cwd = os.getcwd()
    all_md_files = glob.glob(os.path.join(cwd, "*.md"))

    # 先做整串关键词匹配（大小写不敏感）
    keyword = input_path.lower()
    matched_files = [f for f in all_md_files if keyword in os.path.basename(f).lower()]

    if len(matched_files) == 0:
        # 再尝试按空格拆成多个关键词分别匹配
        keywords = keyword.split()
        matched_files = [
            f for f in all_md_files
            if all(kw in os.path.basename(f).lower() for kw in keywords)
        ]

    if len(matched_files) == 0:
        print(f"Error: Cannot find file matching: {input_path}", file=sys.stderr)
        print(f"Searched in: {cwd}", file=sys.stderr)
        if all_md_files:
            print(f"Available .md files:", file=sys.stderr)
            for f in all_md_files[:5]:  # 只显示前5个
                print(f"  - {os.path.basename(f)}", file=sys.stderr)
        sys.exit(1)
    elif len(matched_files) == 1:
        print(f"[parse_markdown] Found file by keyword '{input_path}': {matched_files[0]}", file=sys.stderr)
        return os.path.abspath(matched_files[0])
    else:
        print(f"Error: Multiple files match keyword '{input_path}':", file=sys.stderr)
        for i, f in enumerate(matched_files, 1):
            print(f"  {i}. {os.path.basename(f)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Parse Markdown for X Articles')
    parser.add_argument('file', nargs='?', help='Markdown file path, directory, or keyword (or set MARKDOWN_FILE env variable)')
    parser.add_argument('--output', choices=['json', 'html'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--html-only', action='store_true',
                       help='Output only HTML content')

    args = parser.parse_args()

    # 输入来源优先级：环境变量高于命令行参数
    input_path = None
    if 'MARKDOWN_FILE' in os.environ:
        input_path = os.environ['MARKDOWN_FILE']
        print(f"[parse_markdown] Using input from MARKDOWN_FILE env: {input_path}", file=sys.stderr)
    elif args.file:
        input_path = args.file
    else:
        parser.error("Please provide markdown file via MARKDOWN_FILE environment variable or command line argument")

    # 按上面的规则定位文件
    markdown_file = find_markdown_file(input_path)

    result = parse_markdown_file(markdown_file)

    if args.html_only:
        print(result['html'])
    elif args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['html'])


if __name__ == '__main__':
    main()
