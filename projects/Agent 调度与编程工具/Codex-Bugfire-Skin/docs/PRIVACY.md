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

- The API key is read from `BUGFIRE_OPENAI_API_KEY`; it is not accepted as a CLI argument. The parsed response and validated plan are recursively scanned for the exact key value before writing, so a reflecting or malicious endpoint is rejected without an output artifact. Endpoint-controlled envelope/content parse failures use fixed error text and never append the parser's response excerpt.
- A declared `Content-Length` above 1 MiB is rejected before reading the body. All responses are then accumulated through a streaming reader capped at 1 MiB; the reader is cancelled on the first chunk that would cross the limit. This bounds application accumulation, though the HTTP/runtime stack may buffer data before yielding a chunk.
- Output records only the endpoint origin, model ID, timestamp, and prompt/brief digests; it does not store headers or credentials.
- Live generation cannot author the persisted rights claim: `manifestProposal.rights` is copied from the validated human brief. Recorded-fixture verification requires that brief and rejects any exact-rights mismatch, even with an updated valid checksum.
- Review and materialization require the operator-controlled brief again and independently recheck its digest and exact rights. This binds output to the caller's chosen file; it does not authenticate that file's author or turn its SHA-256 digest into a signature.
- Remote endpoints require HTTPS. HTTP is permitted only for loopback local-model/test endpoints.
- The checked offline fixture performs no network request and states that it is not a live call.

Review an endpoint's privacy terms before using live mode. Do not put secrets, task text, source code, customer data, or private conversations in a character brief.

## Reset and removal

“重置体验” replaces BUGFIRE progress with a new Lv1 / 0 XP record. Pause or Restore removes injected UI but intentionally preserves the local progress file. A user may delete that one JSON file after Restore if they also want to erase BUGFIRE gameplay history.

## Public diagnostics

Do not upload an unredacted Application Support directory. Logs may contain local paths or environment details even though the pet progress file does not contain task or source content. Public screenshots should crop the sidebar and cover project names, task text, account details, and attachment identifiers.
