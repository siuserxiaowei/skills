#!/usr/bin/env python3
"""Immutable rank-input and curator lineage contracts for Top 50 research."""

from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


RANK_INPUT_CONTRACT = "top50-rank-input-manifest/v1"
CURATOR_CONTRACT = "top50-curator-acceptance/v1"
RANK_INPUT_SPECS = {
    "candidates": ("candidates.json", "application/json", "candidate"),
    "run_manifest": ("run_manifest.json", "application/json", "run"),
    "queries": ("queries.tsv", "text/tab-separated-values", "query"),
    "sources": ("sources.tsv", "text/tab-separated-values", "source"),
    "evidence_cards": (
        "evidence_cards.tsv",
        "text/tab-separated-values",
        "evidence",
    ),
    "platform_coverage": (
        "platform_coverage.tsv",
        "text/tab-separated-values",
        "platform",
    ),
}
DESCRIPTOR_FIELDS = {
    "input_id",
    "role",
    "path",
    "media_type",
    "artifact_sha256",
    "record_kind",
    "record_count",
    "record_ids_sha256",
}
MANIFEST_FIELDS = {
    "contract_version",
    "run_id",
    "stage",
    "status",
    "producer",
    "files",
    "counts",
    "result_digest_sha256",
}
CURATOR_FIELDS = {
    "contract_version",
    "run_id",
    "stage",
    "status",
    "producer",
    "input_bindings",
    "curator",
    "worker_ids",
    "decisions",
    "accepted_candidate_ids",
    "evidence_ledger_binding",
    "source_ledger_binding",
    "counts",
    "result_digest_sha256",
}
CURATOR_DECISION_FIELDS = {
    "candidate_id",
    "decision",
    "evidence_ids",
    "reason_codes",
}
INPUT_BINDING_FIELDS = {
    "relation",
    "path",
    "artifact_sha256",
    "contract",
    "run_id",
    "stage",
    "required_status",
    "producer_engine_id",
    "result_digest_sha256",
    "record_kind",
    "record_count",
    "record_ids_sha256",
}
CURATOR_BINDING_SPECS = {
    "process_result": ("top50-process-result/v1", "process", "complete", "candidate"),
    "rank_input_manifest": (RANK_INPUT_CONTRACT, "worker_check", "complete", "file"),
}


class LineageError(ValueError):
    """A frozen research input was missing, replaced, or internally inconsistent."""


def canonical_json_sha256(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and "\x00" not in value


def read_regular_snapshot(path: Path) -> tuple[bytes, str]:
    """Read and hash one non-symlink regular file through one descriptor."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise OSError("bound inputs must be regular files")
            raw = handle.read()
            after = os.fstat(handle.fileno())
        identity_before = (before.st_dev, before.st_ino, before.st_size)
        identity_after = (after.st_dev, after.st_ino, after.st_size)
        if identity_before != identity_after or len(raw) != after.st_size:
            raise OSError("bound input changed while it was read")
    except (OSError, ValueError) as exc:
        raise LineageError(f"cannot read immutable input {path}: {exc}") from exc
    return raw, hashlib.sha256(raw).hexdigest()


def parse_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LineageError(f"{label} is not valid UTF-8 JSON: {exc}") from exc


def parse_tsv_bytes(raw: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = raw.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text, newline=""), delimiter="\t"))
    except (UnicodeError, csv.Error) as exc:
        raise LineageError(f"{label} is not valid UTF-8 TSV: {exc}") from exc
    if not rows:
        raise LineageError(f"{label} TSV is empty")
    if any(None in row for row in rows):
        raise LineageError(f"{label} TSV has overflow columns")
    for row in rows:
        for key in (
            "candidate_count",
            "discovered_count",
            "fetched_count",
            "eligible_count",
            "blocked_count",
            "rejected_count",
        ):
            if key in row and row[key] not in (None, ""):
                try:
                    row[key] = int(row[key])  # type: ignore[assignment]
                except ValueError as exc:
                    raise LineageError(f"{label} has invalid integer {key}") from exc
    return rows


def _unique_identifiers(values: Sequence[Any], label: str) -> list[str]:
    if any(not nonempty(value) for value in values):
        raise LineageError(f"{label} record IDs must be non-empty strings")
    identifiers = [str(value).strip() for value in values]
    if len(identifiers) != len(set(identifiers)):
        raise LineageError(f"{label} record IDs must be unique")
    return sorted(identifiers)


def _candidate_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, Mapping):
        rows = value.get("candidates")
    else:
        rows = None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise LineageError("candidates.json must contain an array of candidate objects")
    return rows


def _query_id(row: Mapping[str, Any]) -> str:
    if nonempty(row.get("query_id")):
        return str(row["query_id"]).strip()
    fields = ("platform", "query", "backend", "executed_at")
    if any(not nonempty(row.get(field)) for field in fields):
        raise LineageError(
            "query rows without query_id require platform, query, backend, and executed_at"
        )
    material = {field: str(row[field]).strip() for field in fields}
    return f"derived:{canonical_json_sha256(material)}"


def record_ids(input_id: str, parsed: Any) -> list[str]:
    if input_id == "candidates":
        rows = _candidate_rows(parsed)
        return _unique_identifiers(
            [row.get("id") or row.get("candidate_id") for row in rows], input_id
        )
    if input_id == "run_manifest":
        if not isinstance(parsed, Mapping):
            raise LineageError("run_manifest.json must be a JSON object")
        return _unique_identifiers([parsed.get("run_id")], input_id)
    if not isinstance(parsed, list) or any(not isinstance(row, Mapping) for row in parsed):
        raise LineageError(f"{input_id} must contain record objects")
    if input_id == "queries":
        return _unique_identifiers([_query_id(row) for row in parsed], input_id)
    field = {
        "sources": "source_id",
        "evidence_cards": "evidence_id",
        "platform_coverage": "platform",
    }[input_id]
    values = [
        row.get(field)
        if field != "platform"
        else row.get("platform") or row.get("platform_id")
        for row in parsed
    ]
    return _unique_identifiers(values, input_id)


def _parse_rank_input(input_id: str, raw: bytes) -> Any:
    filename, media_type, _ = RANK_INPUT_SPECS[input_id]
    if media_type == "application/json":
        return parse_json_bytes(raw, filename)
    return parse_tsv_bytes(raw, filename)


def build_rank_input_manifest(
    run_dir: Path,
    run_id: str,
    *,
    producer_engine_id: str = "python-control-plane",
    producer_engine_version: str = "0.1.0",
) -> dict[str, Any]:
    if not nonempty(run_id):
        raise LineageError("rank input manifest run_id must be non-empty")
    root = Path(run_dir)
    descriptors: list[dict[str, Any]] = []
    record_counts: dict[str, int] = {}
    for input_id, (filename, media_type, record_kind) in RANK_INPUT_SPECS.items():
        path = root / filename
        raw, artifact_sha256 = read_regular_snapshot(path)
        parsed = _parse_rank_input(input_id, raw)
        identifiers = record_ids(input_id, parsed)
        if input_id == "run_manifest" and identifiers != [run_id]:
            raise LineageError("run_manifest.json run_id does not match the frozen run")
        descriptors.append(
            {
                "input_id": input_id,
                "role": f"{record_kind}_ledger",
                "path": str(path),
                "media_type": media_type,
                "artifact_sha256": artifact_sha256,
                "record_kind": record_kind,
                "record_count": len(identifiers),
                "record_ids_sha256": canonical_json_sha256(identifiers),
            }
        )
        record_counts[input_id] = len(identifiers)
    manifest: dict[str, Any] = {
        "contract_version": RANK_INPUT_CONTRACT,
        "run_id": run_id,
        "stage": "worker_check",
        "status": "complete",
        "producer": {
            "engine_id": producer_engine_id,
            "engine_version": producer_engine_version,
        },
        "files": descriptors,
        "counts": {"files": len(descriptors), **record_counts},
    }
    manifest["result_digest_sha256"] = canonical_json_sha256(manifest)
    return manifest


def write_json_atomic(path: Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = handle.name
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary:
            try:
                Path(temporary).unlink()
            except FileNotFoundError:
                pass
        raise


def _resolved_bound_path(value: Any, manifest_parent: Path) -> Path:
    if not nonempty(value):
        raise LineageError("rank input descriptor path must be non-empty")
    path = Path(str(value))
    resolved = (path if path.is_absolute() else manifest_parent / path).resolve(strict=False)
    if resolved.parent != manifest_parent.resolve(strict=False):
        raise LineageError("rank input descriptor escapes the frozen run directory")
    return resolved


def validate_rank_input_manifest(
    manifest_path: Path,
    expected_run_id: str,
) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    raw_manifest, manifest_artifact_sha256 = read_regular_snapshot(manifest_path)
    manifest = parse_json_bytes(raw_manifest, "rank input manifest")
    if not isinstance(manifest, Mapping) or set(manifest) != MANIFEST_FIELDS:
        raise LineageError("rank input manifest fields are invalid")
    if (
        manifest.get("contract_version") != RANK_INPUT_CONTRACT
        or manifest.get("run_id") != expected_run_id
        or manifest.get("stage") != "worker_check"
        or manifest.get("status") != "complete"
    ):
        raise LineageError("rank input manifest identity is invalid")
    producer = manifest.get("producer")
    if (
        not isinstance(producer, Mapping)
        or set(producer) != {"engine_id", "engine_version"}
        or not nonempty(producer.get("engine_id"))
        or not nonempty(producer.get("engine_version"))
    ):
        raise LineageError("rank input manifest producer is invalid")
    digest = manifest.get("result_digest_sha256")
    material = {key: value for key, value in manifest.items() if key != "result_digest_sha256"}
    if not is_sha256(digest) or digest != canonical_json_sha256(material):
        raise LineageError("rank input manifest result digest is invalid")
    files = manifest.get("files")
    if not isinstance(files, list) or len(files) != len(RANK_INPUT_SPECS):
        raise LineageError("rank input manifest must bind exactly six files")
    descriptors: dict[str, Mapping[str, Any]] = {}
    parsed_inputs: dict[str, Any] = {}
    paths: dict[str, Path] = {}
    record_counts: dict[str, int] = {}
    parent = manifest_path.resolve(strict=False).parent
    for descriptor in files:
        if not isinstance(descriptor, Mapping) or set(descriptor) != DESCRIPTOR_FIELDS:
            raise LineageError("rank input descriptor fields are invalid")
        input_id = descriptor.get("input_id")
        if input_id not in RANK_INPUT_SPECS or input_id in descriptors:
            raise LineageError("rank input IDs are missing, duplicate, or unexpected")
        filename, media_type, record_kind = RANK_INPUT_SPECS[str(input_id)]
        path = _resolved_bound_path(descriptor.get("path"), parent)
        if (
            path.name != filename
            or descriptor.get("media_type") != media_type
            or descriptor.get("record_kind") != record_kind
            or descriptor.get("role") != f"{record_kind}_ledger"
            or not is_sha256(descriptor.get("artifact_sha256"))
            or not isinstance(descriptor.get("record_count"), int)
            or isinstance(descriptor.get("record_count"), bool)
            or descriptor.get("record_count") < 0
            or not is_sha256(descriptor.get("record_ids_sha256"))
        ):
            raise LineageError(f"rank input descriptor {input_id!r} is invalid")
        raw, artifact_sha256 = read_regular_snapshot(path)
        parsed = _parse_rank_input(str(input_id), raw)
        identifiers = record_ids(str(input_id), parsed)
        if (
            artifact_sha256 != descriptor["artifact_sha256"]
            or len(identifiers) != descriptor["record_count"]
            or canonical_json_sha256(identifiers) != descriptor["record_ids_sha256"]
        ):
            raise LineageError(f"rank input {input_id!r} no longer matches its descriptor")
        if input_id == "run_manifest" and identifiers != [expected_run_id]:
            raise LineageError("frozen run manifest belongs to another run")
        descriptors[str(input_id)] = descriptor
        parsed_inputs[str(input_id)] = parsed
        paths[str(input_id)] = path
        record_counts[str(input_id)] = len(identifiers)
    if set(descriptors) != set(RANK_INPUT_SPECS):
        raise LineageError("rank input manifest does not bind the canonical six files")
    expected_counts = {"files": len(RANK_INPUT_SPECS), **record_counts}
    if manifest.get("counts") != expected_counts:
        raise LineageError("rank input manifest counts do not match its files")
    return {
        "manifest": dict(manifest),
        "manifest_path": manifest_path.resolve(strict=False),
        "manifest_artifact_sha256": manifest_artifact_sha256,
        "descriptors": descriptors,
        "inputs": parsed_inputs,
        "paths": paths,
        "record_ids": {
            input_id: record_ids(input_id, parsed)
            for input_id, parsed in parsed_inputs.items()
        },
    }


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _curator_binding_record_ids(
    relation: str, payload: Mapping[str, Any]
) -> list[str]:
    if relation == "process_result":
        rows = payload.get("processed_candidates")
        field = "candidate_id"
    else:
        rows = payload.get("files")
        field = "input_id"
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise LineageError(f"bound {relation} records are invalid")
    return _unique_identifiers([row.get(field) for row in rows], relation)


def validate_process_business_semantics(
    payload: Mapping[str, Any], *, label: str = "process artifact"
) -> None:
    """Validate process invariants shared by router, Rust adapter, and rank lineage."""
    arrays: dict[str, list[Mapping[str, Any]]] = {}
    for field in ("processed_candidates", "exact_clusters", "near_duplicate_reviews"):
        value = payload.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, Mapping) for item in value
        ):
            raise LineageError(f"{label} {field} must be an array of objects")
        arrays[field] = value  # type: ignore[assignment]
    counts = payload.get("counts")
    required_counts = {
        "input_candidates",
        "processed_candidates",
        "exact_clusters",
        "exact_duplicate_candidates",
        "near_duplicate_reviews",
        "dns_validation_required",
    }
    if (
        not isinstance(counts, Mapping)
        or set(counts) != required_counts
        or not all(_nonnegative_int(counts.get(field)) for field in required_counts)
    ):
        raise LineageError(f"{label} counts are incomplete or invalid")

    candidate_ids: set[str] = set()
    dns_required = 0
    for candidate in arrays["processed_candidates"]:
        candidate_id = candidate.get("candidate_id")
        dns_flag = candidate.get("requires_fetch_time_dns_validation")
        if not nonempty(candidate_id) or str(candidate_id).strip() in candidate_ids:
            raise LineageError(
                f"{label} processed candidate IDs must be non-empty and unique"
            )
        if not isinstance(dns_flag, bool):
            raise LineageError(
                f"{label} processed candidate DNS validation flags must be boolean"
            )
        candidate_ids.add(str(candidate_id).strip())
        dns_required += int(dns_flag)
    if (
        counts["input_candidates"] != len(candidate_ids)
        or counts["processed_candidates"] != len(candidate_ids)
    ):
        raise LineageError(f"{label} candidate counts do not match the payload")
    if counts["dns_validation_required"] != dns_required:
        raise LineageError(
            f"{label} DNS validation count does not match processed candidates"
        )

    cluster_ids: set[str] = set()
    clustered_members: set[str] = set()
    exact_duplicate_candidates = 0
    for cluster in arrays["exact_clusters"]:
        cluster_id = cluster.get("cluster_id")
        members_value = cluster.get("candidate_ids")
        if not isinstance(members_value, list):
            raise LineageError(f"{label} exact clusters have invalid candidate IDs")
        members = _unique_identifiers(members_value, f"{label} exact cluster members")
        representative = cluster.get("representative_candidate_id")
        if (
            not nonempty(cluster_id)
            or str(cluster_id).strip() in cluster_ids
            or len(members) < 2
            or any(member not in candidate_ids for member in members)
            or representative not in members
            or any(member in clustered_members for member in members)
        ):
            raise LineageError(
                f"{label} exact clusters have invalid IDs, members, or representative references"
            )
        cluster_ids.add(str(cluster_id).strip())
        clustered_members.update(members)
        exact_duplicate_candidates += len(members) - 1
    if counts["exact_clusters"] != len(arrays["exact_clusters"]):
        raise LineageError(f"{label} exact cluster count does not match the payload")
    if counts["exact_duplicate_candidates"] != exact_duplicate_candidates:
        raise LineageError(
            f"{label} exact duplicate count does not match cluster membership"
        )

    review_ids: set[str] = set()
    for review in arrays["near_duplicate_reviews"]:
        review_id = review.get("review_id")
        members_value = review.get("candidate_ids")
        if not isinstance(members_value, list):
            raise LineageError(
                f"{label} near-duplicate reviews have invalid candidate IDs"
            )
        members = _unique_identifiers(
            members_value, f"{label} near-duplicate review members"
        )
        if (
            not nonempty(review_id)
            or str(review_id).strip() in review_ids
            or len(members) != 2
            or any(member not in candidate_ids for member in members)
        ):
            raise LineageError(
                f"{label} near-duplicate reviews have invalid IDs or candidate references"
            )
        review_ids.add(str(review_id).strip())
    if counts["near_duplicate_reviews"] != len(arrays["near_duplicate_reviews"]):
        raise LineageError(
            f"{label} near duplicate count does not match the payload"
        )


def _validate_curator_input_bindings(
    curator: Mapping[str, Any],
    bundle: Mapping[str, Any],
    expected_run_id: str,
) -> dict[str, Mapping[str, Any]]:
    bindings = curator.get("input_bindings")
    if not isinstance(bindings, list) or len(bindings) != len(CURATOR_BINDING_SPECS):
        raise LineageError(
            "curator input bindings do not match the fixed DAG"
        )
    validated: dict[str, Mapping[str, Any]] = {}
    manifest_path_value = bundle.get("manifest_path")
    manifest = bundle.get("manifest")
    manifest_artifact_sha256 = bundle.get("manifest_artifact_sha256")
    if (
        not isinstance(manifest_path_value, Path)
        or not isinstance(manifest, Mapping)
        or not is_sha256(manifest_artifact_sha256)
    ):
        raise LineageError("validated rank bundle is incomplete")
    manifest_parent = manifest_path_value.resolve(strict=False).parent
    for binding in bindings:
        if not isinstance(binding, Mapping) or set(binding) != INPUT_BINDING_FIELDS:
            raise LineageError("curator input binding fields are invalid")
        relation = binding.get("relation")
        if relation not in CURATOR_BINDING_SPECS or relation in validated:
            raise LineageError(
                "curator input bindings do not match the fixed DAG"
            )
        contract, stage, required_status, record_kind = CURATOR_BINDING_SPECS[
            str(relation)
        ]
        if (
            not nonempty(binding.get("path"))
            or not is_sha256(binding.get("artifact_sha256"))
            or binding.get("contract") != contract
            or binding.get("run_id") != expected_run_id
            or binding.get("stage") != stage
            or binding.get("required_status") != required_status
            or not nonempty(binding.get("producer_engine_id"))
            or not is_sha256(binding.get("result_digest_sha256"))
            or binding.get("record_kind") != record_kind
            or not _nonnegative_int(binding.get("record_count"))
            or not is_sha256(binding.get("record_ids_sha256"))
        ):
            raise LineageError("curator input binding metadata is invalid")
        path = Path(str(binding["path"])).resolve(strict=False)
        if path.parent != manifest_parent:
            raise LineageError("curator input binding escapes the frozen run directory")
        raw, artifact_sha256 = read_regular_snapshot(path)
        upstream = parse_json_bytes(raw, f"bound {relation}")
        if not isinstance(upstream, Mapping):
            raise LineageError(f"bound {relation} must be a JSON object")
        producer = upstream.get("producer")
        material = {
            key: value
            for key, value in upstream.items()
            if key != "result_digest_sha256"
        }
        if (
            artifact_sha256 != binding["artifact_sha256"]
            or upstream.get("contract_version") != contract
            or upstream.get("run_id") != expected_run_id
            or upstream.get("stage") != stage
            or upstream.get("status") != required_status
            or not isinstance(producer, Mapping)
            or producer.get("engine_id") != binding["producer_engine_id"]
            or upstream.get("result_digest_sha256")
            != binding["result_digest_sha256"]
            or upstream.get("result_digest_sha256")
            != canonical_json_sha256(material)
        ):
            raise LineageError(f"bound {relation} identity or digest does not match")
        identifiers = _curator_binding_record_ids(str(relation), upstream)
        if relation == "process_result":
            validate_process_business_semantics(upstream)
        if (
            len(identifiers) != binding["record_count"]
            or canonical_json_sha256(identifiers) != binding["record_ids_sha256"]
        ):
            raise LineageError(f"bound {relation} record set does not match")
        if relation == "rank_input_manifest" and (
            path != manifest_path_value
            or artifact_sha256 != manifest_artifact_sha256
            or upstream.get("result_digest_sha256")
            != manifest.get("result_digest_sha256")
        ):
            raise LineageError(
                "curator does not bind the validated rank input manifest"
            )
        validated[str(relation)] = upstream
    if set(validated) != set(CURATOR_BINDING_SPECS):
        raise LineageError("curator input bindings do not match the fixed DAG")
    return validated


def validate_curator_business_semantics(
    curator: Mapping[str, Any],
    *,
    expected_candidate_ids: Sequence[str],
    processed_candidate_ids: Sequence[str],
) -> dict[str, set[str]]:
    """Validate the curator business contract shared by router and ranker."""
    if set(curator) != CURATOR_FIELDS:
        raise LineageError("curator acceptance fields are invalid")
    producer = curator.get("producer")
    if (
        not isinstance(producer, Mapping)
        or set(producer) != {"engine_id", "engine_version"}
        or not nonempty(producer.get("engine_id"))
        or not nonempty(producer.get("engine_version"))
    ):
        raise LineageError("curator acceptance producer is invalid")
    curator_identity = curator.get("curator")
    worker_ids_value = curator.get("worker_ids")
    if (
        not isinstance(curator_identity, Mapping)
        or set(curator_identity) != {"id"}
        or not nonempty(curator_identity.get("id"))
        or not isinstance(worker_ids_value, list)
    ):
        raise LineageError("curator identity and worker IDs are invalid")
    worker_ids = _unique_identifiers(worker_ids_value, "curator worker IDs")
    if str(curator_identity["id"]).strip() in worker_ids:
        raise LineageError("curator must be independent from research workers")

    decisions = curator.get("decisions")
    if (
        not isinstance(decisions, list)
        or any(
            not isinstance(row, Mapping) or set(row) != CURATOR_DECISION_FIELDS
            for row in decisions
        )
    ):
        raise LineageError("curator decisions must be an array of canonical objects")
    decision_ids = set(
        _unique_identifiers(
            [row.get("candidate_id") for row in decisions], "curator decisions"
        )
    )
    expected_ids = set(
        _unique_identifiers(list(expected_candidate_ids), "expected candidates")
    )
    processed_ids = set(
        _unique_identifiers(list(processed_candidate_ids), "processed candidates")
    )
    if decision_ids != expected_ids:
        raise LineageError("curator decisions do not cover the frozen candidate set")

    declared_accepted = curator.get("accepted_candidate_ids")
    if not isinstance(declared_accepted, list):
        raise LineageError("accepted candidate IDs must be an array")
    accepted_ids = set(
        _unique_identifiers(declared_accepted, "accepted candidates")
    )
    accepted_from_decisions: set[str] = set()
    decision_counts = {"accepted": 0, "rejected": 0, "blocked": 0}
    for decision in decisions:
        status = decision.get("decision")
        if status not in decision_counts:
            raise LineageError("curator decision status is invalid")
        evidence_ids = decision.get("evidence_ids")
        reason_codes = decision.get("reason_codes")
        if not isinstance(evidence_ids, list):
            raise LineageError("curator decision evidence IDs must be an array")
        if not isinstance(reason_codes, list):
            raise LineageError("curator decision reason codes must be an array")
        normalized_evidence = _unique_identifiers(
            evidence_ids, "curator decision evidence IDs"
        )
        _unique_identifiers(reason_codes, "curator decision reason codes")
        if status == "accepted" and not normalized_evidence:
            raise LineageError("accepted curator decisions require evidence")
        if status != "accepted" and not reason_codes:
            raise LineageError("non-accepted curator decisions require reason codes")
        decision_counts[str(status)] += 1
        if status == "accepted":
            accepted_from_decisions.add(str(decision["candidate_id"]))

    if accepted_ids != accepted_from_decisions:
        raise LineageError("accepted candidate IDs do not match curator decisions")
    expected_counts = {
        "input_candidates": len(decisions),
        "accepted": decision_counts["accepted"],
        "rejected": decision_counts["rejected"],
        "blocked": decision_counts["blocked"],
    }
    if curator.get("counts") != expected_counts:
        raise LineageError("curator counts do not match the decisions")
    if decision_ids != processed_ids:
        raise LineageError(
            "curator decisions do not cover the bound processed candidate set"
        )
    return {
        "decision_ids": decision_ids,
        "accepted_ids": accepted_ids,
        "processed_ids": processed_ids,
    }


def validate_curator_against_rank_bundle(
    curator: Mapping[str, Any],
    bundle: Mapping[str, Any],
    expected_run_id: str,
) -> None:
    if (
        curator.get("contract_version") != CURATOR_CONTRACT
        or curator.get("run_id") != expected_run_id
        or curator.get("stage") != "curate"
        or curator.get("status") != "accepted"
    ):
        raise LineageError("curator acceptance identity is invalid")
    digest = curator.get("result_digest_sha256")
    material = {key: value for key, value in curator.items() if key != "result_digest_sha256"}
    if not is_sha256(digest) or digest != canonical_json_sha256(material):
        raise LineageError("curator acceptance result digest is invalid")
    inputs = bundle.get("inputs")
    descriptors = bundle.get("descriptors")
    if not isinstance(inputs, Mapping) or not isinstance(descriptors, Mapping):
        raise LineageError("validated rank bundle is incomplete")
    bound_inputs = _validate_curator_input_bindings(
        curator, bundle, expected_run_id
    )
    candidate_rows = _candidate_rows(inputs["candidates"])
    candidate_ids = set(record_ids("candidates", inputs["candidates"]))
    accepted_candidate_rows = {
        str(row.get("id") or row.get("candidate_id"))
        for row in candidate_rows
        if row.get("reviewer_status") == "accepted"
    }
    processed_ids = _curator_binding_record_ids(
        "process_result", bound_inputs["process_result"]
    )
    semantics = validate_curator_business_semantics(
        curator,
        expected_candidate_ids=sorted(candidate_ids),
        processed_candidate_ids=processed_ids,
    )
    decisions = curator["decisions"]
    accepted_ids = semantics["accepted_ids"]
    evidence_rows = inputs["evidence_cards"]
    source_rows = inputs["sources"]
    evidence_index = {str(row["evidence_id"]): row for row in evidence_rows}
    source_ids = set(record_ids("sources", source_rows))
    for decision in decisions:
        for evidence_id in decision["evidence_ids"]:
            card = evidence_index.get(str(evidence_id))
            if card is None or str(card.get("source_id")) not in source_ids:
                raise LineageError("curator evidence does not resolve through the frozen ledgers")
    if accepted_ids != accepted_candidate_rows:
        raise LineageError("curator accepted set does not match the frozen candidates")
    for field, input_id in (
        ("evidence_ledger_binding", "evidence_cards"),
        ("source_ledger_binding", "sources"),
    ):
        binding = curator.get(field)
        descriptor = descriptors[input_id]
        if (
            not isinstance(binding, Mapping)
            or set(binding) != {"artifact_sha256"}
            or not is_sha256(binding.get("artifact_sha256"))
            or binding.get("artifact_sha256") != descriptor.get("artifact_sha256")
        ):
            raise LineageError(f"{field} does not match the frozen ledger")


def command_paths_match_bundle(
    flag_paths: Mapping[str, Path], bundle: Mapping[str, Any]
) -> bool:
    paths = bundle.get("paths")
    if not isinstance(paths, Mapping) or set(flag_paths) != set(RANK_INPUT_SPECS):
        return False
    return all(
        Path(flag_paths[input_id]).resolve(strict=False) == paths[input_id]
        for input_id in RANK_INPUT_SPECS
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-rank-inputs")
    freeze.add_argument("--run-dir", required=True, type=Path)
    freeze.add_argument("--run-id", required=True)
    freeze.add_argument("--output", type=Path)
    validate = subparsers.add_parser("validate-rank-inputs")
    validate.add_argument("--manifest", required=True, type=Path)
    validate.add_argument("--run-id", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "freeze-rank-inputs":
            output = args.output or args.run_dir / "rank-input-manifest.json"
            manifest = build_rank_input_manifest(args.run_dir, args.run_id)
            write_json_atomic(output, manifest)
            print(
                json.dumps(
                    {
                        "contract_version": RANK_INPUT_CONTRACT,
                        "run_id": args.run_id,
                        "output": str(output),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        validated = validate_rank_input_manifest(args.manifest, args.run_id)
        print(
            json.dumps(
                {
                    "contract_version": RANK_INPUT_CONTRACT,
                    "run_id": args.run_id,
                    "status": "complete",
                    "manifest_artifact_sha256": validated[
                        "manifest_artifact_sha256"
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (LineageError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
