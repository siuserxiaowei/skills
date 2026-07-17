# BUGFIRE Patch Dragon — a pixel desktop pet for Codex on macOS

[中文](README.md)

[![Live demo](https://img.shields.io/badge/LIVE_DEMO-BUGFIRE-83ff45?style=for-the-badge&labelColor=050704)](https://siuserxiaowei.github.io/Codex-Bugfire-Skin/)
[![Latest release](https://img.shields.io/github/v/release/siuserxiaowei/Codex-Bugfire-Skin?style=for-the-badge&label=DOWNLOAD&labelColor=050704&color=ff7a1a)](https://github.com/siuserxiaowei/Codex-Bugfire-Skin/releases/latest)
[![Tests](https://img.shields.io/github/actions/workflow/status/siuserxiaowei/Codex-Bugfire-Skin/ci.yml?branch=main&style=for-the-badge&label=CI&labelColor=050704)](https://github.com/siuserxiaowei/Codex-Bugfire-Skin/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/LICENSE-MIT-f4efd8?style=for-the-badge&labelColor=050704)](LICENSE)

**BUGFIRE is an unofficial, local pixel-art desktop pet for Codex Desktop on macOS.** Its clearly labelled demo turns a small coding loop into playable feedback: a simulated Build fails, a Bug appears, a repaired rebuild succeeds, and the Patch Dragon breathes fire to level up. BUGFIRE does not run project commands or read task text, source code, prompts, API keys, or shell output. Pet levels track local activity only; they are not a programming-skills assessment, professional qualification, or OpenAI certification.

> Current version: `1.2.0-bugfire.1` · macOS first release candidate · Unofficial project

![BUGFIRE Patch Dragon in the lower-right corner of the Codex Desktop home screen](docs/images/bugfire-home.png)

**[▶ Try the interactive demo](https://siuserxiaowei.github.io/Codex-Bugfire-Skin/)** · **[↓ Download the latest release](https://github.com/siuserxiaowei/Codex-Bugfire-Skin/releases/latest)** · **[🧩 Build your own companion](skills/codex-bugfire-customizer/SKILL.md)**

[Chinese usage guide](docs/USAGE.zh-CN.md) · [Security architecture](docs/SECURITY-ARCHITECTURE.zh-CN.md) · [Privacy notes](docs/PRIVACY.md) · [Security policy](SECURITY.md) · [macOS technical notes](macos/README.md) · [GEO analysis](GEO-ANALYSIS.md) · [SEO/GEO release plan](SEO-PLAN.md)

## What does BUGFIRE do?

- Adds a 72 px pet nest to Codex and opens a roughly 320 × 420 px cabin.
- Includes six original SVG/CSS states: `idle`, `building`, `bug`, `fire`, `success`, and `level-up`.
- Starts with a clearly labelled experience save at `Lv2 · 220/240 XP`.
- Awards no XP for a failed demo Build and exactly 35 XP for one repaired rebuild.
- Provides five local progression levels, 4:5 growth cards, and an exportable PNG season keepsake.
- Collapses on task routes, avoids the composer, supports keyboard input and Escape, adapts to narrow windows, and respects `prefers-reduced-motion`.
- Preserves the native Codex sidebar, project picker, task content, menus, and composer.
- Supports locally authored pet packs with custom backgrounds, six-state pet art, colors, sayings, aggregate-only quests, reward XP, and keepsake titles.

| Key fact | Current implementation |
| --- | --- |
| Platform | macOS with the official Codex Desktop app |
| Version | `1.2.0-bugfire.1` |
| Build behavior | Clearly labelled local simulation; no shell command |
| Progress file | `~/Library/Application Support/CodexDreamSkinStudio/bugfire-progress.json`, mode `0600` |
| Integration | Codex CDP bound only to `127.0.0.1`; progress sync opens no additional port |
| Custom pet packs | Local `bugfire-pack` CLI; one background plus one idle image required; no remote asset downloads |
| Official app mutation | None; no `.app`, `app.asar`, or signature changes |
| Credential status | Personal local keepsake, not an official credential |

## How does the simulated Build work?

| Step | Feedback | XP |
| --- | --- | ---: |
| Open the pet nest | The cabin shows `Lv2 · 220/240 XP` | 0 |
| Select `BUILD · Demo` | The first simulated Build fails and spawns a Bug | 0 |
| Select “Fixed — rebuild” | The Patch Dragon burns the Bug | +35 |
| Cross 240 XP | Reach Lv3, unlock `BUGFIRE`, and receive a growth card | Included above |

<p align="center">
  <img src="docs/images/bugfire-pet-cabin.png" alt="BUGFIRE pet cabin showing Lv2, 220/240 XP, and the simulated Build control" width="49%">
  <img src="docs/images/bugfire-build-failed.png" alt="The first BUGFIRE demo Build fails without awarding XP" width="49%">
</p>

![BUGFIRE reaches Lv3 and unlocks the BUGFIRE growth card](docs/images/bugfire-level-up.png)

> Public screenshots are privacy-safe: native sidebars are cropped, covered, or blurred as needed, and real project names are replaced with `BUGFIRE DEMO`.

## What are the five progression levels?

| Level | XP | Vibe stage | Skill |
| --- | ---: | --- | --- |
| Lv1 | 0–99 | Describe | Inspiration Spark |
| Lv2 | 100–239 | Assemble | Structure Sniffer |
| Lv3 | 240–449 | Debug | BUGFIRE |
| Lv4 | 450–749 | Verify | Test Ward |
| Lv5 | 750+ | Deliver | Release Leap |

Levels represent BUGFIRE activity only. They do not measure objective programming ability.

The Season 01 PNG keepsake requires Lv5, at least 10 successful simulated Builds, and at least 3 repaired rebuilds.

![Preview of the BUGFIRE Season 01 local growth keepsake](docs/images/bugfire-certificate.png)

Every exported certificate includes this notice:

> Personal growth keepsake generated from local activity; not an official certification and not evidence of professional qualification.

## Can I build my own pet pack?

Yes. The local `Bugfire Pack v1` CLI initializes, validates, and compiles custom packs. A pack needs one background and one idle pet image; art for `building`, `bug`, `fire`, `success`, and `level-up` is optional and falls back to idle. Packs may customize identity, season, nine theme colors, sayings, aggregate-only quests, repaired-Build XP, and the keepsake title. The five-level XP table remains fixed and auditable.

The compiler accepts declarative JSON plus local PNG, JPEG, or WebP files only. It does not fetch remote art or execute pack-provided JavaScript or CSS. See the [customization guide](docs/CUSTOMIZATION.zh-CN.md) and [macOS technical notes](macos/README.md) for commands, limits, rights declarations, and progress behavior.

## How do I install BUGFIRE?

Requirements:

- macOS;
- the official Codex Desktop app, launched at least once;
- a Codex-created `~/.codex/config.toml`;
- permission to close and reopen Codex once during first-time activation.

No global Node.js installation is required. The installer validates the official app signature, Team ID, architecture, and bundled Node.js before it proceeds.

Double-click [`macos/Install Codex Dream Skin.command`](macos/Install%20Codex%20Dream%20Skin.command), or run:

```bash
cd macos
./tests/run-tests.sh
./scripts/install-dream-skin-macos.sh --no-launch
~/.codex/codex-dream-skin-studio/scripts/start-dream-skin-macos.sh --prompt-restart
```

The engine is installed at `~/.codex/codex-dream-skin-studio`. Progress stays in the Application Support path listed above. BUGFIRE pet functionality is currently implemented and tested on macOS; the upstream project's Windows theme scripts do not imply Windows pet support.

## How do I use it?

1. Open the pet nest in the lower-right corner.
2. Select `BUILD · Demo` and watch the first simulated failure.
3. Select “Fixed — rebuild” to trigger fire, +35 XP, and the Lv3 card.
4. Press `Escape` to close a card or collapse the cabin.
5. Open a normal task and confirm that the cabin collapses away from the native composer.

Keyboard users can reach controls with `Tab` and activate them with `Enter` or `Space`.

![A privacy-safe Codex task-route capture showing the collapsed Lv3 pet and native composer controls](docs/images/bugfire-task.png)

## What data is stored?

The progress file is written atomically with mode `0600`. It stores only the schema version, pet and season IDs, XP, aggregate Build counters, unlocked skills, growth-card records, settled event IDs, and an update timestamp.

It does not store task text, prompts, conversations, source files, API keys, provider settings, or real shell output.

## What is the security boundary?

BUGFIRE uses a Codex CDP port bound only to `127.0.0.1`. A validated Runtime binding reuses that renderer session to synchronize pet events, so progress sync opens no additional HTTP server or network port. The extension does not write into the official application bundle.

CDP is powerful even on loopback. Do not expose the port on `0.0.0.0`, and avoid untrusted local software while a themed session is active.

## How do I verify, pause, or restore it?

```bash
# Verify live app identity, signature, version, and injection
~/.codex/codex-dream-skin-studio/scripts/doctor-macos.sh --require-live

# Reload the renderer and verify re-injection
~/.codex/codex-dream-skin-studio/scripts/verify-dream-skin-macos.sh --reload

# Pause without closing Codex
~/.codex/codex-dream-skin-studio/scripts/pause-dream-skin-macos.sh

# Remove live injection and restore the previous base theme
~/.codex/codex-dream-skin-studio/scripts/restore-dream-skin-macos.sh \
  --restore-base-theme --restart-codex
```

## FAQ

### Does BUGFIRE run my project's Build command?

No. `BUILD · Demo` drives a local state machine only. It does not call npm, pnpm, make, xcodebuild, or another project command. Any future real-Build bridge would require separate user authorization and an explicit allowlist.

### Why does the first Build award zero XP?

Failure spawns the Bug but awards no XP. One repaired rebuild awards 35 XP. A unique event ID prevents the same repair from being rewarded twice.

### Will the pet cover the Codex composer?

The open cabin collapses on task routes, and the nest moves away from the composer. BUGFIRE also supports Escape, keyboard navigation, narrow windows, and reduced motion.

### Is BUGFIRE an OpenAI product or certification?

No. BUGFIRE is an independent, unofficial extension. Its levels and cards are local entertainment records, not OpenAI credentials or proof of professional skill.

## Upstream, license, and trademarks

BUGFIRE is based on the pinned [Codex Dream Skin v1.1.2 commit](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2). The upstream project provides the local CDP theme engine. This extension adds the original Patch Dragon, six animation states, simulated Build state machine, XP and skills, growth cards, and season keepsake.

Project code is licensed under the root [`LICENSE`](LICENSE). Upstream attribution, runtime boundaries, and trademark exclusions are documented in [`NOTICE.md`](NOTICE.md).

BUGFIRE is not affiliated with, endorsed by, or sponsored by OpenAI. Codex, OpenAI, and related marks belong to their respective owners.
