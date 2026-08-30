#!/usr/bin/env python3
"""Build the isolated npm/PyPI/Docker Hub discovery shard from official APIs."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "research"
    / "run-pi-platform10-20260826"
    / "workers"
    / "api-packages-candidates.jsonl"
)
USER_AGENT = "pi-runtime-field-guide-research/1.0 (read-only)"
ACCESSED_AT = "2026-08-26"

NPM_PACKAGES = [
    ("@earendil-works/pi-agent-core", "npm-official-runtime", "official runtime package"),
    ("@earendil-works/pi-ai", "npm-official-runtime", "official unified model API package"),
    ("@earendil-works/pi-client", "npm-official-runtime", "official remote-session client package"),
    ("@earendil-works/pi-coding-agent", "npm-official-runtime", "official coding-agent CLI and SDK package"),
    ("@earendil-works/pi-protocol", "npm-official-runtime", "official remote-session protocol package"),
    ("@earendil-works/pi-radius", "npm-official-runtime", "official Pi provider and web-search extension"),
    ("@earendil-works/pi-radius-work", "npm-official-runtime", "official Google Workspace and image extension"),
    ("@earendil-works/pi-server", "npm-official-runtime", "official experimental server package"),
    ("@earendil-works/pi-session-backend-sqlite-node", "npm-official-runtime", "official SQLite session backend"),
    ("@earendil-works/pi-storage-sqlite-node", "npm-official-runtime", "official SQLite storage backend"),
    ("@earendil-works/pi-telemetry", "npm-official-runtime", "official telemetry contracts package"),
    ("@earendil-works/pi-tui", "npm-official-runtime", "official terminal UI package"),
    ("@earendil-works/pi-web-ui", "npm-official-runtime", "official reusable web UI package"),
    ("@automatalabs/pi-acp", "npm-ecosystem-adapters", "in-process ACP server embedding Pi SDK"),
    ("@ai-sdk/harness-pi", "npm-ecosystem-adapters", "HarnessV1 adapter backed by Pi coding agent"),
    ("pi-acp", "npm-ecosystem-adapters", "ACP adapter for Pi coding agent"),
    ("pi-background-tasks", "npm-ecosystem-adapters", "durable background and delegated-agent Pi extension"),
    ("pi-mcp-adapter", "npm-ecosystem-adapters", "MCP adapter extension for Pi coding agent"),
    ("pi-subagents", "npm-ecosystem-adapters", "delegation and multi-agent workflow extension"),
    ("pi-web-ui", "npm-ecosystem-adapters", "web interface powered by the Pi SDK"),
]

PYPI_PACKAGES = [
    ("pi-py-agent-core", "pypi-python-ports", "Python port of official Pi agent core"),
    ("pi-py-ai", "pypi-python-ports", "Python port of official Pi model API"),
    ("pi-py-coding-agent", "pypi-python-ports", "Python port of official Pi coding-agent SDK"),
    ("pi-py-server", "pypi-python-ports", "Python port of official Pi server"),
    ("pi-py-storage-sqlite", "pypi-python-ports", "Python port of official Pi SQLite storage"),
    ("pp-agent-core", "pypi-runtime-components", "independent Python port of official Pi agent core"),
    ("pp-ai", "pypi-runtime-components", "independent Python port of official Pi model API"),
    ("pp-coding-agent", "pypi-runtime-components", "independent Python port of official Pi coding agent"),
    ("pp-evals", "pypi-runtime-components", "Python port of Pi workflow evals"),
    ("pp-rpc-client", "pypi-runtime-components", "Python port of Pi remote-session client"),
    ("pp-rpc-protocol", "pypi-runtime-components", "Python port of Pi CBOR protocol"),
    ("pp-rpc-server", "pypi-runtime-components", "Python port of Pi remote-session server"),
    ("pp-telemetry", "pypi-runtime-components", "Python port of Pi telemetry contracts"),
    ("pp-tui", "pypi-runtime-components", "Python port of Pi terminal UI"),
    ("pi-ai-client", "pypi-runtime-components", "async Python client port of official Pi model API"),
]

DOCKER_REPOSITORIES = [
    ("stck", "pi", "docker-exact-alias", "repository description explicitly names earendil-works/pi"),
    ("stefan2904", "pi-coding-agent", "docker-exact-alias", "exact Pi coding-agent repository name with active versioned tags"),
    ("hoax859", "pi-coding-agent", "docker-exact-alias", "exact Pi coding-agent repository name with 0.82.1 tag"),
    ("jarvisquilter", "pi-coding-agent", "docker-exact-alias", "exact Pi coding-agent repository name with public manifest"),
    ("dbellkoff", "pi-harness", "docker-harness-alias", "exact Pi harness repository name with public manifest"),
]


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def clean_date(value: str | None) -> str:
    return value[:10] if value else "unknown"


def slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-").replace("--", "-")


def item(
    *,
    candidate_id: str,
    platform_id: str,
    title: str,
    canonical_url: str,
    creator_name: str,
    published_at: str,
    date_basis: str,
    content_type: str,
    content_track: str,
    summary: str,
    why_useful: str,
    discovery_backend: str,
    readback_backend: str,
    evidence_status: str,
    limitations: str,
    query_id: str,
    readback_evidence: str,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "platform_id": platform_id,
        "title": title,
        "canonical_url": canonical_url,
        "creator_name": creator_name or "unknown",
        "published_at": published_at,
        "date_basis": date_basis,
        "accessed_at": ACCESSED_AT,
        "language": "en",
        "content_type": content_type,
        "content_track": content_track,
        "summary": summary,
        "why_useful": why_useful,
        "discovery_backend": discovery_backend,
        "readback_backend": readback_backend,
        "evidence_status": evidence_status,
        "limitations": limitations,
        "query_id": query_id,
        "readback_evidence": readback_evidence,
    }


def npm_rows() -> list[dict]:
    rows = []
    for package_name, query_id, relevance in NPM_PACKAGES:
        encoded = urllib.parse.quote(package_name, safe="")
        document = get_json(f"https://registry.npmjs.org/{encoded}")
        version = document["dist-tags"]["latest"]
        release = document["versions"][version]
        description = release.get("description") or document.get("description") or "No package description"
        author = release.get("author") or document.get("author") or {}
        if isinstance(author, str):
            author_name = author
        else:
            author_name = author.get("name", "")
        if not author_name:
            maintainers = document.get("maintainers") or []
            author_name = maintainers[0].get("name", "unknown") if maintainers else "unknown"
        repository = release.get("repository") or document.get("repository") or {}
        repository_url = repository if isinstance(repository, str) else repository.get("url", "")
        readme_length = len(document.get("readme") or "")
        rows.append(
            item(
                candidate_id=f"api-packages-npm-{slug(package_name)}",
                platform_id="npm",
                title=f"{package_name} {version}",
                canonical_url=f"https://www.npmjs.com/package/{package_name}",
                creator_name=author_name,
                published_at=clean_date(document.get("time", {}).get(version)),
                date_basis=f"official npm registry time[{version}]",
                content_type="package",
                content_track="生态与案例" if query_id.endswith("adapters") else "进阶",
                summary=f"npm 官方 registry 回读 {package_name} {version}：{description}。仓库字段为 {repository_url or 'unknown'}，readme 长度 {readme_length}。",
                why_useful=f"该包是 {relevance}，可用来追踪 Pi 运行时拆分、版本和扩展生态。",
                discovery_backend="npm_registry_search_and_exact_alias_list",
                readback_backend="official_npm_registry_package_document",
                evidence_status="curator_review_ready",
                limitations="仅读取公开 registry 元数据与 README，未安装或执行包；仍需主策展人复核供应链、版本和近重复。",
                query_id=query_id,
                readback_evidence=f"registry document HTTP read; name={document.get('name')}; dist-tag latest={version}; version timestamp={document.get('time', {}).get(version)}; readme_length={readme_length}",
            )
        )
    return rows


def pypi_rows() -> list[dict]:
    rows = []
    for project_name, query_id, relevance in PYPI_PACKAGES:
        document = get_json(f"https://pypi.org/pypi/{urllib.parse.quote(project_name)}/json")
        info = document["info"]
        version = info["version"]
        files = document.get("urls") or []
        upload_times = sorted(file.get("upload_time_iso_8601", "") for file in files if file.get("upload_time_iso_8601"))
        project_urls = info.get("project_urls") or {}
        upstream = project_urls.get("Upstream") or project_urls.get("Repository") or project_urls.get("Homepage") or "unknown"
        summary = info.get("summary") or "No project summary"
        rows.append(
            item(
                candidate_id=f"api-packages-pypi-{slug(project_name)}",
                platform_id="pypi",
                title=f"{info.get('name', project_name)} {version}",
                canonical_url=f"https://pypi.org/project/{project_name}/",
                creator_name=info.get("author") or info.get("author_email") or "unknown",
                published_at=clean_date(upload_times[-1] if upload_times else None),
                date_basis=f"official PyPI release file upload_time_iso_8601 for {version}",
                content_type="package",
                content_track="生态与案例",
                summary=f"PyPI 官方 project record 回读 {info.get('name')} {version}：{summary}。项目上游链接为 {upstream}，当前发布文件 {len(files)} 个。",
                why_useful=f"该项目是 {relevance}，提供 Pi TypeScript 运行时的 Python 移植/互操视角。",
                discovery_backend="github_code_exact_upstream_reference_then_pypi_project_lookup",
                readback_backend="official_pypi_json_metadata_probe_canonical_page_challenged",
                evidence_status="metadata_only",
                limitations="PyPI 元数据由发布者上传，平台存在不等于安全背书。canonical project HTML 在 curl 和正常 Chrome 中均返回 Client Challenge；当前平台规则又不允许将 /pypi/*/json 批量路径当作常规回读。因此只标 metadata_only，不得进入主审候选；需用规则允许的 package client 或用户浏览器重读。",
                query_id=query_id,
                readback_evidence=f"official project JSON metadata probe; canonical HTML returned Client Challenge in curl and normal Chrome; normalized name={info.get('name')}; version={version}; release_files={len(files)}; latest_upload={upload_times[-1] if upload_times else 'unknown'}; description_length={len(info.get('description') or '')}; upstream={upstream}",
            )
        )
    return rows


def docker_rows() -> list[dict]:
    rows = []
    for namespace, repository, query_id, relevance in DOCKER_REPOSITORIES:
        detail_url = f"https://hub.docker.com/v2/repositories/{namespace}/{repository}/"
        tag_url = f"https://hub.docker.com/v2/repositories/{namespace}/{repository}/tags?page_size=100"
        document = get_json(detail_url)
        tag_document = get_json(tag_url)
        tags = tag_document.get("results") or []
        latest = next((tag for tag in tags if tag.get("name") == "latest"), tags[0] if tags else {})
        description = document.get("description") or document.get("full_description") or "repository description unavailable"
        provenance_strong = bool(document.get("description") or document.get("full_description"))
        rows.append(
            item(
                candidate_id=f"api-packages-docker-{slug(namespace)}-{slug(repository)}",
                platform_id="docker_hub",
                title=f"{namespace}/{repository}",
                canonical_url=f"https://hub.docker.com/r/{namespace}/{repository}",
                creator_name=namespace,
                published_at=clean_date(document.get("date_registered")),
                date_basis="official Docker Hub repository date_registered",
                content_type="container_repository",
                content_track="生态与案例",
                summary=f"Docker Hub 官方 repository/detail 与 tags API 回读 {namespace}/{repository}：{description}。公开 tags {len(tags)} 个，latest digest 为 {latest.get('digest', 'unknown')}。",
                why_useful=f"该容器对象具有 {relevance}，可评估 Pi 的容器化交付现状。",
                discovery_backend="official_docker_hub_exact_alias_search",
                readback_backend="official_docker_hub_repository_detail_and_tags_api",
                evidence_status=("curator_review_ready" if provenance_strong else "metadata_only"),
                limitations=(
                    "官方 detail 提供了明确 Pi 描述，但未拉取或运行镜像；仍需主策展人复核 Dockerfile/仓库溯源。"
                    if provenance_strong
                    else "只有精确名称、公开 tag/digest 和日期元数据，无 description/full_description/repo_url；必须先做外部溯源才能主审，不得仅因同名接受。"
                ),
                query_id=query_id,
                readback_evidence=f"official Hub APIs HTTP read; namespace={document.get('namespace')}; name={document.get('name')}; private={document.get('is_private')}; registered={document.get('date_registered')}; updated={document.get('last_updated')}; tags={len(tags)}; latest_digest={latest.get('digest', 'unknown')}; description_present={provenance_strong}",
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = npm_rows() + pypi_rows() + docker_rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    counts = {platform_id: sum(row["platform_id"] == platform_id for row in rows) for platform_id in ("npm", "pypi", "docker_hub")}
    print(json.dumps({"output": str(args.output), "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
