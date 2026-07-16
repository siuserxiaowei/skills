# BUGFIRE privacy notes

BUGFIRE does not include analytics, telemetry, advertising, accounts, or a project-owned network service. Its first release uses a verified loopback CDP session and stores gameplay progress locally.

## Data stored locally

`~/Library/Application Support/CodexDreamSkinStudio/bugfire-progress.json` contains only:

- schema version, pet ID, and season ID;
- XP, failed Build count, successful Build count, and repaired Build count;
- unlocked skills;
- level-card and season-keepsake records;
- settled event IDs and an update timestamp.

The file is schema-validated, size-bounded, atomically replaced, and set to permission mode `0600`.

## Data not read by the pet

BUGFIRE does not read or store:

- task text, prompts, or conversations;
- project source code or file contents;
- API keys, provider settings, Base URLs, or credentials;
- real Shell output or Build logs;
- clipboard contents, contacts, camera, microphone recordings, or location.

Codex itself remains responsible for its own data handling; BUGFIRE does not change the official application's privacy policy.

## Reset and removal

“重置体验” replaces BUGFIRE progress with a new Lv1 / 0 XP record. Pause or Restore removes injected UI but intentionally preserves the local progress file. A user may delete that one JSON file after Restore if they also want to erase BUGFIRE gameplay history.

## Public diagnostics

Do not upload an unredacted Application Support directory. Logs may contain local paths or environment details even though the pet progress file does not contain task or source content. Public screenshots should crop the sidebar and cover project names, task text, account details, and attachment identifiers.
