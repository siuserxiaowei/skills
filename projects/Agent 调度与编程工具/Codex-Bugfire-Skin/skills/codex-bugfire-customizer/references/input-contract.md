# Bugfire Pack input contract

## Upload checklist

| Input | Required | Format | Limit | Guidance |
|---|:---:|---|---:|---|
| Workbench background | Yes | PNG, JPEG, WebP | 16 MB | Wide image; keep the text side visually quiet |
| Idle pet | Yes | PNG, JPEG, WebP | 4 MB | Transparent PNG recommended; square canvas; full character visible |
| Building pet | No | PNG, JPEG, WebP | 4 MB | Working, scanning, typing, or charging pose |
| Bug pet | No | PNG, JPEG, WebP | 4 MB | Surprised/error pose |
| Fire/action pet | No | PNG, JPEG, WebP | 4 MB | Repair or attack pose |
| Success pet | No | PNG, JPEG, WebP | 4 MB | Celebration pose |
| Level-up pet | No | PNG, JPEG, WebP | 4 MB | Upgrade/evolution pose |

Pet art totals at most 16 MB. Missing optional states reuse idle art. Animated GIF, SVG, remote URLs, archives, symlinks, and paths outside `assets/` are rejected.

## Text and rule inputs

- IDs: lowercase hyphen-case, at most 64 characters.
- Names: at most 80 characters.
- Tagline: at most 160 characters.
- Sayings: 1–12 entries, at most 80 characters each.
- Quests: 1–5 entries. Metrics are limited to `repairedBuilds`, `successfulBuilds`, `failedBuilds`, `xp`, and `level`.
- Colors: six-digit hex such as `#83ff45`.
- Rights declaration: required; optional source URL must use HTTPS.

Quests are display-only milestones derived from the existing local progress record. They do not unlock extra XP, run commands, inspect code, or contact a server.

## Asset editing

When resizing or removing a background, preserve the subject's identity, use natural edges, and keep lighting consistent. Do not add text inside pet images; the UI supplies labels. Never upscale tiny art as if it were a high-resolution source—keep pixel art crisp with nearest-neighbor treatment.
