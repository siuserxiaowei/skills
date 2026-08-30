---
name: agent-memory
description: Install, upgrade, inspect, and maintain the public Agent Memory Vault system, with a shared Claude Code and Codex setup. Use when the user wants to install a Markdown/Obsidian-first memory vault, connect Claude Code and Codex to one fact source, configure SQLite/FTS or optional Zvec semantic retrieval, run search / closeout / audit flows, or troubleshoot memory scripts and hooks.
---

# Agent Memory Vault

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

## What This Skill Is For

This skill is the Agent-side runbook for setting up and running the public Agent Memory Vault system. Claude Code and Codex can both share a single vault: Markdown stays the one authoritative fact source, while each host attaches through a thin rule-and-hook adapter. The GitHub repository is the product itself; treat this document purely as the operational guide an Agent follows for setup, upkeep, and problem solving.

Repository: work against the public `agent-memory-vault` GitHub repository. If the clone URL is not known yet, ask the user for it.

## Safety Requirements

- A user's real memory vault must never end up in a public repository.
- Do not commit `.env`, SQLite databases, Zvec/vector stores, model caches, logs, API keys, cookies, tokens, passwords, private chat logs, customer data, or personal absolute paths.
- When migrating an older memory system, bring across only its structure, scripts, and sanitized patterns.
- Run the leak checks and review the diff before anything gets published or pushed.
- Any task that deletes files requires explicit user approval first; send files to Trash rather than erasing them outright.
- Claude Code auto-memory must never target the formal vault — disable it, or treat it strictly as scratch memory with no authority.
- Keep shared cookies and tokens in an owner-only private config stored outside the vault and outside Git; Agents should inject selected values into commands rather than dumping the entire file contents.

## Installing the Vault

1. Get a local copy of the repository (or update an existing clone):

```bash
git clone <agent-memory-vault-repository-url>.git
cd agent-memory-vault
```

2. Bootstrap a private local vault from the bundled template:

```bash
python3 scripts/bootstrap.py --memory-root "$HOME/agent-memory-vault" --write-env
source .env
```

3. Install the repository's canonical scripts so both hosts share a stable runtime, and create the private TOML config:

```bash
python3 scripts/install_runtime.py --config-root "$HOME/.config/agent-memory"
cp config/agent-memory.example.toml "$HOME/.config/agent-memory/config/agent-memory.toml"
# Edit memory_root, git_root, and state_db. Never commit this private file.
"$HOME/.config/agent-memory/scripts/install_runtime.py" \
  --config-root "$HOME/.config/agent-memory" --verify --json
```

The public repository is the sole source of core scripts. The installer leaves unknown local adapters and the private config alone, and records file hashes in `runtime-manifest.json`.

4. If desired, initialize Git inside the private vault:

```bash
git -C "$AGENT_MEMORY_GIT_ROOT" init
```

5. Build the indexes and validate everything:

```bash
python3 scripts/agent_memory_evolution.py --init --scan --report
python3 scripts/agent_memory_index.py --init --scan --report
python3 scripts/agent_memory_check.py
python3 scripts/agent_memory_doctor.py
```

6. Finally, tell the user where the vault lives, where the state database sits, and the claim/closeout commands they will need for future important tasks:

```bash
memoryctl --actor codex claim --file "/absolute/path/to/changed-memory.md"
memoryctl --actor codex closeout --dry-run
memoryctl --actor codex closeout
```

## Everyday Operations

If the neutral wrapper is installed, call it from either host in preference to anything else:

```bash
memoryctl --actor codex search "query" --limit 5
memoryctl --actor claude prewrite "summary of the memory to write"
memoryctl --actor claude claim --file "/absolute/path/to/changed-memory.md"
memoryctl --actor claude closeout
```

Restrict yourself to `memoryctl` plus the `agent_memory_*` entrypoints. Compatibility wrappers are deliberately not installed, so update every Hook, scheduler, shell alias, and custom script before an older installation is removed.

Default to the unified search entrypoint:

```bash
python3 scripts/agent_memory_search.py "query" --limit 5
python3 scripts/agent_memory_search.py "query" --track project
python3 scripts/agent_memory_search.py "query" --memory-type workflow
```

Run prewrite reconcile before a new formal memory gets written:

```bash
python3 scripts/agent_memory_closeout.py --prewrite "summary of the memory to write"
```

The reconcile step can return these actions:

- `ADD` — write a brand-new memory.
- `UPDATE` — modify an existing memory.
- `NOOP` — write nothing.
- `MARK_OUTDATED` — flag stale information as outdated while keeping it in place.
- `MERGE_REQUIRED` — stop and let the user merge or pick a version.
- `ASK_USER` — confirm first for sensitive, destructive, account, credential, cost, or otherwise uncertain actions.

Right after a formal memory is created or modified, claim it for the current host session:

```bash
memoryctl --actor codex claim --file "/absolute/path/to/changed-memory.md"
memoryctl --actor claude claim --file "/absolute/path/to/changed-memory.md"
```

A Codex session normally provides `CODEX_THREAD_ID` on its own. Claude needs the bridge instead: register `agent_memory_session_hook.py --actor claude` under `SessionStart`. Through Claude Code's official `CLAUDE_ENV_FILE` mechanism, the hook exports the real `session_id` from its payload to later Bash commands and clears any inherited Codex thread ID. In SQLite, a claim is tied to the session only via a one-way hash. When an important task wraps up, run closeout:

```bash
python3 scripts/agent_memory_closeout.py --dry-run
python3 scripts/agent_memory_closeout.py --commit
```

Closeout is scoped: it processes only the files that actor/session claimed, and it still recovers their changes when an external backup tool committed first; files belonging to other sessions stay excluded. A successful closeout writes the processed content hash into `memory_file_observations`, and only a matching observation proves a piece of historical content is complete — that is what lets the shared Git baseline advance. Dirty memory nobody claimed must be resolved explicitly rather than silently swept into a commit. Deliberate human maintenance goes through `memoryctl --actor human closeout --global`.

Two mechanisms protect closeout: a process lock that serializes SQLite, Zvec, and Git work, and a session ownership ledger whose claims stop cross-session commits. Compaction messages are advisory only and never block; failed checks or unresolved semantic duplicates still halt the normal commit path.

To run an audit by hand:

```bash
python3 scripts/agent_memory_audit.py
python3 scripts/agent_memory_audit.py --ignore FINDING_ID --note "reason"
python3 scripts/agent_memory_audit_autorun.py --reason manual --json
python3 scripts/agent_memory_doctor.py
```

Treat audit findings as review prompts, not automatic edits: audit must not rewrite Markdown facts directly unless the user asks for that update. The current-fact invariants catch retired paths or scripts, incorrect `agent_scope` values, and stale fixed metrics sitting in active summaries.

By default `doctor` is read-only. Among other things it looks for stale session claims, memory history aging without a push, and a semantic virtual environment whose base Python has disappeared. Pass `--repair-derived` only when the user actually wants SQLite/FTS and Zvec rebuilt — it must never rewrite Markdown facts.

## Optional: Semantic Retrieval via Zvec

Start from the tested `requirements-vector.lock`, then build the Zvec index and validate it:

```bash
python3 scripts/agent_memory_zvec_index.py --scan --prune
python3 scripts/agent_memory_zvec_index.py --report
```

If the semantic layer must keep working offline long-term, copy or APFS-clone a pinned model snapshot into the private runtime, set `require_local_model = true`, and keep a private model manifest recording revision, sizes, and hashes. Only call the semantic layer hardened once `doctor` passes the local-model, manifest-integrity, dependency-lock, and real offline-query checks.

Unified search queries SQLite and Zvec side by side, applies all filters after merging, and drops semantic neighbors beyond the configured distance threshold. Every hit is a candidate — read the underlying Markdown before accepting a claim as true.

## Optional: Hooks and Scheduled Automation

Install global Codex hooks or a macOS LaunchAgent only once the user has explicitly asked for automation.

- Stop fires per turn in both hosts, so the memory hook must be gated and stay quiet when the current session holds no claims and every pending file belongs to other sessions.
- Claude's SessionStart bridge has to exist in the live settings and in any settings manager's persistent configuration; re-verify it together with Stop and SessionEnd after provider switches.
- In a shared setup, Stop runs a full closeout only when the Agent has written and claimed formal memory. Dirty memory without a claim should block silent completion and surface a concrete claim instruction.
- When closeout fails, each host should halt normal completion through its native protocol: Claude answers `decision: block`; Codex exits with code `2` and writes a continuation prompt to stderr. A non-blocking fallback via Claude SessionEnd is fine; Codex has no direct equivalent today.
- Keep the outer Stop hook timeout slightly higher than the closeout timeout — a 300-second closeout needs at least 320 seconds outside.
- Across both hosts keep exactly one of each: global closeout lock, Git baseline, session-claim table, audit scheduler, SQLite database, and Zvec index.
- Leave the due/not-due decision to `agent_memory_audit_autorun.py --min-interval-days 7`.
- Once the interval comes due, autorun runs the content audit first and the read-only Doctor second, persists the two reports separately as `latest-audit.json` and `latest-doctor.json`, and notifies when findings appear or infrastructure health drifts.
- Never give the weekly LaunchAgent `--force`, or closeout, the hook, and launchd may fire duplicate audits inside the same seven-day window.
- Merge the memory command into the existing `~/.codex/hooks.json`; unrelated hooks must not be overwritten.
- Whenever a hook command changes, warn the user that Codex may prompt them to review and trust the new hook hash.

## Upgrading or Publishing the Template Repository

When the public template repository needs an update:

1. Do all work inside the `agent-memory-vault` repository.
2. Only public-safe scripts, templates, docs, and fake examples may be added or updated.
3. Real user memory stays in the private vault.
4. Run the validation suite:

```bash
python3 -m compileall scripts
python3 scripts/agent_memory_index.py --init --scan --report
python3 scripts/agent_memory_check.py --skip-state-db
python3 scripts/agent_memory_doctor.py
rg -n "/Users/|sk-[A-Za-z0-9]|token|secret|cookie|password|\\.sqlite|\\.db|zvec" .
```

5. Review `git diff` prior to committing.
6. Commit and push only once the leak check comes back clean, or once every match is confirmed as a harmless example or warning.

## When Something Goes Wrong

- Search reports a missing SQLite index: rebuild it with `agent_memory_index.py --init --scan --report`.
- Closeout finds no changes: verify `AGENT_MEMORY_ROOT` and `AGENT_MEMORY_GIT_ROOT`.
- Commit gets skipped: read the warnings — `MERGE_REQUIRED`, `ASK_USER`, deleted files, or failed checks all need user review.
- Zvec is slow or unavailable: fall back to `--no-zvec` for search/reconcile, or `--skip-zvec` for closeout.
- Zvec parity fails: run `agent_memory_zvec_index.py --scan --prune`, then `--report`.
- The same audit finding keeps coming back: record a decision with `--ack`, `--ignore`, `--resolve`, or `--snooze`; finding IDs must stay stable even as counts change.
- Claude debug shows zero matching hooks after installation: check whether a provider switcher rewrote `~/.claude/settings.json`. Persist the hooks in that manager's common configuration and any live rollback copy, restart it, then verify the loaded matchers again.
- Doctor reports `needs_review` or `mtime_fallback`: never invent a verification date. Classify structural/snapshot documents explicitly, treat document dates as provenance only, and add `verified_at` solely after real evidence has been checked.
- Doctor reports a Zvec hash mismatch: run closeout for the claimed changed files, or run `agent_memory_zvec_index.py --scan --prune`; equal document counts alone do not prove vectors are fresh.
- Doctor reports `session_claim_hygiene`: preview first with `memoryctl --actor human claims-expire --older-than-hours 24 --json`; add `--apply` only after those sessions are confirmed inactive. This updates the SQLite ownership ledger, not Markdown.
- Doctor reports `memory_remote_backup`: inspect the private-vault diff and the leak scan before pushing — a clean local Git baseline is not a remote backup.
- Doctor reports `semantic_python_runtime`: rebuild the private venv from the exact dependency lock with an available Python of the same supported minor version, then rerun the offline semantic probe.
