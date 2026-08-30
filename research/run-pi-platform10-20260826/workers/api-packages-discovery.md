# npm / PyPI / Docker Hub official-readback worker shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26`
Machine-readable shard: `api-packages-candidates.jsonl`

This is an isolated discovery and readback artifact. It is intentionally not a
direct compiler shard: the JSONL uses the local workflow states
`curator_review_ready`, `metadata_only`, and `not_ready`, whereas the shared
compiler only accepts `worker_checked`. None is curator accepted and none has
been added to `candidates.json`. The JSONL carries the frozen 17 acceptance
fields, plus `query_id` and `readback_evidence`.

## Method and policy

- npm: discovery used bounded official registry search and an exact official
  namespace/component list. Every selected package was read through its
  official registry package document, including current dist-tag/version,
  timestamp, author or maintainer, repository metadata, and README length.
  No package was installed or executed and npmjs.com pages were not crawled.
- PyPI: the public search and canonical project pages returned a Client
  Challenge both to curl and to a normal Chrome session. Package names were
  discovered through exact upstream references and their official project JSON
  metadata was probed, but the current platform rule forbids using bulk JSON
  paths as the routine readback route. The 15 rows are therefore
  `metadata_only`, not curator ready. No distribution was downloaded/executed.
- Docker Hub: bounded official repository search was followed by official
  repository-detail and tags API readback. Images were not pulled or run.
  Exact-name repositories without a description or upstream URL are retained
  only as provenance-blocked review leads.
- Raspberry Pi, Pi Network, mathematical pi, policy iteration, and unrelated
  same-name packages/images were excluded.

## Counts

| Platform | Rows | Curator-review ready | Metadata-only | Query intents | Target 15 | Assessment |
|---|---:|---:|---:|---:|---:|---|
| npm | 20 | 20 | 0 | 2 | met | Strong official and ecosystem package pool |
| PyPI | 15 | 0 | 15 | 2 | met for discovery only | Canonical readback blocked; not ready |
| Docker Hub | 5 | 1 | 4 | 2 | short by 10 | Content-scarce; do not fill with aliases alone |

## Query intents

- `npm-official-runtime`: official `@earendil-works/*` runtime, UI, protocol,
  storage, server, and extension packages.
- `npm-ecosystem-adapters`: packages whose registry record explicitly embeds,
  adapts, or extends the Pi coding agent/runtime.
- `pypi-python-ports`: `pi-py-*` projects explicitly described as Python ports
  of official `@earendil-works/pi-*` packages.
- `pypi-runtime-components`: independent `pp-*` and `pi-ai-client` projects with
  explicit official-upstream links in PyPI metadata.
- `docker-exact-alias`: exact `pi-coding-agent` or `earendil-works/pi` image
  aliases found on Docker Hub and read through repository + tag detail.
- `docker-harness-alias`: exact `pi-harness` repository alias, retained only as
  a provenance-blocked lead when no overview/upstream link is published.

## Candidate inventory

### npm (20)

- Official runtime/components (13):
  `@earendil-works/pi-agent-core`, `@earendil-works/pi-ai`,
  `@earendil-works/pi-client`, `@earendil-works/pi-coding-agent`,
  `@earendil-works/pi-protocol`, `@earendil-works/pi-radius`,
  `@earendil-works/pi-radius-work`, `@earendil-works/pi-server`,
  `@earendil-works/pi-session-backend-sqlite-node`,
  `@earendil-works/pi-storage-sqlite-node`,
  `@earendil-works/pi-telemetry`, `@earendil-works/pi-tui`, and
  `@earendil-works/pi-web-ui`.
- Ecosystem/adapters (7): `@automatalabs/pi-acp`, `@ai-sdk/harness-pi`,
  `pi-acp`, `pi-background-tasks`, `pi-mcp-adapter`, `pi-subagents`, and
  `pi-web-ui`.

All 20 have official registry-object readback evidence. Main curator checks:
scope/version drift, package provenance, supply-chain risk, and whether sibling
components should remain independent learning objects rather than be treated as
near duplicates.

### PyPI (15)

- `pi-py-*` ports (5): `pi-py-agent-core`, `pi-py-ai`,
  `pi-py-coding-agent`, `pi-py-server`, `pi-py-storage-sqlite`.
- `pp-*`/other explicit ports (10): `pp-agent-core`, `pp-ai`,
  `pp-coding-agent`, `pp-evals`, `pp-rpc-client`, `pp-rpc-protocol`,
  `pp-rpc-server`, `pp-telemetry`, `pp-tui`, and `pi-ai-client`.

All 15 records explicitly name an official Pi component or link the official
upstream in PyPI metadata, but all remain `metadata_only`: canonical project
HTML could not be read past the Client Challenge, and the official JSON probe
is not an allowed replacement under the currently frozen PyPI rule. Required
resume step: use a rules-compliant package client or user-assisted project-page
readback, then review publisher identity, port completeness, and duplicates.

### Docker Hub (Top K = 5)

- `stck/pi`: strongest row; repository description explicitly states
  `earendil-works/pi image on top of bookworm` and a public latest digest was
  read.
- `stefan2904/pi-coding-agent` (`metadata_only`): exact name and 21 public tags were read, but the
  repository publishes no description, full overview, or upstream URL.
- `hoax859/pi-coding-agent` (`metadata_only`): exact name with `0.82.1` and latest tags, but no
  description or upstream URL.
- `jarvisquilter/pi-coding-agent` (`metadata_only`): exact name and a public latest manifest, but
  no description or upstream URL.
- `dbellkoff/pi-harness` (`metadata_only`): exact harness name and a public latest manifest, but
  no description or upstream URL.

Docker Hub searches for exact Pi aliases and runtime/component terms produced
mostly unrelated generic “agent”, Raspberry Pi, or mathematical/same-name
results. Only five survived the first relevance pass, and four of those still
need external repository/Dockerfile provenance before curator acceptance.
Accordingly Docker Hub is honestly short by ten at the discovery target and
short by at least nine strong-provenance objects; it must remain `partial` or
`rejected` rather than be padded to 15.

## Reproduction and local validation

```bash
python3 scripts/build_api_packages_discovery.py
python3 scripts/validate_api_packages_discovery.py
```

Expected validation summary:

```json
{
  "items": 40,
  "counts": {"docker_hub": 5, "npm": 20, "pypi": 15},
  "shortages_to_15": {"docker_hub": 10, "npm": 0, "pypi": 0}
}
```

The validator requires every row to include the 17 public-library fields plus
`query_id` and non-empty `readback_evidence`, use a public HTTPS canonical URL,
use one of the isolated-shard states, avoid duplicate IDs/URLs, and provide at
least two query intents per platform. It specifically rejects any description-
less Docker alias marked `curator_review_ready`.
