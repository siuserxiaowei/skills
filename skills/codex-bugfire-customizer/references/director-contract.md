# BUGFIRE character director contract

The director separates creative inference from installable output:

1. A user supplies an original-character brief and a rights declaration.
2. A live OpenAI-compatible endpoint or explicitly recorded AI fixture proposes `creativeDecisions` and `manifestProposal`; `manifestProposal.rights` is discarded and replaced with the validated human brief's rights declaration.
3. A reviewer supplies the same operator-controlled brief, rejects one decision, and supplies a materially different replacement over the same manifest fields. Review rechecks the plan's brief digest and exact rights.
4. `materialize` requires that brief again, rechecks the binding independently, then writes `bugfire-pack.json` plus `director-report.json`.
5. The independent `bugfire-pack` validator checks paths, fields, images, dimensions, rights text, and safety limits before build or install.

## Live request

Locate `bugfire-director.mjs` under the engine's `macos/scripts/` or `scripts/` directory, then run:

```bash
export BUGFIRE_OPENAI_BASE_URL="https://your-compatible-endpoint.example/v1"
export BUGFIRE_OPENAI_MODEL="your-model-id"
export BUGFIRE_OPENAI_API_KEY="your-secret"
node bugfire-director.mjs draft-live brief.json ai-draft.json \
  --model "$BUGFIRE_OPENAI_MODEL" --base-url "$BUGFIRE_OPENAI_BASE_URL"
unset BUGFIRE_OPENAI_API_KEY
```

Use `--api-mode responses` for a Responses-compatible endpoint. Remote HTTP is rejected; only HTTPS is allowed. HTTP is accepted for loopback local-model/test endpoints.

The API key is environment-only. Before a live draft can be written, both the parsed endpoint payload and the validated plan are recursively checked for the exact credential value. If an endpoint reflects the key into any accepted string or object key, generation is rejected without an output file.

If the endpoint declares a `Content-Length` above 1 MiB, the response is rejected before body consumption. Every response is then read chunk by chunk with a 1 MiB application cap; the body reader is cancelled as soon as the next chunk would cross it. The HTTP/runtime stack may buffer before yielding an individual chunk, so this is an application accumulation and early-cancellation boundary rather than a claim about all transport buffering.

## Offline evidence

```bash
node bugfire-director.mjs verify-fixture ai-draft.json ai-draft.sha256 brief.json
```

The brief argument is mandatory. The verifier requires the plan to say `recorded-agent-fixture`, checks the checksum and prompt/brief digests, and requires persisted `manifestProposal.rights` to exactly match the validated human brief rights. It also requires the artifact to state that replay is not a live call or human approval. A checksum proves integrity only; it does not independently prove model identity or rights on its own.

## Review, materialize, validate

```bash
node bugfire-director.mjs review ai-draft.json human-review.json brief.json reviewed-plan.json
node bugfire-director.mjs materialize reviewed-plan.json brief.json pack-source
node bugfire-pack.mjs validate pack-source
node bugfire-pack.mjs build pack-source compiled-pack
```

Use new output paths. The director writes through randomly named exclusive temporary files and atomically refuses to replace any existing draft, reviewed plan, materialized manifest, or director report.

The brief is not optional at either boundary. Calling `review` directly on an unverified recorded plan cannot persist rights that differ from the supplied brief, and `materialize` repeats the check rather than trusting the reviewed plan alone. The operator chooses and safeguards this brief; the CLI proves consistency with it, not its authorship or legal sufficiency. SHA-256 values in this workflow are integrity digests, not signatures.

`materialize` reconstructs the canonical pre-review draft from the retained original decision and checks it against `humanReview.draftSha256`. It also rejects symbolic-link components in the caller-controlled portion of the output path before and after directory creation. A privileged or same-user local process that can win a path replacement race remains outside this portable Node CLI's guarantee, so use a private output directory.

Do not label a prepared review fixture as a real person's approval. During a submission recording, the human operator should type or explicitly confirm the rejection and replacement on camera.
