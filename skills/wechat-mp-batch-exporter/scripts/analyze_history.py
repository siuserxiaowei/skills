#!/usr/bin/env python3
"""Reconcile WeChat public-account history records into explicit counting scopes."""

from __future__ import annotations

import argparse
import csv
import datetime as datetime_module
import json
from collections import Counter
from pathlib import Path


OUTPUT_COLUMNS = (
    "position",
    "account_name",
    "account_alias",
    "fakeid",
    "title",
    "url",
    "digest",
    "author",
    "published_at",
    "updated_at",
    "create_time",
    "update_time",
    "msgid",
    "appmsgid",
    "itemidx",
    "comment_id",
    "is_deleted",
    "is_original",
    "copyright_type",
    "copyright_stat",
    "cover_url",
    "source_chunk",
)


def json_array(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"expected an array of objects: {path}")
    return value


def source_records(merged: Path | None, chunks: Path | None) -> list[dict]:
    rows: list[dict] = []
    if merged:
        rows.extend(dict(item) for item in json_array(merged))
    if chunks:
        paths = sorted(chunks.glob("*history-chunk-*.json"))
        for path in paths:
            try:
                items = json_array(path)
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                continue
            for item in items:
                copied = dict(item)
                copied["source_chunk"] = path.name
                rows.append(copied)
    if not rows:
        raise ValueError("no usable history objects were found")
    return rows


def nested_raw(row: dict, name: str):
    value = row.get("raw")
    return value.get(name) if isinstance(value, dict) else None


def timestamp_text(raw) -> str:
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return ""
    if number > 10_000_000_000:
        number /= 1000
    try:
        return datetime_module.datetime.fromtimestamp(number, datetime_module.timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return ""


def identity(row: dict) -> tuple:
    if row.get("url"):
        return ("url", str(row["url"]))
    if row.get("aid"):
        return ("aid", str(row["aid"]))
    return ("tuple", str(row.get("appmsgid")), str(row.get("itemidx")), str(row.get("title")))


def integer(row: dict, name: str) -> int:
    try:
        return int(row.get(name) or 0)
    except (TypeError, ValueError):
        return 0


def normalize(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    chosen: dict[tuple, dict] = {}
    duplicates: list[dict] = []
    for row in rows:
        key = identity(row)
        if key in chosen:
            duplicates.append({"identity": key, "kept_title": chosen[key].get("title"), "dropped_title": row.get("title")})
            continue
        chosen[key] = dict(row)
    normalized = list(chosen.values())
    normalized.sort(key=lambda row: (integer(row, "create_time"), integer(row, "itemidx")), reverse=True)
    for position, row in enumerate(normalized, start=1):
        copyright_type = nested_raw(row, "copyright_type")
        copyright_stat = nested_raw(row, "copyright_stat")
        row["position"] = position
        row["published_at"] = row.get("publish_time_iso") or timestamp_text(row.get("create_time"))
        row["updated_at"] = row.get("update_time_iso") or timestamp_text(row.get("update_time"))
        row["copyright_type"] = copyright_type
        row["copyright_stat"] = copyright_stat
        row["is_original"] = copyright_type == 1 and copyright_stat == 1 and not bool(row.get("is_deleted"))
    return normalized, duplicates


def distinct_publish_groups(rows: list[dict]) -> int:
    message_ids = {str(row["msgid"]) for row in rows if row.get("msgid") not in (None, "")}
    if message_ids:
        return len(message_ids)
    return sum(integer(row, "itemidx") == 1 for row in rows)


def summary(raw_count: int, rows: list[dict], duplicates: list[dict]) -> dict:
    dates = [row["published_at"] for row in rows if row.get("published_at")]
    return {
        "input_objects": raw_count,
        "expanded_articles": len(rows),
        "unique_article_urls": len({row.get("url") for row in rows if row.get("url")}),
        "publish_groups": distinct_publish_groups(rows),
        "headline_articles": sum(integer(row, "itemidx") == 1 for row in rows),
        "marked_original_articles": sum(bool(row.get("is_original")) for row in rows),
        "active_articles": sum(not bool(row.get("is_deleted")) for row in rows),
        "deleted_articles": sum(bool(row.get("is_deleted")) for row in rows),
        "duplicates_removed": len(duplicates),
        "newest_published_at": max(dates, default=""),
        "oldest_published_at": min(dates, default=""),
        "item_position_counts": {str(key): value for key, value in Counter(row.get("itemidx") for row in rows).most_common()},
        "copyright_type_counts": {str(key): value for key, value in Counter(row.get("copyright_type") for row in rows).most_common()},
        "scope_notes": [
            "expanded_articles counts distinct article identities after multi-item messages are expanded",
            "publish_groups counts distinct msgid values when present",
            "marked_original_articles requires copyright_type=1, copyright_stat=1, and a non-deleted record",
            "these scopes are different and must be labeled separately",
        ],
    }


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_urls(path: Path, rows: list[dict]) -> None:
    urls = [str(row["url"]) for row in rows if row.get("url")]
    path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")


def write_markdown(path: Path, report: dict) -> None:
    labels = [
        ("Input objects", "input_objects"),
        ("Expanded articles", "expanded_articles"),
        ("Unique article URLs", "unique_article_urls"),
        ("Publish groups", "publish_groups"),
        ("Marked original articles", "marked_original_articles"),
        ("Duplicates removed", "duplicates_removed"),
    ]
    lines = ["# WeChat public-account history reconciliation", ""]
    lines.extend(f"- {label}: {report[key]}" for label, key in labels)
    lines.extend(["", "## Scope notes", ""])
    lines.extend(f"- {note}" for note in report["scope_notes"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history-json", type=Path)
    parser.add_argument("--chunk-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--prefix", default="history")
    args = parser.parse_args(argv)
    if not args.history_json and not args.chunk_dir:
        parser.error("provide --history-json or --chunk-dir")
    merged = args.history_json.expanduser() if args.history_json else None
    chunks = args.chunk_dir.expanduser() if args.chunk_dir else None
    raw = source_records(merged, chunks)
    rows, duplicates = normalize(raw)
    originals = [row for row in rows if row["is_original"]]
    if args.output_dir:
        output = args.output_dir.expanduser()
    elif merged:
        output = merged.parent
    else:
        output = chunks or Path.cwd()
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "all_json": output / f"{args.prefix}.dedup.json",
        "all_csv": output / f"{args.prefix}.dedup.csv",
        "all_urls": output / "urls.all.txt",
        "original_json": output / f"{args.prefix}.original.json",
        "original_csv": output / f"{args.prefix}.original.csv",
        "original_urls": output / "urls.original.txt",
        "duplicates": output / f"{args.prefix}.duplicates.json",
        "summary_json": output / f"{args.prefix}.summary.json",
        "summary_md": output / f"{args.prefix}.summary.md",
    }
    write_json(paths["all_json"], rows)
    write_csv(paths["all_csv"], rows)
    write_urls(paths["all_urls"], rows)
    write_json(paths["original_json"], originals)
    write_csv(paths["original_csv"], originals)
    write_urls(paths["original_urls"], originals)
    write_json(paths["duplicates"], duplicates)
    report = summary(len(raw), rows, duplicates)
    report["files"] = {name: str(path) for name, path in paths.items()}
    write_json(paths["summary_json"], report)
    write_markdown(paths["summary_md"], report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
