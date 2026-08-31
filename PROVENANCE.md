# BUGFIRE provenance and originality boundary

## Short answer

BUGFIRE is an independent extension built on a pinned MIT-licensed Codex Dream Skin base. The repository may claim an original **implementation and mechanism combination** for its own Patch Dragon experience and the new Character Director gate. It must not claim that desktop pets, AI character direction, human-in-the-loop review, theme packs, or CDP injection were invented here.

## Inherited base

- Upstream: `Fei-Away/Codex-Dream-Skin`
- Pinned commit: [`2f038b5322702cfb248d9c7564b56470a389abc2`](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2)
- License: MIT; see [`LICENSE`](LICENSE), [`NOTICE.md`](NOTICE.md), and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- Inherited capabilities include the external theme engine, loopback CDP integration, native-control preservation, verification, and restore foundations.

Git history retains the upstream commits. Do not squash, rewrite, or relabel that history to imply sole authorship.

## Independent BUGFIRE work

The BUGFIRE branch adds project-specific work including:

- the original Patch Dragon SVG/CSS presentation and six-state pet UX;
- the simulated failure → repair → verified reward state machine, XP, cards, quests, and local progress hardening;
- the declarative `Bugfire Pack v1` compiler, image/path validation, preview, installer, and tests;
- `v1.3.0-bugfire.1` Character Director: a real OpenAI-compatible request path, recorded-fixture verification, a mandatory rejection/replacement gate, and deterministic materialization boundary;
- the original Patchling Zero VibeLab brief and source SVGs under [`contest/bugfire/demo`](contest/bugfire/demo).

These are bounded implementation claims. Similar ideas or independently developed products may exist.

## AI fixture disclosure

[`ai-draft-plan.json`](contest/bugfire/demo/ai-draft-plan.json) was authored in an OpenAI Codex agent session for this repository on 2026-08-31. The public artifact records `Codex agent session (model ID not independently attested)` rather than asserting an unverifiable exact model, and [`ai-draft-plan.sha256`](contest/bugfire/demo/ai-draft-plan.sha256) locks the exact bytes.

The fixture is offline replay evidence. It is **not** presented as:

- a live API request made by the demo script;
- an independently attested model identity;
- proof that a named person reviewed or approved the output.

Checksum verification proves integrity only. The automated live-path test separately starts a loopback OpenAI-compatible mock endpoint and proves that the code performs an HTTP request without persisting its credential.

## Human-review disclosure

[`human-review.json`](contest/bugfire/demo/human-review.json) is a scripted review input prepared so the workflow is reproducible. The demo rejects the AI's orange-first palette and replaces it with a cyan/green verification hierarchy. The file proves the gate and transformation behavior, not a specific person's approval.

Before a public post says “人工否决”, the recording operator should type or explicitly confirm that choice on camera. The checked artifact deliberately uses the neutral reviewer label `VibeLab demo operator`.

## Deterministic boundary

The director can only propose declared manifest fields. Its persisted `manifestProposal.rights` is forcibly derived from the validated human brief, not from an AI claim. Live output receives that binding during generation; recorded-fixture verification requires the brief and independently checks both its digest and exact rights equality even when the fixture checksum is otherwise valid. A live response and the validated plan are recursively checked for the exact API credential before any write. An AI draft cannot materialize. A review must materially change the rejected decision over exactly the same field surface, and `materialize` reconstructs that canonical pre-review draft to verify `humanReview.draftSha256`. Even then, the existing pack validator independently checks schema, local image content, paths, size, dimensions, rights text, and safety limits before build or install.

This is the precise original mechanism being submitted:

> AI proposes → a human rejects and replaces one bounded decision → deterministic validator decides installability → preview / optional live verification → restore.

## Assets

Per-file rights state and SHA-256 records are in [`ASSET_RIGHTS.csv`](ASSET_RIGHTS.csv). The older engineering screenshots and 75-second V2 release video remain evidence for the existing desktop-pet implementation; they are not evidence for the new Character Director path.
