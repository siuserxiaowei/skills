#!/usr/bin/env python3
"""Deterministic, privacy-minimizing summaries for selected WeRead responses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def nonnegative_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def classify_secret(value: Any) -> str:
    if value == 1:
        return "private"
    if value == 0:
        return "public"
    return "unknown"


def shelf_summary(data: dict[str, Any]) -> dict[str, Any]:
    books = data.get("books") if isinstance(data.get("books"), list) else []
    albums = data.get("albums") if isinstance(data.get("albums"), list) else []
    article_entry = 1 if data.get("mp") else 0
    privacy = {"public": 0, "private": 0, "unknown": article_entry}

    for book in books:
        value = book.get("secret") if isinstance(book, dict) else None
        privacy[classify_secret(value)] += 1
    for album in albums:
        extra = album.get("albumInfoExtra") if isinstance(album, dict) else None
        value = extra.get("secret") if isinstance(extra, dict) else None
        privacy[classify_secret(value)] += 1

    return {
        "electronic_book_entries": len(books),
        "audio_album_entries": len(albums),
        "article_collection_entries": article_entry,
        "visible_entries": len(books) + len(albums) + article_entry,
        "privacy": privacy,
        "note": "privacy counts use only explicit flags; the article collection is unknown",
    }


def notebooks_summary(data: dict[str, Any]) -> dict[str, Any]:
    rows = data.get("books") if isinstance(data.get("books"), list) else []
    output_rows: list[dict[str, Any]] = []
    complete = True
    computed_total = 0

    for row in rows:
        row = row if isinstance(row, dict) else {}
        counts = {
            "thoughts_or_reviews": nonnegative_int(row.get("reviewCount")),
            "highlights": nonnegative_int(row.get("noteCount")),
            "bookmarks": nonnegative_int(row.get("bookmarkCount")),
        }
        row_complete = all(value is not None for value in counts.values())
        total = sum(value for value in counts.values() if value is not None) if row_complete else None
        if total is None:
            complete = False
        else:
            computed_total += total
        book = row.get("book") if isinstance(row.get("book"), dict) else {}
        output_rows.append(
            {
                "book_id": row.get("bookId") or book.get("bookId"),
                "title": book.get("title"),
                **counts,
                "total_note_like_items": total,
            }
        )

    reported_total = nonnegative_int(data.get("totalNoteCount"))
    return {
        "fetched_notebook_rows": len(rows),
        "reported_total_book_count": nonnegative_int(data.get("totalBookCount")),
        "reported_total_note_count": reported_total,
        "computed_total_note_count": computed_total if complete else None,
        "reconciles": (reported_total == computed_total) if complete and reported_total is not None else None,
        "pagination_has_more": data.get("hasMore"),
        "rows": output_rows,
    }


def human_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes or hours:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def reading_summary(data: dict[str, Any]) -> dict[str, Any]:
    total = nonnegative_int(data.get("totalReadTime"))
    average = nonnegative_int(data.get("dayAverageReadTime"))
    return {
        "base_time": data.get("baseTime"),
        "total_read_time_seconds": total,
        "total_read_time_human": human_duration(total),
        "read_days": nonnegative_int(data.get("readDays")),
        "natural_day_average_seconds": average,
        "natural_day_average_human": human_duration(average),
        "compare_ratio": data.get("compare") if isinstance(data.get("compare"), (int, float)) else None,
        "note": "totals come from returned totalReadTime; no arbitrary-range extrapolation was performed",
    }


SUMMARIZERS = {"shelf": shelf_summary, "notebooks": notebooks_summary, "reading": reading_summary}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize selected WeRead JSON responses")
    parser.add_argument("kind", choices=tuple(SUMMARIZERS))
    parser.add_argument("path", nargs="?", default="-", help="JSON file or - for stdin")
    args = parser.parse_args(argv)

    try:
        if args.path == "-":
            data = json.load(sys.stdin)
        else:
            data = json.loads(Path(args.path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read JSON ({exc})", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: response must be a JSON object", file=sys.stderr)
        return 2

    print(json.dumps(SUMMARIZERS[args.kind](data), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
