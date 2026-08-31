# BUGFIRE project notes

> Version: `1.3.0-bugfire.1`
> Platform: macOS
> Canonical public repository: <https://github.com/siuserxiaowei/Codex-Bugfire-Skin>

BUGFIRE「补丁兽」is an independent extension of Codex Dream Skin. It adds an original pixel Patch Dragon, a clearly labelled simulated Build loop, five local progression levels, growth cards, and a Season 01 keepsake certificate.

The extension is based on [Codex Dream Skin v1.1.2 commit `2f038b5`](https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2). The upstream project is the runtime base, not BUGFIRE's canonical product URL.

## Product boundaries

- Runs against the official Codex Desktop app on macOS.
- Does not modify the official `.app`, `app.asar`, or code signature.
- Uses only a verified loopback CDP endpoint already associated with Codex.
- The desktop-pet runtime does not read task text, prompts, source code, API keys, secrets, or real Build output.
- The separately invoked Character Director sends only the supplied brief to its configured endpoint and does not persist its environment API key.
- Does not execute a real project or Shell command in `1.3.0-bugfire.1`.
- Treats levels and cards as local entertainment records, not skills assessments or credentials.

## Repository layout

```text
.
├── README.md                  # Chinese product overview
├── README.en.md               # English product overview
├── GEO-ANALYSIS.md            # Repository-level AI-search readiness audit
├── SEO-PLAN.md                # Publication and discovery plan
├── llms.txt                   # Machine-readable navigation and facts
├── docs/
│   ├── USAGE.zh-CN.md         # Installation, controls, verify, restore
│   └── images/                # Privacy-safe BUGFIRE runtime evidence
└── macos/
    ├── assets/                # Theme, renderer UI, CSS
    ├── scripts/               # Installer, injector, progress model
    ├── tests/                 # State, lifecycle, UI and upstream tests
    └── references/            # QA inventory
```

The upstream `windows/` directory remains in the source history, but BUGFIRE pet functionality is currently implemented and tested only under `macos/`. Do not advertise Windows pet support until equivalent code and tests exist.

## Runtime flow

```text
Official Codex Desktop
        │
        │ verified 127.0.0.1 CDP
        ▼
BUGFIRE injector
        │
        ├── inject idempotent CSS and decorative DOM
        ├── validate renderer markers and native interaction surfaces
        └── Runtime binding for validated pet events
                │
                ▼
Application Support progress file
atomic JSON · mode 0600 · no task/source/key fields
```

The renderer exposes a six-state pet animation (`idle`, `building`, `bug`, `fire`, `success`, `level-up`). It automatically collapses the cabin on task routes and positions the 72 px nest away from the native composer.

## Local paths

| Purpose | Path |
| --- | --- |
| Source checkout | User-selected repository directory |
| Installed engine | `~/.codex/codex-dream-skin-studio` |
| Runtime state | `~/Library/Application Support/CodexDreamSkinStudio` |
| Progress | `bugfire-progress.json` inside the runtime state directory |

## Git remotes

The pinned source repository is now named `upstream`, and its push URL is deliberately set to `DISABLED`. No user-owned `origin` or canonical URL is configured yet. Never push this independent product branch to `Fei-Away/Codex-Dream-Skin`.

```bash
git remote add origin <user-owned BUGFIRE repository URL>
```

The second command intentionally remains a release-time step until the user supplies or creates the canonical repository URL.

## Release evidence

The first release should include:

- full `macos/tests/run-tests.sh` output;
- `doctor-macos.sh --require-live` with `pass: true`;
- `verify-dream-skin-macos.sh --reload` with `pass: true`;
- Restore/no-residue verification followed by a hot re-apply;
- privacy-safe home, cabin, failure, growth-card, certificate, and task-route screenshots;
- exact version `v1.3.0-bugfire.1`, upstream attribution, MIT license, and unofficial disclaimer.
