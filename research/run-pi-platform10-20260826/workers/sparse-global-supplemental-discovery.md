# Sparse global platforms supplemental shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26`
Data: `sparse-global-supplemental-candidates.jsonl`

This isolated supplement contains only Pi-primary objects whose canonical body,
repository README, official registry detail, or user-visible platform detail was
actually read. Every row remains `curator_review_ready`; none is `accepted`.

## Included

- note: nine public, free, Pi-primary articles (setup, architecture, extensions,
  provider integration, session/compaction, local/private deployment).
- HackerNoon: two canonical stories read in an ordinary user-visible browser
  session because generic crawler access is not the allowed route.
- Product Hunt: one canonical launch/product page; no vote, comment, follow, or
  other interaction occurred.
- Substack: one previously unshared full public practitioner review by Owain
  Lewis, independently re-read on the canonical page.
- Docker Hub: one official detail/tags API object whose description explicitly
  names `earendil-works/pi`; the image was not pulled or executed.
- Gitee: one non-mirror Pi-based product repository with its rendered README and
  visible Pi-runtime history read on the public root page.

## Honest zero-row outcomes

- Hashnode: both exact-title hits were false positives; the remaining canonical
  pages treated Pi as secondary, so no Pi-primary row qualifies.
- PyPI: project pages still showed `Client Challenge`; registry metadata rows
  are not promoted as canonical body readbacks.
- Stack Overflow: the four bounded exact API intents returned zero strict Pi
  questions; generic Agent content was not substituted.
- arXiv/OpenReview: the one strict Pi-specific SHarD paper is already accepted
  in the shared ledger, and no novel strict item was found.
- Gitee mirror `jianyuan/pi` was excluded because the parent request forbids
  mirrors.
- Existing accepted Substack George Racu and Scaile rows were excluded as
  duplicates; Andrew and Zazen worker rows were also excluded from this novel
  supplemental artifact.

## Validation

```bash
python3 research/run-pi-platform10-20260826/workers/sparse-global-supplemental-validator.py
python3 -m py_compile research/run-pi-platform10-20260826/workers/sparse-global-supplemental-validator.py
PYTHONPATH=scripts python3 - <<'PY'
from pathlib import Path
from curate_worker_candidates import load_readbacks
print(len(load_readbacks(Path(
    "research/run-pi-platform10-20260826/workers/sparse-global-curator-readbacks.jsonl"
))))
PY
```

The validator requires the frozen 17 fields plus `query_id` and
`readback_evidence`, public HTTPS URLs, unique IDs and normalized URLs, non-thin
evidence, and the sole worker state `curator_review_ready`.

The companion `sparse-global-curator-readbacks.jsonl` uses the exact override
allowlist accepted by `scripts/curate_worker_candidates.py`. It is keyed to the
13 new supplemental IDs plus the existing queue IDs
`api-packages-docker-stck-pi` and `code-hosts-gitee-002` so those two originals
can be promoted without introducing duplicate candidate rows.
