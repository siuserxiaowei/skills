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

## Optional Character Director network request

The desktop pet and deterministic pack tools remain offline. `v1.3.0-bugfire.1` also includes an optional, separately invoked `bugfire-director.mjs draft-live` command. Only when the user explicitly runs that command does it send the supplied character brief to the configured OpenAI-compatible endpoint.

- The API key is read from `BUGFIRE_OPENAI_API_KEY`; it is not accepted as a CLI argument or written to a plan.
- Output records only the endpoint origin, model ID, timestamp, and prompt/brief digests; it does not store headers or credentials.
- Remote endpoints require HTTPS. HTTP is permitted only for loopback local-model/test endpoints.
- The checked offline fixture performs no network request and states that it is not a live call.

Review an endpoint's privacy terms before using live mode. Do not put secrets, task text, source code, customer data, or private conversations in a character brief.

## Reset and removal

“重置体验” replaces BUGFIRE progress with a new Lv1 / 0 XP record. Pause or Restore removes injected UI but intentionally preserves the local progress file. A user may delete that one JSON file after Restore if they also want to erase BUGFIRE gameplay history.

## Public diagnostics

Do not upload an unredacted Application Support directory. Logs may contain local paths or environment details even though the pet progress file does not contain task or source content. Public screenshots should crop the sidebar and cover project names, task text, account details, and attachment identifiers.
