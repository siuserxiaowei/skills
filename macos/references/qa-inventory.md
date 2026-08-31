# QA inventory

## Required user-visible behavior

1. Home route shows one independent image banner, live native heading, two to four native suggestion cards, the real project selector, and native composer.
2. Normal tasks show the selected image behind restrained gradients and translucent live content surfaces.
3. Sidebar, navigation, messages, approvals, project selector, attachments, composer, menus, hover, focus, and keyboard input remain native and interactive.
4. Decorative layers have `pointer-events: none`; no screenshot or raster UI is used as an overlay.
5. Route changes, renderer reloads, and ordinary refreshes reapply the current theme while the verified injector runs.
6. Official application signature and `app.asar` remain unchanged.
7. Restore removes live DOM/CSS, restores the two saved base-theme values, closes the CDP session after restart, and supports later reinstallation.
8. BUGFIRE starts with the labelled Lv2 / 220 XP experience seed; failed Build gives 0 XP and one repaired rebuild gives 35 XP exactly once.
9. The pet collapses on task routes and Escape, its decorative layers never receive pointer events, and interactive controls remain keyboard reachable.
10. Growth cards and the 4:5 PNG certificate include the non-official personal-keepsake disclaimer.

## Automated checks

- Shell and JavaScript syntax checks.
- Payload construction with bundled demo and an isolated custom theme.
- Reject unsupported theme config, unsafe image paths, invalid colors, oversized images, non-loopback WebSocket URLs, and unrecognized renderer targets.
- Exact install/restore round trip for the two TOML settings while preserving unrelated values.
- Empty `HOME` recovery.
- Official app and internal Node signature, Team ID, architecture, and version validation.
- Port collision selection and saved-port reuse.
- PID reuse protection through PID, start time, executable, script path, and command-line matching.
- Live verification after `Page.reload` must return the current runtime version and `pass: true`; the last historical live capture is recorded below.
- Strict home verification requires a visible banner of at least 320×160, two to four visible native cards, visible project button, composer, sidebar, non-interactive decoration, and no horizontal overflow.
- BUGFIRE state and pack-core tests enforce 80% minimum line, branch, and function coverage.
- Binding validation rejects unknown event types, outcomes, oversized payloads, and duplicate settlement IDs; no extra network listener is introduced.
- Pack CLI covers `init`, `validate`, `build`, machine-readable reports, idle-art fallback, explicit replacement, installed-engine path resolution, and local-only embedding.
- Pack validation rejects traversal, final/parent symlink escapes, unsupported or mismatched image content, animation, oversized bytes/pixels, disguised WebP frames, invalid identifiers/colors/quest metrics, oversized text, and undeclared fields.
- Theme switching proves watcher identity before signalling, validates a complete staged copy, atomically swaps directories, and preserves the active theme when staged validation fails.
- Character Director tests observe real OpenAI-compatible loopback HTTP requests, credential non-persistence, strict UTF-8 decoding, no-clobber user outputs, fixture checksum/brief/prompt linkage, mandatory same-surface rejection/replacement, and the independent pack-validation boundary.
- VibeLab evidence checks require three offline 1920×1080 boards with SHA-256 entries in `ASSET_RIGHTS.csv`.

## Visual checks

- Home at normal desktop size: banner crop is readable, text remains live, cards are not clipped, and composer does not overlap content.
- Narrower window: quote/orbit decoration hides before covering essential controls.
- Task route: background remains atmospheric, messages and output panels keep high contrast, and the composer remains reachable.
- Selected image contains no fake interface controls or raster text intended to impersonate Codex.
- Inspect sidebar selection, header, banner edges, cards, project label, composer buttons, scrollbars, focus outlines, dialogs, and menus.
- Exercise idle, building, bug, fire, success, and level-up states; export a PNG and verify the 4:5 card remains legible.
- Check `prefers-reduced-motion`, narrow-window nest-only mode, Escape collapse, and task-route auto-collapse.

## Release signoff

- Run `tests/run-tests.sh` successfully.
- Install from a clean extracted copy with no global Node.js.
- Complete install → live verify → reload verify → restore → reinstall.
- Capture a real CDP screenshot and retain the verifier JSON.
- Capture home, open pet cabin, BUGFIRE/level-up, certificate, and normal-task evidence.
- Confirm the progress file is valid JSON with mode `0600`, survives reload, and is not duplicated by a replayed event ID.
- Confirm `codesign --verify --deep --strict` still succeeds for the official Codex app.
- Build ZIP and record SHA-256.
- Initialize, validate, compile, and switch one clean custom pack; confirm custom state art, sayings, quest board, keepsake title, and progress-ID transition.

## BUGFIRE 1.3.0-bugfire.1 source acceptance (2026-08-31)

- `macos/tests/run-tests.sh`: 105/105 automated tests passed on macOS; shell/JavaScript syntax, payload, config round-trip, signature, doctor, Skill, Pages, and Character Director checks passed.
- Enforced core coverage set: 42/42 tests passed; lines `88.42%`, branches `84.50%`, functions `80.39%` (all thresholds 80%).
- Enforced Character Director coverage set: 18/18 tests passed; lines `97.43%`, branches `82.05%`, functions `89.06%` (all thresholds 80%).
- Offline director Demo passed: fixture SHA-256 and brief/prompt digests verified; `alert-first-palette` changed from `#ff7a1a` to `#35d9d1`; materialization, pack validation, build, preview, and injector payload check returned `pass: true`.
- The live request path was exercised against a real loopback mock HTTP server. Tests observed both supported bearer-request shapes, proved a malicious endpoint reflecting the credential into accepted nested plan fields is rejected before write without logging the key, and proved AI-supplied rights are replaced by the validated human brief. No public claim is made that the checked fixture came from a live endpoint.
- Three offline boards were regenerated and visually inspected at 1920×1080. The AI board says the exact model ID is not independently attested; the review board requires on-camera operator confirmation; the third board is a real generated preview capture.
- Release ZIP built successfully at `macos/release/codex-bugfire-skin-v1.3.0-bugfire.1.zip`; its final SHA-256 is written beside it in the gitignored `release/SHA256SUMS.txt` and must be verified after the last source change.
- A new live install/reload/restore capture was not run during source acceptance. The optional `--live-cycle` remains explicitly gated because it may restart Codex; the older 2026-07-16 live evidence below is engineering context only, not proof of the Character Director workflow.

## BUGFIRE 1.2.0-bugfire.1 source acceptance (2026-07-16)

- `macos/tests/run-tests.sh`: 87/87 automated tests passed outside the restricted process sandbox; syntax, payload, custom-theme, config round-trip, HOME recovery, signature, and non-live doctor checks also passed.
- Enforced coverage set: 42/42 tests passed; lines `88.38%`, branches `84.50%`, functions `80.39%` (all thresholds 80%).
- Independent release-blocker re-audit found no remaining P0/P1 after regression fixes for AppleScript metadata injection and disguised WebP frame dimensions.
- A 3 MiB idle-only pet pack completes payload validation with one encoding and a total payload below 10 MiB; six runtime state aliases do not multiply the asset.
- `--no-apply` leaves the active theme and progress untouched; activation uses a staged same-filesystem directory, exact payload validation, identity-safe watcher cleanup, atomic rename, and rollback.

## Live application evidence captured before final Restore (2026-07-16)

- The then-current BUGFIRE runtime completed 42/42 feature tests before live capture.
- `doctor-macos.sh --require-live`: `pass: true` on Codex `26.707.91948`, Team ID `2DC432GLL2`, bundled Node.js `v24.14.0`; official signature valid and `modifiesAppAsar: false`.
- `verify-dream-skin-macos.sh --reload`: `pass: true`; home hero, four native cards, project selector, composer, sidebar, pet, and zero horizontal overflow verified.
- Restore audit removed the watcher, state file, renderer DOM/style, and Runtime binding without restarting Codex; progress SHA-256 stayed `242a4a4db37a1da2ad241a3064b6637a1550c87cc9d0cb30e89ee798621a5781` with mode `0600`.
- Hot reinstall completed in the same Codex process, rebuilt the base-theme backup, restored the launchd watcher, and wrote progress, state, and backup files with mode `0600`.
- Six privacy-safe PNG assets under `docs/images/bugfire-*.png` cover the home, cabin, failed Build, Lv3 growth card, task route, and season certificate.
- The current Codex process was left in restored official appearance after evidence capture; final source synchronization intentionally does not consume a second restart authorization.
