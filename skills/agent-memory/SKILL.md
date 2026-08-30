---
name: agent-memory
description: Design, inspect, migrate, and operate a private Markdown-first memory system shared by coding agents. Use when the user asks for durable agent memory, a local knowledge vault, retrieval/index repair, cross-agent write coordination, or a privacy-preserving memory migration. Do not use for ordinary project documentation or to store conversation data without explicit scope.
---

# Agent Memory

Use this Skill to make durable memory inspectable and recoverable. The memory system may have its own commands, but its source of truth must remain readable without those commands.

Read [references/examples.md](references/examples.md) before acting. Treat every real vault as private user data.

## Define the memory boundary

Resolve these facts from the user's request, existing configuration, or a read-only inspection:

- the canonical memory root;
- the host applications that read or write it;
- the record formats and required metadata;
- the derived search/index locations;
- whether version control or remote backup exists;
- which operation is requested: inspect, design, migrate, retrieve, write, repair, or automate.

Do not guess a vault path, copy a whole home directory, or treat a search index as authoritative. If more than one plausible vault exists, present the paths and the evidence that distinguishes them before writing.

## Use a source/derivative split

Keep the system in four explicit layers:

1. **Records** — human-readable Markdown and intentionally attached assets. These are authoritative.
2. **Catalog** — deterministic metadata such as record ID, title, topic, timestamps, status, and source links.
3. **Indexes** — FTS tables, embeddings, caches, or other rebuildable search data.
4. **Adapters** — host-specific rules, hooks, and commands that call the same record and catalog contracts.

Never allow layers 2–4 to silently rewrite layer 1. A repaired index may change search results; it must not change the remembered fact.

## Inspect before changing anything

Start with the narrowest available inventory. Prefer project-provided read-only commands. Otherwise inspect filenames, configuration, and status without printing record bodies unnecessarily.

Record:

- exact paths and whether they are inside Git;
- file counts by type;
- configuration that selects the active root;
- index format and last successful build signal;
- pending changes, locks, or ownership markers;
- ignored/private files and any remote destination.

Run a secret-path and publication-risk review before proposing a remote backup. The presence of Git does not imply that pushing is authorized.

## Record contract

Use the vault's existing schema when one exists. For a new system, keep a compact contract:

```yaml
id: stable-human-readable-id
title: concise claim or procedure
kind: fact | decision | workflow | preference | source-note
status: active | superseded | disputed
created_at: 2026-08-30T09:00:00+08:00
verified_at: 2026-08-30T09:00:00+08:00
sources:
  - local-or-public-reference
supersedes: []
```

The body should state one durable idea, its context, and the evidence needed to use it. Do not invent `verified_at`; a file modification time is not verification.

## Retrieval workflow

1. Search metadata or full text using the user's terms and close variants.
2. Rank by direct claim match, current status, verification freshness, and source quality.
3. Open the underlying records for the top candidates.
4. Separate quoted record facts from your inference.
5. Report conflicts, superseded records, and missing coverage.

Semantic results are candidates, not facts. If semantic search is unavailable, fall back to metadata and text search. If the two routes disagree, the source record and its status fields decide what is current.

## Write workflow

Before a durable write:

- summarize the proposed memory in one sentence;
- search for an existing record expressing the same claim;
- choose `add`, `update`, `supersede`, `merge`, or `do nothing`;
- identify sensitive content and remove anything outside the approved scope;
- preserve links to the evidence and to any replaced record.

Write the smallest coherent change. Re-read the saved record, then rebuild only the affected derived state. Verify retrieval using a query that should find the record and a control query that should not.

If two active records conflict, do not pick the convenient one. Mark the conflict or ask the user which claim is authoritative.

## Cross-agent coordination

Shared memory needs explicit ownership:

- give each write attempt a host/session identifier;
- claim only the records being edited;
- serialize catalog/index updates with a bounded lock;
- refuse a closeout that would include another active session's changes;
- release stale claims only after proving the original session is inactive;
- keep an audit trail of record IDs and content hashes, not copied private text.

A process exit, chat summary, or elapsed time does not prove a session is finished. Prefer an explicit closeout marker or an authoritative host status.

## Migration

Use a staging directory and synthetic examples first.

1. Freeze the source inventory and hash the files in scope.
2. Map old fields and statuses to the destination contract.
3. Convert a representative sample, including conflicts and attachments.
4. Compare counts, IDs, links, dates, and rendered Markdown.
5. Run retrieval tests against both systems.
6. Migrate the full approved set without deleting the source.
7. Switch adapters only after the destination passes verification.

Deleting or archiving the old vault is a separate, destructive decision. Ask for explicit authorization and prefer a recoverable move.

## Derived-state repair

When search or indexing is wrong, diagnose the boundary first:

| Observation | Likely boundary | Safe first action |
|---|---|---|
| Record exists but exact search misses | catalog/FTS | rebuild a disposable index and compare |
| Metadata is stale | parser/catalog | inspect one affected record and parser output |
| Semantic result points to old text | embeddings/cache | invalidate by content hash and rebuild affected items |
| One host sees different records | adapter/config | compare resolved roots and read-only status |
| Writes disappear or combine | locking/ownership | stop writers and inspect claims before repair |

Repair derived state in a copy when feasible. Count parity alone is insufficient: sample IDs, content hashes, statuses, and expected queries.

## Automation rules

Only install hooks, background jobs, or scheduled audits when the user asks for automation.

- Keep hooks fast and silent when there is no relevant work.
- Use one scheduler for one vault; duplicate timers create races and duplicate reports.
- Bound locks and retries, and leave a readable failure record.
- Merge with existing host configuration instead of overwriting unrelated hooks.
- Do not give background processes access to broader credentials than the memory task requires.
- Recheck the installed configuration and run one synthetic end-to-end event.

## Publication and privacy gates

Never publish a real memory vault by default. Before any authorized remote push, inspect the exact staged diff for:

- credentials, cookies, tokens, account IDs, customer or health data;
- private conversations, personal paths, database files, indexes, logs, caches, and model data;
- attachments whose redistribution rights are unknown;
- records that reveal confidential projects or relationships.

Use a private remote only after the user confirms the target and audience. A sanitized template should contain fake records and no derived database.

## Completion evidence

Report the operation, paths touched, records affected, and tests performed. A memory task is complete only when the requested observable behavior is demonstrated—for example, both named hosts retrieve the same saved record from the same canonical source—and remaining privacy or synchronization risks are stated.

Do not say the system is healthy merely because a command exited successfully.
