#!/usr/bin/env python3
"""Compare rebuilt Skills with a frozen Git baseline without executing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z_][a-z0-9_+.-]*|\d+(?:\.\d+)*|[\u3400-\u4dbf\u4e00-\u9fff]")
SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}


@dataclass(frozen=True)
class Thresholds:
    exact_blob_min_bytes: int = 96
    window_size: int = 16
    material_run_tokens: int = 64
    material_window_matches: int = 12
    material_window_coverage: float = 0.10
    long_line_chars: int = 80


@dataclass
class Finding:
    severity: str
    code: str
    skill: str
    path: str
    detail: str
    evidence: dict
    adjudication: dict | None = None


class AuditError(RuntimeError):
    """Raised when the reproducible evidence cannot be obtained."""


def run_git(root: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        check=False,
    )
    if completed.returncode:
        stderr = completed.stderr.strip() if text else completed.stderr.decode("utf-8", "replace").strip()
        raise AuditError(f"git {' '.join(args)} failed: {stderr}")
    return completed.stdout


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(normalize_text(text))


def decode_text(data: bytes) -> str | None:
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def windows(items: list[str], size: int) -> list[tuple[str, ...]]:
    if len(items) < size:
        return []
    return [tuple(items[index : index + size]) for index in range(len(items) - size + 1)]


def long_lines(text: str, minimum: int) -> set[str]:
    result = set()
    for line in text.splitlines():
        normalized = " ".join(normalize_text(line).split())
        if len(normalized) >= minimum:
            result.add(normalized)
    return result


def current_files(root: Path, skill: str) -> list[tuple[str, bytes]]:
    skill_root = root / "skills" / skill
    if not skill_root.is_dir():
        raise AuditError(f"declared Skill directory is missing: skills/{skill}")
    result = []
    for path in sorted(skill_root.rglob("*")):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.is_symlink():
            raise AuditError(f"symlink requires collection-level review: {path.relative_to(root)}")
        if not path.is_file():
            continue
        result.append((path.relative_to(root).as_posix(), path.read_bytes()))
    return result


def baseline_files(root: Path, baseline: str, skill: str) -> list[tuple[str, bytes]]:
    prefix = f"skills/{skill}"
    raw_paths = run_git(root, "ls-tree", "-r", "-z", "--name-only", baseline, "--", prefix, text=False)
    assert isinstance(raw_paths, bytes)
    result = []
    for raw_path in raw_paths.split(b"\x00"):
        if not raw_path:
            continue
        path = raw_path.decode("utf-8", "surrogateescape")
        data = run_git(root, "show", f"{baseline}:{path}", text=False)
        assert isinstance(data, bytes)
        result.append((path, data))
    return result


def longest_window_run(current: list[tuple[str, ...]], baseline: set[tuple[str, ...]], size: int) -> int:
    longest = 0
    active = 0
    for item in current:
        if item in baseline:
            active += 1
            longest = max(longest, active)
        else:
            active = 0
    return longest + size - 1 if longest else 0


def inspect_file(
    skill: str,
    path: str,
    data: bytes,
    baseline_hashes: set[str],
    baseline_windows: set[tuple[str, ...]],
    baseline_material_windows: set[tuple[str, ...]],
    baseline_lines: set[str],
    thresholds: Thresholds,
) -> tuple[Finding | None, dict]:
    digest = sha256(data)
    exact_blob = len(data) >= thresholds.exact_blob_min_bytes and digest in baseline_hashes
    text = decode_text(data)
    metrics = {
        "bytes": len(data),
        "sha256": digest,
        "text_scanned": text is not None,
        "exact_baseline_blob": exact_blob,
        "window_positions": 0,
        "matching_window_positions": 0,
        "matching_window_samples": [],
        "window_coverage": 0.0,
        "longest_candidate_token_run": 0,
        "material_run_matches": 0,
        "material_run_samples": [],
        "matching_long_lines": 0,
    }

    if text is not None:
        current_tokens = tokens(text)
        current_windows = windows(current_tokens, thresholds.window_size)
        current_material_windows = windows(current_tokens, thresholds.material_run_tokens)
        material_run_samples = []
        for item in current_material_windows:
            if item in baseline_material_windows:
                material_run_samples.append(" ".join(item))
                if len(material_run_samples) == 3:
                    break
        matching_positions = sum(item in baseline_windows for item in current_windows)
        matching_window_samples = []
        seen_samples = set()
        for item in current_windows:
            if item in baseline_windows:
                sample = " ".join(item)
                if sample not in seen_samples:
                    matching_window_samples.append(sample)
                    seen_samples.add(sample)
                if len(matching_window_samples) == 3:
                    break
        coverage = matching_positions / len(current_windows) if current_windows else 0.0
        matching_lines = long_lines(text, thresholds.long_line_chars) & baseline_lines
        metrics.update(
            {
                "window_positions": len(current_windows),
                "matching_window_positions": matching_positions,
                "matching_window_samples": matching_window_samples,
                "window_coverage": coverage,
                "longest_candidate_token_run": longest_window_run(
                    current_windows, baseline_windows, thresholds.window_size
                ),
                "material_run_matches": sum(
                    item in baseline_material_windows for item in current_material_windows
                ),
                "material_run_samples": material_run_samples,
                "matching_long_lines": len(matching_lines),
                "matching_long_line_samples": sorted(matching_lines)[:3],
            }
        )

    material_codes = []
    if exact_blob:
        material_codes.append("exact-baseline-blob")
    if metrics["material_run_matches"]:
        material_codes.append("long-token-run")
    if (
        metrics["matching_window_positions"] >= thresholds.material_window_matches
        and metrics["window_coverage"] >= thresholds.material_window_coverage
    ):
        material_codes.append("high-window-coverage")

    if material_codes:
        finding = Finding(
            "material",
            "+".join(material_codes),
            skill,
            path,
            "current artifact materially overlaps the frozen same-Skill baseline",
            metrics,
        )
    elif (
        metrics["matching_window_positions"]
        or metrics["matching_long_lines"]
        or (text is None and len(data) > 0)
    ):
        code = "unscanned-binary" if text is None else "similarity-review"
        detail = (
            "binary content was hash-checked but not token-scanned"
            if text is None
            else "limited similarity requires contextual review"
        )
        finding = Finding("review", code, skill, path, detail, metrics)
    else:
        finding = None
    return finding, metrics


def load_manifest(root: Path) -> dict:
    path = root / "SKILL_PROVENANCE.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read {path.name}: {error}") from error
    if not isinstance(manifest, dict):
        raise AuditError(f"{path.name} must contain a JSON object")
    return manifest


def thresholds_from_manifest(manifest: dict) -> Thresholds:
    configured = manifest.get("originality_assurance", {}).get("thresholds", {})
    defaults = asdict(Thresholds())
    if configured:
        unknown = sorted(set(configured) - set(defaults))
        if unknown:
            raise AuditError(f"unknown originality threshold(s): {', '.join(unknown)}")
        defaults.update(configured)
    thresholds = Thresholds(**defaults)
    if thresholds.exact_blob_min_bytes < 1:
        raise AuditError("exact_blob_min_bytes must be positive")
    if thresholds.window_size < 2:
        raise AuditError("window_size must be at least 2")
    if thresholds.material_run_tokens < thresholds.window_size:
        raise AuditError("material_run_tokens cannot be smaller than window_size")
    if thresholds.material_window_matches < 1:
        raise AuditError("material_window_matches must be positive")
    if not 0 < thresholds.material_window_coverage <= 1:
        raise AuditError("material_window_coverage must be in (0, 1]")
    if thresholds.long_line_chars < 1:
        raise AuditError("long_line_chars must be positive")
    return thresholds


def verify_new_original_lineage(root: Path, manifest: dict, current_commit: str) -> list[dict]:
    names = manifest.get("origin_groups", {}).get("new_original", [])
    evidence = manifest.get("new_original_evidence", {})
    if not isinstance(names, list) or not all(isinstance(item, str) for item in names):
        raise AuditError("origin_groups.new_original must be a list of Skill names")
    if not isinstance(evidence, dict) or set(evidence) != set(names):
        raise AuditError("new_original_evidence must cover every new_original Skill exactly")

    result = []
    for skill in sorted(names):
        item = evidence[skill]
        if not isinstance(item, dict):
            raise AuditError(f"new_original_evidence.{skill} must be an object")
        claimed_commit = item.get("first_commit")
        anchor = item.get("anchor")
        if not isinstance(claimed_commit, str) or not isinstance(anchor, str):
            raise AuditError(f"new_original_evidence.{skill} requires first_commit and anchor")
        expected_prefix = f"skills/{skill}/"
        if not anchor.startswith(expected_prefix) or not (root / anchor).is_file():
            raise AuditError(f"invalid new-original anchor for {skill}: {anchor}")
        resolved = run_git(root, "rev-parse", "--verify", f"{claimed_commit}^{{commit}}")
        assert isinstance(resolved, str)
        resolved_commit = resolved.strip()
        history = run_git(root, "log", "--follow", "--diff-filter=A", "--format=%H", "--", anchor)
        assert isinstance(history, str)
        additions = [line for line in history.splitlines() if line]
        if not additions or additions[-1] != resolved_commit:
            raise AuditError(
                f"first-commit evidence mismatch for {skill}: claimed {resolved_commit}, observed {additions[-1] if additions else 'none'}"
            )
        try:
            run_git(root, "merge-base", "--is-ancestor", resolved_commit, current_commit)
        except AuditError as error:
            raise AuditError(f"new-original first commit is not an ancestor for {skill}") from error
        result.append({"skill": skill, "first_commit": resolved_commit, "anchor": anchor})
    return result


def audit_repository(root: Path, baseline: str | None = None) -> dict:
    root = root.resolve()
    manifest = load_manifest(root)
    assurance = manifest.get("originality_assurance", {})
    requested_baseline = baseline or assurance.get("historical_baseline_commit")
    if not requested_baseline:
        raise AuditError("historical baseline commit is not configured")
    resolved = run_git(root, "rev-parse", "--verify", f"{requested_baseline}^{{commit}}")
    assert isinstance(resolved, str)
    baseline_commit = resolved.strip()
    current = run_git(root, "rev-parse", "HEAD")
    assert isinstance(current, str)
    current_commit = current.strip()
    try:
        run_git(root, "merge-base", "--is-ancestor", baseline_commit, current_commit)
    except AuditError as error:
        raise AuditError("historical baseline is not an ancestor of the current commit") from error
    worktree = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    assert isinstance(worktree, str)
    new_original_lineage = verify_new_original_lineage(root, manifest, current_commit)

    rebuilt = manifest.get("origin_groups", {}).get("independently_rebuilt", [])
    if not isinstance(rebuilt, list) or not all(isinstance(item, str) for item in rebuilt):
        raise AuditError("origin_groups.independently_rebuilt must be a list of Skill names")

    thresholds = thresholds_from_manifest(manifest)
    findings: list[Finding] = []
    files_checked = 0
    baseline_files_checked = 0
    skill_summaries = []

    for skill in sorted(rebuilt):
        old_files = baseline_files(root, baseline_commit, skill)
        baseline_files_checked += len(old_files)
        old_hashes = {sha256(data) for _, data in old_files}
        old_windows: set[tuple[str, ...]] = set()
        old_material_windows: set[tuple[str, ...]] = set()
        old_lines: set[str] = set()
        if not old_files:
            raise AuditError(f"historical baseline has no files for independently rebuilt Skill: {skill}")
        for _, data in old_files:
            text = decode_text(data)
            if text is None:
                continue
            old_tokens = tokens(text)
            old_windows.update(windows(old_tokens, thresholds.window_size))
            old_material_windows.update(windows(old_tokens, thresholds.material_run_tokens))
            old_lines.update(long_lines(text, thresholds.long_line_chars))

        skill_findings = 0
        skill_files = current_files(root, skill)
        files_checked += len(skill_files)
        for path, data in skill_files:
            finding, _metrics = inspect_file(
                skill,
                path,
                data,
                old_hashes,
                old_windows,
                old_material_windows,
                old_lines,
                thresholds,
            )
            if finding:
                findings.append(finding)
                skill_findings += 1
        skill_summaries.append(
            {
                "skill": skill,
                "current_files": len(skill_files),
                "baseline_files": len(old_files),
                "findings": skill_findings,
            }
        )

    material = sum(item.severity == "material" for item in findings)
    review = sum(item.severity == "review" for item in findings)
    review_records = manifest.get("reviewed_similarity_findings", [])
    if not isinstance(review_records, list):
        raise AuditError("reviewed_similarity_findings must be a list")
    records_by_key = {}
    for index, record in enumerate(review_records):
        if not isinstance(record, dict):
            raise AuditError(f"reviewed_similarity_findings[{index}] must be an object")
        key = (record.get("skill"), record.get("path"), record.get("sha256"))
        if not all(isinstance(value, str) and value for value in key):
            raise AuditError(f"reviewed_similarity_findings[{index}] lacks skill/path/sha256")
        if key in records_by_key:
            raise AuditError(f"duplicate reviewed similarity record: {key[1]}")
        rationale = record.get("rationale")
        disposition = record.get("disposition")
        if not isinstance(rationale, str) or not rationale.strip() or not isinstance(disposition, str) or not disposition:
            raise AuditError(f"reviewed_similarity_findings[{index}] lacks disposition/rationale")
        records_by_key[key] = record

    used_review_records = set()
    for finding in findings:
        if finding.severity != "review":
            continue
        key = (finding.skill, finding.path, finding.evidence["sha256"])
        record = records_by_key.get(key)
        if record:
            finding.adjudication = {
                "disposition": record["disposition"],
                "rationale": record["rationale"],
            }
            used_review_records.add(key)
    stale_records = [
        {
            "skill": key[0],
            "path": key[1],
            "sha256": key[2],
            "detail": "record no longer matches a current review finding",
        }
        for key in sorted(set(records_by_key) - used_review_records)
    ]
    adjudicated = sum(item.severity == "review" and item.adjudication is not None for item in findings)
    unreviewed = review - adjudicated
    return {
        "schema_version": 1,
        "scope": "origin_groups.independently_rebuilt",
        "baseline_commit": baseline_commit,
        "current_commit": current_commit,
        "thresholds": asdict(thresholds),
        "summary": {
            "skills_checked": len(rebuilt),
            "current_files_checked": files_checked,
            "baseline_files_checked": baseline_files_checked,
            "material_findings": material,
            "review_findings": review,
            "adjudicated_review_findings": adjudicated,
            "unreviewed_review_findings": unreviewed,
            "stale_review_records": len(stale_records),
            "new_original_lineage_checked": len(new_original_lineage),
        },
        "new_original_lineage": new_original_lineage,
        "skill_summaries": skill_summaries,
        "findings": [asdict(item) for item in findings],
        "stale_review_records": stale_records,
        "limitations": [
            "Only known artifacts present in the frozen Git baseline are compared.",
            "Token and hash similarity are screening evidence, not a legal conclusion.",
            "Binary files are hash-compared but their internal structure is not analyzed.",
        ],
        "worktree_dirty": bool(worktree.strip()),
    }


def exit_code(report: dict, fail_on: str) -> int:
    summary = report["summary"]
    if fail_on == "never":
        return 0
    if fail_on == "review":
        return 1 if summary["material_findings"] or summary["review_findings"] or summary["stale_review_records"] else 0
    if fail_on == "unreviewed":
        return 1 if summary["material_findings"] or summary["unreviewed_review_findings"] or summary["stale_review_records"] else 0
    return 1 if summary["material_findings"] else 0


def print_text(report: dict) -> None:
    summary = report["summary"]
    print(
        "baseline={baseline} current={current} skills={skills} files={files} "
        "material={material} review={review} unreviewed={unreviewed} stale={stale}".format(
            baseline=report["baseline_commit"],
            current=report["current_commit"],
            skills=summary["skills_checked"],
            files=summary["current_files_checked"],
            material=summary["material_findings"],
            review=summary["review_findings"],
            unreviewed=summary["unreviewed_review_findings"],
            stale=summary["stale_review_records"],
        )
    )
    for finding in report["findings"]:
        evidence = finding["evidence"]
        print(
            f"{finding['severity']}{'-adjudicated' if finding['adjudication'] else ''}: "
            f"{finding['skill']}: {finding['path']}: "
            f"{finding['code']} windows={evidence['matching_window_positions']}/"
            f"{evidence['window_positions']} candidate_longest={evidence['longest_candidate_token_run']} "
            f"long_lines={evidence['matching_long_lines']}"
        )
    for record in report["stale_review_records"]:
        print(f"stale-review: {record['skill']}: {record['path']}: {record['sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--baseline", help="Git commit to use instead of the manifest baseline")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--fail-on", choices=("never", "material", "unreviewed", "review"), default="unreviewed"
    )
    args = parser.parse_args()
    try:
        report = audit_repository(Path(args.root), args.baseline)
    except AuditError as error:
        print(f"audit-originality: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    raise SystemExit(exit_code(report, args.fail_on))


if __name__ == "__main__":
    main()
