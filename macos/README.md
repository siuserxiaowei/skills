# Codex Dream Skin Studio

Unofficial macOS theme studio for the **official Codex Desktop** app.

Turn an image you like into a Codex theme: a dedicated home banner, a low-noise task background, and frosted content layers — while **keeping native sidebar, suggestion cards, project picker, task content, menus, and composer** fully interactive.

This project injects through **local loopback CDP**. It does **not** modify the official `.app`, `app.asar`, or code signature.

> Not affiliated with OpenAI. Codex is a trademark of its respective owners.

## Requirements

- macOS
- Official Codex Desktop installed and launched at least once (`~/.codex/config.toml` exists)
- No global Node.js install required (uses Codex’s signed bundled Node after validation)

## Quick start (from this repo)

```bash
# 1) Optional static checks (needs Codex.app present for bundled Node path)
./tests/run-tests.sh

# 2) Install to the stable path and create Desktop launchers
./scripts/install-dream-skin-macos.sh --no-launch

# 3) Customize with your image (Finder picker if you omit flags)
~/.codex/codex-dream-skin-studio/scripts/customize-theme-macos.sh

# 4) Start / re-apply, verify, or restore via Desktop:
#    Codex Dream Skin.command
#    Codex Dream Skin - Customize.command
#    Codex Dream Skin - Verify.command
#    Codex Dream Skin - Restore.command

# 5) Optional: menu bar (SwiftBar) — apply / pause / change image
./Install\ Menu\ Bar.command
# Look for 🎨 Skin in the top-right menu bar
```

Install location after step 2:

| Item | Path |
| --- | --- |
| Engine | `~/.codex/codex-dream-skin-studio` |
| State / logs / user images | `~/Library/Application Support/CodexDreamSkinStudio` |
| Theme backup | under Application Support (`theme-backup.json`) |

## BUGFIRE 补丁兽

This fork adds an original local coding companion without replacing any Codex controls. Open the
72 px nest in the lower-right corner to run a clearly labelled simulated Build: the first pass
creates a Bug without XP, and a repaired rebuild lets the patch dragon use BUGFIRE and gain 35 XP.

- The first-run experience seed is Lv2 at 220 / 240 XP so one repaired rebuild demonstrates a level-up.
- Reset starts a genuine Lv1 / 0 XP local record.
- Progress is stored at `~/Library/Application Support/CodexDreamSkinStudio/bugfire-progress.json`
  with mode `0600`; no task text, source code, API key, or real shell output is read.
- Renderer events cross the already-verified CDP session through one `Runtime` binding. No extra
  HTTP server or listening port is created.
- Growth cards and the Season 01 PNG are personal local keepsakes, not an official certification
  or a professional-skills assessment.

The demo never runs a project command. A future real-Build bridge must be separately authorized
and may only consume the exit code of an explicit allowlisted command.

## Custom companion packs

`Bugfire Pack v1` turns the fixed demo into a reusable system. A pack may provide a background,
one reusable pet image or six state-specific images, a palette, names, click sayings, derived local
quests, and a keepsake title. It cannot contain executable code, remote assets, SVG/GIF payloads, or
paths outside its own folder.

```bash
cd macos
. ./scripts/common-macos.sh
discover_codex_app
require_macos_runtime

PACK="$HOME/Documents/my-bugfire-pack"
OUTPUT="$HOME/Documents/my-bugfire-pack-built"

"$NODE" ./scripts/bugfire-pack.mjs init "$PACK"
# Add assets/background.png and assets/pet-idle.png, then edit bugfire-pack.json.
"$NODE" ./scripts/bugfire-pack.mjs validate "$PACK"
"$NODE" ./scripts/bugfire-pack.mjs build "$PACK" "$OUTPUT"

# Put a validated build in the local theme library without changing the live theme.
./scripts/install-bugfire-pack-macos.sh --pack "$PACK" --no-apply

# Activate only after review; a cold Codex session may need to restart.
./scripts/switch-theme-macos.sh --id my-codex-companion
```

The pack ID passed to `switch-theme-macos.sh` must equal the manifest `id`. Omitting `--no-apply`
from the installer validates, builds, and activates in one command. Use a different source and
output directory: `build ... --replace` removes an existing output, and the compiler refuses
source/output overlap.

| Input | Limit |
| --- | --- |
| Manifest | 128 KiB; schema v1; no undeclared fields |
| Background | PNG/JPEG/WebP; 16 MiB; max dimension 8192 px; max 32 Mi pixels |
| Each pet image | PNG/JPEG/WebP; 4 MiB; max dimension 4096 px; max 8 Mi pixels |
| Declared pet art total | 16 MiB |
| Text rules | 1–12 sayings, 1–5 aggregate-only quests, reward 1–100 XP |

One background and `pet.art.idle` are required. The other five state images are optional and fall
back to idle. APNG, animated WebP, SVG, GIF, symlinked files, parent-link escapes, extension/content
mismatches, remote URLs, and pack-provided JavaScript/CSS are rejected. The rights declaration is
required. The five XP levels remain fixed.

Changing the manifest `id` or `pet.seasonId` archives the previous progress as a `.previous...` file and creates
the labelled Lv2 experience seed for the new identity; records from different packs are not merged.
Activation stages and validates a complete copy, stops identity-checked watchers, then swaps the
active directory atomically with rollback.

See `../docs/CUSTOMIZATION.zh-CN.md` and `../skills/codex-bugfire-customizer/`.

## AI Character Director (optional)

The director can make a real OpenAI-compatible request that turns an original-character brief into bounded creative decisions and a pack-manifest proposal. It is deliberately outside the desktop-pet runtime.

```bash
export BUGFIRE_OPENAI_BASE_URL="https://your-compatible-endpoint.example/v1"
export BUGFIRE_OPENAI_MODEL="your-model-id"
export BUGFIRE_OPENAI_API_KEY="your-secret"
node ./scripts/bugfire-director.mjs draft-live brief.json ai-draft.json \
  --model "$BUGFIRE_OPENAI_MODEL" --base-url "$BUGFIRE_OPENAI_BASE_URL"
unset BUGFIRE_OPENAI_API_KEY

node ./scripts/bugfire-director.mjs review ai-draft.json human-review.json brief.json reviewed-plan.json
node ./scripts/bugfire-director.mjs materialize reviewed-plan.json brief.json pack-source
node ./scripts/bugfire-pack.mjs validate pack-source
```

An `ai-draft` cannot materialize. A review must reject and materially replace one decision over the same bounded manifest fields. Both `review` and `materialize` require the operator-controlled human brief as a separate input and independently recheck its canonical digest and exact rights against the plan; skipping `verify-fixture` therefore does not bypass the rights binding. The resulting source still has to pass the existing pack validator. API keys are environment-only; the accepted response payload and validated plan are recursively scanned for the exact credential value before any write, so a reflecting endpoint fails closed. Endpoint-controlled envelope/content parse failures return stable generic messages and never append parser excerpts that may contain the key. A declared response `Content-Length` above 1 MiB is rejected before body consumption, and every response is then accumulated with a 1 MiB streaming-reader cap that cancels on the first crossing chunk. This bounds application accumulation; the HTTP/runtime stack can still buffer before yielding a chunk. Live manifest rights are derived from the validated human brief, never accepted from AI output; recorded fixtures are accepted only when the mandatory brief has the same digest and exact rights. Remote endpoints require HTTPS, while HTTP is restricted to loopback local-model/test endpoints. Director JSON is decoded as strict UTF-8, and draft, review, and materialize destinations must be new paths: existing files are never overwritten. `materialize` reconstructs the canonical pre-review draft and verifies `humanReview.draftSha256` before writing.

The supplied brief is the caller's trust root. These checks prove consistency with that chosen file; they do not authenticate who authored it or establish legal ownership. The SHA-256 fields are integrity digests, not signatures.

Materialization checks every existing output-path component below the current working directory, user home, or system temporary-directory anchor and rejects symbolic links before and after directory creation. This reduces accidental or attacker-chosen redirection, but Node does not expose a portable directory-fd `openat` chain here; a local process with permission to race and replace an ancestor during the check/write interval remains outside this CLI's guarantee. Use a private output directory and do not run beside untrusted local processes.

The repository's full offline example and disclosure are in `../contest/bugfire/`.

## Customer ZIP (optional packaging)

To build the “double-click install” folder layout for non-git users:

```bash
./scripts/build-client-release.sh "$HOME/Desktop/Codex 主题编辑器.zip"
```

That ZIP contains a visible installer plus a hidden `.codex-dream-skin-studio` engine. Do not ship only CSS/images.

## How it works (security boundary)

1. Discover `com.openai.codex` and validate signature / Team ID / arch / bundled Node.
2. Start Codex via user `launchd` with CDP bound to `127.0.0.1` only.
3. Accept the debug port only when it belongs to Codex (or a legitimate child).
4. Inject only into expected `app://` renderer targets.
5. Keep a small injector alive across reloads and route changes.
6. Validate and atomically persist BUGFIRE events received through the verified CDP binding.
7. Restore stops the injector only when PID, path, and start time match the recorded job.

CDP is powerful and unauthenticated on loopback. Prefer Restore when you are done theming.

## Image guidelines

- PNG / JPEG / HEIC / TIFF / WebP (macOS readable)
- Source ≤ 50 MB; prepared file ≤ 16 MB
- Wide images work best (width ≥ 2000 px recommended)
- Keep the left side relatively calm for native home titles
- Image is banner + background only — never a full-window fake UI overlay

HEIC and TIFF support applies only to the background customizer. `Bugfire Pack v1` assets accept
PNG, JPEG, and WebP only.

CLI example:

```bash
~/.codex/codex-dream-skin-studio/scripts/customize-theme-macos.sh \
  --image "/path/to/image.png" \
  --name "My theme" \
  --accent "#7cff46" \
  --secondary "#36d7e8" \
  --highlight "#642a8c"
```

Reset to the bundled abstract demo:

```bash
~/.codex/codex-dream-skin-studio/scripts/customize-theme-macos.sh --reset-demo
```

## License

MIT — see `LICENSE`. Additional notices in `NOTICE.md` (trademarks, demo asset, runtime Node).

## What this is not

- Not an OpenAI product and not a fork of Codex source
- Not a way to patch or rebrand the official binary
- Not a Windows build; upstream Windows theme-tooling source remains in the [repository `windows/` directory](https://github.com/siuserxiaowei/Codex-Bugfire-Skin/tree/main/windows).
- Not an API proxy: theming does not change model providers or API keys

If you use a third-party API relay, configure it separately — keep theme install and API config as two explicit steps.
