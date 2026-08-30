# OSChina shortage follow-up — 2026-08-30

## Scope and safe boundary

This append-only shard records three newly read OSChina canonical pages for the
remaining OSChina quota gap. Before writing, the current `candidates.json`,
`review_queue.json`, and all `workers/*-candidates*.jsonl` rows were checked by
candidate ID, normalized canonical URL, OSChina object ID, title/author/date,
and project-entry text. None of the three IDs or URLs below was present. The
root candidate file, queue, accepted ledger, source ledger, evidence ledger,
coverage file, and library were not edited by this shard. All rows remain
`curator_review_ready`; they are not accepted.

## Canonical readbacks

| object | canonical page | visible author/date | Pi identity and original body passage |
|---|---|---|---|
| 19695554 | https://my.oschina.net/u/1756807/blog/19695554 | 右耳朵猫AI / 2026-06-05 | The full article's `#14 can1357/oh-my-pi` entry says “A set of ready to use Agent Skills for research, science, engineering, analysis, finance and writing.” |
| 19719684 | https://my.oschina.net/u/1756807/blog/19719684 | 右耳朵猫AI / 2026-07-10 | The full article's `#19 craft-ai-agents/craft-agents-oss` entry says Craft Agents is a document-centric non-CLI GUI combining Claude Agent SDK and Pi SDK, with natural-language connections to APIs, MCP servers and custom services. |
| 19749892 | https://my.oschina.net/HelloGitHub/blog/19749892 | 削微寒 / 2026-08-28 | The full HelloGitHub AI section's item 33 says oh-my-pi is a TypeScript/Rust terminal coding agent evolved from Pi, integrating LSP and lldb/dlv/debugpy on macOS/Linux/Windows. |

The first and third pages both describe `can1357/oh-my-pi`, but they are not a
single cross-post: they have different canonical URLs, authors, dates, page
series, section numbering, and wording. The first is a GitHub trend entry and
the third is a HelloGitHub project recommendation. This is recorded as
`independent_oschina_roundup_object_same_upstream_project_not_same_article`
and is intentionally left for the primary curator's strict quota decision.
The Craft Agents page is a distinct project and article; its Pi identity is the
explicit `Pi SDK` ecosystem anchor, not a generic “pi” token.

## Evidence and limitations

- All three pages returned HTTP 200 and visibly rendered title, original badge,
  author, date, and the complete author body in ordinary Chrome. Search results
  were used only for discovery; no SERP snippet is used as final evidence.
- The 19719684 body-text fingerprint is 8,262 Unicode characters,
  SHA-256 `91ad527b1f8c04fe7c6963f46982cfcf83afa7fab87dda06ecd24e48e42909a4`.
- These are roundup/project-list entries, not Pi-primary source audits or
  controlled benchmarks. Project statistics, platform support and feature
  claims remain historical publisher descriptions and were not installed or
  reproduced.
- No login, posting, liking, following, commenting, downloading, CAPTCHA
  solving, robots/paywall bypass, or account mutation occurred.

## Files

- `oschina-shortage-followup-20260830-candidates.jsonl`
- `oschina-shortage-followup-20260830-readbacks.jsonl`
- `oschina-shortage-followup-20260830-audit.md`
