#!/usr/bin/env python3
"""Read-only static triage for browser frontend source files."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable


EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".css", ".scss", ".sass", ".less"}
SKIP_DIRS = {".git", ".next", ".nuxt", ".output", "build", "coverage", "dist", "node_modules", "vendor"}
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
FAIL_RANK = {"high": 3, "medium": 2, "low": 1, "never": 0}


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def compact(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def finding(rule_id: str, category: str, severity: str, confidence: str, path: str, line: int, evidence: str, message: str, verify: str) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "path": path,
        "line": line,
        "evidence": compact(evidence),
        "message": message,
        "verify": verify,
    }


def attributes(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    pattern = re.compile(r"([:@\w-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|\{([^}]*)\}|([^\s>]+))", re.S)
    for match in pattern.finditer(raw):
        parsed[match.group(1).lower()] = next((group for group in match.groups()[1:] if group is not None), "")
    return parsed


def has_accessible_name(attrs: dict[str, str], body: str = "") -> bool:
    if any(str(attrs.get(key, "")).strip() for key in ("aria-label", "aria-labelledby", "title")):
        return True
    if re.search(r"<img\b[^>]*\balt\s*=\s*['\"][^'\"]+", body, re.I | re.S):
        return True
    # A static pass cannot know whether a framework expression renders text.
    # Leave that case for the required rendered accessibility-tree check.
    if re.search(r"\{[^{}]*\S[^{}]*\}", body, re.S):
        return True
    text = re.sub(r"<[^>]+>|\{[^}]*\}", " ", body)
    return bool(re.sub(r"\s+", " ", text).strip())


def inside_span(offset: int, spans: Iterable[tuple[int, int]]) -> bool:
    return any(start <= offset <= end for start, end in spans)


def scan_markup(text: str, rel: str, is_document: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if is_document:
        html = re.search(r"<html\b([^>]*)>", text, re.I | re.S)
        if not html or not re.search(r"\blang\s*=", html.group(1), re.I):
            out.append(finding("document-language", "internationalization", "high", "high", rel, 1, "<html>", "Document has no declared language.", "Inspect the rendered documentElement.lang and set the correct BCP 47 language tag."))
        if not re.search(r"<title\b[^>]*>\s*\S", text, re.I | re.S):
            out.append(finding("document-title", "semantics", "high", "high", rel, 1, "<head>", "Document has no non-empty title.", "Load the route and confirm the browser/accessibility title describes the page."))
        viewport = re.search(r"<meta\b[^>]*\bname\s*=\s*['\"]viewport['\"][^>]*>", text, re.I | re.S)
        if not viewport:
            out.append(finding("document-viewport", "responsive", "medium", "high", rel, 1, "<head>", "Document has no viewport meta declaration.", "Render on a real narrow viewport and confirm CSS pixels and zoom behavior are correct."))

    ids: dict[str, list[int]] = {}
    for match in re.finditer(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", text, re.I):
        ids.setdefault(match.group(1), []).append(line_number(text, match.start()))
    for value, lines in ids.items():
        if len(lines) > 1:
            out.append(finding("duplicate-id", "semantics", "high", "high", rel, lines[1], f'id="{value}"', f"ID {value!r} appears {len(lines)} times.", "Inspect the rendered DOM and update references such as labels, descriptions, and fragment links."))

    labels = set()
    label_spans = []
    for match in re.finditer(r"<label\b([^>]*)>(.*?)</label\s*>", text, re.I | re.S):
        label_spans.append(match.span())
        attrs = attributes(match.group(1))
        target = attrs.get("for") or attrs.get("htmlfor")
        if target:
            labels.add(target)

    for match in re.finditer(r"<img\b([^>]*)>", text, re.I | re.S):
        raw = match.group(0)
        attrs = attributes(match.group(1))
        spread = "..." in raw
        if "alt" not in attrs and not spread:
            out.append(finding("image-alt", "accessibility", "high", "high", rel, line_number(text, match.start()), raw, "Literal image has no alt attribute.", "Determine whether the image is informative or decorative, then inspect its accessible name in the rendered tree."))
        if "width" not in attrs or "height" not in attrs:
            out.append(finding("image-dimensions", "performance", "medium", "medium", rel, line_number(text, match.start()), raw, "Image does not declare both intrinsic dimensions in this source tag.", "Inspect the rendered element and confirm its aspect-ratio space is reserved before loading."))

    for tag in ("button", "a"):
        pattern = re.compile(rf"<{tag}\b([^>]*)>(.*?)</{tag}\s*>", re.I | re.S)
        for match in pattern.finditer(text):
            attrs = attributes(match.group(1))
            if not has_accessible_name(attrs, match.group(2)):
                out.append(finding(f"{tag}-name", "accessibility", "high", "medium", rel, line_number(text, match.start()), match.group(0), f"Literal {tag} appears to have no accessible name.", "Inspect the accessibility tree; provide visible text or an accurate accessible name if missing."))

    for match in re.finditer(r"<(input|textarea|select)\b([^>]*)>", text, re.I | re.S):
        tag = match.group(1).lower()
        attrs = attributes(match.group(2))
        input_type = attrs.get("type", "text").lower()
        if tag == "input" and input_type in {"hidden", "button", "submit", "reset", "image"}:
            continue
        identified = attrs.get("id") in labels if attrs.get("id") else False
        named = any(str(attrs.get(key, "")).strip() for key in ("aria-label", "aria-labelledby"))
        if not identified and not named and not inside_span(match.start(), label_spans):
            out.append(finding("form-control-label", "accessibility", "high", "medium", rel, line_number(text, match.start()), match.group(0), f"Literal {tag} is not associated with a detectable label.", "Inspect the accessibility tree and label relationship; account for framework-generated IDs or wrappers."))

    for match in re.finditer(r"\btabindex\s*=\s*(?:['\"]\s*([1-9]\d*)\s*['\"]|\{\s*([1-9]\d*)\s*\})", text, re.I):
        value = match.group(1) or match.group(2)
        out.append(finding("positive-tabindex", "keyboard", "high", "high", rel, line_number(text, match.start()), match.group(0), f"Positive tabindex {value} creates a custom tab order.", "Traverse the entire surface by keyboard and use DOM order or a composite-widget focus pattern instead."))

    for match in re.finditer(r"<(div|span)\b([^>]*)>", text, re.I | re.S):
        raw = match.group(0)
        attrs = attributes(match.group(2))
        has_click = bool(re.search(r"(?:onclick|on:click|@click)\s*=", raw, re.I))
        if not has_click:
            continue
        has_keyboard = bool(re.search(r"(?:onkeydown|onkeyup|on:keydown|@keydown)\s*=", raw, re.I))
        has_role = bool(attrs.get("role"))
        if not has_keyboard or not has_role:
            out.append(finding("clickable-noncontrol", "keyboard", "high", "medium", rel, line_number(text, match.start()), raw, "Clickable non-control may lack native semantics or keyboard behavior.", "Inspect the rendered element; prefer a native button/link or implement the complete applicable keyboard and state pattern."))

    for match in re.finditer(r"<(?:button|a|input|select|textarea)\b[^>]*\baria-hidden\s*=\s*['\"]true['\"][^>]*>", text, re.I | re.S):
        out.append(finding("hidden-focusable", "accessibility", "high", "high", rel, line_number(text, match.start()), match.group(0), "Potentially focusable control is hidden from the accessibility tree.", "Inspect focusability and the accessibility tree; remove the conflict or make the entire subtree inert."))

    for match in re.finditer(r"\bautofocus(?:\s*=|\b)", text, re.I):
        out.append(finding("autofocus", "interaction", "low", "medium", rel, line_number(text, match.start()), match.group(0), "Autofocus can move focus unexpectedly.", "Test entry with keyboard and assistive technology; retain only when the context and focus announcement are appropriate."))
    return out


def scan_styles(text: str, rel: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text, re.S):
        selector, body = match.group(1), match.group(2)
        line = line_number(text, match.start())
        selector_evidence = compact(selector, 80)
        outline = re.search(r"\boutline\s*:\s*(?:none|0(?:\D|$))", body, re.I)
        if outline:
            out.append(finding("focus-outline", "keyboard", "high", "medium", rel, line, f"{selector_evidence} {{ {outline.group(0)} }}", "CSS removes an outline; a visible replacement is not statically established.", "Keyboard-test every affected control and confirm a visible focus indicator in all themes and states."))
        transition_all = re.search(r"\btransition\s*:\s*all\b", body, re.I)
        if transition_all:
            out.append(finding("transition-all", "performance", "medium", "high", rel, line, f"{selector_evidence} {{ {transition_all.group(0)} }}", "transition: all can animate unintended layout or paint properties.", "List the intended properties and inspect the interaction in DevTools."))
        for width in re.finditer(r"\b(?:width|min-width)\s*:\s*(\d{4,})px", body, re.I):
            if int(width.group(1)) > 1440:
                out.append(finding("fixed-wide", "responsive", "medium", "medium", rel, line, f"{selector_evidence} {{ {width.group(0)} }}", f"Fixed width {width.group(1)}px may overflow narrower viewports.", "Render at target and adjacent widths with real content; replace with an intentional responsive constraint if needed."))
                break
        for size in re.finditer(r"\bfont-size\s*:\s*(\d+(?:\.\d+)?)px", body, re.I):
            if float(size.group(1)) < 12:
                out.append(finding("tiny-text", "typography", "low", "medium", rel, line, f"{selector_evidence} {{ {size.group(0)} }}", f"Text size {size.group(1)}px may be unreadable at the intended context.", "Inspect at target size and zoom with the actual font, contrast, content, and user requirements."))
                break
        overflow = re.search(r"\boverflow-x\s*:\s*hidden", body, re.I)
        if overflow:
            out.append(finding("overflow-mask", "responsive", "low", "low", rel, line, f"{selector_evidence} {{ {overflow.group(0)} }}", "Horizontal overflow is hidden and may mask a layout defect.", "Temporarily expose overflow and inspect narrow viewports; retain only for an intentional clipped composition."))
        for value in re.finditer(r"\bz-index\s*:\s*(\d+)", body, re.I):
            if int(value.group(1)) >= 10000:
                out.append(finding("z-index-scale", "design-system", "low", "medium", rel, line, f"{selector_evidence} {{ {value.group(0)} }}", f"z-index {value.group(1)} suggests an unbounded stacking scale.", "Inspect stacking contexts and map overlays to a documented layer token."))
                break

    has_motion = bool(re.search(r"\b(?:animation(?:-name)?|transition)\s*:\s*(?!none\b)[^;]+", text, re.I))
    if has_motion and "prefers-reduced-motion" not in text.lower():
        match = re.search(r"\b(?:animation(?:-name)?|transition)\s*:", text, re.I)
        assert match is not None
        out.append(finding("reduced-motion", "motion", "medium", "medium", rel, line_number(text, match.start()), match.group(0), "Styles define motion without a detectable prefers-reduced-motion branch in this file.", "Trace the cascade and test the rendered surface with reduced motion enabled; add a meaningful alternative if absent."))

    colors = {value.lower() for value in re.findall(r"#[0-9a-fA-F]{3,8}\b", text)}
    if len(colors) > 12:
        first = re.search(r"#[0-9a-fA-F]{3,8}\b", text)
        assert first is not None
        out.append(finding("color-token-drift", "design-system", "low", "low", rel, line_number(text, first.start()), ", ".join(sorted(colors)[:8]), f"File contains {len(colors)} literal hex colors.", "Map the colors to semantic roles; consolidate only true duplicates and preserve intentional data or illustration palettes."))
    return out


def candidate_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            yield path


def audit(source: Path, max_files: int = 5000, max_bytes: int = 1_000_000) -> dict[str, Any]:
    source = source.resolve()
    findings: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    scanned = 0
    if not source.exists():
        raise FileNotFoundError(source)
    root = source if source.is_dir() else source.parent
    for path in candidate_files(source):
        if scanned >= max_files:
            skipped.append({"path": ".", "reason": f"file limit {max_files} reached"})
            break
        rel = str(path.relative_to(root)) if path != source else path.name
        if path.is_symlink():
            skipped.append({"path": rel, "reason": "symlink not followed"})
            continue
        try:
            size = path.stat().st_size
            if size > max_bytes:
                skipped.append({"path": rel, "reason": f"file exceeds {max_bytes} bytes"})
                continue
            data = path.read_bytes()
            if b"\x00" in data:
                skipped.append({"path": rel, "reason": "binary content"})
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            skipped.append({"path": rel, "reason": str(exc)})
            continue
        scanned += 1
        suffix = path.suffix.lower()
        findings.extend(scan_markup(text, rel, suffix in {".html", ".htm"}))
        if suffix in {".css", ".scss", ".sass", ".less"} or "<style" in text.lower():
            findings.extend(scan_styles(text, rel))

    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for item in findings:
        key = (item["rule_id"], item["path"], item["line"], item["evidence"])
        unique[key] = item
    findings = sorted(unique.values(), key=lambda item: (SEVERITY_ORDER[item["severity"]], item["path"], item["line"], item["rule_id"]))
    counts = Counter(item["severity"] for item in findings)
    return {
        "root": str(source),
        "summary": {"files_scanned": scanned, "findings": {level: counts.get(level, 0) for level in ("high", "medium", "low")}, "skipped": len(skipped)},
        "findings": findings,
        "skipped": skipped,
        "limitations": [
            "Static source patterns can be false positives or miss framework/runtime behavior.",
            "The auditor does not execute builds, render a browser, compute CSS, inspect the accessibility tree, measure contrast, or collect performance data.",
            "No findings is not proof of accessibility, usability, visual quality, or performance.",
        ],
    }


def should_fail(report: dict[str, Any], threshold: str) -> bool:
    required = FAIL_RANK[threshold]
    return any(FAIL_RANK[item["severity"]] >= required for item in report["findings"]) if required else False


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("high", "medium", "low", "never"), default="never")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--max-bytes", type=int, default=1_000_000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.max_files < 1 or args.max_bytes < 1:
        print("max-files and max-bytes must be positive", file=sys.stderr)
        return 2
    try:
        report = audit(args.source, args.max_files, args.max_bytes)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["findings"]:
            print(f"{item['severity'].upper():6} {item['rule_id']} {item['path']}:{item['line']} - {item['message']} [{item['confidence']} confidence]")
        summary = report["summary"]
        print(f"files={summary['files_scanned']} high={summary['findings']['high']} medium={summary['findings']['medium']} low={summary['findings']['low']} skipped={summary['skipped']}")
    return 1 if should_fail(report, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
