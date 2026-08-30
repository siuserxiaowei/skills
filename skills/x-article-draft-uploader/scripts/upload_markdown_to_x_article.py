#!/usr/bin/env python3
"""Create and verify an X Article draft from local Markdown; never publish it."""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as datetime_module
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


PARSER_DEFAULT = Path(__file__).with_name("parse_markdown.py")
IMAGE_LINE = re.compile(r"^!\[[^\]]*\]\([^\n]+\)\s*$")


class DraftError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImagePlan:
    order: int
    path: str
    anchor_candidates: list[str]
    source_line: int | None


def compact_text(value: str) -> str:
    value = re.sub(r"^#{1,6}\s+", "", value.strip())
    value = re.sub(r"^(?:[-+*]|\d+[.)、])\s+", "", value)
    return re.sub(r"\s+", " ", value).strip(" |`")


def leading_content(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    cursor = 0
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    if cursor < len(lines) and lines[cursor].strip() == "---":
        cursor += 1
        while cursor < len(lines) and lines[cursor].strip() != "---":
            cursor += 1
        cursor += cursor < len(lines)
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    value = lines[cursor].strip() if cursor < len(lines) else ""
    return {"line": cursor + 1 if value else None, "preview": value[:160], "is_image": bool(IMAGE_LINE.match(value))}


def run_parser(markdown: Path, script: Path) -> dict:
    environment = dict(os.environ)
    environment["MARKDOWN_FILE"] = str(markdown)
    process = subprocess.run(
        [sys.executable, str(script)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    if process.returncode:
        raise DraftError(process.stderr.strip() or f"Markdown parser exited {process.returncode}")
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise DraftError("Markdown parser did not return JSON") from exc
    required = {"title", "html", "cover_image", "content_images", "expected_image_count"}
    missing = sorted(required.difference(value))
    if missing:
        raise DraftError("Markdown parser omitted: " + ", ".join(missing))
    return value


def html_to_text(value: str) -> str:
    separated = re.sub(r"<(?:br\s*/?|/(?:p|div|h[1-6]|li|blockquote))>", "\n", value, flags=re.IGNORECASE)
    without_tags = re.sub(r"<[^>]+>", "", separated)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(without_tags)).strip()


def text_edges(value: str, length: int = 56) -> tuple[str, str]:
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized[:length], normalized[-length:] if normalized else ""


def line_for_image(lines: list[str], path: str) -> int | None:
    name = Path(path).name
    return next((number for number, line in enumerate(lines, start=1) if name in line), None)


def previous_prose(lines: list[str], line_number: int | None) -> list[str]:
    if line_number is None:
        return []
    candidates: list[str] = []
    for cursor in range(line_number - 2, -1, -1):
        value = compact_text(lines[cursor])
        if value and value != "---" and not IMAGE_LINE.match(lines[cursor].strip()):
            candidates.append(value)
            break
    return candidates


def image_plan(parsed: dict, markdown: Path, cover_in_body: bool) -> list[ImagePlan]:
    images = list(parsed["content_images"])
    if cover_in_body and parsed.get("cover_image"):
        images.insert(0, {"path": parsed["cover_image"], "text_before": "", "after_text": ""})
    lines = markdown.read_text(encoding="utf-8").splitlines()
    plans: list[ImagePlan] = []
    for order, item in enumerate(images, start=1):
        line = line_for_image(lines, item["path"])
        candidates = previous_prose(lines, line)
        for key in ("text_before", "after_text", "text_after"):
            for part in str(item.get(key) or "").splitlines():
                cleaned = compact_text(part)
                if cleaned and cleaned not in candidates:
                    candidates.append(cleaned)
        plans.append(ImagePlan(order, str(item["path"]), candidates, line))
    return plans


def load_storage_state(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("cookies")
    if not isinstance(value, list):
        raise DraftError("cookie file must be a Playwright storage-state object or cookie array")
    return value


async def optional_apply(page, seconds: float = 12) -> bool:
    deadline = asyncio.get_running_loop().time() + seconds
    button = page.locator('[data-testid="applyButton"]')
    while asyncio.get_running_loop().time() < deadline:
        if await button.count():
            try:
                await button.last.click(timeout=1500)
                return True
            except Exception:
                pass
        await page.wait_for_timeout(400)
    return False


async def paste_html(page, rich: str, plain: str, start: str, end: str) -> dict:
    return await page.evaluate(
        """async ({rich,plain,start,end}) => {
          const editor=document.querySelector('[data-testid="composer"]');
          if(!editor) return {ok:false,error:'composer missing'};
          editor.focus();
          const transfer=new DataTransfer();
          transfer.setData('text/html',rich); transfer.setData('text/plain',plain);
          editor.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:transfer}));
          await new Promise(resolve=>setTimeout(resolve,2500));
          const normalized=(editor.innerText||'').replace(/\s+/g,' ').trim();
          return {ok:true,length:normalized.length,start:!start||normalized.includes(start),end:!end||normalized.includes(end),marker:normalized.includes('MPH_MARKER')};
        }""",
        {"rich": rich, "plain": plain, "start": start, "end": end},
    )


async def find_anchor_block(page, candidates: list[str]):
    blocks = page.locator('[data-testid="composer"] .public-DraftStyleDefault-block')
    count = await blocks.count()
    normalized_candidates = [compact_text(value) for value in candidates if compact_text(value)]
    best = None
    for index in range(count):
        block = blocks.nth(index)
        text = compact_text(await block.inner_text())
        if not text:
            continue
        for candidate in normalized_candidates:
            score = 3 if text == candidate else 2 if len(candidate) >= 8 and candidate in text else 1 if len(text) >= 8 and text in candidate else 0
            if score and (best is None or score > best[0]):
                best = (score, block, candidate, text)
    return best


async def paste_image(page, path: Path) -> None:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    result = await page.evaluate(
        """async ({encoded,mime,name}) => {
          const editor=document.querySelector('[data-testid="composer"]');
          if(!editor) return false;
          const bytes=Uint8Array.from(atob(encoded), value=>value.charCodeAt(0));
          const transfer=new DataTransfer(); transfer.items.add(new File([bytes],name,{type:mime}));
          editor.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true,clipboardData:transfer}));
          await new Promise(resolve=>setTimeout(resolve,2000)); return true;
        }""",
        {"encoded": encoded, "mime": mime, "name": path.name},
    )
    if not result:
        raise DraftError(f"could not paste image: {path}")


async def visible_media_count(page) -> int:
    return await page.evaluate(
        """() => [...document.images].filter(image => {
          const box=image.getBoundingClientRect();
          return box.width>=80 && box.height>=40 && !image.src.includes('profile_images') && !image.src.includes('/emoji/');
        }).length"""
    )


async def wait_media_growth(page, before: int, timeout_seconds: float = 60) -> int:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    current = before
    while asyncio.get_running_loop().time() < deadline:
        await page.wait_for_timeout(1500)
        current = await visible_media_count(page)
        if current > before:
            return current
    return current


async def create_draft(args: argparse.Namespace, parsed: dict, plans: list[ImagePlan], output: Path) -> dict:
    from playwright.async_api import async_playwright

    plain = html_to_text(parsed["html"])
    beginning, ending = text_edges(plain)
    cookies = load_storage_state(args.cookies)
    output.mkdir(parents=True, exist_ok=False)
    async with async_playwright() as engine:
        browser = await engine.chromium.launch(headless=args.headless)
        context = await browser.new_context(viewport={"width": 1440, "height": 1100}, locale="zh-CN")
        await context.add_cookies(cookies)
        page = await context.new_page()
        page.set_default_timeout(60_000)
        await page.goto("https://x.com/compose/articles", wait_until="domcontentloaded")
        await page.wait_for_timeout(3500)
        if "login" in page.url:
            raise DraftError("X session is not authenticated")
        create_button = page.locator('button[aria-label="create"]')
        if not await create_button.count():
            raise DraftError("create-article control was not found")
        await create_button.first.click()
        await page.wait_for_url(re.compile(r"/compose/articles/edit/"), timeout=45_000)
        draft_url = page.url
        (output / "draft-url.txt").write_text(draft_url + "\n", encoding="utf-8")
        title_box = page.locator('textarea[placeholder="添加标题"]')
        await title_box.wait_for()
        cover_uploaded = False
        if parsed.get("cover_image") and not args.no_cover:
            file_inputs = page.locator('input[type="file"][accept*="image"]')
            await file_inputs.first.set_input_files(parsed["cover_image"])
            await optional_apply(page)
            await page.wait_for_timeout(2500)
            cover_uploaded = True
        await title_box.fill(args.title or parsed["title"])
        body = await paste_html(page, parsed["html"], plain, beginning, ending)
        if not body.get("ok") or not body.get("start") or not body.get("end") or body.get("marker"):
            raise DraftError("body paste did not pass beginning/end verification")
        inserted = []
        for plan in reversed(plans):
            if not Path(plan.path).is_file():
                raise DraftError(f"image is missing: {plan.path}")
            anchor = await find_anchor_block(page, plan.anchor_candidates)
            if anchor is None:
                raise DraftError(f"no editor anchor for image {plan.order}: {Path(plan.path).name}")
            _, block, candidate, visible = anchor
            box = await block.bounding_box()
            if box is None:
                raise DraftError(f"editor anchor became unavailable for image {plan.order}: {Path(plan.path).name}")
            await block.click(position={"x": max(1, box["width"] - 3), "y": max(1, box["height"] / 2)})
            await page.keyboard.press("End")
            await page.keyboard.press("Enter")
            before = await visible_media_count(page)
            await paste_image(page, Path(plan.path))
            await optional_apply(page, 3)
            after = await wait_media_growth(page, before)
            if after <= before:
                raise DraftError(f"image insertion was not observed: {Path(plan.path).name}")
            inserted.append({"order": plan.order, "file": Path(plan.path).name, "candidate": candidate, "visible_block": visible})
        await page.wait_for_timeout(12_000)
        final = await page.evaluate(
            """({beginning,ending}) => {
              const editor=document.querySelector('[data-testid="composer"]');
              const title=document.querySelector('textarea[placeholder="添加标题"]')?.value||'';
              const value=(editor?.innerText||'').replace(/\s+/g,' ').trim();
              return {title,text_length:value.length,beginning:!beginning||value.includes(beginning),ending:!ending||value.includes(ending),marker:value.includes('MPH_MARKER'),page_text:document.body.innerText.slice(-600)};
            }""",
            {"beginning": beginning, "ending": ending},
        )
        final.update({"draft_url": draft_url, "cover_uploaded": cover_uploaded, "inserted": inserted, "media_count": await visible_media_count(page), "published": False})
        await page.screenshot(path=str(output / "draft.png"), full_page=True)
        (output / "result.json").write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        await browser.close()
    expected_title = args.title or parsed["title"]
    if final["title"] != expected_title or not final["beginning"] or not final["ending"] or final["marker"]:
        raise DraftError("final draft verification failed")
    return final


def default_output() -> Path:
    label = datetime_module.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    return Path.cwd() / "x-article-runs" / label


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--cookies", type=Path, required=True)
    parser.add_argument("--parser", type=Path, default=PARSER_DEFAULT)
    parser.add_argument("--title")
    parser.add_argument("--no-cover", action="store_true", help="continue only when the user explicitly accepts no cover")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    markdown = args.markdown.expanduser().resolve(strict=False)
    if not markdown.is_file():
        parser.error(f"Markdown file is missing: {markdown}")
    first = leading_content(markdown)
    parsed = run_parser(markdown, args.parser.expanduser().resolve(strict=False))
    if not first["is_image"] and not args.no_cover:
        raise DraftError(f"first content line is not an image (line {first['line']}): {first['preview']!r}; use --no-cover only after user approval")
    cover_in_body = args.no_cover and bool(parsed.get("cover_image"))
    plans = image_plan(parsed, markdown, cover_in_body)
    if args.no_cover:
        parsed["cover_image"] = None
    preview = {
        "title": args.title or parsed["title"],
        "first_content": first,
        "cover": parsed.get("cover_image"),
        "body_images": [asdict(plan) for plan in plans],
        "creates_draft": args.apply,
        "publishes": False,
    }
    print(json.dumps(preview, ensure_ascii=False, indent=2))
    if not args.apply:
        return 0
    output = (args.output or default_output()).expanduser().resolve(strict=False)
    result = asyncio.run(create_draft(args, parsed, plans, output))
    print(json.dumps({"draft_url": result["draft_url"], "output": str(output), "published": False}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DraftError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(2)
