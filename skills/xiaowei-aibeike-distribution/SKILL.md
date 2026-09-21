---
name: xiaowei-aibeike-distribution
description: Build and operate a local-first video distribution campaign for 爱贝壳内容同步助手 and other platform adapters. Use when a user wants one video prepared for batch distribution, platform-specific titles/captions/covers, 爱贝壳 handoff packages, draft creation, browser-assisted filling, publish-status tracking, or safe retries. Default to preparing and verifying drafts; never treat an attempted click as a successful publish and never click a final publish button without an explicit, current user instruction.
---

# Xiaowei Aibeike Distribution

Use this skill as a new distribution control layer. It is independent of any third-party publisher skill. It learns from proven patterns—source locking, draft-first workflows, platform profiles, idempotent jobs, per-platform isolation, and fresh verification—while keeping the package contract and state machine under this skill's control.

## Operating contract

1. Keep the original video immutable. Resolve the exact file, record size and SHA-256, and never silently replace it.
2. Separate preparation from execution. Preparing files, copy, and a handoff package is allowed by default; saving drafts is allowed when requested; final publication requires a fresh explicit instruction.
3. Treat every platform independently. One failure must not mark the campaign successful or block unrelated platforms.
4. Verify resulting page state, not an attempted action. A draft is verified only when the platform page or 爱贝壳 task view shows the expected title, media, cover, settings, and draft state.
5. Make retries idempotent. Reuse the same campaign and platform job IDs; do not create a second post merely because a browser or network call timed out.
6. Keep credentials out of manifests, logs, prompts, and generated files. Use the already logged-in browser session or an official credential store.
7. Never reverse-engineer private 爱贝壳 endpoints. Use the file handoff adapter by default. Use browser UI only when the user explicitly asks for it and the session is already authorized. Use an API adapter only when the vendor supplies current official documentation.

## Modes

Select one mode before doing work:

- **package** (default): inspect the source, create platform variants and metadata, validate them, and emit an 爱贝壳-ready handoff package. Do not open creator pages or publish.
- **draft-ui**: use a browser automation tool to open the user's existing 爱贝壳 session, inspect the current UI, fill one platform at a time, save drafts, and independently verify each result. Keep the final publish control untouched.
- **official-api**: use only a documented, authorized API. Record the API version and endpoint source in the campaign manifest. If documentation or authorization is missing, fall back to `package`.

If the user says “同步”“批量发” without specifying a mode, use `package` and explain that the resulting package is ready for 爱贝壳. Do not infer permission to publish publicly.

## Workflow

### 1. Establish the campaign brief

Collect or infer only what is needed:

- exact source video path;
- target platforms and account identity when multiple accounts exist;
- whether the source already contains burned-in subtitles;
- per-platform title, description, tags, cover, visibility, and schedule;
- rights/original declaration and any required disclosure;
- requested mode and whether the user wants drafts or public publication.

Keep one content anchor: the factual claim, audience promise, and call to action must remain stable across variants. Adapt length, hook, tags, cover ratio, and disclosure per platform without inventing claims.

### 2. Lock and inspect the source

Create a task directory beside the source or in the user's chosen work directory:

```text
<video>.xiaowei-aibeike/
├── campaign.json
├── source.json
├── manifest.json
├── platforms/<platform>/metadata.json
├── platforms/<platform>/status.json
├── media/
├── covers/
└── receipts/
```

Run `scripts/create_delivery_package.py` to create the initial package. Run `scripts/validate_delivery_package.py` before any browser or API work. The validator must pass with a fresh hash check and no unresolved path errors.

### 3. Build platform variants

Use `references/platform-profiles.md` as a starting point, then inspect the current platform or user-provided requirements. A profile is a constraint set, not proof of the current UI.

For each platform produce:

- a platform-specific video path or the source path;
- a title and description that fit the current editor;
- tags as separate values where the editor has tag chips;
- a cover path and ratio when the platform accepts a custom cover;
- visibility, original-content, AI-content, and schedule fields when relevant;
- a short human review note for any judgment call.

Keep raw source text, generated copy, and user-approved copy distinguishable. Never overwrite user-authored copy without recording the change in the platform metadata.

### 4. Handoff to 爱贝壳

The handoff contract is a directory plus `manifest.json`. It must contain stable relative artifact paths, source fingerprints, platform metadata, an explicit `publish.gate` of `manual-confirmation-required`, and one status file per platform.

Prefer this sequence:

1. Validate the package locally.
2. Open 爱贝壳 and select the intended content type and target platforms.
3. Import or select the package media and paste the platform metadata from each `metadata.json`.
4. Save drafts or schedule only when the user requested that outcome.
5. Capture fresh evidence: target platform, account, title, cover, media duration/thumbnail, visibility, and draft/schedule state.
6. Record the receipt with the platform status. A receipt without fresh evidence is not success.

If using browser automation, follow the `inspect → act → verify` loop. Reuse one browser task space for the entire campaign. Stop and report a typed blocker when login, captcha, permissions, unsupported media, or a changed UI prevents verification.

### 5. Publish gate

Before any public publish action, show the user a compact preflight containing:

- source fingerprint and selected platforms;
- exact title, cover, visibility, schedule, and rights/disclosure fields per platform;
- unresolved warnings and failed platforms;
- the exact action about to happen.

Only proceed if the user explicitly authorizes that current action. Otherwise leave verified drafts open and report their locations.

### 6. Recover and report

Use the same campaign ID and platform job ID on retries. Retry only the failed or unverifiable platform. Do not re-upload successful drafts unless the user requests a replacement. Record `drafted`, `scheduled`, `published`, `failed`, or `blocked` separately for every platform.

Report the result with the package path, validation report, platform receipts, and any manual steps that remain. Distinguish verified facts from assumptions and UI observations.

## Bundled tools

- `scripts/create_delivery_package.py`: create an immutable-source campaign package from a metadata JSON file.
- `scripts/validate_delivery_package.py`: validate schema, paths, source fingerprints, platform records, and the manual publish gate.
- `scripts/record_platform_receipt.py`: update one platform's status after fresh UI/API evidence.

Read these references only when needed:

- `references/adapter-contract.md` for the package schema and state transitions;
- `references/platform-profiles.md` for cautious platform defaults;
- `references/examples.md` for positive, boundary, and recovery cases;
- `references/research-synthesis.md` for the independent design rationale and source links.

## Minimal invocation

```bash
python3 scripts/create_delivery_package.py \
  --source /absolute/path/video.mp4 \
  --metadata /absolute/path/metadata.json \
  --out /absolute/path/video.xiaowei-aibeike \
  --copy-media

python3 scripts/validate_delivery_package.py \
  /absolute/path/video.xiaowei-aibeike
```

The metadata file is content input, not credentials. A minimal shape is:

```json
{
  "campaign_id": "jev-fde-20260921",
  "content_anchor": "一句经过确认的核心观点",
  "platforms": {
    "douyin": {"title": "标题", "description": "简介", "tags": ["AI", "教程"]},
    "xiaohongshu": {"title": "标题", "description": "正文", "tags": ["AI"]}
  }
}
```
