#!/usr/bin/env python3
"""Download a bounded list of known public WeChat article URLs."""

from __future__ import annotations

import argparse
import csv
import datetime as datetime_module
import json
import re
import time
import urllib.parse
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


ARTICLE_URL = re.compile(r"https?://mp\.weixin\.qq\.com/[A-Za-z0-9_?=&%./:-]+", re.IGNORECASE)
EXTENSIONS = {"markdown": ".md", "json": ".json", "text": ".txt", "html": ".html"}


@dataclass
class DownloadRecord:
    position: int
    source_url: str
    status: str
    title: str = ""
    relative_path: str = ""
    retrieved_at: str = ""
    error: str = ""


def utc_now() -> str:
    return datetime_module.datetime.now(datetime_module.timezone.utc).isoformat()


def run_label() -> str:
    return datetime_module.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def urls_in(value: str) -> list[str]:
    return [match.group(0).rstrip(".,;，。；)") for match in ARTICLE_URL.finditer(value)]


def flatten_json(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_json(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_json(child)]
    return []


def collect_urls(arguments: list[str], files: list[Path]) -> list[str]:
    discovered = [url for value in arguments for url in urls_in(value)]
    for path in files:
        text = path.expanduser().read_text(encoding="utf-8")
        if path.suffix.casefold() == ".json":
            try:
                values = flatten_json(json.loads(text))
            except json.JSONDecodeError:
                values = [text]
        else:
            values = [text]
        discovered.extend(url for value in values for url in urls_in(value))
    ordered: list[str] = []
    seen: set[str] = set()
    for url in discovered:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def request_article(api_base: str, source_url: str, output_format: str, timeout: float) -> str:
    parameters = urllib.parse.urlencode({"url": source_url, "format": output_format})
    endpoint = api_base.rstrip("/") + "/api/public/v1/download?" + parameters
    request = urllib.request.Request(endpoint, headers={"User-Agent": "wechat-public-article-client/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def infer_title(payload: str, fallback: str) -> str:
    heading = next((line[2:].strip() for line in payload.splitlines()[:40] if line.startswith("# ")), "")
    if heading:
        return heading
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return fallback
    if isinstance(data, dict):
        for key in ("title", "name"):
            if data.get(key):
                return str(data[key])
    return fallback


def safe_stem(title: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u3400-\u9fff._ -]+", "_", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._")
    return cleaned[:80] or "untitled"


def write_index(destination: Path, records: list[DownloadRecord]) -> Path:
    path = destination / "index.csv"
    fields = list(asdict(records[0]).keys()) if records else list(DownloadRecord.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("values", nargs="*", help="known article URLs or text containing them")
    parser.add_argument("--file", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=tuple(EXTENSIONS), default="markdown")
    parser.add_argument("--api-base", default="https://down.mptext.top")
    parser.add_argument("--timeout", type=float, default=40)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--max-items", type=int, default=100)
    parser.add_argument("--apply", action="store_true", help="perform network downloads after previewing the URL list")
    args = parser.parse_args(argv)
    urls = collect_urls(args.values, args.file)
    if not urls:
        parser.error("no mp.weixin.qq.com article URL was found")
    if len(urls) > args.max_items:
        parser.error(f"found {len(urls)} URLs, exceeding --max-items={args.max_items}")
    preview = {"count": len(urls), "urls": urls, "api_base": args.api_base, "format": args.format, "network_requested": args.apply}
    if not args.apply:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    destination = args.output.expanduser() if args.output else Path.cwd() / "wechat-mp-runs" / run_label()
    destination = destination.resolve(strict=False)
    articles = destination / "articles"
    articles.mkdir(parents=True, exist_ok=False)
    records: list[DownloadRecord] = []
    for position, url in enumerate(urls, start=1):
        record = DownloadRecord(position=position, source_url=url, status="failed", retrieved_at=utc_now())
        try:
            body = request_article(args.api_base, url, args.format, args.timeout)
            record.title = infer_title(body, f"article-{position:03d}")
            relative = Path("articles") / f"{position:03d}-{safe_stem(record.title)}{EXTENSIONS[args.format]}"
            (destination / relative).write_text(body, encoding="utf-8")
            record.relative_path = str(relative)
            record.status = "success"
        except Exception as exc:
            record.error = str(exc)
        records.append(record)
        if position != len(urls) and args.interval > 0:
            time.sleep(args.interval)
    index = write_index(destination, records)
    failures = [asdict(record) for record in records if record.status != "success"]
    failure_path = destination / "failures.json"
    failure_path.write_text(json.dumps(failures, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {
        "output": str(destination),
        "index": str(index),
        "failures": str(failure_path),
        "success": sum(record.status == "success" for record in records),
        "failed": len(failures),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
