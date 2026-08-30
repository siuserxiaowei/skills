# Public API / research supplemental audit

Access date: 2026-08-26. This is a worker evidence artifact, not an accepted
ledger. It does not promote candidates or claim that any platform meets its
ten-item quota.

## Curator-ready objects

The supplemental candidate shard contains two globally novel arXiv full-text
objects:

- `public-api-arxiv-harness-convergence` — arXiv `2608.23953v1`; canonical
  HTML 173,647 bytes; SHA-256
  `713465f5bbed0fea6280e83bc040e808dd801921fdec9088be1296c9453900cb`.
- `public-api-arxiv-polar-pi-rl` — arXiv `2605.24220v1`; canonical HTML
  207,208 bytes; SHA-256
  `bf16b5b5104e20fdd286c24601a6e95135b3a819554acbac2846c9b66f774a0a`.

Both canonical bodies were independently read. Benchmark, acceptance-rate,
GPU, and architectural claims remain paper-author claims unless a row says
otherwise. Neither URL nor exact normalized title collides with a different
accepted or queued object. The previously accepted arXiv object is SHarD,
`2607.25890v1`.

## PyPI existing-ID readbacks

Ten curator readbacks in
`public-api-research-supplemental-readbacks.jsonl` intentionally reuse existing
review-queue IDs. No duplicate candidate rows were created. The documented
PyPI project JSON detail route supplied the full project description, project
URLs, current version, release upload timestamps, file names, published file
hashes, and yanked flags. Each response has a frozen SHA-256 in the readback
artifact. No distribution was downloaded, installed, or executed.

Nine `pp-*` records are distinct component packages in one HSPK Python-port
family: agent core, AI, coding agent, evals, RPC client, protocol, server,
telemetry, and TUI. They are useful as component cards but do **not** constitute
nine independent reproductions. `pi-ai-client` is a separate repository-family
port. Publisher/author fields are upload-supplied metadata, not verified
identity or endorsement.

PyPI's canonical HTML remained behind a Client Challenge and was not bypassed.
Its current `robots.txt` disallows crawler access to `/pypi/*/json`, `/simple`,
and `/search`; this pass was a bounded, documented API-client detail read of
already-known exact project IDs, not generic crawling, search, or bulk
collection. The official terms' abuse, excessive-request, token-circumvention,
and spam-collection limits remain controlling.

## Honest shortages and exclusions

- Stack Overflow: official AUP, API terms, and throttle documentation were
  readable. Four quoted exact Stack Exchange API intents returned no strict Pi
  question. One unquoted `earendil-works` response was an old JSFiddle author
  name false positive and was rejected. Candidate count: zero.
- OpenReview: both official API generations and the terms route returned HTTP
  403 from this environment. No proxy, alternate identity, or bypass was used.
  The combined `arxiv_openreview` platform is therefore partial: arXiv worked;
  OpenReview remained blocked.
- Bluesky: official docs and terms were readable, but public AppView search
  returned regional HTTP 403. No proxy or bypass was used. Candidate count:
  zero.
- Docker Hub: four exact-name repositories remained descriptionless and had no
  independently located upstream provenance. They stay metadata-only. The one
  defensible object, `stck/pi`, is already accepted, so this shard adds zero.
- Gitee: `HappyVing/pi-web` overlaps the queued GitHub `worker-global-028`
  content cluster, and `Geek_Raingor/pi-web-switch` directs users to
  `github.com/Raingor/pi-web-switch`. Both were removed under the no-mirror /
  one-content-cluster rule. Other probes were a full upstream Pi mirror or a
  thin placeholder. This shard adds zero Gitee objects.
- HackerNoon: two strict public canonical stories already have independent
  user-visible browser readbacks in the sparse/social supplemental artifacts;
  this shard does not duplicate them.
- Hashnode: two exact-title false positives and two Pi-secondary articles stay
  excluded. There is no Pi-primary curator-ready object.

## Validation

The dedicated validator is offline and side-effect free:

```bash
python3 research/run-pi-platform10-20260826/workers/public-api-research-supplemental-validator.py
```

It freezes candidate/status/hash fields, requires a readback for every new
candidate, verifies the ten PyPI overlays against existing worker-checked queue
IDs, checks normalized URLs and exact titles globally, rejects the known Gitee
content clusters, and reports the zero/blocked outcomes above. It does not
compile, promote, rebuild, or modify shared ledgers.
