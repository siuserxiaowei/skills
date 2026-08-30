# Hugging Face accepted-set overlap audit

Audit date: 2026-08-26 (Asia/Shanghai)

Scope: `code-hosts-hf-001` through `code-hosts-hf-010` as present in the accepted `candidates.json` snapshot. This audit applies the project rule that a mirror, repost, summary, aggregate, or transformed view of the same underlying content does not become another unique quota item. A separately trained model is treated as a distinct artifact, but its source sessions are not described as a new raw corpus.

## Decision

Keep as distinct/canonical content objects:

- `code-hosts-hf-001`: canonical first-party `badlogicgames/pi-mono` session corpus.
- `code-hosts-hf-002`: canonical first-party sessions for the separate `pi-diff-review` project.
- `code-hosts-hf-004`: independently trained Needle tool-router model plus its own generated training bundle.
- `code-hosts-hf-007`: independent contributor session corpus; it has zero session UUID or content-hash overlap with `001`.
- `code-hosts-hf-008`, `009`, `010`: distinct trained model/adapter artifacts. Their cards disclose use of `001`; do not count their training rows as new raw sessions.

Exclude from the ten-unique-content quota:

- `code-hosts-hf-003`: byte-preserving compilation of upstream datasets, including every session from `001` and `002` and every session blob from `007`. It is valuable as a provenance catalog, but its own card says it adds no new raw data and applies no extra content cleaning.
- `code-hosts-hf-005`: filtered/line-ending-normalized subset of `001`; all 182 session UUIDs occur upstream. Its very short card does not include reproducible filtering code or a per-session manifest.
- `code-hosts-hf-006`: Talos conversion/scoring/error-masking of `001`. The converted representation and heuristics are useful, but all conversations come from the already accepted upstream corpus.

This leaves seven eligible unique objects, so Hugging Face should return to `partial (7/10)` until three unrelated, full-readback objects are found. Do not keep `003`, `005`, or `006` merely to preserve the platform quota.

## Reproducible evidence

The audit used read-only shallow Git metadata from each canonical Hugging Face repository. Git tree blob OIDs are content hashes; source manifests additionally expose SHA-256 per session. No model weights were downloaded or executed.

Pinned repository commits:

| ID | Hugging Face repository commit | Files | Session UUID files |
|---|---|---:|---:|
| `001` | `dac2a1d3ba12dda597b973a791a77618ccb5f413` | 629 | 626 |
| `002` | `034993bf7d9a19cc6320705e2e3a6bae7068a21a` | 9 | 6 |
| `003` | `8c593252ddad7dca08a0afc07896195fa73f2d6e` | 1,294 | 1,291 |
| `004` | `54c5de0a97dbf150d64d4d188b2f60e032d8c050` | 14 | 0 |
| `005` | `32e67a8d04febcb38a2d28798a6d80fb41481a38` | 184 | 182 |
| `006` | `e63223b09fbde86750b22e9f3825b1559ddbe7e6` | 7 | 0 (converted rows) |
| `007` | `d0895347aaac586876f53bd5d71b2209ab275dca` | 107 | 104 |
| `008` | `93aa816fc0bf280b7b00773529a700d32bea399f` | 9 | 0 |
| `009` | `382f8e8b919676864df4520eb8377ff0606d56a4` | 12 | 0 |
| `010` | `30047ef82e787a1533ec7bafa7332f4923ece3d3` | 3 | 0 |

Exact relationships:

1. `001 → 003`: `003/manifest.jsonl` attributes 626 sessions to `badlogicgames/pi-mono`. All 626 manifest SHA-256 values and all 626 Git blob OIDs exactly equal `001`; this is 100% of the upstream sessions.
2. `002 → 003`: the same check finds all 6 `pi-diff-review` session blobs unchanged in `003`.
3. `007 → 003`: all 104 current `007` session blobs occur unchanged in `003`. The aggregate attributes 103 to `thomasmustier/pi-mono-sessions`; the remaining identical session (`b562f345-3f12-405b-8e9e-d0236d5ecca2`) is attributed to `thomasmustier/pi-extensions-sessions`. This explains the card's `103` count without making the content independent.
4. `001 → 005`: all 182 `005` session UUIDs are members of the 626-session `001` set. The paths are unchanged. Sampled matched files have identical logical JSONL lines and differ only because `005` uses CRLF while `001` uses LF, explaining why raw Git OIDs differ.
5. `001 → 006`: the card explicitly says it downloaded `badlogicgames/pi-mono`, converted the traces, scored them, and produced a 149-row error-masked subset. The pinned `data.jsonl` resolves to 610 parseable rows (`trace_0` through `trace_610`, with `trace_426` absent), although the card says 611; `data_clean.jsonl` contains 149 rows. Of its original UUID labels, 148 exist in the current `001` manifest and one (`4f663c71-73b3-4714-8525-92b6d2b91816`) does not. These inconsistencies strengthen the case for treating `006` as derivative research metadata rather than an independent accepted corpus.
6. `001 ↔ 007`: zero shared session UUIDs and zero shared session-content hashes. They are separate raw corpora even though both concern development of Pi.

Compact reproduction pattern:

```bash
git clone --filter=blob:none --no-checkout --depth=1 \
  https://huggingface.co/datasets/badlogicgames/pi-mono.git hf-001
git clone --filter=blob:none --no-checkout --depth=1 \
  https://huggingface.co/datasets/MaxDevv/real-pi-coding-agent-traces-sessions.git hf-003
git -C hf-001 ls-tree -r HEAD
git -C hf-003 ls-tree -r HEAD
git -C hf-003 show HEAD:manifest.jsonl
```

Compare UUID suffixes in `*.jsonl`, Git blob OIDs from `ls-tree`, and the manifest SHA-256 fields. The machine-readable decisions and exact counts are in `huggingface-overlap-audit.tsv`.

## Limitations

- This is an identity/provenance audit, not a quality, privacy, license, or model-performance audit.
- `006` has internally inconsistent current card/file counts. The conclusion relies primarily on its explicit upstream declaration and transformation description, not an unsupported one-to-one mapping claim.
- Hugging Face repositories can change. Re-run against the pinned commits above or record new commits before accepting replacements.
