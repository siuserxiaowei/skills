# BUGFIRE character director contract

The director separates creative inference from installable output:

1. A user supplies an original-character brief and a rights declaration.
2. A live OpenAI-compatible endpoint or explicitly recorded AI fixture proposes `creativeDecisions` and `manifestProposal`.
3. A reviewer rejects one decision and supplies a materially different replacement over the same manifest fields.
4. `materialize` writes `bugfire-pack.json` plus `director-report.json`.
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

## Offline evidence

```bash
node bugfire-director.mjs verify-fixture ai-draft.json ai-draft.sha256 brief.json
```

The plan must say `recorded-agent-fixture`, identify its agent/model, and state that replay is not a live call or human approval. A checksum proves integrity only; it does not independently prove model identity.

## Review, materialize, validate

```bash
node bugfire-director.mjs review ai-draft.json human-review.json reviewed-plan.json
node bugfire-director.mjs materialize reviewed-plan.json pack-source
node bugfire-pack.mjs validate pack-source
node bugfire-pack.mjs build pack-source compiled-pack
```

Use new output paths. The director writes through randomly named exclusive temporary files and atomically refuses to replace any existing draft, reviewed plan, materialized manifest, or director report.

Do not label a prepared review fixture as a real person's approval. During a submission recording, the human operator should type or explicitly confirm the rejection and replacement on camera.
