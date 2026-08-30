# Pi domain-benchmark arXiv follow-up (2026-08-29)

This append-only pass looked for globally novel arXiv papers whose full body
uses the specified Pi runtime as an evaluated agent harness. It does not modify
`candidates.json`, `review_queue.json`, or any shared ledger.

## Preflight de-duplication

Before each readback, the current queue, accepted ledger, and every
`*-candidates*.jsonl` shard were checked for the candidate ID, canonical URL,
arXiv object ID, and exact title. None of the following three objects appeared:

- `arXiv:2605.28065v1`
- `arXiv:2606.13602v1`
- `arXiv:2607.19262v1`

The three papers are separate benchmarks with distinct titles, dates, task
sets and domains. They share some authors and a benchmark methodology, but not
the same experiments, text object, URL or result set; they are not mirrors or
versions of one paper.

## Official discovery/readback evidence

All discovery confirmations used the official arXiv Atom API with a bounded
exact-ID lookup (`search_query=id:<id>`, one result). Canonical v1 HTML was then
read anonymously in full.

| arXiv ID | Atom bytes / SHA-256 | HTML bytes / SHA-256 | Pi anchor |
|---|---|---|---|
| `2605.28065v1` | 3,023 / `993672cadc793ec40f6c477ee8b27fd803ee6d8254a46619906074e1c81dd64a` | 167,343 / `1243a0785ce9e0114163d0bbccdaaac043dfaf9b1e229cd5c20da2e424b71faf` | Defines Pi as the Pi terminal coding harness; 15 model-harness pairs and 1,080 trajectories across Pi, Codex and Claude Code. |
| `2606.13602v1` | 2,602 / `79eee0fccf43c5c1d10d859a346e2d2a76b930ac99a2a8e358c52105fb154141` | 103,748 / `0847eb28a74421f4269c3c28335679e86d414cf93a1f113cf011ec189ecca5a8` | Defines Pi as the Pi terminal coding harness; 106 evaluations, 16 pairs and 5,088 trajectories. |
| `2607.19262v1` | 3,498 / `c437cefd92d71213ee2b522b0f1e2ab85a6836b8760d90f9548b3a3e6a483b6b` | 84,329 / `92085ea3215bc7f3ed49c5ed1a0d560fe028512ba9cf2387e7296f38503b5427` | Methods defines PI, Claude Code and Codex as separate harness scaffolds; 100 evaluations and 3,962 gradable attempts. |

The full bodies were read through the benchmark/task design, model-harness
results, grading, execution method, discussion and limitations. No snippet or
abstract alone is being used as final evidence.

## Curatorial boundary

These are Pi-primary *harness evaluation* objects under the run's ecosystem
and critical-evidence acceptance rule: Pi is a named, repeatedly measured
harness axis, not a coincidental token. The papers' scientific domains remain
their main application topic, so summaries do not pretend Pi is the sole
subject. Results are author-reported and were not reproduced. Each row retains
the paper-specific limits: small or unbalanced task inventories, constrained
deterministic answer surfaces, partial comparability of cost/turn metadata, or
refusal-induced denominator bias.

No login, interaction, PDF download, code execution, proxy, CAPTCHA, rate-limit
or access-control bypass was used. The new rows remain
`curator_review_ready`; only the primary curator may promote them after a final
content-cluster decision.

## Artifacts

- `arxiv-domain-benchmarks-candidates-20260829.jsonl`
- `arxiv-domain-benchmarks-curator-readbacks-20260829.jsonl`
- this audit file
