# Hugging Face / GitLab / Gitee official-readback worker shard

Run: `pi-platform10-20260826`
Checked: `2026-08-26`
Machine-readable shard: `code-hosts-candidates.jsonl`

This is an isolated discovery and original-page readback artifact. It does not
modify `candidates.json`, shared ledgers, compiler inputs, scripts, or tests.
Every JSONL row contains the frozen 17 acceptance fields plus `query_id` and
`readback_evidence`; every status is `curator_review_ready`, never `accepted`.
The shared compiler currently expects `worker_checked`, so this shard must stay
standalone until a curator explicitly reviews and transforms selected rows.

## Result

| Platform | Curator-review-ready rows | Distinct query intents | 10-object target | Assessment |
|---|---:|---:|---:|---|
| Hugging Face | 10 | 2 | met | Strong pool after derivative/card-quality deduplication |
| GitLab | 9 | 2 | short by 1 | Honest Top K; placeholder and mirror projects rejected |
| Gitee | 2 | 2 | short by 8 | Honest Top K; both public repository roots read in Chrome |

No quota was padded with individual Pi session JSONL files, near-identical
model runs, empty Trackio cards, generic “pi”, Raspberry Pi, Pi Network, or
unread search snippets.

## Method and query intents

### Hugging Face

Policy sources:

- <https://huggingface.co/docs/hub/en/api>
- <https://huggingface.co/docs/hub/main/rate-limits>
- <https://huggingface.co/terms-of-service>

Discovery used bounded public Hub API searches across models, datasets, and
Spaces for exact `pi-mono`, `pi-coding-agent`, and `pi-agent-core` aliases.
Every selected object was read twice: the official object API for identity,
author, dates, tags, and repository files, plus the object's
`resolve/main/README.md` card. No model/dataset artifact was downloaded or
executed.

The two recorded intent classes are:

- `hf-session-traces`: original or project-specific Pi session datasets.
- `hf-derived-training-evaluation`: aggregations, filtered/converted data, and
  models whose cards document a distinct Pi-derived training or evaluation
  operation.

The ten retained objects are seven datasets/derived datasets and three model
artifacts. The cards range from 324 bytes to 16 KB; the 324-byte Opus-filtered
row is retained with a strong limitation because it still documents a distinct
filter, while cardless or config-only objects are rejected.

### GitLab

Policy sources:

- <https://docs.gitlab.com/api/rest/>
- <https://docs.gitlab.com/api/rest/authentication/>
- <https://about.gitlab.com/terms/>

Discovery used public Projects API searches for exact Pi aliases. Each selected
project was read through `GET /api/v4/projects/{id}` and the official
Repository Files raw README endpoint on its declared default branch. No stars,
issues, merge requests, comments, forks, downloads, or other mutations were
performed.

The two recorded intent classes are:

- `gitlab-pi-extensions-runtime`: SDK, runtime, hook, audit, and extension
  repositories.
- `gitlab-pi-deployment-products`: sandbox, service, multi-agent, or vertical
  product repositories built around Pi.

Nine objects survive. Their raw README sizes range from 494 to 24,204 bytes and
all return HTTP 200. GitLab is therefore `partial`, Top K = 9; it is not padded
to ten with a placeholder repository or a near mirror.

### Gitee

Policy source: <https://gitee.com/robots.txt>

Gitee's robots policy publishes `Crawl-delay: 1` and disallows `/api/v*`, raw,
tree, commits, archives, and other repository routes. The two known public
repository roots were therefore read in a normal Chrome session, without using
those disallowed routes. No login, star, fork, issue, download, or repository
mutation occurred.

The two recorded intent classes are:

- `gitee-pi-mirror`: exact upstream mirror visibility.
- `gitee-pi-productization`: a distinct product built on the Pi runtime.

`jianyuan/pi` rendered the full Pi Agent Harness README and explicitly labelled
itself a synchronization of `earendil-works/pi`. `Yonja/feynman` rendered a
large README describing an open-source research agent, its multi-agent
workflows, science workbench, in-app Pi chat, and Pi package update behavior.
The direct `RELEASES.md` page displayed a security-verification challenge. No
CAPTCHA was solved; that detail page was not used as evidence. The repository
root alone contains enough visible Pi identity and product detail for the
candidate, with the blocked detail disclosed in `limitations`.

## Included inventory

### Hugging Face (10)

1. `badlogicgames/pi-mono` — foundational shared Pi session dataset.
2. `badlogicgames/pi-diff-review` — project-specific diff-review sessions.
3. `MaxDevv/real-pi-coding-agent-traces-sessions` — 21-source aggregation with
   provenance manifest and hash deduplication.
4. `theabbie/needle-pi-coding-agent` — small four-tool routing model.
5. `armand0e/badlogicgames-pi-mono-opus-filtered` — Opus-only filtered subset.
6. `DJLougen/Talos-pi-mono-badlogicgames` — scored, error-classified, converted
   and clean-subset Talos dataset.
7. `thomasmustier/pi-mono-sessions` — upstream-contribution session traces.
8. `burtenshaw/gemma-4-12b-sdpo-pi-mono-trace-feedback` — failure/user-feedback
   SDPO adapter experiment.
9. `Chengshuo0723/gemma-4-E2B-it-pi-mono-lora` — selected SFT LoRA with
   evaluation protocol notes.
10. `shasan35/gemma-4-2b-pi-mono-sft` — merged SFT model with explicit domain
    and context limitations.

### GitLab (Top K = 9)

1. `DraconDev/pi-goal-list-loop-audit` — durable goal loop and isolated audit.
2. `psyb0t/docker-pibox` — containerized shell/API/OpenAI/MCP/Telegram/cron.
3. `ai-agents-dev/pi-sdk-providers` — provider and SDK sandbox.
4. `r3b1s/rtk-pi` — RTK output-filtering extension.
5. `mikeysax/smithy-agent` — coordinated Pi team and decision ledger.
6. `jetjake/pi-extensions` — auto-push and Rust cargo-check hooks.
7. `tessellation-systems/zenith-sandbox` — Docker/Playwright/tmux sandbox.
8. `jonasreyes/pi-deeproot` — Spanish extension/MCP package collection.
9. `acyuta108/pi-extensions` — global Pi extension suite.

### Gitee (Top K = 2)

1. `jianyuan/pi` — non-authoritative upstream mirror.
2. `Yonja/feynman` — distinct Pi-based research-agent product repository.

## Rejections and blocked evidence

### Hugging Face

- `cfahlgren1/pi-mono-fresh`, `karkowww/pi-mono`, `invincible-jha/pi-mono`,
  and similar clones: pure or near mirrors of the foundational dataset; no
  distinct processing card strong enough to justify a new content object.
- `lhoestq/tmp-pi-mono-parquet*`, `JohnBeanerson/pi-mono-test`: temporary or
  test conversions; duplicate source content and insufficient independent
  value.
- `kryvokhyzha/pi-mono-sft` and `sergiopaniego/pi-mono-chat`: automatically
  generated schema-only cards; no narrative provenance or transformation
  method to support original-page summary.
- `Chengshuo0723/gemma-4-E2B-it-pi-mono-agent-eval`: the expected README path
  returned 404 during final readback, so it is not promoted on metadata alone.
- `burtenshaw/sdpo-pi-mono-trackio` and
  `burtenshaw/pi-mono-sft-trackio`: both have the same 112-byte config-only
  README hash and no substantive experiment narrative; rejected as thin and
  near-duplicate dashboards.
- `shasan35/gemma-4-2b-pi-mono-experiments`: 212-byte default Space card that
  points only to the generic configuration reference.
- Additional `burtenshaw/*` and livestream sweep variants: retained only when
  one representative final artifact had a materially distinct method/card;
  repeated smoke, version, and hyperparameter-run objects were deduplicated.

### GitLab

- `jetjake/pictl` (project 83348666): README points to the placeholder
  `https://github.com/you/pi-agent` and lacks a strict canonical Pi/package
  anchor; likely relevant intent is insufficient for the identity gate.
- `black-lotus-dev/pi` (project 84830444): explicitly a carry of
  `earendil-works/pi`; README is near-identical to upstream. The cancellable
  preflight patch would require a patch-specific readback before it could be a
  distinct object.
- `igor.../pi-monorepo` (project 77733923): direct fork of the old
  `badlogic/pi-mono`, with no independent artifact value.
- `PeKaStLa/base_server_setup-deletion_scheduled-*`: deletion-scheduled,
  low-evidence infrastructure repositories; not robust learning objects.

### Gitee

- No additional strict public object survived discovery. Generic “pi” results
  were excluded rather than treated as Pi Agent content.
- `Yonja/feynman/blob/main/RELEASES.md`: blocked by Gitee's security
  verification in Chrome. The challenge was not bypassed or solved and the
  previously recorded summary was not reused as current evidence.

## Curator handoff

- Review URL/content fingerprints against shared `candidates.json` before
  promotion, especially the Gitee mirror and overlapping Hugging Face sessions.
- Preserve all status values as non-accepted until that review is complete.
- For model cards, treat every reported score as an author-reported local result
  unless its exact dataset split, prompt, decoding, scorer, and runtime can be
  reproduced.
- Keep GitLab at 9 and Gitee at 2 if no new strict original object appears; a
  truthful Top K is required by `PLATFORM_ACCEPTANCE.md`.

## Shard-only validation

Run only the dedicated validator:

```bash
python3 research/run-pi-platform10-20260826/workers/code-hosts-validator.py
```

Expected high-level result:

```json
{"items": 21, "counts": {"gitee": 2, "gitlab": 9, "huggingface": 10}}
```
