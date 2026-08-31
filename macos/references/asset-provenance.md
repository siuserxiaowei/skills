# Asset provenance

## Bundled demo hero

- File: `assets/portal-hero.png`
- SHA-256: `31bde93bb02d6723e0b6aa0ead675577604120acb0a6799163dd37f5cdd0a08e`
- Source: inherited unchanged from pinned upstream commit [`2f038b5`](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2)
- Upstream record: generated for the theme pack on 2026-07-15 using `gpt-image-2`; the third-party proxy endpoint is omitted here
- Purpose: default banner / task background preset for light red-white product hero
- Rights: the upstream project describes the image as generated for its theme pack; redistribution remains subject to the upstream MIT license, NOTICE, and any applicable provider terms

## User themes

Images chosen through Customize belong to the user (or their licensors).

## BUGFIRE runtime evidence

The six `docs/images/bugfire-*.png` files were captured from the local BUGFIRE demo and reviewed for task text, account data, private paths, and real project names before repository inclusion. They document product behavior; they are not raster overlays used by the runtime.

| File | Pixels | SHA-256 |
| --- | ---: | --- |
| `bugfire-home.png` | 1600×1141 | `4b1913d97639acfaeecf016a6f56025bb19011420d40321420a6367732b27868` |
| `bugfire-pet-cabin.png` | 1600×1141 | `b42d8fdef71d7c56ae1b3cacec2ddccfa23444d4d173226b7d99c43462aa0f75` |
| `bugfire-build-failed.png` | 1600×1141 | `e4fad7a73024606b8ebbd036d41a7334bf7c0f20f8411663b6f817ebd3039d4f` |
| `bugfire-level-up.png` | 1600×916 | `bc8c8602306bb39f363149ee0eab5490782ad14ded29b24fa9fc6a731c96bc22` |
| `bugfire-certificate.png` | 1200×1500 | `f070279acb6797f4a1dfcc797a9f4c6f2e18203ec959de8f65edee620aaed56b` |
| `bugfire-task.png` | 2362×1684 | `24fdf691e547b2721ffe342f271cb30a1f497eb11cafdfafcd126a0c58769215` |

## Character Director evidence boards

The three `docs/images/bugfire-director-*.png` files are offline 1920×1080 Chrome captures. Their HTML sources, original Patchling Zero SVGs, and renderer script are retained under `contest/bugfire/`. They load no network resources.

| File | SHA-256 |
| --- | --- |
| `bugfire-director-ai-draft.png` | `6bc423a9305eb0a8d311f0567ea481d280e58aa455ac42f07de92951e7a7a987` |
| `bugfire-director-human-rejection.png` | `ca22ffd2a065ca538a8c0520860f5596e37061decaedea64911596c5cd3d56c6` |
| `bugfire-director-pack-preview.png` | `b0c6e094c44fe26dc7e0ac3443fedccd9c5933d7363574ab67f8e14646f60ab0` |

The first board says `model ID not independently attested`. The second uses a neutral demo-operator gate, and the third is captured from the generated offline preview. These boards do not claim a live API call or named-person approval.
