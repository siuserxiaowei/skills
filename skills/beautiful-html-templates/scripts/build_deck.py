#!/usr/bin/env python3
"""Validate a deck JSON spec and build one self-contained HTML presentation."""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


LAYOUTS = {"cover", "section", "bullets", "two-column", "metrics", "quote", "image", "closing"}
FONT_PAIRS = {
    "modern": ('ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'),
    "editorial": ('ui-serif, Georgia, Cambria, "Times New Roman", serif', 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'),
    "technical": ('ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'),
    "humanist": ('Optima, Candara, "Noto Sans", system-ui, sans-serif', 'Optima, Candara, "Noto Sans", system-ui, sans-serif'),
    "system": ('system-ui, sans-serif', 'system-ui, sans-serif'),
}
DEFAULT_THEME = {
    "font_pair": "modern",
    "background": "#f5f6f8",
    "panel": "#ffffff",
    "text": "#16191f",
    "muted": "#505966",
    "accent": "#174f91",
    "line": "#b9c2cc",
}
RIGHTS = {"user-provided", "original", "open-license", "licensed", "public-domain"}
RTL_LANGUAGES = {"ar", "fa", "he", "ur"}
LANGUAGE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
SEVERITY = {"error": 2, "warning": 1}


def finding(rule: str, severity: str, path: str, message: str) -> dict[str, str]:
    return {"rule_id": rule, "severity": severity, "path": path, "message": message}


def text_value(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def srgb_channel(value: int) -> float:
    component = value / 255
    return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4


def luminance(color: str) -> float:
    red, green, blue = (int(color[index:index + 2], 16) for index in (1, 3, 5))
    return 0.2126 * srgb_channel(red) + 0.7152 * srgb_channel(green) + 0.0722 * srgb_channel(blue)


def contrast(first: str, second: str) -> float:
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def safe_image(root: Path, raw: Any, max_bytes: int, path_label: str, findings: list[dict[str, str]]) -> tuple[Path, str] | None:
    if not text_value(raw):
        findings.append(finding("image-path", "error", path_label, "image path must be a non-empty string"))
        return None
    relative = Path(str(raw))
    if relative.is_absolute() or ".." in relative.parts:
        findings.append(finding("image-path", "error", path_label, "image path must stay inside the spec directory"))
        return None
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            findings.append(finding("image-symlink", "error", path_label, "image path must not contain a symbolic link"))
            return None
    try:
        cursor.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        findings.append(finding("image-path", "error", path_label, "image resolves outside the spec directory"))
        return None
    if not cursor.is_file():
        findings.append(finding("image-missing", "error", path_label, "image file does not exist"))
        return None
    size = cursor.stat().st_size
    if size > max_bytes:
        findings.append(finding("image-size", "error", path_label, f"image exceeds {max_bytes} bytes"))
        return None
    with cursor.open("rb") as handle:
        head = handle.read(16)
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif head.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        findings.append(finding("image-format", "error", path_label, "image must contain PNG, JPEG, or WebP bytes"))
        return None
    return cursor, mime


def validate_source_records(slide: dict[str, Any], label: str, findings: list[dict[str, str]]) -> None:
    sources = slide.get("sources", [])
    if not isinstance(sources, list):
        findings.append(finding("sources", "error", label, "sources must be a list"))
        return
    for index, source in enumerate(sources):
        source_label = f"{label}.sources[{index}]"
        if not isinstance(source, dict) or not text_value(source.get("label")):
            findings.append(finding("source-label", "error", source_label, "source needs a non-empty label"))
            continue
        url = source.get("url")
        if url is not None and (not text_value(url) or not re.match(r"^https?://", str(url), re.I)):
            findings.append(finding("source-url", "error", source_label, "source URL must use HTTP or HTTPS"))
        if source.get("current") is True and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(source.get("as_of", ""))):
            findings.append(finding("source-date", "error", source_label, "current source needs an as_of date in YYYY-MM-DD form"))


def validate_spec(spec_path: Path, max_image_bytes: int = 10_000_000) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []
    spec_path = spec_path.resolve()
    try:
        raw = spec_path.read_text(encoding="utf-8")
        spec = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "findings": [finding("spec-readable", "error", str(spec_path), str(exc))], "summary": {"error": 1, "warning": 0}, "inventory": []}
    if not isinstance(spec, dict):
        return {"ok": False, "findings": [finding("spec-shape", "error", ".", "spec root must be an object")], "summary": {"error": 1, "warning": 0}, "inventory": []}
    if spec.get("version") != 1:
        findings.append(finding("spec-version", "error", ".", "version must be 1"))
    if not text_value(spec.get("title")):
        findings.append(finding("deck-title", "error", ".", "title must be a non-empty string"))
    language = spec.get("language")
    if not isinstance(language, str) or not LANGUAGE.fullmatch(language):
        findings.append(finding("deck-language", "error", ".", "language must be a BCP 47-style tag"))
    direction = spec.get("direction")
    if direction is not None and direction not in {"ltr", "rtl"}:
        findings.append(finding("deck-direction", "error", ".", "direction must be ltr or rtl"))
    meta = spec.get("meta")
    if not isinstance(meta, dict):
        findings.append(finding("deck-meta", "error", ".", "meta must be an object"))
    else:
        for key in ("audience", "occasion", "outcome"):
            if not text_value(meta.get(key)):
                findings.append(finding(f"meta-{key}", "error", ".", f"meta.{key} must be a non-empty string"))

    theme = {**DEFAULT_THEME}
    supplied_theme = spec.get("theme", {})
    if not isinstance(supplied_theme, dict):
        findings.append(finding("theme", "error", ".", "theme must be an object"))
    else:
        unknown = set(supplied_theme) - set(DEFAULT_THEME)
        for key in sorted(unknown):
            findings.append(finding("theme-key", "error", f"theme.{key}", "unknown theme token"))
        theme.update({key: value for key, value in supplied_theme.items() if key in DEFAULT_THEME})
    if theme.get("font_pair") not in FONT_PAIRS:
        findings.append(finding("theme-font", "error", "theme.font_pair", f"font_pair must be one of {sorted(FONT_PAIRS)}"))
    for key in ("background", "panel", "text", "muted", "accent", "line"):
        if not isinstance(theme.get(key), str) or not HEX.fullmatch(theme[key]):
            findings.append(finding("theme-color", "error", f"theme.{key}", "color must be six-digit sRGB hex"))
    if not any(item["rule_id"] == "theme-color" for item in findings):
        for foreground, background, minimum in (("text", "background", 4.5), ("text", "panel", 4.5), ("muted", "background", 4.5), ("accent", "background", 4.5), ("accent", "panel", 4.5)):
            ratio = contrast(theme[foreground], theme[background])
            if ratio < minimum:
                findings.append(finding("theme-contrast", "error", f"theme.{foreground}", f"{foreground}/{background} contrast is {ratio:.2f}:1; requires {minimum:.1f}:1"))

    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        findings.append(finding("slides", "error", ".", "slides must be a non-empty list"))
        slides = []
    elif len(slides) > 50:
        findings.append(finding("slide-count", "error", ".", "slide count must not exceed 50"))
    for index, slide in enumerate(slides):
        label = f"slides[{index}]"
        if not isinstance(slide, dict):
            findings.append(finding("slide-shape", "error", label, "slide must be an object"))
            continue
        layout = slide.get("layout")
        if layout not in LAYOUTS:
            findings.append(finding("slide-layout", "error", label, f"layout must be one of {sorted(LAYOUTS)}"))
            continue
        if not text_value(slide.get("title")):
            findings.append(finding("slide-title", "error", label, "every slide needs a non-empty title"))
        elif len(slide["title"]) > 90:
            findings.append(finding("slide-title-length", "warning", label, "title exceeds 90 characters; inspect fit at every target viewport"))
        if "notes" in slide and not isinstance(slide["notes"], str):
            findings.append(finding("slide-notes", "error", label, "notes must be a string"))
        if layout == "bullets":
            items = slide.get("items")
            if not isinstance(items, list) or not 1 <= len(items) <= 6 or not all(text_value(item) for item in items):
                findings.append(finding("bullet-items", "error", label, "bullets layout needs 1–6 non-empty string items"))
            elif any(len(item) > 180 for item in items):
                findings.append(finding("bullet-length", "warning", label, "a bullet exceeds 180 characters; move detail to notes or another slide"))
        elif layout == "two-column":
            columns = slide.get("columns")
            if not isinstance(columns, list) or len(columns) != 2:
                findings.append(finding("columns", "error", label, "two-column layout needs exactly two columns"))
            else:
                for column_index, column in enumerate(columns):
                    column_label = f"{label}.columns[{column_index}]"
                    if not isinstance(column, dict) or not text_value(column.get("heading")):
                        findings.append(finding("column-heading", "error", column_label, "column needs a heading"))
                        continue
                    body = text_value(column.get("body"))
                    items = column.get("items")
                    item_list = isinstance(items, list) and 1 <= len(items) <= 4 and all(text_value(item) for item in items)
                    if body == item_list:
                        findings.append(finding("column-content", "error", column_label, "column needs exactly one of body or 1–4 items"))
        elif layout == "metrics":
            metrics = slide.get("metrics")
            if not isinstance(metrics, list) or not 1 <= len(metrics) <= 4:
                findings.append(finding("metrics", "error", label, "metrics layout needs 1–4 metrics"))
            else:
                for metric_index, metric in enumerate(metrics):
                    if not isinstance(metric, dict) or not text_value(metric.get("value")) or not text_value(metric.get("label")):
                        findings.append(finding("metric-record", "error", f"{label}.metrics[{metric_index}]", "metric needs value and label"))
        elif layout == "quote":
            if not text_value(slide.get("quote")) or not text_value(slide.get("attribution")):
                findings.append(finding("quote", "error", label, "quote layout needs quote and attribution"))
            elif len(slide["quote"]) > 300:
                findings.append(finding("quote-length", "warning", label, "quote exceeds 300 characters; inspect projected legibility"))
        elif layout == "image":
            image = slide.get("image")
            if not isinstance(image, dict):
                findings.append(finding("image", "error", label, "image layout needs an image object"))
            else:
                image_label = f"{label}.image"
                resolved = safe_image(spec_path.parent, image.get("path"), max_image_bytes, image_label, findings)
                if resolved:
                    path, mime = resolved
                    inventory.append({"path": str(image["path"]), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mime": mime})
                if not text_value(image.get("alt")):
                    findings.append(finding("image-alt", "error", image_label, "image needs identifying alt text"))
                if image.get("rights") not in RIGHTS:
                    findings.append(finding("image-rights", "error", image_label, "image needs a supported rights record"))
                if image.get("rights") in {"open-license", "licensed", "public-domain"} and not text_value(image.get("source")):
                    findings.append(finding("image-source", "error", image_label, "third-party image needs its source"))
                if image.get("rights") in {"open-license", "licensed"} and not text_value(image.get("license")):
                    findings.append(finding("image-license", "error", image_label, "licensed image needs its license or permission record"))
                if not text_value(image.get("description")):
                    findings.append(finding("image-description", "error", image_label, "image needs a visible detailed description"))
        validate_source_records(slide, label, findings)

    findings.sort(key=lambda item: (-SEVERITY[item["severity"]], item["path"], item["rule_id"]))
    counts = Counter(item["severity"] for item in findings)
    return {
        "ok": counts["error"] == 0,
        "spec": spec,
        "theme": theme,
        "summary": {level: counts[level] for level in ("error", "warning")},
        "findings": findings,
        "inventory": sorted(inventory, key=lambda item: item["path"]),
        "spec_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "limitations": [
            "Validation does not render a browser, test assistive technology, verify factual truth, or prove asset ownership.",
            "Content-length and contrast checks are preflight evidence, not proof of projected fit or WCAG conformance.",
        ],
    }


def inline_text(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def render_list(items: list[str]) -> str:
    return "<ul class=\"bullet-list\">" + "".join(f"<li>{inline_text(item)}</li>" for item in items) + "</ul>"


def render_sources(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return ""
    items = []
    for source in sources:
        label = inline_text(source["label"])
        if source.get("url"):
            label = f'<a href="{inline_text(source["url"])}">{label}</a>'
        suffix = f" · {inline_text(source['as_of'])}" if source.get("as_of") else ""
        items.append(f"<li>{label}{suffix}</li>")
    return '<footer class="sources" aria-label="Sources"><ol>' + "".join(items) + "</ol></footer>"


def image_data(spec_root: Path, image: dict[str, Any]) -> str:
    path = spec_root / image["path"]
    with path.open("rb") as handle:
        data = handle.read()
    if data.startswith(b"\x89PNG"):
        mime = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    else:
        mime = "image/webp"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def render_slide(slide: dict[str, Any], index: int, total: int, spec_root: Path) -> str:
    layout = slide["layout"]
    heading_id = f"slide-{index + 1}-title"
    eyebrow = f'<p class="eyebrow">{inline_text(slide.get("eyebrow"))}</p>' if slide.get("eyebrow") else ""
    title = f'<h2 id="{heading_id}">{inline_text(slide["title"])}</h2>'
    if layout == "cover":
        body = f"{eyebrow}{title}"
        if slide.get("subtitle"):
            body += f'<p class="lede">{inline_text(slide["subtitle"])}</p>'
        if slide.get("byline"):
            body += f'<p class="byline">{inline_text(slide["byline"])}</p>'
    elif layout == "section":
        body = f"{eyebrow}{title}"
        if slide.get("body"):
            body += f'<p class="lede">{inline_text(slide["body"])}</p>'
    elif layout == "bullets":
        body = f"{eyebrow}{title}{render_list(slide['items'])}"
    elif layout == "two-column":
        columns = []
        for column in slide["columns"]:
            content = f'<h3>{inline_text(column["heading"])}</h3>'
            content += f'<p>{inline_text(column["body"])}</p>' if column.get("body") else render_list(column["items"])
            columns.append(f'<section class="column">{content}</section>')
        body = f"{eyebrow}{title}<div class=\"columns\">{''.join(columns)}</div>"
    elif layout == "metrics":
        cards = []
        for metric in slide["metrics"]:
            detail = f'<p>{inline_text(metric["detail"])}</p>' if metric.get("detail") else ""
            cards.append(f'<section class="metric"><strong>{inline_text(metric["value"])}</strong><h3>{inline_text(metric["label"])}</h3>{detail}</section>')
        body = f"{eyebrow}{title}<div class=\"metrics\">{''.join(cards)}</div>"
    elif layout == "quote":
        body = f'{eyebrow}{title}<figure class="quotation"><blockquote>{inline_text(slide["quote"])}</blockquote><figcaption>{inline_text(slide["attribution"])}</figcaption></figure>'
    elif layout == "image":
        image = slide["image"]
        source = f' · {inline_text(image["source"])}' if image.get("source") else ""
        caption = f'<figcaption>{inline_text(slide.get("caption", ""))}{source}</figcaption>'
        body = f'{eyebrow}{title}<figure class="image-figure"><img src="{image_data(spec_root, image)}" alt="{inline_text(image["alt"])}">{caption}</figure><div class="image-description"><h3>Figure description</h3><p>{inline_text(image["description"])}</p></div>'
    else:
        body = f"{eyebrow}{title}"
        if slide.get("body"):
            body += f'<p class="lede">{inline_text(slide["body"])}</p>'
        if slide.get("action"):
            body += f'<p class="action">{inline_text(slide["action"])}</p>'
    sources = render_sources(slide.get("sources", []))
    return f'<section class="slide layout-{layout}" role="group" aria-roledescription="slide" aria-labelledby="{heading_id}" data-slide="{index + 1}"><div class="slide-content">{body}</div>{sources}<p class="slide-number" aria-hidden="true">{index + 1:02d} / {total:02d}</p></section>'


CSS = r"""
:root{color-scheme:light;--bg:THEME_BG;--panel:THEME_PANEL;--text:THEME_TEXT;--muted:THEME_MUTED;--accent:THEME_ACCENT;--line:THEME_LINE;--display:THEME_DISPLAY;--body:THEME_BODY;--mono:ui-monospace,"SFMono-Regular",Consolas,monospace}
*{box-sizing:border-box}html{background:var(--bg);color:var(--text);font-family:var(--body);line-height:1.45}body{margin:0;min-height:100dvh}.skip-link{position:fixed;inset-block-start:.75rem;inset-inline-start:-999rem;z-index:20;background:var(--panel);color:var(--text);padding:.7rem 1rem;border:2px solid var(--accent)}.skip-link:focus{inset-inline-start:.75rem}.deck-shell{min-height:100dvh;display:grid;grid-template-rows:auto 1fr}.controls{display:flex;align-items:center;justify-content:center;gap:.65rem;padding:.7rem;background:var(--panel);border-block-end:1px solid var(--line);font-family:var(--body);position:relative;z-index:5}.controls button{min-width:2.75rem;min-height:2.5rem;border:1px solid var(--line);border-radius:.35rem;background:var(--panel);color:var(--text);font:inherit;cursor:pointer}.controls button:hover{border-color:var(--accent)}.controls button:focus-visible,.slide a:focus-visible,.speaker-notes button:focus-visible{outline:.2rem solid var(--accent);outline-offset:.15rem}.controls button:disabled{opacity:.45;cursor:not-allowed}.progress{min-width:6rem;text-align:center;font-variant-numeric:tabular-nums}.slides{display:grid;place-items:center;min-height:0;padding:1rem}.slide{position:relative;isolation:isolate;display:grid;grid-template-rows:1fr auto;width:min(96vw,calc((100dvh - 6.5rem)*1.7778));aspect-ratio:16/9;background:var(--bg);border:1px solid var(--line);box-shadow:0 1.25rem 3rem rgb(0 0 0 / .12);overflow:auto;padding:clamp(1.4rem,4.2vw,4.6rem);container-type:inline-size}.js .slide[hidden]{display:none}.slide::before{content:"";position:absolute;inset-block-start:0;inset-inline-start:0;width:clamp(.45rem,1.2vw,.9rem);height:100%;background:var(--accent);z-index:-1}.slide-content{align-self:center;max-width:100%}.eyebrow{margin:0 0 .8rem;color:var(--accent);font:700 clamp(.78rem,1.5cqw,1rem)/1.2 var(--mono);letter-spacing:.09em;text-transform:uppercase}.slide h2{max-width:18ch;margin:0 0 clamp(1rem,2.4cqw,2rem);font:700 clamp(2rem,6.1cqw,5.5rem)/.98 var(--display);letter-spacing:-.035em;text-wrap:balance}.layout-cover h2,.layout-section h2,.layout-closing h2{max-width:14ch;font-size:clamp(2.7rem,8.2cqw,7.2rem)}.lede{max-width:54ch;margin:0 0 1.25rem;color:var(--muted);font-size:clamp(1.05rem,2cqw,1.65rem)}.byline,.action{margin-block-start:2rem;font-weight:700}.bullet-list{display:grid;gap:clamp(.65rem,1.5cqw,1.2rem);max-width:62rem;margin:0;padding-inline-start:1.4em;font-size:clamp(1.05rem,2.05cqw,1.65rem)}.bullet-list li::marker{color:var(--accent)}.columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(1rem,2.5cqw,2.25rem)}.column,.metric{background:var(--panel);border:1px solid var(--line);border-block-start:.35rem solid var(--accent);padding:clamp(1rem,2.2cqw,2rem)}.column h3,.metric h3,.image-description h3{margin:0 0 .7rem;font-size:clamp(1.1rem,2cqw,1.55rem)}.column p,.column li,.metric p{font-size:clamp(.95rem,1.55cqw,1.25rem)}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:clamp(.8rem,1.8cqw,1.5rem)}.metric strong{display:block;color:var(--accent);font:700 clamp(2.3rem,5.5cqw,5rem)/1 var(--display)}.quotation{max-width:58rem;margin:0}.quotation blockquote{margin:0;color:var(--text);font:600 clamp(1.8rem,4.5cqw,4rem)/1.12 var(--display)}.quotation figcaption{margin-block-start:1.4rem;color:var(--muted);font-weight:700}.image-figure{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(12rem,.5fr);gap:1rem;align-items:end;margin:0}.image-figure img{display:block;width:100%;max-height:48vh;object-fit:contain;background:var(--panel)}.image-figure figcaption,.image-description,.sources{color:var(--muted);font-size:clamp(.76rem,1.15cqw,.95rem)}.image-description{margin-block-start:1rem;max-width:72ch}.image-description h3{color:var(--text);margin-block-end:.2rem}.image-description p{margin:0}.sources{align-self:end;margin-block-start:1.25rem;padding-block-start:.65rem;border-block-start:1px solid var(--line)}.sources ol{display:flex;flex-wrap:wrap;gap:.35rem 1rem;margin:0;padding:0;list-style-position:inside}.sources a{color:var(--accent)}.slide-number{position:absolute;inset-inline-end:1.2rem;inset-block-end:.7rem;margin:0;color:var(--muted);font:700 .78rem/1 var(--mono)}.speaker-notes{position:fixed;inset:auto 1rem 1rem auto;z-index:10;width:min(34rem,calc(100vw - 2rem));max-height:55vh;overflow:auto;background:var(--panel);border:2px solid var(--accent);box-shadow:0 1rem 3rem rgb(0 0 0 / .2);padding:1.25rem}.speaker-notes h2{font:700 1.25rem var(--display);margin:0 2rem .6rem 0}.speaker-notes p{white-space:pre-wrap}.speaker-notes button{position:absolute;inset-block-start:.6rem;inset-inline-end:.6rem;border:1px solid var(--line);background:var(--panel);color:var(--text);font:inherit}.noscript{padding:.8rem;background:var(--panel);border-block-end:1px solid var(--line);text-align:center}
@media(max-width:43rem),(max-height:34rem){.deck-shell{display:block}.controls{position:sticky;top:0}.slides{display:block;padding:0}.slide{width:100%;min-height:calc(100dvh - 4rem);aspect-ratio:auto;border:0;border-block-end:1px solid var(--line);box-shadow:none;padding:3.2rem 1.25rem 2.5rem;overflow:visible}.js .slide:not([hidden]){display:grid}.columns,.image-figure{grid-template-columns:1fr}.slide h2,.layout-cover h2,.layout-section h2,.layout-closing h2{font-size:clamp(2rem,12vw,4rem)}.image-figure img{max-height:45vh}.sources ol{display:block}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}
@page{size:13.333in 7.5in;margin:0}@media print{html,body{background:#fff}.deck-shell{display:block}.controls,.skip-link,.speaker-notes,.noscript{display:none!important}.slides{display:block;padding:0}.slide,.js .slide[hidden]{display:grid!important;width:13.333in;height:7.5in;aspect-ratio:auto;border:0;box-shadow:none;overflow:hidden;break-after:page;page-break-after:always}.slide:last-child{break-after:auto;page-break-after:auto}}
"""


JS = r"""
document.documentElement.classList.add('js');
const slides=[...document.querySelectorAll('.slide')];
const previous=document.querySelector('#previous');
const next=document.querySelector('#next');
const status=document.querySelector('#deck-status');
const notesButton=document.querySelector('#notes-button');
const notesPanel=document.querySelector('#notes-panel');
const notesText=document.querySelector('#notes-text');
const notes=NOTES_JSON;
let current=0;
const hashIndex=()=>{const match=location.hash.match(/^#slide-(\d+)$/);return match?Math.min(slides.length-1,Math.max(0,Number(match[1])-1)):0};
function show(index,{announce=true}={}){current=Math.min(slides.length-1,Math.max(0,index));slides.forEach((slide,i)=>{slide.hidden=i!==current});previous.disabled=current===0;next.disabled=current===slides.length-1;status.textContent=`${current+1} / ${slides.length}`;history.replaceState(null,'',`#slide-${current+1}`);notesText.textContent=notes[current]||'No notes for this slide.';if(announce){status.setAttribute('aria-live','polite')}}
function interactive(target){return Boolean(target.closest('a,button,input,textarea,select,[contenteditable="true"]'))}
previous.addEventListener('click',()=>show(current-1));next.addEventListener('click',()=>show(current+1));
document.querySelector('#fullscreen').addEventListener('click',()=>{if(document.fullscreenElement){document.exitFullscreen()}else if(document.documentElement.requestFullscreen){document.documentElement.requestFullscreen()}});
document.querySelector('#notes-close').addEventListener('click',()=>{notesPanel.hidden=true;notesButton.setAttribute('aria-expanded','false');notesButton.focus()});
notesButton.addEventListener('click',()=>{notesPanel.hidden=!notesPanel.hidden;notesButton.setAttribute('aria-expanded',String(!notesPanel.hidden));if(!notesPanel.hidden){document.querySelector('#notes-close').focus()}});
document.addEventListener('keydown',event=>{if(interactive(event.target))return;const actions={ArrowRight:()=>show(current+1),PageDown:()=>show(current+1),ArrowLeft:()=>show(current-1),PageUp:()=>show(current-1),Home:()=>show(0),End:()=>show(slides.length-1)};if(actions[event.key]){event.preventDefault();actions[event.key]()}else if(event.key.toLowerCase()==='n'&&notes.some(Boolean)){event.preventDefault();notesButton.click()}});
addEventListener('hashchange',()=>show(hashIndex(),{announce:false}));
if(!notes.some(Boolean)){notesButton.hidden=true}show(hashIndex(),{announce:false});
"""


def build_html(spec_path: Path, spec: dict[str, Any], theme: dict[str, str]) -> str:
    language = spec["language"]
    direction = spec.get("direction") or ("rtl" if language.split("-", 1)[0].lower() in RTL_LANGUAGES else "ltr")
    display, body = FONT_PAIRS[theme["font_pair"]]
    css = CSS.replace("THEME_BG", theme["background"]).replace("THEME_PANEL", theme["panel"]).replace("THEME_TEXT", theme["text"]).replace("THEME_MUTED", theme["muted"]).replace("THEME_ACCENT", theme["accent"]).replace("THEME_LINE", theme["line"]).replace("THEME_DISPLAY", display).replace("THEME_BODY", body)
    slides = "".join(render_slide(slide, index, len(spec["slides"]), spec_path.parent) for index, slide in enumerate(spec["slides"]))
    notes_json = json.dumps([slide.get("notes", "") for slide in spec["slides"]], ensure_ascii=False).replace("<", "\\u003c")
    script = JS.replace("NOTES_JSON", notes_json)
    title = inline_text(spec["title"])
    return f'''<!doctype html>
<html lang="{inline_text(language)}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, width=device-width">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<a class="skip-link" href="#slides">Skip to slides</a>
<main>
<section class="deck-shell" role="region" aria-roledescription="carousel" aria-label="{title}">
<nav class="controls" aria-label="Presentation controls">
<button id="previous" type="button" aria-label="Previous slide">←</button>
<output id="deck-status" class="progress" aria-live="polite">1 / {len(spec['slides'])}</output>
<button id="next" type="button" aria-label="Next slide">→</button>
<button id="notes-button" type="button" aria-controls="notes-panel" aria-expanded="false">Notes</button>
<button id="fullscreen" type="button">Full screen</button>
</nav>
<noscript><p class="noscript">JavaScript is off. All slides remain available below in source order.</p></noscript>
<div id="slides" class="slides" aria-live="polite" aria-atomic="false">{slides}</div>
</section>
</main>
<aside id="notes-panel" class="speaker-notes" aria-label="Speaker notes" hidden>
<button id="notes-close" type="button" aria-label="Close speaker notes">×</button>
<h2>Speaker notes</h2><p id="notes-text"></p>
</aside>
<script>{script}</script>
</body>
</html>
'''


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_output(path: Path, content: str, force: bool) -> None:
    if path.is_symlink():
        raise ValueError("output must not be a symbolic link")
    if path.exists() and not force:
        raise FileExistsError(f"output exists; pass --force only after confirming overwrite: {path}")
    if not path.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {path.parent}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}-", suffix=".tmp", delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def read_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="build_deck.py", description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--max-image-bytes", type=int, default=10_000_000)
    return parser.parse_args(arguments)


def main(sequence: list[str] | None = None) -> int:
    args = read_arguments(sequence or sys.argv[1:])
    if args.max_image_bytes < 1:
        print("max-image-bytes must be positive", file=sys.stderr)
        return 2
    report = validate_spec(args.spec, args.max_image_bytes)
    report.pop("spec", None)
    theme = report.pop("theme", None)
    if report["ok"] and not args.check:
        full_report = validate_spec(args.spec, args.max_image_bytes)
        spec = full_report["spec"]
        output = (args.out or args.spec.with_suffix(".html")).resolve()
        try:
            write_output(output, build_html(args.spec.resolve(), spec, theme), args.force)
        except (OSError, ValueError) as exc:
            report["ok"] = False
            report["summary"]["error"] += 1
            report["findings"].append(finding("output-write", "error", str(output), str(exc)))
        else:
            report["output"] = str(output)
            report["output_sha256"] = sha256(output)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["findings"]:
            print(f"{item['severity'].upper():7} {item['rule_id']} {item['path']} - {item['message']}")
        summary = report["summary"]
        print(f"errors={summary['error']} warnings={summary['warning']} images={len(report['inventory'])}")
        if report.get("output"):
            print(f"output={report['output']} sha256={report['output_sha256']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
