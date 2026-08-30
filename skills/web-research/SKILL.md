---
name: web-research
description: Plan and route an internet-research request that spans discovery, source verification, authorized collection, archiving, and optional transcription. Use when the request crosses stages or platforms and the correct research capability is not yet clear. Route a single known action directly to its specialist Skill instead of invoking this coordinator.
---

# Web Research Router

Turn an open-ended research request into a bounded sequence of evidence-producing stages. This Skill coordinates; it does not grant extra access to platforms, accounts, or private collections.

Read [references/examples.md](references/examples.md) first.

## Decide whether routing is needed

Use this coordinator when the request contains more than one of these stages:

1. discover candidate sources;
2. verify identity, relevance, date, or authority;
3. select a bounded set;
4. capture known sources;
5. transcribe existing media;
6. synthesize the evidence for a decision.

Route directly when the request is already singular:

| Requested action | Specialist capability |
|---|---|
| Search by query or find candidates | `unified-search` |
| Preserve known URLs or selected candidates | `content-archive` |
| Export the user's private saved/bookmarked links | `bookmarks-export` |
| Transcribe media already supplied or authorized | `asr` |

Installed tools do not determine intent. A browser already being logged in is not authorization to read an account.

## Build the research contract

Before selecting routes, define:

- the question and decision to support;
- geography, language, date range, and freshness requirement;
- named platforms and acceptable alternatives;
- target candidate count and stopping rule;
- what counts as primary or authoritative evidence;
- whether private-account data, downloads, paid APIs, or transcription are requested;
- output format and destination.

If the user asks for “best”, “all”, “latest”, or a ranking, define the candidate universe and the comparison date. A few search results cannot prove a superlative.

## Inspect local routing readiness

Resolve this Skill's path from the active registry and run the bundled read-only doctor:

```bash
python3 <skill-directory>/scripts/doctor.py --format json
```

The doctor checks child Skill structure and local executable availability. It does not access cookies, browser state, private collections, credentials, or the network. Missing optional tools should narrow the route, not trigger an installation without user approval.

After choosing a specialist, read its current `SKILL.md` in full. Its authorization and execution rules supersede this high-level route for that stage.

## Plan stages with explicit handoffs

Represent the plan as records rather than prose-only intent:

```json
{
  "question": "decision-oriented question",
  "as_of": "YYYY-MM-DD",
  "stages": [
    {"id": "discover", "capability": "unified-search", "input": {}, "output": "candidates.json"},
    {"id": "verify", "capability": "unified-search", "input": "candidates.json", "output": "verified.json"},
    {"id": "archive", "capability": "content-archive", "input": "approved subset", "output": "sources/"}
  ],
  "authorization": [],
  "stop": "coverage and evidence condition"
}
```

Each handoff should preserve stable source identifiers, URL, platform, query, retrieval time, publication time when known, selection status, and error. Never transform failed or unverified candidates into confirmed sources.

## Default research sequence

1. **Discover** — query more than one relevant route when breadth matters.
2. **Normalize** — deduplicate canonical URLs and entity identities without discarding provenance.
3. **Verify** — open the strongest candidates and check author, date, claims, and source type.
4. **Select** — apply the stated inclusion/exclusion rules; ask for confirmation when collection changes scope or accesses private data.
5. **Capture** — archive only known or approved sources through the archival specialist.
6. **Transform** — transcribe or extract only media already in scope.
7. **Synthesize** — cite the preserved evidence, describe gaps, and avoid unsupported completeness claims.

Discovery never implies permission to download. Bookmark export never implies permission to open every link. A stage may stop with a candidate list when the next stage needs new authority.

## Platform and account boundaries

- Prefer public, anonymous, documented access when it satisfies the task.
- Private bookmarks, feeds, dashboards, histories, and account-only search require explicit platform and scope authorization for this run.
- Do not publish, react, follow, comment, message, subscribe, or alter account state during research.
- Do not bypass login walls, CAPTCHA, paywalls, rate limits, geographic controls, or robots/access restrictions.
- Never print or persist cookies, tokens, API keys, signed URLs, or password data.
- Keep paid or quota-consuming work bounded and disclose the expected units before submission.
- Do not send the same paid transcription job to a second provider merely because the first is slow; confirm terminal state first.

## Evidence quality

For every important conclusion, track:

- source title and direct URL;
- publisher/author and source type;
- publication date versus retrieval date;
- the exact claim supported;
- confidence and any conflicting source;
- whether evidence is current for the requested date.

Search snippets are discovery evidence, not final factual support. Prefer primary documents for product behavior, technical details, policies, prices, schedules, and current versions.

## Failure handling

If one platform fails, preserve its query and error, then use an authorized alternative source where possible. Reduce the strength of conclusions when coverage falls below the contract.

Do not silently change the question, date window, private/public boundary, or candidate universe to make the run look complete.

## Delivery

Return the decision-relevant synthesis first. Then include coverage, excluded sources, failed routes, retrieval dates, saved artifacts, and unresolved uncertainty. Completion requires the evidence set—not merely the search command—to satisfy the research contract.
