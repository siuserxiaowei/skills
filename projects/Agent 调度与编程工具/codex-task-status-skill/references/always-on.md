# Optional always-on mode

Always-on mode is opt-in. It adds a small managed block to the user's Codex `AGENTS.md`; it does not change `agents/openai.yaml` or implicitly install the skill elsewhere.

## Enable

Run from the skill directory:

```sh
python3 scripts/toggle-always-on.py enable
```

The script targets `$CODEX_HOME/AGENTS.md` when `CODEX_HOME` is set, otherwise `~/.codex/AGENTS.md`. Use `--path <file>` to target a different user-level `AGENTS.md`. If the file exists, the script creates a timestamped backup before the first actual change. Repeated enable calls are no-ops and never duplicate the block.

## Check or disable

```sh
python3 scripts/toggle-always-on.py status
python3 scripts/toggle-always-on.py disable
```

Disable removes only the content between the task-status markers and preserves all unrelated text. It also backs up an existing file before changing it.

Always-on mode asks Codex to apply the seven-state lifecycle to substantive Codex work. It does not authorize creating tasks, dispatching messages, or changing historical tasks without the same explicit commands and confirmations required by the skill.
