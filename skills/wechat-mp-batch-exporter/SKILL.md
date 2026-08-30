---
name: wechat-mp-batch-exporter
description: Build a bounded, private archive from known WeChat Official Account article URLs or an owner-authorized account-history export, with explicit reconciliation of article, publish-group, and platform-marked-original counts. Use for batch body capture, history normalization, or enhanced metrics/comments workflows. Do not use for a one-page summary or to automate the WeChat client.
---

# WeChat Official Account archive

Separate public URL capture, account-history access, and credential-assisted metrics. They have different authorization and evidence requirements.

Read [references/examples.md](references/examples.md). For account/exporter integration read [references/exporter-workflow.md](references/exporter-workflow.md); for human-controlled steps read [references/manual-gates.md](references/manual-gates.md).

## Boundaries

- Never control the desktop or mobile WeChat interface.
- Never publish, message, follow, delete, or change an account.
- Do not expose or save cookies, `auth-key`, `pass_ticket`, tokens, QR material, account identifiers, or credential files in reports.
- Do not bypass access controls or retrieve private/deleted material outside the owner's authorization.
- Downloaded articles retain their authors' rights. Default to private analysis/archiving, not redistribution.
- Certificate trust and system proxy changes are manual, separately approved operations; bundled scripts do not perform them.

## Classify the request

| Requested result | Route |
|---|---|
| Bodies for a finite list of known public article URLs | bundled `download_urls.py` |
| Historical article list for an account the user controls | external exporter checkout and user login |
| Read/like/share/comment metrics or comment bodies | owner-authorized external exporter plus credential helper |
| Reconcile history totals and original flags | bundled `analyze_history.py` |

Do not make the high-privilege route the default merely because it is installed.

## Read-only readiness report

Resolve this Skill's directory and run:

```bash
python3 <skill-dir>/scripts/doctor.py
```

Use `--check-network` only when the task will call the configured public API. The report inventories local checkouts and tools without reading credentials, opening WeChat, altering proxies, or installing certificates.

## Known public URLs

First preview the exact deduplicated list:

```bash
python3 <skill-dir>/scripts/download_urls.py \
  --file /absolute/path/urls.txt \
  --format markdown
```

After reviewing count, URLs, API base, and output format, add `--apply`:

```bash
python3 <skill-dir>/scripts/download_urls.py \
  --file /absolute/path/urls.txt \
  --format markdown \
  --output /absolute/path/archive-run \
  --apply
```

The output directory must be new. Inspect `index.csv`, `failures.json`, and representative article files. Report successes and failures separately; a partial run is not a full archive.

## History reconciliation

An exported history contains several non-equivalent totals. Run:

```bash
python3 <skill-dir>/scripts/analyze_history.py \
  --history-json /absolute/path/history.json \
  --output-dir /absolute/path/reconciled
```

Chunked input is also supported with `--chunk-dir`. Use these output labels:

- `expanded_articles`: distinct article identities after multi-article messages are expanded;
- `publish_groups`: distinct `msgid` values when available;
- `headline_articles`: records whose item position is 1;
- `marked_original_articles`: non-deleted records where both upstream copyright flags equal 1.

Never collapse these into a bare “article count”. When a platform UI differs, state its apparent scope and compare like with like.

## External exporter and enhanced fields

The repositories `wechat-article/wechat-article-exporter` and `wechat-article/wxdown-service` are external products; their code is not bundled here. Verify their current instructions, version, license, and checkout before use.

Preview a local credential-helper launch:

```bash
python3 <skill-dir>/scripts/start_wxdown_service.py \
  --project /absolute/path/wxdown-service
```

Only after the user approves the displayed project, interpreter, entrypoint, ports, and proxy-environment policy:

```bash
python3 <skill-dir>/scripts/start_wxdown_service.py \
  --project /absolute/path/wxdown-service \
  --apply
```

The user performs QR login, account selection, certificate decisions, proxy changes, and required navigation. Fresh credentials may still lack fields or expire; preserve unknown values and errors instead of substituting zero.

## Archive contract

Read [references/output-schema.md](references/output-schema.md) before merging body, history, metrics, or comment data. Keep raw exporter results separate from normalized records. Every normalized article should retain its source URL, retrieval time, access mode, and per-field availability.

Do not include credential material in the archive. If debugging requires sensitive evidence, stop and define a separate private artifact with explicit retention and deletion rules.

## Verification

Before completion:

1. reconcile input object count, duplicates, normalized articles, publish groups, and marked-original records;
2. open a sample of saved article bodies and confirm source URLs;
3. check failure records rather than retrying indefinitely;
4. confirm output paths contain no credential files or secret values;
5. disclose external-tool versions, authentication limitations, and missing fields.

Completion means the requested bounded archive and count scopes are verifiable, not that every platform field was obtainable.
