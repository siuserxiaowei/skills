#!/usr/bin/env python3
"""Read-only consistency and evidence checks for a Kami delivery manifest."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Any


SEVERITY = {"error": 2, "warning": 1, "info": 0}
KINDS = {"one-pager", "report", "letter", "resume", "portfolio", "slide-deck", "landing-page", "other"}
FORMATS = {"html": {".html", ".htm"}, "pdf": {".pdf"}, "pptx": {".pptx"}, "docx": {".docx"}, "markdown": {".md"}, "png": {".png"}, "svg": {".svg"}}
RIGHTS = {"user-provided", "original", "open-license", "licensed", "public-domain"}
ACCESS = {"tested", "failed", "unknown", "not-applicable"}
SOURCE_KINDS = {"user-file", "user-statement", "primary-url", "derived"}
MARKER = re.compile(r"\[\[(?:REPLACE|TODO|DATA NEEDED):", re.I)
LANGUAGE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class HtmlEvidenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_depth = 0
        self.title_text: list[str] = []
        self.viewport = False
        self.utf8 = False
        self.main_count = 0
        self.h1_count = 0
        self.images: list[dict[str, str | None]] = []

    def handle_starttag(self, element: str, pairs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in pairs}
        element = element.lower()
        if element == "html":
            self.lang = (values.get("lang") or "").strip()
        elif element == "title":
            self.title_depth += 1
        elif element == "meta" and (values.get("name") or "").lower() == "viewport":
            self.viewport = True
        elif element == "meta" and (values.get("charset") or "").lower().replace("-", "") == "utf8":
            self.utf8 = True
        elif element == "main":
            self.main_count += 1
        elif element == "h1":
            self.h1_count += 1
        elif element == "img":
            self.images.append(values)

    def handle_endtag(self, element: str) -> None:
        if element.lower() == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, chunk: str) -> None:
        if self.title_depth:
            self.title_text.append(chunk)


def issue(rule: str, severity: str, message: str, path: str = ".") -> dict[str, str]:
    return {"rule_id": rule, "severity": severity, "path": path, "message": message}


def safe_local(base: Path, raw: Any, findings: list[dict[str, str]], rule: str) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        findings.append(issue(rule, "error", "path must be a non-empty string"))
        return None
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts:
        findings.append(issue(rule, "error", "path must stay inside the delivery directory", raw))
        return None
    resolved = base / candidate
    cursor = base
    for part in candidate.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            findings.append(issue(rule, "error", "symbolic links are not accepted as delivery evidence", raw))
            return None
    try:
        resolved.resolve().relative_to(base.resolve())
    except (OSError, ValueError):
        findings.append(issue(rule, "error", "path resolves outside the delivery directory", raw))
        return None
    if not resolved.is_file():
        findings.append(issue(rule, "error", "recorded file does not exist", raw))
        return None
    return resolved


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def check_signature(path: Path, fmt: str, rel: str) -> list[dict[str, str]]:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError as exc:
        return [issue("file-signature", "error", f"cannot inspect file signature: {exc}", rel)]
    expected = {
        "pdf": head.startswith(b"%PDF-"),
        "png": head.startswith(b"\x89PNG\r\n\x1a\n"),
        "pptx": head.startswith(b"PK\x03\x04"),
        "docx": head.startswith(b"PK\x03\x04"),
    }
    if fmt in expected and not expected[fmt]:
        return [issue("file-signature", "error", f"file bytes do not match declared {fmt} format", rel)]
    return []


def check_image_evidence(path: Path, rel: str) -> list[dict[str, str]]:
    try:
        with path.open("rb") as handle:
            head = handle.read(16)
    except OSError as exc:
        return [issue("evidence-image", "error", f"cannot inspect evidence image: {exc}", rel)]
    png = head.startswith(b"\x89PNG\r\n\x1a\n")
    jpeg = head.startswith(b"\xff\xd8\xff")
    webp = len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP"
    if not (png or jpeg or webp):
        return [issue("evidence-image", "error", "render evidence must be PNG, JPEG, or WebP bytes", rel)]
    return []


def check_html(path: Path, rel: str, landing: bool) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [issue("html-readable", "error", f"HTML is not readable UTF-8: {exc}", rel)]
    parser = HtmlEvidenceParser()
    try:
        parser.feed(text)
    except Exception as exc:
        findings.append(issue("html-parse", "error", f"HTML parser failed: {exc}", rel))
        return findings
    if not parser.lang or not LANGUAGE.fullmatch(parser.lang):
        findings.append(issue("html-language", "error", "HTML needs a valid document language", rel))
    if not parser.utf8:
        findings.append(issue("html-charset", "error", "HTML needs an explicit UTF-8 charset declaration", rel))
    if not "".join(parser.title_text).strip():
        findings.append(issue("html-title", "error", "HTML needs a non-empty title", rel))
    if parser.main_count != 1:
        findings.append(issue("html-main", "error", f"expected one main element, found {parser.main_count}", rel))
    if parser.h1_count != 1:
        findings.append(issue("html-h1", "warning", f"expected one primary h1, found {parser.h1_count}", rel))
    if landing and not parser.viewport:
        findings.append(issue("html-viewport", "error", "landing page needs a viewport declaration", rel))
    if MARKER.search(text):
        findings.append(issue("html-marker", "error", "unresolved replacement or data marker remains", rel))
    for index, attrs in enumerate(parser.images, 1):
        if "alt" not in attrs:
            findings.append(issue("html-image-alt", "error", f"image {index} has no alt attribute", rel))
        if "width" not in attrs or "height" not in attrs:
            findings.append(issue("html-image-size", "warning", f"image {index} lacks intrinsic width and height", rel))
    return findings


def validate(manifest_path: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    inventory: list[dict[str, Any]] = []
    manifest_path = manifest_path.resolve()
    base = manifest_path.parent
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"ok": False, "findings": [issue("manifest-readable", "error", str(exc), str(manifest_path))], "inventory": [], "summary": {"error": 1, "warning": 0, "info": 0}}
    if not isinstance(data, dict):
        return {"ok": False, "findings": [issue("manifest-shape", "error", "manifest root must be an object")], "inventory": [], "summary": {"error": 1, "warning": 0, "info": 0}}

    if data.get("version") != 1:
        findings.append(issue("manifest-version", "error", "version must be 1"))
    status = data.get("status")
    if status not in {"draft", "verified", "blocked"}:
        findings.append(issue("manifest-status", "error", "status must be draft, verified, or blocked"))
    strict = status == "verified"

    artifact = data.get("artifact")
    if not isinstance(artifact, dict):
        findings.append(issue("artifact", "error", "artifact must be an object"))
        artifact = {}
    kind = artifact.get("kind")
    if kind not in KINDS:
        findings.append(issue("artifact-kind", "error", f"artifact.kind must be one of {sorted(KINDS)}"))
    for key in ("title", "audience", "purpose"):
        if not isinstance(artifact.get(key), str) or not artifact[key].strip():
            findings.append(issue(f"artifact-{key}", "error", f"artifact.{key} must be a non-empty string"))
    language = artifact.get("language")
    if not isinstance(language, str) or not LANGUAGE.fullmatch(language):
        findings.append(issue("artifact-language", "error", "artifact.language must be a BCP 47-style tag"))

    outputs = data.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        findings.append(issue("outputs", "error", "outputs must be a non-empty list"))
        outputs = []
    output_map: dict[str, dict[str, Any]] = {}
    for index, output in enumerate(outputs):
        label = f"outputs[{index}]"
        if not isinstance(output, dict):
            findings.append(issue("output-shape", "error", "output must be an object", label))
            continue
        raw = output.get("path")
        if isinstance(raw, str) and raw in output_map:
            findings.append(issue("output-duplicate", "error", "duplicate output path", raw))
        elif isinstance(raw, str):
            output_map[raw] = output
        fmt = output.get("format")
        if fmt not in FORMATS:
            findings.append(issue("output-format", "error", f"unsupported output format {fmt!r}", str(raw or label)))
        elif isinstance(raw, str) and Path(raw).suffix.lower() not in FORMATS[fmt]:
            findings.append(issue("output-suffix", "error", f"suffix does not match format {fmt}", raw))
        if not isinstance(output.get("editable"), bool):
            findings.append(issue("output-editable", "error", "editable must be boolean", str(raw or label)))
        path = safe_local(base, raw, findings, "output-path")
        if path:
            inventory.append({"path": str(raw), "role": "output", "bytes": path.stat().st_size, "sha256": digest(path)})
            findings.extend(check_signature(path, str(fmt), str(raw)))
            if fmt == "html":
                findings.extend(check_html(path, str(raw), kind == "landing-page"))

    sources = data.get("sources", [])
    if not isinstance(sources, list):
        findings.append(issue("sources", "error", "sources must be a list"))
    else:
        for index, source in enumerate(sources):
            if not isinstance(source, dict) or source.get("kind") not in SOURCE_KINDS or not isinstance(source.get("locator"), str) or not source["locator"].strip():
                findings.append(issue("source-record", "error", "source needs a supported kind and non-empty locator", f"sources[{index}]"))
                continue
            source_kind = source["kind"]
            locator = source["locator"]
            if source_kind == "user-file":
                path = safe_local(base, locator, findings, "source-path")
                if path:
                    inventory.append({"path": locator, "role": "source", "bytes": path.stat().st_size, "sha256": digest(path)})
            elif source_kind == "primary-url" and not re.match(r"^https?://", locator, re.I):
                findings.append(issue("source-url", "error", "primary-url locator must use HTTP or HTTPS", f"sources[{index}]"))
            if source_kind in {"primary-url", "derived"} and not source.get("as_of"):
                findings.append(issue("source-date", "warning", "external or derived source has no as_of date", f"sources[{index}]"))
            elif source.get("as_of") and (not isinstance(source["as_of"], str) or not DATE.fullmatch(source["as_of"])):
                findings.append(issue("source-date-format", "warning", "as_of should use YYYY-MM-DD", f"sources[{index}]"))

    assets = data.get("assets", [])
    if not isinstance(assets, list):
        findings.append(issue("assets", "error", "assets must be a list"))
        assets = []
    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            findings.append(issue("asset-shape", "error", "asset must be an object", label))
            continue
        raw = asset.get("path")
        if asset.get("rights") not in RIGHTS:
            findings.append(issue("asset-rights", "error", "asset needs a supported rights record", str(raw or label)))
        if asset.get("role") == "font":
            for key in ("license", "source", "offline_fallback"):
                if not isinstance(asset.get(key), str) or not asset[key].strip():
                    findings.append(issue(f"font-{key}", "error", f"font asset needs {key}", str(raw or label)))
        elif not isinstance(asset.get("alt"), str):
            findings.append(issue("asset-alt", "warning", "visual asset needs alt text or an explicit empty string", str(raw or label)))
        path = safe_local(base, raw, findings, "asset-path")
        if path:
            inventory.append({"path": str(raw), "role": "asset", "bytes": path.stat().st_size, "sha256": digest(path)})

    verification = data.get("verification")
    if not isinstance(verification, dict):
        findings.append(issue("verification", "error", "verification must be an object"))
        verification = {}
    gaps = verification.get("gaps")
    if not isinstance(gaps, list):
        findings.append(issue("verification-gaps", "error", "verification.gaps must be a list"))
    elif strict and gaps:
        findings.append(issue("verified-gaps", "error", "verified delivery cannot contain unresolved gaps"))
    if strict and verification.get("content_reviewed") is not True:
        findings.append(issue("content-review", "error", "verified delivery must record content_reviewed=true"))

    access = verification.get("accessibility")
    if not isinstance(access, dict):
        findings.append(issue("accessibility", "error", "verification.accessibility must be an object"))
    else:
        for key in ("html_keyboard", "html_structure", "pdf"):
            if access.get(key) not in ACCESS:
                findings.append(issue(f"accessibility-{key}", "error", f"accessibility.{key} needs an explicit test status"))
        if any(access.get(key) in {"failed", "unknown"} for key in ("html_keyboard", "html_structure", "pdf")) and not isinstance(access.get("notes"), str):
            findings.append(issue("accessibility-notes", "warning", "failed or unknown accessibility status should explain the boundary"))

    renders = verification.get("renders")
    if not isinstance(renders, list):
        findings.append(issue("renders", "error", "verification.renders must be a list"))
        renders = []
    render_outputs: set[str] = set()
    for index, render in enumerate(renders):
        label = f"verification.renders[{index}]"
        if not isinstance(render, dict):
            findings.append(issue("render-shape", "error", "render record must be an object", label))
            continue
        output = render.get("output")
        if output not in output_map:
            findings.append(issue("render-output", "error", "render record must name a declared output", str(output or label)))
            continue
        render_outputs.add(output)
        if not isinstance(render.get("tool"), str) or not render["tool"].strip():
            findings.append(issue("render-tool", "error", "render record needs the actual tool", output))
        fmt = output_map[output].get("format")
        if fmt == "pdf":
            pages = render.get("pages")
            reviewed = render.get("reviewed_pages")
            if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1:
                findings.append(issue("render-pages", "error", "PDF render needs a positive page count", output))
            if not isinstance(reviewed, list) or not isinstance(pages, int) or sorted(reviewed) != list(range(1, pages + 1)):
                findings.append(issue("render-page-review", "error", "reviewed_pages must cover every PDF page exactly once", output))
            evidence = render.get("evidence")
            if not isinstance(evidence, list) or not isinstance(pages, int) or len(evidence) != pages:
                findings.append(issue("render-page-evidence", "error", "PDF needs one evidence image per page", output))
            else:
                for raw in evidence:
                    path = safe_local(base, raw, findings, "render-evidence")
                    if path:
                        findings.extend(check_image_evidence(path, str(raw)))
        elif fmt == "html" and kind == "landing-page":
            viewports = render.get("viewports")
            if not isinstance(viewports, list):
                findings.append(issue("render-viewports", "error", "landing page render needs viewport evidence", output))
            else:
                widths = set()
                for viewport in viewports:
                    if not isinstance(viewport, dict) or not isinstance(viewport.get("width"), int) or isinstance(viewport.get("width"), bool):
                        findings.append(issue("render-viewport", "error", "viewport needs integer width and screenshot", output))
                        continue
                    widths.add(viewport["width"])
                    screenshot = viewport.get("screenshot")
                    path = safe_local(base, screenshot, findings, "render-screenshot")
                    if path:
                        findings.extend(check_image_evidence(path, str(screenshot)))
                if strict and not any(width <= 375 for width in widths):
                    findings.append(issue("render-narrow", "error", "verified landing page needs a viewport at or below 375px", output))
                if strict and not any(width >= 1280 for width in widths):
                    findings.append(issue("render-wide", "error", "verified landing page needs a viewport at or above 1280px", output))

    if strict:
        for raw, output in output_map.items():
            if output.get("format") in {"pdf"} or (kind == "landing-page" and output.get("format") == "html"):
                if raw not in render_outputs:
                    findings.append(issue("verified-render", "error", "verified rendered output has no render evidence", raw))

    findings.sort(key=lambda item: (-SEVERITY[item["severity"]], item["path"], item["rule_id"]))
    counts = Counter(item["severity"] for item in findings)
    return {
        "ok": counts["error"] == 0,
        "root": str(base),
        "status": status,
        "summary": {level: counts[level] for level in ("error", "warning", "info")},
        "findings": findings,
        "inventory": sorted(inventory, key=lambda item: (item["path"], item["role"])),
        "limitations": [
            "No project code, renderer, browser, presentation application, or network request was executed.",
            "Manifest consistency and basic HTML structure do not prove factual accuracy, visual quality, WCAG conformance, PDF/UA conformance, editability, or asset ownership.",
        ],
    }


def read_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="validate_delivery.py", description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("error", "warning", "never"), default="error")
    return parser.parse_args(arguments)


def main(sequence: list[str] | None = None) -> int:
    args = read_arguments(sequence or sys.argv[1:])
    report = validate(args.manifest)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["findings"]:
            print(f"{item['severity'].upper():7} {item['rule_id']} {item['path']} - {item['message']}")
        summary = report["summary"]
        print(f"errors={summary['error']} warnings={summary['warning']} files={len(report['inventory'])}")
    if args.fail_on == "never":
        return 0
    threshold = SEVERITY[args.fail_on]
    return 1 if any(SEVERITY[item["severity"]] >= threshold for item in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
