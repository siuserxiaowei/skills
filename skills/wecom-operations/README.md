# WeCom Operations

Work with owner-authorized WeCom documents, todos, meetings, and schedules via the official [`@wecom/cli`](https://github.com/WecomTeam/wecom-cli). The WeCom desktop app is never automated, and no messages are ever sent.

## What it can do

- Turn local Markdown into normal documents or smart documents.
- Read back or fully overwrite a document, but only after target and permission checks pass.
- Create, inspect, update, and remove todos behind confirmation gates.
- Book, query, modify, or cancel meetings and schedules where the tenant has opened those categories.
- Dry-run every write first; destructive or replacing actions ask for an explicit go-ahead.
- Keep internal IDs and receipts inside private local state only.

## Setup

Get the official CLI installed and configured before anything else:

```bash
npm install -g @wecom/cli
wecom-cli init
```

`wecom-cli init` is for first-time setup only. When `~/.config/wecom/` already holds the encrypted configuration files, leave the existing configuration untouched instead of overwriting it.

After that, probe the runtime:

```bash
python3 "$HOME/.agents/skills/wecom-operations/scripts/doctor.py"
python3 "$HOME/.agents/skills/wecom-operations/scripts/doctor.py" --category doc
```

## Working with local images

Out of the box, the official CLI writes text documents and embeds images that are already hosted. The bundled `create_smartpage.py` rewrites local Markdown image paths too, yet actually pushing those files up to WeCom requires a separately supplied executable offering `doc +doc_upload_image`:

```bash
export WECOM_UPLOAD_HELPER=/absolute/path/to/wecom-cli-with-doc-upload-image
```

This helper is an external local extension and does not ship with this repository. If it is missing, stick to Markdown without local images, or swap in authorized remote image URLs ahead of execution.

## Privacy and safety rules

- The WeCom desktop UI is never driven, and the message category is never invoked.
- Encrypted credential contents under `~/.config/wecom/` are never read or printed.
- Every write needs a user instruction from the current task; cancellation, deletion, and whole-document overwrite additionally require reconfirmation of the exact target.
- Bot IDs, secrets, user IDs, document/meeting/todo IDs, authorization URLs, receipts, source documents, and customer data must not be committed anywhere.
- Which categories are usable depends on the tenant, so availability is always probed dynamically.

## Upstream runtime and license

Original files in this directory are covered by the repository's [Personal Learning and Non-Commercial Use License](LICENSE). The [`WeComTeam/wecom-cli`](https://github.com/WecomTeam/wecom-cli) runtime itself is external, maintained by WeComTeam under its own MIT License — no upstream CLI source or binary is vendored into this repository.
