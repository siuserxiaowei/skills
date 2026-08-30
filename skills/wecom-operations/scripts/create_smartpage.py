#!/usr/bin/env python3
"""Preview or create a WeCom SmartPage from a Markdown file."""

from __future__ import annotations

import argparse
import datetime as datetime_module
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


MARKDOWN_IMAGE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<destination><[^>\n]+>|[^)\n]+)\)")


@dataclass(frozen=True)
class ImageReference:
    markdown: str
    alt: str
    destination: str
    kind: str
    local_path: str | None


class CliError(RuntimeError):
    pass


def unwrap_response(stdout: str) -> dict:
    try:
        envelope = json.loads(stdout)
        if isinstance(envelope, dict) and "errcode" not in envelope:
            text = envelope["result"]["content"][0]["text"]
            envelope = json.loads(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise CliError("wecom-cli returned an unrecognized response") from exc
    if not isinstance(envelope, dict):
        raise CliError("wecom-cli business response is not an object")
    if envelope.get("errcode") != 0:
        detail = envelope.get("help_message") or envelope.get("errmsg") or "unknown error"
        raise CliError(f"WeCom rejected the operation: {detail}")
    return envelope


class WeComClient:
    def __init__(self, executable: str):
        self.executable = executable

    def invoke(self, category: str, operation: str, payload: dict, *, helper: str | None = None, extra: list[str] | None = None) -> dict:
        command = [helper or self.executable, category, operation]
        if extra:
            command.extend(extra)
        else:
            command.append(json.dumps(payload, ensure_ascii=False))
        result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            raise CliError((result.stderr or result.stdout).strip() or f"command exited {result.returncode}")
        return unwrap_response(result.stdout)


def destination_text(raw: str) -> str:
    value = raw.strip()
    return value[1:-1] if value.startswith("<") and value.endswith(">") else value


def inspect_images(markdown: str, source: Path) -> list[ImageReference]:
    references: list[ImageReference] = []
    for match in MARKDOWN_IMAGE.finditer(markdown):
        destination = destination_text(match.group("destination"))
        parsed = urlparse(destination)
        if parsed.scheme in ("http", "https"):
            references.append(ImageReference(match.group(0), match.group("alt"), destination, "remote", None))
            continue
        if parsed.scheme == "data":
            raise CliError("inline data images are unsupported; use a local file or hosted URL")
        candidate = Path(unquote(parsed.path if parsed.scheme == "file" else destination))
        if not candidate.is_absolute():
            candidate = source.parent / candidate
        resolved = candidate.resolve(strict=False)
        if not resolved.is_file():
            raise CliError(f"local image is missing: {resolved}")
        references.append(ImageReference(match.group(0), match.group("alt"), destination, "local", str(resolved)))
    return references


def private_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def upload_local_images(client: WeComClient, helper: str, title: str, references: list[ImageReference]) -> tuple[dict[str, str], dict]:
    resource = client.invoke("doc", "create_doc", {"doc_type": 3, "doc_name": f"{title} - image resources"})
    docid = str(resource.get("docid") or "")
    if not docid:
        raise CliError("resource document creation returned no docid")
    uploaded: dict[str, str] = {}
    for path in dict.fromkeys(reference.local_path for reference in references if reference.local_path):
        response = client.invoke(
            "doc",
            "+doc_upload_image",
            {},
            helper=helper,
            extra=["--docid", docid, "--image-path", str(path)],
        )
        url = response.get("url")
        if not url:
            raise CliError(f"image upload returned no URL: {path}")
        uploaded[str(path)] = str(url)
    return uploaded, resource


def replace_local_images(markdown: str, source: Path, mapping: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        destination = destination_text(match.group("destination"))
        parsed = urlparse(destination)
        if parsed.scheme in ("http", "https"):
            return match.group(0)
        candidate = Path(unquote(parsed.path if parsed.scheme == "file" else destination))
        if not candidate.is_absolute():
            candidate = source.parent / candidate
        url = mapping[str(candidate.resolve(strict=False))]
        return f"![{match.group('alt')}]({url})"

    return MARKDOWN_IMAGE.sub(replace, markdown)


def state_root() -> Path:
    configured = os.environ.get("WECOM_OPERATIONS_STATE_ROOT")
    return Path(configured).expanduser() if configured else Path("~/.local/state/wecom-operations").expanduser()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--page-title", default="正文")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    source = args.source.expanduser().resolve(strict=False)
    if not source.is_file():
        parser.error(f"source is not a file: {source}")
    if source.stat().st_size > 10 * 1024 * 1024:
        parser.error("source exceeds the 10 MiB safety limit")
    markdown = source.read_text(encoding="utf-8")
    references = inspect_images(markdown, source)
    local = [reference for reference in references if reference.kind == "local"]
    preview = {
        "source": str(source),
        "title": args.title,
        "page_title": args.page_title,
        "local_image_files": len({reference.local_path for reference in local}),
        "remote_image_references": sum(reference.kind == "remote" for reference in references),
        "creates_resource_document": bool(local),
        "creates_smartpage": True,
        "apply": args.apply,
    }
    if not args.apply:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    executable = os.environ.get("WECOM_CLI") or shutil.which("wecom-cli")
    if not executable:
        raise CliError("wecom-cli is unavailable")
    helper = os.environ.get("WECOM_UPLOAD_HELPER")
    if local and (not helper or not Path(helper).expanduser().is_file() or not os.access(Path(helper).expanduser(), os.X_OK)):
        raise CliError("local images require an executable WECOM_UPLOAD_HELPER")
    client = WeComClient(executable)
    resource = None
    if local:
        mapping, resource = upload_local_images(client, str(Path(helper).expanduser()), args.title, references)
        markdown = replace_local_images(markdown, source, mapping)
    run_id = datetime_module.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    run_dir = state_root() / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    upload_copy = run_dir / source.name
    private_write(upload_copy, markdown)
    created = client.invoke(
        "doc",
        "+smartpage_create",
        {"title": args.title, "pages": [{"page_title": args.page_title, "content_type": 1, "page_filepath": str(upload_copy)}]},
    )
    receipt = {
        "created_at": datetime_module.datetime.now().astimezone().isoformat(),
        "source": str(source),
        "run_id": run_id,
        "smartpage_docid": created.get("docid"),
        "smartpage_url": created.get("url"),
        "resource_docid": resource.get("docid") if resource else None,
        "resource_url": resource.get("url") if resource else None,
        "local_images_uploaded": len({reference.local_path for reference in local}),
    }
    private_write(run_dir / "receipt.json", json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    public = {key: receipt[key] for key in ("run_id", "smartpage_url", "resource_url", "local_images_uploaded")}
    print(json.dumps(public, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CliError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
