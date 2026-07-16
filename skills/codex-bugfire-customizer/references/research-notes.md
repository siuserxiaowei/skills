# Research-derived design notes

These notes justify the reusable mechanics; they are not licenses for third-party assets.

| Source | Confirmed mechanism | Applied here | Boundary |
|---|---|---|---|
| VS Code Pets README and extension manifest | Multiple pets, color/size/theme choices, adding pets, play interaction, import/export pet lists | Six-state art, click sayings, portable pack | No third-party sprites copied |
| Habitica README and public content modules | Tasks become RPG progress; levels, pets, quests, achievements, rewards | Local XP, derived quest board, growth cards | No punitive HP and no network/account layer |
| WakaTime VS Code README and CLI usage | Opt-in coding metrics, status display, local/offline behavior, privacy hiding controls | Local-first aggregate counters and explicit privacy boundary | No file, project, branch, language, or transcript tracking |
| Codex Dream Skin pinned upstream README | User-selected background, reversible loopback CDP injection, native controls retained | Theme engine and rollback model | Do not modify official bundle or expose CDP |

Sources accessed 2026-07-16:

- https://github.com/tonybaloney/vscode-pets
- https://github.com/HabitRPG/habitica
- https://github.com/wakatime/vscode-wakatime
- https://github.com/wakatime/wakatime-cli/blob/develop/USAGE.md
- https://github.com/Fei-Away/Codex-Dream-Skin/commit/2f038b5322702cfb248d9c7564b56470a389abc2

The selected mechanics emphasize customization, playful feedback, portability, privacy, and reversible installation. Social accounts, leaderboards, real command execution, transcript tracking, and externally scored skill claims remain outside this pack format.
