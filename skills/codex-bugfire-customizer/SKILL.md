---
name: codex-bugfire-customizer
description: Direct, build, validate, preview, install, or package a custom Codex BUGFIRE companion from an original character brief and user-supplied background/pet images. Use when someone asks to create a structured AI character-direction draft, make their own Codex desktop pet or skin, convert owned PNG/JPEG/WebP art into a Bugfire Pack, require a human rejection/review gate, validate a bugfire-pack.json folder, or prepare a reusable companion pack without modifying the official Codex app.
---

# Codex BUGFIRE Customizer

Create one portable `Bugfire Pack` that controls the Codex background, six pet states, interaction sayings, local quest board, colors, and keepsake title. Use the deterministic compiler in this skill; do not hand-edit the runtime injector.

## Locate the engine

Run `scripts/find-engine.sh`. It prints the first valid engine directory from `CODEX_BUGFIRE_ROOT`, this skill's repository, or `~/.codex/codex-dream-skin-studio`.

Require either repository layout `macos/scripts/bugfire-pack.mjs` or installed-engine layout `scripts/bugfire-pack.mjs`. If no engine is found, ask the user to clone the project or set `CODEX_BUGFIRE_ROOT`.

## Gather inputs

Read [references/input-contract.md](references/input-contract.md) before accepting or generating assets.

Require exactly these minimum user inputs:

- one background image;
- one transparent or clean-background pet image used for every state;
- pack name and pet name;
- confirmation that the user has permission to use the assets.

Accept five optional pet images for `building`, `bug`, `fire`, `success`, and `levelUp`, plus a tagline, quote, palette, sayings, quest titles/targets, season label, and keepsake title.

Never require task text, source code, prompts, API keys, shell output, or account data. Do not fetch copyrighted character art merely because a user names a character; require user-supplied or clearly licensed art.

## Optional AI character director

Read [references/director-contract.md](references/director-contract.md) when the user wants AI-assisted character direction. The director may propose names, palette, voice, quests, and a pack manifest, but it cannot approve rights or bypass the pack validator.

For a real OpenAI-compatible request, set credentials in the environment and run the engine's `bugfire-director.mjs draft-live`. Never put the key in a command argument, plan, log, or shared fixture. If no key is available, do not pretend a live call happened; use a clearly labelled, checksum-verified recorded fixture if the project supplies one.

Before materialization, require an explicit review file that rejects and materially replaces one decision. `materialize` accepts only a `human-approved` plan; `bugfire-pack validate` is still mandatory afterward. Treat a scripted review fixture as a reproducible demo input, not proof that a named person approved it.

## Build a pack

1. Create a working directory outside the engine source tree.
2. Initialize it:

   ```bash
   node scripts/create-pack.mjs init /absolute/path/to/workdir
   ```

3. Copy user files to the exact paths declared by `bugfire-pack.json`. The starter requires `assets/background.png` and `assets/pet-idle.png`.
4. Edit only `bugfire-pack.json`; preserve schema version 1 and allowed quest metrics.
5. Validate, then compile into a separate empty directory:

   ```bash
   node scripts/create-pack.mjs validate /absolute/path/to/workdir
   node scripts/create-pack.mjs build /absolute/path/to/workdir /absolute/path/to/output
   ```

6. Inspect `theme.json` and `pack-report.json`. Report which optional state images fell back to idle art.

Do not bypass validation or copy undeclared files into the output.

## Preview and install

Create an offline interactive preview. Use its six state buttons to inspect every mapping and click the pet to sample configured sayings:

```bash
node scripts/create-pack.mjs preview /absolute/path/to/output /absolute/path/to/preview.html
```

Install only when the user asks to apply the pack:

```bash
ENGINE="$(scripts/find-engine.sh)"
if [ -x "$ENGINE/macos/scripts/install-bugfire-pack-macos.sh" ]; then
  INSTALLER="$ENGINE/macos/scripts/install-bugfire-pack-macos.sh"
else
  INSTALLER="$ENGINE/scripts/install-bugfire-pack-macos.sh"
fi
"$INSTALLER" --pack /absolute/path/to/workdir --no-apply
```

Without `--no-apply`, first tell the user that applying may ask to restart Codex. Never restart silently. Preserve the official `.app`, `app.asar`, signature, native controls, and loopback-only CDP boundaries.

## Verify

Run:

```bash
ENGINE="$(scripts/find-engine.sh)"
cd "$ENGINE/macos"
npm test
node scripts/injector.mjs --check-payload --theme-dir /absolute/path/to/output
```

After an explicitly authorized live install, also run `doctor-macos.sh --require-live` and `verify-dream-skin-macos.sh --reload`. Do not claim live success unless the verifier returns `pass: true`.

## Package for sharing

Share the compiled output directory or ZIP, not the raw workspace. Include `theme.json`, declared local images, and `pack-report.json`. Do not include progress files, logs, personal paths, `.codex/auth.json`, task screenshots, or API configuration.

Use [references/acceptance.md](references/acceptance.md) for final signoff. Read [references/research-notes.md](references/research-notes.md) only when explaining why these mechanics were selected.
