# BUGFIRE｜补丁兽 · VibeLab submission pack

Track: `VibeVision`

## One-line product

BUGFIRE turns an original character brief into an auditable companion pack: AI proposes a structured direction, an operator rejects and replaces one choice, and the existing deterministic validator decides whether the result can build, preview, install, verify, and restore.

## Pain point

“让 AI 帮我设计一个角色” often collapses creative intent, rights claims, implementation fields, and approval into one unreviewed answer. A plausible-looking draft can be mistaken for an installable asset pack. BUGFIRE makes the boundaries visible and executable.

## Original mechanism claim

The submitted mechanism is the concrete workflow implemented here:

```text
original brief
  -> recorded or live AI structured draft
  -> explicit rejection + bounded replacement
  -> human-approved plan
  -> deterministic pack validator
  -> compiled local assets + offline preview
  -> optional live install / verify / restore
```

This is an original implementation and mechanism combination, not a claim to have invented AI art direction, desktop pets, human review, or CDP theming. See [`PROVENANCE.md`](../../PROVENANCE.md).

## Reproduce in one command

From the repository root:

```bash
./contest/bugfire/run-demo.sh
```

The offline run:

1. verifies the recorded AI fixture and SHA-256;
2. applies the scripted rejection of `alert-first-palette`;
3. proves the accent changed from `#ff7a1a` to `#35d9d1`;
4. materializes `bugfire-pack.json` only after the review gate;
5. runs the independent pack validator and builder;
6. creates an interactive six-state `preview.html`;
7. checks the renderer payload without changing Codex.

The fixture is real AI-authored output from the repository's Codex agent session, but the replay is not called a live API request. The review JSON is a scripted demo input, not proof of a named person's approval. During recording, the operator must type or explicitly confirm the rejection.

## Real live-AI path

```bash
export BUGFIRE_OPENAI_BASE_URL="https://your-compatible-endpoint.example/v1"
export BUGFIRE_OPENAI_MODEL="your-model-id"
export BUGFIRE_OPENAI_API_KEY="your-secret"

node macos/scripts/bugfire-director.mjs draft-live \
  contest/bugfire/demo/brief.json /tmp/bugfire-ai-draft.json \
  --model "$BUGFIRE_OPENAI_MODEL" \
  --base-url "$BUGFIRE_OPENAI_BASE_URL"

unset BUGFIRE_OPENAI_API_KEY
```

The automated test starts a real loopback HTTP server, observes the request, and proves the credential is not serialized. Remote endpoints require HTTPS. No test or fixture pretends that a live provider was called when it was not.

## Evidence matrix

| Claim | Evidence | Limit |
|---|---|---|
| AI director has a real network path | `bugfire-director.test.mjs` observes a loopback OpenAI-compatible HTTP request | Mock endpoint proves transport/contract, not model quality |
| Offline fixture came from an AI agent | fixture metadata + checksum + repository task provenance | Checksum proves integrity, not independent model attestation |
| An AI draft cannot build directly | `materializeReviewedPlan` rejects `ai-draft`; automated test covers it | A scripted review is not personal approval |
| Rejection changes the product | orange `#ff7a1a` becomes cyan `#35d9d1`; checked reviewed plan | Operator must confirm the choice before saying “人工否决” publicly |
| Builder is independently gated | original `bugfire-pack` schema/image/path/rights validator and tests | It validates declared local inputs, not artistic quality |
| Product is reversible | existing install / verify / restore scripts and older real Codex footage | Older V2 footage does not show the new director workflow |
| Demo assets are clear for public use | source SVGs, SHA-256 values, `ASSET_RIGHTS.csv` | Third-party user packs remain their owner's responsibility |

## Validation commands

```bash
cd macos
npm test
./scripts/build-release.sh
```

Windows pet/director parity is not claimed. The Windows subtree remains upstream theme tooling and is not exercised on this macOS submission machine.

## Submission assets

- [`boards/01-ai-draft.png`](boards/01-ai-draft.png): 1920×1080 AI draft/provenance board.
- [`boards/02-human-rejection.png`](boards/02-human-rejection.png): 1920×1080 before/after rejection board.
- [`boards/03-pack-preview.png`](boards/03-pack-preview.png): 1920×1080 real offline preview capture.
- [`render-boards.sh`](render-boards.sh): regenerates all three PNGs locally with no network resources.
- [`WEIBO_SUBMISSION.md`](WEIBO_SUBMISSION.md): ready-to-paste post and evidence links.
- [`RECORDING_SCRIPT.md`](RECORDING_SCRIPT.md): separate 60–75 second director video storyboard.
- [`demo/brief.json`](demo/brief.json): original Patchling Zero input.
- [`demo/ai-draft-plan.json`](demo/ai-draft-plan.json): checksum-locked recorded AI draft.
- [`demo/human-review.json`](demo/human-review.json): scripted rejection/replacement input.
- [`demo/reviewed-plan.json`](demo/reviewed-plan.json): expected reviewed output.
- [`run-demo.sh`](run-demo.sh): offline replay plus opt-in live-cycle support.

## Go / no-go before posting

Post only when all are true:

- `npm test`, offline demo, `git diff --check`, and release build pass;
- public commit contains the exact fixture, review, source SVGs, rights table, and submission pack;
- new director video is recorded, or the post plainly says it is a terminal demo and does not reuse the old V2 video as AI evidence;
- if “人工否决” appears, the human operator confirmed the rejection on camera;
- live install claims appear only if `verify-dream-skin-macos.sh` returned `pass: true`, followed by restore.
