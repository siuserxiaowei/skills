#!/usr/bin/env python3
"""Validate the bounded public-API, research, and PyPI readback supplement.

This validator is intentionally offline.  It checks frozen response hashes and
the evidence artifacts already written by the research pass; it never fetches,
promotes, builds, or rewrites a shared ledger.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
DEFAULT_CANDIDATES = HERE / "public-api-research-supplemental-candidates.jsonl"
DEFAULT_READBACKS = HERE / "public-api-research-supplemental-readbacks.jsonl"
DEFAULT_PYPI_CANONICAL_READBACKS = HERE / "pypi-canonical-curator-readbacks.jsonl"
QUEUE_PATH = RUN_DIR / "review_queue.json"
ACCEPTED_PATH = RUN_DIR / "candidates.json"

REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id", "platform_id", "title", "canonical_url", "creator_name",
    "published_at", "date_basis", "accessed_at", "language", "content_type",
    "content_track", "summary", "why_useful", "discovery_backend",
    "readback_backend", "evidence_status", "limitations", "query_id",
    "readback_evidence",
}
REQUIRED_READBACK_FIELDS = {
    "candidate_id", "title", "creator_name", "published_at", "date_basis",
    "accessed_at", "language", "content_type", "content_track", "summary",
    "why_useful", "discovery_backend", "readback_backend", "limitations",
    "query_id", "readback_locator", "readback_observation",
    "readback_content_sha256", "platform_object_id",
}
REQUIRED_CANONICAL_READBACK_FIELDS = REQUIRED_READBACK_FIELDS - {
    "readback_content_sha256",
}
TRACKS = {"入门", "技巧", "进阶", "商业化", "生态与案例", "批评与风险"}

NEW_CANDIDATES = {
    "public-api-arxiv-harness-convergence": {
        "url": "https://arxiv.org/html/2608.23953v1",
        "sha256": "713465f5bbed0fea6280e83bc040e808dd801921fdec9088be1296c9453900cb",
        "object_id": "arXiv:2608.23953v1",
    },
    "public-api-arxiv-polar-pi-rl": {
        "url": "https://arxiv.org/html/2605.24220v1",
        "sha256": "bf16b5b5104e20fdd286c24601a6e95135b3a819554acbac2846c9b66f774a0a",
        "object_id": "arXiv:2605.24220v1",
    },
}

PYPI_READBACKS = {
    "api-packages-pypi-pp-agent-core": (
        "https://pypi.org/pypi/pp-agent-core/json",
        "ec36ecc4edc822a76c95a47b99067e1ebdff870a7f664cfce9769536a42a1562",
        "https://github.com/earendil-works/pi/tree/main/packages/agent",
    ),
    "api-packages-pypi-pp-ai": (
        "https://pypi.org/pypi/pp-ai/json",
        "6870a29343b77a294d8f50b94f0b6665c8e2d48d5c4622c36fcb645b7d1ac6e8",
        "https://github.com/earendil-works/pi/tree/main/packages/ai",
    ),
    "api-packages-pypi-pp-coding-agent": (
        "https://pypi.org/pypi/pp-coding-agent/json",
        "d53f8ff19e931d56bb61773fb4999aecd0ef4c493a06a4f575893a539aad68bd",
        "https://github.com/earendil-works/pi/tree/main/packages/coding-agent",
    ),
    "api-packages-pypi-pp-evals": (
        "https://pypi.org/pypi/pp-evals/json",
        "b8c08497cc2e57cb0e73f03abca73e891512042bc1c18b24b2a9c5f9ded9fd2e",
        "https://github.com/earendil-works/pi/tree/main/packages/evals",
    ),
    "api-packages-pypi-pp-rpc-client": (
        "https://pypi.org/pypi/pp-rpc-client/json",
        "04eaab066624880a9525f1a2b4f04a25a11eb67aa5d1e717a5b6d3c30fabc52d",
        "https://github.com/earendil-works/pi/tree/main/packages/client",
    ),
    "api-packages-pypi-pp-rpc-protocol": (
        "https://pypi.org/pypi/pp-rpc-protocol/json",
        "5a073c51eb790f04cd54a2522fc2a946a716e2adb4ecb5c5131515972672db93",
        "https://github.com/earendil-works/pi/tree/main/packages/protocol",
    ),
    "api-packages-pypi-pp-rpc-server": (
        "https://pypi.org/pypi/pp-rpc-server/json",
        "f6dc561464394ff4fa172b02a501d3591e795afc8144cc0a4741067f4544d244",
        "https://github.com/earendil-works/pi/tree/main/packages/server",
    ),
    "api-packages-pypi-pp-telemetry": (
        "https://pypi.org/pypi/pp-telemetry/json",
        "a8eed700c6279a8e255a2cf8499c832c747795cb1c662fc06aa3e5e7b9e06be8",
        "https://github.com/earendil-works/pi/tree/main/packages/telemetry",
    ),
    "api-packages-pypi-pp-tui": (
        "https://pypi.org/pypi/pp-tui/json",
        "969aa281f825bd32c193edce1b7448d2406b1a9769aba93460f2211e358d213a",
        "https://github.com/earendil-works/pi/tree/main/packages/tui",
    ),
    "api-packages-pypi-pi-ai-client": (
        "https://pypi.org/pypi/pi-ai-client/json",
        "d51fa07280ce54f467711d07adceb14a3f126d1540b7a1ef8ee7b788bbb47830",
        "https://github.com/Kisjjw/pi-ai-py",
    ),
}

# These are the independent, ordinary-browser project-page readbacks that may
# support acceptance.  PYPI_READBACKS above intentionally remains a frozen
# record of the earlier JSON-detail research pass; that robots-disallowed route
# is discovery/history evidence only and must never become the acceptance
# basis merely because a candidate with the same ID was later promoted.
PYPI_CANONICAL_READBACKS = {
    "api-packages-pypi-pp-agent-core": (
        "https://pypi.org/project/pp-agent-core/", "PyPI:pp-agent-core",
    ),
    "api-packages-pypi-pp-ai": (
        "https://pypi.org/project/pp-ai/", "PyPI:pp-ai",
    ),
    "api-packages-pypi-pp-coding-agent": (
        "https://pypi.org/project/pp-coding-agent/", "PyPI:pp-coding-agent",
    ),
    "api-packages-pypi-pp-evals": (
        "https://pypi.org/project/pp-evals/", "PyPI:pp-evals",
    ),
    "api-packages-pypi-pp-rpc-client": (
        "https://pypi.org/project/pp-rpc-client/", "PyPI:pp-rpc-client",
    ),
    "api-packages-pypi-pp-rpc-protocol": (
        "https://pypi.org/project/pp-rpc-protocol/", "PyPI:pp-rpc-protocol",
    ),
    "api-packages-pypi-pp-rpc-server": (
        "https://pypi.org/project/pp-rpc-server/", "PyPI:pp-rpc-server",
    ),
    "api-packages-pypi-pp-telemetry": (
        "https://pypi.org/project/pp-telemetry/", "PyPI:pp-telemetry",
    ),
    "api-packages-pypi-pp-tui": (
        "https://pypi.org/project/pp-tui/", "PyPI:pp-tui",
    ),
    "api-packages-pypi-pi-py-storage-sqlite": (
        "https://pypi.org/project/pi-py-storage-sqlite/",
        "PyPI:pi-py-storage-sqlite",
    ),
    "api-packages-pypi-pi-ai-client": (
        "https://pypi.org/project/pi-ai-client/", "PyPI:pi-ai-client",
    ),
}

EXCLUDED_GITEE_IDS = {
    "public-api-gitee-pi-web",
    "public-api-gitee-pi-web-switch",
}
ZERO_OR_BLOCKED_OUTCOMES = {
    "stackoverflow": {
        "state": "partial",
        "fetched": 0,
        "blocked": 0,
        "reason": "four quoted exact Stack Exchange API intents returned zero strict Pi questions; an unquoted Earendil false positive was rejected",
    },
    "openreview": {
        "state": "blocked",
        "fetched": 0,
        "blocked": 1,
        "reason": "official OpenReview API v1/v2 and terms routes returned HTTP 403; no bypass used",
    },
    "bluesky": {
        "state": "blocked",
        "fetched": 0,
        "blocked": 1,
        "reason": "official public AppView search returned regional HTTP 403; no proxy or bypass used",
    },
    "docker_hub": {
        "state": "partial",
        "fetched": 0,
        "blocked": 0,
        "reason": "no supplemental object: four exact-name repositories lacked description/upstream provenance; existing stck/pi already accepted",
    },
    "gitee": {
        "state": "partial",
        "fetched": 0,
        "blocked": 0,
        "reason": "two apparent results were excluded as GitHub-upstream mirror/content clusters",
    },
}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path.name}:{line_no}: JSON object required")
            rows.append(row)
    return rows


def load_items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError(f"{path}: expected an object with an items list")
    return payload["items"]


def normalize_url(raw: str) -> str:
    parsed = urlsplit(str(raw).strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError(f"invalid public URL: {raw!r}")
    host = parsed.hostname.lower() + (f":{parsed.port}" if parsed.port else "")
    return urlunsplit((
        parsed.scheme.lower(), host, parsed.path.rstrip("/") or "/", parsed.query, "",
    ))


def normalize_title(raw: str) -> str:
    folded = unicodedata.normalize("NFKC", str(raw)).casefold()
    return " ".join(re.findall(r"[\w]+", folded, flags=re.UNICODE))


def require_fields(row: dict, required: set[str], label: str) -> None:
    missing = sorted(required - set(row))
    empty = sorted(field for field in required if not str(row.get(field, "")).strip())
    if missing or empty:
        raise ValueError(f"{label}: missing={missing} empty={empty}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--readbacks", type=Path, default=DEFAULT_READBACKS)
    parser.add_argument(
        "--pypi-canonical-readbacks",
        type=Path,
        default=DEFAULT_PYPI_CANONICAL_READBACKS,
    )
    args = parser.parse_args()

    candidates = load_jsonl(args.candidates)
    readbacks = load_jsonl(args.readbacks)
    pypi_canonical_readbacks = load_jsonl(args.pypi_canonical_readbacks)
    queue = load_items(QUEUE_PATH)
    accepted = load_items(ACCEPTED_PATH)
    queue_by_id = {str(row.get("candidate_id", "")): row for row in queue}
    accepted_ids = {str(row.get("candidate_id", "")) for row in accepted}

    candidate_ids: set[str] = set()
    candidate_urls: set[str] = set()
    candidate_titles: set[str] = set()
    for line_no, row in enumerate(candidates, 1):
        require_fields(row, REQUIRED_CANDIDATE_FIELDS, f"candidate line {line_no}")
        candidate_id = str(row["candidate_id"])
        if candidate_id in candidate_ids:
            raise ValueError(f"candidate line {line_no}: duplicate candidate ID")
        if candidate_id not in NEW_CANDIDATES:
            raise ValueError(f"candidate line {line_no}: unexpected frozen ID {candidate_id}")
        frozen = NEW_CANDIDATES[candidate_id]
        url = normalize_url(row["canonical_url"])
        title = normalize_title(row["title"])
        if url != normalize_url(frozen["url"]):
            raise ValueError(f"{candidate_id}: canonical URL drift")
        if row["platform_id"] != "arxiv_openreview":
            raise ValueError(f"{candidate_id}: platform drift")
        if row["evidence_status"] != "curator_review_ready":
            raise ValueError(f"{candidate_id}: status must remain curator_review_ready")
        if row["content_track"] not in TRACKS:
            raise ValueError(f"{candidate_id}: invalid content track")
        if "official arxiv" not in row["discovery_backend"].lower():
            raise ValueError(f"{candidate_id}: non-official discovery route")
        if "canonical html full-text" not in row["readback_backend"].lower():
            raise ValueError(f"{candidate_id}: non-full-text readback route")
        if frozen["sha256"] not in row["readback_evidence"]:
            raise ValueError(f"{candidate_id}: frozen body hash missing from evidence")
        if len(row["summary"].strip()) < 18 or len(row["readback_evidence"].strip()) < 80:
            raise ValueError(f"{candidate_id}: thin summary/readback evidence")
        if url in candidate_urls or title in candidate_titles:
            raise ValueError(f"{candidate_id}: duplicate URL or exact normalized title in shard")
        candidate_ids.add(candidate_id)
        candidate_urls.add(url)
        candidate_titles.add(title)
    if candidate_ids != set(NEW_CANDIDATES):
        raise ValueError(f"frozen new-candidate set drift: {sorted(candidate_ids ^ set(NEW_CANDIDATES))}")
    promoted_same_id = candidate_ids & accepted_ids
    for candidate_id in promoted_same_id:
        candidate = next(item for item in candidates if item["candidate_id"] == candidate_id)
        promoted = next(item for item in accepted if item.get("candidate_id") == candidate_id)
        if (
            normalize_url(candidate["canonical_url"])
            != normalize_url(promoted.get("canonical_url", ""))
            or normalize_title(candidate["title"])
            != normalize_title(promoted.get("title", ""))
        ):
            raise ValueError(f"{candidate_id}: promoted same-ID copy changed URL/title")

    readbacks_by_id: dict[str, dict] = {}
    for line_no, row in enumerate(readbacks, 1):
        require_fields(row, REQUIRED_READBACK_FIELDS, f"readback line {line_no}")
        candidate_id = str(row["candidate_id"])
        if candidate_id in readbacks_by_id:
            raise ValueError(f"readback line {line_no}: duplicate candidate ID")
        if len(row["summary"].strip()) < 18 or len(row["readback_observation"].strip()) < 60:
            raise ValueError(f"readback line {line_no}: thin independent readback")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row["readback_content_sha256"])):
            raise ValueError(f"readback line {line_no}: invalid SHA-256")
        readbacks_by_id[candidate_id] = row

    expected_readbacks = set(NEW_CANDIDATES) | set(PYPI_READBACKS)
    if set(readbacks_by_id) != expected_readbacks:
        raise ValueError(
            f"frozen readback set drift: {sorted(set(readbacks_by_id) ^ expected_readbacks)}"
        )

    canonical_pypi_by_id: dict[str, dict] = {}
    for line_no, row in enumerate(pypi_canonical_readbacks, 1):
        require_fields(
            row,
            REQUIRED_CANONICAL_READBACK_FIELDS,
            f"canonical PyPI readback line {line_no}",
        )
        candidate_id = str(row["candidate_id"])
        if candidate_id in canonical_pypi_by_id:
            raise ValueError(
                f"canonical PyPI readback line {line_no}: duplicate candidate ID"
            )
        if len(row["summary"].strip()) < 18 or len(row["readback_observation"].strip()) < 60:
            raise ValueError(
                f"canonical PyPI readback line {line_no}: thin independent readback"
            )
        canonical_pypi_by_id[candidate_id] = row
    if set(canonical_pypi_by_id) != set(PYPI_CANONICAL_READBACKS):
        raise ValueError(
            "frozen canonical PyPI readback set drift: "
            f"{sorted(set(canonical_pypi_by_id) ^ set(PYPI_CANONICAL_READBACKS))}"
        )

    for candidate_id, frozen in NEW_CANDIDATES.items():
        row = readbacks_by_id[candidate_id]
        if normalize_url(row["readback_locator"]) != normalize_url(frozen["url"]):
            raise ValueError(f"{candidate_id}: readback locator drift")
        if row["readback_content_sha256"] != frozen["sha256"]:
            raise ValueError(f"{candidate_id}: readback body hash drift")
        if row["platform_object_id"] != frozen["object_id"]:
            raise ValueError(f"{candidate_id}: platform object ID drift")
        candidate = next(item for item in candidates if item["candidate_id"] == candidate_id)
        for field in ("title", "creator_name", "published_at"):
            if row[field] != candidate[field]:
                raise ValueError(f"{candidate_id}: {field} differs between candidate and readback")

    pypi_intents: Counter[str] = Counter()
    for candidate_id, (locator, digest, upstream) in PYPI_READBACKS.items():
        row = readbacks_by_id[candidate_id]
        queue_row = queue_by_id.get(candidate_id)
        if queue_row is None:
            raise ValueError(f"{candidate_id}: PyPI overlay does not match an existing queue ID")
        if queue_row.get("platform_id") != "pypi":
            raise ValueError(f"{candidate_id}: existing queue object is not PyPI")
        if queue_row.get("evidence_status") != "worker_checked":
            raise ValueError(f"{candidate_id}: existing queue object is not worker_checked")
        if queue_row.get("readback_backend") != "not_read_back_discovery_only":
            raise ValueError(f"{candidate_id}: queue row is not eligible for curator-readback override")
        if normalize_url(row["readback_locator"]) != normalize_url(locator):
            raise ValueError(f"{candidate_id}: PyPI readback locator drift")
        if row["readback_content_sha256"] != digest:
            raise ValueError(f"{candidate_id}: PyPI response hash drift")
        upstream_path = urlsplit(upstream).path.rstrip("/")
        upstream_component = upstream_path.rsplit("/", 1)[-1]
        observation = row["readback_observation"]
        upstream_repo = upstream_path.lstrip("/")
        if not any(token in observation for token in (
            upstream, upstream_path, upstream_repo, f"packages/{upstream_component}",
        )):
            raise ValueError(f"{candidate_id}: expected upstream missing from observation")
        if "official documented pypi project json detail api" not in row["readback_backend"].lower():
            raise ValueError(f"{candidate_id}: unsupported PyPI readback route")
        limitations = row["limitations"].lower()
        if "client challenge" not in limitations or not (
            "upload" in limitations or "上传者" in row["limitations"]
        ):
            raise ValueError(f"{candidate_id}: upload-supplied metadata/challenge limits missing")
        if "no distribution was fetched" not in row["readback_observation"].lower():
            raise ValueError(f"{candidate_id}: no-download boundary missing")
        pypi_intents[row["query_id"]] += 1
    if pypi_intents != Counter({
        "pypi-direct-component-port-details": 9,
        "pypi-independent-python-port-details": 1,
    }):
        raise ValueError(f"unexpected PyPI intent coverage: {dict(pypi_intents)}")

    # Acceptance is validated against the later canonical HTML readback, not
    # the frozen JSON-detail response above.  The queue row deliberately stays
    # discovery-only so this check also proves that the curator override is the
    # source of the accepted metadata.
    accepted_by_id = {
        str(row.get("candidate_id", "")): row for row in accepted
    }
    for candidate_id, (locator, object_id) in PYPI_CANONICAL_READBACKS.items():
        row = canonical_pypi_by_id[candidate_id]
        queue_row = queue_by_id.get(candidate_id)
        promoted = accepted_by_id.get(candidate_id)
        if queue_row is None or queue_row.get("platform_id") != "pypi":
            raise ValueError(f"{candidate_id}: canonical readback lacks PyPI queue object")
        if queue_row.get("evidence_status") != "worker_checked" or (
            queue_row.get("readback_backend") != "not_read_back_discovery_only"
        ):
            raise ValueError(
                f"{candidate_id}: canonical readback no longer overlays a discovery-only row"
            )
        if promoted is None:
            raise ValueError(f"{candidate_id}: canonical readback was not promoted")
        if promoted.get("platform_id") != "pypi" or promoted.get("evidence_status") != "accepted":
            raise ValueError(f"{candidate_id}: invalid accepted PyPI state")
        if not str(promoted.get("curator_reviewer", "")).strip() or not str(
            promoted.get("curator_reviewed_at", "")
        ).strip():
            raise ValueError(f"{candidate_id}: missing curator acceptance provenance")

        if normalize_url(row["readback_locator"]) != normalize_url(locator):
            raise ValueError(f"{candidate_id}: canonical PyPI locator drift")
        if normalize_url(queue_row["canonical_url"]) != normalize_url(locator):
            raise ValueError(f"{candidate_id}: queue URL differs from canonical project page")
        if normalize_url(promoted["canonical_url"]) != normalize_url(locator):
            raise ValueError(f"{candidate_id}: accepted URL differs from canonical project page")
        if row["platform_object_id"] != object_id:
            raise ValueError(f"{candidate_id}: canonical PyPI object ID drift")

        backend = str(row["readback_backend"]).lower()
        if (
            "ordinary anonymous public canonical pypi project page" not in backend
            or "client-challenge wait" not in backend
            or "json" in backend
        ):
            raise ValueError(f"{candidate_id}: non-canonical PyPI acceptance backend")
        if promoted.get("readback_backend") != row["readback_backend"]:
            raise ValueError(f"{candidate_id}: accepted backend is not the canonical readback")
        if normalize_url(promoted.get("readback_locator", "")) != normalize_url(locator):
            raise ValueError(f"{candidate_id}: accepted readback locator drift")
        if promoted.get("readback_observation") != row["readback_observation"]:
            raise ValueError(f"{candidate_id}: accepted readback observation drift")

        for field in (
            "title", "creator_name", "published_at", "date_basis", "accessed_at",
            "language", "content_type", "content_track", "summary", "why_useful",
            "discovery_backend", "query_id", "platform_object_id",
        ):
            if promoted.get(field) != row[field]:
                raise ValueError(
                    f"{candidate_id}: accepted {field} is not from canonical readback"
                )
        if not str(promoted.get("limitations", "")).startswith(row["limitations"]):
            raise ValueError(
                f"{candidate_id}: accepted limitations lost canonical readback boundary"
            )

    promoted_legacy_pypi = set(PYPI_READBACKS) & accepted_ids
    missing_canonical_basis = promoted_legacy_pypi - set(canonical_pypi_by_id)
    if missing_canonical_basis:
        raise ValueError(
            "accepted legacy PyPI IDs lack canonical project-page readback: "
            f"{sorted(missing_canonical_basis)}"
        )

    if set(readbacks_by_id) & EXCLUDED_GITEE_IDS or candidate_ids & EXCLUDED_GITEE_IDS:
        raise ValueError("excluded Gitee mirror/content-cluster row leaked into artifacts")

    # Compare new objects against current accepted and queue objects.  The
    # queue may contain promoted copies of this exact shard after compilation;
    # same-ID copies are allowed, while every different owner remains a clash.
    global_urls: dict[str, set[str]] = defaultdict(set)
    global_titles: dict[str, set[str]] = defaultdict(set)
    for row in accepted + queue:
        candidate_id = str(row.get("candidate_id", ""))
        if row.get("canonical_url"):
            global_urls[normalize_url(row["canonical_url"])].add(candidate_id)
        if row.get("title"):
            global_titles[normalize_title(row["title"])].add(candidate_id)
    for row in candidates:
        candidate_id = row["candidate_id"]
        url_owners = global_urls.get(normalize_url(row["canonical_url"]), set()) - {candidate_id}
        title_owners = global_titles.get(normalize_title(row["title"]), set()) - {candidate_id}
        if url_owners or title_owners:
            raise ValueError(
                f"{candidate_id}: global URL/title collision with "
                f"{sorted(url_owners | title_owners)}"
            )

    # Supplemental worker shards are also checked so uncompiled duplicate
    # candidates cannot hide outside the shared queue.
    for path in sorted(HERE.glob("*-candidates.jsonl")):
        if path.resolve() == args.candidates.resolve():
            continue
        for row in load_jsonl(path):
            owner = str(row.get("candidate_id", ""))
            if owner in candidate_ids:
                continue
            if row.get("canonical_url") and normalize_url(row["canonical_url"]) in candidate_urls:
                raise ValueError(f"global worker URL collision with {owner} in {path.name}")
            if row.get("title") and normalize_title(row["title"]) in candidate_titles:
                raise ValueError(f"global worker exact-title collision with {owner} in {path.name}")

    result = {
        "new_candidate_items": len(candidates),
        "new_candidate_counts": dict(sorted(Counter(row["platform_id"] for row in candidates).items())),
        "new_candidate_ids": sorted(candidate_ids),
        "independent_readbacks": len(readbacks),
        "pypi_existing_queue_overlays": len(PYPI_READBACKS),
        "pypi_canonical_accepted_readbacks": len(canonical_pypi_by_id),
        "pypi_intents": dict(sorted(pypi_intents.items())),
        "promoted_same_id_copies": len(promoted_same_id),
        "global_url_collisions": 0,
        "global_exact_title_collisions": 0,
        "excluded_content_clusters": {
            "gitee_pi_web": ["public-api-gitee-pi-web", "worker-global-028"],
            "gitee_pi_web_switch": [
                "public-api-gitee-pi-web-switch",
                "https://github.com/Raingor/pi-web-switch",
            ],
        },
        "zero_or_blocked_outcomes": ZERO_OR_BLOCKED_OUTCOMES,
        "accepted": 0,
        "status": "curator_review_ready_only",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
