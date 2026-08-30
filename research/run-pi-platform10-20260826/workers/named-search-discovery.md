# Named search-engine Pi discovery/readback shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26` (Asia/Shanghai)

This shard covers only `bing_search` and `baidu_search`. Google Search was
intentionally left to the primary curator after they confirmed a working native
Google route. Rows remain `curator_review_ready`; they are not accepted here.

## Executed named-engine intents

Both engines were used directly in the in-app browser. No DDG, Exa, Jina,
Brave, cached snippet, or third-party SERP was substituted.

| Platform | Query ID | Native query | Outcome |
|---|---|---|---|
| Bing | `bing-native-exact-pi-coding-agent` | `"pi coding agent"` | native SERP rendered; target URLs decoded from Bing redirects |
| Bing | `bing-native-pi-coding-agent-extensions` | `"pi coding agent" extensions` | native SERP rendered; extension/package/source results inspected |
| Baidu | `baidu-native-exact-pi-coding-agent` | `"pi coding agent"` | native SERP rendered; each selected Baidu redirect was opened |
| Baidu | `baidu-native-pi-coding-agent-extensions` | `"pi coding agent" 扩展` | native SERP rendered; each selected redirect was opened |

No CAPTCHA, login requirement, or robot interstitial appeared during these four
queries. Cookie notices were not used as evidence. Search snippets were used
only for discovery; every candidate row has a separate canonical-page body or
native detail readback.

## Coverage

| Platform | Candidate rows | Distinct executed intents | Shortage to 10 |
|---|---:|---:|---:|
| Bing Search | 10 | 2 | 0 |
| Baidu Search | 10 | 2 | 0 |

One otherwise readable CSDN result was already globally occupied by another
candidate shard and was excluded. Baidu still reached ten only after a distinct
canonical article on the Extension evidence ladder was fully read back; no
mirror or repost was used to pad the quota.

## Readback and exclusion rules

- All candidate URLs were normalized and checked against the current
  `candidates.json`, `review_queue.json`, and every existing worker
  `*-candidates.jsonl` before this shard was written.
- Canonical-page bodies/details were read in the ordinary browser. No search
  snippet is a `readback_backend`.
- DeepWiki was inspected but excluded because it is a generated code wiki, not
  the repository's canonical source object.
- An `hochej.github.io/pi-mono` documentation result was excluded as a stale
  mirror.
- A `pi-doc.com` documentation result was excluded as a noncanonical mirror.
- A CSDN extension-architecture URL already present in another shard was
  excluded despite successful canonical readback.
- Claims about benchmarks, Stars, provider counts, performance and model prices
  remain explicitly attributed and were not treated as independent validation.

## Files

- `named-search-candidates.jsonl`: worker submission rows.
- `named-search-curator-readbacks.jsonl`: separate canonical readback overlay.
- `named-search-validator.py`: schema, intent, named-backend, URL uniqueness and
  global-collision checks.

Run validation from the repository root:

```bash
python3 research/run-pi-platform10-20260826/workers/named-search-validator.py
```
