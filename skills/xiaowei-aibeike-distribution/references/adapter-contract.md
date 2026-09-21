# Adapter contract

This skill treats the distribution package as the stable boundary between content preparation and a publisher. 爱贝壳 is one adapter; a future official API or another browser tool can consume the same package.

## Directory contract

```text
campaign.json                 campaign identity and content anchor
source.json                   immutable source path, bytes, and SHA-256
manifest.json                 package index, publish gate, and platform rows
platforms/<id>/metadata.json  copy and artifact references for one platform
platforms/<id>/status.json    latest per-platform state and evidence pointers
media/                        optional copied video files
covers/                       optional copied cover files
receipts/                     one receipt per platform after verification
validation.json               last local validation report
```

## Manifest shape

```json
{
  "schema": "xiaowei-aibeike/1",
  "campaign_id": "stable-id",
  "created_at": "2026-09-21T12:00:00Z",
  "mode": "aibeike-handoff",
  "source": {"path": "/absolute/video.mp4", "bytes": 123, "sha256": "..."},
  "media": {"path": "media/video.mp4", "sha256": "..."},
  "publish": {"gate": "manual-confirmation-required", "requested": false},
  "platforms": [
    {
      "id": "douyin",
      "job_id": "stable-id:douyin",
      "metadata": "platforms/douyin/metadata.json",
      "status": "platforms/douyin/status.json",
      "state": "prepared"
    }
  ]
}
```

`metadata` may contain `title`, `description`, `tags`, `video`, `cover`, `visibility`, `schedule`, `original_declaration`, `ai_disclosure`, and `review_notes`. Keep platform-specific values in that platform file; do not use one global caption and assume every editor accepts it.

## State machine

```text
prepared → drafted → scheduled → published
    └──────────────→ failed
    └──────────────→ blocked
```

Only a fresh receipt can move a platform out of `prepared`. `failed` means an action returned an error. `blocked` means the next step needs a user, account, permission, captcha, or changed UI. A timeout with no fresh page evidence is `blocked` or `failed`, never `published`.

## Idempotency

Use `campaign_id` plus platform ID as the stable job key. A retry must first inspect the existing draft/task state. Never create a second post solely because the previous browser or network call did not return a response.

## Publish boundary

The package deliberately starts with `publish.requested: false`. A browser adapter may prepare and save a draft. A public action must be a separate, user-authorized operation and must leave a receipt containing the platform, account, resulting URL or platform ID, time, and evidence reference.
