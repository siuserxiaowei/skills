#!/usr/bin/env python3
"""Record a verified platform result without performing a publish action."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--status", required=True, choices=["drafted", "scheduled", "published", "failed", "blocked"])
    parser.add_argument("--url", default="")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    root = Path(args.package).expanduser().resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        parser.error(f"manifest.json not found in {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("platforms", [])
    row = next((item for item in rows if item.get("id") == args.platform), None)
    if row is None:
        parser.error(f"platform not found: {args.platform}")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "campaign_id": manifest.get("campaign_id"),
        "platform": args.platform,
        "job_id": row.get("job_id"),
        "status": args.status,
        "updated_at": timestamp,
        "url": args.url,
        "evidence": args.evidence,
        "note": args.note,
    }
    status_path = (root / row["status"]).resolve()
    if root not in status_path.parents:
        parser.error("status path escapes package")
    write_json(status_path, receipt)
    receipt_path = root / "receipts" / f"{args.platform}.json"
    write_json(receipt_path, receipt)
    row["state"] = args.status
    row["receipt"] = str(receipt_path.relative_to(root))
    write_json(manifest_path, manifest)
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
