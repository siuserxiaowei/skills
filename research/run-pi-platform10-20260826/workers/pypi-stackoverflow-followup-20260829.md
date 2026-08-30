# PyPI / Stack Overflow follow-up (2026-08-29)

This is a follow-up evidence artifact only. It does not modify `candidates.json`,
`review_queue.json`, or any shared ledger. Candidate IDs and canonical URLs are
the existing queue objects; no new duplicate objects were created.

## PyPI

Using the connected ordinary public browser, I independently read five existing
worker-checked PyPI project pages that had previously been metadata-only:

| candidate ID | canonical page | visible result |
|---|---|---|
| `api-packages-pypi-pi-ai-client` | https://pypi.org/project/pi-ai-client/ | 0.1.0; sug_doctor; released 2026-08-19; Chinese body describes a Python port of `@earendil-works/pi-ai`, 35 providers, five protocols, Model/Context/Models/event-stream, tools, errors and cost accounting; upstream `Kisjjw/pi-ai-py`. |
| `api-packages-pypi-pi-py-agent-core` | https://pypi.org/project/pi-py-agent-core/ | 0.84.1; Justin Gao; released 2026-08-18; body names the official agent-core port and documents the stateful Agent, double loop, steering/follow-up/abort, skills, session persistence and compaction; upstream `encyc/pi-py`. |
| `api-packages-pypi-pi-py-ai` | https://pypi.org/project/pi-py-ai/ | 0.84.1; Justin Gao; released 2026-08-18; body names the official pi-ai port and shows Model/Context/stream plus OpenAI, Anthropic and Faux providers; upstream `encyc/pi-py`. |
| `api-packages-pypi-pi-py-coding-agent` | https://pypi.org/project/pi-py-coding-agent/ | 0.84.1; Justin Gao; released 2026-08-18; body names the official coding-agent port, says core-only/no TUI, and lists bash/read/edit/write/grep/find/ls; upstream `encyc/pi-py`. |
| `api-packages-pypi-pi-py-server` | https://pypi.org/project/pi-py-server/ | 0.84.1; Justin Gao; released 2026-08-18; body names the official server port, labels it experimental Unix-socket + JSONL, and lists spawn/list/status/stop/rpc/rpc_stream; upstream `encyc/pi-py`. |

The JSONL companion records the 17 acceptance fields plus a rendered-DOM body
SHA-256 and concrete observation for each page. `pi-py-storage-sqlite` is
intentionally absent because its canonical readback already exists in the
repository's `pypi-canonical-curator-readbacks.jsonl`; it was not duplicated.
These five rows remain **curator-review-ready evidence**, not accepted rows,
until the primary curator explicitly promotes them and performs the global
content-cluster / publisher-provenance check. They are separate components in
the same `encyc/pi-py` family (except `pi-ai-client`), not five independent
implementations or performance replications.

The page route succeeded anonymously after the normal client-challenge wait;
no login, interaction, download, install, or execution occurred. PyPI metadata
and README text remain upload-supplied and are not a security endorsement.

## Stack Overflow

Six additional bounded official Stack Exchange API intents were run at a low
rate on 2026-08-29. All six strict aliases returned HTTP 200 with
`items: []`; exact request URLs, quotas, response sizes, body bytes, and
SHA-256 values are in `stackoverflow-followup-probes-20260829.jsonl`.

The strict probes covered quoted `pi-coding-agent`, `pi-agent-core`,
`earendil-works/pi`, `badlogic/pi-mono`, plus title-only `pi-coding-agent` and
body-only `earendil-works`. Broader unquoted probes did return generic
Raspberry Pi / Mono / Bluetooth / multi-agent questions, but none named the
specified Pi runtime aliases and they were rejected as false positives rather
than padded into the platform quota. No Stack Overflow candidate ID or URL was
created. The platform should remain `partial` with a reproducible zero-result
record; retry only when new indexed exact-alias content appears.

All requests stayed well below the documented 30 requests/second threshold and
the remaining anonymous API quota was recorded. No HTML scraping, votes,
comments, edits, answers, login, or account action was performed.
