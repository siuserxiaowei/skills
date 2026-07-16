# Acceptance checklist

- `validate` returns `pass: true`.
- `build` produces `theme.json`, `pack-report.json`, background art, and local pet art.
- No compiled path is absolute or contains `..`.
- `injector.mjs --check-payload --theme-dir <compiled>` returns `pass: true`.
- The offline preview shows the intended background, names, palette, quests, all six pet state mappings, and configured sayings.
- `npm test` passes in the engine.
- Live install, if requested, preserves the native sidebar, project picker, task area, menus, and composer.
- The open cabin collapses on task routes and Escape works.
- Every supplied state maps to its declared art; verify a visible change only when the user supplied distinct art. Missing states reuse idle art.
- Clicking the pet shows a configured saying.
- Quest progress matches aggregate local counts.
- Restore removes the pet, overlays, styles, listeners, and binding.
- Official `.app`, `app.asar`, signature, API configuration, task data, and source files remain unchanged.
- Public/shared ZIP contains no progress file, logs, keys, personal paths, or private screenshots.
