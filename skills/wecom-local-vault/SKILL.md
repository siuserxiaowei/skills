---
name: wecom-local-vault
description: Inspect authorized local WeCom databases on macOS, create private plaintext snapshots, and query or export contacts, conversations, and messages without modifying the source account store. Use when the user asks to parse 企业微信/WeCom local data, recover a private database snapshot, inspect local contacts or sessions, search chat history, or export a bounded conversation.
---

# WeCom local vault

Use this Skill only for data the user is entitled to inspect. The operating model is source read-only: discover an account store, validate a captured 16-byte secret against encrypted page one, materialize a new protected snapshot, then run every query against that snapshot.

Read [references/examples.md](references/examples.md) for complete positive, boundary, and recovery cases. Read [references/database-notes.md](references/database-notes.md) only when inspecting or adapting database schemas.

## Inputs and prerequisites

- Confirm the user is entitled to inspect the local dataset and select a passive inspection, secret capture, snapshot, bounded query, or export.
- Provide or choose an exact dataset label/data directory; multiple discovered accounts must be resolved by the user, not by inspecting private contents.
- Snapshot/decrypt requires a candidate secret that validates against page one. Query/export requires a pinned private snapshot, exact conversation, time bounds/timezone, and a new owner-only destination.
- Process attachment, a copied signed app, and sudo scanning are distinct authorization gates. Failure of one route does not authorize the next.

## Safety contract

- Never drive the WeCom interface or send a message.
- `discover`, `status`, `list`, and `doctor` are passive. Process attachment, launching a re-signed copy, and sudo memory reading each require their own explicit flag in the current run.
- Never change a source database or its WAL. Snapshot, key, diagnostic, and export files stay under the private vault unless the user explicitly supplies another private destination.
- Existing outputs are not replaced. Secrets never appear in terminal output. Do not paste internal IDs or unrelated private-message bodies into the response.
- Do not disable SIP, alter task-port policy, or install dependencies automatically.

The default vault is `~/Library/Application Support/wecom-local-vault`. `WECOM_LOCAL_VAULT_HOME` can select a different private root. A JSON config at `~/.config/wecom-local-vault.json` may set `vault_dir` and `data_dir`.

## First inspection

Set `SKILL_DIR` to this directory, then run:

```bash
VAULT_CLI="$SKILL_DIR/scripts/vault_cli.py"
CAPTURE_HELPER="$SKILL_DIR/scripts/capture_key_macos.py"
python3 "$VAULT_CLI" status
python3 "$VAULT_CLI" discover
python3 "$CAPTURE_HELPER" doctor
```

Paths are omitted from discovery output unless `--show-paths` is requested. When more than one account is found, choose one with `--data-dir`.

## Secret acquisition

Attaching to an already-running process requires explicit authorization:

```bash
python3 "$SKILL_DIR/scripts/capture_key_macos.py" capture --confirm-attach --duration 60
```

If macOS blocks attachment, stop. With a separate user instruction permitting a copied and ad-hoc-signed application, use:

```bash
python3 "$CAPTURE_HELPER" capture --duration 240 \
  --confirm-signed-copy --mode=spawn-signed-copy
```

The capture agent observes known CommonCrypto/SQLite key paths. A candidate is saved at mode `0600` only after it decrypts a supported database first page and yields a valid SQLite B-tree marker.

As a separate fallback, the Mach scanner reads a known WeCom 5.x `DbKeyManager` object layout without code injection. It is version-sensitive and asks for administrator credentials in the local terminal:

```bash
python3 "$SKILL_DIR/scripts/scan_dbkey_manager_macos.py" scan --confirm-sudo
```

Never infer that a timeout means the database is unsupported; the application may simply not have exercised a hooked path during the observation window.

## Snapshot creation

```bash
python3 "$VAULT_CLI" decrypt --key-file "/private/location/key.json"
python3 "$VAULT_CLI" decrypt
```

Every run creates a new `0700` timestamp directory. Database files and `manifest.json` are `0600`. By default, complete frames through the final commit marker in a matching-salt WAL are decrypted into the new SQLite image. `--no-wal` is available when an evidence workflow intentionally excludes WAL state.

## Read and export

```bash
CLI=(python3 "$SKILL_DIR/scripts/vault_cli.py")
"${CLI[@]}" contacts --query "name"
"${CLI[@]}" sessions --limit 50
"${CLI[@]}" search "term" --chat "room" --limit 200
"${CLI[@]}" history "room or conversation_id" --start "2026-08-01" --limit 500
"${CLI[@]}" export "room" --format markdown
```

Pass `--snapshot` to pin a specific evidence version. Export refuses an existing destination. Read [references/database-notes.md](references/database-notes.md) before adapting schemas, and [references/examples.md](references/examples.md) for acceptance evidence.

## Known limits

- The supported page codec is the observed 4096-byte wxSQLite3-style AES-128 layout. Unknown headers fail closed.
- Message text extraction handles direct UTF-8 and conservative protobuf length-delimited strings; media payloads remain labeled binary content.
- The Frida agent intentionally avoids private, build-specific symbol offsets. The memory scanner retains one known 5.x object layout and must be revalidated after a client update.
- Direction labels such as “me” are not inferred without a separately verified self identifier.

## Operational acceptance

- The selected dataset label, snapshot directory, manifest and query/export bounds are explicit.
- Source database and WAL metadata remain unchanged; all generated material is owner-only and no output was overwritten.
- Conversation resolution, time bounds, message counts and media/binary limitations are reported without exposing secrets or unrelated internal IDs.
- Partial or unsupported results are labeled as such; a readable SQLite header alone is not claimed as a complete successful export.

## Offline verification

```bash
python3 -m unittest discover -s "$SKILL_DIR/tests" -v
python3 -m py_compile "$SKILL_DIR"/scripts/*.py "$SKILL_DIR"/tests/*.py
VALIDATOR="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
python3 "$VALIDATOR" "$SKILL_DIR"
```

## Failure and recovery

Unsupported headers, schemas, page layouts, WAL state, or memory layouts fail closed. Preserve the diagnostic and require fixture-based compatibility tests before retrying live data; never reinterpret unknown bytes as plaintext or infer that a capture timeout proves an invalid key.
